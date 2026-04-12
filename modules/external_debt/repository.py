"""
Repository pour le module Dettes Externes
"""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from core.repositories import BaseRepository
from core.models import ExternalContact, ExternalTransaction
from utils.constants import (
    EXT_OP_LEND, EXT_OP_REPAY_LEND,
    EXT_OP_BORROW, EXT_OP_REPAY_BORROW
)


class ExternalContactRepository(BaseRepository[ExternalContact]):
    """Repository pour les contacts externes"""
    
    def __init__(self):
        super().__init__(ExternalContact)
    
    def get_active_contacts(self, session: Session) -> List[ExternalContact]:
        """Récupère les contacts actifs (Purified Sort)"""
        # Cleanup: Ascending unified order (oldest first)
        return session.query(ExternalContact).filter(
            ExternalContact.is_active == True
        ).order_by(ExternalContact.id).all()


class ExternalTransactionRepository(BaseRepository[ExternalTransaction]):
    """Repository pour les transactions externes"""
    
    def __init__(self):
        super().__init__(ExternalTransaction)
    
    def get_by_contact(self, session: Session, contact_id: int, limit: int = 100) -> List[ExternalTransaction]:
        """Récupère les transactions d'un contact (Purified Sort)"""
        return session.query(ExternalTransaction).filter(
            ExternalTransaction.contact_id == contact_id
        ).order_by(ExternalTransaction.id).limit(limit).all()
        
    def get_contact_balance(self, session: Session, contact_id: int, currency_id: int) -> float:
        """
        Calcule le solde d'un contact (Purified Algorithm)
        [NEW] 2026-04-05: Utilise amount_da pour un calcul unifié en DA
        """
        transactions = session.query(ExternalTransaction).filter(
            and_(
                ExternalTransaction.contact_id == contact_id,
                ExternalTransaction.currency_id == currency_id
            )
        ).all()

        balance = 0.0
        for t in transactions:
            # [NEW] 2026-04-05 - Utiliser amount_da si disponible, sinon amount
            # [FIX] 2026-04-05 - Handle None values for old records
            amount = getattr(t, 'amount_da', None) or t.amount or 0
            if t.type == EXT_OP_LEND: balance += amount
            elif t.type == EXT_OP_REPAY_LEND: balance -= amount
            elif t.type == EXT_OP_BORROW: balance -= amount
            elif t.type == EXT_OP_REPAY_BORROW: balance += amount

        return balance
    
    def get_all_balances(self, session: Session, contact_id: int) -> Dict[int, float]:
        """Récupère les soldes par devise (Purified)"""
        currencies = session.query(ExternalTransaction.currency_id).filter(
            ExternalTransaction.contact_id == contact_id
        ).distinct().all()
        
        balances = {}
        for (curr_id,) in currencies:
            bal = self.get_contact_balance(session, contact_id, curr_id)
            if bal != 0: balances[curr_id] = bal
        
        return balances
