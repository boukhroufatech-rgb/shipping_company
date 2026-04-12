"""
Repository pour le module Partenaires
"""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from core.repositories import BaseRepository
from core.models import Partner, PartnerTransaction, Transaction


class PartnerRepository(BaseRepository[Partner]):
    """Repository pour les associés"""
    
    def __init__(self):
        super().__init__(Partner)
    
    # get_active_partners supprimée car redondante avec get_active()

    def get_total_contributions(self, session: Session) -> float:
        """Calcule le total des contributions de tous les associés (Purified)"""
        result = session.query(func.sum(PartnerTransaction.amount)).filter(
            PartnerTransaction.type == 'CONTRIBUTION',
            PartnerTransaction.is_active == True
        ).scalar()
        return result or 0.0


class PartnerTransactionRepository(BaseRepository[PartnerTransaction]):
    """Repository pour les transactions des associés"""
    
    def __init__(self):
        super().__init__(PartnerTransaction)
    
    def get_by_partner(self, session: Session, partner_id: int) -> List[PartnerTransaction]:
        """Récupère les transactions d'un associé (Purified Sort)"""
        return session.query(PartnerTransaction).options(
            joinedload(PartnerTransaction.treasury_transaction).joinedload(Transaction.account)
        ).filter(
            PartnerTransaction.partner_id == partner_id,
            PartnerTransaction.is_active == True
        ).order_by(PartnerTransaction.id).all()
    
    def get_partner_balance_stats(self, session: Session, partner_id: int) -> Dict[str, float]:
        """
        Calcule les statistiques financières d'un associé (Purified Logic)
        """
        stats = {'contributions': 0.0, 'profits': 0.0, 'withdrawals': 0.0}
        
        transactions = self.get_by_partner(session, partner_id)
        for t in transactions:
            if t.type == 'CONTRIBUTION': stats['contributions'] += t.amount
            elif t.type == 'PROFIT_ALLOCATION': stats['profits'] += t.amount
            elif t.type == 'WITHDRAWAL': stats['withdrawals'] += t.amount
                
        return stats
