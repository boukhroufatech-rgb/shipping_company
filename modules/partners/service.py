"""
Service pour le module Partenaires
"""
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from core.database import get_session
from core.models import Partner, PartnerTransaction
from .repository import PartnerRepository, PartnerTransactionRepository
from modules.treasury.service import TreasuryService

# Types de transaction
TRANS_CONTRIBUTION = "CONTRIBUTION"
TRANS_WITHDRAWAL = "WITHDRAWAL"
TRANS_PROFIT = "PROFIT_ALLOCATION"

class PartnerService:
    def __init__(self):
        self.partner_repo = PartnerRepository()
        self.transaction_repo = PartnerTransactionRepository()
        self.treasury_service = TreasuryService()

    def get_all_partners(self, filter_status: str = "active") -> List[dict]:
        """Récupère les associés selon le statut (active, inactive, all)"""
        with get_session() as session:
            query = session.query(self.partner_repo.model)
            if filter_status == "active": query = query.filter_by(is_active=True)
            elif filter_status == "inactive": query = query.filter_by(is_active=False)
            
            partners = query.order_by(self.partner_repo.model.id.desc()).all()
            return [
                {
                    'id': p.id,
                    'name': p.name,
                    'phone': p.phone or "",
                    'email': p.email or "",
                    'function': p.function or "",
                    'is_active': p.is_active
                } for p in partners
            ]

    def get_partner_stats(self, partner_id: int) -> Dict[str, Any]:
        """Récupère les statistiques détaillées d'un partenaire"""
        with get_session() as session:
            total_company_contributions = self.partner_repo.get_total_contributions(session)
            partner_stats = self.transaction_repo.get_partner_balance_stats(session, partner_id)
            
            contributions = partner_stats['contributions']
            
            # Calcul du pourcentage
            percentage = 0.0
            if total_company_contributions > 0:
                percentage = (contributions / total_company_contributions) * 100
                
            return {
                **partner_stats,
                'percentage': percentage,
                'remaining': partner_stats['profits'] - partner_stats['withdrawals']
            }

    def get_partners_table_data(self, filter_status: str = "active") -> List[Dict[str, Any]]:
        """Prépare les données pour le tableau principal selon le statut"""
        with get_session() as session:
            query = session.query(self.partner_repo.model)
            if filter_status == "active": query = query.filter_by(is_active=True)
            elif filter_status == "inactive": query = query.filter_by(is_active=False)
            
            partners = query.order_by(self.partner_repo.model.id.desc()).all()
            total_company_contributions = self.partner_repo.get_total_contributions(session)
            
            result = []
            for p in partners:
                stats = self.transaction_repo.get_partner_balance_stats(session, p.id)
                contributions = stats['contributions']
                
                percentage = 0.0
                if total_company_contributions > 0:
                    percentage = (contributions / total_company_contributions) * 100
                
                remaining = stats['profits'] - stats['withdrawals']
                
                result.append({
                    'id': p.id,
                    'name': p.name,
                    'phone': p.phone,
                    'email': p.email,
                    'function': p.function,
                    'total_contributions': contributions,
                    'percentage': percentage,
                    'net_profit': stats['profits'],
                    'total_withdrawals': stats['withdrawals'],
                    'remaining': remaining,
                    'is_active': p.is_active,
                    'status': "Actif" if p.is_active else "Archivé"
                })
            return result

    def create_partner(self, **kwargs) -> Tuple[bool, str]:
        try:
            with get_session() as session:
                self.partner_repo.create(session, **kwargs)
                return True, "Partenaire créé avec succès"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def update_partner(self, partner_id: int, **kwargs) -> Tuple[bool, str]:
        try:
            with get_session() as session:
                self.partner_repo.update(session, partner_id, **kwargs)
                return True, "Partenaire mis à jour"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def delete_partner(self, partner_id: int) -> Tuple[bool, str]:
        """Archive un partenaire (Soft Delete)"""
        try:
            with get_session() as session:
                success = self.partner_repo.soft_delete(session, partner_id)
                session.commit()
                return success, "Partenaire archivé" if success else "Échec"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def restore_partner(self, partner_id: int) -> Tuple[bool, str]:
        """Restaure un partenaire archivé"""
        try:
            with get_session() as session:
                success = self.partner_repo.restore(session, partner_id)
                session.commit()
                return success, "Partenaire restauré" if success else "Échec"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def add_contribution(self, partner_id: int, amount: float, date: datetime, 
                        account_id: int = None, notes: str = "") -> Tuple[bool, str]:
        """
        Ajoute une contribution (Capital).
        Si account_id est fourni, crédite le compte de trésorerie (Entrée d'argent).
        """
        try:
            with get_session() as session:
                partner = self.partner_repo.get_by_id(session, partner_id)
                if not partner: return False, "Partenaire introuvable"
                
                treasury_trans_id = None
                
                # Impact Trésorerie (Optionnel)
                if account_id:
                    success, msg, trans_id = self.treasury_service.create_transaction(
                        account_id=account_id,
                        transaction_type="CREDIT", # Entrée d'argent
                        amount=amount,
                        description=f"Contribution Capital: {partner.name}",
                        reference=f"CONTRIB-{partner_id}-{int(datetime.now().timestamp())}",
                        date=date
                    )
                    if not success: return False, f"Erreur Trésorerie: {msg}"
                    treasury_trans_id = trans_id
                
                # Création Transaction Partenaire
                self.transaction_repo.create(
                    session,
                    partner_id=partner_id,
                    type=TRANS_CONTRIBUTION,
                    amount=amount,
                    date=date,
                    transaction_id=treasury_trans_id,
                    notes=notes
                )
                return True, "Contribution enregistrée"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def record_withdrawal(self, partner_id: int, amount: float, date: datetime, 
                         account_id: int = None, notes: str = "") -> Tuple[bool, str]:
        """
        Enregistre un retrait sur bénéfices.
        Si account_id est fourni, débite le compte de trésorerie (Sortie d'argent).
        """
        try:
            with get_session() as session:
                partner = self.partner_repo.get_by_id(session, partner_id)
                if not partner: return False, "Partenaire introuvable"
                
                treasury_trans_id = None
                
                # Impact Trésorerie (Optionnel)
                if account_id:
                    success, msg, trans_id = self.treasury_service.create_transaction(
                        account_id=account_id,
                        transaction_type="DEBIT", # Sortie d'argent
                        amount=amount,
                        description=f"Retrait Associé: {partner.name}",
                        reference=f"WITHDRAW-{partner_id}-{int(datetime.now().timestamp())}",
                        date=date
                    )
                    if not success: return False, f"Erreur Trésorerie: {msg}"
                    treasury_trans_id = trans_id
                
                # Création Transaction Partenaire
                self.transaction_repo.create(
                    session,
                    partner_id=partner_id,
                    type=TRANS_WITHDRAWAL,
                    amount=amount,
                    date=date,
                    transaction_id=treasury_trans_id,
                    notes=notes
                )
                return True, "Retrait enregistré"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def allocate_profit(self, partner_id: int, amount: float, date: datetime, 
                       notes: str = "") -> Tuple[bool, str]:
        """
        Alloue une part de bénéfice au partenaire.
        N'impacte PAS la trésorerie (c'est une écriture comptable interne).
        """
        try:
            with get_session() as session:
                self.transaction_repo.create(
                    session,
                    partner_id=partner_id,
                    type=TRANS_PROFIT,
                    amount=amount,
                    date=date,
                    notes=notes
                )
                return True, "Bénéfice alloué"
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    def update_transaction(self, transaction_id: int, date: datetime, amount: float, notes: str = "") -> Tuple[bool, str]:
        """Met à jour une transaction et sa liée en trésorerie si elle existe"""
        try:
            with get_session() as session:
                trans = self.transaction_repo.get_by_id(session, transaction_id)
                if not trans: return False, "Transaction introuvable"
                
                # Mise à jour de la transaction trésorerie liée
                if trans.transaction_id:
                    # On récupère la transaction trésorerie via le service (ou repository)
                    # Utilisation directe du repository Treasury pour simplifier car service.update_transaction n'est pas exposé pareil
                    # Ou mieux, on utilise le service Treasury s'il a une méthode update
                    success, msg = self.treasury_service.update_transaction(
                        trans.transaction_id, 
                        date=date, 
                        amount=amount, 
                        description=f"{trans.type} Associé: {trans.partner.name} (Modifié)"
                    )
                    if not success: return False, f"Erreur Trésorerie: {msg}"

                # Mise à jour locale
                self.transaction_repo.update(session, transaction_id, date=date, amount=amount, notes=notes)
                return True, "Transaction mise à jour"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def delete_transaction(self, transaction_id: int) -> Tuple[bool, str]:
        """Archive une transaction de partenaire"""
        try:
            with get_session() as session:
                trans = self.transaction_repo.get_by_id(session, transaction_id)
                if not trans: return False, "Transaction introuvable"
                
                # Suppression trésorerie liée
                if trans.transaction_id:
                    success, msg = self.treasury_service.delete_transaction(trans.transaction_id)
                    if not success: return False, f"Erreur Trésorerie: {msg}"
                
                self.transaction_repo.soft_delete(session, transaction_id)
                session.commit()
                return True, "Transaction archivée"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def restore_transaction(self, transaction_id: int) -> Tuple[bool, str]:
        """Restaure une transaction de partenaire archivée"""
        try:
            with get_session() as session:
                trans = self.transaction_repo.get_by_id(session, transaction_id)
                if not trans: return False, "Transaction introuvable"
                
                # Restauration trésorerie liée
                if trans.transaction_id:
                    success, msg = self.treasury_service.restore_transaction(trans.transaction_id)
                    if not success: return False, f"Erreur Trésorerie: {msg}"
                
                self.transaction_repo.restore(session, transaction_id)
                session.commit()
                return True, "Transaction restaurée"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def get_transactions(self, partner_id: int) -> List[Dict[str, Any]]:
        with get_session() as session:
            transactions = self.transaction_repo.get_by_partner(session, partner_id)
            result = []
            for t in transactions:
                # Extraction des données en DTO pour éviter DetachedInstanceError dans la vue
                dto = {
                    "id": t.id,
                    "date": t.date,
                    "type": t.type,
                    "amount": t.amount,
                    "notes": t.notes,
                    "treasury_reference": None,
                    "treasury_account": None
                }
                
                if t.treasury_transaction:
                    dto["treasury_reference"] = t.treasury_transaction.reference
                    if t.treasury_transaction.account:
                        dto["treasury_account"] = t.treasury_transaction.account.name
                
                result.append(dto)
            return result
