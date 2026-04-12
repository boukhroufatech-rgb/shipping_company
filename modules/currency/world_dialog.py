"""
Interface standardisée pour la bibliothèque mondiale de devises.
Optimisée pour la performance et l'activation instantanée.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QApplication, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from components.enhanced_table import EnhancedTableView
from components.smart_form import SmartFormDialog
from components.dialogs import show_error, show_success, confirm_action
from utils.icon_manager import IconManager
from core.themes import THEMES
from modules.settings.service import SettingsService
from PyQt6.QtWidgets import QMessageBox

class WorldCurrenciesDialog(QDialog):
    """
    Fenêtre de bibliothèque (Standardized & Optimized).
    Activation instantanée via le Smart Search Discovery.
    """
    def __init__(self, service, sync_engine, parent=None):
        super().__init__(parent)
        self.service = service
        self.sync_engine = sync_engine
        
        # Initialisation du thème et de la couleur d'accent
        settings = SettingsService()
        self.active_theme = settings.get_setting("active_theme", "emerald")
        self.accent_color = THEMES.get(self.active_theme, THEMES["emerald"])["colors"]["accent"]
        
        self.setWindowTitle("🌍 Bibliothèque Mondiale des Devises")
        self.setMinimumSize(1000, 750)
        self._all_data = []
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        # 1. Utilisation de EnhancedTableView (Source Unique)
        self.table = EnhancedTableView(table_id="world_library")
        self.table.status_filter.hide()
        self.table.footer.hide()
        
        # Action Ajout Custom
        color = self.accent_color
        self.table.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.add_custom_action = QAction(IconManager.get_icon("plus", color), "Devise Personnalisée", self)
        self.add_custom_action.triggered.connect(self.add_custom_currency)
        self.table.toolbar.insertAction(self.table.toolbar.actions()[0], self.add_custom_action)
        self.table.toolbar.addSeparator()

        # Connecter l'action de suppression (Archive/Désactiver)
        self.table.delete_action.triggered.disconnect() # On déconnecte l'action générique
        self.table.delete_action.triggered.connect(self.on_delete_currency)

        # Configuration Headers (5 colonnes au lieu de 6)
        self.table.set_headers(["N°", "Code", "Nom", "Pays", "Symbole"])
        
        layout.addWidget(self.table)

        # 2. SMART SEARCH SUGGESTION BANNER
        self.suggestion_banner = QFrame()
        self.suggestion_banner.setObjectName("suggestionBanner")
        self.suggestion_banner.setStyleSheet(f"""
            QFrame#suggestionBanner {{
                background-color: {self.accent_color}22;
                border: 1px solid {self.accent_color};
                border-radius: 6px;
                margin: 5px 10px;
            }}
        """)
        self.suggestion_banner.setFixedHeight(45)
        self.suggestion_banner.hide()
        
        banner_layout = QHBoxLayout(self.suggestion_banner)
        self.lbl_suggestion = QLabel("✨ Suggestion intelligente...")
        self.lbl_suggestion.setStyleSheet("color: #e6edf3; font-weight: bold;")
        
        self.btn_smart_activate = QPushButton(" Activer maintenant")
        self.btn_smart_activate.setIcon(IconManager.get_icon("circle-dollar-sign", "#ffffff", 16))
        self.btn_smart_activate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_smart_activate.setStyleSheet("""
            QPushButton {
                background-color: #2ea043; color: white; border-radius: 6px;
                padding: 10px 24px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #3fb950; }
            QPushButton:pressed { background-color: #238636; }
        """)
        banner_layout.addWidget(self.lbl_suggestion)
        banner_layout.addStretch()
        banner_layout.addWidget(self.btn_smart_activate)
        layout.addWidget(self.suggestion_banner)

        # 3. FOOTER
        footer_box = QFrame()
        footer_box.setStyleSheet("border-top: 1px solid #30363d;")
        footer_layout = QHBoxLayout(footer_box)
        btn_close = QPushButton("Fermer la bibliothèque")
        btn_close.setStyleSheet("background-color: #30363d; color: white; padding: 10px 25px; font-weight: bold;")
        btn_close.clicked.connect(self.accept)
        footer_layout.addStretch()
        footer_layout.addWidget(btn_close)
        layout.addWidget(footer_box)

        # Listeners
        self.table.search_input.textChanged.connect(self.on_smart_search)
        self.btn_smart_activate.clicked.connect(self.on_smart_activate)

    def on_smart_search(self, text):
        text = text.strip().upper()
        if len(text) < 2:
            self.suggestion_banner.hide()
            return
        visible_codes = {row["code"] for row in self._all_data if row["is_active"]}
        if text in visible_codes:
            self.suggestion_banner.hide()
            return
        from utils.currency_catalog import GLOBAL_CURRENCY_CATALOG
        match = next((c for c in GLOBAL_CURRENCY_CATALOG if c["code"].startswith(text) or text in c["name"].upper()), None)
        if match:
            self.current_suggestion = match
            self.lbl_suggestion.setText(f"✨ Activer {match['name']} ({match['code']}) depuis le catalogue mondial ?")
            self.suggestion_banner.show()
        else:
            self.suggestion_banner.hide()

    def on_smart_activate(self):
        """Marque une devise pour activation (sera confirmée à la fermeture)"""
        if not hasattr(self, 'current_suggestion'): return
        code = self.current_suggestion["code"]
        
        if code not in getattr(self, '_pending_activations', []):
            if not hasattr(self, '_pending_activations'): self._pending_activations = []
            self._pending_activations.append(code)
            
            # Feedback visuel immédiat dans le tableau
            self.suggestion_banner.hide()
            self.table.search_input.clear()
            self.load_data()
            show_success(self, "Préparation", f"La devise {code} a été ajoutée à la liste de confirmation.")

    def accept(self):
        """Action finale avec message d'avertissement en Arabe."""
        pending = getattr(self, '_pending_activations', [])
        
        if pending:
            # Création du message arabe personnalisé
            cur_list_str = "\n".join([f"• {c}" for c in pending])
            msg = (
                "عزيزي المستخدم\n"
                "⚠️ حذاري\n\n"
                "إن إضافة العملة سيندرج عنها إضافة حساب تلقائي بالعملات المضافة.\n"
                "وعندما تقوم بأي عملية تخص العملة (أي نوع من العمليات)، فلا يمكنك حذف هذه العملة تماماً.\n\n"
                "هل أنت متأكد من إضافة العملات التالية؟\n"
                f"{cur_list_str}\n\n"
                "بعد إضافة العملات، يمكنك تسمية حسابات العملة كما تشاء أو حذفها إن لم يكن بها أي عملية."
            )
            
            reply = QMessageBox.question(
                self, "تأكيد الإضافة", msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                try:
                    for code in pending:
                        self.service.toggle_world_currency(code, True)
                    super().accept()
                except Exception as e:
                    show_error(self, "Erreur", str(e))
                finally:
                    QApplication.restoreOverrideCursor()
            else:
                return # On reste dans le dialogue pour modifier
        else:
            super().accept()

    def load_data(self):
        """Charge les devises actives + les devises en attente (Pending)"""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self._all_data = self.sync_engine.get_catalog_status()
            pending = getattr(self, '_pending_activations', [])
            
            # Combiner les actives et les en attente pour affichage
            display_data = []
            for d in self._all_data:
                if d["is_active"] or d["code"] in pending:
                    display_data.append(d)
                
            self.table.clear_rows()
            
            for i, status in enumerate(display_data):
                is_pending = status["code"] in pending and not status["is_active"]
                
                row_idx = self.table.add_row([
                    str(i + 1),
                    status["code"],
                    status["name"],
                    status["country"],
                    status["symbol"]
                ])
                
                if is_pending:
                    self.table.set_row_background_color(row_idx, "#4d3d00")
                else:
                    self.table.set_row_background_color(row_idx, "#072b25")

            self.table.proxy_model.invalidateFilter()
        finally:
            QApplication.restoreOverrideCursor()

    def on_delete_currency(self):
        """Désactive une devise sélectionnée"""
        selected_rows = self.table.get_selected_rows()
        if not selected_rows: return
        
        row_idx = selected_rows[0]
        code = self.table.get_row_data(row_idx)[1]
        if not confirm_action(self, "Désactiver", f"Souhaitez-vous retirer '{code}' de votre liste active ?"):
            return
            
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            ok, msg = self.service.toggle_world_currency(code, False)
            if ok:
                show_success(self, "Succès", msg)
                self.load_data()
            else:
                show_error(self, "Impossible de désactiver", msg)
        finally:
            QApplication.restoreOverrideCursor()

    def add_custom_currency(self):
        schema = [
            {'name': 'code', 'label': 'Code', 'type': 'text', 'required': True},
            {'name': 'name', 'label': 'Nom', 'type': 'text', 'required': True},
            {'name': 'symbol', 'label': 'Symbole', 'type': 'text', 'required': True},
            {'name': 'country', 'label': 'Pays', 'type': 'text', 'required': True},
        ]
        dialog = SmartFormDialog("Nouvelle Devise", schema, parent=self)
        if dialog.exec():
            res = dialog.get_results()
            success, message, _ = self.service.create_currency(res['code'].upper(), res['name'], res['symbol'], res['country'])
            if success:
                self.load_data()
            else:
                show_error(self, "Erreur", message)
