"""
Vues pour le module Clients (Customers) - Standardized & Purified
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QComboBox,
    QDialog, QLineEdit, QPushButton, QTextEdit, QFormLayout,
    QDateEdit, QDialogButtonBox
)
from PyQt6.QtCore import pyqtSignal, QDate, Qt
from datetime import datetime

from components.enhanced_table import EnhancedTableView
from components.dialogs import (
    show_error, show_success, confirm_delete, create_quick_add_layout
)
from components.smart_form import SmartFormDialog
from components.amount_input import AmountInput
from utils.formatters import format_amount, format_date
from .service import CustomerService
from modules.currency.service import CurrencyService
from modules.treasury.service import TreasuryService
from modules.logistics.service import LogisticsService

# ============================================================================
# SCHEMAS
# ============================================================================

CUSTOMER_SCHEMA = [
    {"name": "name", "label": "Nom du Client", "type": "text", "required": True},
    {"name": "phone", "label": "Téléphone", "type": "text"},
    {"name": "address", "label": "Adresse", "type": "multiline"},
    {"name": "initial_balance", "label": "Solde Initial (DA)", "type": "number", "default": 0},
    {"name": "notes", "label": "Notes", "type": "text"}
]

# ============================================================================
# MAIN VIEW
# ============================================================================

class CustomersView(QWidget):
    """Vue principale du module Clients (Standardized)"""
    dataChanged = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.service = CustomerService()
        self.currency_service = CurrencyService()
        self.treasury_service = TreasuryService()
        self.logistics_service = LogisticsService()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        self.list_tab = CustomerListTab(self.service)
        self.tabs.addTab(self.list_tab, "Clients")

        self.payments_tab = CustomerPaymentsTab(self.service, self.treasury_service)
        self.payments_tab.dataChanged.connect(self.dataChanged.emit)
        self.tabs.addTab(self.payments_tab, "Paiements")

        self.costs_tab = CustomerCostsTab(self.service)
        self.costs_tab.dataChanged.connect(self.dataChanged.emit)
        self.tabs.addTab(self.costs_tab, "Charges Client")

        self.ledger_tab = CustomerLedgerTab(self.service)
        self.tabs.addTab(self.ledger_tab, "Relevé")
    
    def refresh(self):
        self.list_tab.load_data()
        self.payments_tab.load_data()
        self.costs_tab.load_data()
        self.ledger_tab.refresh_customers()


# ============================================================================
# TABS
# ============================================================================

class CustomerListTab(QWidget):
    def __init__(self, service: CustomerService):
        super().__init__()
        self.service = service
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.table = EnhancedTableView(table_id="customer_list")
        self.table.set_headers_from_schema("customer_list")  # [GOLDEN PRINCIPLE] schema centralisé
        
        self.table.addClicked.connect(self.add_customer)
        self.table.editClicked.connect(self.edit_customer)
        self.table.deleteClicked.connect(self.delete_customer)
        self.table.restoreClicked.connect(self.restore_customer)
        self.table.refreshClicked.connect(self.load_data)
        self.table.status_filter.statusChanged.connect(self.load_data)
        self.table.add_action_button("Importer Excel", "", self.import_customers)
        
        layout.addWidget(self.table)

    def import_customers(self):
        """Importe des clients depuis un fichier Excel"""
        from PyQt6.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout, QLabel
        from PyQt6.QtWidgets import QDialogButtonBox, QComboBox, QFormLayout

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importer des clients", "",
            "Fichiers Excel (*.xlsx *.xls);;Tous les fichiers (*)"
        )
        if not file_path:
            return

        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path)
            ws = wb.active
        except Exception as e:
            return show_error(self, "Erreur", f"Impossible de lire le fichier:\n{str(e)}")

        # Lire les données
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return show_error(self, "Erreur", "Le fichier est vide.")

        # Dialog de prévisualisation
        preview = QDialog(self)
        preview.setWindowTitle(f"Prévisualisation — {len(rows)-1} lignes trouvées")
        preview.setMinimumSize(600, 400)
        p_layout = QVBoxLayout(preview)

        # Mapper les colonnes
        col_count = len(rows[0]) if rows else 0
        map_layout = QFormLayout()
        col_combos = []
        field_names = ["Ignorer", "Nom", "Téléphone", "Adresse", "Solde Initial", "Notes"]
        for i in range(min(col_count, 7)):
            combo = QComboBox()
            combo.addItems(field_names)
            # Auto-détection basée sur l'en-tête
            header = str(rows[0][i]).lower() if rows[0][i] else ""
            if "nom" in header or "name" in header:
                combo.setCurrentIndex(1)
            elif "tel" in header or "phone" in header:
                combo.setCurrentIndex(2)
            elif "adress" in header or "adresse" in header:
                combo.setCurrentIndex(3)
            elif "solde" in header or "initial" in header:
                combo.setCurrentIndex(4)
            elif "note" in header or "remarque" in header:
                combo.setCurrentIndex(5)
            col_combos.append(combo)
            map_layout.addRow(f"Colonne {i+1}:", combo)
        p_layout.addLayout(map_layout)

        # Tableau de prévisualisation
        preview_table = QTableWidget(min(10, len(rows)-1), col_count)
        preview_headers = []
        for i in range(col_count):
            h = rows[0][i] if rows[0][i] else f"Col {i+1}"
            preview_headers.append(str(h))
        preview_table.setHorizontalHeaderLabels(preview_headers)
        preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        for r in range(min(10, len(rows)-1)):
            for c in range(col_count):
                val = rows[r+1][c] if c < len(rows[r+1]) else ""
                preview_table.setItem(r, c, QTableWidgetItem(str(val) if val else ""))

        p_layout.addWidget(QLabel(f"Aperçu des 10 premières lignes (sur {len(rows)-1} au total):"))
        p_layout.addWidget(preview_table)

        # Boutons
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        p_layout.addWidget(btns)

        def on_import():
            # Créer un mapping colonne → champ
            col_map = {}
            for i, combo in enumerate(col_combos):
                field = combo.currentText()
                if field != "Ignorer":
                    col_map[i] = field

            if "Nom" not in col_map.values():
                return show_error(preview, "Erreur", "Au moins une colonne doit être mappée à 'Nom'.")

            # Importer
            existing = {c['name'].lower() for c in self.service.get_all_customers()}
            imported = 0
            skipped = 0

            for r in range(1, len(rows)):
                data = {}
                for col_idx, field in col_map.items():
                    if col_idx < len(rows[r]):
                        val = rows[r][col_idx]
                        data[field.lower()] = str(val).strip() if val else ""

                name = data.get("nom", "")
                if not name:
                    skipped += 1
                    continue
                if name.lower() in existing:
                    skipped += 1
                    continue

                try:
                    initial = 0
                    if "solde initial" in data:
                        try:
                            initial = float(data["solde initial"].replace(",", "").replace(" ", ""))
                        except:
                            initial = 0
                    self.service.create_customer(
                        name=name,
                        phone=data.get("téléphone", data.get("telephone", "")),
                        address=data.get("adresse", ""),
                        notes=data.get("notes", ""),
                        initial_balance=initial
                    )
                    existing.add(name.lower())
                    imported += 1
                except Exception:
                    skipped += 1

            preview.accept()
            self.load_data()
            show_success(self, "Importation terminée",
                         f"Importés: {imported}\nIgnorés (doublons/vides): {skipped}")

        btns.accepted.connect(on_import)
        btns.rejected.connect(preview.reject)
        preview.exec()

    def load_data(self):
        filter_status = self.table.status_filter.get_filter()
        self.table.update_actions_for_status(filter_status)

        customers = self.service.get_all_customers(filter_status=filter_status)
        self.table.clear_rows()
        for i, c in enumerate(customers, 1):
            cid = c['id']
            initial_balance = c.get('initial_balance', 0)

            # Calculate all values
            total_business = self.service.get_customer_total_business(cid)
            total_costs = self.service.get_customer_total_costs(cid)
            total_discounts = self.service.get_customer_total_discounts(cid)
            total_payments = self.service.get_customer_total_payments(cid)
            dette_externe = 0
            current_balance = self.service.get_customer_balance(cid)

            # [GOLDEN PRINCIPLE] 2026-04-19 - Pass raw floats, not formatted strings
            self.table.add_row([
                str(i), str(cid), c["name"], c["phone"] or "",
                c["address"] or "", initial_balance,
                total_business, total_costs, total_discounts,
                total_payments, dette_externe, current_balance,
                c["notes"] or ""
            ], is_active=c['is_active'])
        self.table.resize_columns_to_contents()

    def add_customer(self):
        dialog = SmartFormDialog("Nouveau Client", CUSTOMER_SCHEMA, parent=self)
        if dialog.exec():
            self.service.create_customer(**dialog.get_results())
            self.load_data()

    def edit_customer(self, row_idx):
        cust_id = int(self.table.get_row_data(row_idx)[1])
        customers = self.service.get_all_customers()
        cust = next((c for c in customers if c["id"] == cust_id), None)
        if cust:
            dialog = SmartFormDialog("Modifier Client", CUSTOMER_SCHEMA, data=cust, parent=self)
            if dialog.exec():
                self.service.update_customer(cust_id, **dialog.get_results())
                self.load_data()

    def delete_customer(self, row_idx):
        cust_id = int(self.table.get_row_data(row_idx)[1])
        name = self.table.get_row_data(row_idx)[2]
        from components.dialogs import confirm_action
        if confirm_action(self, "Archiver", f"Voulez-vous vraiment archiver le client '{name}' ?"):
            if self.service.delete_customer(cust_id):
                show_success(self, "Succès", "Client archivé")
                self.load_data()

    def restore_customer(self, row_idx):
        cust_id = int(self.table.get_row_data(row_idx)[1])
        name = self.table.get_row_data(row_idx)[2]
        from components.dialogs import confirm_action
        if confirm_action(self, "Restaurer", f"Voulez-vous réactiver le client '{name}' ?"):
            if self.service.restore_customer(cust_id):
                show_success(self, "Succès", "Client restauré")
                self.load_data()


class CustomerGoodsTab(QWidget):
    def __init__(self, service: CustomerService, logistics_service: LogisticsService):
        super().__init__()
        self.service, self.logistics_service = service, logistics_service
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.table = EnhancedTableView(table_id="customer_goods")
        self.table.set_headers_from_schema("customer_goods")  # [GOLDEN PRINCIPLE] schema centralisé
        self.table.addClicked.connect(self.add_goods)
        self.table.editClicked.connect(self.edit_goods)
        self.table.deleteClicked.connect(self.delete_goods)
        self.table.refreshClicked.connect(self.load_data)
        layout.addWidget(self.table)

    def load_data(self):
        goods = self.service.get_all_goods()
        self.table.clear_rows()
        for g in goods:
            # [GOLDEN PRINCIPLE] 2026-04-19 - Pass raw values, not formatted strings
            self.table.add_row([
                None,
                str(g["id"]),
                g["date"],  # ISO date string
                g["customer_name"],
                g["container_number"] or "N/A",
                g["goods_type"],
                g["cartons"],  # raw number
                g["cbm"],  # raw float
                g["cbm_price_dzd"],  # raw float
                g["total_net"]  # raw float
            ])
        self.table.resize_columns_to_contents()

    def _get_goods_schema(self):
        customers = [(c["name"], c["id"]) for c in self.service.get_all_customers()]
        containers = [(f"{c['container_number']} ({c['bill_number']})", c["id"]) for c in self.logistics_service.get_all_containers()]
        return [
            {"name": "date", "label": "Date de l'opération", "type": "date", "required": True, "default": QDate.currentDate()},
            {"name": "customer_id", "label": "Client", "type": "dropdown", "options": customers, "required": True, "quick_add_callback": self._quick_add_customer},
            {"name": "container_id", "label": "Conteneur", "type": "dropdown", "options": containers, "required": True},
            {"name": "goods_type", "label": "Désignation", "type": "text", "required": True},
            {"name": "cartons", "label": "N° Cartons", "type": "number"},
            {"name": "cbm", "label": "CBM", "type": "number", "required": True},
            {"name": "cbm_price_dzd", "label": "Prix/CBM (DA)", "type": "number", "required": True},
            {"name": "discount", "label": "Remise (%)", "type": "number"},
            {"name": "notes", "label": "Notes", "type": "text"}
        ]

    def add_goods(self):
        dialog = SmartFormDialog("Nouveau Chargement Client", self._get_goods_schema(), parent=self)
        if dialog.exec():
            self.service.add_customer_goods(**dialog.get_results())
            self.load_data()

    def edit_goods(self, row_idx):
        gid = int(self.table.get_row_data(row_idx)[1])
        g = self.service.get_customer_goods_by_id(gid)
        if g:
            dialog = SmartFormDialog("Modifier Chargement", self._get_goods_schema(), data=g, parent=self)
            if dialog.exec():
                self.service.update_customer_goods(gid, **dialog.get_results())
                self.load_data()

    def delete_goods(self, row_idx):
        gid = int(self.table.get_row_data(row_idx)[1])
        if confirm_delete(self, f"ce chargement (ID: {gid})"):
            self.service.delete_customer_goods(gid)
            self.load_data()

    def _quick_add_customer(self, combo_box):
        from modules.customers.views import CUSTOMER_SCHEMA
        dialog = SmartFormDialog("Nouveau Client (Rapide)", CUSTOMER_SCHEMA, parent=self)
        if dialog.exec():
            try:
                new_customer = self.service.create_customer(**dialog.get_results())
                from components.dialogs import show_success
                show_success(self, "Succès", "Client ajouté avec succès")
                combo_box.clear()
                for c in self.service.get_all_customers():
                    combo_box.addItem(c["name"], c["id"])
                idx = combo_box.findData(new_customer.id)
                if idx >= 0: combo_box.setCurrentIndex(idx)
            except Exception as e:
                from components.dialogs import show_error
                show_error(self, "Erreur", f"Échec de l'ajout: {str(e)}")


class CustomerPaymentsTab(QWidget):
    dataChanged = pyqtSignal()  # 🔗 Signal for real-time sync

    def __init__(self, service: CustomerService, treasury_service: TreasuryService):
        super().__init__()
        self.service, self.treasury_service = service, treasury_service
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.table = EnhancedTableView(table_id="customer_payments")
        self.table.set_headers_from_schema("customer_payments")  # [GOLDEN PRINCIPLE] schema centralisé
        self.table.addClicked.connect(self.receive_payment)
        self.table.refreshClicked.connect(self.load_data)
        layout.addWidget(self.table)

    def load_data(self):
        payments = self.service.get_all_payments()
        self.table.clear_rows()
        for p in payments:
            # [GOLDEN PRINCIPLE] 2026-04-19 - Pass raw values, not formatted strings
            row_idx = self.table.add_row([
                None,
                str(p["id"]),
                p["date"],  # ISO date string
                p["customer_name"],
                p["account_name"] or "N/A",
                p["amount"],  # raw float
                p["reference"] or "",
                p["notes"] or ""
            ])
            # [CUSTOM] Couleur personnalisée pour l'historique des paiements clients
            # [WHY]: Distinction visuelle de tous les paiements avec la couleur vert
            #        émeraude foncé (#072b25) pour la lecture rapide des relevés de compte.
            # [DATE]: 2026-03-29
            self.table.set_row_background_color(row_idx, "#072b25")
        self.table.resize_columns_to_contents()

    def receive_payment(self):
        dialog = ReceivePaymentDialog(self.service, self.treasury_service, parent=self)
        if dialog.exec():
            results = dialog.get_results()
            if results:
                success, msg = self.service.receive_payment(**results)
                if success:
                    show_success(self, "Succès", msg)
                    self.load_data()
                    self.dataChanged.emit()  # 🔗 Triggers treasury refresh instantly
                else:
                    show_error(self, "Erreur", msg)

    def _quick_add_customer(self, combo_box):
        from modules.customers.views import CUSTOMER_SCHEMA
        dialog = SmartFormDialog("Nouveau Client (Rapide)", CUSTOMER_SCHEMA, parent=self)
        if dialog.exec():
            try:
                new_customer = self.service.create_customer(**dialog.get_results())
                show_success(self, "Succès", "Client ajouté avec succès")
                combo_box.clear()
                for c in self.service.get_all_customers():
                    combo_box.addItem(c["name"], c["id"])
                idx = combo_box.findData(new_customer.id)
                if idx >= 0: combo_box.setCurrentIndex(idx)
            except Exception as e:
                show_error(self, "Erreur", f"Échec de l'ajout: {str(e)}")

    def _quick_add_account(self, combo):
        from modules.treasury.views import quick_add_account
        quick_add_account(combo, self.treasury_service, parent=self)


# ============================================================================
# RECEIVE PAYMENT DIALOG
# ============================================================================

class ReceivePaymentDialog(QDialog):
    """Dialog for receiving payment from customer with balance simulation - Using BaseTransactionDialog pattern"""
    
    def __init__(self, service: CustomerService, treasury_service, parent=None):
        super().__init__(parent)
        self.service = service
        self.treasury_service = treasury_service
        self.setWindowTitle("Réception Paiement Client")
        self.setMinimumWidth(450)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)
        
        # Date
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setFixedWidth(140)
        form.addRow("Date:", self.date_input)
        
        # Customer with balance - using BaseTransactionDialog pattern
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        self.customer_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.customer_combo.lineEdit().setPlaceholderText("Rechercher un client...")

        # Load customers
        customers = self.service.get_all_customers()
        for c in customers:
            self.customer_combo.addItem(c['name'], c['id'])

        # [UNIFIED] 2026-04-08 - Add completer for search like SmartForm
        from PyQt6.QtWidgets import QCompleter
        from PyQt6.QtCore import Qt
        completer = QCompleter(self.customer_combo.model())
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.customer_combo.setCompleter(completer)
        popup = completer.popup()
        popup.setStyleSheet("""
            QListView {
                background-color: #112e2a;
                color: #e6edf3;
                border: 1px solid #214d47;
            }
            QListView::item {
                padding: 8px;
            }
            QListView::item:selected {
                background-color: #2ea043;
                color: white;
            }
            QListView::item:hover {
                background-color: #1a3d38;
            }
        """)

        # [UNIFIED] 2026-04-08 - Balance Display (Composant unifié)
        from components.balance_display import BalanceDisplay
        self.balance_display = BalanceDisplay("client")
        
        self.customer_combo.currentIndexChanged.connect(lambda idx: self.balance_display.update_from_combo(self.customer_combo, self.service))
        self.customer_widget = create_quick_add_layout(self.customer_combo, self._quick_add_customer)
        form.addRow("Client:", self.customer_widget)
        form.addRow("", self.balance_display)

        # Account with balance
        self.account_combo = QComboBox()
        accounts = self.treasury_service.get_all_accounts(currency_filter="DA")
        for a in accounts:
            self.account_combo.addItem(f"{a['name']} (Solde: {a['balance']:,.0f} DA)", a['id'])

        # [UNIFIED] 2026-04-08 - Account Balance Display (Composant unifié)
        self.account_balance_display = BalanceDisplay("account")
        self.account_combo.currentIndexChanged.connect(lambda idx: self.account_balance_display.update_from_combo(self.account_combo, self.treasury_service))
        self.account_widget = create_quick_add_layout(self.account_combo, self._quick_add_account)
        form.addRow("Compte de Versement:", self.account_widget)
        form.addRow("", self.account_balance_display)
        
        # Amount with simulation
        self.amount_input = AmountInput(currency_symbol="DA")
        self.amount_input.valueChanged.connect(self._update_simulation)
        form.addRow("Montant (DA):", self.amount_input)
        
        # [UNIFIED] 2026-04-08 - Simulation Display (Composant unifié)
        from components.simulation_display import AmountSimulationLabel
        self.sim_label = AmountSimulationLabel()
        form.addRow("", self.sim_label)
        
        # Reference
        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("N°-chèque, virement...")
        form.addRow("Référence:", self.reference_input)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText("Notes supplémentaires...")
        form.addRow("Notes:", self.notes_input)
        
        layout.addLayout(form)
        
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        
        # [UNIFIED] 2026-04-08 - Initial balance update via component
        self.balance_display.update_from_combo(self.customer_combo, self.service)
        self.account_balance_display.update_from_combo(self.account_combo, self.treasury_service)

    def _update_balance(self):
        pass  # Handled by BalanceDisplay component

    def _update_account_balance(self):
        pass  # Handled by BalanceDisplay component

    def _quick_add_customer(self, combo):
        """Quick Add client (regle 10)"""
        from modules.customers.views import CUSTOMER_SCHEMA
        dialog = SmartFormDialog("Nouveau Client", CUSTOMER_SCHEMA, parent=self)
        if dialog.exec():
            try:
                customer = self.service.create_customer(**dialog.get_results())
                if customer:
                    combo.addItem(dialog.get_results()['name'], customer.id)
                    combo.setCurrentIndex(combo.count() - 1)
            except Exception as e:
                show_error(self, "Erreur", f"Erreur lors de la creation du client: {str(e)}")

    def _quick_add_account(self, combo):
        """Quick Add compte (regle 10)"""
        from utils.constants import ACCOUNT_SCHEMA
        dialog = SmartFormDialog("Nouveau Compte", ACCOUNT_SCHEMA, parent=self)
        if dialog.exec():
            try:
                results = dialog.get_results()
                account = self.treasury_service.create_account(**results)
                if account:
                    combo.addItem(results['name'], account.id)
                    combo.setCurrentIndex(combo.count() - 1)
            except Exception as e:
                show_error(self, "Erreur", f"Erreur lors de la creation du compte: {str(e)}")

    def _update_simulation(self):
        cid = self.customer_combo.currentData()
        if not cid:
            self.sim_label.clear()
            return
        
        current_balance = self.service.get_customer_balance(cid)
        payment = self.amount_input.get_amount()
        new_balance = current_balance - payment
        
        # [UNIFIED] 2026-04-08 - Use unified simulation component
        if new_balance > 0:
            color = "#f0883e"  # Orange - still owes
            status = f"➖ Remaining: {new_balance:,.2f} DA"
        elif new_balance == 0:
            color = "#2ecc71"  # Green - paid off
            status = "✅ Soldé!"
        else:
            color = "#2ecc71"  # Green - credit (paid too much)
            status = f"✓ Credit: {abs(new_balance):,.2f} DA"
        
        self.sim_label.setText(f"💡 Après paiement: <span style='color: {color}'>{status}</span>")

    def _validate_and_accept(self):
        if not self.customer_combo.currentData():
            show_error(self, "Erreur", "Veuillez sélectionner un client")
            return
        if self.amount_input.get_amount() <= 0:
            show_error(self, "Erreur", "Le montant doit être supérieur à 0")
            return
        if not self.account_combo.currentData():
            show_error(self, "Erreur", "Veuillez sélectionner un compte")
            return
        self.accept()

    def get_results(self):
        if not self.result():
            return None
        return {
            "date": datetime.combine(self.date_input.date().toPyDate(), datetime.now().time()),
            "customer_id": self.customer_combo.currentData(),
            "account_id": self.account_combo.currentData(),
            "amount": self.amount_input.get_amount(),
            "reference": self.reference_input.text().strip() or None,
            "notes": self.notes_input.toPlainText().strip() or None
        }


class CustomerCostsTab(QWidget):
    dataChanged = pyqtSignal()  # 🔗 Signal for real-time sync

    def __init__(self, service: CustomerService):
        super().__init__()
        self.service = service
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.table = EnhancedTableView(table_id="customer_costs")
        self.table.set_headers_from_schema("customer_costs")  # [GOLDEN PRINCIPLE] schema centralisé
        self.table.addClicked.connect(self.add_cost)
        self.table.editClicked.connect(self.edit_cost)
        self.table.deleteClicked.connect(self.delete_cost)
        self.table.refreshClicked.connect(self.load_data)
        layout.addWidget(self.table)

    def load_data(self):
        costs = self.service.get_all_side_costs()
        self.table.clear_rows()
        for c in costs:
            # [GOLDEN PRINCIPLE] 2026-04-19 - Pass raw values, not formatted strings
            self.table.add_row([
                None,
                str(c["id"]),
                c["date"],  # ISO date string
                c["customer_name"],
                c["cost_type_name"] or "N/A",
                c["amount"],  # raw float
                c["notes"] or ""
            ])
        self.table.resize_columns_to_contents()

    def _get_cost_schema(self):
        customers = [(c["name"], c["id"]) for c in self.service.get_all_customers()]
        cost_types = [(t["name"], t["id"]) for t in self.service.get_all_cost_types()]
        
        # [CUSTOM] Add cost type quick add callback
        # [WHY]: Following GOLDEN_RULES - same pattern as customer quick add
        # [DATE]: 2026-04-04
        def on_quick_add_type(combo_box):
            from components.catalog_dialog import GenericCatalogDialog
            dialog = GenericCatalogDialog(
                title="Types de Charges Client",
                get_data_func=lambda include_inactive=False: [{"id": t['id'], "name": t['name']} for t in self.service.get_all_cost_types()],
                create_data_func=lambda name, desc: self.service.create_cost_type(name, desc),
                delete_data_func=lambda tid: self.service.delete_cost_type(tid),
                restore_data_func=lambda tid: self.service.restore_cost_type(tid),
                primary_placeholder="Nom du type de charge",
                secondary_placeholder="Description (optionnel)",
                headers=["N°", "ID", "Type de Charge"],
                parent=self
            )
            dialog.exec()
            # Refresh combo
            combo_box.clear()
            new_types = self.service.get_all_cost_types()
            for t in new_types:
                combo_box.addItem(t['name'], t['id'])
            if new_types:
                combo_box.setCurrentIndex(len(new_types) - 1)
        
        return [
            {"name": "date", "label": "Date de l'opération", "type": "date", "required": True, "default": QDate.currentDate()},
            {"name": "customer_id", "label": "Client", "type": "dropdown", "options": customers, "required": True, "quick_add_callback": self._quick_add_customer},
            {"name": "cost_type_id", "label": "Type de Frais", "type": "dropdown", "options": cost_types, "required": True, "quick_add_callback": on_quick_add_type},
            {"name": "amount", "label": "Montant (DA)", "type": "number", "required": True, "validation": {"min": 0.01}},
            {"name": "notes", "label": "Notes", "type": "text"}
        ]

    def add_cost(self):
        dialog = SmartFormDialog("Ajouter Charge Client", self._get_cost_schema(), parent=self)
        if dialog.exec(): self.service.add_side_cost(**dialog.get_results()); self.load_data()

    def edit_cost(self, row_idx):
        cid = int(self.table.get_row_data(row_idx)[1])
        cost = self.service.get_side_cost(cid)
        if cost:
            dialog = SmartFormDialog("Modifier Charge Client", self._get_cost_schema(), data=cost, parent=self)
            if dialog.exec(): self.service.update_side_cost(cid, **dialog.get_results()); self.load_data()

    def delete_cost(self, row_idx):
        cid = int(self.table.get_row_data(row_idx)[1])
        if confirm_delete(self, f"ce frais (ID: {cid})"):
            with self.service.side_cost_repo.get_session() as s:
                self.service.side_cost_repo.soft_delete(s, cid)
                s.commit()
                self.load_data()

    def _quick_add_customer(self, combo_box):
        from modules.customers.views import CUSTOMER_SCHEMA
        dialog = SmartFormDialog("Nouveau Client (Rapide)", CUSTOMER_SCHEMA, parent=self)
        if dialog.exec():
            try:
                new_customer = self.service.create_customer(**dialog.get_results())
                from components.dialogs import show_success
                show_success(self, "Succès", "Client ajouté avec succès")
                combo_box.clear()
                for c in self.service.get_all_customers():
                    combo_box.addItem(c["name"], c["id"])
                idx = combo_box.findData(new_customer.id)
                if idx >= 0: combo_box.setCurrentIndex(idx)
            except Exception as e:
                from components.dialogs import show_error
                show_error(self, "Erreur", f"Échec de l'ajout: {str(e)}")


class CustomerLedgerTab(QWidget):
    def __init__(self, service: CustomerService):
        super().__init__(); self.service = service; self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        hbox = QHBoxLayout(); hbox.addWidget(QLabel("Client:")); self.combo_customer = QComboBox()
        self.combo_customer.currentIndexChanged.connect(self.load_data); hbox.addWidget(self.combo_customer); hbox.addStretch()
        layout.addLayout(hbox)
        self.table = EnhancedTableView(table_id="customer_ledger")
        self.table.set_headers_from_schema("customer_ledger")  # [GOLDEN PRINCIPLE] schema centralisé
        layout.addWidget(self.table)
        self.refresh_customers()

    def refresh_customers(self):
        self.combo_customer.blockSignals(True); self.combo_customer.clear()
        for c in self.service.get_all_customers(): self.combo_customer.addItem(c["name"], c["id"])
        self.combo_customer.blockSignals(False); self.load_data()

    def load_data(self):
        cid = self.combo_customer.currentData()
        if not cid: self.table.clear_rows(); return
        ledger = self.service.get_customer_ledger(cid)
        self.table.clear_rows()
        for item in ledger:
            is_payment = item["type"] == "PAIEMENT"
            # [GOLDEN PRINCIPLE] 2026-04-19 - Pass raw values, not formatted strings
            row_idx = self.table.add_row([
                None,
                str(item["id"]),
                item["date"],  # ISO date string
                item["type"],
                item["desc"],
                item["debit"],  # raw float
                item["credit"],  # raw float
                item["balance"]  # raw float
            ])
            # [CUSTOM] Coloration du relevé de compte client
            # [WHY]: Distinction visuelle: Paiements (Vert #072b25) / Factures (Rouge #2b0707)
            #        pour la lecture rapide des relevés de compte.
            # [DATE]: 2026-03-29
            self.table.set_row_background_color(row_idx, "#072b25" if is_payment else "#2b0707")
        self.table.resize_columns_to_contents()
