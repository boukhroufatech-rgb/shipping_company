"""
Système de génération de documents professionnels
Factures, Reçus, Relevés — HTML + CSS → PDF / Impression
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QPrinter, QPrintPreviewDialog, QFileDialog
)
from PyQt6.QtGui import QTextDocument, QPageLayout
from PyQt6.QtCore import Qt, QMarginsF
from PyQt6.QtPrintSupport import QPrintDialog
from datetime import datetime


class DocumentGenerator:
    """Générateur de documents HTML → PDF / Impression"""

    def __init__(self):
        self.company_name = ""
        self.company_address = ""
        self.company_phone = ""
        self.company_email = ""

    def load_company_info(self):
        try:
            from modules.settings.service import SettingsService
            svc = SettingsService()
            self.company_name = svc.get_setting("company_name", "Société")
            self.company_address = svc.get_setting("company_address", "")
            self.company_phone = svc.get_setting("company_phone", "")
            self.company_email = svc.get_setting("company_email", "")
        except:
            pass

    def _get_base_css(self):
        return """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            color: #1a1a1a;
            padding: 15mm;
            font-size: 11pt;
            line-height: 1.5;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 3px solid #1f6feb;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }
        .company-info h1 {
            font-size: 18pt;
            color: #1f6feb;
            margin-bottom: 5px;
        }
        .company-info p {
            font-size: 9pt;
            color: #555;
        }
        .document-info {
            text-align: right;
            font-size: 10pt;
        }
        .document-info .doc-title {
            font-size: 16pt;
            font-weight: bold;
            color: #1f6feb;
            margin-bottom: 5px;
        }
        .document-info .doc-number {
            font-size: 12pt;
            color: #333;
        }
        table.main-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        table.main-table th {
            background-color: #1f6feb;
            color: white;
            padding: 10px 8px;
            text-align: center;
            font-size: 10pt;
            border: 1px solid #145a9e;
        }
        table.main-table td {
            padding: 8px;
            border: 1px solid #ddd;
            font-size: 10pt;
            vertical-align: middle;
        }
        table.main-table tr:nth-child(even) td {
            background-color: #f8faff;
        }
        .total-section {
            margin-top: 20px;
            text-align: right;
            border-top: 2px solid #1f6feb;
            padding-top: 10px;
        }
        .total-section .total-label {
            font-size: 14pt;
            font-weight: bold;
            color: #1f6feb;
        }
        .total-section .total-value {
            font-size: 16pt;
            font-weight: bold;
            color: #1a1a1a;
        }
        .footer {
            margin-top: 40px;
            display: flex;
            justify-content: space-between;
            font-size: 9pt;
            color: #888;
            border-top: 1px solid #ddd;
            padding-top: 10px;
        }
        .signature-area {
            margin-top: 50px;
            display: flex;
            justify-content: space-between;
        }
        .signature-box {
            text-align: center;
            width: 200px;
        }
        .signature-box .line {
            border-top: 1px solid #333;
            margin-top: 60px;
            padding-top: 5px;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            padding: 3px 0;
        }
        .info-row .label {
            font-weight: bold;
            color: #555;
        }
        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 9pt;
            font-weight: bold;
        }
        .badge-active { background: #d4edda; color: #155724; }
        .badge-pending { background: #fff3cd; color: #856404; }
        .badge-paid { background: #d1ecf1; color: #0c5460; }
        """

    def _get_header_html(self, doc_title, doc_number, doc_date):
        return f"""
        <div class="header">
            <div class="company-info">
                <h1>{self.company_name}</h1>
                <p>{self.company_address}</p>
                <p>Tel: {self.company_phone}</p>
                <p>{self.company_email}</p>
            </div>
            <div class="document-info">
                <div class="doc-title">{doc_title}</div>
                <div class="doc-number">N°: {doc_number}</div>
                <div>Date: {doc_date}</div>
            </div>
        </div>
        """

    def _get_footer_html(self):
        date_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
        return f"""
        <div class="footer">
            <span>{self.company_name} — {self.company_address}</span>
            <span>Généré le {date_str}</span>
        </div>
        """

    def _get_signature_html(self, left_label="Le Client", right_label="Le Responsable"):
        return f"""
        <div class="signature-area">
            <div class="signature-box">
                <div class="line">{left_label}</div>
            </div>
            <div class="signature-box">
                <div class="line">{right_label}</div>
            </div>
        </div>
        """

    def generate_invoice(self, bill_data, containers, goods_list):
        """Génère une facture de shavنة"""
        self.load_company_info()
        css = self._get_base_css()

        total_usd = bill_data.get('total_usd', 0)
        total_cbm = sum(c.get('cbm', 0) for c in containers)
        total_cartons = sum(c.get('cartons', 0) for c in containers)

        # En-tête infos
        info_rows = ""
        if bill_data.get('agent'):
            info_rows += f'<div class="info-row"><span class="label">Agent Maritime:</span><span>{bill_data["agent"]}</span></div>'
        if bill_data.get('port'):
            info_rows += f'<div class="info-row"><span class="label">Port:</span><span>{bill_data["port"]}</span></div>'
        if bill_data.get('transitaire'):
            info_rows += f'<div class="info-row"><span class="label">Transitaire:</span><span>{bill_data["transitaire"]}</span></div>'

        # Table conteneurs
        cont_rows = ""
        for i, c in enumerate(containers):
            goods_for_cont = [g for g in goods_list if g.get('container_id') == c.get('id')]
            goods_names = ", ".join(set(g.get('goods_type', '') for g in goods_for_cont))
            cont_rows += f"""
            <tr>
                <td style="text-align:center">{i+1}</td>
                <td>{c.get('container_number', '')}</td>
                <td>{goods_names or '---'}</td>
                <td style="text-align:center">{c.get('cbm', 0):.4f}</td>
                <td style="text-align:center">{c.get('cartons', 0)}</td>
                <td style="text-align:right">{c.get('used_usd_amount', 0):,.2f} DA</td>
            </tr>
            """

        # Table marchandises
        goods_rows = ""
        for i, g in enumerate(goods_list):
            goods_rows += f"""
            <tr>
                <td style="text-align:center">{i+1}</td>
                <td>{g.get('customer', '')}</td>
                <td>{g.get('goods_type', '')}</td>
                <td style="text-align:center">{g.get('cartons', 0)}</td>
                <td style="text-align:center">{g.get('cbm', 0):.4f}</td>
                <td style="text-align:right">{g.get('cbm_price_usd', 0):,.2f} DA</td>
                <td style="text-align:right">{g.get('discount_usd', 0):,.2f} DA</td>
                <td style="text-align:right">{(g.get('cbm', 0) * g.get('cbm_price_usd', 0) - g.get('discount_usd', 0)):,.2f} DA</td>
            </tr>
            """

        html = f"""
        <html><head><style>{css}</style></head><body>
        {self._get_header_html("FACTURE", bill_data.get('bill', '---'), bill_data.get('date', ''))}

        <div style="margin-bottom:15px">
            {info_rows}
        </div>

        <h3 style="color:#1f6feb;margin:15px 0 5px">Conteneurs</h3>
        <table class="main-table">
            <tr><th>N°</th><th>Conteneur</th><th>Marchandises</th><th>CBM</th><th>Cartons</th><th>Montant</th></tr>
            {cont_rows}
            <tr style="font-weight:bold;background:#e8f0fe">
                <td colspan="3" style="text-align:right">TOTAL</td>
                <td style="text-align:center">{total_cbm:.4f}</td>
                <td style="text-align:center">{total_cartons}</td>
                <td style="text-align:right">{total_usd:,.2f} DA</td>
            </tr>
        </table>

        <h3 style="color:#1f6feb;margin:15px 0 5px">Détail des Marchandises</h3>
        <table class="main-table">
            <tr><th>N°</th><th>Client</th><th>Marchandise</th><th>Cartons</th><th>CBM</th><th>Prix CBM</th><th>Remise</th><th>Total</th></tr>
            {goods_rows}
        </table>

        <div class="total-section">
            <span class="total-label">MONTANT TOTAL: </span>
            <span class="total-value">{total_usd:,.2f} DA</span>
        </div>

        {self._get_signature_html()}
        {self._get_footer_html()}
        </body></html>
        """
        return html

    def generate_receipt(self, payment_data):
        """Génère un reçu de paiement"""
        self.load_company_info()
        css = self._get_base_css()

        html = f"""
        <html><head><style>{css}</style></head><body>
        {self._get_header_html("REÇU DE PAIEMENT", payment_data.get('reference', '---'), payment_data.get('date', ''))}

        <div style="border:2px solid #238636;border-radius:8px;padding:20px;margin:20px 0;background:#f0fff4">
            <div class="info-row"><span class="label">Montant:</span><span style="font-size:16pt;font-weight:bold;color:#238636">{payment_data.get('amount', 0):,.2f} DA</span></div>
            <div class="info-row"><span class="label">Client:</span><span>{payment_data.get('customer', '---')}</span></div>
            <div class="info-row"><span class="label">Compte:</span><span>{payment_data.get('account', '---')}</span></div>
            <div class="info-row"><span class="label">Moyen de paiement:</span><span>{payment_data.get('payment_type', '---')}</span></div>
            <div class="info-row"><span class="label">Référence:</span><span>{payment_data.get('reference', '---')}</span></div>
            <div class="info-row"><span class="label">Notes:</span><span>{payment_data.get('notes', '---')}</span></div>
        </div>

        {self._get_signature_html("Le Payeur", "Le Réceptionnaire")}
        {self._get_footer_html()}
        </body></html>
        """
        return html

    def generate_statement(self, customer_name, transactions, start_date, end_date, opening_balance):
        """Génère un relevé de compte"""
        self.load_company_info()
        css = self._get_base_css()

        rows = ""
        running_balance = opening_balance
        total_debit = 0
        total_credit = 0

        for i, t in enumerate(transactions):
            debit = t.get('debit', 0)
            credit = t.get('credit', 0)
            running_balance += credit - debit
            total_debit += debit
            total_credit += credit

            rows += f"""
            <tr>
                <td style="text-align:center">{i+1}</td>
                <td>{t.get('date', '')}</td>
                <td>{t.get('description', '')}</td>
                <td style="text-align:right">{debit:,.2f}</td>
                <td style="text-align:right">{credit:,.2f}</td>
                <td style="text-align:right;font-weight:bold">{running_balance:,.2f}</td>
            </tr>
            """

        balance_class = "color:#238636" if running_balance >= 0 else "color:#f85149"

        html = f"""
        <html><head><style>{css}</style></head><body>
        {self._get_header_html("RELEVÉ DE COMPTE", "---", f"{start_date} au {end_date}")}

        <div style="margin-bottom:15px">
            <div class="info-row"><span class="label">Client:</span><span style="font-weight:bold">{customer_name}</span></div>
            <div class="info-row"><span class="label">Période:</span><span>{start_date} — {end_date}</span></div>
            <div class="info-row"><span class="label">Solde d'ouverture:</span><span>{opening_balance:,.2f} DA</span></div>
        </div>

        <table class="main-table">
            <tr><th>N°</th><th>Date</th><th>Description</th><th>Débit</th><th>Crédit</th><th>Solde</th></tr>
            {rows}
            <tr style="font-weight:bold;background:#e8f0fe">
                <td colspan="3" style="text-align:right">TOTAUX</td>
                <td style="text-align:right">{total_debit:,.2f}</td>
                <td style="text-align:right">{total_credit:,.2f}</td>
                <td style="text-align:right;{balance_class}">{running_balance:,.2f}</td>
            </tr>
        </table>

        <div class="total-section">
            <span class="total-label">SOLDE FINAL: </span>
            <span class="total-value" style="{balance_class}">{running_balance:,.2f} DA</span>
        </div>

        {self._get_signature_html()}
        {self._get_footer_html()}
        </body></html>
        """
        return html


class DocumentPreviewDialog(QDialog):
    """Dialog de prévisualisation et impression"""

    def __init__(self, html_content, title="Aperçu du document", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(800, 600)
        self.html_content = html_content
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Barre d'outils
        toolbar = QHBoxLayout()

        btn_print = QPushButton("Imprimer")
        btn_print.setStyleSheet("padding: 10px 20px; font-weight: bold; background-color: #1f6feb; color: white;")
        btn_print.clicked.connect(self._print)

        btn_preview = QPushButton("Aperçu avant impression")
        btn_preview.setStyleSheet("padding: 10px 20px;")
        btn_preview.clicked.connect(self._print_preview)

        btn_save_pdf = QPushButton("Enregistrer PDF")
        btn_save_pdf.setStyleSheet("padding: 10px 20px; background-color: #238636; color: white; font-weight: bold;")
        btn_save_pdf.clicked.connect(self._save_pdf)

        btn_close = QPushButton("Fermer")
        btn_close.setStyleSheet("padding: 10px 20px;")
        btn_close.clicked.connect(self.close)

        toolbar.addWidget(btn_print)
        toolbar.addWidget(btn_preview)
        toolbar.addWidget(btn_save_pdf)
        toolbar.addStretch()
        toolbar.addWidget(btn_close)

        layout.addLayout(toolbar)

        # Zone de prévisualisation
        self.doc = QTextDocument()
        self.doc.setHtml(self.html_content)

        from PyQt6.QtWidgets import QTextBrowser
        self.preview = QTextBrowser()
        self.preview.setHtml(self.html_content)
        self.preview.setStyleSheet("background: white; border: 1px solid #ddd;")
        layout.addWidget(self.preview)

    def _create_printer(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        try:
            printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        except:
            pass
        return printer

    def _print(self):
        printer = self._create_printer()
        dialog = QPrintDialog(printer, self)
        if dialog.exec():
            self.doc.print(printer)

    def _print_preview(self):
        printer = self._create_printer()
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(self.doc.print)
        preview.exec()

    def _save_pdf(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer en PDF", "", "PDF (*.pdf)"
        )
        if not filename:
            return
        printer = self._create_printer()
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(filename)
        self.doc.print(printer)
        from components.dialogs import show_success
        show_success(self, "Succès", f"PDF enregistré:\n{filename}")
