"""
Service pour le module Warehouse (Gestion des entrepôts)
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from core.database import get_session
from core.repositories import BaseRepository
from core.models import Warehouse, WarehouseStock, WarehouseMovement


class WarehouseRepository(BaseRepository[Warehouse]):
    """Repository pour les entrepôts"""
    def __init__(self):
        super().__init__(Warehouse)
    
    def get_active(self, session: Session) -> List[Warehouse]:
        return session.query(Warehouse).filter(Warehouse.is_active == True).order_by(Warehouse.id).all()
    
    def get_main_warehouse(self, session: Session) -> Optional[Warehouse]:
        """Récupère le склад principal"""
        return session.query(Warehouse).filter(Warehouse.is_main == True).first()


class WarehouseStockRepository(BaseRepository[WarehouseStock]):
    """Repository pour les stocks"""
    def __init__(self):
        super().__init__(WarehouseStock)
    
    def get_by_warehouse(self, session: Session, warehouse_id: int) -> List[WarehouseStock]:
        return session.query(WarehouseStock).filter(
            WarehouseStock.warehouse_id == warehouse_id,
            WarehouseStock.is_active == True
        ).all()
    
    def get_by_customer(self, session: Session, customer_id: int) -> List[WarehouseStock]:
        return session.query(WarehouseStock).filter(
            WarehouseStock.customer_id == customer_id,
            WarehouseStock.is_active == True
        ).all()


class WarehouseMovementRepository(BaseRepository[WarehouseMovement]):
    """Repository pour les mouvements"""
    def __init__(self):
        super().__init__(WarehouseMovement)
    
    def get_by_warehouse(self, session: Session, warehouse_id: int) -> List[WarehouseMovement]:
        return session.query(WarehouseMovement).filter(
            WarehouseMovement.warehouse_id == warehouse_id
        ).order_by(WarehouseMovement.date.desc()).all()


# ============================================================================
# WAREHOUSE SERVICE
# ============================================================================

class WarehouseService:
    """Service principal pour la gestion des entrepôts"""
    
    def __init__(self):
        self.warehouse_repo = WarehouseRepository()
        self.stock_repo = WarehouseStockRepository()
        self.movement_repo = WarehouseMovementRepository()
    
    # --- CRUD ENTREPÔTS ---
    def get_all_warehouses(self) -> List[Dict[str, Any]]:
        """Récupère tous les entrepôts"""
        with get_session() as session:
            warehouses = self.warehouse_repo.get_active(session)
            return [
                {
                    "id": w.id,
                    "name": w.name,
                    "address": w.address or "",
                    "is_main": w.is_main,
                    "notes": w.notes or ""
                } for w in warehouses
            ]
    
    def create_warehouse(self, name: str, address: str = "", is_main: bool = False, notes: str = "") -> Tuple[bool, str, Optional[int]]:
        """Crée un nouvel entrepôt"""
        if not name or not name.strip():
            return False, "Le nom est obligatoire", None
        
        try:
            with get_session() as session:
                # Vérifier si un autre entrepôt principal existe
                if is_main:
                    existing_main = self.warehouse_repo.get_main_warehouse(session)
                    if existing_main:
                        return False, "Il existe déjà un entrepôt principal", None
                
                warehouse = self.warehouse_repo.create(
                    session,
                    name=name.strip(),
                    address=address,
                    is_main=is_main,
                    notes=notes,
                    is_active=True
                )
                session.commit()
                return True, "Entrepôt créé avec succès", warehouse.id
        except Exception as e:
            return False, f"Erreur: {str(e)}", None
    
    def update_warehouse(self, warehouse_id: int, **data) -> Tuple[bool, str]:
        """Met à jour un entrepôt"""
        try:
            with get_session() as session:
                warehouse = self.warehouse_repo.get_by_id(session, warehouse_id)
                if not warehouse:
                    return False, "Entrepôt non trouvé"
                
                # Si on veut définir comme principal, vérifier qu'il n'y en a pas un autre
                if data.get('is_main') and not warehouse.is_main:
                    existing_main = self.warehouse_repo.get_main_warehouse(session)
                    if existing_main and existing_main.id != warehouse_id:
                        return False, "Il existe déjà un entrepôt principal"
                
                for key, value in data.items():
                    setattr(warehouse, key, value)
                
                session.commit()
                return True, "Entrepôt mis à jour"
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    def delete_warehouse(self, warehouse_id: int) -> Tuple[bool, str]:
        """Supprime (désactive) un entrepôt"""
        try:
            with get_session() as session:
                warehouse = self.warehouse_repo.get_by_id(session, warehouse_id)
                if not warehouse:
                    return False, "Entrepôt non trouvé"
                
                if warehouse.is_main:
                    return False, "Impossible de supprimer l'entrepôt principal"
                
                warehouse.is_active = False
                session.commit()
                return True, "Entrepôt supprimé"
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    def get_warehouse(self, warehouse_id: int) -> Optional[Dict[str, Any]]:
        """Récupère un entrepôt par ID"""
        with get_session() as session:
            w = self.warehouse_repo.get_by_id(session, warehouse_id)
            if not w:
                return None
            return {
                "id": w.id,
                "name": w.name,
                "address": w.address or "",
                "is_main": w.is_main,
                "notes": w.notes or ""
            }
    
    # --- GESTION STOCKS ---
    def get_warehouse_stocks(self, warehouse_id: int) -> List[Dict[str, Any]]:
        """Récupère les stocks d'un entrepôt"""
        with get_session() as session:
            stocks = self.stock_repo.get_by_warehouse(session, warehouse_id)
            return [
                {
                    "id": s.id,
                    "customer_id": s.customer_id,
                    "customer_name": s.customer.name if s.customer else "N/A",
                    "container_id": s.container_id,
                    "goods_type": s.goods_type or "",
                    "quantity": s.quantity,
                    "weight": s.weight,
                    "notes": s.notes or ""
                } for s in stocks
            ]
    
    def get_all_stocks(self) -> List[Dict[str, Any]]:
        """Récupère tous les stocks"""
        with get_session() as session:
            stocks = self.stock_repo.get_all(session)
            return [
                {
                    "id": s.id,
                    "warehouse_id": s.warehouse_id,
                    "warehouse_name": s.warehouse.name if s.warehouse else "N/A",
                    "customer_id": s.customer_id,
                    "customer_name": s.customer.name if s.customer else "N/A",
                    "container_id": s.container_id,
                    "goods_type": s.goods_type or "",
                    "quantity": s.quantity,
                    "weight": s.weight,
                    "notes": s.notes or ""
                } for s in stocks
            ]
    
    # --- MOUVEMENTS ---
    def get_warehouse_movements(self, warehouse_id: int) -> List[Dict[str, Any]]:
        """Récupère les mouvements d'un entrepôt"""
        with get_session() as session:
            movements = self.movement_repo.get_by_warehouse(session, warehouse_id)
            return [
                {
                    "id": m.id,
                    "movement_type": m.movement_type,
                    "customer_id": m.customer_id,
                    "customer_name": m.customer.name if m.customer else "N/A",
                    "container_id": m.container_id,
                    "quantity": m.quantity,
                    "weight": m.weight,
                    "notes": m.notes or "",
                    "date": m.date
                } for m in movements
            ]
    
    def create_stock(self, warehouse_id: int, customer_id: int, container_id: int = None,
                     goods_type: str = "", quantity: int = 0, weight: float = 0.0, notes: str = "") -> Tuple[bool, str, Optional[int]]:
        """Crée un nouveau stock (استلام بضاعة)"""
        try:
            with get_session() as session:
                stock = self.stock_repo.create(
                    session,
                    warehouse_id=warehouse_id,
                    customer_id=customer_id,
                    container_id=container_id,
                    goods_type=goods_type,
                    quantity=quantity,
                    weight=weight,
                    notes=notes,
                    is_active=True
                )
                
                # Enregistrer le mouvement
                self.movement_repo.create(
                    session,
                    warehouse_id=warehouse_id,
                    customer_id=customer_id,
                    container_id=container_id,
                    movement_type="RECEIVE",
                    quantity=quantity,
                    weight=weight,
                    notes=notes,
                    date=datetime.now(),
                    is_active=True
                )
                
                session.commit()
                return True, "Stock créé avec succès", stock.id
        except Exception as e:
            return False, f"Erreur: {str(e)}", None
    
    def deliver_stock(self, stock_id: int, quantity: int, notes: str = "") -> Tuple[bool, str]:
        """تسليم بضاعة (تسليم جزئي أو كلي)"""
        try:
            with get_session() as session:
                stock = self.stock_repo.get_by_id(session, stock_id)
                if not stock:
                    return False, "Stock non trouvé"
                
                if quantity > stock.quantity:
                    return False, "La quantité à livrer dépasse le stock disponible"
                
                # Enregistrer le mouvement de livraison
                self.movement_repo.create(
                    session,
                    warehouse_id=stock.warehouse_id,
                    customer_id=stock.customer_id,
                    container_id=stock.container_id,
                    movement_type="DELIVER",
                    quantity=quantity,
                    weight=stock.weight * (quantity / stock.quantity) if stock.quantity > 0 else 0,
                    notes=notes,
                    date=datetime.now(),
                    is_active=True
                )
                
                # Réduire le stock
                stock.quantity -= quantity
                if stock.quantity == 0:
                    stock.is_active = False
                
                session.commit()
                return True, "Livraison enregistrée"
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    def receive_from_container(self, container_id: int, warehouse_id: int, customer_id: int, 
                                goods_type: str = "", quantity: int = 0, weight: float = 0.0, 
                                notes: str = "") -> Tuple[bool, str, Optional[int]]:
        """استلام بضاعة من حاوية -_receive from container"""
        try:
            with get_session() as session:
                # Create stock
                stock = self.stock_repo.create(
                    session,
                    warehouse_id=warehouse_id,
                    customer_id=customer_id,
                    container_id=container_id,
                    goods_type=goods_type,
                    quantity=quantity,
                    weight=weight,
                    notes=notes,
                    is_active=True
                )
                
                # Record movement
                self.movement_repo.create(
                    session,
                    warehouse_id=warehouse_id,
                    customer_id=customer_id,
                    container_id=container_id,
                    movement_type="RECEIVE",
                    quantity=quantity,
                    weight=weight,
                    notes=f"استلام من حاوية: {notes}",
                    date=datetime.now(),
                    is_active=True
                )
                
                session.commit()
                return True, "بضاعة المستلمة من الحاوية", stock.id
        except Exception as e:
            return False, f"Erreur: {str(e)}", None

    def receive_goods_from_container(self, container_id: int, warehouse_id: int,
                                       received_data: list) -> Tuple[bool, str, Optional[int]]:
        """Receive goods from container with manual lost value input"""
        try:
            with get_session() as session:
                total_stock_created = 0
                total_lost_value_dzd = 0.0
                
                for item in received_data:
                    customer_id = item['customer_id']
                    goods_type = item['goods_type']
                    original_cartons = item['original_cartons']
                    original_cbm = item['original_cbm']
                    received_cartons = item['received_cartons']
                    cbm_price_usd = item.get('cbm_price_usd', 0)
                    discount_usd = item.get('discount_usd', 0)
                    exchange_rate = item.get('exchange_rate', 150)
                    lost_value_dzd = item.get('lost_value_dzd', 0)
                    
                    lost_cartons = original_cartons - received_cartons
                    total_lost_value_dzd += lost_value_dzd
                    
                    if received_cartons > 0:
                        # Valeur Expédition = (CBM × Prix CBM × Taux) - Remise
                        shipping_value_dzd = original_cbm * cbm_price_usd * exchange_rate
                        discount_dzd = discount_usd * exchange_rate
                        valeur_expe_dzd = shipping_value_dzd - discount_dzd
                        
                        # Solde = Valeur expé - Valeur perdue
                        saldo_dzd = valeur_expe_dzd - lost_value_dzd
                        
                        stock = self.stock_repo.create(
                            session,
                            warehouse_id=warehouse_id,
                            customer_id=customer_id,
                            container_id=container_id,
                            goods_type=goods_type,
                            quantity=received_cartons,
                            weight=original_cbm,
                            notes=f"Original: {original_cartons}, Lost: {lost_cartons}, Val. expé: {valeur_expe_dzd:,.0f} DA, Solde: {saldo_dzd:,.0f} DA",
                            is_active=True
                        )
                        
                        self.movement_repo.create(
                            session,
                            warehouse_id=warehouse_id,
                            customer_id=customer_id,
                            container_id=container_id,
                            movement_type="RECEIVE",
                            quantity=received_cartons,
                            weight=original_cbm,
                            notes=f"Reçu: {received_cartons}, Perdu: {lost_cartons}, Val. expé: {valeur_expe_dzd:,.0f} DA, Solde: {saldo_dzd:,.0f} DA",
                            date=datetime.now(),
                            is_active=True
                        )
                        total_stock_created += 1
                
                session.commit()
                
                msg = f"Reçu {total_stock_created} marchandise(s)"
                if total_lost_value_dzd > 0:
                    msg += f" - Perte: {total_lost_value_dzd:,.0f} DA"
                
                return True, msg, total_stock_created
        except Exception as e:
            return False, f"Erreur: {str(e)}", None