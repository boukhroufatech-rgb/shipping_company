"""
Repository pour le module Gestion des Devises
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime

from core.repositories import BaseRepository
from core.models import Currency, ExchangeRate, CurrencySupplier, CurrencyPurchase, SupplierPayment


class CurrencyRepository(BaseRepository[Currency]):
    """Repository pour les devises"""
    
    def __init__(self):
        super().__init__(Currency)
    
    def get_by_code(self, session: Session, code: str) -> Optional[Currency]:
        """Récupère une devise par son code"""
        return session.query(Currency).filter(Currency.code == code).first()
    
    def get_default_currency(self, session: Session) -> Optional[Currency]:
        """Récupère la devise par défaut (DZD)"""
        return session.query(Currency).filter(Currency.is_default == True).first()
    
    def get_deletable_currencies(self, session: Session) -> List[Currency]:
        """Récupère les devises supprimables (Purified Sort)"""
        return session.query(Currency).filter(
            and_(Currency.is_active == True, Currency.is_deletable == True)
        ).order_by(Currency.id).all()


class ExchangeRateRepository(BaseRepository[ExchangeRate]):
    """Repository pour les taux de change"""
    
    def __init__(self):
        super().__init__(ExchangeRate)
    
    def get_latest_rate(self, session: Session, currency_id: int) -> Optional[ExchangeRate]:
        """Récupère le dernier taux de change actif pour une devise (Tri DESC nécessaire pour le calcul)"""
        return session.query(ExchangeRate).filter(
            and_(ExchangeRate.currency_id == currency_id, ExchangeRate.is_active == True)
        ).order_by(desc(ExchangeRate.date)).first()
    
    def get_rates_by_currency(self, session: Session, currency_id: int) -> List[ExchangeRate]:
        """Récupère tous les taux de change d'une devise (Tri ASC / Purified Sort)"""
        return session.query(ExchangeRate).filter(
            ExchangeRate.currency_id == currency_id
        ).order_by(ExchangeRate.id).all()


class CurrencySupplierRepository(BaseRepository[CurrencySupplier]):
    """Repository pour les fournisseurs de devises"""
    
    def __init__(self):
        super().__init__(CurrencySupplier)
    
    def get_active_suppliers(self, session: Session, supplier_type: str = None) -> List[CurrencySupplier]:
        """Récupère les fournisseurs actifs avec filtre optionnel (Purified Sort)"""
        query = session.query(CurrencySupplier).filter(CurrencySupplier.is_active == True)
        if supplier_type:
            query = query.filter(CurrencySupplier.supplier_type == supplier_type)
        return query.order_by(CurrencySupplier.id).all()
    
    def get_suppliers_with_balance(self, session: Session, supplier_type: str = None) -> List[CurrencySupplier]:
        """Récupère les fournisseurs avec un solde (dette) > 0 (Purified Sort)"""
        query = session.query(CurrencySupplier).filter(
            and_(CurrencySupplier.is_active == True, CurrencySupplier.balance > 0)
        )
        if supplier_type:
            query = query.filter(CurrencySupplier.supplier_type == supplier_type)
        return query.order_by(CurrencySupplier.id).all()
    
    def update_balance(self, session: Session, supplier_id: int, amount: float, is_purchase: bool) -> bool:
        """
        Met à jour le solde d'un fournisseur.
        """
        supplier = self.get_by_id(session, supplier_id)
        if not supplier:
            return False
        
        if is_purchase:
            supplier.balance += amount
        else:
            supplier.balance -= amount
        
        session.flush()
        return True


class CurrencyPurchaseRepository(BaseRepository[CurrencyPurchase]):
    """Repository pour les achats de devises"""
    
    def __init__(self):
        super().__init__(CurrencyPurchase)
    
    def get_by_currency(self, session: Session, currency_id: int, limit: int = 100) -> List[CurrencyPurchase]:
        """Récupère les achats d'une devise (Purified Sort)"""
        return session.query(CurrencyPurchase).filter(
            CurrencyPurchase.currency_id == currency_id
        ).order_by(CurrencyPurchase.id).limit(limit).all()
    
    def get_by_supplier(self, session: Session, supplier_id: int, limit: int = 100) -> List[CurrencyPurchase]:
        """Récupère les achats d'un fournisseur (Purified Sort)"""
        return session.query(CurrencyPurchase).filter(
            CurrencyPurchase.supplier_id == supplier_id
        ).order_by(CurrencyPurchase.id).limit(limit).all()
    
    def get_credit_purchases(self, session: Session, limit: int = 100) -> List[CurrencyPurchase]:
        """Récupère les achats à crédit (Purified Sort)"""
        return session.query(CurrencyPurchase).filter(
            CurrencyPurchase.payment_type == "CREDIT"
        ).order_by(CurrencyPurchase.id).limit(limit).all()


class SupplierPaymentRepository(BaseRepository[SupplierPayment]):
    """Repository pour les paiements aux fournisseurs"""
    
    def __init__(self):
        super().__init__(SupplierPayment)
    
    def get_by_supplier(self, session: Session, supplier_id: int, limit: int = 100) -> List[SupplierPayment]:
        """Récupère les paiements d'un fournisseur (Purified Sort)"""
        return session.query(SupplierPayment).filter(
            SupplierPayment.supplier_id == supplier_id
        ).order_by(SupplierPayment.id).limit(limit).all()
