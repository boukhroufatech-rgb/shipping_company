"""
Fenêtre de prévisualisation et configuration de l'exportation
[UPDATED] with Live HTML & PDF Preview
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QCheckBox, QFormLayout,
    QDialogButtonBox, QGroupBox, QFrame, QTextEdit,
    QTabWidget, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtPrintSupport import QPrinter, QPrintPreviewDialog

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False


class ExportPreviewDialog(QDialog):
    """
    Dialogue permettant de configurer et prévisualiser le rapport
    avant la génération effective.
    """
    def __init__(self, table_id: str = "Rapport", parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Configuration du Rapport Premium")
        self.setMinimumSize(700, 600)
        self._setup_ui(table_id)
        
    def _setup_ui(self, table_id):
        main_layout = QVBoxLayout(self)
        
        # Tabs: Configuration | Preview HTML | Preview PDF
        self.tabs = QTabWidget()
        
        # ===== TAB 1: Configuration =====
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)
        
        # 1. Section Identification du Rapport
        group_info = QGroupBox("Identification du Rapport")
        form = QFormLayout(group_info)
        
        self.report_title = QLineEdit(f"RAPPORT : {table_id.upper()}")
        self.report_title.setPlaceholderText("Ex: Relevé de compte client")
        self.report_title.textChanged.connect(self._update_preview)
        
        self.report_subtitle = QLineEdit()
        self.report_subtitle.setPlaceholderText("Sous-titre optionnel (Ex: Période du 01/01 au 31/01)")
        self.report_subtitle.textChanged.connect(self._update_preview)
        
        form.addRow("Titre principal:", self.report_title)
        form.addRow("Sous-titre:", self.report_subtitle)
        config_layout.addWidget(group_info)
        
        # 2. Options de Formatage
        group_opts = QGroupBox("Options de Mise en Page")
        opts_layout = QVBoxLayout(group_opts)
        
        self.include_company = QCheckBox("Inclure l'en-tête de l'institution (Nom, Adresse, Tél)")
        self.include_company.setChecked(True)
        self.include_company.stateChanged.connect(self._update_preview)
        
        self.include_date = QCheckBox("Inclure la date et l'heure de génération")
        self.include_date.setChecked(True)
        self.include_date.stateChanged.connect(self._update_preview)
        
        self.zebra_stripes = QCheckBox("Appliquer le style Zèbre (lignes alternées)")
        self.zebra_stripes.setChecked(True)
        self.zebra_stripes.stateChanged.connect(self._update_preview)
        
        self.auto_filters = QCheckBox("Activer les filtres Excel automatiques")
        self.auto_filters.setChecked(True)
        
        opts_layout.addWidget(self.include_company)
        opts_layout.addWidget(self.include_date)
        opts_layout.addWidget(self.zebra_stripes)
        opts_layout.addWidget(self.auto_filters)
        config_layout.addWidget(group_opts)
        
        # 3. Note
        note = QLabel("ℹ️ Le fichier généré sera au format PDF (.pdf) avec mise en page Premium")
        note.setStyleSheet("color: #8b949e; font-style: italic; font-size: 11px;")
        config_layout.addWidget(note)
        config_layout.addStretch()
        
        self.tabs.addTab(config_widget, "⚙️ Configuration")
        
        # ===== TAB 2: HTML Preview =====
        html_preview_widget = QWidget()
        html_layout = QVBoxLayout(html_preview_widget)
        
        html_title = QLabel("👁️ Aperçu HTML (Live)")
        html_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        html_layout.addWidget(html_title)
        
        if WEBENGINE_AVAILABLE:
            self.web_view = QWebEngineView()
            self.web_view.setMinimumHeight(400)
            html_layout.addWidget(self.web_view)
        else:
            self.html_text = QTextEdit()
            self.html_text.setReadOnly(True)
            self.html_text.setMinimumHeight(400)
            html_layout.addWidget(self.html_text)
            
            fallback_note = QLabel("⚠️ QWebEngineView non disponible - Affichage HTML texte")
            fallback_note.setStyleSheet("color: #f39c12; font-size: 11px;")
            html_layout.addWidget(fallback_note)
        
        refresh_btn = QPushButton("🔄 Rafraîchir l'aperçu")
        refresh_btn.clicked.connect(self._update_preview)
        html_layout.addWidget(refresh_btn)
        
        self.tabs.addTab(html_preview_widget, "👁️ Aperçu HTML")
        
        # ===== TAB 3: PDF Preview =====
        pdf_preview_widget = QWidget()
        pdf_layout = QVBoxLayout(pdf_preview_widget)
        
        pdf_title = QLabel("📄 Aperçu PDF (Plein écran)")
        pdf_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        pdf_layout.addWidget(pdf_title)
        
        self.pdf_preview_btn = QPushButton("👁️ Ouvrir l'aperçu PDF")
        self.pdf_preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white; font-weight: bold;
                padding: 12px 24px; border-radius: 6px; font-size: 14px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        pdf_layout.addWidget(self.pdf_preview_btn)
        
        pdf_note = QLabel("ℹ️ Cette option ouvre une fenêtre d'aperçu pour l'impression ou la prévisualisation")
        pdf_note.setStyleSheet("color: #8b949e; font-size: 11px;")
        pdf_layout.addWidget(pdf_note)
        
        pdf_layout.addStretch()
        self.tabs.addTab(pdf_preview_widget, "📄 Aperçu PDF")
        
        main_layout.addWidget(self.tabs)
        
        # ===== Buttons =====
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        main_layout.addWidget(btns)
        
        self.ok_button = btns.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setText("💾 Enregistrer PDF")
        self.ok_button.setStyleSheet("font-weight: bold; background-color: #27ae60;")
        
        # Generate initial preview
        self._update_preview()

    def set_button_text(self, text: str):
        self.ok_button.setText(text)
        
    def set_pdf_callback(self, callback):
        """Set callback for PDF preview"""
        self._pdf_callback = callback
        self.pdf_preview_btn.clicked.connect(self._open_pdf_preview)
        
    def _open_pdf_preview(self):
        """Open PDF print preview dialog"""
        if hasattr(self, '_pdf_callback') and self._pdf_callback:
            self._pdf_callback()
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Info", "Générez d'abord le rapport pour voir l'aperçu PDF")
        
    def _update_preview(self):
        """Update HTML preview"""
        opts = self.get_options()
        html = self._generate_preview_html(opts)
        
        if WEBENGINE_AVAILABLE and hasattr(self, 'web_view'):
            self.web_view.setHtml(html)
        elif hasattr(self, 'html_text'):
            self.html_text.setHtml(html)
    
    def _generate_preview_html(self, opts):
        """Generate preview HTML"""
        from datetime import datetime
        
        css = """
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; color: #333; margin: 20px; }
            .header { border-bottom: 2px solid #1f6feb; padding-bottom: 15px; margin-bottom: 30px; }
            .company-name { font-size: 22pt; font-weight: bold; color: #1f6feb; }
            .report-title { font-size: 28pt; font-weight: bold; text-align: center; margin: 20px 0; }
            .report-subtitle { font-size: 14pt; color: #666; font-style: italic; text-align: center; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th { background-color: #1f6feb; color: white; padding: 12px; }
            td { padding: 10px; border: 1px solid #ddd; }
            .zebra { background-color: #f8faff; }
            .footer { margin-top: 30px; text-align: center; font-size: 10px; color: #888; }
        </style>
        """
        
        html = f"""
        <html><head>{css}</head><body>
        """
        
        if opts["include_company"]:
            html += """
            <div class="header">
                <div class="company-name">🚢 Shipping Company</div>
                <div>Gestion Import-Export | Tél: +213 555 123 456</div>
            </div>
            """
        
        html += f"""
        <h1 class="report-title">{opts['title']}</h1>
        """
        
        if opts["subtitle"]:
            html += f"<div class='report-subtitle'>{opts['subtitle']}</div>"
        
        if opts["include_date"]:
            html += f"<p style='text-align:right; color:#888;'>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>"
        
        # Sample table for preview
        sample_data = [
            ["001", "2026-04-01", "Achat Marchandises", "1,250,000.00 DA", "CREDIT"],
            ["002", "2026-04-01", "Frais Transport", "-250,000.00 DA", "DEBIT"],
            ["003", "2026-04-02", "Vente Client X", "500,000.00 DA", "CREDIT"],
            ["004", "2026-04-02", "Paiement Fournisseur", "-180,000.00 DA", "DEBIT"],
        ]
        
        zebra_class = "zebra" if opts["zebra_stripes"] else ""
        
        html += """
        <table>
            <tr><th>N°</th><th>Date</th><th>Description</th><th>Montant</th><th>Type</th></tr>
        """
        
        for i, row in enumerate(sample_data):
            cls = zebra_class if opts["zebra_stripes"] and i % 2 else ""
            color = "#27ae60" if row[4] == "CREDIT" else "#e74c3c"
            html += f"""
            <tr class="{cls}">
                <td>{row[0]}</td>
                <td>{row[1]}</td>
                <td>{row[2]}</td>
                <td style='text-align:right;'>{row[3]}</td>
                <td style='color:{color};'>{row[4]}</td>
            </tr>
            """
        
        html += """
        </table>
        <div class="footer">Logiciel de Gestion Logistique - Rapport interactif</div>
        </body></html>
        """
        
        return html

    def get_options(self):
        """Retourne les résultats de la configuration"""
        return {
            "title": self.report_title.text(),
            "subtitle": self.report_subtitle.text(),
            "include_company": self.include_company.isChecked(),
            "include_date": self.include_date.isChecked(),
            "zebra_stripes": self.zebra_stripes.isChecked(),
            "auto_filters": self.auto_filters.isChecked()
        }