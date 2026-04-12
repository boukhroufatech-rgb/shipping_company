"""
Service Logic pour le module Clients (Customers)
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from .repository import (
    CustomerRepository, CustomerGoodsRepository, 
    CustomerPaymentRepository, CustomerSideCostRepository,
    SideCostTypeRepository
)
from modules.treasury.service import TreasuryService
from core.database import get_session
from core.models import Customer, CustomerGoods, CustomerPayment, CustomerSideCost


class CustomerService:
    """Service pour la gestion des clients et leur comptabilité"""
    
    def __init__(self):
        self.customer_repo = CustomerRepository()
        self.goods_repo = CustomerGoodsRepository()
        self.payment_repo = CustomerPaymentRepository()
        self.side_cost_repo = CustomerSideCostRepository()
        self.cost_type_repo = SideCostTypeRepository()
        self.treasury_service = TreasuryService()

    # --- CLIENTS CRUD ---
    def get_all_customers(self, filter_status: str = "active") -> List[Dict[str, Any]]:
        """Récupère les clients selon leur statut (active, inactive, all)"""
        with get_session() as session:
            if filter_status == "active":
                customers = self.customer_repo.get_active(session)
            elif filter_status == "inactive":
                customers = self.customer_repo.get_inactive(session)
            else: # "all"
                customers = self.customer_repo.get_all(session, include_inactive=True)
                
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "phone": c.phone or "",
                    "address": c.address or "",
                    "notes": c.notes or "",
                    "is_active": c.is_active,
                    "initial_balance": float(c.initial_balance or 0)
                } for c in customers
            ]

    def create_customer(self, name: str, phone: str = None, address: str = None, notes: str = None, initial_balance: float = 0):
        with get_session() as session:
            customer = self.customer_repo.create(
                session, 
                name=name, 
                phone=phone, 
                address=address, 
                notes=notes,
                initial_balance=initial_balance
            )
            session.commit()
            return customer

    def update_customer(self, customer_id: int, **data) -> bool:
        """Met à jour un client (Purified)"""
        with get_session() as session:
            success = self.customer_repo.update(session, customer_id, **data)
            session.commit()
            return success

    def delete_customer(self, customer_id: int) -> bool:
        """Désactive un client (Soft Delete)"""
        with get_session() as session:
            success = self.customer_repo.soft_delete(session, customer_id)
            session.commit()
            return success

    def restore_customer(self, customer_id: int) -> bool:
        """Réactive un client archivé"""
        with get_session() as session:
            success = self.customer_repo.restore(session, customer_id)
            session.commit()
            return success

    # --- GOODS & CONTAINERS ---
    def get_all_goods(self) -> List[Dict[str, Any]]:
        """Récupère toutes les bourses de clients (Purified)"""
        with get_session() as session:
            goods = self.goods_repo.get_all(session)
            return [
                {
                    "id": g.id,
                    "date": g.date,
                    "customer_id": g.customer_id,
                    "customer_name": g.customer.name if g.customer else "N/A",
                    "container_id": g.container_id,
                    "container_number": g.container.container_number if g.container else "N/A",
                    "goods_type": g.goods_type,
                    "cartons": g.cartons,
                    "cbm": g.cbm,
                    "cbm_price_dzd": g.cbm_price_dzd,
                    "discount": g.discount,
                    "total_net": g.total_net,
                    "notes": g.notes or ""
                } for g in goods
            ]

    def get_customer_goods_by_id(self, goods_id: int) -> Optional[Dict[str, Any]]:
        """Récupère une bourse par ID (Purified)"""
        with get_session() as session:
            g = self.goods_repo.get_by_id(session, goods_id)
            if not g: return None
            return {
                "id": g.id, "customer_id": g.customer_id, "container_id": g.container_id,
                "goods_type": g.goods_type, "cartons": g.cartons, "cbm": g.cbm,
                "cbm_price_dzd": g.cbm_price_dzd, "discount": g.discount, "notes": g.notes or ""
            }

    def add_customer_goods(self, customer_id: int, container_id: int, goods_type: str, 
                           cartons: int, cbm: float, cbm_price: float, 
                           discount: float = 0.0, notes: str = None, date: datetime = None):
        with get_session() as session:
            goods = self.goods_repo.create(
                session,
                customer_id=customer_id,
                container_id=container_id,
                goods_type=goods_type,
                cartons=cartons,
                cbm=cbm,
                cbm_price_dzd=cbm_price,
                discount=discount,
                notes=notes,
                date=datetime.now()
            )
            session.commit()
            return goods

    def update_customer_goods(self, goods_id: int, **data) -> bool:
        """Met à jour une bourse (Purified)"""
        with get_session() as session:
            success = self.goods_repo.update(session, goods_id, **data)
            session.commit()
            return success

    def delete_customer_goods(self, goods_id: int) -> bool:
        """Supprime une bourse (Purified)"""
        with get_session() as session:
            success = self.goods_repo.soft_delete(session, goods_id)
            session.commit()
            return success

    # --- PAYMENTS (TREASURY LINK) ---
    def get_all_payments(self) -> List[Dict[str, Any]]:
        """Récupère tous les paiements clients (Purified)"""
        with get_session() as session:
            payments = self.payment_repo.get_all(session)
            return [
                {
                    "id": p.id,
                    "date": p.date,
                    "customer_id": p.customer_id,
                    "customer_name": p.customer.name if p.customer else "N/A",
                    "account_id": p.account_id,
                    "account_name": p.account.name if p.account else "N/A",
                    "amount": p.amount,
                    "reference": p.reference or "",
                    "notes": p.notes or ""
                } for p in payments
            ]

    def receive_payment(self, customer_id: int, account_id: int, amount: float, 
                      reference: str = None, notes: str = None, date: datetime = None):
        """Reçoit un paiement d'un client et l'enregistre dans la trésorerie"""
        with get_session() as session:
            # 1. Créer la transaction de trésorerie (Crédit car l'argent entre)
            desc = f"Paiement reçu du client #{customer_id}"
            if reference: desc += f" (Réf: {reference})"
            
            success, msg, treasury_tx_id = self.treasury_service.create_transaction(
                account_id=account_id,
                amount=amount,
                transaction_type="CREDIT",
                description=desc,
                reference=reference,
                date=date or datetime.now()
            )
            
            if not success:
                return False, f"Erreur Trésorerie: {msg}"

            # 2. Enregistrer le paiement dans le module client
            payment = self.payment_repo.create(
                session,
                customer_id=customer_id,
                account_id=account_id,
                transaction_id=treasury_tx_id,
                amount=amount,
                reference=reference,
                notes=notes,
                date=date or datetime.now()
            )
            session.commit()
            return True, "Paiement enregistré avec succès"

    # --- SIDE COSTS ---
    def get_all_side_costs(self) -> List[Dict[str, Any]]:
        """Récupère tous les frais annexes (Purified)"""
        with get_session() as session:
            costs = self.side_cost_repo.get_all(session)
            return [
                {
                    "id": c.id,
                    "date": c.date,
                    "customer_id": c.customer_id,
                    "customer_name": c.customer.name if c.customer else "N/A",
                    "cost_type_id": c.cost_type_id,
                    "cost_type_name": c.cost_type.name if c.cost_type else "N/A",
                    "amount": c.amount,
                    "notes": c.notes or ""
                } for c in costs
            ]

    def get_all_cost_types(self) -> List[Dict[str, Any]]:
        """Récupère les types de frais (Purified)"""
        with get_session() as session:
            types = self.cost_type_repo.get_all(session)
            return [{"id": t.id, "name": t.name} for t in types]
    
    def get_cost_type(self, cost_type_id: int) -> Optional[Dict[str, Any]]:
        """Récupère un type de frais par ID"""
        with get_session() as session:
            cost_type = self.cost_type_repo.get_by_id(session, cost_type_id)
            if cost_type:
                return {"id": cost_type.id, "name": cost_type.name}
            return None

    def create_cost_type(self, name: str, description: str = "") -> Tuple[bool, str, Optional[int]]:
        """Créer un nouveau type de frais"""
        if not name or not name.strip():
            return False, "Le nom est obligatoire", None
        try:
            with get_session() as session:
                cost_type = self.cost_type_repo.create(session, name=name.strip())
                session.commit()
                return True, "Type créé avec succès", cost_type.id
        except Exception as e:
            return False, f"Erreur: {str(e)}", None

    def delete_cost_type(self, type_id: int) -> Tuple[bool, str]:
        """Supprimer un type de frais (Soft Delete)"""
        try:
            with get_session() as session:
                success = self.cost_type_repo.soft_delete(session, type_id)
                if success:
                    session.commit()
                    return True, "Type supprimé"
                return False, "Type non trouvé"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def restore_cost_type(self, type_id: int) -> Tuple[bool, str]:
        """Restaurer un type de frais supprimé"""
        try:
            with get_session() as session:
                cost_type = self.cost_type_repo.get_by_id(session, type_id)
                if cost_type:
                    cost_type.is_active = True
                    session.commit()
                    return True, "Type restauré"
                return False, "Type non trouvé"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def get_side_cost(self, cost_id: int) -> Optional[Dict[str, Any]]:
        """Récupère un frais par ID (Purified)"""
        with get_session() as session:
            c = self.side_cost_repo.get_by_id(session, cost_id)
            if not c: return None
            return {
                "id": c.id, "customer_id": c.customer_id, "cost_type_id": c.cost_type_id,
                "amount": c.amount, "notes": c.notes or ""
            }

    def add_side_cost(self, customer_id: int, cost_type_id: int, amount: float, 
                      notes: str = None, date: datetime = None):
        cost_type = self.get_cost_type(cost_type_id)
        cost_type_name = cost_type['name'] if cost_type else "Frais"
        
        with get_session() as session:
            cost = self.side_cost_repo.create(
                session,
                customer_id=customer_id,
                cost_type_id=cost_type_id,
                amount=amount,
                notes=notes,
                date=date or datetime.now()
            )
            session.commit()
            
            customer = self.customer_repo.get_by_id(session, customer_id)
            customer_name = customer.name if customer else "Client"
            
            main_account = self.treasury_service.account_repo.get_main_account(session)
            if main_account:
                self.treasury_service.create_transaction(
                    account_id=int(main_account.id),
                    transaction_type="DEBIT",
                    amount=float(amount),
                    description=f"Frais: {cost_type_name} - {customer_name}",
                    reference=f"COST-{cost.id}",
                    category="FRAIS",
                    source="CLIENT",
                    source_id=int(customer_id),
                    user="system"
                )
            
            return cost

    def update_side_cost(self, cost_id: int, **data) -> bool:
        """Met à jour un frais (Purified)"""
        with get_session() as session:
            success = self.side_cost_repo.update(session, cost_id, **data)
            session.commit()
            return success

    def delete_side_cost(self, cost_id: int) -> bool:
        """Supprime un frais (Purified)"""
        with get_session() as session:
            success = self.side_cost_repo.soft_delete(session, cost_id)
            session.commit()
            return success

    # --- LEDGER & BALANCE ---
    def get_customer_ledger(self, customer_id: int) -> List[Dict[str, Any]]:
        """
        Génère un relevé de compte complet (Ledger) chronologique.
        Suit la règle 'Oldest First' آلياً.
        """
        with get_session() as session:
            ledger = []
            
            # 0. Charger le solde initial
            customer = self.customer_repo.get_by_id(session, customer_id)
            initial_balance = float(customer.initial_balance or 0) if customer else 0
            
            # Add initial balance as first entry in statement
            if initial_balance != 0:
                ledger.append({
                    "date": customer.created_at if customer else datetime.now(),
                    "type": "SOLDE INITIAL",
                    "desc": "Solde initial",
                    "debit": initial_balance if initial_balance > 0 else 0,
                    "credit": abs(initial_balance) if initial_balance < 0 else 0,
                    "balance": initial_balance,
                    "obj": None,
                    "is_initial": True
                })
            
            # 1. Charger bourses (Débits)
            goods = self.goods_repo.get_by_customer(session, customer_id)
            for g in goods:
                ledger.append({
                    "date": g.date,
                    "type": "MARCHANDISE",
                    "desc": f"Chargement {g.goods_type} (Conteneur #{g.container_id})",
                    "debit": g.total_net,
                    "credit": 0.0,
                    "obj": g
                })
            
            # 2. Charger frais annexes (Débits)
            costs = self.side_cost_repo.get_by_customer(session, customer_id)
            for c in costs:
                ledger.append({
                    "date": c.date,
                    "type": "FRAIS",
                    "desc": f"Frais: {c.cost_type.name if c.cost_type else 'Divers'}",
                    "debit": c.amount,
                    "credit": 0.0,
                    "obj": c
                })
            
            # 3. Charger paiements (Crédits)
            payments = self.payment_repo.get_by_customer(session, customer_id)
            for p in payments:
                ledger.append({
                    "date": p.date,
                    "type": "PAIEMENT",
                    "desc": f"Versement: {p.reference or 'N/A'}",
                    "debit": 0.0,
                    "credit": p.amount,
                    "obj": p
                })
            
            # Sort by date (Ensure Purified Sort)
            ledger.sort(key=lambda x: x['date'])
            
            # Calculate progressive balance (initial balance is already in statement)
            balance = 0.0  # Start from 0, not initial_balance (initial is already in ledger)
            results = []
            for item in ledger:
                balance += (item['debit'] - item['credit'])
                # Convert data to independent objects
                obj = item['obj']
                results.append({
                    "date": item['date'],
                    "type": item['type'],
                    "desc": item['desc'],
                    "debit": item['debit'],
                    "credit": item['credit'],
                    "balance": balance,
                    "id": obj.id if obj else None
                })
                
            return results

    def get_customer_balance(self, customer_id: int) -> float:
        """Calcule le solde actuel d'un client (مع الرصيد الافتتاحي)"""
        with get_session() as session:
            customer = self.customer_repo.get_by_id(session, customer_id)
            initial = float(customer.initial_balance or 0) if customer else 0
            ledger = self.get_customer_ledger(customer_id)
            return ledger[-1]['balance'] if ledger else initial

    def get_customer_total_business(self, customer_id: int) -> float:
        """احسب رقم الأعمال (بدون تخفيض) = مجموع (CBM × السعر)"""
        with get_session() as session:
            goods = self.goods_repo.get_by_customer(session, customer_id)
            return sum(g.cbm * g.cbm_price_dzd for g in goods)

    def get_customer_total_costs(self, customer_id: int) -> float:
        """احسب التكاليف (Frais annexes)"""
        with get_session() as session:
            costs = self.side_cost_repo.get_by_customer(session, customer_id)
            return sum(c.amount for c in costs)

    def get_customer_total_discounts(self, customer_id: int) -> float:
        """احسب التخفيضات (المبلغ المخفض)"""
        with get_session() as session:
            goods = self.goods_repo.get_by_customer(session, customer_id)
            return sum((g.cbm * g.cbm_price_dzd) * (g.discount / 100) for g in goods)

    def get_customer_total_payments(self, customer_id: int) -> float:
        """احسب الدفعات"""
        with get_session() as session:
            payments = self.payment_repo.get_by_customer(session, customer_id)
            return sum(p.amount for p in payments)
