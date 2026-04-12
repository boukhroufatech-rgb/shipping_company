"""
Service pour le module Dettes Externes
"""
from typing import List, Tuple, Optional, Dict
from datetime import datetime
import json

from core.services import BaseService
from core.database import get_session
from .repository import ExternalContactRepository, ExternalTransactionRepository
from modules.treasury.repository import AccountRepository, TransactionRepository, TransactionAuditRepository
from modules.currency.repository import CurrencyRepository

from utils.constants import (
    EXT_OP_LEND, EXT_OP_REPAY_LEND,
    EXT_OP_BORROW, EXT_OP_REPAY_BORROW,
    TRANSACTION_TYPE_DEBIT, TRANSACTION_TYPE_CREDIT,
    SUCCESS_OPERATION_CREATED, AUDIT_ACTION_CREATE
)
from utils.validators import validate_required_field, validate_amount


class ExternalDebtService(BaseService):
    """Service pour la gestion des dettes externes"""
    
    def __init__(self):
        self.contact_repo = ExternalContactRepository()
        self.ext_trans_repo = ExternalTransactionRepository()
        self.account_repo = AccountRepository()
        self.treasury_trans_repo = TransactionRepository()
        self.currency_repo = CurrencyRepository()
        self.audit_repo = TransactionAuditRepository()
    
    # ========================================================================
    # GESTION DES CONTACTS
    # ========================================================================
    
    def create_contact(self, name: str, phone: str = "", email: str = "", 
                      address: str = "", notes: str = "") -> Tuple[bool, Optional[str], Optional[int]]:
        """Crée un nouveau contact"""
        is_valid, error = validate_required_field(name, "Nom du contact")
        if not is_valid:
            return False, error, None
            
        try:
            with get_session() as session:
                contact = self.contact_repo.create(
                    session,
                    name=name,
                    phone=phone,
                    email=email,
                    address=address,
                    notes=notes,
                    is_active=True
                )
                return True, "Contact créé avec succès", contact.id
        except Exception as e:
            return False, f"Erreur: {str(e)}", None

    def get_all_contacts(self, filter_status: str = "active") -> List[dict]:
        """Récupère tous les contacts (Purified Data)"""
        with get_session() as session:
            if filter_status == "active":
                contacts = self.contact_repo.get_active_contacts(session)
            elif filter_status == "inactive":
                contacts = self.contact_repo.get_inactive(session, limit=1000)
            else:
                contacts = self.contact_repo.get_all(session, limit=1000, include_inactive=True)

            result = []
            for contact in contacts:
                balances_dict = self.ext_trans_repo.get_all_balances(session, contact.id)
                formatted_balances = []
                for curr_id, balance in balances_dict.items():
                    currency = self.currency_repo.get_by_id(session, curr_id)
                    symbol = currency.symbol if currency else "?"
                    if balance > 0: formatted_balances.append(f"+{balance:,.2f} {symbol} (Créance)")
                    elif balance < 0: formatted_balances.append(f"{balance:,.2f} {symbol} (Dette)")

                # [NEW] 2026-04-05 - Calcul des totaux par type d'opération
                totals = self._get_contact_totals(session, contact.id)

                result.append({
                    'id': contact.id,
                    'name': contact.name,
                    'phone': contact.phone or "",
                    'email': contact.email or "",
                    'is_active': contact.is_active,
                    'notes': contact.notes or "",
                    'balances_text': ", ".join(formatted_balances) if formatted_balances else "Solde nul",
                    'total_pret': totals['pret'],
                    'total_recu': totals['recu'],
                    'total_emprunt': totals['emprunt'],
                    'total_rembourse': totals['rembourse'],
                    'solde_net': totals['solde_net']
                })
            return result

    def _get_contact_totals(self, session, contact_id: int) -> dict:
        """Calcule les totaux par type d'opération pour un contact (en DA)"""
        transactions = self.ext_trans_repo.get_by_contact(session, contact_id, limit=10000)

        totals = {'pret': 0, 'recu': 0, 'emprunt': 0, 'rembourse': 0}
        for t in transactions:
            if not t.is_active: continue
            # [NEW] 2026-04-05 - Utiliser amount_da si disponible, sinon amount
            # [FIX] 2026-04-05 - Handle None values for old records
            amount = getattr(t, 'amount_da', None) or t.amount or 0
            if t.type == EXT_OP_LEND: totals['pret'] += amount
            elif t.type == EXT_OP_REPAY_LEND: totals['recu'] += amount
            elif t.type == EXT_OP_BORROW: totals['emprunt'] += amount
            elif t.type == EXT_OP_REPAY_BORROW: totals['rembourse'] += amount

        # Solde net = (Prêté + Remboursé) - (Reçu + Emprunté) - en DA
        totals['solde_net'] = (totals['pret'] + totals['rembourse']) - (totals['recu'] + totals['emprunt'])

        return totals
            
    def get_contact(self, contact_id: int) -> Optional[dict]:
        """Récupère un contact par ID (Purified Data)"""
        with get_session() as session:
            c = self.contact_repo.get_by_id(session, contact_id)
            if not c: return None
            return {
                'id': c.id, 'name': c.name, 'phone': c.phone or "",
                'email': c.email or "", 'address': c.address or "", 'notes': c.notes or ""
            }

    def update_contact(self, contact_id: int, name: str, phone: str = "", 
                      email: str = "", address: str = "", notes: str = "") -> Tuple[bool, str]:
        """Met à jour un contact"""
        is_valid, error = validate_required_field(name, "Nom du contact")
        if not is_valid:
            return False, error
            
        try:
            with get_session() as session:
                contact = self.contact_repo.get_by_id(session, contact_id)
                if not contact:
                    return False, "Contact introuvable"
                    
                contact.name = name
                contact.phone = phone
                contact.email = email
                contact.address = address
                contact.notes = notes
                
                return True, "Contact mis à jour avec succès"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def delete_contact(self, contact_id: int) -> Tuple[bool, str]:
        """Archive un contact (Soft Delete)"""
        try:
            with get_session() as session:
                success = self.contact_repo.soft_delete(session, contact_id)
                session.commit()
                return success, "Contact archivé" if success else "Échec"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def restore_contact(self, contact_id: int) -> Tuple[bool, str]:
        """Restaure un contact archivé"""
        try:
            with get_session() as session:
                success = self.contact_repo.restore(session, contact_id)
                session.commit()
                return success, "Contact restauré" if success else "Échec"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def get_contact_balance(self, contact_id: int, currency_id: int) -> float:
        """Retourne le solde actuel d'un contact dans une devise"""
        with get_session() as session:
            return self.ext_trans_repo.get_contact_balance(session, contact_id, currency_id)

    def get_operation_full(self, operation_id: int) -> Optional[dict]:
        """Récupère une opération par ID (Purified Data)"""
        with get_session() as session:
            op = self.ext_trans_repo.get_by_id(session, operation_id)
            if not op: return None
            return {
                'id': op.id, 'date': op.date, 'type': op.type, 
                'amount': op.amount, 'account_id': op.account_id, 'notes': op.notes or ""
            }

    def delete_operation(self, operation_id: int) -> Tuple[bool, str]:
        """Archive une opération (Soft Delete) et inverse l'impact sur la trésorerie"""
        try:
            with get_session() as session:
                ext_trans = self.ext_trans_repo.get_by_id(session, operation_id)
                if not ext_trans:
                    return False, "Opération introuvable"
                    
                # Retrouver la transaction de trésorerie associée
                ref = f"EXT-{ext_trans.id}"
                treasury_trans = self.treasury_trans_repo.get_by_reference(session, ref)
                
                if treasury_trans:
                    # Inverser l'impact sur le solde
                    account = self.account_repo.get_by_id(session, treasury_trans.account_id)
                    is_debit = treasury_trans.type == TRANSACTION_TYPE_DEBIT
                    self.account_repo.update_balance(session, account.id, treasury_trans.amount, not is_debit)
                    
                    # Marquer comme inactif
                    treasury_trans.is_active = False
                
                # Marquer l'opération externe comme inactive
                ext_trans.is_active = False
                session.commit()
                return True, "Opération archivée avec succès"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def restore_operation(self, operation_id: int) -> Tuple[bool, str]:
        """Restaure une opération archivée et ré-applique l'impact sur la trésorerie"""
        try:
            with get_session() as session:
                ext_trans = self.ext_trans_repo.get_by_id(session, operation_id)
                if not ext_trans:
                    return False, "Opération introuvable"
                    
                # Retrouver la transaction de trésorerie associée
                ref = f"EXT-{ext_trans.id}"
                treasury_trans = self.treasury_trans_repo.get_by_reference(session, ref)
                
                if treasury_trans:
                    # Vérifier si le solde permet la restauration
                    account = self.account_repo.get_by_id(session, treasury_trans.account_id)
                    is_debit = treasury_trans.type == TRANSACTION_TYPE_DEBIT
                    if is_debit and account.balance < treasury_trans.amount:
                        from modules.settings.service import SettingsService
                        allow_negative = SettingsService().get_setting("allow_negative_treasury", "False") == "True"
                        if not allow_negative:
                            return False, "Solde insuffisant pour restaurer cette sortie"
                        
                    # Ré-appliquer l'impact
                    self.account_repo.update_balance(session, account.id, treasury_trans.amount, is_debit)
                    
                    # Réactiver
                    treasury_trans.is_active = True
                
                # Réactiver l'opération externe
                ext_trans.is_active = True
                session.commit()
                return True, "Opération restaurée avec succès"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def update_operation_full(self, operation_id: int, operation_type: str, account_id: int,
                             amount: float, notes: str = "", date: datetime = None,
                             exchange_rate: float = 1.0) -> Tuple[bool, str]:
        """Met à jour une opération complète (Type, Compte, Montant...)"""
        try:
            with get_session() as session:
                ext_trans = self.ext_trans_repo.get_by_id(session, operation_id)
                if not ext_trans:
                    return False, "Opération introuvable"

                # 1. RÉVERSİON de l'ancien impact
                old_ref = f"EXT-{ext_trans.id}"
                old_treasury_trans = self.treasury_trans_repo.get_by_reference(session, old_ref)

                if old_treasury_trans:
                    # Inverser l'ancien solde
                    old_acc = self.account_repo.get_by_id(session, old_treasury_trans.account_id)
                    is_old_debit = old_treasury_trans.type == TRANSACTION_TYPE_DEBIT
                    self.account_repo.update_balance(session, old_acc.id, old_treasury_trans.amount, not is_old_debit)

                # 2. APPLICATION du nouvel impact
                new_acc = self.account_repo.get_by_id(session, account_id)
                if not new_acc:
                    return False, "Nouveau compte introuvable"

                is_money_out = operation_type in [EXT_OP_LEND, EXT_OP_REPAY_BORROW]
                if is_money_out and new_acc.balance < amount:
                    from modules.settings.service import SettingsService
                    allow_negative = SettingsService().get_setting("allow_negative_treasury", "False") == "True"
                    if not allow_negative:
                        return False, "Solde insuffisant dans le nouveau compte"

                # [NEW] 2026-04-05 - Calculer le montant en DA
                currency = self.currency_repo.get_by_id(session, new_acc.currency_id)
                currency_code = currency.code if currency else "DA"
                if currency_code in ["DA", "DZD"]:
                    exchange_rate = 1.0
                amount_da = amount * exchange_rate

                # Appliquer nouveau solde
                self.account_repo.update_balance(session, new_acc.id, amount, is_money_out)

                # 3. MISE À JOUR des enregistrements
                ext_trans.type = operation_type
                ext_trans.account_id = account_id
                ext_trans.currency_id = new_acc.currency_id
                ext_trans.amount = amount
                ext_trans.exchange_rate = exchange_rate
                ext_trans.amount_da = amount_da
                ext_trans.notes = notes
                if date:
                    ext_trans.date = date

                if old_treasury_trans:
                    old_treasury_trans.account_id = account_id
                    old_treasury_trans.amount = amount
                    old_treasury_trans.type = TRANSACTION_TYPE_DEBIT if is_money_out else TRANSACTION_TYPE_CREDIT
                    old_treasury_trans.date = date or datetime.now()
                    # Mettre à jour description
                    contact = self.contact_repo.get_by_id(session, ext_trans.contact_id)
                    desc_map = {
                        EXT_OP_LEND: f"Prêt accordé à {contact.name}",
                        EXT_OP_REPAY_LEND: f"Remboursement prêt par {contact.name}",
                        EXT_OP_BORROW: f"Emprunt reçu de {contact.name}",
                        EXT_OP_REPAY_BORROW: f"Remboursement emprunt à {contact.name}"
                    }
                    desc = desc_map.get(operation_type, "Opération dette externe")
                    if notes: desc += f" ({notes})"
                    old_treasury_trans.description = desc

                session.commit()
                return True, "Opération mise à jour avec succès"
        except Exception as e:
            session.rollback()
            return False, f"Erreur: {str(e)}"

    # ========================================================================
    # GESTION DES OPÉRATIONS
    # ========================================================================
    
    def create_operation(self, contact_id: int, operation_type: str, account_id: int,
                        amount: float, notes: str = "", date: datetime = None,
                        user: str = "system", exchange_rate: float = 1.0) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Crée une opération de dette externe (Prêt/Emprunt/Remboursement).
        Gère automatiquement les mouvements de trésorerie.
        
        [NEW] 2026-04-05: exchange_rate pour la conversion en DA
        """
        # Validation
        is_valid, error = validate_amount(amount)
        if not is_valid:
            return False, error, None

        try:
            with get_session() as session:
                # 1. Vérifications
                contact = self.contact_repo.get_by_id(session, contact_id)
                if not contact:
                    return False, "Contact introuvable", None

                account = self.account_repo.get_by_id(session, account_id)
                if not account:
                    return False, "Compte introuvable", None

                # 2. Déterminer le mouvement de trésorerie
                is_money_out = operation_type in [EXT_OP_LEND, EXT_OP_REPAY_BORROW]
                treasury_type = TRANSACTION_TYPE_DEBIT if is_money_out else TRANSACTION_TYPE_CREDIT

                # 3. Vérifier solde caisse si sortie d'argent
                if is_money_out and account.balance < amount:
                    from modules.settings.service import SettingsService
                    allow_negative = SettingsService().get_setting("allow_negative_treasury", "False") == "True"
                    if not allow_negative:
                        return False, "Solde insuffisant dans le compte sélectionné", None

                # 4. Calculer le montant en DA
                currency = self.currency_repo.get_by_id(session, account.currency_id)
                currency_code = currency.code if currency else "DA"
                if currency_code in ["DA", "DZD"]:
                    exchange_rate = 1.0
                amount_da = amount * exchange_rate

                # 5. Description automatique pour la transaction
                desc_map = {
                    EXT_OP_LEND: f"Prêt accordé à {contact.name}",
                    EXT_OP_REPAY_LEND: f"Remboursement prêt par {contact.name}",
                    EXT_OP_BORROW: f"Emprunt reçu de {contact.name}",
                    EXT_OP_REPAY_BORROW: f"Remboursement emprunt à {contact.name}"
                }
                description = desc_map.get(operation_type, "Opération dette externe")
                if notes:
                    description += f" ({notes})"

                # 6. Créer l'opération externe
                ext_trans = self.ext_trans_repo.create(
                    session,
                    contact_id=contact_id,
                    account_id=account_id,
                    currency_id=account.currency_id,
                    type=operation_type,
                    amount=amount,
                    exchange_rate=exchange_rate,
                    amount_da=amount_da,
                    date=date or datetime.now(),
                    notes=notes
                )

                # 7. Créer le mouvement de trésorerie
                transaction = self.treasury_trans_repo.create(
                    session,
                    account_id=account_id,
                    type=treasury_type,
                    amount=amount,
                    description=description,
                    reference=f"EXT-{ext_trans.id}",
                    date=date or datetime.now(),
                    created_by=user
                )

                # 8. Mettre à jour le solde du compte
                self.account_repo.update_balance(session, account_id, amount, is_money_out)

                return True, SUCCESS_OPERATION_CREATED, ext_trans.id

        except Exception as e:
            return False, f"Erreur: {str(e)}", None

    def get_contact_history(self, contact_id: int, filter_status: str = "active") -> List[dict]:
        """Récupère l'historique d'un contact avec filtrage par statut"""
        with get_session() as session:
            transactions = self.ext_trans_repo.get_by_contact(session, contact_id)

            if filter_status == "active":
                transactions = [t for t in transactions if t.is_active]
            elif filter_status == "inactive":
                transactions = [t for t in transactions if not t.is_active]

            type_map = {
                EXT_OP_LEND: "Prêt accordé", EXT_OP_REPAY_LEND: "Remboursement reçu",
                EXT_OP_BORROW: "Emprunt reçu", EXT_OP_REPAY_BORROW: "Remboursement effectué"
            }
            return [
                {
                    'id': t.id, 'date': t.date, 'type': t.type,
                    'type_display': type_map.get(t.type, t.type),
                    'amount': t.amount or 0,
                    'currency_symbol': t.currency.symbol if t.currency else "DA",
                    'currency_code': t.currency.code if t.currency else "DA",
                    'exchange_rate': getattr(t, 'exchange_rate', None) or 1.0,
                    'amount_da': getattr(t, 'amount_da', None) or t.amount or 0,
                    'account_name': t.account.name if t.account else "N/A",
                    'notes': t.notes or "",
                    'is_active': t.is_active
                } for t in transactions
            ]

    def get_all_history(self, filter_status: str = "active", limit: int = 1000) -> List[dict]:
        """Récupère l'historique global de tous les contacts (Purified Data)"""
        with get_session() as session:
            if filter_status == "active":
                transactions = self.ext_trans_repo.get_active(session, limit=limit)
            elif filter_status == "inactive":
                transactions = self.ext_trans_repo.get_inactive(session, limit=limit)
            else:
                transactions = self.ext_trans_repo.get_all(session, limit=limit, include_inactive=True)

            type_map = {
                EXT_OP_LEND: "Prêt accordé", EXT_OP_REPAY_LEND: "Remboursement reçu",
                EXT_OP_BORROW: "Emprunt reçu", EXT_OP_REPAY_BORROW: "Remboursement effectué"
            }
            return [
                {
                    'id': t.id,
                    'date': t.date,
                    'type': t.type,
                    'type_display': type_map.get(t.type, t.type),
                    'contact_id': t.contact_id,
                    'contact_name': t.contact.name if t.contact else "N/A",
                    'amount': t.amount or 0,
                    'currency_symbol': t.currency.symbol if t.currency else "DA",
                    'currency_code': t.currency.code if t.currency else "DA",
                    'exchange_rate': getattr(t, 'exchange_rate', None) or 1.0,
                    'amount_da': getattr(t, 'amount_da', None) or t.amount or 0,
                    'account_name': t.account.name if t.account else "N/A",
                    'notes': t.notes or "",
                    'is_active': t.is_active
                } for t in transactions
            ]
