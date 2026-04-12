"""
مكون فلترة الحالة (ACTIVE/INACTIVE/ALL)
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import pyqtSignal

from core.themes import THEMES
from modules.settings.service import SettingsService


class StatusFilter(QWidget):
    """
    فلتر لعرض العناصر حسب حالتها (نشط/غير نشط/الكل)
    يظهر في أسفل كل جدول للسماح بتصفية البيانات المعروضة
    """
    statusChanged = pyqtSignal(str)  # "active", "inactive", "all"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusFilterContainer")
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 10)
        layout.setSpacing(10)

        # [FIX] 2026-03-31: استخدام الثيم الموحد بدلاً من الألوان الثابتة
        # الآن StatusFilter يتبع نظام الثيمات المركزي (Tree System)
        settings_service = SettingsService()
        active_theme = settings_service.get_setting("active_theme", "emerald")
        theme = THEMES.get(active_theme, THEMES["emerald"])
        
        self.setStyleSheet(f"""
            QWidget#statusFilterContainer {{
                background-color: {theme['colors']['filter_bg']};
                border-top: 1px solid {theme['colors']['filter_border_top']};
            }}
            QLabel {{
                color: {theme['colors']['filter_text']};
                font-size: 11px;
                font-weight: bold;
                border: none;
            }}
            QComboBox {{
                background-color: {theme['colors']['filter_combo_bg']};
                color: {theme['colors']['filter_combo_text']};
                border: 1px solid {theme['colors']['filter_combo_border']};
                border-radius: 4px;
                padding: 2px 8px;
                min-width: 150px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme['colors']['filter_combo_popup_bg']};
                color: {theme['colors']['filter_combo_text']};
                selection-background-color: {theme['colors']['filter_combo_selection']};
                border: 1px solid {theme['colors']['filter_combo_border']};
            }}
        """)

        label = QLabel("FILTRAGE :")
        layout.addWidget(label)

        self.combo = QComboBox()
        self.combo.addItem("✓ Actifs uniquement", "active")
        self.combo.addItem("✗ Supprimés uniquement", "inactive")
        self.combo.addItem("📋 Tous les enregistrements", "all")
        self.combo.currentIndexChanged.connect(self._on_change)
        layout.addWidget(self.combo)

        layout.addStretch()

    def _on_change(self):
        """عند تغيير الفلتر، إرسال إشارة للجدول لتحديث البيانات"""
        self.statusChanged.emit(self.combo.currentData())

    def get_filter(self) -> str:
        """الحصول على الفلتر الحالي"""
        return self.combo.currentData()

    def set_filter(self, filter_value: str):
        """تعيين الفلتر برمجياً"""
        for i in range(self.combo.count()):
            if self.combo.itemData(i) == filter_value:
                self.combo.setCurrentIndex(i)
                break
