"""
Vues pour le module Dettes Externes
Standardized & Purified
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QDialog, QFormLayout, QTabWidget,
    QLineEdit, QComboBox, QTextEdit, QDialogButtonBox,
    QRadioButton, QButtonGroup, QFrame, QGroupBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from datetime import datetime

from components.enhanced_table import EnhancedTableView
from components.amount_input import AmountInput
from components.smart_form import SmartFormDialog
from components.dialogs import show_error, show_success, confirm_delete, create_quick_add_layout
from utils.formatters import format_amount, format_date
from utils.constants import (
    EXT_OP_LEND, EXT_OP_REPAY_LEND,
    EXT_OP_BORROW, EXT_OP_REPAY_BORROW
)
from .service import ExternalDebtService
from modules.treasury.service import TreasuryService
from modules.settings.service import SettingsService

# ============================================================================
# SCHEMAS
# ============================================================================

CONTACT_SCHEMA = [
    {'name': 'name', 'label': 'Nom', 'type': 'text', 'required': True},
    {'name': 'phone', 'label': 'Téléphone', 'type': 'text'},
    {'name': 'notes', 'label': 'Notes', 'type': 'multiline'},
]

# ============================================================================
# TABS
# ============================================================================

class ContactListTab(QWidget):
    """Tab pour la liste des contacts"""
    dataChanged = pyqtSignal()
    
    def __init__(self, view):
        super().__init__()
        self.view = view
        self.service = view.service
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Table des contacts (Pattern N°/ID) - [NEW] 2026-04-05: Colonnes détaillées
        self.table = EnhancedTableView(table_id="external_contacts")
        self.table.set_headers([
            "N°", "ID", "Nom", "Téléphone",
            "Total Prêté", "Total Reçu", "Total Emprunté", "Total Remboursé", "Solde Net"
        ])

        # Actions Standard
        self.table.addClicked.connect(self.add_contact)
        self.table.editClicked.connect(self.edit_contact)
        self.table.deleteClicked.connect(self.delete_contact)
        self.table.restoreClicked.connect(self.restore_contact)
        self.table.refreshClicked.connect(self.load_data)
        self.table.status_filter.statusChanged.connect(self.load_data)

        # Actions Spécifiques
        self.table.add_action_button("Opération", "💸", self.new_operation)
        self.table.add_action_button("Historique", "📜", self.show_history)

        layout.addWidget(self.table)
        self.load_data()

    def load_data(self):
        filter_status = self.table.status_filter.get_filter()
        self.table.update_actions_for_status(filter_status)

        contacts = self.service.get_all_contacts(filter_status=filter_status)
        self.table.clear_rows()
        for c in contacts:
            # [FIX] 2026-04-05 - Handle None values for old records
            total_pret = c.get('total_pret') or 0
            total_recu = c.get('total_recu') or 0
            total_emprunt = c.get('total_emprunt') or 0
            total_rembourse = c.get('total_rembourse') or 0
            solde_net = c.get('solde_net') or 0
            
            # Déterminer la couleur du solde net
            solde_color = "#2ea043" if solde_net > 0 else ("#f85149" if solde_net < 0 else None)

            self.table.add_row([
                None, # N° Auto
                str(c['id']),
                c['name'],
                c['phone'] or "-",
                f"{total_pret:,.2f}",
                f"{total_recu:,.2f}",
                f"{total_emprunt:,.2f}",
                f"{total_rembourse:,.2f}",
                f"{solde_net:,.2f}"
            ], is_active=c['is_active'], color=solde_color)
        self.table.resize_columns_to_contents()

    def add_contact(self):
        dialog = SmartFormDialog("Nouveau Contact", CONTACT_SCHEMA, parent=self)
        if dialog.exec():
            success, message, _ = self.service.create_contact(**dialog.get_results())
            if success:
                show_success(self, "Succès", message)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", message)

    def edit_contact(self, row_idx):
        contact_id = int(self.table.get_row_data(row_idx)[1])
        contact = self.service.get_contact(contact_id)
        if contact:
            dialog = SmartFormDialog("Modifier Contact", CONTACT_SCHEMA, contact, parent=self)
            if dialog.exec():
                success, message = self.service.update_contact(contact_id, **dialog.get_results())
                if success:
                    show_success(self, "Succès", message)
                    self.load_data()
                    self.dataChanged.emit()
                else:
                    show_error(self, "Erreur", message)
                
    def delete_contact(self, row_idx):
        from components.dialogs import confirm_action
        contact_id = int(self.table.get_row_data(row_idx)[1])
        contact_name = self.table.get_row_data(row_idx)[2]
        if confirm_action(self, "Archiver Contact", f"Voulez-vous vraiment archiver le contact '{contact_name}' ?"):
            success, message = self.service.delete_contact(contact_id)
            if success:
                show_success(self, "Succès", message)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", message)

    def restore_contact(self, row_idx):
        from components.dialogs import confirm_action
        contact_id = int(self.table.get_row_data(row_idx)[1])
        contact_name = self.table.get_row_data(row_idx)[2]
        if confirm_action(self, "Restaurer Contact", f"Voulez-vous réactiver le contact '{contact_name}' ?"):
            success, message = self.service.restore_contact(contact_id)
            if success:
                show_success(self, "Succès", message)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", message)

    def new_operation(self):
        selected = self.table.get_selected_rows()
        if not selected:
            show_error(self, "Erreur", "Sélectionnez un contact")
            return
            
        row_data = self.table.get_row_data(selected[0])
        contact_id = int(row_data[1])
        contact_name = row_data[2]
        
        dialog = OperationDialog(self.service, self.view.treasury_service, contact_id, contact_name, parent=self)
        dialog.dataChanged.connect(self.load_data)
        dialog.dataChanged.connect(self.dataChanged.emit)
        if dialog.exec():
            self.load_data()
            self.dataChanged.emit()
            
    def show_history(self):
        selected = self.table.get_selected_rows()
        if not selected:
            show_error(self, "Erreur", "Sélectionnez un contact")
            return
            
        row_data = self.table.get_row_data(selected[0])
        contact_id = int(row_data[1])
        contact_name = row_data[2]
        
        dialog = HistoryDialog(self.service, contact_id, contact_name, parent=self)
        dialog.dataChanged.connect(self.load_data)
        dialog.dataChanged.connect(self.dataChanged.emit)
        dialog.exec()


class DebtJournalTab(QWidget):
    """Tab pour le journal global des opérations"""
    dataChanged = pyqtSignal()
    
    def __init__(self, view):
        super().__init__()
        self.view = view
        self.service = view.service
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Table du journal (Pattern N°/ID) - [NEW] 2026-04-05: Colonnes détaillées
        self.table = EnhancedTableView(table_id="external_journal")
        self.table.set_headers([
            "N°", "ID", "Date", "Contact", "Type",
            "Montant", "Devise", "Taux", "Montant (DA)", "Compte", "Notes"
        ])

        # Actions Standard
        self.table.editClicked.connect(self.edit_operation)
        self.table.deleteClicked.connect(self.delete_operation)
        self.table.restoreClicked.connect(self.restore_operation)
        self.table.refreshClicked.connect(self.load_data)
        self.table.status_filter.statusChanged.connect(self.load_data)

        layout.addWidget(self.table)
        self.load_data()

    def load_data(self):
        filter_status = self.table.status_filter.get_filter()
        self.table.update_actions_for_status(filter_status)

        history = self.service.get_all_history(filter_status=filter_status)
        self.table.clear_rows()
        for h in history:
            # [FIX] 2026-04-05 - Handle None values for old records
            exchange_rate = h.get('exchange_rate') or 1.0
            amount_da = h.get('amount_da') or h.get('amount', 0)
            
            self.table.add_row([
                None,
                str(h['id']),
                format_date(h['date']),
                h['contact_name'],
                h['type_display'],
                f"{h['amount']:,.2f}",
                h.get('currency_code', 'DA'),
                f"{exchange_rate:.2f}",
                f"{amount_da:,.2f} DA",
                h['account_name'],
                h['notes'] or ""
            ], is_active=h['is_active'])
        self.table.resize_columns_to_contents()
        
    def edit_operation(self, row_idx):
        row_data = self.table.get_row_data(row_idx)
        op_id = int(row_data[1])
        contact_name = row_data[3]
        
        # Il nous faut l'ID du contact pour OperationDialog
        # On pourrait modifier get_all_history pour inclure contact_id
        # C'est ce que j'ai fait dans service.py
        op_history_item = next((h for h in self.service.get_all_history() if h['id'] == op_id), None)
        if not op_history_item: return
        
        op = self.service.get_operation_full(op_id)
        if op:
            dialog = OperationDialog(self.service, self.view.treasury_service, 
                                    op_history_item['contact_id'], contact_name, 
                                    edit_data=op, parent=self)
            dialog.dataChanged.connect(self.load_data)
            dialog.dataChanged.connect(self.dataChanged.emit)
            dialog.exec()
            
    def delete_operation(self, row_idx):
        from components.dialogs import confirm_action
        op_id = int(self.table.get_row_data(row_idx)[1])
        if confirm_action(self, "Archiver Opération", "Voulez-vous vraiment archiver cette opération ?"):
            success, message = self.service.delete_operation(op_id)
            if success:
                show_success(self, "Succès", message)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", message)

    def restore_operation(self, row_idx):
        from components.dialogs import confirm_action
        op_id = int(self.table.get_row_data(row_idx)[1])
        if confirm_action(self, "Restaurer Opération", "Voulez-vous réactiver cette opération ?"):
            success, message = self.service.restore_operation(op_id)
            if success:
                show_success(self, "Succès", message)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", message)


# ============================================================================
# MAIN VIEW
# ============================================================================

class ExternalDebtView(QWidget):
    """Vue principale du module Dettes Externes (Standardized with Tabs)"""
    dataChanged = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.service = ExternalDebtService()
        self.treasury_service = TreasuryService()
        self.settings_service = SettingsService()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        
        self.contact_tab = ContactListTab(self)
        self.journal_tab = DebtJournalTab(self)
        
        self.tabs.addTab(self.contact_tab, "Liste des Contacts")
        self.tabs.addTab(self.journal_tab, "Journal des Opérations")
        
        # Synchronisation
        self.contact_tab.dataChanged.connect(self.journal_tab.load_data)
        self.journal_tab.dataChanged.connect(self.contact_tab.load_data)
        self.contact_tab.dataChanged.connect(self.dataChanged.emit)
        self.journal_tab.dataChanged.connect(self.dataChanged.emit)
        
        layout.addWidget(self.tabs)
    
    def load_data(self):
        self.contact_tab.load_data()
        self.journal_tab.load_data()
    
    def refresh(self):
        self.load_data()


# ============================================================================
# DIALOGS (Inchangés mais inclus pour complétude)
# ============================================================================

class OperationDialog(QDialog):
    dataChanged = pyqtSignal()

    def __init__(self, service: ExternalDebtService, treasury_service: TreasuryService, 
                 contact_id: int, contact_name: str, edit_data=None, parent=None):
        super().__init__(parent)
        self.service = service
        self.treasury_service = treasury_service
        self.contact_id = contact_id
        self.contact_name = contact_name
        self.edit_data = edit_data
        self.setWindowTitle(f"{'Modifier' if edit_data else 'Nouvelle'} Opération - {contact_name}")
        self.setMinimumWidth(550)
        
        self._setup_ui()
        self._load_accounts()
        if edit_data:
            self._load_edit_data()
            
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        group = QGroupBox("Type d'Opération")
        vbox = QVBoxLayout()
        
        self.op_loan_given = QRadioButton("Moi ➡️ Lui : Je PRÊTE de l'argent (Créance ↑)")
        self.op_repay_borrow = QRadioButton("Moi ➡️ Lui : Je REMBOURSE ma dette (Dette ↓)")
        self.op_loan_repay = QRadioButton("Lui ➡️ Moi : Il REMBOURSE son prêt (Créance ↓)")
        self.op_borrow = QRadioButton("Lui ➡️ Moi : J'EMPRUNTE de l'argent (Dette ↑)")
        
        self.op_loan_given.setProperty("op_type", EXT_OP_LEND)
        self.op_repay_borrow.setProperty("op_type", EXT_OP_REPAY_BORROW)
        self.op_loan_repay.setProperty("op_type", EXT_OP_REPAY_LEND)
        self.op_borrow.setProperty("op_type", EXT_OP_BORROW)
        
        self.op_loan_given.setChecked(True)
        
        self.group_btn = QButtonGroup()
        for btn in [self.op_loan_given, self.op_repay_borrow, self.op_loan_repay, self.op_borrow]:
            self.group_btn.addButton(btn)
            vbox.addWidget(btn)
            
        self.group_btn.buttonClicked.connect(self._update_simulation)
        group.setLayout(vbox)
        layout.addWidget(group)
        
        form = QFormLayout()

        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setFixedWidth(140)
        form.addRow("Date de l'opération:", self.date_input)

        # [NEW] 2026-04-05 - Filtre par devise avant sélection du compte
        self.currency_filter = QComboBox()
        self.currency_filter.addItem("Toutes les devises", None)
        self.currency_filter.currentIndexChanged.connect(self._on_currency_filter_changed)
        form.addRow("💱 Devise:", self.currency_filter)

        # [NEW] 2026-04-05 - Quick Add pour compte trésorerie (règle 10)
        self.account_combo = QComboBox()
        self.account_widget = create_quick_add_layout(self.account_combo, self._quick_add_account)
        self.account_combo.currentIndexChanged.connect(self._on_account_changed)
        form.addRow("Compte Trésorerie:", self.account_widget)

        self.amount_input = AmountInput()
        self.amount_input.valueChanged.connect(self._update_simulation)
        form.addRow("Montant:", self.amount_input)

        # [NEW] 2026-04-05 - Taux de change pour les devises étrangères
        self.exchange_rate_frame = QFrame()
        self.exchange_rate_frame.setVisible(False)
        er_layout = QHBoxLayout(self.exchange_rate_frame)
        er_layout.setContentsMargins(0, 0, 0, 0)
        er_layout.addWidget(QLabel("1"))
        self.rate_currency_label = QLabel("USD")
        self.rate_currency_label.setStyleSheet("font-weight: bold; color: #58a6ff;")
        er_layout.addWidget(self.rate_currency_label)
        er_layout.addWidget(QLabel("="))
        self.exchange_rate_input = AmountInput(currency_symbol="DA")
        self.exchange_rate_input.input.textChanged.connect(self._update_simulation)
        er_layout.addWidget(self.exchange_rate_input)
        form.addRow("Taux de Change:", self.exchange_rate_frame)

        self.notes_input = QLineEdit()
        form.addRow("Notes:", self.notes_input)

        layout.addLayout(form)

        # Simulation Soldes
        self.balance_frame = QFrame()
        self.balance_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.balance_frame.setStyleSheet("background-color: #1a1a1a; padding: 10px; border-radius: 8px;")
        bal_layout = QVBoxLayout(self.balance_frame)

        self.lbl_current_balance = QLabel("Solde Actuel: -")
        self.lbl_new_balance = QLabel("Nouveau Solde: -")
        self.lbl_new_balance.setStyleSheet("font-weight: bold; font-size: 14px;")

        # [NEW] 2026-04-05 - Affichage en DA pour les devises
        self.lbl_equivalent_da = QLabel("")
        self.lbl_equivalent_da.setStyleSheet("color: #7d8590; font-size: 12px;")

        bal_layout.addWidget(self.lbl_current_balance)
        bal_layout.addWidget(self.lbl_new_balance)
        bal_layout.addWidget(self.lbl_equivalent_da)
        layout.addWidget(self.balance_frame)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        # Load currencies for filter
        self._load_currencies()

    def _load_currencies(self):
        """Charger les devises pour le filtre"""
        from modules.currency.service import CurrencyService
        currency_service = CurrencyService()
        currencies = currency_service.get_all_currencies()
        self.currency_filter.clear()
        self.currency_filter.addItem("Toutes les devises", None)
        for c in currencies:
            if c['is_active']:
                self.currency_filter.addItem(f"{c['code']} - {c['name']}", c['id'])
        self._load_accounts()

    def _on_currency_filter_changed(self):
        """Quand le filtre de devise change, recharger les comptes"""
        self._load_accounts()

    def _quick_add_account(self, combo):
        """Quick Add compte trésorerie (règle 10)"""
        from utils.constants import ACCOUNT_SCHEMA
        dialog = SmartFormDialog("Nouveau Compte", ACCOUNT_SCHEMA, parent=self)
        if dialog.exec():
            try:
                results = dialog.get_results()
                account = self.treasury_service.create_account(**results)
                if account:
                    # Recharger les comptes
                    self._load_accounts()
                    # Sélectionner le nouveau compte
                    for i in range(combo.count()):
                        d = combo.itemData(i)
                        if d and d["id"] == account.id:
                            combo.setCurrentIndex(i)
                            break
            except Exception as e:
                show_error(self, "Erreur", f"Erreur lors de la création du compte: {str(e)}")

    def _load_edit_data(self):
        for btn in self.group_btn.buttons():
            if btn.property("op_type") == self.edit_data['type']:
                btn.setChecked(True)
                break
        
        # Sélectionner la devise du compte édité
        op = self.service.get_operation_full(self.edit_data['id'])
        if op:
            account = self.treasury_service.get_account(op['account_id'])
            if account:
                currency_id = account.get('currency_id')
                for i in range(self.currency_filter.count()):
                    if self.currency_filter.itemData(i) == currency_id:
                        self.currency_filter.setCurrentIndex(i)
                        break
        
        for i in range(self.account_combo.count()):
            d = self.account_combo.itemData(i)
            if d and d["id"] == self.edit_data['account_id']:
                self.account_combo.setCurrentIndex(i)
                break
        self.amount_input.setValue(self.edit_data['amount'])
        self.notes_input.setText(self.edit_data['notes'] or "")
        self.date_input.setDate(self.edit_data['date'])
        self._update_simulation()
        
    def _load_accounts(self):
        """Charger les comptes filtrés par devise"""
        currency_id = self.currency_filter.currentData()
        accounts = self.treasury_service.get_all_accounts(currency_filter=None)  # Tous les comptes
        
        self.account_combo.clear()
        for acc in accounts:
            # Filtrer par devise si sélectionnée
            if currency_id and acc['currency_id'] != currency_id:
                continue
            label = f"{acc['name']} ({format_amount(acc['balance'], acc['currency_symbol'])})"
            self.account_combo.addItem(label, {"id": acc['id'], "currency_id": acc['currency_id'], "symbol": acc['currency_symbol'], "code": acc['currency_code']})
        
        if self.account_combo.count() > 0 and not self.edit_data:
            self._on_account_changed()

    def _on_account_changed(self):
        data = self.account_combo.currentData()
        if data:
            self.amount_input.set_currency_symbol(data["symbol"])
            self.current_balance = self.service.get_contact_balance(self.contact_id, data["currency_id"])
            self._update_current_balance_ui(data["symbol"])
            
            # [NEW] 2026-04-05 - Afficher/masquer le taux de change selon la devise
            is_foreign = data["code"] not in ["DA", "DZD"]
            self.exchange_rate_frame.setVisible(is_foreign)
            if is_foreign:
                self.rate_currency_label.setText(data["code"])
                # Charger le taux par défaut depuis la base
                from modules.currency.service import CurrencyService
                currency_service = CurrencyService()
                rate = currency_service.get_latest_rate(data["currency_id"])
                if rate:
                    self.exchange_rate_input.setValue(rate)
                else:
                    self.exchange_rate_input.setValue(0)
            
            self._update_simulation()

    def _update_current_balance_ui(self, symbol):
        txt = f"Solde Actuel: {format_amount(self.current_balance, symbol)}"
        color = "green" if self.current_balance > 0 else ("red" if self.current_balance < 0 else "white")
        self.lbl_current_balance.setText(txt)
        self.lbl_current_balance.setStyleSheet(f"color: {color};")

    def _update_simulation(self, _=None):
        if not hasattr(self, 'current_balance'): return
        amount = self.amount_input.get_amount()
        op_type = self.group_btn.checkedButton().property("op_type")

        impact = 0
        if op_type in [EXT_OP_LEND, EXT_OP_REPAY_BORROW]: impact = amount
        else: impact = -amount

        new_balance = self.current_balance + impact
        data = self.account_combo.currentData()
        symbol = data["symbol"] if data else ""
        currency_code = data["code"] if data else ""

        # Texte principal (devise du compte)
        txt = f"Nouveau Solde: {format_amount(new_balance, symbol)}"
        color = "green" if new_balance > 0 else ("red" if new_balance < 0 else "white")
        self.lbl_new_balance.setText(txt)
        self.lbl_new_balance.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {color};")

        # [NEW] 2026-04-05 - Affichage équivalent en DA pour les devises étrangères
        if currency_code not in ["DA", "DZD"] and amount > 0:
            rate = self.exchange_rate_input.get_amount()
            if rate > 0:
                equivalent_da = amount * rate
                new_balance_da = new_balance * rate
                self.lbl_equivalent_da.setText(
                    f"Équivalent: {format_amount(equivalent_da, 'DA')} | "
                    f"Nouveau Solde (DA): {format_amount(new_balance_da, 'DA')}"
                )
            else:
                self.lbl_equivalent_da.setText("⚠️ Veuillez saisir le taux de change")
        else:
            self.lbl_equivalent_da.setText("")

    def save(self):
        data = self.account_combo.currentData()
        if not data: return show_error(self, "Erreur", "Compte requis")
        amount = self.amount_input.get_amount()
        if amount <= 0: return show_error(self, "Erreur", "Montant invalide")

        # [NEW] 2026-04-05 - Récupérer le taux de change
        currency_code = data.get("code", "DA")
        exchange_rate = 1.0
        if currency_code not in ["DA", "DZD"]:
            exchange_rate = self.exchange_rate_input.get_amount()
            if exchange_rate <= 0:
                return show_error(self, "Erreur", "Veuillez saisir le taux de change pour cette devise")

        params = {
            'operation_type': self.group_btn.checkedButton().property("op_type"),
            'account_id': data["id"],
            'amount': amount,
            'notes': self.notes_input.text(),
            'date': datetime.combine(self.date_input.date().toPyDate(), datetime.now().time()),
            'exchange_rate': exchange_rate  # [NEW] 2026-04-05
        }

        if self.edit_data:
            success, message = self.service.update_operation_full(operation_id=self.edit_data['id'], **params)
        else:
            success, message, _ = self.service.create_operation(contact_id=self.contact_id, **params)

        if success:
            show_success(self, "Succès", message)
            self.dataChanged.emit()
            self.accept()
        else:
            show_error(self, "Erreur", message)


class HistoryDialog(QDialog):
    """Note: On garde ce dialog car il est pratique pour voir un contact précis"""
    dataChanged = pyqtSignal()
    def __init__(self, service, contact_id, contact_name, parent=None):
        super().__init__(parent)
        self.service = service
        self.contact_id = contact_id
        self.contact_name = contact_name
        self.setWindowTitle(f"Historique - {contact_name}")
        self.resize(1000, 550)

        layout = QVBoxLayout(self)
        self.table = EnhancedTableView(table_id="external_history")
        self.table.set_headers([
            "N°", "ID", "Date", "Type",
            "Montant", "Devise", "Taux", "Montant (DA)", "Compte", "Notes"
        ])

        self.table.editClicked.connect(self.edit_operation)
        self.table.deleteClicked.connect(self.delete_operation)
        self.table.restoreClicked.connect(self.restore_operation)
        self.table.refreshClicked.connect(self.load_data)
        self.table.status_filter.statusChanged.connect(self.load_data)
        layout.addWidget(self.table)
        self.load_data()

    def load_data(self):
        filter_status = self.table.status_filter.get_filter()
        self.table.update_actions_for_status(filter_status)

        history = self.service.get_contact_history(self.contact_id, filter_status=filter_status)
        self.table.clear_rows()
        for h in history:
            # [FIX] 2026-04-05 - Handle None values for old records
            exchange_rate = h.get('exchange_rate') or 1.0
            amount_da = h.get('amount_da') or h.get('amount', 0)
            
            self.table.add_row([
                None,
                str(h['id']),
                format_date(h['date']),
                h['type_display'],
                f"{h['amount']:,.2f}",
                h.get('currency_code', 'DA'),
                f"{exchange_rate:.2f}",
                f"{amount_da:,.2f} DA",
                h['account_name'],
                h['notes'] or ""
            ], is_active=h['is_active'])
        self.table.resize_columns_to_contents()
        
    def edit_operation(self, row_idx):
        op_id = int(self.table.get_row_data(row_idx)[1])
        op = self.service.get_operation_full(op_id)
        if not op: return
        dialog = OperationDialog(self.service, self.parent().treasury_service, self.contact_id, self.contact_name, edit_data=op, parent=self)
        dialog.dataChanged.connect(self.load_data)
        dialog.dataChanged.connect(self.dataChanged.emit)
        dialog.exec()
            
    def delete_operation(self, row_idx):
        from components.dialogs import confirm_action
        op_id = int(self.table.get_row_data(row_idx)[1])
        if confirm_action(self, "Archiver Opération", "Voulez-vous vraiment archiver cette opération ?"):
            success, message = self.service.delete_operation(op_id)
            if success:
                show_success(self, "Succès", message)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", message)

    def restore_operation(self, row_idx):
        from components.dialogs import confirm_action
        op_id = int(self.table.get_row_data(row_idx)[1])
        if confirm_action(self, "Restaurer Opération", "Voulez-vous réactiver cette opération ?"):
            success, message = self.service.restore_operation(op_id)
            if success:
                show_success(self, "Succès", message)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", message)
