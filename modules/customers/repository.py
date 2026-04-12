"""
Repository pour le module Clients (Customers)
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime

from core.repositories import BaseRepository
from core.models import Customer, CustomerGoods, CustomerPayment, CustomerSideCost, SideCostType


class CustomerRepository(BaseRepository[Customer]):
    """Repository pour les clients"""
    def __init__(self):
        super().__init__(Customer)
    
    def search(self, session: Session, query: str) -> List[Customer]:
        """Recherche de clients par nom (Purified Sort)"""
        search_pattern = f"%{query}%"
        return session.query(Customer).filter(
            Customer.name.like(search_pattern)
        ).order_by(Customer.id).all()


class CustomerGoodsRepository(BaseRepository[CustomerGoods]):
    """Repository pour les marchandises des clients"""
    def __init__(self):
        super().__init__(CustomerGoods)
        
    def get_by_customer(self, session: Session, customer_id: int) -> List[CustomerGoods]:
        """Récupère les marchandises d'un client (Purified Sort)"""
        return session.query(CustomerGoods).filter(
            CustomerGoods.customer_id == customer_id
        ).order_by(CustomerGoods.id).all()
        
    def get_by_container(self, session: Session, container_id: int) -> List[CustomerGoods]:
        """Récupère les marchandises dans un conteneur spécifique (Purified Sort)"""
        return session.query(CustomerGoods).filter(
            CustomerGoods.container_id == container_id
        ).order_by(CustomerGoods.id).all()


class CustomerPaymentRepository(BaseRepository[CustomerPayment]):
    """Repository pour les paiements des clients"""
    def __init__(self):
        super().__init__(CustomerPayment)
        
    def get_by_customer(self, session: Session, customer_id: int) -> List[CustomerPayment]:
        """Récupère l'historique des paiements d'un client (Purified Sort)"""
        return session.query(CustomerPayment).filter(
            CustomerPayment.customer_id == customer_id
        ).order_by(CustomerPayment.id).all()


class CustomerSideCostRepository(BaseRepository[CustomerSideCost]):
    """Repository pour les frais annexes des clients"""
    def __init__(self):
        super().__init__(CustomerSideCost)
        
    def get_by_customer(self, session: Session, customer_id: int) -> List[CustomerSideCost]:
        """Récupère les frais annexes d'un client (Purified Sort)"""
        return session.query(CustomerSideCost).filter(
            CustomerSideCost.customer_id == customer_id
        ).order_by(CustomerSideCost.id).all()


class SideCostTypeRepository(BaseRepository[SideCostType]):
    """Repository pour les types de frais annexes"""
    def __init__(self):
        super().__init__(SideCostType)
