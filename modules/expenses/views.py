"""
Dépenses — Vue principale et Dialog d'ajout/modification
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit,
    QComboBox, QDateEdit, QDialog, QDialogButtonBox,
    QButtonGroup, QRadioButton, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from datetime import datetime

from components.enhanced_table import EnhancedTableView
from components.amount_input import AmountInput
from components.dialogs import show_error, show_success, confirm_action, create_quick_add_layout
from components.smart_form import SmartFormDialog
from modules.logistics.expense_service import ExpenseService
from modules.logistics.service import LogisticsService
from modules.currency.service import CurrencyService
from modules.treasury.service import TreasuryService
from modules.customers.service import CustomerService
from modules.settings.service import SettingsService
from utils.formatters import format_date, format_amount
from core.themes import get_active_colors


# ============================================================================
# MAIN VIEW
# ============================================================================

class ExpensesView(QWidget):
    dataChanged = pyqtSignal()
    loaded = False

    def __init__(self):
        super().__init__()
        self.expense_service = ExpenseService()
        self.logistics_service = LogisticsService()
        self.currency_service = CurrencyService()
        self.treasury_service = TreasuryService()
        self.customer_service = CustomerService()
        self.settings_service = SettingsService()
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.table = EnhancedTableView(table_id="expenses_main")
        self.table.set_headers_from_schema("expenses_main")  # [GOLDEN PRINCIPLE]
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
        expenses = self.expense_service.get_all_expenses(filter_status=filter_status)
        self.table.clear_rows()
        for e in expenses:
            # Catégorie: Directe si container_id ou license_id, sinon Opérationnelle
            categorie = "Directe" if (getattr(e, 'container_id', None) or getattr(e, 'license_id', None)) else "Opérationnelle"
            linked = getattr(e, 'linked_to', "") or ""
            account = getattr(e, 'account_name', "") or ""
            supplier = getattr(e, 'supplier_name', "") or ""
            compte_str = account if account and account != "N/A" else supplier
            paiement = getattr(e, 'payment_type', "CASH")

            self.table.add_row([
                None,
                str(e.id),
                e.date,               # [GOLDEN PRINCIPLE] raw date
                categorie,
                e.type_name,
                linked,
                e.currency_code,
                e.amount,             # [GOLDEN PRINCIPLE] raw float
                e.total_dzd,          # [GOLDEN PRINCIPLE] raw float
                compte_str,
                paiement,
                e.reference or ""
            ], is_active=e.is_active)
        self.table.resize_columns_to_contents()
        self.dataChanged.emit()
        self.loaded = True

    def add_expense(self):
        dialog = ExpenseDialog(
            self.expense_service, self.logistics_service,
            self.currency_service, self.treasury_service,
            self.customer_service, parent=self
        )
        if dialog.exec():
            self.load_data()

    def edit_expense(self, row_idx):
        expense_id = int(self.table.get_row_data(row_idx)[1])
        e_data = self.expense_service.get_expense(expense_id)
        if e_data:
            dialog = ExpenseDialog(
                self.expense_service, self.logistics_service,
                self.currency_service, self.treasury_service,
                self.customer_service, edit_data=e_data, parent=self
            )
            if dialog.exec():
                self.load_data()

    def delete_expense(self, row_idx):
        expense_id = int(self.table.get_row_data(row_idx)[1])
        if confirm_action(self, "Archiver", "Archiver cette dépense ?"):
            success, msg = self.expense_service.delete_expense(expense_id)
            if success:
                self.load_data()
            else:
                show_error(self, "Erreur", msg)

    def restore_expense(self, row_idx):
        expense_id = int(self.table.get_row_data(row_idx)[1])
        success, msg = self.expense_service.restore_expense(expense_id)
        if success:
            self.load_data()

    def refresh(self):
        self.load_data()


# ============================================================================
# EXPENSE DIALOG
# ============================================================================

FIXED_TYPES = {"Transport / Fret", "TAXS", "SURISTARIE"}


class ExpenseDialog(QDialog):
    """
    Dialog d'ajout/modification de dépense.
    Deux catégories: Directe (liée à une facture/conteneur) ou Opérationnelle.
    """
    dataChanged = pyqtSignal()

    def __init__(self, expense_service, logistics_service, currency_service,
                 treasury_service, customer_service=None, edit_data=None, parent=None):
        super().__init__(parent)
        self.expense_service = expense_service
        self.logistics_service = logistics_service
        self.currency_service = currency_service
        self.treasury_service = treasury_service
        self.customer_service = customer_service
        self.edit_data = edit_data

        self.setWindowTitle("Modifier Dépense" if edit_data else "Nouvelle Dépense")
        self.setMinimumWidth(520)
        self._setup_ui()
        self._load_dropdowns()
        if edit_data:
            self._load_edit_data()

    # ------------------------------------------------------------------
    # UI SETUP
    # ------------------------------------------------------------------

    def _setup_ui(self):
        c = get_active_colors()
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        # ════════════════════════════════════════════════════════════════
        # 1️⃣ COMMON: Date + Category (toujours visible)
        # ════════════════════════════════════════════════════════════════
        common_group = QGroupBox("Informations de base")
        common_form = QFormLayout(common_group)
        common_form.setSpacing(8)

        # Date (PREMIER toujours)
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setFixedWidth(140)
        common_form.addRow("Date:", self.date_input)

        # Catégorie de dépense
        cat_row = QHBoxLayout()
        self.radio_direct = QRadioButton("Directe")
        self.radio_oper   = QRadioButton("Opérationnelle")
        self.radio_direct.setChecked(True)
        self._cat_group = QButtonGroup()
        self._cat_group.addButton(self.radio_direct, 0)
        self._cat_group.addButton(self.radio_oper,   1)
        cat_row.addWidget(self.radio_direct)
        cat_row.addWidget(self.radio_oper)
        cat_row.addStretch()
        common_form.addRow("Type:", cat_row)

        main_layout.addWidget(common_group)

        # ════════════════════════════════════════════════════════════════
        # 2️⃣ OPERATIONAL SECTION (si Opérationnelle)
        # ════════════════════════════════════════════════════════════════
        self.oper_group = QGroupBox("Dépense Opérationnelle")
        oper_form = QFormLayout(self.oper_group)
        oper_form.setSpacing(8)

        # Type de frais
        self.oper_type_combo = QComboBox()
        oper_form.addRow("Type de frais:", self.oper_type_combo)

        # Devise + Quick Add
        self.oper_currency_combo = QComboBox()
        oper_curr_row_widget = create_quick_add_layout(self.oper_currency_combo, self._quick_add_currency)
        oper_form.addRow("Devise:", oper_curr_row_widget)

        # Compte de la devise (affichage du solde)
        self.oper_account_display = QLabel("—")
        self.oper_account_display.setStyleSheet(f"color: {c['text_secondary']}; font-style: italic;")
        oper_form.addRow("Compte:", self.oper_account_display)

        # Montant
        self.oper_amount_input = AmountInput(currency_symbol="DA")
        oper_form.addRow("Montant:", self.oper_amount_input)

        # Notes
        self.oper_notes_input = QTextEdit()
        self.oper_notes_input.setMaximumHeight(55)
        self.oper_notes_input.setPlaceholderText("Remarques...")
        oper_form.addRow("Notes:", self.oper_notes_input)

        main_layout.addWidget(self.oper_group)

        # ════════════════════════════════════════════════════════════════
        # 3️⃣ DIRECT SECTION (si Directe)
        # ════════════════════════════════════════════════════════════════
        self.direct_group = QGroupBox("Dépense Directe")
        direct_form = QFormLayout(self.direct_group)
        direct_form.setSpacing(8)

        # 3.1 Lier à: Facture ou Conteneur
        link_row = QHBoxLayout()
        self.radio_license   = QRadioButton("Facture (Shp.)")
        self.radio_container = QRadioButton("Conteneur")
        self.radio_container.setChecked(True)
        self._link_group = QButtonGroup()
        self._link_group.addButton(self.radio_license,   0)
        self._link_group.addButton(self.radio_container, 1)
        link_row.addWidget(self.radio_license)
        link_row.addWidget(self.radio_container)
        link_row.addStretch()
        direct_form.addRow("Lier à:", link_row)

        # 3.2 Sélection (Facture ou Conteneur) + Quick Add
        self.link_combo = QComboBox()
        link_row_widget = create_quick_add_layout(self.link_combo, self._quick_add_link)
        direct_form.addRow("Sélection:", link_row_widget)

        # 3.3 Type de frais
        self.direct_type_combo = QComboBox()
        direct_form.addRow("Type de frais:", self.direct_type_combo)

        # 3.4 Devise + Quick Add
        self.direct_currency_combo = QComboBox()
        curr_row_widget = create_quick_add_layout(self.direct_currency_combo, self._quick_add_currency)
        direct_form.addRow("Devise:", curr_row_widget)

        # ── Paiement (visible seulement pour Transport/Fret) ────────────
        self.transport_payment_group = QGroupBox("Paiement Transport / Fret")
        tpg_form = QFormLayout(self.transport_payment_group)
        tpg_form.setSpacing(6)

        # Agent info
        self.agent_label = QLabel("—")
        self.agent_label.setStyleSheet(f"color: {c['text_secondary']}; font-style: italic; font-size: 11px;")
        tpg_form.addRow("Agent:", self.agent_label)

        # Agent balance
        self.agent_balance_label = QLabel("—")
        self.agent_balance_label.setStyleSheet(f"color: {c['accent']}; font-weight: bold; font-size: 11px;")
        tpg_form.addRow("Solde:", self.agent_balance_label)

        # Paiement radio
        pay_row = QHBoxLayout()
        self.radio_cash   = QRadioButton("Caisse")
        self.radio_credit = QRadioButton("À crédit (dette)")
        self.radio_cash.setChecked(True)
        self._pay_group = QButtonGroup()
        self._pay_group.addButton(self.radio_cash,   0)
        self._pay_group.addButton(self.radio_credit, 1)
        pay_row.addWidget(self.radio_cash)
        pay_row.addWidget(self.radio_credit)
        pay_row.addStretch()
        tpg_form.addRow("Paiement:", pay_row)

        direct_form.addRow(self.transport_payment_group)

        # 3.5 Compte (visible uniquement si Caisse dans Transport)
        self.direct_account_display = QLabel("—")
        self.direct_account_display.setStyleSheet(f"color: {c['text_secondary']}; font-style: italic;")
        direct_form.addRow("Compte:", self.direct_account_display)

        # 3.6 Montant
        self.direct_amount_input = AmountInput(currency_symbol="DA")
        direct_form.addRow("Montant:", self.direct_amount_input)

        # 3.7 Taux de change (visible si devise ≠ DA)
        self.direct_rate_label = QLabel("Taux de change:")
        self.direct_rate_input = QLineEdit()
        self.direct_rate_input.setPlaceholderText("ex: 110.50")
        self.direct_rate_input.setFixedWidth(120)
        self.direct_rate_input.textChanged.connect(self._on_direct_rate_changed)
        direct_form.addRow(self.direct_rate_label, self.direct_rate_input)

        # 3.8 Montant en DZD (affichage)
        self.direct_amount_dzd_label = QLabel("—")
        self.direct_amount_dzd_label.setStyleSheet(f"color: {c['accent']}; font-weight: bold;")
        direct_form.addRow("Montant (DA):", self.direct_amount_dzd_label)

        # 3.9 Notes
        self.direct_notes_input = QTextEdit()
        self.direct_notes_input.setMaximumHeight(55)
        self.direct_notes_input.setPlaceholderText("Remarques...")
        direct_form.addRow("Notes:", self.direct_notes_input)

        main_layout.addWidget(self.direct_group)

        # ════════════════════════════════════════════════════════════════
        # 4️⃣ BUTTONS
        # ════════════════════════════════════════════════════════════════
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        main_layout.addWidget(btns)

        # ════════════════════════════════════════════════════════════════
        # SIGNAL CONNECTIONS
        # ════════════════════════════════════════════════════════════════
        self._cat_group.buttonClicked.connect(self._on_category_changed)
        self._link_group.buttonClicked.connect(self._on_link_changed)
        self.direct_type_combo.currentIndexChanged.connect(self._on_direct_type_changed)
        self._pay_group.buttonClicked.connect(self._on_payment_changed)
        self.direct_currency_combo.currentIndexChanged.connect(self._on_direct_currency_changed)
        self.oper_currency_combo.currentIndexChanged.connect(self._on_oper_currency_changed)
        self.direct_amount_input.input.textChanged.connect(self._on_direct_amount_changed)

        # Initial state
        self._on_category_changed()

    # ------------------------------------------------------------------
    # LOAD DROPDOWNS
    # ------------------------------------------------------------------

    def _load_dropdowns(self):
        # Devises
        currencies = self.currency_service.get_all_currencies()
        for combo in (self.oper_currency_combo, self.direct_currency_combo):
            combo.clear()
            for cur in currencies:
                combo.addItem(f"{cur['code']} - {cur['name']}", cur['id'])

        # Types de frais
        types = self.expense_service.get_all_expense_types()
        for combo in (self.direct_type_combo, self.oper_type_combo):
            combo.clear()
            for t in types:
                combo.addItem(t['name'], t['id'])

        # Initialiser le lien
        self._on_link_changed()


    # ------------------------------------------------------------------
    # DYNAMIC STATE & CALLBACKS
    # ------------------------------------------------------------------

    def _on_category_changed(self, *_):
        """Afficher/Masquer les sections selon la catégorie choisie."""
        is_direct = self.radio_direct.isChecked()
        self.direct_group.setVisible(is_direct)
        self.oper_group.setVisible(not is_direct)

        if is_direct:
            self._on_direct_type_changed()
            self._on_link_changed()
        else:
            self._on_oper_currency_changed()

    def _on_link_changed(self, *_):
        """Charger factures ou conteneurs selon le choix."""
        self.link_combo.clear()
        if self.radio_license.isChecked():
            licenses = self.logistics_service.get_all_licenses(filter_status="active")
            for lic in licenses:
                label = f"Facture #{lic['id']}  –  {lic.get('supplier_name','')}"
                self.link_combo.addItem(label, lic['id'])
        else:
            containers = self.logistics_service.get_all_containers(filter_status="active")
            for c in containers:
                label = f"{c['container_number']}  ({c.get('bill_number','')})  –  {c.get('shipping_supplier_name','')}"
                self.link_combo.addItem(label, c['id'])
        self._on_direct_type_changed()

    def _on_direct_type_changed(self, *_):
        """Afficher le groupe Transport/Paiement si type = Transport/Fret."""
        type_name = self.direct_type_combo.currentText()
        is_transport = type_name == "Transport / Fret"

        self.transport_payment_group.setVisible(is_transport)

        if is_transport:
            self._refresh_agent_info()
            self._on_payment_changed()
        else:
            # Pour autres types, afficher le compte (caché quand Transport)
            self.direct_account_display.setVisible(not is_transport)

    def _refresh_agent_info(self):
        """Afficher le nom et le solde de l'agent du transporteur."""
        link_id = self.link_combo.currentData()
        if not link_id:
            self.agent_label.setText("—")
            self.agent_balance_label.setText("—")
            self._current_agent_id = None
            return

        if self.radio_container.isChecked():
            containers = self.logistics_service.get_all_containers(filter_status="active")
            container = next((c for c in containers if c['id'] == link_id), None)
            if container:
                agent_name = container.get('shipping_supplier_name', '—')
                self.agent_label.setText(agent_name or "—")
                self._current_agent_id = container.get('shipping_supplier_id')

                # Afficher le solde (par défaut: 0)
                self.agent_balance_label.setText("0.00 DA")
        else:
            self.agent_label.setText("(réparti sur conteneurs)")
            self.agent_balance_label.setText("—")
            self._current_agent_id = None

    def _on_payment_changed(self, *_):
        """Afficher/Masquer le compte selon Cash/Crédit."""
        is_cash = self.radio_cash.isChecked()
        self.direct_account_display.setVisible(is_cash)

        if is_cash:
            # Afficher le compte disponible selon la devise
            self._refresh_direct_account_display()

    def _refresh_direct_account_display(self):
        """Afficher le compte pour la devise sélectionnée."""
        currency_code = self.direct_currency_combo.currentText().split(" - ")[0]
        try:
            accounts = self.treasury_service.get_all_accounts(filter_status="active")
            account = next((a for a in accounts if a.get('currency_code') == currency_code), None)
            if account:
                balance = account.get('balance', 0)
                self.direct_account_display.setText(f"{account['name']} ({balance:,.2f} {currency_code})")
            else:
                self.direct_account_display.setText(f"Pas de compte en {currency_code}")
        except:
            self.direct_account_display.setText("—")

    def _on_direct_currency_changed(self, *_):
        """Mettre à jour le taux de change et affichage du compte."""
        code = self.direct_currency_combo.currentText().split(" - ")[0] if self.direct_currency_combo.currentText() else "DA"
        self.direct_amount_input.set_currency_symbol(code)

        # Afficher/Masquer taux de change si devise ≠ DA
        is_non_dzd = code not in ("DA", "DZD")
        self.direct_rate_label.setVisible(is_non_dzd)
        self.direct_rate_input.setVisible(is_non_dzd)
        self.direct_amount_dzd_label.setVisible(is_non_dzd)

        if is_non_dzd:
            # Pré-remplir le taux de change depuis la base de données
            try:
                currency_id = self.direct_currency_combo.currentData()
                cur_data = self.currency_service.get_currency(currency_id)
                if cur_data and cur_data.get('rate'):
                    self.direct_rate_input.setText(str(cur_data['rate']))
            except:
                pass
        else:
            self.direct_rate_input.clear()

        if self.radio_cash.isChecked():
            self._refresh_direct_account_display()

    def _on_direct_rate_changed(self, *_):
        """Recalculer le montant en DZD."""
        self._on_direct_amount_changed()

    def _on_direct_amount_changed(self, *_):
        """Calculer montant en DZD = montant × taux."""
        try:
            amount = self.direct_amount_input.get_amount()
            code = self.direct_currency_combo.currentText().split(" - ")[0]

            if code in ("DA", "DZD"):
                self.direct_amount_dzd_label.setText(f"{amount:,.2f} DA")
            else:
                rate_str = self.direct_rate_input.text().strip()
                if rate_str:
                    rate = float(rate_str)
                    amount_dzd = amount * rate
                    self.direct_amount_dzd_label.setText(f"{amount_dzd:,.2f} DA")
                else:
                    self.direct_amount_dzd_label.setText("—")
        except:
            self.direct_amount_dzd_label.setText("—")

    def _on_oper_currency_changed(self, *_):
        """Mettre à jour symbole et affichage du compte pour Opérationnel."""
        code = self.oper_currency_combo.currentText().split(" - ")[0] if self.oper_currency_combo.currentText() else "DA"
        self.oper_amount_input.set_currency_symbol(code)

        # Afficher le compte pour cette devise
        try:
            accounts = self.treasury_service.get_all_accounts(filter_status="active")
            account = next((a for a in accounts if a.get('currency_code') == code), None)
            if account:
                balance = account.get('balance', 0)
                self.oper_account_display.setText(f"{account['name']} ({balance:,.2f} {code})")
            else:
                self.oper_account_display.setText(f"Pas de compte en {code}")
        except:
            self.oper_account_display.setText("—")

    # ------------------------------------------------------------------
    # EDIT MODE
    # ------------------------------------------------------------------

    def _load_edit_data(self):
        e = self.edit_data

        # Date
        if hasattr(e, 'date') and e.date:
            d = e.date if isinstance(e.date, datetime) else datetime.fromisoformat(str(e.date))
            self.date_input.setDate(QDate(d.year, d.month, d.day))

        # Catégorie (Directe ou Opérationnelle)
        is_direct = bool(getattr(e, 'container_id', None) or getattr(e, 'license_id', None))
        if is_direct:
            self.radio_direct.setChecked(True)
        else:
            self.radio_oper.setChecked(True)
        self._on_category_changed()

        # Type de frais
        type_id = getattr(e, 'expense_type_id', None)
        if type_id:
            idx = self.direct_type_combo.findData(type_id)
            if idx >= 0:
                self.direct_type_combo.setCurrentIndex(idx)

        # Devise
        currency_id = getattr(e, 'currency_id', None)
        if currency_id:
            if is_direct:
                idx = self.direct_currency_combo.findData(currency_id)
                if idx >= 0:
                    self.direct_currency_combo.setCurrentIndex(idx)
            else:
                idx = self.oper_currency_combo.findData(currency_id)
                if idx >= 0:
                    self.oper_currency_combo.setCurrentIndex(idx)

        # Montant
        if hasattr(e, 'amount'):
            if is_direct:
                self.direct_amount_input.setValue(e.amount)
            else:
                self.oper_amount_input.setValue(e.amount)

        # Notes
        if hasattr(e, 'notes') and e.notes:
            if is_direct:
                self.direct_notes_input.setPlainText(e.notes)
            else:
                self.oper_notes_input.setPlainText(e.notes)

        # Spécifique aux dépenses directes
        if is_direct:
            # Lien (Facture ou Conteneur)
            if getattr(e, 'license_id', None):
                self.radio_license.setChecked(True)
                self._on_link_changed()
                idx = self.link_combo.findData(e.license_id)
                if idx >= 0:
                    self.link_combo.setCurrentIndex(idx)
            elif getattr(e, 'container_id', None):
                self.radio_container.setChecked(True)
                self._on_link_changed()
                idx = self.link_combo.findData(e.container_id)
                if idx >= 0:
                    self.link_combo.setCurrentIndex(idx)

            # Paiement
            pt = getattr(e, 'payment_type', 'CASH')
            if pt == 'CREDIT':
                self.radio_credit.setChecked(True)
            else:
                self.radio_cash.setChecked(True)
            self._on_payment_changed()

            # Taux de change
            if hasattr(e, 'rate') and e.rate and e.rate != 1.0:
                self.direct_rate_input.setText(str(e.rate))

    # ------------------------------------------------------------------
    # QUICK ADD HANDLERS
    # ------------------------------------------------------------------

    def _quick_add_link(self, combo):
        """Ajouter rapidement une facture ou un conteneur."""
        from components.dialogs import show_info
        show_info(self, "Information", "Utilisez la section Logistique pour ajouter des factures ou des conteneurs")
        # Rafraîchir la liste
        self._on_link_changed()

    def _quick_add_currency(self, combo):
        """Ajouter rapidement une devise."""
        from modules.currency.views import CURRENCY_SCHEMA
        dialog = SmartFormDialog("Nouvelle Devise", CURRENCY_SCHEMA, parent=self)
        if dialog.exec():
            # Recharger les devises
            currencies = self.currency_service.get_all_currencies()
            current_text = combo.currentText()
            combo.clear()
            selected_idx = 0
            for i, cur in enumerate(currencies):
                item_text = f"{cur['code']} - {cur['name']}"
                combo.addItem(item_text, cur['id'])
                if item_text == current_text:
                    selected_idx = i
            combo.setCurrentIndex(selected_idx)

    # ------------------------------------------------------------------
    # SAVE
    # ------------------------------------------------------------------

    def _save(self):
        date = datetime.combine(
            self.date_input.date().toPyDate(), datetime.now().time()
        )

        if self.radio_direct.isChecked():
            self._save_direct(date)
        else:
            self._save_operational(date)

    def _save_direct(self, date):
        """Enregistrer une dépense directe."""
        type_id = self.direct_type_combo.currentData()
        type_name = self.direct_type_combo.currentText()
        link_id = self.link_combo.currentData()
        amount = self.direct_amount_input.get_amount()
        currency_id = self.direct_currency_combo.currentData()
        notes = self.direct_notes_input.toPlainText().strip()

        if not type_id:
            show_error(self, "Erreur", "Sélectionnez un type de frais")
            return
        if not link_id:
            show_error(self, "Erreur", "Sélectionnez une facture ou un conteneur")
            return
        if amount <= 0:
            show_error(self, "Erreur", "Le montant doit être > 0")
            return
        if not currency_id:
            show_error(self, "Erreur", "Sélectionnez une devise")
            return

        # Taux de change
        code = self.direct_currency_combo.currentText().split(" - ")[0]
        rate = 1.0
        if code not in ("DA", "DZD"):
            try:
                rate = float(self.direct_rate_input.text().strip())
                if rate <= 0:
                    show_error(self, "Erreur", "Taux de change invalide")
                    return
            except:
                show_error(self, "Erreur", "Taux de change invalide")
                return

        is_license_link = self.radio_license.isChecked()
        payment_type = "CREDIT" if self.radio_credit.isChecked() else "CASH"
        account_id = None
        supplier_id = None

        # Déterminer account_id / supplier_id selon type et paiement
        if type_name == "Transport / Fret":
            if self.radio_credit.isChecked():
                # Crédit = dette agent
                supplier_id = getattr(self, '_current_agent_id', None)
                if not supplier_id:
                    show_error(self, "Erreur", "Aucun agent associé")
                    return
            else:
                # Cash = prise sur compte
                try:
                    accounts = self.treasury_service.get_all_accounts(filter_status="active")
                    account = next((a for a in accounts if a.get('currency_code') == code), None)
                    if account:
                        account_id = account['id']
                    else:
                        show_error(self, "Erreur", f"Pas de compte en {code}")
                        return
                except Exception as e:
                    show_error(self, "Erreur", f"Erreur: {str(e)}")
                    return
        else:
            # Autres types: trouver compte automatiquement
            try:
                accounts = self.treasury_service.get_all_accounts(filter_status="active")
                account = next((a for a in accounts if a.get('currency_code') == code), None)
                if account:
                    account_id = account['id']
                else:
                    show_error(self, "Erreur", f"Pas de compte en {code}")
                    return
            except Exception as e:
                show_error(self, "Erreur", f"Erreur: {str(e)}")
                return
            payment_type = "CASH"

        # Enregistrer
        try:
            if is_license_link:
                success, msg, nb = self.expense_service.record_expense_split_by_license(
                    license_id=link_id,
                    expense_type_id=type_id,
                    total_amount=amount,
                    currency_id=currency_id,
                    rate=rate,
                    payment_type=payment_type,
                    account_id=account_id,
                    supplier_id=supplier_id,
                    reference="",
                    notes=notes,
                    date=date
                )
            else:
                success, msg, _ = self.expense_service.record_expense(
                    expense_type_id=type_id,
                    amount=amount,
                    currency_id=currency_id,
                    rate=rate,
                    payment_type=payment_type,
                    account_id=account_id,
                    supplier_id=supplier_id,
                    container_id=link_id,
                    reference="",
                    notes=notes,
                    date=date
                )

            if success:
                show_success(self, "Succès", msg)
                self.dataChanged.emit()
                self.accept()
            else:
                show_error(self, "Erreur", msg)
        except Exception as e:
            show_error(self, "Erreur", f"{str(e)}")

    def _save_operational(self, date):
        """Enregistrer une dépense opérationnelle."""
        type_id = self.oper_type_combo.currentData()
        amount = self.oper_amount_input.get_amount()
        currency_id = self.oper_currency_combo.currentData()
        notes = self.oper_notes_input.toPlainText().strip()

        if not type_id:
            show_error(self, "Erreur", "Sélectionnez un type de frais")
            return
        if amount <= 0:
            show_error(self, "Erreur", "Le montant doit être > 0")
            return
        if not currency_id:
            show_error(self, "Erreur", "Sélectionnez une devise")
            return

        # Taux de change (toujours 1.0 pour opérationnel)
        code = self.oper_currency_combo.currentText().split(" - ")[0]
        rate = 1.0

        try:
            accounts = self.treasury_service.get_all_accounts(filter_status="active")
            account = next((a for a in accounts if a.get('currency_code') == code), None)
            if not account:
                show_error(self, "Erreur", f"Pas de compte en {code}")
                return

            success, msg, _ = self.expense_service.record_expense(
                expense_type_id=type_id,
                amount=amount,
                currency_id=currency_id,
                rate=rate,
                payment_type="CASH",
                account_id=account['id'],
                reference="",
                notes=notes,
                date=date
            )

            if success:
                show_success(self, "Succès", msg)
                self.dataChanged.emit()
                self.accept()
            else:
                show_error(self, "Erreur", msg)
        except Exception as e:
            show_error(self, "Erreur", f"{str(e)}")
