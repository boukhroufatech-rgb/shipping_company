"""
Vues pour le module Trésorerie - Modèle de Référence (Golden Model)
Standardized & Purified
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QDialog,
    QFormLayout, QLineEdit, QTextEdit, QComboBox, QDateEdit, QPushButton,
    QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from datetime import datetime

from components.enhanced_table import EnhancedTableView
from components.smart_form import SmartFormDialog
from components.dialogs import (
    show_error, show_success, show_warning, confirm_delete, create_quick_add_layout, confirm_action
)
from utils.formatters import format_amount
from .service import TreasuryService
from modules.settings.service import SettingsService
from utils.constants import (
    TRANSACTION_TYPE_DEBIT, TRANSACTION_TYPE_CREDIT,
    ACCOUNT_SCHEMA, TRANSACTION_SCHEMA
)

# ============================================================================
# MAIN VIEW
# ============================================================================

class TreasuryView(QWidget):
    """Vue principale du module Trésorerie (Standardized Version)"""
    dataChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = TreasuryService()
        self.settings_service = SettingsService()
        self._setup_ui()
        self.load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.tabs = QTabWidget()
        self.accounts_tab = AccountsTab(self.service, self.settings_service)
        self.transfers_tab = TransfersTab(self.service, self.settings_service)
        self.transactions_tab = TransactionsTab(self.service, self.settings_service)

        self.tabs.addTab(self.accounts_tab, "Comptes")
        self.tabs.addTab(self.transfers_tab, "Transferts")
        self.tabs.addTab(self.transactions_tab, "Journal")

        layout.addWidget(self.tabs)

    def load_data(self):
        self.accounts_tab.load_data()
        self.transfers_tab.load_data()
        self.transactions_tab.load_data()

    def refresh(self):
        self.load_data()


# ============================================================================
# ACCOUNTS TAB
# ============================================================================

class AccountsTab(QWidget):
    """Onglet de gestion des comptes (Standardized)"""
    
    def __init__(self, service, settings_service, parent=None):
        super().__init__(parent)
        self.service = service
        self.settings_service = settings_service
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.table = EnhancedTableView(table_id="treasury_accounts")
        self.table.set_headers_from_schema("treasury_accounts")  # [GOLDEN PRINCIPLE] schema centralisé
        
        self.table.addClicked.connect(self.add_account)
        self.table.editClicked.connect(self.edit_account)
        self.table.deleteClicked.connect(self.delete_account)
        self.table.restoreClicked.connect(self.restore_account)
        self.table.refreshClicked.connect(self.load_data)
        self.table.status_filter.statusChanged.connect(self.load_data)
        
        layout.addWidget(self.table)
    
    def load_data(self):
        filter_status = self.table.status_filter.get_filter()
        self.table.update_actions_for_status(filter_status)
        
        accounts = self.service.get_all_accounts(filter_status=filter_status, currency_filter="DA", account_type_filter="CAISSE,BANQUE,CCP")
        
        self.table.clear_rows()
        for acc in accounts:
            self.table.add_row([
                None,
                str(acc['id']),
                acc['code'],
                acc['name'],
                acc['account_type'],
                acc['currency_code'],
                acc.get('initial_balance', 0),   # [GOLDEN PRINCIPLE] raw float
                acc['balance'],                   # [GOLDEN PRINCIPLE] raw float
                "⭐" if acc['is_main'] else ""
            ], is_active=acc['is_active'])
        self.table.resize_columns_to_contents()

    def _get_account_schema(self, dialog_ref=None):
        types = self.service.get_all_account_types()
        type_options = [(t['name'], t['name']) for t in types]
        
        def on_add_type(combo):
            from components.catalog_dialog import GenericCatalogDialog
            dialog = GenericCatalogDialog(
                title="Types de Comptes (Khazina)",
                get_data_func=lambda include_inactive=False: [{"id": t['id'], "name": t['name']} for t in self.service.get_all_account_types(include_inactive=include_inactive)],
                create_data_func=lambda name, desc: self.service.create_account_type(name, desc),
                delete_data_func=lambda tid: self.service.delete_account_type(tid),
                restore_data_func=lambda tid: self.service.restore_account_type(tid),
                primary_placeholder="Nom du type de compte",
                secondary_placeholder="",
                headers=["N", "ID", "Type de Compte"],
                parent=self
            )
            dialog.exec()
            # Refresh combo
            combo.clear()
            new_types = self.service.get_all_account_types()
            idx = 0
            for i, t in enumerate(new_types):
                combo.addItem(t['name'], t['name'])
                if t['name'] == combo.currentText(): idx = i
            combo.setCurrentIndex(combo.count() - 1)
        
        schema = []
        for field in ACCOUNT_SCHEMA:
            f = field.copy()
            if f['name'] == 'account_type':
                f['options'] = type_options
                f['quick_add_callback'] = on_add_type
            schema.append(f)
        return schema

    def add_account(self):
        schema = self._get_account_schema()
        dialog = SmartFormDialog("Nouveau Compte", schema, parent=self)
        if dialog.exec():
            results = dialog.get_results()
            success, message, _ = self.service.create_account(
                name=results['name'], code=results['code'], 
                account_type=results['account_type'], currency_id=results['currency_id'],
                description=results.get('description', ""),
                initial_balance=results.get('initial_balance', 0.0)
            )
            if success:
                show_success(self, "Succès", message)
                self.load_data()
                if hasattr(self.parent(), 'dataChanged'): self.parent().dataChanged.emit()
            else:
                show_error(self, "Erreur", message)

    def edit_account(self, row: int):
        account_id = int(self.table.get_row_data(row)[1])
        account = self.service.get_account(account_id)
        if account:
            schema = self._get_account_schema()
            dialog = SmartFormDialog("Modifier Compte", schema, account, parent=self)
            if dialog.exec():
                results = dialog.get_results()
                success, message = self.service.update_account(
                    account_id, results['name'], results['account_type'], 
                    results['currency_id'], results.get('description', ""),
                    results.get('initial_balance')
                )
                if success:
                    show_success(self, "Succès", message)
                    self.load_data()
                    if hasattr(self.parent(), 'dataChanged'): self.parent().dataChanged.emit()
                else:
                    show_error(self, "Erreur", message)

    def delete_account(self, row: int):
        from components.dialogs import confirm_action, show_warning
        row_data = self.table.get_row_data(row)
        account_id = int(row_data[1])
        account_name = row_data[3]
        is_main = row_data[8] == "⭐"  # [PROTECTION] 2026-04-18 - Compte principal protégé
        if is_main:
            show_warning(self, "Action interdite", f"Le compte principal '{account_name}' ne peut pas être archivé.")
            return
        if confirm_action(self, "Archiver", f"Voulez-vous vraiment archiver le compte '{account_name}' ?"):
            success, message = self.service.delete_account(account_id)
            if success:
                show_success(self, "Succès", message)
                self.load_data()
                if hasattr(self.parent(), 'dataChanged'): self.parent().dataChanged.emit()
            else:
                show_error(self, "Erreur", message)

    def restore_account(self, row: int):
        from components.dialogs import confirm_action
        account_id = int(self.table.get_row_data(row)[1])
        account_name = self.table.get_row_data(row)[3]
        if confirm_action(self, "Restaurer", f"Voulez-vous réactiver le compte '{account_name}' ?"):
            success, message = self.service.restore_account(account_id)
            if success:
                show_success(self, "Succès", message)
                self.load_data()
                if hasattr(self.parent(), 'dataChanged'): self.parent().dataChanged.emit()
            else:
                show_error(self, "Erreur", message)


# ============================================================================
# TRANSACTIONS TAB
# ============================================================================

class TransactionsTab(QWidget):
    """Journal des opérations (Standardized)"""

    def __init__(self, service, settings_service, parent=None):
        super().__init__(parent)
        self.service = service
        self.settings_service = settings_service
        self._setup_ui()
        self._load_account_selector()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Filtres
        filter_layout = QHBoxLayout()
        
        # Account Selector
        self.account_selector = QComboBox()
        self.account_selector.addItem("--- Tous les Comptes (Global) ---", None)
        self.account_selector.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(QLabel("Compte:"))
        filter_layout.addWidget(self.account_selector)
        
        # Source Filter
        self.source_filter = QComboBox()
        self.source_filter.addItem("--- Toutes les Sources ---", None)
        self.source_filter.addItem("💰 Caisse Interne", "CAISSE")
        self.source_filter.addItem("👤 Clients", "CLIENT")
        self.source_filter.addItem("🏢 Fournisseurs", "FOURNISSEUR")
        self.source_filter.addItem("💱 Devises", "DEVISE")
        self.source_filter.addItem("🤝 Partenaires", "PARTNER")
        self.source_filter.addItem("📋 Dépenses", "EXPENSE")
        self.source_filter.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(QLabel("Source:"))
        filter_layout.addWidget(self.source_filter)
        
        # Status Filter
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItem("--- Tous les Statuts ---", None)
        self.status_filter_combo.addItem("✅ Validée", "VALIDEE")
        self.status_filter_combo.addItem("⏳ En attente", "EN_ATTENTE")
        self.status_filter_combo.addItem("🔄 En cours", "EN_COURS")
        self.status_filter_combo.addItem("❌ Annulée", "ANNULEE")
        self.status_filter_combo.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(QLabel("Statut:"))
        filter_layout.addWidget(self.status_filter_combo)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Table avec 11 colonnes
        self.table = EnhancedTableView(table_id="treasury_transactions")
        self.table.set_headers([
            "N°", "ID", "Date", "Source", "Compte", 
            "Type", "Montant", "Moyen Paiement", 
            "Catégorie", "Statut", "Utilisateur", "Observation"
        ])

        # Actions (pas de modification depuis le journal)
        self.table.addClicked.connect(self.add_transaction)
        # Pas de edit/delete - seulement restauration
        self.table.restoreClicked.connect(self.restore_transaction)
        self.table.refreshClicked.connect(self.load_data)
        self.table.status_filter.statusChanged.connect(self.load_data)

        layout.addWidget(self.table)

    def _load_account_selector(self):
        self.account_selector.blockSignals(True)
        self.account_selector.clear()
        self.account_selector.addItem("--- Tous les Comptes (Global) ---", None)
        accounts = self.service.get_all_accounts(currency_filter="DA", account_type_filter="CAISSE,BANQUE,CCP")
        for acc in accounts:
            self.account_selector.addItem(acc['name'], acc['id'])
        self.account_selector.blockSignals(False)

    def load_data(self):
        account_id = self.account_selector.currentData()
        filter_status = self.table.status_filter.get_filter()
        source_filter = self.source_filter.currentData()
        status_filter = self.status_filter_combo.currentData()

        if account_id:
            transactions = self.service.get_account_transactions(account_id, limit=500)
            transactions.sort(key=lambda x: x['date'])
        else:
            transactions = self.service.get_all_transactions(
                limit=500, 
                filter_status=filter_status, 
                currency_filter="DA",
                source_filter=source_filter,
                status_filter=status_filter
            )
        
        self.table.update_actions_for_status(filter_status)
        self.table.clear_rows()
        running_bal = 0.0

        # Icônes pour les sources
        source_icons = {
            "CAISSE": "💰",
            "CLIENT": "👤",
            "FOURNISSEUR": "🏢",
            "DEVISE": "💱",
            "PARTNER": "🤝",
            "EXPENSE": "📋"
        }
        
        # Icônes pour les statuts
        status_icons = {
            "VALIDEE": "✅",
            "EN_ATTENTE": "⏳",
            "EN_COURS": "🔄",
            "ANNULEE": "❌"
        }
        
        # Moyens de paiement
        payment_labels = {
            "ESPECES": "Espèces 💵",
            "CHEQUE": "Chèque 📝",
            "VIREMENT": "Virement 🏦",
            "TRAITE": "Traite",
            "EFFET": "Effet",
            "AUTRE": "Autre"
        }

        for trans in transactions:
            is_credit = trans['type'] == TRANSACTION_TYPE_CREDIT

            if account_id:
                if is_credit: running_bal += trans['amount']
                else: running_bal -= trans['amount']
                reste_str = format_amount(running_bal, "DA")
            else:
                reste_str = "---"

            # Format source avec icône
            source_display = f"{source_icons.get(trans.get('source', 'CAISSE'), '📝')} {trans.get('source', 'CAISSE')}"
            
            # Format statut avec icône
            status_display = f"{status_icons.get(trans.get('status', 'VALIDEE'), '✅')} {trans.get('status', 'VALIDEE')}"
            
            # Format moyen de paiement
            payment_display = payment_labels.get(trans.get('payment_method', 'ESPECES'), "Espèces")
            
            # Utilisateur
            user_display = trans.get('created_by', 'System')
            
            # Observation/Notes
            obs_display = trans.get('notes', '') or ''

            # Format montant avec signe (+/-)
            is_credit = trans['type'] == TRANSACTION_TYPE_CREDIT
            amount_str = f"+ {format_amount(trans['amount'], 'DA')}" if is_credit else f"- {format_amount(trans['amount'], 'DA')}"

            row_idx = self.table.add_row([
                None,  # N°
                str(trans['id']),  # ID
                trans['date'].strftime("%d/%m/%Y"),  # Date
                source_display,  # Source
                trans['account_name'],  # Compte
                trans['type'],  # Type
                amount_str,  # Montant avec signe
                payment_display,  # Moyen de paiement
                trans.get('category', 'DIVERS'),  # Catégorie
                status_display,  # Statut
                user_display,  # Utilisateur
                obs_display  # Observation
            ], is_active=trans['is_active'])

            # Coloration des transactions
            if trans['is_active']:
                color = "#072b25" if is_credit else "#2b0707"
                self.table.set_row_background_color(row_idx, color)
            else:
                self.table.set_row_background_color(row_idx, "#1a1a1a")

        self.table.resize_columns_to_contents()

    def _get_transaction_dialog(self, edit_id=None):
        # Build dynamic options for accounts
        accounts = self.service.get_all_accounts(currency_filter="DA", account_type_filter="CAISSE,BANQUE,CCP")
        acc_options = [(acc['name'], acc['id']) for acc in accounts]
        
        schema = TRANSACTION_SCHEMA.copy()
        for field in schema:
            if field['name'] == 'account_id': field['options'] = acc_options
            
        initial_data = {}
        if edit_id:
            trans = self.service.get_transaction(edit_id)
            if trans: initial_data = trans
            
        return SmartFormDialog("Modifier Opération" if edit_id else "Nouvelle Opération", schema, initial_data, parent=self)

    def add_transaction(self):
        """Ajouter une transaction interne (CAISSE uniquement)"""
        dialog = self._get_transaction_dialog()
        if dialog.exec():
            results = dialog.get_results()
            success, message, _ = self.service.create_transaction(
                account_id=results['account_id'],
                transaction_type=results['type'],
                amount=results['amount'],
                description=results['description'],
                reference=results.get('reference', ''),
                date=results.get('date'),
                user="admin",
                source="CAISSE",  # Operation interne
                source_id=None,
                payment_method=results.get('payment_method', 'ESPECES'),
                category=results.get('category', 'DIVERS'),
                status=results.get('status', 'VALIDEE'),
                notes=results.get('notes', '')
            )
            if success:
                show_success(self, "Succès", message)
                self.load_data()
                if hasattr(self.parent(), 'dataChanged'): self.parent().dataChanged.emit()
            else:
                show_error(self, "Erreur", message)

    def edit_transaction(self, row: int):
        """
        MODIFICATION INTERDITE DEPUIS LE JOURNAL
        L'utilisateur doit modifier depuis la source
        """
        trans_id = int(self.table.get_row_data(row)[1])
        source = self.table.get_row_data(row)[3]  # Colonne Source
        
        show_warning(
            self, 
            "Modification non autorisée",
            f"⚠️ Impossible de modifier cette opération depuis le journal général.\n\n"
            f"Source: {source}\n\n"
            f"Pour modifier cette opération, veuillez vous rendre dans le module correspondant:\n"
            f"  • Operations Caisse → Onglet 'Opérations Internes'\n"
            f"  • Clients → Journal des opérations client\n"
            f"  • Fournisseurs → Journal des paiements\n"
            f"  • Devises → Historique des achats\n\n"
            f"Le journal général est en lecture seule pour garantir l'intégrité des données."
        )

    def delete_transaction(self, row: int):
        """
        SUPPRESSION INTERDITE DEPUIS LE JOURNAL
        """
        show_warning(
            self, 
            "Suppression non autorisée",
            "⚠️ Impossible de supprimer une opération depuis le journal général.\n\n"
            f"La suppression doit être faite depuis le module source.\n\n"
            f"Vous pouvez uniquement:\n"
            f"  • Annuler la transaction (si elle est de source CAISSE)\n"
            f"  • Restaurer une transaction annulée"
        )

    def restore_transaction(self, row: int):
        from components.dialogs import confirm_action
        trans_id = int(self.table.get_row_data(row)[1])
        if confirm_action(self, "Restaurer Transaction", "Voulez-vous réactiver cette transaction ?"):
            success, message = self.service.restore_transaction(trans_id, user="admin")
            if success:
                show_success(self, "Succès", message)
                self.load_data()
                if hasattr(self.parent(), 'dataChanged'): self.parent().dataChanged.emit()
            else:
                show_error(self, "Erreur", message)


# ============================================================================
# TRANSFERS TAB (NOUVEAU - Gestion des transferts entre comptes)
# ============================================================================

class TransfersTab(QWidget):
    """Onglet de gestion des transferts entre comptes"""

    def __init__(self, service, settings_service, parent=None):
        super().__init__(parent)
        self.service = service
        self.settings_service = settings_service
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Header removed - using tab name instead

        # Filtres
        filter_layout = QHBoxLayout()
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setFixedWidth(140)
        filter_layout.addWidget(QLabel("Du:"))
        filter_layout.addWidget(self.date_from)
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setFixedWidth(140)
        filter_layout.addWidget(QLabel("Au:"))
        filter_layout.addWidget(self.date_to)
        
        self.source_filter = QComboBox()
        self.source_filter.addItem("--- Tous les comptes source ---", None)
        accounts = self.service.get_all_accounts(currency_filter="DA", account_type_filter="CAISSE,BANQUE,CCP")
        for acc in accounts:
            self.source_filter.addItem(acc['name'], acc['id'])
        filter_layout.addWidget(QLabel("Compte Source:"))
        filter_layout.addWidget(self.source_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Table
        self.table = EnhancedTableView(table_id="transfers_table")
        self.table.set_headers([
            "N°", "ID", "Date", "De (Source)", "À (Destination)", 
            "Montant", "Référence", "Description", "Statut"
        ])

        # [CUSTOM] Actions: Utilise les boutons par defaut du EnhancedTableView
        # [WHY] Nouveau -> _add_transfer (ouvre TreasuryTransferDialog)
        # [WHY] Modifier -> _edit_transfer (ouvre TreasuryTransferDialog en mode edition)
        # [WHY] Supprimer -> _delete_transfer (suppression douce avec ajustement des soldes)
        # [DATE] 2026-04-07
        self.table.addClicked.connect(self._add_transfer)
        self.table.editClicked.connect(self._edit_transfer)
        self.table.deleteClicked.connect(self._delete_transfer)
        
        self.table.refreshClicked.connect(self.load_data)
        self.table.status_filter.statusChanged.connect(self.load_data)
        self.date_from.dateChanged.connect(self.load_data)
        self.date_to.dateChanged.connect(self.load_data)
        self.source_filter.currentIndexChanged.connect(self.load_data)

        layout.addWidget(self.table)

    def load_data(self):
        """Charger tous les transferts (groupés par référence - une seule ligne par transfert)"""
        filter_status = self.table.status_filter.get_filter()
        source_account = self.source_filter.currentData()

        # Récupérer toutes les transactions avec filtre
        transactions = self.service.get_all_transactions(
            limit=1000,
            filter_status=filter_status,
            currency_filter="DA"
        )

        # Filtrer pour ne garder que les transferts
        all_transfers = [t for t in transactions if t.get('category') == 'TRANSFERT']

        # Filtrer par date
        date_from = self.date_from.date().toPyDate()
        date_to = self.date_to.date().toPyDate()
        all_transfers = [t for t in all_transfers if date_from <= t['date'].date() <= date_to]

        # Filtrer par compte source si sélectionné
        if source_account:
            all_transfers = [t for t in all_transfers if t.get('account_id') == source_account]

        # Trier par date décroissante
        all_transfers.sort(key=lambda x: x['date'], reverse=True)

        self.table.update_actions_for_status(filter_status)
        self.table.clear_rows()

        status_icons = {
            "VALIDEE": "Validee",
            "EN_ATTENTE": "En attente",
            "EN_COURS": "En cours",
            "ANNULEE": "Annulee"
        }

        # Grouper par référence pour afficher chaque transfert sur une seule ligne
        grouped = {}
        for t in all_transfers:
            ref = t.get('reference', f"ID-{t['id']}")
            if ref not in grouped:
                grouped[ref] = {'debit': None, 'credit': None, 'is_active': True}
            if t['type'] == TRANSACTION_TYPE_DEBIT:
                grouped[ref]['debit'] = t
            else:
                grouped[ref]['credit'] = t
            if not t['is_active']:
                grouped[ref]['is_active'] = False

        # Afficher chaque transfert comme une seule ligne
        row_num = 0
        for ref, data in grouped.items():
            row_num += 1
            debit = data['debit']
            credit = data['credit']
            is_active = data['is_active']

            # Utiliser les données du DEBIT (ou CREDIT si DEBIT manquant)
            main_trans = debit or credit
            source_name = debit['account_name'] if debit else "---"
            dest_name = credit['account_name'] if credit else "---"
            amount = debit['amount'] if debit else (credit['amount'] if credit else 0)
            trans_date = main_trans['date'].strftime("%d/%m/%Y")
            description = main_trans.get('description', '')[:50]
            status = main_trans.get('status', 'VALIDEE')

            row_idx = self.table.add_row([
                str(row_num),
                str(main_trans['id']),
                trans_date,
                source_name,
                dest_name,
                format_amount(amount, "DA"),
                ref,
                description,
                status_icons.get(status, status)
            ], is_active=is_active)

            if not is_active:
                self.table.set_row_background_color(row_idx, "#1a1a1a")

        self.table.resize_columns_to_contents()

    def _add_transfer(self):
        """Ouvrir le dialog de transfert"""
        dialog = TreasuryTransferDialog(self.service, self)
        if dialog.exec():
            self.load_data()
            if hasattr(self.parent(), 'dataChanged'):
                self.parent().dataChanged.emit()

    def _edit_transfer(self):
        """Modifier un transfert existant"""
        selected_rows = self.table.get_selected_rows()
        if not selected_rows:
            show_warning(self, "Sélection", "Veuillez sélectionner un transfert")
            return

        row = selected_rows[0]
        trans_id = int(self.table.get_row_data(row)[1])
        dialog = TreasuryTransferDialog(self.service, edit_id=trans_id, parent=self)
        if dialog.exec():
            self.load_data()
            if hasattr(self.parent(), 'dataChanged'):
                self.parent().dataChanged.emit()

    def _view_transfer(self):
        """Voir les détails d'un transfert"""
        selected_rows = self.table.get_selected_rows()
        if not selected_rows:
            show_warning(self, "Sélection", "Veuillez sélectionner un transfert")
            return

        row = selected_rows[0]
        trans_id = int(self.table.get_row_data(row)[1])
        trans = self.service.get_transaction(trans_id)

        if trans:
            details = (
                f"📋 Détails du Transfert\n\n"
                f"ID: {trans['id']}\n"
                f"Date: {trans['date'].strftime('%d/%m/%Y %H:%M')}\n"
                f"Compte: {trans.get('account_name', 'N/A')}\n"
                f"Type: {trans['type']}\n"
                f"Montant: {format_amount(trans['amount'], 'DA')}\n"
                f"Référence: {trans.get('reference', 'N/A')}\n"
                f"Description: {trans.get('description', 'N/A')}\n"
                f"Statut: {trans.get('status', 'VALIDEE')}\n"
                f"Créé par: {trans.get('created_by', 'System')}\n"
                f"Observation: {trans.get('notes', 'Aucune')}"
            )
            QMessageBox.information(self, "Détails du Transfert", details)

    def _delete_transfer(self):
        """Supprimer (annuler) un transfert - suppression douce avec ajustement des soldes"""
        selected_rows = self.table.get_selected_rows()
        if not selected_rows:
            show_warning(self, "Sélection", "Veuillez sélectionner un transfert")
            return
        
        row = selected_rows[0]
        trans_id = int(self.table.get_row_data(row)[1])
        
        if confirm_action(self, "Annuler le Transfert", "Voulez-vous vraiment annuler ce transfert ?\n\nCette opération va réajuster les soldes des deux comptes."):
            success, message = self.service.delete_transaction(trans_id, user="admin")
            if success:
                show_success(self, "Succès", message)
                self.load_data()
            else:
                show_error(self, "Erreur", message)


# ============================================================================
# TRANSFER DIALOG (Kept Custom for logic)
# ============================================================================

class TreasuryTransferDialog(QDialog):
    """Dialogue pour effectuer un transfert entre comptes Treasury"""
    def __init__(self, service, edit_id=None, parent=None):
        super().__init__(parent)
        self.service = service
        self.edit_id = edit_id
        self.setWindowTitle("Modifier le Transfert" if edit_id else "Transférer entre comptes Treasury")
        self.setFixedWidth(500)
        self._setup_ui()
        self._load_accounts()
        if edit_id:
            self._load_transfer_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setFixedWidth(140)

        self.from_account = QComboBox()
        self.from_account.currentIndexChanged.connect(self._update_from_balance)
        
        # [UNIFIED] 2026-04-08 - Balance Display (Composant unifié)
        from components.balance_display import BalanceDisplay
        self.from_balance_display = BalanceDisplay("account")
        self.from_account.currentIndexChanged.connect(lambda idx: self.from_balance_display.update_from_combo(self.from_account, self.service))
        self.from_account_widget = create_quick_add_layout(self.from_account, self._quick_add_account)

        self.to_account = QComboBox()
        self.to_account.currentIndexChanged.connect(self._update_to_balance)
        
        # [UNIFIED] 2026-04-08 - Balance Display (Composant unifié)
        self.to_balance_display = BalanceDisplay("account")
        self.to_account.currentIndexChanged.connect(lambda idx: self.to_balance_display.update_from_combo(self.to_account, self.service))
        self.to_account_widget = create_quick_add_layout(self.to_account, self._quick_add_account)

        self.amount = SmartFormDialog._create_widget_by_type(None, {'type': 'number'})
        self.amount.valueChanged.connect(self._update_simulation)

        # [UNIFIED] 2026-04-08 - Simulation Display (Composant unifié)
        from components.simulation_display import AmountSimulationLabel
        self.sim_label = AmountSimulationLabel()

        self.payment_method = QComboBox()
        self.payment_method.addItem("Espèces 💵", "ESPECES")
        self.payment_method.addItem("Chèque 📝", "CHEQUE")
        self.payment_method.addItem("Virement 🏦", "VIREMENT")
        self.payment_method.addItem("Traite", "TRAITE")

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(60)

        form.addRow("📅 Date de l'opération:", self.date_input)
        form.addRow("Depuis (Source):", self.from_account_widget)
        form.addRow("", self.from_balance_display)
        form.addRow("Vers (Destination):", self.to_account_widget)
        form.addRow("", self.to_balance_display)
        form.addRow("Montant (DA):", self.amount)
        form.addRow("", self.sim_label)
        form.addRow("Moyen de paiement:", self.payment_method)
        form.addRow("Motif:", self.notes)

        layout.addLayout(form)

        btns = QHBoxLayout()
        self.btn_save = QPushButton("Confirmer le Transfert")
        self.btn_save.clicked.connect(self.save)
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)
        btns.addWidget(self.btn_save)
        btns.addWidget(self.btn_cancel)
        layout.addLayout(btns)

    def _load_accounts(self):
        accounts = self.service.get_all_accounts(currency_filter="DA", account_type_filter="CAISSE,BANQUE,CCP")
        for acc in accounts:
            label = f"{acc['name']} (Solde: {format_amount(acc['balance'], 'DA')})"
            self.from_account.addItem(label, acc['id'])
            self.to_account.addItem(label, acc['id'])

        # [UNIFIED] 2026-04-08 - Initial balance update via component
        self.from_balance_display.update_from_combo(self.from_account, self.service)
        self.to_balance_display.update_from_combo(self.to_account, self.service)

    def _load_transfer_data(self):
        """Charge les données d'un transfert existant (les 2 transactions)"""
        trans = self.service.get_transaction(self.edit_id)
        if not trans:
            return

        ref = trans.get('reference', '')
        all_trans = self.service.get_all_transactions(limit=1000, filter_status="all", currency_filter="DA")
        paired = [t for t in all_trans if t.get('reference') == ref and t.get('category') == 'TRANSFERT']

        debit_trans = next((t for t in paired if t['type'] == TRANSACTION_TYPE_DEBIT), trans)
        credit_trans = next((t for t in paired if t['type'] == TRANSACTION_TYPE_CREDIT), None)

        self.date_input.setDate(debit_trans['date'].date() if hasattr(debit_trans['date'], 'date') else debit_trans['date'])
        self.amount.setValue(debit_trans['amount'])
        self.notes.setPlainText(debit_trans.get('notes', '') or debit_trans.get('description', ''))

        for i in range(self.from_account.count()):
            if self.from_account.itemData(i) == debit_trans['account_id']:
                self.from_account.setCurrentIndex(i)
                break
        if credit_trans:
            for i in range(self.to_account.count()):
                if self.to_account.itemData(i) == credit_trans['account_id']:
                    self.to_account.setCurrentIndex(i)
                    break

        pm = debit_trans.get('payment_method', 'VIREMENT')
        for i in range(self.payment_method.count()):
            if self.payment_method.itemData(i) == pm:
                self.payment_method.setCurrentIndex(i)
                break

        self._update_simulation()

    def _quick_add_account(self, combo):
        """Quick Add account (regle 10)"""
        from utils.constants import ACCOUNT_SCHEMA
        dialog = SmartFormDialog("Nouveau Compte", ACCOUNT_SCHEMA, parent=self)
        if dialog.exec():
            try:
                results = dialog.get_results()
                account = self.service.create_account(**results)
                if account:
                    label = f"{results['name']} (Solde: {format_amount(0, 'DA')})"
                    combo.addItem(label, account.id)
                    combo.setCurrentIndex(combo.count() - 1)
                    self._load_accounts()
            except Exception as e:
                show_error(self, "Erreur", f"Erreur lors de la creation du compte: {str(e)}")

    def _get_accounts_list(self):
        """Get current accounts list for balance lookup"""
        return self.service.get_all_accounts(currency_filter="DA", account_type_filter="CAISSE,BANQUE,CCP")

    def _update_from_balance(self):
        pass  # [UNIFIED] 2026-04-08 - Handled by BalanceDisplay component

    def _update_to_balance(self):
        pass  # [UNIFIED] 2026-04-08 - Handled by BalanceDisplay component

    def _update_simulation(self):
        """Show transfer simulation - how balances will change"""
        from_aid = self.from_account.currentData()
        if not from_aid:
            self.sim_label.setText("")
            return

        accounts = self._get_accounts_list()
        from_balance = 0
        for acc in accounts:
            if acc['id'] == from_aid:
                from_balance = acc['balance']
                break

        amount = self.amount.get_amount()
        new_balance = from_balance - amount

        if new_balance < 0:
            color = "#e74c3c"
            status = f"⚠️ Insuffisant! Manque: {abs(new_balance):,.2f} DA"
        elif new_balance == 0:
            color = "#2ecc71"
            status = "✅ Compte source vide"
        else:
            color = "#7d8590"
            status = f" Nouveau solde source: {new_balance:,.2f} DA"

        self.sim_label.setText(f"💡 Après transfert: <span style='color: {color}'>{status}</span>")

    def save(self):
        if self.from_account.currentData() == self.to_account.currentData():
            show_error(self, "Erreur", "Source et destination identiques.")
            return

        if self.edit_id:
            # Mode modification : annuler l'ancien transfert puis créer un nouveau
            old_trans = self.service.get_transaction(self.edit_id)
            if not old_trans:
                show_error(self, "Erreur", "Transfert introuvable.")
                return

            ref = old_trans.get('reference', '')
            all_trans = self.service.get_all_transactions(limit=1000, filter_status="all", currency_filter="DA")
            paired = [t for t in all_trans if t.get('reference') == ref and t.get('category') == 'TRANSFERT']

            # Annuler les anciennes transactions
            for t in paired:
                self.service.delete_transaction(t['id'])

            # Créer un nouveau transfert
            success, message = self.service.transfer_funds(
                self.from_account.currentData(),
                self.to_account.currentData(),
                self.amount.get_amount(),
                self.notes.toPlainText(),
                date=datetime.combine(self.date_input.date().toPyDate(), datetime.now().time()),
                payment_method=self.payment_method.currentData(),
                category="TRANSFERT",
                status="VALIDEE"
            )
        else:
            success, message = self.service.transfer_funds(
                self.from_account.currentData(),
                self.to_account.currentData(),
                self.amount.get_amount(),
                self.notes.toPlainText(),
                date=datetime.combine(self.date_input.date().toPyDate(), datetime.now().time()),
                payment_method=self.payment_method.currentData(),
                category="TRANSFERT",
                status="VALIDEE"
            )

        if success:
            show_success(self, "Succès", message)
            self.accept()
        else:
            show_error(self, "Erreur", message)


# ============================================================================
# SHARED: Quick Add Account (cross-module)
# ============================================================================

def quick_add_account(combo, treasury_service, parent=None, currency_filter=None):
    """
    Ouvre un dialogue pour ajouter rapidement un nouveau compte.
    Actualise le combo après la création.
    Utilisable depuis n'importe quel module.
    :param currency_filter: Code de devise pour filtrer (ex: "DA"). Si None, toutes les devises.
    """
    from components.smart_form import SmartFormDialog
    from utils.constants import ACCOUNT_SCHEMA
    from modules.currency.service import CurrencyService

    types = treasury_service.get_all_account_types()
    type_options = [(t['name'], t['name']) for t in types]
    cs = CurrencyService()
    if currency_filter:
        currencies = [c for c in cs.get_all_currencies() if c['code'] == currency_filter]
    else:
        currencies = cs.get_all_currencies()
    curr_options = [(f"{c['code']} ({c['name']})", c['id']) for c in currencies]

    schema = []
    for field in ACCOUNT_SCHEMA:
        f = field.copy()
        if f['name'] == 'account_type':
            f['options'] = type_options
        elif f['name'] == 'currency_id':
            f['options'] = curr_options
        schema.append(f)

    dialog = SmartFormDialog("Nouveau Compte", schema, parent=parent)
    if dialog.exec():
        results = dialog.get_results()
        success, message, new_id = treasury_service.create_account(**results)
        if success:
            combo.clear()
            if currency_filter:
                accounts = treasury_service.get_all_accounts(currency_filter=currency_filter, account_type_filter="CAISSE,BANQUE,CCP")
            else:
                accounts = treasury_service.get_all_accounts(account_type_filter="CAISSE,BANQUE,CCP")
            for a in accounts:
                combo.addItem(a['name'], a['id'])
            idx = combo.findData(new_id)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        else:
            show_error(parent, "Erreur", message)
