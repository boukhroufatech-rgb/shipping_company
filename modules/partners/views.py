from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QDialog, QFormLayout, 
    QLineEdit, QDialogButtonBox, QComboBox, QTextEdit, QLabel,
    QDateEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from datetime import datetime

from components.enhanced_table import EnhancedTableView
from components.amount_input import AmountInput
from components.smart_form import SmartFormDialog
from components.dialogs import show_success, show_error, confirm_delete
from utils.formatters import format_amount

from .service import PartnerService, TRANS_CONTRIBUTION, TRANS_WITHDRAWAL, TRANS_PROFIT

# ============================================================================
# SCHEMAS
# ============================================================================

PARTNER_SCHEMA = [
    {'name': 'name', 'label': 'Nom Prénom', 'type': 'text', 'required': True},
    {'name': 'phone', 'label': 'N° Téléphone', 'type': 'text'},
    {'name': 'email', 'label': 'E-Mail', 'type': 'text'},
    {'name': 'function', 'label': 'Fonction', 'type': 'text'},
]

# ============================================================================
# MAIN VIEW
# ============================================================================

class PartnersView(QWidget):
    """Vue principale du module Partenaires (Standardized & Purified)"""
    dataChanged = pyqtSignal()

    def __init__(self, treasury_service=None):
        super().__init__()
        self.service = PartnerService()
        self.treasury_service = treasury_service
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Table (N°/ID Pattern)
        self.table = EnhancedTableView(self, "partners_table")
        self.table.set_headers([
            "N°", "ID", "Nom Prénom", "N° Téléphone", "E-Mail", "Fonction",
            "M. Contributions", "% Contrib.", "M. Profit", "M. Surchats", "Reste", "Statut"
        ])

        # Actions Standard
        self.table.addClicked.connect(self._add_partner)
        self.table.editClicked.connect(self._edit_partner)
        self.table.deleteClicked.connect(self._delete_partner)
        self.table.restoreClicked.connect(self._restore_partner)
        self.table.refreshClicked.connect(self.refresh)
        self.table.status_filter.statusChanged.connect(self.refresh)
        
        # Actions Spécifiques
        self.table.add_action_button("Historique", "📜", self._show_history)
        self.table.add_action_button("Contribution", "💰", self._add_contribution)
        self.table.add_action_button("Retrait", "💸", self._add_withdrawal)
        self.table.add_action_button("Profit", "📈", self._allocate_profit)
        
        layout.addWidget(self.table)
        
    def refresh(self):
        filter_status = self.table.status_filter.get_filter()
        self.table.update_actions_for_status(filter_status)
        
        data = self.service.get_partners_table_data(filter_status=filter_status)
        self.table.clear_rows()
        for d in data:
            self.table.add_row([
                None,
                str(d['id']),
                d['name'],
                d['phone'] or "",
                d['email'] or "",
                d['function'] or "",
                format_amount(d['total_contributions'], "DA"),
                f"{d['percentage']:.2f} %",
                format_amount(d['net_profit'], "DA"),
                format_amount(d['total_withdrawals'], "DA"),
                format_amount(d['remaining'], "DA"),
                d['status']
            ], is_active=d['is_active'])
        self.table.resize_columns_to_contents()

    def _add_partner(self):
        dialog = SmartFormDialog("Ajouter Partenaire", PARTNER_SCHEMA, parent=self)
        if dialog.exec():
            success, msg = self.service.create_partner(**dialog.get_results())
            if success:
                show_success(self, "Succès", msg)
                self.refresh()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", msg)

    def _edit_partner(self, row_idx):
        from components.dialogs import confirm_action
        partner_id = int(self.table.get_row_data(row_idx)[1])
        partners = self.service.get_all_partners(filter_status="all")
        partner = next((p for p in partners if p['id'] == partner_id), None)
        
        if partner:
            dialog = SmartFormDialog("Modifier Partenaire", PARTNER_SCHEMA, partner, parent=self)
            if dialog.exec():
                success, msg = self.service.update_partner(partner_id, **dialog.get_results())
                if success:
                    show_success(self, "Succès", msg)
                    self.refresh()
                    self.dataChanged.emit()
                else:
                    show_error(self, "Erreur", msg)

    def _delete_partner(self, row_idx):
        from components.dialogs import confirm_action
        partner_id = int(self.table.get_row_data(row_idx)[1])
        name = self.table.get_row_data(row_idx)[2]
        if confirm_action(self, "Archiver Associé", f"Voulez-vous vraiment archiver l'associé '{name}' ?"):
            success, msg = self.service.delete_partner(partner_id)
            if success:
                show_success(self, "Succès", msg)
                self.refresh()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", msg)

    def _restore_partner(self, row_idx):
        from components.dialogs import confirm_action
        partner_id = int(self.table.get_row_data(row_idx)[1])
        name = self.table.get_row_data(row_idx)[2]
        if confirm_action(self, "Restaurer Associé", f"Voulez-vous réactiver l'associé '{name}' ?"):
            success, msg = self.service.restore_partner(partner_id)
            if success:
                show_success(self, "Succès", msg)
                self.refresh()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", msg)

    def _get_selected_partner_id(self):
        rows = self.table.get_selected_rows()
        if not rows:
            show_error(self, "Erreur", "Veuillez sélectionner un partenaire")
            return None
        return int(self.table.get_row_data(rows[0])[1])

    def _add_contribution(self):
        pid = self._get_selected_partner_id()
        if pid: self._open_transaction_dialog(pid, TRANS_CONTRIBUTION, "Ajouter Contribution")

    def _add_withdrawal(self):
        pid = self._get_selected_partner_id()
        if pid: self._open_transaction_dialog(pid, TRANS_WITHDRAWAL, "Enregistrer Retrait")

    def _allocate_profit(self):
        pid = self._get_selected_partner_id()
        if pid: self._open_transaction_dialog(pid, TRANS_PROFIT, "Allouer Bénéfice")

    def _show_history(self):
        pid = self._get_selected_partner_id()
        if not pid: return
        
        rows = self.table.get_selected_rows()
        name = self.table.get_row_data(rows[0])[2]
        
        dialog = PartnerHistoryDialog(pid, name, self.service, parent=self)
        dialog.exec()
        self.refresh()
        self.dataChanged.emit()

    def _open_transaction_dialog(self, partner_id, trans_type, title):
        # TransactionDialog reste spécifique car il gère la condition de compte DA
        dialog = TransactionDialog(self.treasury_service, trans_type, parent=self)
        dialog.setWindowTitle(title)
        if dialog.exec():
            data = dialog.get_data()
            success = False
            msg = ""
            
            if trans_type == TRANS_CONTRIBUTION:
                success, msg = self.service.add_contribution(partner_id, **data)
            elif trans_type == TRANS_WITHDRAWAL:
                success, msg = self.service.record_withdrawal(partner_id, **data)
            elif trans_type == TRANS_PROFIT:
                if "account_id" in data: del data["account_id"]
                success, msg = self.service.allocate_profit(partner_id, **data)
                
            if success:
                show_success(self, "Succès", msg)
                self.refresh()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", msg)

# ============================================================================
# DIALOGS
# ============================================================================

# [CUSTOM] TransactionDialog: Dialog personnalisé pour les transactions de partenaires
# [WHY]: Nécessite un compte Trésorerie DA uniquement, ne fonctionne pas avec les
#        devises étrangères car le système des partenaires est lié à la devise
#        nationale uniquement. Impossible d'utiliser SmartFormDialog standard car
#        la logique nécessite de filtrer les comptes par devise (DA uniquement)
#        et d'afficher les soldes en temps réel.
# [DATE]: 2026-03-29
class TransactionDialog(QDialog):
    """Dialog spécifique pour les transactions de capital (avec sélection de compte DA)"""
    def __init__(self, treasury_service, trans_type, parent=None):
        super().__init__(parent)
        self.treasury_service = treasury_service
        self.trans_type = trans_type
        self.setMinimumWidth(400)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(QDate.currentDate())
        self.date.setFixedWidth(140)
        form.addRow("Date de l'opération:", self.date)
        
        self.amount = AmountInput()
        self.amount.valueChanged.connect(self._update_simulation)
        form.addRow("Montant (DA):", self.amount)
        
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
        
        if self.trans_type != TRANS_PROFIT and self.treasury_service:
            self.account_combo = QComboBox()
            accounts = self.treasury_service.get_all_accounts()
            if accounts:
                for acc in accounts:
                    if acc['currency_code'] == 'DA':
                        self.account_combo.addItem(f"{acc['name']} (Solde: {format_amount(acc['balance'], 'DA')})", acc['id'])
                
                # Account balance label
                self.account_balance_label = QLabel()
                self.account_balance_label.setStyleSheet("color: #7d8590; font-size: 12px;")
                
                self.account_combo.currentIndexChanged.connect(self._update_account_balance)
                form.addRow("Compte Trésorerie:", self.account_combo)
                form.addRow("", self.account_balance_label)
        
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        form.addRow("Notes:", self.notes)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_data(self):
        data = {
            "amount": self.amount.get_amount(),
            "date": self.date.date().toPyDate(),
            "notes": self.notes.toPlainText().strip()
        }
        if self.trans_type != TRANS_PROFIT and hasattr(self, 'account_combo'):
            data["account_id"] = self.account_combo.currentData()
        return data

    def _update_account_balance(self):
        """Update account balance display when account is selected"""
        if not hasattr(self, 'account_combo') or not hasattr(self, 'account_balance_label'):
            return
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
        """Show how account balance will change"""
        if not hasattr(self, 'account_combo'):
            self.sim_label.setText("")
            return
        
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
        
        amount = self.amount.get_amount()
        new_balance = current_balance - amount
        
        if new_balance < 0:
            color = "#e74c3c"
            status = f"⚠️ Insuffisant: {abs(new_balance):,.2f} DA"
        elif new_balance == 0:
            color = "#2ecc71"
            status = "✅ Compte vide"
        else:
            color = "#7d8590"
            status = f" Nouveau: {new_balance:,.2f} DA"
        
        self.sim_label.setText(f"💡 Après opération: <span style='color: {color}'>{status}</span>")


class PartnerHistoryDialog(QDialog):
    """Historique des transactions d'un partenaire (Standardized Table)"""
    def __init__(self, partner_id, partner_name, service, parent=None):
        super().__init__(parent)
        self.partner_id = partner_id
        self.service = service
        self.setWindowTitle(f"Historique - {partner_name}")
        self.resize(900, 550)
        self._setup_ui()
        self.refresh()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.table = EnhancedTableView(self, f"partner_history_{self.partner_id}")
        self.table.set_headers(["N°", "Date", "Type", "Montant", "Réf", "Trésorerie", "Notes"])
        
        self.table.editClicked.connect(self._edit_transaction)
        self.table.deleteClicked.connect(self._delete_transaction)
        self.table.restoreClicked.connect(self._restore_transaction)
        self.table.refreshClicked.connect(self.refresh)
        self.table.status_filter.statusChanged.connect(self.refresh)
        
        layout.addWidget(self.table)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        
    def refresh(self):
        filter_status = self.table.status_filter.get_filter()
        self.table.update_actions_for_status(filter_status)
        
        # Note: get_transactions should be updated to support filter_status if needed
        # but for now it might return all or active. Let's assume we filter manually
        # OR better: update the service.
        transactions = self.service.get_transactions(self.partner_id)
        
        # Manual filtering if service doesn't support it yet
        if filter_status == "active":
            transactions = [t for t in transactions if t.get('is_active', True)]
        elif filter_status == "inactive":
            transactions = [t for t in transactions if not t.get('is_active', True)]

        self.table.clear_rows()
        for t in transactions:
            type_map = {
                TRANS_CONTRIBUTION: "Apport (Capital)",
                TRANS_WITHDRAWAL: "Retrait",
                TRANS_PROFIT: "Bénéfice Alloué"
            }
            treasury_info = t["treasury_account"] if t["treasury_reference"] else "Non (Ajustement)"
            
            self.table.add_row([
                None,
                str(t["id"]),
                t["date"].strftime("%d/%m/%Y"),
                type_map.get(t["type"], t["type"]),
                format_amount(t["amount"], "DA"),
                t["treasury_reference"] or "-",
                treasury_info,
                t["notes"] or ""
            ], is_active=t.get('is_active', True))
        self.table.resize_columns_to_contents()

    def _edit_transaction(self, row_idx):
        trans_id = int(self.table.get_row_data(row_idx)[1])
        transactions = self.service.get_transactions(self.partner_id)
        trans = next((t for t in transactions if t["id"] == trans_id), None)
        if not trans: return

        dialog = TransactionDialog(None, trans["type"], parent=self)
        dialog.setWindowTitle("Modifier Transaction")
        dialog.amount.setValue(trans["amount"])
        dialog.date.setDate(trans["date"])
        dialog.notes.setText(trans["notes"] or "")
        
        if hasattr(dialog, 'account_combo'): dialog.account_combo.setEnabled(False)
            
        if dialog.exec():
            data = dialog.get_data()
            success, msg = self.service.update_transaction(
                trans_id, date=data['date'], amount=data['amount'], notes=data['notes']
            )
            if success:
                show_success(self, "Succès", msg)
                self.refresh()
            else:
                show_error(self, "Erreur", msg)

    def _delete_transaction(self, row_idx):
        from components.dialogs import confirm_action
        trans_id = int(self.table.get_row_data(row_idx)[1])
        if confirm_action(self, "Archiver transaction", "Voulez-vous vraiment archiver cette transaction ?"):
            success, msg = self.service.delete_transaction(trans_id)
            if success:
                show_success(self, "Succès", msg)
                self.refresh()
            else:
                show_error(self, "Erreur", msg)

    def _restore_transaction(self, row_idx):
        from components.dialogs import confirm_action
        trans_id = int(self.table.get_row_data(row_idx)[1])
        if confirm_action(self, "Restaurer transaction", "Voulez-vous réactiver cette transaction ?"):
            success, msg = self.service.restore_transaction(trans_id)
            if success:
                show_success(self, "Succès", msg)
                self.refresh()
            else:
                show_error(self, "Erreur", msg)
