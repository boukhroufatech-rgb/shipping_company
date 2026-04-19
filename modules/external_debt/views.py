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
# DIALOG AJOUT CONTACT (avec lien client)
# ============================================================================

class ContactDialog(QDialog):
    """Dialog pour ajouter/modifier un contact externe avec option de lier un client"""
    def __init__(self, service, edit_data=None, parent=None):
        super().__init__(parent)
        self.service = service
        self.edit_data = edit_data
        self.setWindowTitle(f"{'Modifier' if edit_data else 'Nouveau'} Contact")
        self.setMinimumWidth(500)
        self._setup_ui()
        if edit_data:
            self._load_edit_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ── Type de contact ──
        type_group = QGroupBox("Type de contact")
        type_layout = QVBoxLayout(type_group)

        self.rb_external = QRadioButton("Contact externe (nouveau)")
        self.rb_client = QRadioButton("Client existant du programme")
        self.rb_external.setChecked(True)

        self.type_btn_group = QButtonGroup()
        self.type_btn_group.addButton(self.rb_external)
        self.type_btn_group.addButton(self.rb_client)
        self.type_btn_group.buttonClicked.connect(self._on_type_changed)

        type_layout.addWidget(self.rb_external)
        type_layout.addWidget(self.rb_client)
        layout.addWidget(type_group)

        # ── Formulaire contact externe ──
        self.external_frame = QFrame()
        ext_form = QFormLayout()
        ext_form.setContentsMargins(0, 0, 0, 0)
        self.external_frame.setLayout(ext_form)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nom complet ou raison sociale")
        ext_form.addRow("Nom:", self.name_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("0555 XX XX XX")
        ext_form.addRow("Téléphone:", self.phone_input)

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        ext_form.addRow("Notes:", self.notes_input)

        layout.addWidget(self.external_frame)

        # ── Sélection client ──
        self.client_frame = QFrame()
        self.client_frame.setVisible(False)
        client_layout = QVBoxLayout(self.client_frame)
        client_layout.setContentsMargins(0, 0, 0, 0)

        client_form = QFormLayout()
        client_form.setContentsMargins(0, 0, 0, 0)
        self.client_combo = QComboBox()
        self.client_widget = create_quick_add_layout(self.client_combo, self._quick_add_client)
        client_form.addRow("Client:", self.client_widget)
        client_layout.addLayout(client_form)

        # Infos lecture seule
        self.info_group = QGroupBox("Informations du client (lecture seule)")
        info_layout = QFormLayout(self.info_group)
        self.lbl_client_phone = QLabel("-")
        self.lbl_client_phone.setStyleSheet("color: #7d8590;")
        info_layout.addRow("Téléphone:", self.lbl_client_phone)
        self.lbl_client_address = QLabel("-")
        self.lbl_client_address.setStyleSheet("color: #7d8590;")
        info_layout.addRow("Adresse:", self.lbl_client_address)
        self.lbl_client_email = QLabel("-")
        self.lbl_client_email.setStyleSheet("color: #7d8590;")
        info_layout.addRow("E-Mail:", self.lbl_client_email)
        client_layout.addWidget(self.info_group)

        layout.addWidget(self.client_frame)

        self.client_combo.currentIndexChanged.connect(self._on_client_changed)

        # ── Boutons ──
        btns = QDialogButtonBox()
        btn_save = btns.addButton("Enregistrer", QDialogButtonBox.ButtonRole.AcceptRole)
        btn_cancel = btns.addButton("Annuler", QDialogButtonBox.ButtonRole.RejectRole)
        btn_save.clicked.connect(self.save)
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btns)

        # Charger les clients
        self._load_clients()

    def _load_clients(self):
        """Charger la liste des clients existants"""
        from modules.customers.service import CustomerService
        cs = CustomerService()
        clients = cs.get_all_customers()

        self.client_combo.clear()
        for c in clients:
            if c.get('is_active', True):
                self.client_combo.addItem(c['name'], c['id'])

    def _quick_add_client(self, combo):
        """Ajout rapide d'un client — utilise la même fenêtre que le module Clients"""
        from modules.customers.views import CUSTOMER_SCHEMA
        from components.smart_form import SmartFormDialog
        from modules.customers.service import CustomerService

        dialog = SmartFormDialog("Nouveau Client", CUSTOMER_SCHEMA, parent=self)
        if dialog.exec():
            try:
                results = dialog.get_results()
                cs = CustomerService()
                success, msg, client_id = cs.create_customer(**results)
                if success:
                    self._load_clients()
                    # Sélectionner le nouveau client
                    for i in range(self.client_combo.count()):
                        if self.client_combo.itemData(i) == client_id:
                            self.client_combo.setCurrentIndex(i)
                            break
            except Exception as e:
                show_error(self, "Erreur", f"Erreur: {str(e)}")

    def _on_type_changed(self):
        """Basculer entre les deux modes"""
        is_external = self.rb_external.isChecked()
        self.external_frame.setVisible(is_external)
        self.client_frame.setVisible(not is_external)

    def _on_client_changed(self):
        """Afficher les infos du client sélectionné"""
        client_id = self.client_combo.currentData()
        if client_id:
            from modules.customers.service import CustomerService
            cs = CustomerService()
            # get_all_customers retourne une liste de dicts
            clients = cs.get_all_customers(filter_status="all")
            client = next((c for c in clients if c['id'] == client_id), None)
            if client:
                self.lbl_client_phone.setText(client.get('phone') or "-")
                self.lbl_client_address.setText(client.get('address') or "-")
                self.lbl_client_email.setText(client.get('email') or "-")
        else:
            self.lbl_client_phone.setText("-")
            self.lbl_client_address.setText("-")
            self.lbl_client_email.setText("-")

    def _load_edit_data(self):
        """Charger les données pour modification"""
        # Si le contact a un customer_id lié
        customer_id = self.edit_data.get('customer_id')
        if customer_id:
            self.rb_client.setChecked(True)
            for i in range(self.client_combo.count()):
                if self.client_combo.itemData(i) == customer_id:
                    self.client_combo.setCurrentIndex(i)
                    break
        else:
            self.rb_external.setChecked(True)
            self.name_input.setText(self.edit_data.get('name') or "")
            self.phone_input.setText(self.edit_data.get('phone') or "")
            self.notes_input.setPlainText(self.edit_data.get('notes') or "")

    def save(self):
        """Enregistrer le contact"""
        if self.rb_external.isChecked():
            # Mode contact externe
            name = self.name_input.text().strip()
            if not name:
                return show_error(self, "Erreur", "Le nom est requis")

            phone = self.phone_input.text().strip()
            notes = self.notes_input.toPlainText().strip()

            if self.edit_data:
                success, msg = self.service.update_contact(
                    self.edit_data['id'], name=name, phone=phone, notes=notes
                )
            else:
                success, msg, _ = self.service.create_contact(
                    name=name, phone=phone, notes=notes
                )
        else:
            # Mode client lié
            client_id = self.client_combo.currentData()
            if not client_id:
                return show_error(self, "Erreur", "Veuillez sélectionner un client")

            from modules.customers.service import CustomerService
            cs = CustomerService()
            clients = cs.get_all_customers(filter_status="all")
            client = next((c for c in clients if c['id'] == client_id), None)
            if not client:
                return show_error(self, "Erreur", "Client introuvable")

            name = client['name']
            phone = client.get('phone') or ""
            notes = f"Client lié (ID: {client_id})"

            if self.edit_data:
                success, msg = self.service.update_contact(
                    self.edit_data['id'], name=name, phone=phone, notes=notes,
                    customer_id=client_id
                )
            else:
                success, msg, _ = self.service.create_contact(
                    name=name, phone=phone, notes=notes, customer_id=client_id
                )

        if success:
            show_success(self, "Succès", msg)
            self.accept()
        else:
            show_error(self, "Erreur", msg)

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

        # Table des contacts - [NEW] 2026-04-14: Design simplifié
        self.table = EnhancedTableView(table_id="external_contacts")
        self.table.set_headers([
            "N°", "ID", "Nom", "Téléphone", "Type",
            "J'ai Donné", "J'ai Reçu", "Objet", "Solde"
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
            total_pret = c.get('total_pret') or 0
            total_recu = c.get('total_recu') or 0
            total_emprunt = c.get('total_emprunt') or 0
            total_rembourse = c.get('total_rembourse') or 0
            solde_net = c.get('solde_net') or 0

            # Type de contact
            is_client = c.get('customer_id') is not None
            type_text = "Client" if is_client else "Contact"
            type_color = "#58a6ff" if is_client else None  # Bleu si client

            # Solde coloré
            solde_color = "#2ea043" if solde_net > 0 else ("#f85149" if solde_net < 0 else None)

            # Objet: résumé des opérations actives
            objet_parts = []
            if total_pret > 0: objet_parts.append(f"Prêt: {total_pret:,.0f}")
            if total_emprunt > 0: objet_parts.append(f"Emprunt: {total_emprunt:,.0f}")
            if total_recu > 0: objet_parts.append(f"Remb. reçu: {total_recu:,.0f}")
            if total_rembourse > 0: objet_parts.append(f"Remb. fait: {total_rembourse:,.0f}")
            objet = " | ".join(objet_parts) if objet_parts else "Aucune opération"

            self.table.add_row([
                None,  # N° Auto
                str(c['id']),
                c['name'],
                c['phone'] or "-",
                type_text,
                f"{total_pret:,.2f} DA",
                f"{total_recu + total_rembourse:,.2f} DA",
                objet,
                f"{solde_net:,.2f} DA"
            ], is_active=c['is_active'], color=solde_color)
        self.table.resize_columns_to_contents()

    def add_contact(self):
        dialog = ContactDialog(self.service, parent=self)
        if dialog.exec():
            self.load_data()
            self.dataChanged.emit()

    def edit_contact(self, row_idx):
        contact_id = int(self.table.get_row_data(row_idx)[1])
        contact = self.service.get_contact(contact_id)
        if contact:
            # Ajouter le customer_id aux données
            contact_detail = self.service.get_contact_detail(contact_id)
            contact['customer_id'] = contact_detail.get('customer_id') if contact_detail else None

            dialog = ContactDialog(self.service, edit_data=contact, parent=self)
            if dialog.exec():
                self.load_data()
                self.dataChanged.emit()
                
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
        self.table.set_headers_from_schema("external_journal")  # [GOLDEN PRINCIPLE] schema centralisé

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

            # [GOLDEN PRINCIPLE] 2026-04-19 - Pass raw values, not formatted strings
            self.table.add_row([
                None,
                str(h['id']),
                h['date'] if isinstance(h['date'], str) else h['date'].isoformat(),  # Raw ISO date
                h['contact_name'],
                h['type_display'],
                h['amount'],  # raw float
                h.get('currency_code', 'DA'),
                exchange_rate,  # raw float
                amount_da,  # raw float
                h['account_name'],
                h['notes'] or ""
            ], is_active=h['is_active'])
        self.table.resize_columns_to_contents()
        
    def edit_operation(self, row_idx):
        """Modifie une opération depuis le journal"""
        row_data = self.table.get_row_data(row_idx)
        op_id = int(row_data[1])
        contact_name = row_data[3]

        # [FIX] 2026-04-14 - Recherche directe au lieu de charger tout l'historique
        op_history_item = next(
            (h for h in self.service.get_all_history(filter_status="all", limit=100) if h['id'] == op_id),
            None
        )
        if not op_history_item:
            show_error(self, "Erreur", "Opération introuvable")
            return

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

        self.op_donne = QRadioButton("J'ai DONNÉ de l'argent (Sortie d'argent)")
        self.op_recu = QRadioButton("J'ai REÇU de l'argent (Entrée d'argent)")

        self.op_donne.setChecked(True)

        self.group_btn = QButtonGroup()
        for btn in [self.op_donne, self.op_recu]:
            self.group_btn.addButton(btn)
            vbox.addWidget(btn)

        self.lbl_op_info = QLabel()
        self.lbl_op_info.setStyleSheet("color: #7d8590; font-size: 12px; font-style: italic;")
        self.lbl_op_info.setWordWrap(True)
        vbox.addWidget(self.lbl_op_info)

        self.group_btn.buttonClicked.connect(self._update_simulation)
        group.setLayout(vbox)
        layout.addWidget(group)

        form = QFormLayout()

        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setFixedWidth(140)
        form.addRow("Date:", self.date_input)

        # Filtre par devise
        self.currency_filter = QComboBox()
        self.currency_filter.addItem("Toutes les devises", None)
        self.currency_filter.currentIndexChanged.connect(self._on_currency_filter_changed)
        form.addRow("Devise:", self.currency_filter)

        # Quick Add pour compte trésorerie
        self.account_combo = QComboBox()
        self.account_widget = create_quick_add_layout(self.account_combo, self._quick_add_account)
        self.account_combo.currentIndexChanged.connect(self._on_account_changed)
        form.addRow("Compte Trésorerie:", self.account_widget)

        self.amount_input = AmountInput()
        self.amount_input.valueChanged.connect(self._update_simulation)
        form.addRow("Montant:", self.amount_input)

        # Taux de change pour les devises étrangères
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
        form.addRow("Taux:", self.exchange_rate_frame)

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

        self.lbl_equivalent_da = QLabel("")
        self.lbl_equivalent_da.setStyleSheet("color: #7d8590; font-size: 12px;")

        bal_layout.addWidget(self.lbl_current_balance)
        bal_layout.addWidget(self.lbl_new_balance)
        bal_layout.addWidget(self.lbl_equivalent_da)
        layout.addWidget(self.balance_frame)

        # Boutons
        btns = QDialogButtonBox()
        btn_save = btns.addButton("Enregistrer", QDialogButtonBox.ButtonRole.AcceptRole)
        btn_cancel = btns.addButton("Annuler", QDialogButtonBox.ButtonRole.RejectRole)
        btn_save.clicked.connect(self.save)
        btn_cancel.clicked.connect(self.reject)
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
                success, msg, account_id = self.treasury_service.create_account(**results)
                if success:
                    # Recharger les comptes
                    self._load_accounts()
                    # Sélectionner le nouveau compte
                    combo.setCurrentIndex(combo.count() - 1)
                else:
                    from components.dialogs import show_error
                    show_error(self, "Erreur", msg)
            except Exception as e:
                show_error(self, "Erreur", f"Erreur lors de la création du compte: {str(e)}")

    def _load_edit_data(self):
        """Charge les données pour modification"""
        # Sélectionner le bon bouton selon le type d'opération
        op_type = self.edit_data.get('type')
        if op_type in [EXT_OP_LEND, EXT_OP_REPAY_BORROW]:
            self.op_donne.setChecked(True)  # Argent sorti
        else:
            self.op_recu.setChecked(True)  # Argent entré

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

        # Charger le taux de change
        exchange_rate = self.edit_data.get('exchange_rate')
        if exchange_rate and exchange_rate != 1.0:
            self.exchange_rate_input.setValue(exchange_rate)

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

            # Afficher/masquer le taux de change selon la devise
            is_foreign = data["code"] not in ["DA", "DZD"]
            self.exchange_rate_frame.setVisible(is_foreign)
            if is_foreign:
                self.rate_currency_label.setText(data["code"])
                from modules.currency.service import CurrencyService
                currency_service = CurrencyService()
                rate = currency_service.get_latest_rate(data["currency_id"])
                if rate:
                    self.exchange_rate_input.setValue(rate)
                else:
                    self.exchange_rate_input.setValue(0)

            # Mettre à jour l'info d'auto-détection
            self._update_op_info()

            self._update_simulation()

    def _update_op_info(self):
        """Affiche l'info sur le type d'opération détecté automatiquement"""
        if self.current_balance >= 0:
            # Solde positif ou nul: il me doit
            if self.op_donne.isChecked():
                self.lbl_op_info.setText("→ Nouveau prêt (il me devra plus)")
            else:
                self.lbl_op_info.setText("→ Il rembourse son prêt (il me devra moins)")
        else:
            # Solde négatif: je lui dois
            if self.op_donne.isChecked():
                self.lbl_op_info.setText("→ Je rembourse ma dette (je lui devrai moins)")
            else:
                self.lbl_op_info.setText("→ Nouvel emprunt (je lui devrai plus)")

    def _update_current_balance_ui(self, symbol):
        txt = f"Solde Actuel: {format_amount(self.current_balance, symbol)}"
        color = "green" if self.current_balance > 0 else ("red" if self.current_balance < 0 else "white")
        self.lbl_current_balance.setText(txt)
        self.lbl_current_balance.setStyleSheet(f"color: {color};")

    def _update_simulation(self, _=None):
        if not hasattr(self, 'current_balance'): return
        amount = self.amount_input.get_amount()

        # Auto-détection du type d'opération selon le solde
        op_type = self._get_auto_op_type()

        # Calcul de l'impact sur le solde
        # Solde = (J'ai donné) - (J'ai reçu)
        if self.op_donne.isChecked():
            impact = amount  # Solde augmente (je donne → créance ↑)
        else:
            impact = -amount  # Solde diminue (je reçois → créance ↓)

        new_balance = self.current_balance + impact
        data = self.account_combo.currentData()
        symbol = data["symbol"] if data else ""
        currency_code = data["code"] if data else ""

        # Texte principal (devise du compte)
        txt = f"Nouveau Solde: {format_amount(new_balance, symbol)}"
        color = "green" if new_balance > 0 else ("red" if new_balance < 0 else "white")
        self.lbl_new_balance.setText(txt)
        self.lbl_new_balance.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {color};")

        # Affichage équivalent en DA pour les devises étrangères
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

        # Mettre à jour l'info
        self._update_op_info()

    def _get_auto_op_type(self):
        """Détermine automatiquement le type d'opération selon le solde"""
        balance = self.current_balance
        is_donne = self.op_donne.isChecked()

        if balance >= 0:
            # Solde positif: il me doit
            if is_donne:
                return EXT_OP_LEND  # Nouveau prêt
            else:
                return EXT_OP_REPAY_LEND  # Il rembourse
        else:
            # Solde négatif: je lui dois
            if is_donne:
                return EXT_OP_REPAY_BORROW  # Je rembourse
            else:
                return EXT_OP_BORROW  # Nouvel emprunt

    def save(self):
        data = self.account_combo.currentData()
        if not data: return show_error(self, "Erreur", "Compte requis")
        amount = self.amount_input.get_amount()
        if amount <= 0: return show_error(self, "Erreur", "Montant invalide")

        # Récupérer le taux de change
        currency_code = data.get("code", "DA")
        exchange_rate = 1.0
        if currency_code not in ["DA", "DZD"]:
            exchange_rate = self.exchange_rate_input.get_amount()
            if exchange_rate <= 0:
                return show_error(self, "Erreur", "Veuillez saisir le taux de change pour cette devise")

        # Auto-détection du type d'opération
        op_type = self._get_auto_op_type()

        params = {
            'operation_type': op_type,
            'account_id': data["id"],
            'amount': amount,
            'notes': self.notes_input.text(),
            'date': datetime.combine(self.date_input.date().toPyDate(), datetime.now().time()),
            'exchange_rate': exchange_rate
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
        self.table.set_headers_from_schema("external_history")  # [GOLDEN PRINCIPLE] schema centralisé

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

            # [GOLDEN PRINCIPLE] 2026-04-19 - Pass raw values, not formatted strings
            self.table.add_row([
                None,
                str(h['id']),
                h['date'] if isinstance(h['date'], str) else h['date'].isoformat(),  # Raw ISO date
                h['type_display'],
                h['amount'],  # raw float
                h.get('currency_code', 'DA'),
                exchange_rate,  # raw float
                amount_da,  # raw float
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
