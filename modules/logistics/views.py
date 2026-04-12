"""
Vues pour le module Logistique & Traitements
Standardized & Purified
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTabWidget, QDialog, QFormLayout,
    QLineEdit, QComboBox, QDateEdit, QTextEdit,
    QDialogButtonBox, QMessageBox, QGroupBox,
    QSpinBox, QDoubleSpinBox, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor, QStandardItem
from datetime import datetime

from components.enhanced_table import EnhancedTableView
from components.amount_input import AmountInput
from components.smart_form import SmartFormDialog
from components.dialogs import (
    show_error, show_success, confirm_delete, confirm_action,
    create_quick_add_layout
)
from utils.formatters import format_amount, format_date
from utils.constants import (
    PAYMENT_TYPE_CASH, PAYMENT_TYPE_CREDIT,
    SUPPLIER_TYPE_LICENSE, SUPPLIER_TYPE_SHIPPING,
    DEFAULT_CURRENCY_CODE, DEFAULT_CURRENCY_NAME, DEFAULT_CURRENCY_SYMBOL
)
from modules.currency.views import SuppliersTab

from .service import LogisticsService
from .expense_service import ExpenseService
from modules.currency.service import CurrencyService
from modules.treasury.service import TreasuryService
from modules.settings.service import SettingsService
from modules.customers.service import CustomerService
from core.database import get_session

# ============================================================================
# SCHEMAS
# ============================================================================

LICENSE_SCHEMA = [
    {'name': 'date', 'label': "Date d'achat", 'type': 'date', 'required': True},
    {'name': 'supplier_id', 'label': "Titulaire", 'type': 'dropdown', 'options': [], 'required': True},
    {'name': 'license_type', 'label': "Type de marchandise", 'type': 'dropdown', 'options': []},
    {'name': 'total_usd', 'label': 'Montant Total (USD)', 'type': 'number', 'required': True},
    {'name': 'total_dzd', 'label': 'Prix Total Facture (DA)', 'type': 'number', 'required': True, 'placeholder': 'Prix payé pour le traitement'},
    {'name': 'commission_rate', 'label': '% Commission Dédouanement', 'type': 'number', 'default': 30.0, 'placeholder': 'Ex: 30.0'},
    {'name': 'notes', 'label': 'Notes', 'type': 'text'},
]

EXPENSE_TYPE_SCHEMA = [
    {'name': 'name', 'label': 'Nom du type de frais', 'type': 'text', 'required': True},
]

# ============================================================================
# MAIN VIEW
# ============================================================================

class LogisticsView(QWidget):
    """Vue principale du module Logistique (Standardized)"""
    dataChanged = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.service = LogisticsService()
        self.expense_service = ExpenseService()
        self.currency_service = CurrencyService()
        self.treasury_service = TreasuryService()
        self.settings_service = SettingsService()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        self.agents_tab = SuppliersTab(self.currency_service, self.treasury_service, self.settings_service, supplier_type_filter=SUPPLIER_TYPE_SHIPPING)
        self.agents_tab.dataChanged.connect(self.dataChanged.emit)
        self.tabs.addTab(self.agents_tab, "Agents")

        self.agent_payments_tab = AgentPaymentsTab(self.currency_service, self.treasury_service)
        self.agent_payments_tab.dataChanged.connect(self.dataChanged.emit)
        self.tabs.addTab(self.agent_payments_tab, "Paiements")

        self.containers_tab = ContainersTab(self.service, self.settings_service, self.currency_service)
        self.containers_tab.dataChanged.connect(self.dataChanged.emit)
        self.tabs.addTab(self.containers_tab, "Factures")

        from modules.customers.service import CustomerService
        self.customer_service = CustomerService()
        self.expenses_tab = ExpensesTab(self.expense_service, self.service, self.currency_service, self.treasury_service, self.settings_service, self.customer_service)
        self.expenses_tab.dataChanged.connect(self.dataChanged.emit)
        self.tabs.addTab(self.expenses_tab, "Dépenses")
        
    def refresh(self):
        self.agents_tab.load_data()
        self.agent_payments_tab.load_data()
        self.containers_tab.load_data()
        self.expenses_tab.load_data()


# ============================================================================
# AGENT PAYMENTS TAB
# ============================================================================

class AgentPaymentDialog(QDialog):
    """Dialogue de paiement d'un agent maritime (uniquement SHIPPING)"""
    dataSaved = pyqtSignal()

    def __init__(self, currency_service: CurrencyService, treasury_service: TreasuryService, parent=None):
        super().__init__(parent)
        self.currency_service = currency_service
        self.treasury_service = treasury_service
        self.setWindowTitle("Payer Dette Agent Maritime")
        self.setMinimumWidth(450)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.agent_combo = QComboBox()
        form.addRow("Agent Maritime:", self.agent_combo)

        self.account_combo = QComboBox()
        form.addRow("Compte Devise:", self.account_combo)

        self.amount_input = AmountInput()
        form.addRow("Montant payé:", self.amount_input)

        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("Référence du paiement...")
        form.addRow("Référence:", self.ref_input)

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Notes...")
        form.addRow("Notes:", self.notes_input)

        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._on_save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _load_data(self):
        agents = self.currency_service.get_all_suppliers(supplier_type=SUPPLIER_TYPE_SHIPPING)
        for a in agents:
            bal = format_amount(a.get('balance', 0), 'DA')
            self.agent_combo.addItem(f"{a['name']} ({bal})", a['id'])

        accounts = self.treasury_service.get_all_accounts(currency_filter="FOREIGN")
        for acc in accounts:
            bal = format_amount(acc['balance'], acc['currency_symbol'])
            self.account_combo.addItem(f"{acc['name']} ({bal})", acc['id'])

    def _on_save(self):
        agent_id = self.agent_combo.currentData()
        account_id = self.account_combo.currentData()
        amount = self.amount_input.get_amount()

        if not agent_id:
            return show_error(self, "Erreur", "Sélectionnez un agent")
        if not account_id:
            return show_error(self, "Erreur", "Sélectionnez un compte")
        if amount <= 0:
            return show_error(self, "Erreur", "Montant invalide")

        success, msg, _ = self.currency_service.pay_supplier(
            supplier_id=agent_id,
            account_id=account_id,
            amount=amount,
            reference=self.ref_input.text(),
            notes=self.notes_input.text()
        )
        if success:
            show_success(self, "Succès", msg)
            self.dataSaved.emit()
            self.accept()
        else:
            show_error(self, "Erreur", msg)


class AgentPaymentsTab(QWidget):
    """Historique des paiements effectués aux agents maritimes (SHIPPING)"""
    dataChanged = pyqtSignal()

    def __init__(self, currency_service: CurrencyService, treasury_service: TreasuryService):
        super().__init__()
        self.currency_service = currency_service
        self.treasury_service = treasury_service
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.table = EnhancedTableView(table_id="agent_payments")
        self.table.set_headers(["N°", "ID", "Date", "Agent", "Montant", "Compte", "Référence"])
        self.table.addClicked.connect(self._new_payment)
        self.table.refreshClicked.connect(self.load_data)
        layout.addWidget(self.table)

    def load_data(self):
        agents = self.currency_service.get_all_suppliers(supplier_type=SUPPLIER_TYPE_SHIPPING)
        agent_ids = [a['id'] for a in agents]
        agent_names = {a['id']: a['name'] for a in agents}

        payments = self.currency_service.get_supplier_payments_history()

        self.table.clear_rows()
        for p in payments:
            if p['id'] and p.get('supplier_name', '') in agent_names.values():
                self.table.add_row([
                    None,
                    str(p['id']),
                    format_date(p['date']),
                    p.get('supplier_name', ''),
                    format_amount(p['amount'], p.get('currency_symbol', '')),
                    p.get('account_name', ''),
                    p.get('reference', '')
                ])
        self.table.resize_columns_to_contents()

    def _is_shipping_payment(self, payment, agent_ids, agent_names):
        """Vérifie si le paiement concerne un agent maritime"""
        return payment.get('supplier_name', '') in agent_names.values()

    def _new_payment(self):
        dialog = AgentPaymentDialog(self.currency_service, self.treasury_service, self)
        if dialog.exec():
            self.load_data()
            self.dataChanged.emit()


# ============================================================================
# LICENSES TAB
# ============================================================================

class LicensesTab(QWidget):
    dataChanged = pyqtSignal()
    
    def __init__(self, service: LogisticsService, currency_service: CurrencyService, 
                 treasury_service: TreasuryService, settings_service: SettingsService):
        super().__init__()
        self.service = service
        self.currency_service = currency_service
        self.treasury_service = treasury_service
        self.settings_service = settings_service
        self._setup_ui()
        self.load_data()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.table = EnhancedTableView(table_id="logistics_licenses")
        self.table.set_headers([
            "N°", "ID", "Date", "Titulaire", 
            "Global ($)", "Valeur (DA)", 
            "Utilisé ($)", "Restant ($)", 
            "PRIX Consommé (DA)", "% Comm.", 
            "Total Versé (DA)", "Total Dû (DA)", "Reste (DA)",
            "Total Domiciliations", "Total Taxs", "Total Versements", "Total Du",
            "Notes"
        ])

        # Actions Standard
        self.table.addClicked.connect(self.add_license)
        self.table.editClicked.connect(self.edit_license)
        self.table.deleteClicked.connect(self.delete_license)
        self.table.restoreClicked.connect(self.restore_license)
        self.table.refreshClicked.connect(self.load_data)
        self.table.status_filter.statusChanged.connect(self.load_data)

        # Actions Spécifiques
        self.table.add_action_button("Payer Dette", "💵", self.pay_supplier)

        layout.addWidget(self.table)
        
    def load_data(self):
        filter_status = self.table.status_filter.get_filter()
        self.table.update_actions_for_status(filter_status)

        licenses = self.service.get_all_licenses(filter_status=filter_status)
        self.table.clear_rows()

        for lic in licenses:
            # 1. Get Base Data
            global_usd = lic.get('total_usd', 0)
            valeur_dzd = lic.get('total_dzd', 0)
            utilise_usd = lic.get('used_usd', 0)
            
            # 2. Calculations (Simulation Logic)
            # Ratio = Valeur (DA) / Global ($)
            ratio = (valeur_dzd / global_usd) if global_usd > 0 else 0
            
            # PRIX Consommé (DA) = Utilisé ($) * Ratio
            prix_consomme = utilise_usd * ratio
            
            # Restant ($)
            restant_usd = global_usd - utilise_usd
            
            # Commission %
            commission_pct = lic.get('commission_rate', 0)
            
            # Mock Financials (Will be replaced by actual logic later)
            total_vers = 0 # Placeholder
            total_du = prix_consomme # Simplified for now (until TAX module is added)
            reste_a_payer = total_du - total_vers

            row_idx = self.table.add_row([
                None,  # N°
                str(lic['id']),
                format_date(lic['date']),
                lic['supplier_name'],
                format_amount(global_usd, "$"),
                format_amount(valeur_dzd, "DA"),
                format_amount(utilise_usd, "$"),
                format_amount(restant_usd, "$"),
                format_amount(prix_consomme, "DA"),
                f"{commission_pct}%",
                format_amount(total_vers, "DA"),
                format_amount(total_du, "DA"),
                format_amount(reste_a_payer, "DA"),
                format_amount(lic.get('total_domiciliations', 0), "DA"),
                format_amount(lic.get('total_taxes', 0), "DA"),
                format_amount(lic.get('total_versements', 0), "DA"),
                format_amount(lic.get('total_du', 0), "DA"),
                lic.get('notes', '')
            ], is_active=lic['is_active'])

            # Coloring Logic
            if lic['is_active']:
                if restant_usd > 0:
                    self.table.set_row_background_color(row_idx, "#072b25") # Green/Active
                else:
                    self.table.set_row_background_color(row_idx, "#2b0707") # Red/Consumed
            else:
                self.table.set_row_background_color(row_idx, "#1a1a1a") # Archived

        self.table.resize_columns_to_contents()
        
    def add_license(self):
        self._show_license_dialog()

    def edit_license(self, row_idx):
        lic_id = int(self.table.get_row_data(row_idx)[1])
        self._show_license_dialog(lic_id)

    def _show_license_dialog(self, edit_id=None):
        suppliers = self.currency_service.get_all_suppliers(supplier_type=SUPPLIER_TYPE_LICENSE)
        supp_options = [(s['name'], s['id']) for s in suppliers]
        
        def on_add_owner(combo):
            from modules.currency.views import run_supplier_dialog
            success, message, new_id = run_supplier_dialog(self.currency_service, SUPPLIER_TYPE_LICENSE, parent=self)
            if success:
                new_supps = self.currency_service.get_all_suppliers(supplier_type=SUPPLIER_TYPE_LICENSE)
                combo.clear()
                for s in new_supps:
                    combo.addItem(s['name'], s['id'])
                combo.setCurrentIndex(combo.count() - 1)
        
        schema = []
        def on_add_goods_type(combo):
            from components.catalog_dialog import GenericCatalogDialog
            dialog = GenericCatalogDialog(
                title="Catalogue des Types de Marchandises",
                get_data_func=self.currency_service.get_all_license_goods,
                create_data_func=self.currency_service.create_license_goods,
                edit_data_func=self.currency_service.update_license_goods,
                delete_data_func=self.currency_service.delete_license_goods,
                restore_data_func=self.currency_service.restore_license_goods,
                primary_placeholder="Nom du type de marchandise (ex: Chaussures...)",
                secondary_placeholder="Description (optionnel)",
                headers=["N°", "ID", "Nom", "Description"],
                parent=self
            )
            dialog.exec()
            # Rafraichir les options du dropdown
            goods_types = self.currency_service.get_all_license_goods()
            combo.clear()
            for g in goods_types:
                combo.addItem(g['name'], g['id'])
        
        goods_types = self.currency_service.get_all_license_goods()
        goods_options = [(g['name'], g['id']) for g in goods_types]
        
        for field in LICENSE_SCHEMA:
            f = field.copy()
            if f['name'] == 'supplier_id': 
                f['options'] = supp_options
                f['quick_add_callback'] = on_add_owner
            elif f['name'] == 'license_type':
                f['options'] = goods_options
                f['quick_add_callback'] = on_add_goods_type
            schema.append(f)

        initial_data = {}
        if edit_id:
            all_lic = self.service.get_all_licenses()
            lic = next((l for l in all_lic if l['id'] == edit_id), None)
            if lic: initial_data = lic

        dialog = SmartFormDialog("Modifier Licence" if edit_id else "Nouvel Achat de Licence", schema, initial_data, parent=self)
        if dialog.exec():
            results = dialog.get_results()
            if edit_id:
                results.pop('supplier_id', None)
                success, message = self.service.update_license(edit_id, **results)
            else:
                success, message, _ = self.service.create_license(**results)
            
            if success:
                show_success(self, "Succès", message)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", message)

    def delete_license(self, row_idx):
        lic_id = int(self.table.get_row_data(row_idx)[1])
        if confirm_action(self, "Confirmer l'archivage", "Voulez-vous vraiment archiver cette licence ?"):
            success, msg = self.service.delete_license(lic_id)
            if success:
                show_success(self, "Succès", msg)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", msg)

    def restore_license(self, row_idx):
        lic_id = int(self.table.get_row_data(row_idx)[1])
        if confirm_action(self, "Confirmer la restauration", "Voulez-vous réactiver cette licence ?"):
            success, msg = self.service.restore_license(lic_id)
            if success:
                show_success(self, "Succès", msg)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", msg)

    def pay_supplier(self):
        selected = self.table.get_selected_rows()
        if not selected: return show_error(self, "Erreur", "Sélectionnez une licence")
            
        lic_id = int(self.table.get_row_data(selected[0])[1])
        all_lic = self.service.get_all_licenses()
        lic = next((l for l in all_lic if l['id'] == lic_id), None)
        if not lic: return
        
        from modules.currency.views import SupplierPaymentDialog
        dialog = SupplierPaymentDialog(self.currency_service, self.treasury_service, supplier_id=lic['supplier_id'], supplier_name=lic['supplier_name'], parent=self)
        if dialog.exec():
            self.load_data()
            self.dataChanged.emit()


# ============================================================================
# CONTAINERS TAB
# ============================================================================

class ContainersTab(QWidget):
    dataChanged = pyqtSignal()
    
    def __init__(self, service: LogisticsService, settings_service: SettingsService, currency_service: CurrencyService):
        super().__init__()
        self.service = service
        self.settings_service = settings_service
        self.currency_service = currency_service
        self._setup_ui()
        self.load_data()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.table = EnhancedTableView(table_id="logistics_containers")
        self.table.set_headers([
            "N°", "ID", "Date", "N° BILL", "N° Facture", "Agent", "Licence",
            "Conteneurs", "Clients", "Total CBM", "Total Cartons",
            "Montant (USD)", "Taux", "Taux Exp", "Eq. Expedition (DA)", "Port", "Transitaire",
            "Shipping", "Licence", "Tax", "Pourcentage", "Charge DA", "Charge Port", "Surestarie"
        ], align_map={2: 'text'}) # Index 2 is Date, force text alignment to prevent summing
        # Temporarily show all columns for review
        # self.table.hide_column(1)
        # self.table.hide_column(6)

        # Actions
        self.table.addClicked.connect(self._open_new_file)
        self.table.editClicked.connect(self.edit_container)
        self.table.deleteClicked.connect(self.delete_container)
        self.table.restoreClicked.connect(self.restore_container)
        self.table.refreshClicked.connect(self.load_data)
        self.table.status_filter.statusChanged.connect(self.load_data)
        self.table.add_action_button("Détails", "", self._view_details)
        self.table.add_action_button("Réception", "", self._receive_in_warehouse)
        layout.addWidget(self.table)

    def _view_details(self):
        """Afficher les détails d'une facture sélectionnée"""
        selected = self.table.get_selected_rows()
        if not selected:
            return show_error(self, "Erreur", "Sélectionnez une facture.")
        row_data = self.table.get_row_data(selected[0])
        bill = row_data[3]
        containers = self.service.get_all_containers(filter_status="all")
        bill_containers = [c for c in containers if c.get('bill_number') == bill]
        details = f"Facture: {bill}\n\n"
        for c in bill_containers:
            details += f"  Conteneur: {c['container_number']} | CBM: {c['cbm']:.2f} | Cartons: {c['cartons']}\n"
        QMessageBox.information(self, f"Détails - {bill}", details)
    
    def _receive_in_warehouse(self):
        """استلام الحاوية في المخزن مع عرض بيانات الشحنة الأصلية"""
        selected = self.table.get_selected_rows()
        if not selected:
            return show_error(self, "Erreur", "Sélectionnez une facture.")
        
        row_data = self.table.get_row_data(selected[0])
        container_id = int(row_data[1])
        
        goods = self.service.get_container_goods(container_id)
        
        if not goods:
            return show_error(self, "Erreur", "Aucune marchandise trouvée")
        
        from modules.warehouse.service import WarehouseService
        warehouse_service = WarehouseService()
        warehouses = warehouse_service.get_all_warehouses()
        
        if not warehouses:
            return show_error(self, "Erreur", "Aucun entrepôt disponible")
        
        warehouse_options = [(w['name'], w['id']) for w in warehouses]
        
        dialog = ReceiveWarehouseDialog(container_id, goods, warehouse_options, self)
        
        if dialog.exec():
            data = dialog.get_results()
            if data:
                success, msg, count = warehouse_service.receive_goods_from_container(
                    container_id, data['warehouse_id'], data['received_data']
                )
                
                if success:
                    self.service.update_container_warehouse_info(
                        container_id, data['warehouse_id'], 'RECEIVED', data['received_data']
                    )
                    show_success(self, "Succès", msg)
                    self.load_data()
                else:
                    show_error(self, "Erreur", msg)

    def load_data(self):
        filter_status = self.table.status_filter.get_filter()
        self.table.update_actions_for_status(filter_status)

        containers = self.service.get_all_containers(filter_status=filter_status)

        bills = {}
        for c in containers:
            bill = c.get('bill_number', 'Sans BILL')
            if bill not in bills:
                bills[bill] = {
                    'id': c['id'],
                    'date': c['date_opened'],
                    'bill': bill,
                    'invoice': c.get('invoice_number', ''),
                    'agent': c.get('supplier_name', ''),
                    'license': f"#{c.get('license_id', '')}",
                    'containers': [],
                    'container_count': 0,
                    'customer_ids': set(),  # Track unique customer IDs
                    'total_cbm': 0,
                    'total_cartons': 0,
                    'total_usd': 0,
                    'taux': c.get('taux', 0),
                    'taux_expedition': c.get('taux_expedition', 0),
                    'equivalent_dzd': c.get('equivalent_dzd', 0),
                    'equivalent_expedition': c.get('equivalent_expedition', 0),
                    'port': c.get('discharge_port', ''),
                    'transitaire': c.get('transitaire', ''),
                    'is_active': c['is_active']
                }
            bills[bill]['containers'].append(c['container_number'])
            bills[bill]['container_count'] += 1
            if c.get('customer_id'):
                bills[bill]['customer_ids'].add(c['customer_id'])
            bills[bill]['total_cbm'] += c.get('cbm', 0)
            bills[bill]['total_cartons'] += c.get('cartons', 0)
            bills[bill]['total_usd'] += c.get('used_usd_amount', 0)
            if not c['is_active']:
                bills[bill]['is_active'] = False

        self.table.clear_rows()
        for bill_key, b in bills.items():
            row_idx = self.table.add_row([
                None,
                str(b['id']),
                format_date(b['date']),
                b['bill'],
                b['invoice'],
                b['agent'],
                b['license'],
                str(b['container_count']),
                str(len(b['customer_ids'])),  # Now showing actual count
                f"{b['total_cbm']:.2f}",
                str(b['total_cartons']),
                format_amount(b['total_usd'], "$"),
                f"{b['taux']:.2f}" if b['taux'] else "",
                f"{b['taux_expedition']:.2f}" if b['taux_expedition'] else "",
                format_amount(b['equivalent_expedition'], "DA") if b['equivalent_expedition'] else "",
                b['port'],
                b['transitaire'],
                "",  # Shipping
                "",  # Licence
                "",  # Tax
                "",  # Pourcentage
                "",  # Charge DA
                "",  # Charge Port
                ""   # Surestarie
            ], is_active=b['is_active'])
        self.table.resize_columns_to_contents()

    def delete_container(self, row_idx):
        container_id = int(self.table.get_row_data(row_idx)[1])
        if confirm_action(self, "Confirmer l'archivage", "Voulez-vous vraiment archiver ce dossier conteneur ?"):
            success, msg = self.service.delete_container(container_id)
            if success:
                show_success(self, "Succès", msg)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", msg)

    def restore_container(self, row_idx):
        container_id = int(self.table.get_row_data(row_idx)[1])
        if confirm_action(self, "Confirmer la restauration", "Voulez-vous réactiver ce dossier conteneur ?"):
            success, msg = self.service.restore_container(container_id)
            if success:
                show_success(self, "Succès", msg)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", msg)

    def edit_container(self, row_idx):
        container_id = int(self.table.get_row_data(row_idx)[1])
        from modules.customers.service import CustomerService
        from modules.treasury.service import TreasuryService
        from .shipment_wizard import ShipmentWizard
        dialog = ShipmentWizard(
            self.service,
            self.currency_service,
            TreasuryService(),
            CustomerService(),
            edit_container_id=container_id,
            parent=self
        )
        if dialog.exec():
            self.load_data()
            self.dataChanged.emit()
        
    def edit_customs(self):
        selected = self.table.get_selected_rows()
        if not selected: return show_error(self, "Erreur", "Sélectionnez un conteneur")
            
        row_data = self.table.get_row_data(selected[0])
        container_id = int(row_data[1])
        val_dzd = float(row_data[12].replace("DA", "").replace(",", "").strip())
        
        dialog = CustomsDialog(container_id, val_dzd, parent=self)
        if dialog.exec():
            success, message = self.service.update_customs_data(container_id, dialog.get_value())
            if success:
                show_success(self, "Succès", message)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", message)

    def _open_new_file(self):
        from modules.customers.service import CustomerService
        from modules.treasury.service import TreasuryService
        from .shipment_wizard import ShipmentWizard
        dialog = ShipmentWizard(
            self.service,
            self.currency_service,
            TreasuryService(),
            CustomerService(),
            parent=self
        )
        if dialog.exec():
            self.load_data()
            self.dataChanged.emit()


# ============================================================================
# OPEN BILL DIALOG (Ouvrir/Modifier un dossier conteneur)
# ============================================================================

class OpenBillDialog(QDialog):
    """Dialogue pour ouvrir ou modifier un dossier conteneur"""
    def __init__(self, service: LogisticsService, edit_data=None, parent=None):
        super().__init__(parent)
        self.service = service
        self.edit_data = edit_data
        self.setWindowTitle("Modifier Dossier" if edit_data else "Ouvrir un Nouveau Dossier")
        self.setMinimumWidth(550)
        self._setup_ui()
        self._load_data()
        if edit_data:
            self._load_edit_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Licence
        self.license_combo = QComboBox()
        form.addRow("Licence:", self.license_combo)

        # Numéros de conteneur
        self.container_input = QLineEdit()
        self.container_input.setPlaceholderText("Ex: MSKU1234567, MRKU7654321 (séparés par virgule)")
        form.addRow("N° Conteneur(s):", self.container_input)

        # Montant total USD
        self.amount_input = AmountInput()
        form.addRow("Montant Total (USD):", self.amount_input)

        # BILL
        self.bill_input = QLineEdit()
        self.bill_input.setPlaceholderText("N° de BILL...")
        form.addRow("N° BILL:", self.bill_input)

        # Facture
        self.invoice_input = QLineEdit()
        self.invoice_input.setPlaceholderText("N° de facture...")
        form.addRow("N° Facture:", self.invoice_input)

        # Agent maritime
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("Aucun", None)
        form.addRow("Agent Maritime:", self.supplier_combo)

        # Transitaire
        self.transitaire_input = QLineEdit()
        self.transitaire_input.setPlaceholderText("Nom du transitaire...")
        form.addRow("Transitaire:", self.transitaire_input)

        # Type de marchandise
        self.products_input = QLineEdit()
        self.products_input.setPlaceholderText("Ex: Chaussures, Vêtements...")
        form.addRow("Marchandise:", self.products_input)

        # CBM
        self.cbm_input = AmountInput()
        form.addRow("CBM:", self.cbm_input)

        # Cartons
        self.cartons_input = AmountInput()
        form.addRow("Cartons:", self.cartons_input)

        # Port de déchargement
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Ex: Alger, Oran...")
        form.addRow("Port Déchargement:", self.port_input)

        # Dates
        self.shipping_date = QDateEdit()
        self.shipping_date.setCalendarPopup(True)
        self.shipping_date.setDate(QDate.currentDate())
        self.shipping_date.setFixedWidth(140)
        form.addRow("Date Expédition:", self.shipping_date)

        self.arrival_date = QDateEdit()
        self.arrival_date.setCalendarPopup(True)
        self.arrival_date.setDate(QDate.currentDate().addDays(30))
        self.arrival_date.setFixedWidth(140)
        form.addRow("Arrivée Prévue:", self.arrival_date)

        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        form.addRow("Notes:", self.notes_input)

        layout.addLayout(form)

        # Boutons
        btns = QHBoxLayout()
        btn_save = QPushButton("Enregistrer")
        btn_save.setStyleSheet("padding: 12px 24px; font-weight: bold; background-color: #238636; color: white;")
        btn_save.clicked.connect(self._on_save)
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setStyleSheet("padding: 12px 24px;")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_save)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    def _load_data(self):
        licenses = self.service.get_all_licenses(filter_status="active")
        for lic in licenses:
            remaining = lic['remaining_usd']
            label = f"{lic['supplier_name']} ({remaining:.2f} $ restant)"
            self.license_combo.addItem(label, lic['id'])

        from modules.currency.service import CurrencyService
        from utils.constants import SUPPLIER_TYPE_SHIPPING
        cs = CurrencyService()
        agents = cs.get_all_suppliers(supplier_type=SUPPLIER_TYPE_SHIPPING)
        for a in agents:
            self.supplier_combo.addItem(a['name'], a['id'])

    def _load_edit_data(self):
        d = self.edit_data
        idx = self.license_combo.findData(d.license_id)
        if idx >= 0:
            self.license_combo.setCurrentIndex(idx)
            self.license_combo.setEnabled(False)

        self.container_input.setText(d.container_number)
        self.container_input.setEnabled(False)
        self.amount_input.setValue(d.used_usd_amount)
        self.bill_input.setText(d.bill_number or "")
        self.invoice_input.setText(d.invoice_number or "")

        idx = self.supplier_combo.findData(d.shipping_supplier_id)
        if idx >= 0:
            self.supplier_combo.setCurrentIndex(idx)

        self.transitaire_input.setText(d.transitaire or "")
        self.products_input.setText(d.products_type or "")
        self.cbm_input.setValue(d.cbm)
        self.cartons_input.setValue(d.cartons)
        self.port_input.setText(d.discharge_port or "")
        self.notes_input.setText(d.notes or "")

        if hasattr(d, 'shipping_date') and d.shipping_date:
            self.shipping_date.setDate(QDate(d.shipping_date))
        if hasattr(d, 'expected_arrival_date') and d.expected_arrival_date:
            self.arrival_date.setDate(QDate(d.expected_arrival_date))

    def _on_save(self):
        license_id = self.license_combo.currentData()
        container_text = self.container_input.text().strip()
        amount = self.amount_input.get_amount()

        if not license_id:
            return show_error(self, "Erreur", "Sélectionnez une licence.")
        if not container_text:
            return show_error(self, "Erreur", "Entrez au moins un numéro de conteneur.")
        if amount <= 0:
            return show_error(self, "Erreur", "Le montant doit être supérieur à zéro.")
        self.accept()

    def get_data(self):
        """Retourne les données pour le service"""
        container_text = self.container_input.text().strip()
        containers = [c.strip() for c in container_text.split(",") if c.strip()]

        if self.edit_data:
            return {
                "container_number": containers[0] if containers else "",
                "used_usd": self.amount_input.get_amount(),
                "shipping_supplier_id": self.supplier_combo.currentData(),
                "bill_number": self.bill_input.text().strip(),
                "products_type": self.products_input.text().strip(),
                "discharge_port": self.port_input.text().strip(),
                "shipping_date": datetime.combine(self.shipping_date.date().toPyDate(), datetime.now().time()) if self.shipping_date.date().isValid() else None,
                "expected_arrival_date": datetime.combine(self.arrival_date.date().toPyDate(), datetime.now().time()) if self.arrival_date.date().isValid() else None,
                "cbm": self.cbm_input.get_amount(),
                "cartons": int(self.cartons_input.get_amount()),
                "transitaire": self.transitaire_input.text().strip(),
                "notes": self.notes_input.toPlainText().strip()
            }
        else:
            return {
                "license_id": self.license_combo.currentData(),
                "container_numbers": containers,
                "total_usd_amount": self.amount_input.get_amount(),
                "bill_number": self.bill_input.text().strip(),
                "invoice_number": self.invoice_input.text().strip(),
                "shipping_supplier_id": self.supplier_combo.currentData(),
                "products_type": self.products_input.text().strip(),
                "discharge_port": self.port_input.text().strip(),
                "shipping_date": datetime.combine(self.shipping_date.date().toPyDate(), datetime.now().time()) if self.shipping_date.date().isValid() else None,
                "expected_arrival_date": datetime.combine(self.arrival_date.date().toPyDate(), datetime.now().time()) if self.arrival_date.date().isValid() else None,
                "cbm": self.cbm_input.get_amount(),
                "cartons": int(self.cartons_input.get_amount()),
                "transitaire": self.transitaire_input.text().strip(),
                "notes": self.notes_input.toPlainText().strip()
            }


# ============================================================================
# EXPENSES TAB
# ============================================================================

class ExpensesTab(QWidget):
    dataChanged = pyqtSignal()
    
    def __init__(self, expense_service, logistics_service, currency_service, 
                 treasury_service, settings_service: SettingsService, customer_service: CustomerService = None):
        super().__init__()
        self.service = expense_service
        self.logistics_service = logistics_service
        self.currency_service = currency_service
        self.treasury_service = treasury_service
        self.settings_service = settings_service
        self.customer_service = customer_service
        self._setup_ui()
        self.load_data()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.table = EnhancedTableView(table_id="logistics_expenses")
        self.table.set_headers([
            "N°", "ID", "Date", "Client", "Type", "Devise", "Montant", "Total (DA)", "Compte", "Référence"
        ])
        
        self.table.addClicked.connect(self.add_expense)
        self.table.editClicked.connect(self.edit_expense)
        self.table.deleteClicked.connect(self.delete_expense)
        self.table.restoreClicked.connect(self.restore_expense)
        self.table.refreshClicked.connect(self.load_data)
        self.table.status_filter.statusChanged.connect(self.load_data)
        
        layout.addWidget(self.table)
        
    def load_data(self):
        filter_status = self.table.status_filter.get_filter()
        self.table.update_actions_for_status(filter_status)
        
        expenses = self.service.get_all_expenses(filter_status=filter_status)
        self.table.clear_rows()
        for e in expenses:
            self.table.add_row([
                None,
                str(e.id),
                format_date(e.date),
                e.customer_name,
                e.type_name,
                e.currency_code,
                format_amount(e.amount, e.currency_code),
                format_amount(e.total_dzd, "DA"),
                e.account_name,
                e.reference or ""
            ], is_active=e.is_active)
        self.table.resize_columns_to_contents()

    def add_expense(self):
        dialog = ExpenseDialog(self.service, self.logistics_service, self.currency_service, self.treasury_service, self.customer_service, parent=self)
        if dialog.exec(): self.load_data()

    def edit_expense(self, row_idx):
        expense_id = int(self.table.get_row_data(row_idx)[1])
        e_data = self.service.get_expense(expense_id)
        if e_data:
            dialog = ExpenseDialog(self.service, self.logistics_service, self.currency_service, self.treasury_service, self.customer_service, edit_data=e_data, parent=self)
            if dialog.exec(): self.load_data()

    def delete_expense(self, row_idx):
        expense_id = int(self.table.get_row_data(row_idx)[1])
        if confirm_action(self, "Confirmer l'archivage", "Voulez-vous vraiment archiver cette dépense ?"):
            success, msg = self.service.delete_expense(expense_id)
            if success:
                show_success(self, "Succès", msg)
                self.load_data()
            else:
                show_error(self, "Erreur", msg)

    def restore_expense(self, row_idx):
        expense_id = int(self.table.get_row_data(row_idx)[1])
        if confirm_action(self, "Confirmer la restauration", "Voulez-vous réactiver cette dépense ?"):
            success, msg = self.service.restore_expense(expense_id)
            if success:
                show_success(self, "Succès", msg)
                self.load_data()
            else:
                show_error(self, "Erreur", msg)


# ============================================================================
# SPECIFIC DIALOGS (Custom Logic)
# ============================================================================

class CustomsDialog(QDialog):
    def __init__(self, container_id, current_value, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Données Dédouanement (Jumerka)")
        self.setFixedWidth(400)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.value = AmountInput()
        self.value.setValue(current_value)
        form.addRow("Valeur Jumerka (DA):", self.value)
        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        
    def get_value(self): return self.value.get_amount()


class ExpenseDialog(QDialog):
    """Dialog for adding direct expenses (Dépenses Directes)"""
    dataSaved = pyqtSignal()
    
    def __init__(self, expense_service, logistics_service, currency_service, treasury_service, customer_service=None, edit_data=None, parent=None):
        super().__init__(parent)
        self.expense_service = expense_service
        self.logistics_service = logistics_service
        self.currency_service = currency_service
        self.treasury_service = treasury_service
        self.customer_service = customer_service
        self.edit_data = edit_data
        self.setWindowTitle("Modifier Dépense" if edit_data else "Nouvelle Dépense")
        self.setMinimumWidth(450)
        self._setup_ui()
        self._load_data()
        if edit_data: self._load_edit_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)
        
        # Client selection
        self.client_combo = QComboBox()
        self.client_widget = create_quick_add_layout(self.client_combo, self._quick_add_client)
        form.addRow("Client:", self.client_widget)
        
        # Type de charge
        self.type_combo = QComboBox()
        self.type_widget = create_quick_add_layout(self.type_combo, self._quick_add_type)
        form.addRow("Type:", self.type_widget)
        
        # Currency selection
        self.currency_combo = QComboBox()
        self.currency_combo.currentIndexChanged.connect(self._on_currency_changed)
        self.currency_widget = create_quick_add_layout(self.currency_combo, self._quick_add_currency)
        form.addRow("Devise:", self.currency_widget)
        
        # Account selection (filtered by currency)
        self.account_combo = QComboBox()
        self.account_widget = create_quick_add_layout(self.account_combo, self._quick_add_account)
        form.addRow("Compte:", self.account_widget)
        
        # Montant with dynamic currency
        self.amount = AmountInput(currency_symbol="DA")
        form.addRow("Montant:", self.amount)
        
        # Date
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setFixedWidth(140)
        form.addRow("Date:", self.date_input)
        
        # Référence
        self.ref = QLineEdit()
        self.ref.setPlaceholderText("N°-facture, N°-BL...")
        form.addRow("Référence:", self.ref)
        
        # Notes
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(60)
        self.notes.setPlaceholderText("Détails supplémentaires...")
        form.addRow("Notes:", self.notes)
        
        layout.addLayout(form)
        
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _load_data(self):
        if self.customer_service:
            clients = self.customer_service.get_all_customers(filter_status="active")
            for c in clients:
                self.client_combo.addItem(c['name'], c['id'])
        
        types = self.expense_service.get_all_expense_types()
        for t in types:
            self.type_combo.addItem(t['name'], t['id'])
        
        # Load currencies
        currencies = self.currency_service.get_all_currencies()
        for c in currencies:
            self.currency_combo.addItem(f"{c['code']} - {c['name']}", c['id'])
        
        # Load accounts for selected currency
        self._load_accounts_by_currency()
    
    def _on_currency_changed(self):
        self._load_accounts_by_currency()
    
    def _load_accounts_by_currency(self):
        self.account_combo.clear()
        currency_id = self.currency_combo.currentData()
        if not currency_id:
            return
        
        accounts = self.treasury_service.get_all_accounts(filter_status="active")
        for acc in accounts:
            if acc.get('currency_id') == currency_id:
                balance_str = f"{acc['balance']:,.2f}" if acc.get('balance') else "0.00"
                self.account_combo.addItem(f"{acc['name']} ({balance_str} {acc.get('currency_code', '')})", acc['id'])
        
        # Update amount input currency symbol
        currency_code = self.currency_combo.currentText().split(" - ")[0] if self.currency_combo.currentText() else "DA"
        self.amount.set_currency_symbol(currency_code)

    def _quick_add_client(self, combo):
        from components.smart_form import SmartFormDialog
        CUSTOMER_SCHEMA = [
            {'name': 'name', 'label': 'Nom du Client', 'type': 'text', 'required': True},
            {'name': 'contact', 'label': 'Contact', 'type': 'text'},
            {'name': 'phone', 'label': 'Téléphone', 'type': 'text'},
            {'name': 'address', 'label': 'Adresse', 'type': 'text'},
        ]
        dialog = SmartFormDialog("Nouveau Client", CUSTOMER_SCHEMA, parent=self)
        if dialog.exec():
            results = dialog.get_results()
            if self.customer_service:
                success, msg, client_id = self.customer_service.create_customer(**results)
                if success:
                    self.client_combo.addItem(results['name'], client_id)
                    self.client_combo.setCurrentIndex(self.client_combo.count()-1)

    def _quick_add_type(self):
        from components.catalog_dialog import GenericCatalogDialog
        dialog = GenericCatalogDialog(
            title="Catalogue des Types de Dépenses",
            get_data_func=self.expense_service.get_all_expense_types,
            create_data_func=self.expense_service.create_expense_type,
            delete_data_func=self.expense_service.delete_expense_type,
            restore_data_func=self.expense_service.restore_expense_type,
            edit_data_func=self.expense_service.update_expense_type,
            primary_placeholder="Nom du type de dépense (ex: Transport, Dédouanement, Tax...)",
            secondary_placeholder="Description (optionnel)",
            headers=["N°", "ID", "Nom", "Description"],
            parent=self
        )
        dialog.exec()
        # Refresh the type combo
        self.type_combo.clear()
        types = self.expense_service.get_all_expense_types()
        for t in types:
            self.type_combo.addItem(t['name'], t['id'])

    def _quick_add_currency(self, combo):
        from components.smart_form import SmartFormDialog
        CURRENCY_SCHEMA = [
            {'name': 'code', 'label': 'Code (ex: EUR, USD)', 'type': 'text', 'required': True},
            {'name': 'name', 'label': 'Nom', 'type': 'text', 'required': True},
            {'name': 'symbol', 'label': 'Symbole', 'type': 'text', 'required': True},
            {'name': 'rate', 'label': 'Taux (DA pour 1)', 'type': 'number', 'required': True},
        ]
        dialog = SmartFormDialog("Nouvelle Devise", CURRENCY_SCHEMA, parent=self)
        if dialog.exec():
            results = dialog.get_results()
            from modules.currency.service import CurrencyService
            currency_service = CurrencyService()
            success, msg, currency_id = currency_service.create_currency(**results)
            if success:
                self.currency_combo.addItem(f"{results['code']} - {results['name']}", currency_id)
                self.currency_combo.setCurrentIndex(self.currency_combo.count()-1)
                self._load_accounts_by_currency()

    def _quick_add_account(self, combo):
        from components.smart_form import SmartFormDialog
        from utils.constants import ACCOUNT_SCHEMA
        dialog = SmartFormDialog("Nouveau Compte", ACCOUNT_SCHEMA, parent=self)
        if dialog.exec():
            results = dialog.get_results()
            success, msg, account_id = self.treasury_service.create_account(**results)
            if success:
                self.account_combo.addItem(f"{results['name']}", account_id)
                self.account_combo.setCurrentIndex(self.account_combo.count()-1)

    def _load_edit_data(self):
        if not self.edit_data:
            return
        e = self.edit_data
        if hasattr(e, 'customer_id') and e.customer_id:
            idx = self.client_combo.findData(e.customer_id)
            if idx >= 0: self.client_combo.setCurrentIndex(idx)
        if hasattr(e, 'expense_type_id') and e.expense_type_id:
            idx = self.type_combo.findData(e.expense_type_id)
            if idx >= 0: self.type_combo.setCurrentIndex(idx)
        if hasattr(e, 'amount'):
            self.amount.setValue(e.amount)
        if hasattr(e, 'date'):
            self.date_input.setDate(e.date)
        if hasattr(e, 'reference') and e.reference:
            self.ref.setText(e.reference)
        if hasattr(e, 'notes') and e.notes:
            self.notes.setText(e.notes)

    def save(self):
        if not self.client_combo.currentData():
            show_error(self, "Erreur", "Veuillez sélectionner un client")
            return
        if self.amount.get_amount() <= 0:
            show_error(self, "Erreur", "Le montant doit être supérieur à 0")
            return
        if not self.type_combo.currentData():
            show_error(self, "Erreur", "Veuillez sélectionner un type de charge")
            return
        if not self.currency_combo.currentData():
            show_error(self, "Erreur", "Veuillez sélectionner une devise")
            return
        if not self.account_combo.currentData():
            show_error(self, "Erreur", "Veuillez sélectionner un compte")
            return
        
        currency_id = self.currency_combo.currentData()
        account_id = self.account_combo.currentData()
        amount = self.amount.get_amount()
        
        # Get exchange rate for the selected currency
        rate = 1.0
        currency_code = self.currency_combo.currentText().split(" - ")[0]
        if currency_code != "DA" and currency_code != "DZD":
            # Get rate from currency service
            currency_data = self.currency_service.get_currency(currency_id)
            if currency_data and currency_data.get('rate'):
                rate = currency_data['rate']
        
        total_dzd = amount * rate
        
        data = {
            "customer_id": self.client_combo.currentData(),
            "expense_type_id": self.type_combo.currentData(),
            "amount": amount,
            "currency_id": currency_id,
            "rate": rate,
            "total_dzd": total_dzd,
            "account_id": account_id,
            "reference": self.ref.text().strip(),
            "notes": self.notes.toPlainText().strip(),
            "date": datetime.combine(self.date_input.date().toPyDate(), datetime.now().time()),
            "payment_type": "CASH",
        }
        
        if self.edit_data:
            success, msg = self.expense_service.update_expense(self.edit_data.id, **data)
        else:
            success, msg, _ = self.expense_service.record_expense(**data)
        
        if success:
            if self.customer_service:
                self.customer_service.add_side_cost(
                    customer_id=self.client_combo.currentData(),
                    cost_type_id=self.type_combo.currentData(),
                    amount=self.amount.get_amount(),
                    notes=f"Charge: {self.type_combo.currentText()}" + (f" - {self.ref.text().strip()}" if self.ref.text().strip() else ""),
                    date=data['date']
                )
            show_success(self, "Succès", msg)
            self.dataSaved.emit()
            self.accept()
        else:
            show_error(self, "Erreur", msg)


# ============================================================================
# RECEIVE WAREHOUSE DIALOG
# ============================================================================

class ReceiveWarehouseDialog(QDialog):
    def __init__(self, container_id: int, goods: list, warehouse_options: list, parent=None):
        super().__init__(parent)
        self.container_id = container_id
        self.goods = goods
        self.warehouse_options = warehouse_options
        self.setWindowTitle("Réception Conteneur en Entrepôt")
        self.setMinimumSize(1200, 750)  # Taller window
        self._selected_row = None
        self._reception_data = {}  # {row_idx: {'received_cartons': X, 'lost_value': Y}}
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # =============================================
        # TOP: Date + Warehouse
        # =============================================
        top_bar = QGroupBox("📋 Informations de Réception")
        top_bar.setStyleSheet("""
            QGroupBox {
                font-weight: bold; font-size: 13px; color: #58a6ff;
                border: 2px solid #30363d; border-radius: 8px;
                margin-top: 8px; padding-top: 12px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setSpacing(20)

        date_label = QLabel("📅 Date:")
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setFixedWidth(130)
        top_layout.addWidget(date_label)
        top_layout.addWidget(self.date_input)

        warehouse_label = QLabel("🏭 Entrepôt:")
        self.warehouse_combo = QComboBox()
        self.warehouse_combo.setFixedWidth(220)
        for name, wid in self.warehouse_options:
            self.warehouse_combo.addItem(name, wid)
        self.warehouse_widget = create_quick_add_layout(self.warehouse_combo, self._quick_add_warehouse)
        top_layout.addWidget(warehouse_label)
        top_layout.addWidget(self.warehouse_widget)

        top_layout.addStretch()
        main_layout.addWidget(top_bar)

        # =============================================
        # MIDDLE: Split horizontal (75% gauche / 25% droite)
        # =============================================
        content_split = QHBoxLayout()
        content_split.setSpacing(10)

        # LEFT: EnhancedTableView (lecture seule - tous les colonnes) ~75%
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        table_label = QLabel("📦 Marchandises du Conteneur")
        table_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #58a6ff; padding: 6px;")
        left_layout.addWidget(table_label)

        self.goods_table = EnhancedTableView(table_id="reception_goods")
        self.goods_table.set_headers([
            "N°", "Client", "Marchandise",
            "Qte Chargée", "CBM", "Prix (DA)", "Remise (DA)", "Total (DA)",
            "Qte Reçue", "Qte Perdue", "Val. Perdue (DA)", "Total Net (DA)"
        ])
        self.goods_table.toolbar.setVisible(False)
        self.goods_table.status_filter.setVisible(False)
        self.goods_table.footer.setVisible(False)
        self.goods_table.table.clicked.connect(self._on_row_selected)
        left_layout.addWidget(self.goods_table)

        total_cartons = sum(g['cartons'] for g in self.goods)
        total_cbm = sum(g['cbm'] for g in self.goods)

        self.summary = QLabel(f"Total: {len(self.goods)} marchandise(s) | {total_cbm:.4f} CBM | {total_cartons} cartons")
        self.summary.setStyleSheet("font-weight: bold; padding: 6px; color: #58a6ff;")
        left_layout.addWidget(self.summary)

        content_split.addWidget(left_widget, 3)  # 75%

        # RIGHT: Panneau de saisie (input only) ~25%
        right_panel = QGroupBox("📝 Saisie")
        right_panel.setStyleSheet("""
            QGroupBox {
                font-weight: bold; font-size: 13px; color: #58a6ff;
                border: 2px solid #30363d; border-radius: 8px;
                margin-top: 0px; padding-top: 12px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        """)
        right_panel.setMinimumWidth(280)
        right_panel.setMaximumWidth(350)
        right_layout = QFormLayout(right_panel)
        right_layout.setSpacing(8)
        right_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Info fields (read-only)
        self.info_client = QLabel("—")
        self.info_client.setStyleSheet("color: #e6edf3; font-size: 12px; padding: 3px;")
        right_layout.addRow("Client:", self.info_client)

        self.info_marchandise = QLabel("—")
        self.info_marchandise.setStyleSheet("color: #e6edf3; font-size: 12px; padding: 3px;")
        right_layout.addRow("Marchandise:", self.info_marchandise)

        self.info_qte_chargee = QLabel("—")
        self.info_qte_chargee.setStyleSheet("color: #e6edf3; font-size: 12px; padding: 3px;")
        right_layout.addRow("Qte Chargée:", self.info_qte_chargee)

        right_layout.addRow("", QLabel(""))  # Spacer

        # Input fields
        from PyQt6.QtWidgets import QSpinBox
        self.input_qte_recue = QSpinBox()
        self.input_qte_recue.setRange(0, 99999)
        self.input_qte_recue.valueChanged.connect(self._update_calculations)
        right_layout.addRow("Qte Reçue:", self.input_qte_recue)

        self.info_qte_perdue = QLabel("—")
        self.info_qte_perdue.setStyleSheet("color: #f0883e; font-size: 12px; font-weight: bold; padding: 3px;")
        right_layout.addRow("Qte Perdue:", self.info_qte_perdue)

        from components.amount_input import AmountInput
        self.input_val_perdue = AmountInput(currency_symbol="DA")
        self.input_val_perdue.input.textChanged.connect(self._on_val_perdue_changed)
        right_layout.addRow("Val. Perdue:", self.input_val_perdue)

        right_layout.addRow("", QLabel(""))  # Spacer

        # Buttons
        from PyQt6.QtWidgets import QPushButton
        btns_layout = QVBoxLayout()

        self.btn_apply = QPushButton("✓ Appliquer")
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #238636; color: white; font-weight: bold;
                padding: 8px 16px; border-radius: 6px; font-size: 12px;
            }
            QPushButton:hover { background-color: #2ea043; }
        """)
        self.btn_apply.clicked.connect(self._apply_reception)
        btns_layout.addWidget(self.btn_apply)

        self.btn_next = QPushButton("Suivant →")
        self.btn_next.setStyleSheet("""
            QPushButton {
                background-color: #1f6feb; color: white; font-weight: bold;
                padding: 8px 16px; border-radius: 6px; font-size: 12px;
            }
            QPushButton:hover { background-color: #388bfd; }
        """)
        self.btn_next.clicked.connect(self._go_to_next_row)
        btns_layout.addWidget(self.btn_next)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #30363d;")
        btns_layout.addWidget(sep)

        # Save button (confirms and closes dialog)
        self.btn_save = QPushButton("💾 Enregistrer")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #d29922; color: white; font-weight: bold;
                padding: 10px 16px; border-radius: 6px; font-size: 13px;
            }
            QPushButton:hover { background-color: #e3b341; }
        """)
        self.btn_save.clicked.connect(self._save_and_close)
        btns_layout.addWidget(self.btn_save)

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #6e7681; color: white; font-weight: bold;
                padding: 8px 16px; border-radius: 6px; font-size: 12px;
            }
            QPushButton:hover { background-color: #8b949e; }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        btns_layout.addWidget(self.btn_cancel)

        right_layout.addRow("", btns_layout)

        content_split.addWidget(right_panel, 1)  # 25%

        main_layout.addLayout(content_split, 1)

        # Load data
        self.original_data = []
        self._load_goods()

    def _on_row_selected(self, index):
        """Quand un row est sélectionné, remplir le panneau de saisie"""
        source_row = self.goods_table.proxy_model.mapToSource(index).row()
        if 0 <= source_row < len(self.goods):
            self._selected_row = source_row
            g = self.goods[source_row]

            # Remplir les infos
            self.info_client.setText(g['customer_name'])
            self.info_marchandise.setText(g['goods_type'])
            self.info_qte_chargee.setText(str(g['cartons']))

            # Restaurer les données saisies si existantes
            if source_row in self._reception_data:
                rd = self._reception_data[source_row]
                self.input_qte_recue.setValue(rd.get('received_cartons', g['cartons']))
                self.input_val_perdue.setValue(rd.get('lost_value', 0))
            else:
                self.input_qte_recue.setValue(g['cartons'])  # Par défaut = chargé
                self.input_val_perdue.setValue(0)

            self._update_calculations()

    def _update_calculations(self):
        """Mettre à jour Qte Perdue automatiquement"""
        if self._selected_row is None:
            return

        g = self.goods[self._selected_row]
        qte_chargee = g['cartons']
        qte_recue = self.input_qte_recue.value()
        qte_perdue = qte_chargee - qte_recue

        if qte_perdue > 0:
            self.info_qte_perdue.setText(f"{qte_perdue}")
            self.info_qte_perdue.setStyleSheet("color: #f85149; font-size: 13px; font-weight: bold; padding: 4px;")
        elif qte_perdue == 0:
            self.info_qte_perdue.setText("0")
            self.info_qte_perdue.setStyleSheet("color: #2ea043; font-size: 13px; font-weight: bold; padding: 4px;")
        else:
            self.info_qte_perdue.setText(f"{qte_perdue} (excédent)")
            self.info_qte_perdue.setStyleSheet("color: #f0883e; font-size: 13px; font-weight: bold; padding: 4px;")

        # Mettre à jour le tableau
        self._update_table_row(self._selected_row)

    def _on_val_perdue_changed(self, text):
        """Quand la valeur perdue change"""
        if self._selected_row is not None:
            self._update_table_row(self._selected_row)

    def _update_table_row(self, row_idx):
        """Mettre à jour une ligne du tableau avec les données de réception"""
        if row_idx < 0 or row_idx >= len(self.goods):
            return

        g = self.goods[row_idx]
        rd = self._reception_data.get(row_idx, {})

        cbm_price_dzd = g.get('cbm_price_dzd', 0)
        discount_dzd = g.get('discount_dzd', 0)

        qte_recue = rd.get('received_cartons', g['cartons'])
        qte_perdue = g['cartons'] - qte_recue
        val_perdue = rd.get('lost_value', 0)

        # Get the source model
        model = self.goods_table.model

        # [FIX] 2026-04-04 - Remplacer les items au lieu de les modifier
        # car le tableau est en lecture seule (EnhancedTableView)
        
        # Update Qte Reçue (column 8)
        new_item_recue = QStandardItem(str(qte_recue))
        new_item_recue.setEditable(False)
        new_item_recue.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        model.setItem(row_idx, 8, new_item_recue)

        # Update Qte Perdue (column 9)
        new_item_perdue = QStandardItem(str(qte_perdue))
        new_item_perdue.setEditable(False)
        new_item_perdue.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if qte_perdue > 0:
            new_item_perdue.setForeground(QColor("#f85149"))
        else:
            new_item_perdue.setForeground(QColor("#2ea043"))
        model.setItem(row_idx, 9, new_item_perdue)

        # Update Val. Perdue (column 10)
        new_item_val = QStandardItem(f"{val_perdue:,.2f} DA")
        new_item_val.setEditable(False)
        new_item_val.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        model.setItem(row_idx, 10, new_item_val)

        # Update Total Net (column 11) = Total (DA) - Val. Perdue (DA)
        total_da = (g['cbm'] * cbm_price_dzd) - discount_dzd
        total_net = total_da - val_perdue
        new_item_total_net = QStandardItem(f"{total_net:,.2f} DA")
        new_item_total_net.setEditable(False)
        new_item_total_net.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if total_net < total_da:
            new_item_total_net.setForeground(QColor("#f0883e"))  # Orange si perte
        else:
            new_item_total_net.setForeground(QColor("#2ea043"))  # Vert si complet
        model.setItem(row_idx, 11, new_item_total_net)

    def _apply_reception(self):
        """Appliquer les données saisies"""
        if self._selected_row is None:
            return

        g = self.goods[self._selected_row]
        self._reception_data[self._selected_row] = {
            'received_cartons': self.input_qte_recue.value(),
            'lost_value': self.input_val_perdue.get_amount()
        }

        self._update_table_row(self._selected_row)

        # Passer au suivant automatiquement
        self._go_to_next_row()

    def _go_to_next_row(self):
        """Passer à la ligne suivante"""
        if self._selected_row is None:
            return
        next_row = self._selected_row + 1
        if next_row < len(self.goods):
            self.goods_table.table.selectRow(next_row)
        else:
            from components.dialogs import show_success
            show_success(self, "Terminé", "Toutes les marchandises ont été réceptionnées!")

    def _save_and_close(self):
        """Valider et enregistrer la réception"""
        # Vérifier que toutes les lignes ont été traitées
        unprocessed = []
        for i, g in enumerate(self.goods):
            if i not in self._reception_data:
                unprocessed.append(g['customer_name'])

        if unprocessed:
            from components.dialogs import show_error
            show_error(self, "Attention",
                f"Certains clients n'ont pas été réceptionnés:\n{', '.join(unprocessed[:5])}"
                + (f"\n...et {len(unprocessed)-5} autres" if len(unprocessed) > 5 else "")
                + "\n\nVeuillez traiter toutes les lignes avant d'enregistrer.")
            return

        # Tout est bon, fermer le dialogue
        self.accept()

    def _load_goods(self):
        self.goods_table.clear_rows()

        for i, g in enumerate(self.goods):
            cbm_price_dzd = g.get('cbm_price_dzd', 0)
            discount_dzd = g.get('discount_dzd', 0)
            original_cbm = g['cbm']
            valeur_expe_dzd = (original_cbm * cbm_price_dzd) - discount_dzd

            self.goods_table.add_row([
                None,  # N° auto
                g['customer_name'],
                g['goods_type'],
                str(g['cartons']),
                f"{g['cbm']:.4f}",
                f"{cbm_price_dzd:,.2f} DA",
                f"{discount_dzd:,.2f} DA",
                f"{valeur_expe_dzd:,.2f} DA",
                str(g['cartons']),  # Qte Reçue (par défaut = chargée)
                "0",  # Qte Perdue
                f"0.00 DA",  # Val. Perdue
                f"{valeur_expe_dzd:,.2f} DA"  # Total Net (par défaut = Total)
            ])

            self.original_data.append({
                'id': g['id'], 'customer_id': g['customer_id'],
                'goods_type': g['goods_type'], 'original_cartons': g['cartons'],
                'original_cbm': g['cbm'], 'cbm_price_dzd': cbm_price_dzd,
                'discount_dzd': discount_dzd, 'valeur_expe_dzd': valeur_expe_dzd
            })

        self.goods_table.resize_columns_to_contents()

        # [FIX] 2026-04-04 - S'assurer que les colonnes 8, 9, 10, 11 sont non-éditables
        # Ces colonnes sont mises à jour uniquement via le panneau de saisie
        model = self.goods_table.model
        for row in range(model.rowCount()):
            for col in [8, 9, 10, 11]:  # Qte Reçue, Qte Perdue, Val. Perdue, Total Net
                item = model.item(row, col)
                if item:
                    item.setEditable(False)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        # Sélectionner la première ligne
        if self.goods:
            self.goods_table.table.selectRow(0)

    def get_results(self):
        if self.result() == QDialog.DialogCode.Accepted:
            wid = self.warehouse_combo.currentData()
            date = datetime.combine(self.date_input.date().toPyDate(), datetime.now().time())
            data = []
            for i, g in enumerate(self.goods):
                d = self.original_data[i].copy()
                rd = self._reception_data.get(i, {})
                d['received_cartons'] = rd.get('received_cartons', g['cartons'])
                d['lost_value'] = rd.get('lost_value', 0)
                d['qte_perdue'] = g['cartons'] - d['received_cartons']
                d['total_net'] = d['valeur_expe_dzd'] - d['lost_value']
                data.append(d)
            return {'warehouse_id': wid, 'received_data': data, 'date': date}
        return None

    def _quick_add_warehouse(self, combo):
        from components.smart_form import SmartFormDialog
        from modules.warehouse.service import WarehouseService

        WAREHOUSE_SCHEMA = [
            {"name": "name", "label": "Nom de l'entrepôt", "type": "text", "required": True},
            {"name": "address", "label": "Adresse", "type": "multiline"},
            {"name": "is_main", "label": "Entrepôt principal", "type": "checkbox"},
        ]

        dialog = SmartFormDialog("Nouvel Entrepôt", WAREHOUSE_SCHEMA, parent=self)
        if dialog.exec():
            results = dialog.get_results()
            warehouse_service = WarehouseService()
            success, msg, wid = warehouse_service.create_warehouse(
                name=results['name'],
                address=results.get('address', ''),
                is_main=results.get('is_main', False)
            )
            if success:
                self.warehouse_combo.addItem(results['name'], wid)
                self.warehouse_combo.setCurrentIndex(self.warehouse_combo.count()-1)