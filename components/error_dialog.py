"""
نظام عرض الأخطاء في الواجهة الرسومية
Professional Error Dialog System
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QFrame, QSizePolicy,
    QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon


class ErrorDialog(QDialog):
    """
    نافذة احترافية لعرض الأخطاء
    - تصميم واضح
    - تفاصيل كاملة للخطأ
    - خيار نسخ التفاصيل
    - ألوان حسب خطورة الخطأ
    """
    
    def __init__(self, parent=None, title: str = "خطأ", message: str = "", 
                 details: str = "", error_type: str = "error"):
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setMinimumSize(500, 300)
        self.setModal(True)
        
        # تحديد نوع الخطأ (error, warning, critical)
        self.error_type = error_type
        self._init_ui(message, details)
    
    def _init_ui(self, message: str, details: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 1. العنوان والأيقونة
        header_layout = QHBoxLayout()
        
        # الأيقونة حسب النوع
        icon_label = QLabel()
        icon_label.setFont(QFont("Segoe UI", 24))
        if self.error_type == "critical":
            icon_label.setText("🔴")
        elif self.error_type == "warning":
            icon_label.setText("⚠️")
        else:
            icon_label.setText("❌")
        
        header_layout.addWidget(icon_label)
        
        # العنوان
        title_label = QLabel(self.windowTitle())
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #c0392b;" if self.error_type != "warning" else "#e67e22;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 2. رسالة الخطأ
        if message:
            msg_frame = QFrame()
            msg_frame.setStyleSheet("""
                QFrame {
                    background-color: #fdf2f2;
                    border-left: 4px solid #e74c3c;
                    padding: 10px;
                    border-radius: 4px;
                }
            """)
            msg_layout = QVBoxLayout(msg_frame)
            
            msg_label = QLabel(message)
            msg_label.setWordWrap(True)
            msg_label.setFont(QFont("Segoe UI", 11))
            msg_label.setStyleSheet("color: #2c3e50;")
            msg_layout.addWidget(msg_label)
            
            layout.addWidget(msg_frame)
        
        # 3. التفاصيل التقنية
        if details:
            details_label = QLabel("📋 التفاصيل التقنية:")
            details_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            layout.addWidget(details_label)
            
            self.details_text = QTextEdit()
            self.details_text.setReadOnly(True)
            self.details_text.setFont(QFont("Consolas", 9))
            self.details_text.setText(details)
            self.details_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.details_text.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 8px;
                    color: #2c3e50;
                }
            """)
            layout.addWidget(self.details_text, 1)
        
        # 4. الأزرار
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # زر نسخ التفاصيل
        if details:
            copy_btn = QPushButton("📋 نسخ التفاصيل")
            copy_btn.clicked.connect(self._copy_details)
            copy_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            button_layout.addWidget(copy_btn)
        
        # زر إغلاق
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 8px 24px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _copy_details(self):
        """نسخ التفاصيل للحافظة"""
        from PyQt6.QtWidgets import QApplication
        if hasattr(self, 'details_text'):
            clipboard = QApplication.clipboard()
            clipboard.setText(self.details_text.toPlainText())
            
            # إشعار صغير
            self.details_label = QLabel("✅ تم النسخ!")
            self.details_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.layout().addWidget(self.details_label)
            
            QTimer.singleShot(2000, self.details_label.deleteLater)


def show_error(parent, message: str, exception: Exception = None, 
               title: str = "خطأ", details: str = None):
    """
    دالة مساعدة لعرض خطأ بسرعة
    
    Example:
        show_error(self, "فشل حفظ البيانات", exception=e)
    """
    full_details = details or ""
    if exception:
        import traceback
        full_details += "\n" + traceback.format_exc()
    
    dialog = ErrorDialog(
        parent=parent,
        title=title,
        message=message,
        details=full_details.strip()
    )
    dialog.exec()


def show_warning(parent, message: str, title: str = "تحذير"):
    """عرض تحذير"""
    dialog = ErrorDialog(
        parent=parent,
        title=title,
        message=message,
        error_type="warning"
    )
    dialog.exec()


def show_critical(parent, message: str, exception: Exception = None, 
                  title: str = "خطأ حرج"):
    """عرض خطأ حرج"""
    import traceback
    details = traceback.format_exc() if exception else ""
    
    dialog = ErrorDialog(
        parent=parent,
        title=title,
        message=message,
        details=details,
        error_type="critical"
    )
    dialog.exec()


def show_info(parent, message: str, title: str = "معلومة"):
    """عرض معلومة"""
    QMessageBox.information(parent, title, message)


def show_success(parent, message: str, title: str = "نجاح"):
    """عرض رسالة نجاح"""
    QMessageBox.information(parent, f"✅ {title}", message)


def confirm_action(parent, message: str, title: str = "تأكيد") -> bool:
    """
    طلب تأكيد من المستخدم
    Returns:
        True إذا أكد المستخدم، False otherwise
    """
    result = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    return result == QMessageBox.StandardButton.Yes
