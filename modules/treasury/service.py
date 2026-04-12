"""
Service pour le module Trésorerie
"""
import json
from typing import Optional, Tuple, List
from datetime import datetime
from sqlalchemy.orm import joinedload

from core.services import BaseService
from core.database import get_session
from core.models import Account, Transaction, Currency
from .repository import AccountRepository, TransactionRepository, TransactionAuditRepository
from utils.constants import (
    TRANSACTION_TYPE_DEBIT, TRANSACTION_TYPE_CREDIT,
    AUDIT_ACTION_CREATE, AUDIT_ACTION_UPDATE, AUDIT_ACTION_DELETE,
    ERROR_INSUFFICIENT_BALANCE, ERROR_CANNOT_DELETE_MAIN_ACCOUNT,
    ERROR_ACCOUNT_NOT_FOUND, ERROR_INVALID_AMOUNT,
    SUCCESS_OPERATION_CREATED, SUCCESS_ACCOUNT_CREATED,
    DEFAULT_CURRENCY_CODE
)
from utils.validators import validate_amount, validate_required_field
from utils.logger import log_info, log_error, log_success, log_warning
from utils.error_handler import handle_errors, transactional


class TreasuryService(BaseService):
    """Service pour la gestion de la trésorerie"""
    
    def __init__(self):
        self.account_repo = AccountRepository()
        self.transaction_repo = TransactionRepository()
        self.audit_repo = TransactionAuditRepository()
        self._seed_default_account_types() # S'assure que les 3 types de base existent
    
    # ========================================================================
    # GESTION DU CATALOGUE: TYPES DE COMPTES
    # ========================================================================
    
    def _seed_default_account_types(self):
        """Assure que les types de base existent toujours (CAISSE, COMPTE, CCP)"""
        from core.models import TreasuryAccountType
        default_types = ["CAISSE", "COMPTE", "CCP"]
        try:
            with get_session() as session:
                for t_name in default_types:
                    existing = session.query(TreasuryAccountType).filter_by(name=t_name).first()
                    if not existing:
                        new_type = TreasuryAccountType(name=t_name, is_fixed=True, is_active=True, description="Type de compte système protégé")
                        session.add(new_type)
                session.commit()
        except:
            pass # Si la table n'est pas encore créée, on ignore pour le moment

    def get_all_account_types(self, include_inactive: bool = False) -> List[dict]:
        from core.models import TreasuryAccountType
        with get_session() as session:
            query = session.query(TreasuryAccountType)
            if not include_inactive:
                query = query.filter_by(is_active=True)
            types = query.all()
            return [{'id': t.id, 'name': t.name, 'is_fixed': t.is_fixed, 'is_active': t.is_active} for t in types]

    def create_account_type(self, name: str, description: str = "") -> Tuple[bool, str, Optional[int]]:
        from core.models import TreasuryAccountType
        is_valid, error = validate_required_field(name, "Nom du type")
        if not is_valid: return False, error, None
        
        try:
            with get_session() as session:
                existing = session.query(TreasuryAccountType).filter(TreasuryAccountType.name.ilike(name)).first()
                if existing:
                    if not existing.is_active:
                        existing.is_active = True
                        session.commit()
                        return True, "Type réactivé", existing.id
                    return False, "Ce type existe déjà", None
                
                new_type = TreasuryAccountType(name=name.upper(), description=description, is_fixed=False, is_active=True)
                session.add(new_type)
                session.flush()
                return True, "Type créé avec succès", new_type.id
        except Exception as e:
            return False, f"Erreur: {str(e)}", None

    def delete_account_type(self, type_id: int) -> Tuple[bool, str]:
        from core.models import TreasuryAccountType
        with get_session() as session:
            acc_type = session.query(TreasuryAccountType).get(type_id)
            if not acc_type: return False, "Introuvable"
            if acc_type.is_fixed: return False, "Impossible de supprimer un type système protégé"
            acc_type.is_active = False # Soft delete
            session.commit()
            return True, "Type supprimé"

    def restore_account_type(self, type_id: int) -> Tuple[bool, str]:
        from core.models import TreasuryAccountType
        with get_session() as session:
            acc_type = session.query(TreasuryAccountType).get(type_id)
            if not acc_type: return False, "Introuvable"
            acc_type.is_active = True
            session.commit()
            return True, "Type restauré"
            
    # ========================================================================
    # GESTION DES COMPTES
    # ========================================================================
    
    def create_account(self, name: str, code: str, account_type: str, currency_id: int,
                      is_main: bool = False, description: str = "", 
                      initial_balance: float = 0.0) -> Tuple[bool, Optional[str], Optional[int]]:
        """Crée un nouveau compte avec solde initial."""
        log_info(f"Création du compte: {name} ({code}) - Solde initial: {initial_balance}", context="TreasuryService.create_account")
        
        is_valid, error = validate_required_field(name, "Nom du compte")
        if not is_valid:
            log_warning(f"Validation échouée (nom): {error}", context="TreasuryService.create_account")
            return False, error, None
        is_valid, error = validate_required_field(code, "Code du compte")
        if not is_valid:
            log_warning(f"Validation échouée (code): {error}", context="TreasuryService.create_account")
            return False, error, None

        try:
            with get_session() as session:
                existing = self.account_repo.get_by_code(session, code)
                if existing:
                    log_warning(f"Le code {code} existe déjà", context="TreasuryService.create_account")
                    return False, "Ce code de compte existe déjà", None
                    
                account = self.account_repo.create(
                    session, name=name, code=code, account_type=account_type,
                    currency_id=currency_id, is_main=is_main, description=description, 
                    balance=initial_balance, initial_balance=initial_balance
                )
                log_success(f"Compte créé avec succès - ID: {account.id} - Solde: {initial_balance}", context="TreasuryService.create_account")
                return True, SUCCESS_ACCOUNT_CREATED, account.id
        except Exception as e:
            log_error(e, context="TreasuryService.create_account", extra_data={
                "name": name, "code": code, "account_type": account_type, "currency_id": currency_id
            })
            return False, f"Erreur lors de la création du compte: {str(e)}", None
    
    def update_account(self, account_id: int, name: str, account_type: str, 
                       currency_id: int, description: str = "", 
                       initial_balance: float = None) -> Tuple[bool, str]:
        """Met à jour les informations d'un compte."""
        is_valid, error = validate_required_field(name, "Nom du compte")
        if not is_valid: return False, error
        try:
            with get_session() as session:
                account = self.account_repo.get_by_id(session, account_id)
                if not account: return False, "Compte introuvable"
                account.name = name
                account.account_type = account_type
                account.currency_id = currency_id
                account.description = description
                if initial_balance is not None and hasattr(account, 'initial_balance'):
                    account.initial_balance = initial_balance
                return True, "Compte mis à jour avec succès"
        except Exception as e:
            return False, f"Erreur lors de la mise à jour: {str(e)}"
    
    def get_all_accounts(self, filter_status: str = "active", currency_filter: str = None, account_type_filter: str = None) -> List[dict]:
        """Récupère tous les comptes (Purified Data)"""
        with get_session() as session:
            query = session.query(Account).join(Account.currency).options(joinedload(Account.currency))
            
            if filter_status == "active":
                query = query.filter(Account.is_active == True, Currency.is_active == True)
            elif filter_status == "inactive":
                query = query.filter((Account.is_active == False) | (Currency.is_active == False))
            
            accounts = query.all()

            if currency_filter and currency_filter.upper() == "DA":
                accounts = [a for a in accounts if a.currency and a.currency.code.upper() == "DA"]
            elif currency_filter and currency_filter.upper() == "FOREIGN":
                accounts = [a for a in accounts if a.currency and a.currency.code.upper() != "DA"]

            if account_type_filter:
                types = [t.strip().upper() for t in account_type_filter.split(",")]
                accounts = [a for a in accounts if a.account_type and a.account_type.upper() in types]
            
            return [
                {
                    'id': a.id, 'code': a.code, 'name': a.name,
                    'account_type': a.account_type, 'balance': a.balance,
                    'initial_balance': a.initial_balance if hasattr(a, 'initial_balance') else 0.0,
                    'is_main': a.is_main, 'is_active': a.is_active,
                    'description': a.description or "", 'currency_id': a.currency_id,
                    'currency_code': a.currency.code if a.currency else "??",
                    'currency_symbol': a.currency.symbol if a.currency else "?"
                } for a in accounts
            ]
    
    def get_account(self, account_id: int) -> Optional[dict]:
        """Récupère un compte par ID (Purified Data)"""
        with get_session() as session:
            a = session.query(Account).options(joinedload(Account.currency)).filter(Account.id == account_id).first()
            if not a: return None
            return {
                'id': a.id, 'code': a.code, 'name': a.name, 'account_type': a.account_type,
                'balance': a.balance, 
                'initial_balance': getattr(a, 'initial_balance', 0.0),
                'is_main': a.is_main, 'is_active': a.is_active,
                'description': a.description or "", 'currency_id': a.currency_id,
                'currency_code': a.currency.code, 'currency_symbol': a.currency.symbol
            }
    
    def delete_account(self, account_id: int) -> Tuple[bool, Optional[str]]:
        """Supprime un compte."""
        try:
            with get_session() as session:
                account = self.account_repo.get_by_id(session, account_id)
                if not account: return False, ERROR_ACCOUNT_NOT_FOUND
                if account.is_main: return False, ERROR_CANNOT_DELETE_MAIN_ACCOUNT
                from core.models import Transaction
                transaction_count = session.query(Transaction).filter(Transaction.account_id == account_id, Transaction.is_active == True).count()
                if transaction_count > 0: return False, "Impossible de supprimer le compte : des transactions y sont rattachées."
                account.is_active = False
                session.flush()
                return True, "Compte désactivé avec succès"
        except Exception as e:
            return False, f"Erreur lors de la suppression: {str(e)}"

    def restore_account(self, account_id: int) -> Tuple[bool, Optional[str]]:
        """Réactive un compte archivé."""
        try:
            with get_session() as session:
                account = self.account_repo.get_by_id(session, account_id)
                if not account: return False, ERROR_ACCOUNT_NOT_FOUND
                account.is_active = True
                session.flush()
                return True, "Compte restauré avec succès"
        except Exception as e:
            return False, f"Erreur lors de la restauration: {str(e)}"
    
    def create_transaction(
        self, 
        account_id: int, 
        transaction_type: str, 
        amount: float, 
        description: str, 
        reference: str = "", 
        date: datetime = None, 
        user: str = "system",
        source: str = "CAISSE",
        source_id: int = None,
        payment_method: str = "ESPECES",
        category: str = "DIVERS",
        status: str = "VALIDEE",
        notes: str = ""
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Crée une nouvelle transaction avec tous les champs avancés.
        
        Args:
            source: Source de l'opération (CAISSE, CLIENT, FOURNISSEUR, DEVISE, PARTNER, EXPENSE)
            source_id: ID de l'opération dans le module source
            payment_method: Moyen de paiement (ESPECES, CHEQUE, VIREMENT, TRAITE, EFFET, AUTRE)
            category: Catégorie de l'opération (DEPOT, RETRAIT, TRANSFERT, PAIEMENT_CLIENT, etc.)
            status: Statut de l'opération (VALIDEE, EN_ATTENTE, ANNULEE, EN_COURS)
            notes: Notes additionnelles
        """
        log_info(f"Création transaction - Account: {account_id}, Type: {transaction_type}, Amount: {amount}, Source: {source}", 
                 context="TreasuryService.create_transaction")

        is_valid, error = validate_amount(amount)
        if not is_valid:
            log_warning(f"Validation échouée (montant): {error}", context="TreasuryService.create_transaction")
            return False, error, None
        is_valid, error = validate_required_field(description, "Description")
        if not is_valid:
            log_warning(f"Validation échouée (description): {error}", context="TreasuryService.create_transaction")
            return False, error, None
        if transaction_type not in [TRANSACTION_TYPE_DEBIT, TRANSACTION_TYPE_CREDIT]:
            log_warning(f"Type de transaction invalide: {transaction_type}", context="TreasuryService.create_transaction")
            return False, "Type de transaction invalide", None

        try:
            with get_session() as session:
                account = self.account_repo.get_by_id(session, account_id)
                if not account:
                    log_error(Exception("Account not found"), context="TreasuryService.create_transaction", extra_data={"account_id": account_id})
                    return False, ERROR_ACCOUNT_NOT_FOUND, None

                if transaction_type == TRANSACTION_TYPE_DEBIT and account.balance < amount:
                    from modules.settings.service import SettingsService
                    allow_negative = SettingsService().get_setting("allow_negative_treasury", "False") == "True"
                    if not allow_negative:
                        log_warning(f"Solde insuffisant - Balance: {account.balance}, Required: {amount}", context="TreasuryService.create_transaction")
                        return False, ERROR_INSUFFICIENT_BALANCE, None
                    log_warning(f"Solde negatif autorise - Balance: {account.balance}, Required: {amount}", context="TreasuryService.create_transaction")

                # Créer la transaction avec tous les nouveaux champs
                from core.models import Transaction
                transaction = Transaction(
                    account_id=account_id,
                    type=transaction_type,
                    amount=amount,
                    description=description,
                    reference=reference,
                    date=date or datetime.now(),
                    created_by=user,
                    source=source,
                    source_id=source_id,
                    payment_method=payment_method,
                    category=category,
                    status=status,
                    notes=notes or "",
                    is_active=True
                )
                session.add(transaction)
                session.flush()

                is_debit = transaction_type == TRANSACTION_TYPE_DEBIT
                self.account_repo.update_balance(session, account_id, amount, is_debit)

                transaction_data = {
                    "type": transaction_type, 
                    "amount": amount, 
                    "description": description, 
                    "reference": reference,
                    "source": source,
                    "payment_method": payment_method,
                    "category": category
                }
                self.audit_repo.create_audit_entry(session, transaction.id, AUDIT_ACTION_CREATE, user, new_data=json.dumps(transaction_data))

                log_success(f"Transaction créée avec succès - ID: {transaction.id}", context="TreasuryService.create_transaction")
                return True, SUCCESS_OPERATION_CREATED, transaction.id

        except Exception as e:
            log_error(e, context="TreasuryService.create_transaction", extra_data={
                "account_id": account_id, "type": transaction_type, "amount": amount
            })
            return False, f"Erreur lors de la création de la transaction: {str(e)}", None

    def get_transaction(self, transaction_id: int) -> Optional[dict]:
        """Récupère une transaction par ID (Purified Data)"""
        with get_session() as session:
            t = self.transaction_repo.get_by_id(session, transaction_id)
            if not t: return None
            return {
                'id': t.id, 
                'date': t.date, 
                'type': t.type, 
                'amount': t.amount,
                'description': t.description, 
                'reference': t.reference or "",
                'account_id': t.account_id,
                'account_name': t.account.name if t.account else None,
                'source': t.source,
                'source_id': t.source_id,
                'payment_method': t.payment_method,
                'category': t.category,
                'status': t.status,
                'notes': t.notes or "",
                'created_by': t.created_by,
                'is_active': t.is_active
            }

    def get_account_transactions(self, account_id: int, limit: int = 100) -> List[dict]:
        """Récupère les transactions d'un compte (Purified Data)"""
        with get_session() as session:
            transactions = self.transaction_repo.get_by_account(session, account_id, limit)
            return [
                {
                    'id': t.id, 
                    'date': t.date, 
                    'type': t.type, 
                    'amount': t.amount,
                    'description': t.description, 
                    'reference': t.reference or "",
                    'account_name': t.account.name, 
                    'account_currency_symbol': t.account.currency.symbol,
                    'source': t.source,
                    'source_id': t.source_id,
                    'payment_method': t.payment_method,
                    'category': t.category,
                    'status': t.status,
                    'notes': t.notes or "",
                    'created_by': t.created_by,
                    'is_active': t.is_active
                } for t in transactions
            ]

    def get_all_transactions(
        self, 
        limit: int = 100, 
        filter_status: str = "active", 
        currency_filter: str = None,
        source_filter: str = None,
        status_filter: str = None
    ) -> List[dict]:
        """
        Récupère toutes les transactions selon le statut et la devise.
        
        Args:
            source_filter: Filtre par source (CAISSE, CLIENT, FOURNISSEUR, etc.)
            status_filter: Filtre par statut (VALIDEE, EN_ATTENTE, etc.)
        """
        from sqlalchemy.orm import joinedload
        with get_session() as session:
            query = session.query(Transaction).options(
                joinedload(Transaction.account).joinedload(Account.currency)
            )
            if filter_status == "active": 
                query = query.filter(Transaction.is_active == True)
            elif filter_status == "inactive": 
                query = query.filter(Transaction.is_active == False)
            
            # Filtres additionnels
            if source_filter:
                query = query.filter(Transaction.source == source_filter)
            if status_filter:
                query = query.filter(Transaction.status == status_filter)
            
            query = query.order_by(Transaction.date.asc()).limit(limit)
            transactions = query.all()

            if currency_filter and currency_filter.upper() == "DA":
                transactions = [t for t in transactions if t.account.currency and t.account.currency.code.upper() == "DA"]
            elif currency_filter and currency_filter.upper() == "FOREIGN":
                transactions = [t for t in transactions if t.account.currency and t.account.currency.code.upper() != "DA"]

            return [
                {
                    'id': t.id, 
                    'date': t.date, 
                    'type': t.type, 
                    'amount': t.amount,
                    'description': t.description, 
                    'reference': t.reference or "",
                    'account_id': t.account_id,
                    'account_name': t.account.name,
                    'account_currency_symbol': t.account.currency.symbol,
                    'source': t.source,
                    'source_id': t.source_id,
                    'payment_method': t.payment_method,
                    'category': t.category,
                    'status': t.status,
                    'notes': t.notes or "",
                    'created_by': t.created_by,
                    'is_active': t.is_active
                } for t in transactions
            ]

    def update_transaction(self, transaction_id: int, account_id: int = None, transaction_type: str = None, amount: float = None, description: str = None, reference: str = None, date: datetime = None, user: str = "system") -> Tuple[bool, Optional[str]]:
        """Met à jour une transaction complète"""
        try:
            with get_session() as session:
                transaction = self.transaction_repo.get_by_id(session, transaction_id)
                if not transaction: return False, "Transaction introuvable"
                old_data = {"account_id": transaction.account_id, "type": transaction.type, "amount": transaction.amount, "description": transaction.description, "reference": transaction.reference, "date": transaction.date.isoformat() if transaction.date else None}
                old_acc_repo = AccountRepository()
                old_acc = old_acc_repo.get_by_id(session, transaction.account_id)
                is_old_debit = transaction.type == TRANSACTION_TYPE_DEBIT
                old_acc_repo.update_balance(session, old_acc.id, transaction.amount, not is_old_debit)
                if account_id: transaction.account_id = account_id
                if transaction_type: transaction.type = transaction_type
                if amount is not None: transaction.amount = amount
                if description: transaction.description = description
                if reference is not None: transaction.reference = reference
                if date: transaction.date = date
                transaction.updated_by = user
                new_acc_repo = AccountRepository()
                new_acc = new_acc_repo.get_by_id(session, transaction.account_id)
                is_new_debit = transaction.type == TRANSACTION_TYPE_DEBIT
                new_acc_repo.update_balance(session, new_acc.id, transaction.amount, is_new_debit)
                new_data = {"account_id": transaction.account_id, "type": transaction.type, "amount": transaction.amount, "description": transaction.description, "reference": transaction.reference, "date": transaction.date.isoformat() if transaction.date else None}
                self.audit_repo.create_audit_entry(session, transaction_id, "UPDATE", user, old_data=json.dumps(old_data), new_data=json.dumps(new_data))
                session.commit()
                return True, "Transaction mise à jour avec succès"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def delete_transaction(self, transaction_id: int, user: str = "system") -> Tuple[bool, Optional[str]]:
        """Annule une transaction et réajuste le solde du compte"""
        try:
            with get_session() as session:
                transaction = self.transaction_repo.get_by_id(session, transaction_id)
                if not transaction: return False, "Transaction introuvable"
                transaction_data = {"type": transaction.type, "amount": transaction.amount, "description": transaction.description, "reference": transaction.reference}
                self.audit_repo.create_audit_entry(session, transaction_id, AUDIT_ACTION_DELETE, user, old_data=json.dumps(transaction_data))
                account = transaction.account
                is_debit = transaction.type == TRANSACTION_TYPE_DEBIT
                self.account_repo.update_balance(session, account.id, transaction.amount, not is_debit)
                transaction.is_active = False
                session.flush()
                return True, "Transaction annulée avec succès"
        except Exception as e:
            return False, f"Erreur lors de la suppression: {str(e)}"

    def restore_transaction(self, transaction_id: int, user: str = "system") -> Tuple[bool, Optional[str]]:
        """Réactive une transaction archivée (recrée le mouvement financier)"""
        try:
            with get_session() as session:
                transaction = self.transaction_repo.get_by_id(session, transaction_id)
                if not transaction: return False, "Transaction introuvable"
                account = transaction.account
                is_debit = transaction.type == TRANSACTION_TYPE_DEBIT
                # Vérifier le solde si c'est un débit qu'on restaure
                if is_debit and account.balance < transaction.amount:
                    from modules.settings.service import SettingsService
                    allow_negative = SettingsService().get_setting("allow_negative_treasury", "False") == "True"
                    if not allow_negative:
                        return False, ERROR_INSUFFICIENT_BALANCE
                self.account_repo.update_balance(session, account.id, transaction.amount, is_debit)
                transaction.is_active = True
                session.flush()
                return True, "Transaction restaurée avec succès"
        except Exception as e:
            return False, f"Erreur lors de la restauration: {str(e)}"

    def transfer_funds(
        self, 
        from_id: int, 
        to_id: int, 
        amount: float, 
        description: str, 
        date: datetime = None, 
        user: str = "system",
        payment_method: str = "VIREMENT",
        category: str = "TRANSFERT",
        status: str = "VALIDEE",
        notes: str = ""
    ) -> Tuple[bool, str]:
        """
        Transfère des fonds entre deux comptes avec tous les champs avancés.
        
        Args:
            payment_method: Moyen de paiement (ESPECES, CHEQUE, VIREMENT, etc.)
            category: Catégorie (par défaut: TRANSFERT)
            status: Statut du transfert
            notes: Notes additionnelles
        """
        if from_id == to_id: 
            return False, "Le compte source et destination doivent être différents"
        try:
            with get_session() as session:
                from_account = self.account_repo.get_by_id(session, from_id)
                if not from_account: 
                    return False, "Compte source introuvable"
                if from_account.balance < amount:
                    from modules.settings.service import SettingsService
                    allow_negative = SettingsService().get_setting("allow_negative_treasury", "False") == "True"
                    if not allow_negative:
                        return False, "Solde insuffisant dans le compte source"
                to_account = self.account_repo.get_by_id(session, to_id)
                if not to_account: 
                    return False, "Compte destination introuvable"
                    
                op_date = date or datetime.now()
                trans_ref = f"TRF-{datetime.now().strftime('%y%m%d%H%M')}"
                
                # Créer la transaction DEBIT (source)
                from core.models import Transaction
                debit_trans = Transaction(
                    account_id=from_id,
                    type=TRANSACTION_TYPE_DEBIT,
                    amount=amount,
                    description=f"Transfert vers {to_account.name}: {description}",
                    reference=trans_ref,
                    date=op_date,
                    created_by=user,
                    source="CAISSE",
                    source_id=None,
                    payment_method=payment_method,
                    category=category,
                    status=status,
                    notes=notes,
                    is_active=True
                )
                session.add(debit_trans)
                session.flush()
                self.account_repo.update_balance(session, from_id, amount, is_debit=True)
                
                # Créer la transaction CREDIT (destination)
                credit_trans = Transaction(
                    account_id=to_id,
                    type=TRANSACTION_TYPE_CREDIT,
                    amount=amount,
                    description=f"Transfert depuis {from_account.name}: {description}",
                    reference=trans_ref,
                    date=op_date,
                    created_by=user,
                    source="CAISSE",
                    source_id=None,
                    payment_method=payment_method,
                    category=category,
                    status=status,
                    notes=notes,
                    is_active=True
                )
                session.add(credit_trans)
                session.flush()
                self.account_repo.update_balance(session, to_id, amount, is_debit=False)
                
                log_success(f"Transfert effectué - De: {from_account.name} -> À: {to_account.name} - Montant: {amount}", 
                           context="TreasuryService.transfer_funds")
                return True, "Transfert effectué avec succès"
        except Exception as e:
            log_error(e, context="TreasuryService.transfer_funds", extra_data={
                "from_id": from_id, "to_id": to_id, "amount": amount
            })
            return False, f"Erreur lors du transfert: {str(e)}"
    
    def get_transaction_audit(self, transaction_id: int) -> List[dict]:
        """Récupère l'historique d'audit d'une transaction (Purified Data)"""
        with get_session() as session:
            history = self.audit_repo.get_by_transaction(session, transaction_id)
            return [
                {
                    'id': h.id, 'action': h.action, 'user': h.user,
                    'timestamp': h.timestamp, 'old_data': h.old_data, 'new_data': h.new_data
                } for h in history
            ]
