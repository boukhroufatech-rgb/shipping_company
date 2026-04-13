"""
Smart Form Engine - Advanced Metadata-Driven UI
Strategy: Generic Shell + Dynamic Fields + Validation Schema + Custom Slots
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QTextEdit, QComboBox, QDateEdit, QDialogButtonBox,
    QLabel, QWidget, QHBoxLayout
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont
from components.amount_input import AmountInput
from components.dialogs import show_error


class SmartFormDialog(QDialog):
    """
    محرك النماذج الذكية (Smart Form Engine)
    يعتمد على استراتيجية فصل العام عن الخاص (Generic vs Dynamic).
    """
    
    def __init__(self, title: str, schema: list, data: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.schema = schema # Le schéma (Metadata)
        self.initial_data = data or {} # Les données initiales
        self.widgets = {}
        self.custom_widgets = {} # Pour gérer les "slots personnalisés" (Custom Slots)

        self._set_ui_shell()

    def _set_ui_shell(self):
        """1. Le générique (The Generic Shell)"""
        from core.themes import get_active_colors
        c = get_active_colors()
        self._theme_colors = c
        self.setStyleSheet(f"""
            QDialog {{ background-color: {c['bg_main']}; }}
            QLabel {{ color: {c['text_main']}; }}
            QLineEdit, QTextEdit, QComboBox, QDateEdit {{
                background-color: {c['bg_secondary']}; color: {c['text_main']};
                border: 1px solid {c['border']}; border-radius: 4px; padding: 4px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {c['bg_secondary']}; color: {c['text_main']};
                selection-background-color: {c['accent']}; selection-color: #ffffff;
            }}
            QPushButton {{
                background-color: {c['accent']}; color: #ffffff;
                border: none; padding: 6px 16px; border-radius: 4px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {c['accent_hover']}; }}
            QPushButton:disabled {{ background-color: {c['bg_secondary']}; color: {c['text_secondary']}; }}
        """)
        self.main_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        # 2. Le dynamique (The Dynamic Fields / Rendering Engine)
        self._render_fields()

        self.main_layout.addLayout(self.form_layout)

        # Boutons d'action standardisés
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        self.main_layout.addWidget(self.buttons)

    def _render_fields(self):
        """Moteur de rendu (Rendering Engine)"""
        for field in self.schema:
            name = field['name']
            label = field['label']

            # Vérifier s'il y a un "slot personnalisé" (Custom Slot)
            if 'custom_widget' in field:
                widget = field['custom_widget']
            else:
                widget = self._create_widget_by_type(field)

            self.widgets[name] = widget

            if 'quick_add_callback' in field:
                from components.dialogs import create_quick_add_layout
                # Pass the original widget to the callback so it can update it
                callback = lambda checked=False, w=widget, cb=field['quick_add_callback']: cb(w)
                layout_widget = create_quick_add_layout(widget, callback)
                self.form_layout.addRow(label + ":", layout_widget)
            else:
                self.form_layout.addRow(label + ":", widget)

            # Liaison des données (Data Binding) - Données initiales
            if name in self.initial_data:
                self._apply_initial_value(widget, field, self.initial_data[name])

    def _create_widget_by_type(self, field: dict) -> QWidget:
        f_type = field.get('type', 'text')
        
        if f_type == 'text':
            return QLineEdit()
        elif f_type == 'multiline':
            w = QTextEdit()
            w.setMaximumHeight(80)
            return w
        elif f_type == 'number':
            return AmountInput()
        elif f_type == 'date':
            w = QDateEdit()
            w.setCalendarPopup(True)
            w.setDate(QDate.currentDate())
            w.setFixedWidth(140)
            return w
        elif f_type == 'dropdown':
            w = QComboBox()
            # [CUSTOM] 2026-04-03 - Rendre le dropdown editable avec recherche
            w.setEditable(True)
            w.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
            w.lineEdit().setPlaceholderText("Rechercher...")
            
            for opt in field.get('options', []):
                if isinstance(opt, tuple):
                    w.addItem(opt[0], opt[1])
                else:
                    w.addItem(str(opt), opt)
            
            # Ajouter completer pour recherche
            from PyQt6.QtWidgets import QCompleter
            completer = QCompleter(w.model())
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            w.setCompleter(completer)
            
            # [CUSTOM] 2026-04-03 - Styliser le popup avec highlight (thème actif)
            c = getattr(self, '_theme_colors', {})
            popup = completer.popup()
            popup.setStyleSheet(f"""
                QListView {{
                    background-color: {c.get('bg_secondary', '#112e2a')};
                    color: {c.get('text_main', '#e6edf3')};
                    border: 1px solid {c.get('border', '#214d47')};
                }}
                QListView::item {{ padding: 8px; }}
                QListView::item:selected {{
                    background-color: {c.get('accent', '#2ea043')};
                    color: white;
                }}
                QListView::item:hover {{
                    background-color: {c.get('bg_tertiary', '#1a3d38')};
                }}
            """)
            
            # [CUSTOM] 2026-04-03 - Highlight search text en jaune
            w.editTextChanged.connect(lambda text, combo=w: self._highlight_completer(combo, text))
            
            return w
    
    def _highlight_completer(self, combo: QComboBox, text: str):
        """Highlight search text in yellow in the dropdown popup"""
        if not text:
            return
        completer = combo.completer()
        if not completer:
            return
        
        popup = completer.popup()
        model = completer.model()
        
        # Appliquer le style (thème actif)
        c = getattr(self, '_theme_colors', {})
        popup.setStyleSheet(f"""
            QListView {{
                background-color: {c.get('bg_secondary', '#112e2a')};
                color: {c.get('text_main', '#e6edf3')};
                border: 1px solid {c.get('border', '#214d47')};
            }}
            QListView::item {{ padding: 8px; }}
            QListView::item:selected {{
                background-color: {c.get('accent', '#2ea043')};
                color: white;
            }}
            QListView::item:hover {{
                background-color: {c.get('bg_tertiary', '#1a3d38')};
            }}
        """)

    def _apply_initial_value(self, widget, field: dict, value):
        f_type = field.get('type', 'text')
        if value is None: return
        
        if f_type == 'text': widget.setText(str(value))
        elif f_type == 'multiline': widget.setPlainText(str(value))
        elif f_type == 'number': widget.setValue(float(value))
        elif f_type == 'date':
            if hasattr(value, 'date'): value = value.date()
            widget.setDate(QDate(value.year, value.month, value.day))
        elif f_type == 'dropdown':
            index = widget.findData(value)
            if index >= 0: widget.setCurrentIndex(index)

    def get_results(self) -> dict:
        """3. الربط ثنائي الاتجاه (Data Binding / State Object)"""
        state = {}
        for field in self.schema:
            name = field['name']
            widget = self.widgets[name]
            f_type = field.get('type', 'text')
            
            if f_type == 'text': state[name] = widget.text().strip()
            elif f_type == 'multiline': state[name] = widget.toPlainText().strip()
            elif f_type == 'number': state[name] = widget.get_amount()
            elif f_type == 'date': state[name] = widget.date().toPyDate()
            elif f_type == 'dropdown': state[name] = widget.currentData()
            elif 'custom_widget' in field:
                # محاولة الحصول على القيمة من الـ widget المخصص إذا كان يدوي
                if hasattr(widget, 'value'): state[name] = widget.value()
                
        return state

    def validate_and_accept(self):
        """منطق التحقق (Validation Schema)"""
        state = self.get_results()
        for field in self.schema:
            name = field['name']
            label = field['label']
            
            # التحقق من "الحقل مطلوب"
            if field.get('required', False) and not state.get(name):
                show_error(self, "خطأ في التحقق", f"الحقل '{label}' مطلوب ولا يمكن تركه فارغاً.")
                return
            
            # التحقق من القيم الرقمية (Min/Max)
            if field.get('type') == 'number' and 'validation' in field:
                val = state.get(name, 0)
                v_schema = field['validation']
                if 'min' in v_schema and val < v_schema['min']:
                    show_error(self, "خطأ في القيمة", f"القيمة في '{label}' يجب أن تكون أكبر من {v_schema['min']}.")
                    return
                if 'max' in v_schema and val > v_schema['max']:
                    show_error(self, "خطأ في القيمة", f"القيمة في '{label}' يجب أن تكون أصغر من {v_schema['max']}.")
                    return
        
        self.accept()
