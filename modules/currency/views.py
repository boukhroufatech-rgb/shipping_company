"""
Vues pour le module Gestion des Devises
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTabWidget, QDialog, QFormLayout,
    QLineEdit, QComboBox, QDateEdit, QTextEdit,
    QDialogButtonBox, QMessageBox, QGroupBox, QCheckBox,
    QApplication, QListWidget, QListWidgetItem, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTimer
from datetime import datetime

from components.enhanced_table import EnhancedTableView
from components.amount_input import AmountInput
from components.smart_form import SmartFormDialog
from components.dialogs import (
    show_error, show_success, confirm_action,
    create_quick_add_layout
)
from utils.formatters import format_amount, format_date
from utils.constants import (
    PAYMENT_TYPE_CASH, PAYMENT_TYPE_CREDIT,
    SUPPLIER_TYPE_CURRENCY, SUPPLIER_TYPE_LICENSE, SUPPLIER_TYPE_SHIPPING,
    ACCOUNT_SCHEMA, DEFAULT_CURRENCY_CODE
)
from .service import CurrencyService
from modules.treasury.service import TreasuryService
from modules.settings.service import SettingsService
from .world_dialog import WorldCurrenciesDialog

# ============================================================================
# SCHEMAS
# ============================================================================

# SCHEMAS supprimés (Taux gérés par Achats)

# [MODIFIED] Le fournisseur de devises est un changeur qui travaille uniquement en DA
# [WHY]: Le changeur de devises ne traite que le Dinar Algérien. Le champ currency_id n'est plus nécessaire.
# [DATE]: 2026-04-07
SUPPLIER_SCHEMA = [
    {'name': 'name', 'label': 'Nom du Changeur', 'type': 'text', 'required': True},
    {'name': 'contact', 'label': 'Contact', 'type': 'text'},
    {'name': 'phone', 'label': 'Téléphone', 'type': 'text'},
    {'name': 'email', 'label': 'Email', 'type': 'text'},
    {'name': 'company_name', 'label': 'Nom de la Société', 'type': 'text'},
    {'name': 'company_address', 'label': 'Adresse Complète', 'type': 'text'},
    {'name': 'country', 'label': 'Pays', 'type': 'text'},
]

# ============================================================================
# MAIN VIEW
# ============================================================================

class CurrencyView(QWidget):
    """Vue principale du module de gestion des devises"""
    dataChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.service = CurrencyService()
        self.treasury_service = TreasuryService()
        self.settings_service = SettingsService()
        self._setup_ui()
        # 🚀 Lazy Loading: Data loading is now handled by main.py on tab click.

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # 1. Comptes & Soldes (Synthèse)
        self.summary_tab = CurrenciesSummaryTab(self.service, self.settings_service)
        self.summary_tab.dataChanged.connect(self.refresh)
        self.tabs.addTab(self.summary_tab, "Soldes")

        self.purchases_tab = CurrencyPurchasesTab(self.service, self.treasury_service, self.settings_service)
        self.purchases_tab.dataChanged.connect(self.refresh)
        self.tabs.addTab(self.purchases_tab, "Achats")

        self.suppliers_tab = SuppliersTab(self.service, self.treasury_service, self.settings_service, supplier_type_filter=SUPPLIER_TYPE_CURRENCY)
        self.suppliers_tab.dataChanged.connect(self.refresh)
        self.tabs.addTab(self.suppliers_tab, "Fournisseurs")

        self.payments_tab = SupplierPaymentsTab(self.service)
        self.payments_tab.dataChanged.connect(self.refresh)
        self.tabs.addTab(self.payments_tab, "Paiements")

    def refresh(self):
        """Rafraîchit toutes les vues (Synchronisation Totale)"""
        self.summary_tab.load_data()
        self.purchases_tab.load_data()
        self.suppliers_tab.load_data()
        self.payments_tab.load_data()
        self.dataChanged.emit() # Notifier le reste de l'app si besoin


# ============================================================================
# ============================================================================
# 1. COMPTES & SOLDES (SYNTHÈSE)
# ============================================================================

class CurrenciesSummaryTab(QWidget):
    """Onglet de synthèse financière par devise"""
    dataChanged = pyqtSignal()

    def __init__(self, service: CurrencyService, settings_service: SettingsService):
        super().__init__()
        self.service = service
        self.settings_service = settings_service
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.table = EnhancedTableView(table_id="currency_summary")
        self.table.set_headers([
            "N°", "Devise", "Nom", "Compte Trésorerie",
            "Total Acheté (+)", "Total Consommé (-)", "Solde Actuel",
            "Valeur Totale (DA)", "Solde en DA"
        ])

        self.table.addClicked.connect(self.add_currency)
        self.table.editClicked.connect(self.edit_currency)
        self.table.deleteClicked.connect(self.delete_currency)
        self.table.refreshClicked.connect(self.load_data)
        self.table.selectionChanged.connect(self._on_selection_changed)

        layout.addWidget(self.table)

    def load_data(self):
        summary = self.service.get_currency_financial_summary()
        self.table.clear_rows()

        for i, s in enumerate(summary):
            row_idx = self.table.add_row([
                str(i + 1),
                s['code'],
                s['name'],
                s['account_name'],
                format_amount(s['total_purchased']),
                format_amount(s['total_consumed']),
                format_amount(s['balance']),
                format_amount(s['total_value_dzd'], "DA"),
                format_amount(s['balance_dzd'], "DA")
            ])

        self.table.resize_columns_to_contents()

    def _on_selection_changed(self, selected_rows):
        pass

    def add_currency(self):
        """Ouvre la bibliothèque mondiale pour gérer les devises."""
        dialog = WorldCurrenciesDialog(self.service, self.service.sync_engine, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()
            self.dataChanged.emit()

    def edit_currency(self, row_idx):
        """Modifie une devise existante."""
        row_data = self.table.get_row_data(row_idx)
        code = row_data[1]

        currencies = self.service.get_all_currencies()
        curr = next((c for c in currencies if c['code'] == code), None)
        if not curr:
            return

        schema = [
            {'name': 'code', 'label': 'Code', 'type': 'text', 'required': True, 'readonly': True},
            {'name': 'name', 'label': 'Nom', 'type': 'text', 'required': True},
            {'name': 'symbol', 'label': 'Symbole', 'type': 'text', 'required': True},
            {'name': 'country', 'label': 'Pays', 'type': 'text', 'required': True},
        ]

        initial_data = {
            'code': curr['code'],
            'name': curr['name'],
            'symbol': curr['symbol'],
            'country': curr.get('country', ''),
        }

        dialog = SmartFormDialog("Modifier Devise", schema, initial_data, parent=self)
        if dialog.exec():
            res = dialog.get_results()
            success, message = self.service.update_currency(curr['id'], res['name'], res['symbol'])
            if success:
                from components.dialogs import show_success
                show_success(self, "Succès", message)
                self.load_data()
                self.dataChanged.emit()
            else:
                from components.dialogs import show_error
                show_error(self, "Erreur", message)

    def delete_currency(self, row_idx):
        """Désactive une devise (Archive)."""
        row_data = self.table.get_row_data(row_idx)
        code = row_data[1]
        name = row_data[2]

        from components.dialogs import confirm_action
        if confirm_action(self, "Archiver", f"Voulez-vous désactiver la devise '{code} ({name})' ?"):
            currencies = self.service.get_all_currencies()
            curr = next((c for c in currencies if c['code'] == code), None)
            if curr:
                success, message = self.service.delete_currency(curr['id'])
                if success:
                    from components.dialogs import show_success
                    show_success(self, "Succès", message)
                    self.load_data()
                    self.dataChanged.emit()
                else:
                    from components.dialogs import show_error
                    show_error(self, "Erreur", message)

# ============================================================================
# 4. SUIVI DES PAIEMENTS (DETTES)
# ============================================================================

class SupplierPaymentsTab(QWidget):
    """Onglet de suivi des paiements aux fournisseurs de devises"""
    dataChanged = pyqtSignal()

    def __init__(self, service: CurrencyService):
        super().__init__()
        self.service = service
        from modules.treasury.service import TreasuryService
        self.treasury_service = TreasuryService()
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.table = EnhancedTableView(table_id="supplier_payments_history")
        self.table.set_headers(["N°", "Date", "Fournisseur", "Montant Payé", "Caisse Source", "Référence"])
        self.table.addClicked.connect(self.add_payment)
        self.table.editClicked.connect(self.edit_payment)
        self.table.deleteClicked.connect(self.delete_payment)
        self.table.restoreClicked.connect(self.restore_payment)
        self.table.refreshClicked.connect(self.load_data)
        self.table.status_filter.statusChanged.connect(self.load_data)
        layout.addWidget(self.table)

    def load_data(self):
        filter_status = self.table.status_filter.get_filter()
        self.table.update_actions_for_status(filter_status)

        payments = self.service.get_supplier_payments_history(filter_status=filter_status)
        self.table.clear_rows()
        for i, p in enumerate(payments):
            self.table.add_row([
                str(i + 1),
                str(p['id']),
                format_date(p['date']),
                p['supplier_name'],
                f"{format_amount(p['amount'])} {p['currency_symbol']}",
                p['account_name'],
                p['reference']
            ], is_active=p['is_active'])
        self.table.resize_columns_to_contents()

    def add_payment(self):
        dialog = SupplierPaymentDialog(self.service, self.treasury_service, parent=self)
        if dialog.exec():
            self.load_data()
            self.dataChanged.emit()

    def edit_payment(self, row_idx):
        payment_id = int(self.table.get_row_data(row_idx)[1])
        dialog = SupplierPaymentDialog(self.service, self.treasury_service, edit_id=payment_id, parent=self)
        if dialog.exec():
            self.load_data()
            self.dataChanged.emit()

    def delete_payment(self, row_idx):
        from components.dialogs import confirm_action
        payment_id = int(self.table.get_row_data(row_idx)[1])
        if confirm_action(self, "Annuler", "Cela inversera l'impact sur les soldes. Continuer ?"):
            success, message = self.service.delete_supplier_payment(payment_id)
            if success:
                from components.dialogs import show_success
                show_success(self, "Succès", message)
                self.load_data()
                self.dataChanged.emit()
            else:
                from components.dialogs import show_error
                show_error(self, "Erreur", message)

    def restore_payment(self, row_idx):
        from components.dialogs import confirm_action
        payment_id = int(self.table.get_row_data(row_idx)[1])
        if confirm_action(self, "Restaurer", "Voulez-vous réactiver ce paiement ?"):
            success, message = self.service.restore_supplier_payment(payment_id)
            if success:
                from components.dialogs import show_success
                show_success(self, "Succès", message)
                self.load_data()
                self.dataChanged.emit()
            else:
                from components.dialogs import show_error
                show_error(self, "Erreur", message)


# ============================================================================
# PURCHASES TAB
# ============================================================================

class CurrencyPurchasesTab(QWidget):
    """Onglet des achats de devises"""
    dataChanged = pyqtSignal()  # 🔗

    def __init__(self, service: CurrencyService, treasury_service: TreasuryService, settings_service: SettingsService):
        super().__init__()
        self.service = service
        self.treasury_service = treasury_service
        self.settings_service = settings_service
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.table = EnhancedTableView(table_id="currency_purchases")
        self.table.set_headers([
            "N°", "Date", "Devise", "Fournisseur",
            "Montant Devise", "Taux", "Total DA", "Consommé", "Rest",
            "Paiement", "Référence"
        ])

        self.table.addClicked.connect(self.add_purchase)
        self.table.editClicked.connect(self.edit_purchase)
        self.table.deleteClicked.connect(self.delete_purchase)
        self.table.restoreClicked.connect(self.restore_purchase)
        self.table.refreshClicked.connect(self.load_data)
        self.table.status_filter.statusChanged.connect(self.load_data)

        layout.addWidget(self.table)

    def load_data(self):
        filter_status = self.table.status_filter.get_filter()
        self.table.update_actions_for_status(filter_status)
        
        purchases = self.service.get_all_purchases(filter_status=filter_status)
        self.table.clear_rows()
        for p in purchases:
            consumed = p.get('consumed', 0)
            remaining = p['amount'] - consumed
            self.table.add_row([
                None,
                str(p['id']),
                format_date(p['date']),
                p['currency_code'],
                p['supplier_name'],
                format_amount(p['amount']),
                format_amount(p['rate']),
                format_amount(p['total_dzd'], "DA"),
                format_amount(consumed),
                format_amount(remaining),
                "Espèce" if p['payment_type'] == PAYMENT_TYPE_CASH else "Crédit",
                p['reference'] or ""
            ], is_active=p['is_active'])
        self.table.resize_columns_to_contents()

    def add_purchase(self):
        dialog = PurchaseDialog(self.service, self.treasury_service, parent=self)
        if dialog.exec():
            self.load_data()
            self.dataChanged.emit()  # 🔗

    def edit_purchase(self, row_idx):
        purchase_id = int(self.table.get_row_data(row_idx)[1])
        dialog = PurchaseDialog(self.service, self.treasury_service, edit_id=purchase_id, parent=self)
        if dialog.exec():
            self.load_data()
            self.dataChanged.emit()  # 🔗

    def delete_purchase(self, row_idx):
        from components.dialogs import confirm_action
        purchase_id = int(self.table.get_row_data(row_idx)[1])
        if confirm_action(self, "Annuler L'achat", "Cela inversera l'impact sur les soldes. Continuer ?"):
            success, message = self.service.delete_purchase(purchase_id)
            if success:
                show_success(self, "Succès", message)
                self.load_data()
                self.dataChanged.emit()  # 🔗
            else:
                show_error(self, "Erreur", message)

    def restore_purchase(self, row_idx):
        from components.dialogs import confirm_action
        purchase_id = int(self.table.get_row_data(row_idx)[1])
        if confirm_action(self, "Restaurer L'achat", "Voulez-vous réactiver cet achat et réappliquer son impact ?"):
            success, message = self.service.restore_purchase(purchase_id)
            if success:
                show_success(self, "Succès", message)
                self.load_data()
                self.dataChanged.emit()  # 🔗
            else:
                show_error(self, "Erreur", message)


# ============================================================================
# SUPPLIERS TAB
# ============================================================================

class SuppliersTab(QWidget):
    """Onglet des fournisseurs"""
    dataChanged = pyqtSignal()  # 🔗

    def __init__(self, service: CurrencyService, treasury_service: TreasuryService, settings_service: SettingsService, supplier_type_filter: str = None):
        super().__init__()
        self.service = service
        self.treasury_service = treasury_service
        self.settings_service = settings_service
        self.supplier_type_filter = supplier_type_filter
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        table_ids = {
            SUPPLIER_TYPE_CURRENCY: "currency_suppliers",
            SUPPLIER_TYPE_LICENSE: "license_suppliers",
            SUPPLIER_TYPE_SHIPPING: "shipping_suppliers",
        }
        tid = table_ids.get(self.supplier_type_filter, "currency_suppliers")
        self.table = EnhancedTableView(table_id=tid)
        self.table.set_headers(["N°", "ID", "Nom", "Type", "Contact", "Téléphone", "Solde (Dette)"])

        self.table.addClicked.connect(self.add_supplier)
        self.table.editClicked.connect(self.edit_supplier)
        self.table.deleteClicked.connect(self.delete_supplier)
        self.table.restoreClicked.connect(self.restore_supplier)
        self.table.refreshClicked.connect(self.load_data)
        self.table.status_filter.statusChanged.connect(self.load_data)

        layout.addWidget(self.table)
        
    def load_data(self):
        """Charge les données des fournisseurs avec filtrage"""
        filter_status = self.table.status_filter.get_filter()
        self.table.update_actions_for_status(filter_status)
        
        suppliers = self.service.get_all_suppliers(filter_status=filter_status, supplier_type=self.supplier_type_filter)
        self.table.clear_rows()
        type_map = {
            SUPPLIER_TYPE_CURRENCY: "Devise",
            SUPPLIER_TYPE_LICENSE: "Licence",
            SUPPLIER_TYPE_SHIPPING: "Fret/Logistique"
        }
        for s in suppliers:
            # Récupérer le symbole de la devise (DA par défaut)
            symbol = s.get('currency_symbol', "DA")
            self.table.add_row([
                None,
                str(s['id']),
                s['name'],
                type_map.get(s['supplier_type'], s['supplier_type']),
                s['contact'] or "",
                s['phone'] or "",
                format_amount(s['balance'], symbol)
            ], is_active=s['is_active'])
        self.table.resize_columns_to_contents()

    def add_supplier(self):
        self._show_supplier_dialog()

    def edit_supplier(self, row_idx):
        supplier_id = int(self.table.get_row_data(row_idx)[1])
        self._show_supplier_dialog(supplier_id)

    def _show_supplier_dialog(self, edit_id=None):
        # Pour les fournisseurs de licences, on utilise un dialog spécialisé
        if self.supplier_type_filter == SUPPLIER_TYPE_LICENSE:
            suppliers = self.service.get_all_suppliers(filter_status="all", supplier_type=SUPPLIER_TYPE_LICENSE)
            initial_data = next((s for s in suppliers if s['id'] == edit_id), {}) if edit_id else {}
            dialog = LicenseSupplierDialog(self.service, initial_data, parent=self)
            if dialog.exec():
                results = dialog.get_results()
                if edit_id:
                    success, message = self.service.update_supplier(edit_id, **results)
                else:
                    results['supplier_type'] = SUPPLIER_TYPE_LICENSE
                    success, message, _ = self.service.create_supplier(**results)
                if success:
                    show_success(self, "Succès", message)
                    self.load_data()
                else:
                    show_error(self, "Erreur", message)
            return

        # Standard suppliers (CURRENCY, SHIPPING)
        # [MODIFIED] The exchanger works only in DA - no currency selection
        # [DATE]: 2026-04-07
        import copy
        schema = copy.deepcopy(SUPPLIER_SCHEMA)

        initial_data = {}
        if edit_id:
            suppliers = self.service.get_all_suppliers(filter_status="all")
            supp = next((s for s in suppliers if s['id'] == edit_id), None)
            if supp: initial_data = supp

        dialog = SmartFormDialog("Modifier Fournisseur" if edit_id else "Nouveau Fournisseur", schema, initial_data, parent=self)
        if dialog.exec():
            results = dialog.get_results()
            if edit_id:
                # Preserve supplier_type when editing
                if 'supplier_type' not in results and initial_data:
                    results['supplier_type'] = initial_data.get('supplier_type')
                success, message = self.service.update_supplier(edit_id, **results)
            else:
                if self.supplier_type_filter:
                    results['supplier_type'] = self.supplier_type_filter
                success, message, _ = self.service.create_supplier(**results)

            if success:
                show_success(self, "Succès", message)
                self.load_data()
            else:
                show_error(self, "Erreur", message)

    def delete_supplier(self, row_idx):
        from components.dialogs import confirm_action
        supplier_id = int(self.table.get_row_data(row_idx)[1])
        name = self.table.get_row_data(row_idx)[2]
        if confirm_action(self, "Archiver", f"Voulez-vous vraiment archiver le fournisseur '{name}' ?"):
            success, message = self.service.delete_supplier(supplier_id)
            if success:
                show_success(self, "Succès", message)
                self.load_data()
            else:
                show_error(self, "Erreur", message)

    def restore_supplier(self, row_idx):
        from components.dialogs import confirm_action
        supplier_id = int(self.table.get_row_data(row_idx)[1])
        name = self.table.get_row_data(row_idx)[2]
        if confirm_action(self, "Restaurer", f"Voulez-vous réactiver le fournisseur '{name}' ?"):
            success, message = self.service.restore_supplier(supplier_id)
            if success:
                show_success(self, "Succès", message)
                self.load_data()
            else:
                show_error(self, "Erreur", message)

# Legacy WorldCurrenciesDialog removed. Replaced by world_dialog.py (Clean UI).
            
            
# ============================================================================



class LicenseSupplierDialog(QDialog):
    """Dialog spécialisé pour la fiche d'un Titulaire de Licence"""

    def __init__(self, service: CurrencyService, initial_data: dict = None, parent=None):
        super().__init__(parent)
        self.service = service
        self.initial_data = initial_data or {}
        is_edit = bool(initial_data)
        self.setWindowTitle("Modifier Titulaire" if is_edit else "Nouveau Titulaire")
        self.setMinimumSize(700, 680)
        self._setup_ui()
        self._load_catalog()
        if is_edit:
            self._fill_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # --- Name ---
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Nom du fournisseur *")
        form.addRow("Nom *:", self.inp_name)

        # --- Registry Name ---
        self.inp_rc = QLineEdit()
        self.inp_rc.setPlaceholderText("Ex: SARL Al-Baraka Import...")
        form.addRow("Registre de Commerce:", self.inp_rc)

        # --- Registry Number ---
        self.inp_reg_num = QLineEdit()
        self.inp_reg_num.setPlaceholderText("Ex: 16/00-1234567B15")
        form.addRow("N° de Registre:", self.inp_reg_num)

        # --- NIF ---
        self.inp_nif = QLineEdit()
        self.inp_nif.setPlaceholderText("Ex: 000016123456789")
        form.addRow("NIF:", self.inp_nif)

        # --- License Goods Type ---
        self.goods_combo = QComboBox()
        from components.dialogs import create_quick_add_layout
        goods_layout = create_quick_add_layout(self.goods_combo, self._quick_add_good)
        form.addRow("Marchandise:", goods_layout)

        # --- Currency ---
        self.currency_combo = QComboBox()
        currencies = self.service.get_all_currencies()
        for c in currencies:
            self.currency_combo.addItem(f"{c['code']} ({c['name']})", c['id'])
        form.addRow("Devise de compte *:", self.currency_combo)

        # --- Contact Info ---
        self.inp_contact = QLineEdit()
        form.addRow("Contact:", self.inp_contact)
        self.inp_phone = QLineEdit()
        form.addRow("Téléphone:", self.inp_phone)
        self.inp_email = QLineEdit()
        form.addRow("Email:", self.inp_email)

        # --- Address ---
        self.inp_address = QLineEdit()
        self.inp_address.setPlaceholderText("Adresse complète...")
        form.addRow("Adresse:", self.inp_address)

        # --- Bank ---
        self.inp_bank = QLineEdit()
        self.inp_bank.setPlaceholderText("Ex: BNA, CPA, BDL, BADR...")
        form.addRow("Banque:", self.inp_bank)

        layout.addLayout(form)

        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _load_catalog(self, selected_ids: list = None):
        """Charge le catalogue dans la combobox"""
        if selected_ids is None:
            selected_ids = self.initial_data.get('license_goods_ids', [])
        
        self.goods_combo.clear()
        all_goods = self.service.get_all_license_goods()
        
        for g in all_goods:
            self.goods_combo.addItem(g['name'], g['id'])
            
        if selected_ids and len(selected_ids) > 0:
            idx = self.goods_combo.findData(selected_ids[0])
            if idx >= 0:
                self.goods_combo.setCurrentIndex(idx)

    def _fill_data(self):
        d = self.initial_data
        self.inp_name.setText(d.get('name', ''))
        self.inp_rc.setText(d.get('commercial_register_name', ''))
        self.inp_reg_num.setText(d.get('register_number', ''))
        self.inp_nif.setText(d.get('nif', ''))
        self.inp_contact.setText(d.get('contact', ''))
        self.inp_phone.setText(d.get('phone', ''))
        self.inp_email.setText(d.get('email', ''))
        self.inp_address.setText(d.get('address', ''))
        self.inp_bank.setText(d.get('bank', ''))
        cid = d.get('currency_id')
        if cid:
            idx = self.currency_combo.findData(cid)
            if idx >= 0:
                self.currency_combo.setCurrentIndex(idx)

    def _quick_add_good(self, _checked=False):
        current_selected = self.goods_combo.currentData()
        from components.catalog_dialog import GenericCatalogDialog
        dialog = GenericCatalogDialog(
            title="كاتالوج البضائع — Catalogue des Marchandises",
            get_data_func=self.service.get_all_license_goods,
            create_data_func=self.service.create_license_goods,
            delete_data_func=self.service.delete_license_goods,
            restore_data_func=self.service.restore_license_goods,
            primary_placeholder="Nom de la marchandise (ex: Chaussures...)",
            secondary_placeholder="Description (optionnel)",
            headers=["N°", "ID", "Nom", "Description"],
            parent=self
        )
        dialog.exec()
        self._load_catalog(selected_ids=[current_selected] if current_selected else None)

    def _get_selected_goods_ids(self) -> list:
        val = self.goods_combo.currentData()
        return [val] if val else []

    def _validate_and_accept(self):
        if not self.inp_name.text().strip():
            return show_error(self, "Erreur", "Le nom du fournisseur est obligatoire")
            
        # Message d'avertissement demandé par le client pour la création
        if not self.initial_data.get('id'):
            from components.dialogs import confirm_action
            msg = (
                "⚠️ AVERTISSEMENT / تحذير ⚠️\n\n"
                "Un compte bancaire sera créé automatiquement dans la trésorerie pour ce registre.\n"
                "Il ne pourra pas être supprimé plus tard s'il contient des opérations.\n\n"
                "سيتم إنشاء حساب بنكي تلقائياً في الخزينة لهذا السجل، ولا يمكن حذفه لاحقاً إذا ارتبطت به عمليات مالية.\n\n"
                "Êtes-vous d'accord pour continuer ? / هل توافق على الاستمرار؟"
            )
            if not confirm_action(self, "Création de Registre / إنشاء سجل", msg):
                return
                
        self.accept()

    def get_results(self) -> dict:
        return {
            'name': self.inp_name.text().strip(),
            'commercial_register_name': self.inp_rc.text().strip(),
            'register_number': self.inp_reg_num.text().strip(),
            'nif': self.inp_nif.text().strip(),
            'currency_id': self.currency_combo.currentData(),
            'contact': self.inp_contact.text().strip(),
            'phone': self.inp_phone.text().strip(),
            'email': self.inp_email.text().strip(),
            'address': self.inp_address.text().strip(),
            'bank': self.inp_bank.text().strip(),
            'license_goods_ids': self._get_selected_goods_ids(),
            'supplier_type': 'LICENSE',
        }


# ============================================================================
# SPECIFIC DIALOGS (Purchase remain custom)
# ============================================================================

class PurchaseDialog(QDialog):

    dataSaved = pyqtSignal()

    def __init__(self, service, treasury_service, edit_id=None, parent=None):
        super().__init__(parent)
        self.service = service
        self.treasury_service = treasury_service
        self.edit_id = edit_id
        self.setWindowTitle("Modifier Achat" if edit_id else "Achat de Devises")
        self.setMinimumWidth(550)
        self._setup_ui()
        self._load_suppliers()
        self._load_currencies()
        self._load_accounts()
        if edit_id: self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setFixedWidth(140)
        form.addRow("Date de l'opération:", self.date_input)

        self.supplier_combo = QComboBox()
        from components.dialogs import create_quick_add_layout
        supplier_layout = create_quick_add_layout(self.supplier_combo, self._quick_add_supplier)
        form.addRow("Fournisseur:", supplier_layout)

        self.currency_combo = QComboBox()
        self.currency_combo.currentIndexChanged.connect(self._update_rate)
        currency_layout = create_quick_add_layout(self.currency_combo, self._quick_add_currency)
        form.addRow("Devise:", currency_layout)

        self.amount_input = AmountInput()
        self.amount_input.valueChanged.connect(self._update_total)
        form.addRow("Montant Devise:", self.amount_input)

        self.rate_input = AmountInput()
        self.rate_input.valueChanged.connect(self._update_total)
        form.addRow("Taux de change:", self.rate_input)

        self.discount_input = AmountInput()
        self.discount_input.valueChanged.connect(self._update_total)
        form.addRow("Remise (DA):", self.discount_input)

        self.total_input = QLineEdit()
        self.total_input.setReadOnly(True)
        form.addRow("Total (DA):", self.total_input)

        self.payment_type = QComboBox()
        self.payment_type.addItem("Espèce", PAYMENT_TYPE_CASH)
        self.payment_type.addItem("Crédit (Dette)", PAYMENT_TYPE_CREDIT)
        self.payment_type.currentIndexChanged.connect(self._update_account_visibility)
        form.addRow("Paiement:", self.payment_type)

        self.account_label = QLabel("Compte débité:")
        self.account_combo = QComboBox()
        
        # Account balance label
        self.account_balance_label = QLabel()
        self.account_balance_label.setStyleSheet("color: #7d8590; font-size: 12px;")
        
        self.account_combo.currentIndexChanged.connect(self._update_account_balance)
        
        self.account_widget = create_quick_add_layout(self.account_combo, self._quick_add_account)
        form.addRow(self.account_label, self.account_widget)
        form.addRow("", self.account_balance_label)

        self.reference_input = QLineEdit()
        form.addRow("Référence:", self.reference_input)

        from PyQt6.QtWidgets import QTextEdit
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        form.addRow("Notes:", self.notes_input)

        layout.addLayout(form)

        # Appliquer l'état initial
        self._update_account_visibility()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_data(self):
        p = self.service.get_purchase(self.edit_id)
        if not p: return
        idx = self.supplier_combo.findData(p['supplier_id'])
        if idx >= 0: self.supplier_combo.setCurrentIndex(idx)
        for i in range(self.currency_combo.count()):
            if self.currency_combo.itemData(i)["id"] == p['currency_id']:
                self.currency_combo.setCurrentIndex(i)
                break
        self.amount_input.setValue(p['amount'])
        self.rate_input.setValue(p['rate'])
        self.discount_input.setValue(p.get('discount', 0))
        idx = self.payment_type.findData(p['payment_type'])
        if idx >= 0: self.payment_type.setCurrentIndex(idx)
        self.reference_input.setText(p['reference'] or "")
        self.date_input.setDate(p['date'])
        self.notes_input.setPlainText(p['notes'] or "")

    def _load_suppliers(self):
        self.supplier_combo.clear()
        suppliers = self.service.get_all_suppliers(SUPPLIER_TYPE_CURRENCY)
        for s in suppliers: self.supplier_combo.addItem(s['name'], s['id'])

    def _load_currencies(self):
        self.currency_combo.clear()
        currencies = self.service.get_all_currencies()
        for c in currencies:
            self.currency_combo.addItem(f"{c['code']} ({c['name']})", {"id": c['id'], "rate": c['latest_rate']})

    def _load_accounts(self):
        self.account_combo.clear()
        
        payment_type = self.payment_type.currentData() if hasattr(self, 'payment_type') else PAYMENT_TYPE_CASH
        
        if payment_type == PAYMENT_TYPE_CASH:
            # Only show DA accounts (TRESORIE - Dinar)
            accounts = self.treasury_service.get_all_accounts(
                account_type_filter="CAISSE",
                currency_filter="DA"
            )
        else:
            # For credit, show all DA accounts
            accounts = self.treasury_service.get_all_accounts(currency_filter="DA")
            
        for acc in accounts: self.account_combo.addItem(f"{acc['name']} ({format_amount(acc['balance'], 'DA')})", acc['id'])

    def _update_rate(self):
        data = self.currency_combo.currentData()
        if data: self.rate_input.setValue(data["rate"])
        self._update_total()

    def _update_total(self):
        subtotal = self.amount_input.get_amount() * self.rate_input.get_amount()
        discount = self.discount_input.get_amount()
        total = subtotal - discount
        if total < 0:
            total = 0
        self.total_input.setText(format_amount(total, "DA"))

    def _update_account_visibility(self):
        is_cash = self.payment_type.currentData() == PAYMENT_TYPE_CASH
        self.account_combo.setVisible(is_cash)
        self.account_label.setVisible(is_cash)
        self.account_widget.setVisible(is_cash)
        self.account_balance_label.setVisible(is_cash)
        self._load_accounts()
        self._update_account_balance()

    def _update_account_balance(self):
        """Update account balance display when account is selected"""
        aid = self.account_combo.currentData()
        payment_type = self.payment_type.currentData() if hasattr(self, 'payment_type') else PAYMENT_TYPE_CASH
        
        if not aid or payment_type != PAYMENT_TYPE_CASH:
            self.account_balance_label.setText("")
            return
        
        if payment_type == PAYMENT_TYPE_CASH:
            accounts = self.treasury_service.get_all_accounts(account_type_filter="CAISSE", currency_filter="DA")
        else:
            accounts = self.treasury_service.get_all_accounts(currency_filter="DA")
        
        for acc in accounts:
            if acc['id'] == aid:
                self.account_balance_label.setText(f"💰 Solde actuel: {format_amount(acc['balance'], 'DA')}")
                break

    def _quick_add_account(self, combo):
        from modules.treasury.views import quick_add_account
        quick_add_account(combo, self.treasury_service, parent=self, currency_filter="DA")

    def _quick_add_currency(self, combo):
        """Ouvre la bibliothèque mondiale pour ajouter une devise."""
        dialog = WorldCurrenciesDialog(self.service, self.service.sync_engine, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_currencies()

    def save(self):
        results = {
            'supplier_id': self.supplier_combo.currentData(),
            'currency_id': self.currency_combo.currentData()["id"] if self.currency_combo.currentData() else None,
            'amount': self.amount_input.get_amount(),
            'rate': self.rate_input.get_amount(),
            'discount': self.discount_input.get_amount(),
            'payment_type': self.payment_type.currentData(),
            'account_id': self.account_combo.currentData() if self.payment_type.currentData() == PAYMENT_TYPE_CASH else None,
            'reference': self.reference_input.text(),
            'notes': self.notes_input.toPlainText(),
            'date': datetime.combine(self.date_input.date().toPyDate(), datetime.now().time())
        }
        if self.edit_id:
            success, message = self.service.update_purchase_currency(purchase_id=self.edit_id, **results)
        else:
            success, message, _ = self.service.purchase_currency(**results)
        
        if success:
            show_success(self, "Succès", message)
            self.dataSaved.emit()
            self.accept()
        else:
            show_error(self, "Erreur", message)

    def _quick_add_supplier(self, _checked=False):
        from modules.currency.views import SUPPLIER_SCHEMA
        from components.smart_form import SmartFormDialog
        from components.dialogs import show_success, show_error
        import copy

        currencies = self.service.get_all_currencies()
        curr_options = [(f"{c['code']} ({c['name']})", c['id']) for c in currencies]

        schema = copy.deepcopy(SUPPLIER_SCHEMA)
        for field in schema:
            if field['name'] == 'currency_id':
                field['options'] = curr_options

        dialog = SmartFormDialog("Nouveau Fournisseur (Ajout Rapide)", schema, {}, parent=self)
        if dialog.exec():
            results = dialog.get_results()
            results['supplier_type'] = SUPPLIER_TYPE_CURRENCY
            success, message, new_id = self.service.create_supplier(**results)
            if success:
                show_success(self, "Succès", message)
                self._load_suppliers()  # Refresh the dropdown securely
                idx = self.supplier_combo.findData(new_id)
                if idx >= 0: self.supplier_combo.setCurrentIndex(idx)
            else:
                show_error(self, "Erreur", message)


class SupplierPaymentDialog(QDialog):
    dataSaved = pyqtSignal()

    def __init__(self, service, treasury_service, supplier_id=None, supplier_name=None, edit_id=None, parent=None):
        super().__init__(parent)
        self.service = service
        self.treasury_service = treasury_service
        self.supplier_id = supplier_id
        self.edit_id = edit_id
        suppliers = self.service.get_all_suppliers(filter_status="all")
        self.supplier = None

        if edit_id:
            # Edit mode: load payment data
            payment = self.service.get_supplier_payment(edit_id)
            if payment:
                self.supplier_id = payment['supplier_id']
                self.supplier = next((s for s in suppliers if s['id'] == self.supplier_id), None)
                supplier_name = payment['supplier_name']
        elif supplier_id:
            self.supplier = next((s for s in suppliers if s['id'] == supplier_id), None)

        self.setWindowTitle(f"{'Modifier Paiement' if edit_id else 'Payer Dette'} - {supplier_name or ''}")
        self._setup_ui()
        if edit_id:
            self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Fournisseur (affiché uniquement si pas de supplier_id prédéfini)
        self.supplier_combo = QComboBox()
        if not self.supplier_id:
            from components.dialogs import create_quick_add_layout
            self._load_suppliers()
            supplier_layout = create_quick_add_layout(self.supplier_combo, self._quick_add_supplier)
            form.addRow("Fournisseur:", supplier_layout)
        else:
            # Afficher le nom du fournisseur en lecture seule
            name = self.supplier['name'] if self.supplier else ""
            form.addRow(QLabel(f"<b>Fournisseur:</b> {name}"))

        curr_code = self.supplier['currency_code'] if self.supplier else "DA"
        form.addRow(QLabel(f"<b>Dette en:</b> {curr_code}"))

        self.account_combo = QComboBox()
        self._load_accounts()
        account_layout = create_quick_add_layout(self.account_combo, self._quick_add_account)
        form.addRow("Compte (DA):", account_layout)

        # Account balance label
        self.account_balance_label = QLabel()
        self.account_balance_label.setStyleSheet("color: #7d8590; font-size: 12px;")
        self.account_combo.currentIndexChanged.connect(self._update_account_balance)
        form.addRow("", self.account_balance_label)

        self.amount_input = AmountInput()
        self.amount_input.valueChanged.connect(self._update_simulation)
        form.addRow("Montant payé (DA):", self.amount_input)

        # Simulation label
        self.sim_label = QLabel()
        self.sim_label.setStyleSheet("""
            QLabel {
                background-color: #0d1117;
                color: #e6edf3;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        form.addRow("", self.sim_label)

        self.ref_input = QLineEdit()
        form.addRow("Référence:", self.ref_input)

        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        # Initial balance update
        self._update_account_balance()

    def _load_data(self):
        payment = self.service.get_supplier_payment(self.edit_id)
        if not payment:
            return
        if not self.supplier_id and self.supplier_combo.count() > 0:
            idx = self.supplier_combo.findData(payment['supplier_id'])
            if idx >= 0:
                self.supplier_combo.setCurrentIndex(idx)
        self.amount_input.setValue(payment['amount'])
        self.ref_input.setText(payment.get('reference', ''))

    def _load_suppliers(self):
        self.supplier_combo.clear()
        suppliers = self.service.get_all_suppliers(filter_status="all", supplier_type=SUPPLIER_TYPE_CURRENCY)
        for s in suppliers:
            self.supplier_combo.addItem(s['name'], s['id'])

    def _load_accounts(self):
        self.account_combo.clear()
        accounts = self.treasury_service.get_all_accounts(account_type_filter="CAISSE", currency_filter="DA")
        for acc in accounts:
            self.account_combo.addItem(f"{acc['name']} ({format_amount(acc['balance'], 'DA')})", acc['id'])

    def _quick_add_supplier(self, combo):
        """Ajoute un fournisseur de devises (changeur) rapidement."""
        import copy
        schema = copy.deepcopy(SUPPLIER_SCHEMA)
        dialog = SmartFormDialog("Nouveau Fournisseur", schema, parent=self)
        if dialog.exec():
            results = dialog.get_results()
            results['supplier_type'] = SUPPLIER_TYPE_CURRENCY
            success, message, new_id = self.service.create_supplier(**results)
            if success:
                self._load_suppliers()
                idx = combo.findData(new_id)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            else:
                show_error(self, "Erreur", message)

    def _quick_add_account(self, combo):
        """Ajoute un compte trésorerie rapidement."""
        from modules.treasury.views import quick_add_account
        quick_add_account(combo, self.treasury_service, parent=self, currency_filter="DA")

    def save(self):
        sid = self.supplier_id or self.supplier_combo.currentData()
        if not sid:
            show_error(self, "Erreur", "Veuillez sélectionner un fournisseur")
            return

        results = {
            'supplier_id': sid,
            'account_id': self.account_combo.currentData(),
            'amount': self.amount_input.get_amount(),
            'reference': self.ref_input.text()
        }
        if self.edit_id:
            success, message = self.service.update_supplier_payment(self.edit_id, **results)
        else:
            success, message, _ = self.service.pay_supplier(**results)

        if success:
            show_success(self, "Succès", message)
            self.dataSaved.emit()
            self.accept()
        else:
            show_error(self, "Erreur", message)

    def _update_account_balance(self):
        """Update account balance display when account is selected"""
        aid = self.account_combo.currentData()
        if aid:
            accounts = self.treasury_service.get_all_accounts()
            for acc in accounts:
                if acc['id'] == aid:
                    self.account_balance_label.setText(f"💰 Solde actuel: {format_amount(acc['balance'], 'DA')}")
                    break
        else:
            self.account_balance_label.setText("")

    def _update_simulation(self):
        """Show how account balance will change after payment"""
        aid = self.account_combo.currentData()
        if not aid:
            self.sim_label.setText("")
            return
        
        accounts = self.treasury_service.get_all_accounts()
        current_balance = 0
        for acc in accounts:
            if acc['id'] == aid:
                current_balance = acc['balance']
                break
        
        amount = self.amount_input.get_amount()
        new_balance = current_balance - amount
        
        if new_balance < 0:
            color = "#e74c3c"  # Red - not enough funds
            status = f"⚠️ Insuffisant: {abs(new_balance):,.2f} DA"
        elif new_balance == 0:
            color = "#2ecc71"  # Green
            status = "✅ Compte vide"
        else:
            color = "#7d8590"  # Gray
            status = f" Nouveau solde: {new_balance:,.2f} DA"
        
        self.sim_label.setText(f"💡 Après paiement: <span style='color: {color}'>{status}</span>")


# ============================================================================
# FOREIGN ACCOUNTS TAB
# ============================================================================

# CompteDeviseTab supprimé (Fusionné dans Tab 1)

# ============================================================================
# SHARED GLOBALS (For cross-module Quick Add)
# ============================================================================

def run_supplier_dialog(currency_service, supplier_type: str, parent=None, title=None):
    """
    Lance le dialogue pour ajouter un nouveau fournisseur et retourne son ID.
    Pour LICENSE: utilise LicenseSupplierDialog (design specifique).
    Pour les autres: utilise SmartFormDialog (design generique).
    """
    if supplier_type == SUPPLIER_TYPE_LICENSE:
        dialog = LicenseSupplierDialog(currency_service, parent=parent)
        if dialog.exec():
            data = dialog.get_results()
            data['supplier_type'] = SUPPLIER_TYPE_LICENSE
            success, message, new_id = currency_service.create_supplier(**data)
            return success, message, new_id
        return False, "Annulé", None

    # Pour SHIPPING et CURRENCY: SmartFormDialog generique
    if not title:
        titles = {
            "SHIPPING": "Nouvel Agent Maritime",
            "CURRENCY": "Nouveau Fournisseur",
        }
        title = titles.get(supplier_type, "Nouveau Fournisseur")

    currencies = currency_service.get_all_currencies()
    curr_options = [(f"{c['code']} ({c['name']})", c['id']) for c in currencies]

    schema = []
    for field in SUPPLIER_SCHEMA:
        f = field.copy()
        if f['name'] == 'currency_id':
            f['options'] = curr_options
        schema.append(f)

    dialog = SmartFormDialog(title, schema, parent=parent)
    if dialog.exec():
        results = dialog.get_results()
        results['supplier_type'] = supplier_type
        success, message, new_id = currency_service.create_supplier(**results)
        return success, message, new_id
    return False, "Annulé", None
