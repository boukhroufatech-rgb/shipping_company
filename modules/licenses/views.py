"""
Vues pour le module Traitements & Licences
Nouveau Module Spécialisé
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTabWidget, QDialog, QFormLayout,
    QLineEdit, QComboBox, QDateEdit, QTextEdit,
    QDialogButtonBox, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from datetime import datetime

from components.enhanced_table import EnhancedTableView
from components.amount_input import AmountInput
from components.smart_form import SmartFormDialog
from components.dialogs import (
    show_error, show_success, confirm_action, create_quick_add_layout
)
from utils.formatters import format_amount, format_date
from utils.constants import (
    SUPPLIER_TYPE_LICENSE
)

from modules.logistics.service import LogisticsService
from modules.currency.service import CurrencyService
from modules.treasury.service import TreasuryService
# [FIX] 2026-03-31: Suppression de l'import dupliqué de TreasuryService
from modules.currency.views import SuppliersTab
from modules.logistics.views import LicensesTab

# ============================================================================
# REAL DATABASE DIALOGS & TABS
# ============================================================================

# [CUSTOM] LicenseToBankTransferDialog: Transfert d'une licence vers un compte bancaire (Registre de Commerce)
# [WHY]: Nécessite un lien spécial entre la trésorerie et les comptes bancaires liés aux
#        registres de commerce (Licences). Affiche uniquement les comptes DA et filtre
#        les comptes bancaires associés aux registres de commerce uniquement.
#        Impossible d'utiliser TransferDialog standard car il ne supporte pas ce lien spécial.
# [DATE]: 2026-03-30
class LicenseToBankTransferDialog(QDialog):
    """Dialogue pour effectuer un transfert d'une licence vers un compte bancaire (Registre)"""
    def __init__(self, currency_service: CurrencyService, treasury_service: TreasuryService, parent=None):
        super().__init__(parent)
        self.currency_service = currency_service
        self.treasury_service = treasury_service
        self.setWindowTitle("Nouveau Transfert: Licence → Banque")
        self.setMinimumSize(450, 300)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Date
        self.inp_date = QDateEdit()
        self.inp_date.setCalendarPopup(True)
        self.inp_date.setDate(QDate.currentDate())
        self.inp_date.setFixedWidth(140)
        form.addRow("Date:", self.inp_date)

        # Montant
        self.inp_amount = AmountInput()
        form.addRow("Montant (DA):", self.inp_amount)

        # Destination (Registre)
        self.cmb_dest = QComboBox()
        self.cmb_dest_widget = create_quick_add_layout(self.cmb_dest, self._quick_add_account)
        form.addRow("Vers (Banque Registre):", self.cmb_dest_widget)

        # Caisse Source
        self.cmb_source = QComboBox()
        self.cmb_source_widget = create_quick_add_layout(self.cmb_source, self._quick_add_account)
        form.addRow("De (Caisse Source):", self.cmb_source_widget)

        # Réf / Note
        self.inp_note = QLineEdit()
        self.inp_note.setPlaceholderText("Ex: Alimentation compte pour licence...")
        self.inp_note.setText("Alimentation compte Registre de Commerce")
        form.addRow("Note:", self.inp_note)

        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._on_save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _load_data(self):
        # Charger les sources DA
        accounts = self.treasury_service.get_all_accounts(filter_status="active")
        for acc in accounts:
            if acc['currency_code'] in ["DA", "DZD"]:
                self.cmb_source.addItem(f"{acc['name']} ({format_amount(acc['balance'], 'DA')})", acc['id'])
                if acc['is_main']:
                    self.cmb_source.setCurrentIndex(self.cmb_source.count() - 1)

        # Charger les destinations (Comptes de registres liés)
        suppliers = self.currency_service.get_all_suppliers(supplier_type=SUPPLIER_TYPE_LICENSE)
        for s in suppliers:
            if s.get('bank_account_id'):
                # Fetch balance
                acc_info = next((a for a in accounts if a['id'] == s['bank_account_id']), None)
                bal_str = format_amount(acc_info['balance'], 'DA') if acc_info else "0 DA"
                self.cmb_dest.addItem(f"{s['name']} - {s['bank']} ({bal_str})", s['bank_account_id'])

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
                    # Recharger les combos
                    self._load_data()
            except Exception as e:
                show_error(self, "Erreur", f"Erreur lors de la creation du compte: {str(e)}")

    def _on_save(self):
        amount = self.inp_amount.get_amount()
        if amount <= 0:
            return show_error(self, "Erreur", "Veuillez saisir un montant supérieur à zéro.")
        
        src_id = self.cmb_source.currentData()
        dest_id = self.cmb_dest.currentData()
        
        if not src_id or not dest_id:
            return show_error(self, "Erreur", "Veuillez sélectionner les comptes source et destination.")
            
        success, msg = self.treasury_service.transfer_funds(
            src_id, dest_id, amount,
            description=self.inp_note.text(),
        )
        if success:
            show_success(self, "Succès", msg)
            self.accept()
        else:
            show_error(self, "Erreur", msg)


# [CUSTOM] LicenseAccountsTab: Affichage des comptes bancaires liés aux registres de commerce
# [WHY]: Nécessite de fusionner les données de deux sources différentes (Treasury + Currency Suppliers)
#        pour afficher les comptes bancaires générés automatiquement lors de l'ajout d'un registre
#        de commerce. Cet affichage est spécifique au module Licences et ne s'applique pas aux
#        autres modules.
# [DATE]: 2026-03-30
class LicenseAccountsTab(QWidget):
    """Affichage en temps réel des comptes bancaires générés des registres"""
    def __init__(self, currency_service: CurrencyService, treasury_service: TreasuryService):
        super().__init__()
        self.currency_service = currency_service
        self.treasury_service = treasury_service
        layout = QVBoxLayout(self)

        self.table = EnhancedTableView(table_id="license_bank_accounts")
        self.table.set_headers(["N°", "ID", "Propriétaire (RC)", "N° Registre", "Banque", "Solde (DA)"])
        self.table.refreshClicked.connect(self.load_data)
        layout.addWidget(self.table)
        
    def load_data(self):
        accounts = self.treasury_service.get_all_accounts(filter_status="all")
        suppliers = self.currency_service.get_all_suppliers(supplier_type=SUPPLIER_TYPE_LICENSE)

        self.table.clear_rows()
        for s in suppliers:
            if s.get('bank_account_id'):
                acc = next((a for a in accounts if a['id'] == s['bank_account_id']), None)
                bal = acc['balance'] if acc else 0.0
                owner_name = s.get('commercial_register_name') or s.get('name', '')
                register = s.get('register_number', '')
                bank = s.get('bank', '')

                self.table.add_row([
                    None,
                    str(s['id']),
                    owner_name,
                    register,
                    bank,
                    format_amount(bal, "DA")
                ])
        self.table.resize_columns_to_contents()


# [CUSTOM] LicenseTransfersTab: Historique des transferts vers les comptes des registres de commerce
# [WHY]: Nécessite un filtrage spécial des transactions liées uniquement aux comptes bancaires
#        des registres de commerce. Affiche uniquement les transferts CREDIT vers les comptes
#        de registre, avec liaison aux informations du fournisseur. Cet onglet est spécifique
#        au module Licences et ne s'applique pas à la trésorerie générale.
# [DATE]: 2026-03-30
class LicenseTransfersTab(QWidget):
    """Historique des transferts DA vers les registres"""
    def __init__(self, currency_service: CurrencyService, treasury_service: TreasuryService):
        super().__init__()
        self.currency_service = currency_service
        self.treasury_service = treasury_service
        layout = QVBoxLayout(self)

        self.table = EnhancedTableView(table_id="license_bank_transfers")
        self.table.set_headers(["N°", "ID", "Date", "Montant (DA)", "De (Caisse)", "Vers (Banque)", "Note"])
        
        # Action dans la table "Même ligne que les autres boutons"
        self.table.add_action_button("+ Nouveau Transfert", "🔄", self._add_transfer)
        self.table.editClicked.connect(self._edit_transfer)
        self.table.deleteClicked.connect(self._delete_transfer)
        self.table.restoreClicked.connect(self._restore_transfer)
        self.table.refreshClicked.connect(self.load_data)
        self.table.status_filter.statusChanged.connect(self.load_data)
        
        layout.addWidget(self.table)

    def load_data(self):
        suppliers = self.currency_service.get_all_suppliers(supplier_type=SUPPLIER_TYPE_LICENSE)
        license_account_ids = [s['bank_account_id'] for s in suppliers if s.get('bank_account_id')]

        transactions = self.treasury_service.get_all_transactions()
        all_accounts = self.treasury_service.get_all_accounts(filter_status="all")
        account_names = {a['id']: a['name'] for a in all_accounts}

        self.table.clear_rows()
        for t in transactions:
            if t['type'] == 'CREDIT' and t['account_id'] in license_account_ids:
                supplier = next((s for s in suppliers if s.get('bank_account_id') == t['account_id']), None)
                dest_name = f"{supplier['name']} - {supplier['bank']}" if supplier else "Inconnu"

                # Trouver le compte source via la reference
                ref = t.get('reference', '')
                debit_trans = next(
                    (tr for tr in transactions if tr.get('reference') == ref and tr['type'] == 'DEBIT'),
                    None
                )
                source_name = account_names.get(debit_trans['account_id'], "Trésorerie") if debit_trans else "Trésorerie"

                self.table.add_row([
                    None,
                    str(t['id']),
                    format_date(t['date']),
                    format_amount(t['amount'], "DA"),
                    source_name,
                    dest_name,
                    t['description']
                ])
        self.table.resize_columns_to_contents()

    def _add_transfer(self):
        dialog = LicenseToBankTransferDialog(self.currency_service, self.treasury_service, self)
        if dialog.exec():
            self.load_data()
            if hasattr(self.parent(), 'dataChanged'):
                self.parent().dataChanged.emit()

    def _get_selected_transaction(self):
        """Retourne la transaction CREDIT sélectionnée ou None"""
        selected = self.table.get_selected_rows()
        if not selected:
            show_error(self, "Erreur", "Veuillez sélectionner un transfert.")
            return None
        trans_id = int(self.table.get_row_data(selected[0])[1])
        transaction = self.treasury_service.get_transaction(trans_id)
        if not transaction:
            show_error(self, "Erreur", "Transaction introuvable.")
            return None
        return transaction

    def _edit_transfer(self):
        """Modifier le montant et la note d'un transfert"""
        credit_trans = self._get_selected_transaction()
        if not credit_trans:
            return

        # Trouver la transaction DEBIT liée par référence
        ref = credit_trans.get('reference', '')
        all_transactions = self.treasury_service.get_all_transactions(limit=500)
        debit_trans = next(
            (t for t in all_transactions if t.get('reference') == ref and t['type'] == 'DEBIT'),
            None
        )

        # Charger les infos pour l'affichage
        all_accounts = self.treasury_service.get_all_accounts(filter_status="all")
        account_names = {a['id']: a['name'] for a in all_accounts}
        source_name = account_names.get(debit_trans['account_id'], "Inconnu") if debit_trans else "Inconnu"
        dest_name = account_names.get(credit_trans['account_id'], "Inconnu")

        # Dialog de modification
        dialog = QDialog(self)
        dialog.setWindowTitle("Modifier le Transfert")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        lbl_source = QLabel(source_name)
        lbl_source.setStyleSheet("font-weight: bold; color: #58a6ff;")
        form.addRow("De (Source):", lbl_source)

        lbl_dest = QLabel(dest_name)
        lbl_dest.setStyleSheet("font-weight: bold; color: #58a6ff;")
        form.addRow("Vers (Destination):", lbl_dest)

        inp_amount = AmountInput()
        inp_amount.setValue(credit_trans['amount'])
        form.addRow("Montant (DA):", inp_amount)

        inp_note = QLineEdit()
        inp_note.setText(credit_trans.get('description', ''))
        form.addRow("Note:", inp_note)

        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(btns)

        def on_save():
            new_amount = inp_amount.get_amount()
            if new_amount <= 0:
                return show_error(dialog, "Erreur", "Montant invalide.")

            if not confirm_action(dialog, "Confirmer la modification",
                                  f"Le transfert sera modifié:\n\n"
                                  f"Ancien montant: {format_amount(credit_trans['amount'], 'DA')}\n"
                                  f"Nouveau montant: {format_amount(new_amount, 'DA')}\n\n"
                                  "Les soldes seront réajustés automatiquement."):
                return

            # Annuler les deux anciennes transactions (remet les soldes)
            if debit_trans:
                self.treasury_service.delete_transaction(debit_trans['id'], user="admin")
            self.treasury_service.delete_transaction(credit_trans['id'], user="admin")

            # Créer les deux nouvelles transactions
            new_ref = ref or f"TRF-{datetime.now().strftime('%H%M%S')}"
            description = inp_note.text()

            # DEBIT depuis la source
            self.treasury_service.create_transaction(
                account_id=debit_trans['account_id'] if debit_trans else credit_trans['account_id'],
                transaction_type="DEBIT",
                amount=new_amount,
                description=description,
                reference=new_ref,
                category="TRANSFERT",
                user="admin"
            )

            # CREDIT vers la destination
            self.treasury_service.create_transaction(
                account_id=credit_trans['account_id'],
                transaction_type="CREDIT",
                amount=new_amount,
                description=description,
                reference=new_ref,
                category="TRANSFERT",
                user="admin"
            )

            show_success(dialog, "Succès", "Transfert modifié avec succès.")
            dialog.accept()
            self.load_data()
            if hasattr(self.parent(), 'dataChanged'):
                self.parent().dataChanged.emit()

        btns.accepted.connect(on_save)
        btns.rejected.connect(dialog.reject)
        dialog.exec()

    def _delete_transfer(self):
        """Annuler un transfert (supprime les DEUX transactions)"""
        credit_trans = self._get_selected_transaction()
        if not credit_trans:
            return

        ref = credit_trans.get('reference', '')
        amount = credit_trans['amount']

        if not confirm_action(self, "Annuler le Transfert",
                              f"Voulez-vous vraiment annuler ce transfert ?\n\n"
                              f"Montant: {format_amount(amount, 'DA')}\n"
                              f"Référence: {ref}\n\n"
                              "Les soldes des deux comptes seront réajustés."):
            return

        # Trouver la transaction DEBIT liée
        all_transactions = self.treasury_service.get_all_transactions(limit=500)
        debit_trans = next(
            (t for t in all_transactions if t.get('reference') == ref and t['type'] == 'DEBIT'),
            None
        )

        # Annuler les deux transactions
        if debit_trans:
            success1, msg1 = self.treasury_service.delete_transaction(debit_trans['id'], user="admin")
        else:
            success1, msg1 = True, ""

        success2, msg2 = self.treasury_service.delete_transaction(credit_trans['id'], user="admin")

        if success1 and success2:
            show_success(self, "Succès", "Transfert annulé avec succès.")
            self.load_data()
            if hasattr(self.parent(), 'dataChanged'):
                self.parent().dataChanged.emit()
        else:
            show_error(self, "Erreur", f"{msg1}\n{msg2}")

    def _restore_transfer(self):
        """Restaurer un transfert annulé (réactive les DEUX transactions)"""
        credit_trans = self._get_selected_transaction()
        if not credit_trans:
            return

        ref = credit_trans.get('reference', '')
        amount = credit_trans['amount']

        if not confirm_action(self, "Restaurer le Transfert",
                              f"Voulez-vous vraiment restaurer ce transfert ?\n\n"
                              f"Montant: {format_amount(amount, 'DA')}\n"
                              f"Référence: {ref}"):
            return

        # Trouver la transaction DEBIT liée
        all_transactions = self.treasury_service.get_all_transactions(limit=500)
        debit_trans = next(
            (t for t in all_transactions if t.get('reference') == ref and t['type'] == 'DEBIT'),
            None
        )

        # Restaurer les deux transactions
        if debit_trans:
            success1, msg1 = self.treasury_service.restore_transaction(debit_trans['id'], user="admin")
        else:
            success1, msg1 = True, ""

        success2, msg2 = self.treasury_service.restore_transaction(credit_trans['id'], user="admin")

        if success1 and success2:
            show_success(self, "Succès", "Transfert restauré avec succès.")
            self.load_data()
            if hasattr(self.parent(), 'dataChanged'):
                self.parent().dataChanged.emit()
        else:
            show_error(self, "Erreur", f"{msg1}\n{msg2}")

# ============================================================================
# MAIN VIEW
# ============================================================================

class LicensesView(QWidget):
    """Vue principale du module Licences (Nouveau)"""
    dataChanged = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.service = LogisticsService()
        self.currency_service = CurrencyService()
        self.treasury_service = TreasuryService()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # 1. Propriétaires de Licences (Filter: LICENSE)
        from modules.settings.service import SettingsService
        self.owners_tab = SuppliersTab(self.currency_service, self.treasury_service, SettingsService(), supplier_type_filter=SUPPLIER_TYPE_LICENSE)
        self.owners_tab.dataChanged.connect(self.refresh)
        self.owners_tab.dataChanged.connect(self.dataChanged.emit)
        self.tabs.addTab(self.owners_tab, "Titulaires")

        from modules.logistics.views import LicensesTab
        self.licenses_tab = LicensesTab(self.service, self.currency_service, self.treasury_service, SettingsService())
        self.licenses_tab.dataChanged.connect(self.refresh)
        self.licenses_tab.dataChanged.connect(self.dataChanged.emit)
        self.tabs.addTab(self.licenses_tab, "Licences")

        self.accounts_tab = LicenseAccountsTab(self.currency_service, self.treasury_service)
        self.tabs.addTab(self.accounts_tab, "Comptes Bancaires")

        self.transfers_tab = LicenseTransfersTab(self.currency_service, self.treasury_service)
        self.tabs.addTab(self.transfers_tab, "Transferts")
        
    def refresh(self):
        self.owners_tab.load_data()
        self.licenses_tab.load_data()
        self.accounts_tab.load_data()
        self.transfers_tab.load_data()
