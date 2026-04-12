"""
Repository pour le module Trésorerie
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime

from core.repositories import BaseRepository
from core.models import Account, Transaction, TransactionAudit


class AccountRepository(BaseRepository[Account]):
    """Repository pour les comptes de trésorerie"""
    
    def __init__(self):
        super().__init__(Account)
    
    def get_by_code(self, session: Session, code: str) -> Optional[Account]:
        """Récupère un compte par son code"""
        return session.query(Account).filter(Account.code == code).first()
    
    def get_main_account(self, session: Session) -> Optional[Account]:
        """Récupère le compte principal"""
        return session.query(Account).filter(Account.is_main == True).first()
    
    def get_accounts_by_currency(self, session: Session, currency_id: int) -> List[Account]:
        """Récupère les comptes d'une devise spécifique (Purified Sort)"""
        return session.query(Account).filter(
            and_(Account.currency_id == currency_id, Account.is_active == True)
        ).order_by(Account.id).all()
    
    def update_balance(self, session: Session, account_id: int, amount: float, is_debit: bool) -> bool:
        """
        Met à jour le solde d'un compte.
        """
        account = self.get_by_id(session, account_id)
        if not account:
            return False
        
        if is_debit:
            account.balance -= amount
        else:
            account.balance += amount
        
        session.flush()
        return True


class TransactionRepository(BaseRepository[Transaction]):
    """Repository pour les transactions"""
    
    def __init__(self):
        super().__init__(Transaction)
    
    def get_by_account(self, session: Session, account_id: int, limit: int = 100) -> List[Transaction]:
        """Récupère les transactions d'un compte (Purified Sort: Oldest First)"""
        return session.query(Transaction).filter(
            Transaction.account_id == account_id
        ).order_by(Transaction.id).limit(limit).all()
    
    def get_by_date_range(self, session: Session, start_date: datetime, end_date: datetime) -> List[Transaction]:
        """Récupère les transactions dans une plage de dates (Purified Sort)"""
        return session.query(Transaction).filter(
            and_(Transaction.date >= start_date, Transaction.date <= end_date)
        ).order_by(Transaction.id).all()
    
    def get_by_type(self, session: Session, transaction_type: str, limit: int = 100) -> List[Transaction]:
        """Récupère les transactions d'un type spécifique (Purified Sort)"""
        return session.query(Transaction).filter(
            Transaction.type == transaction_type
        ).order_by(Transaction.id).limit(limit).all()
    
    def search(self, session: Session, query: str, limit: int = 100) -> List[Transaction]:
        """Recherche dans les transactions (Purified Sort)"""
        search_pattern = f"%{query}%"
        return session.query(Transaction).filter(
            or_(
                Transaction.description.like(search_pattern),
                Transaction.reference.like(search_pattern)
            )
        ).order_by(Transaction.id).limit(limit).all()

    def get_by_reference(self, session: Session, reference: str) -> Optional[Transaction]:
        """Récupère une transaction par sa référence"""
        return session.query(Transaction).filter(Transaction.reference == reference).first()


class TransactionAuditRepository(BaseRepository[TransactionAudit]):
    """Repository pour l'audit des transactions"""
    
    def __init__(self):
        super().__init__(TransactionAudit)
    
    def get_by_transaction(self, session: Session, transaction_id: int) -> List[TransactionAudit]:
        """Récupère l'historique d'audit d'une transaction (Purified Sort)"""
        return session.query(TransactionAudit).filter(
            TransactionAudit.transaction_id == transaction_id
        ).order_by(TransactionAudit.id).all()
    
    def create_audit_entry(self, session: Session, transaction_id: int, action: str, 
                          user: str = "system", old_data: str = None, new_data: str = None):
        """Crée une entrée d'audit"""
        audit = TransactionAudit(
            transaction_id=transaction_id,
            action=action,
            user=user,
            old_data=old_data,
            new_data=new_data
        )
        session.add(audit)
        session.flush()
        return audit
