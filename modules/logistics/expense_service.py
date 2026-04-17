"""
Service pour la gestion des types de frais et des dépenses réelles
"""
from typing import List, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from core.database import get_session
from core.models import (
    ExpenseType, Expense, Transaction, ContainerFile, ImportLicense,
    TRANSACTION_TYPE_DEBIT, PAYMENT_TYPE_CASH, PAYMENT_TYPE_CREDIT
)
from core.repositories import BaseRepository

class ExpenseService:
    def __init__(self):
        self.type_repo = BaseRepository(ExpenseType)
        self.expense_repo = BaseRepository(Expense)
        
    # ========================================================================
    # GESTION DES TYPES DE DÉPENSES
    # ========================================================================
    
    def create_expense_type(self, name: str, description: str = "", sort_order: int = 0) -> Tuple[bool, str, Optional[int]]:
        """Crée un nouveau type de dépense (compatible avec GenericCatalogDialog)"""
        with get_session() as session:
            try:
                # Vérifier si existe déjà
                existing = session.query(ExpenseType).filter_by(name=name).first()
                if existing:
                    return False, "Ce type de dépense existe déjà", None
                
                exp_type = ExpenseType(
                    name=name,
                    is_direct=True,
                    description=description,
                    sort_order=sort_order
                )
                session.add(exp_type)
                session.commit()
                return True, "Type de dépense créé", exp_type.id
            except Exception as e:
                return False, str(e), None

    def update_expense_type(self, type_id: int, new_name: str) -> Tuple[bool, str]:
        """Met à jour le nom d'un type de dépense"""
        with get_session() as session:
            try:
                exp_type = session.query(ExpenseType).get(type_id)
                if not exp_type:
                    return False, "Type introuvable"
                
                # Check if name already exists
                existing = session.query(ExpenseType).filter(ExpenseType.name == new_name, ExpenseType.id != type_id).first()
                if existing:
                    return False, "Ce nom existe déjà"
                
                exp_type.name = new_name
                session.commit()
                return True, "Type mis à jour"
            except Exception as e:
                return False, str(e)

    def get_all_expense_types(self, include_inactive: bool = False) -> List[dict]:
        """Récupère tous les types de dépenses (compatible avec GenericCatalogDialog)"""
        with get_session() as session:
            # Create defaults if none exist
            default_types = [
                {"name": "Transport / Fret", "description": "Frais de transport maritime ou terrestre", "sort_order": 1},
                {"name": "TAXS", "description": "Droits de douane et taxes (Dédouanement)", "sort_order": 2},
                {"name": "SURISTARIE", "description": "Frais de surestarie", "sort_order": 3},
                {"name": "Magasinage", "description": "Frais de stockage", "sort_order": 4},
                {"name": "TransitAIRE", "description": "Frais de transit", "sort_order": 5},
                {"name": "Logistique / Port", "description": "Frais de logistique portuaire", "sort_order": 6},
                {"name": "Charges Globales", "description": "Charges globales de l'entreprise", "sort_order": 7},
                {"name": "Transport", "description": "Transport local", "sort_order": 8},
                {"name": "Timbre", "description": "Timbre et frais administratifs", "sort_order": 9},
            ]
            
            for dt in default_types:
                existing = session.query(ExpenseType).filter_by(name=dt["name"]).first()
                if not existing:
                    exp_type = ExpenseType(
                        name=dt["name"],
                        description=dt["description"],
                        sort_order=dt["sort_order"]
                    )
                    session.add(exp_type)
            
            # Commit additions
            try:
                session.commit()
            except:
                session.rollback()
            
            # Now get all
            query = session.query(ExpenseType)
            if not include_inactive:
                query = query.filter_by(is_active=True)
            types = query.all()
            
            return sorted([
                {
                    'id': t.id,
                    'name': t.name,
                    'description': t.description or '',
                    'sort_order': t.sort_order or 0,
                    'is_active': t.is_active
                } for t in types
            ], key=lambda x: x['sort_order'])

    # ========================================================================
    # GESTION DES DÉPENSES
    # ========================================================================
    
    def record_expense(self, expense_type_id: int, amount: float, currency_id: int, 
                      rate: float = 1.0, payment_type: str = "CASH", 
                      account_id: int = None, supplier_id: int = None,
                      container_id: int = None, license_id: int = None,
                      reference: str = "", notes: str = "",
                      date: datetime = None) -> Tuple[bool, str, Optional[Expense]]:
        """
        Enregistre une dépense réelle.
        """
        total_dzd = amount * rate
        
        with get_session() as session:
            try:
                # 1. Créer l'objet dépense
                expense = Expense(
                    expense_type_id=expense_type_id,
                    amount=amount,
                    currency_id=currency_id,
                    rate=rate,
                    total_dzd=total_dzd,
                    payment_type=payment_type,
                    account_id=account_id if payment_type == PAYMENT_TYPE_CASH else None,
                    supplier_id=supplier_id if payment_type == PAYMENT_TYPE_CREDIT else None,
                    container_id=container_id,
                    license_id=license_id,
                    reference=reference,
                    notes=notes,
                    date=date or datetime.now()
                )
                session.add(expense)
                session.flush()
                
                # 2. Gérer l'impact financier
                if payment_type == PAYMENT_TYPE_CASH:
                    if not account_id:
                        return False, "Compte requis pour paiement CASH", None
                    
                    # Débiter le compte de trésorerie
                    from modules.treasury.repository import AccountRepository
                    acc_repo = AccountRepository()
                    account = acc_repo.get_by_id(session, account_id)
                    if not account:
                        return False, "Compte introuvable", None
                    if account.balance < total_dzd:
                        from modules.settings.service import SettingsService
                        allow_negative = SettingsService().get_setting("allow_negative_treasury", "False") == "True"
                        if not allow_negative:
                            return False, "Solde insuffisant", None
                    
                    account.balance -= total_dzd
                    
                    # Créer la transaction de trésorerie
                    trans = Transaction(
                        account_id=account_id,
                        type=TRANSACTION_TYPE_DEBIT,
                        amount=total_dzd,
                        description=f"Dépense: {expense.expense_type.name if expense.expense_type else 'Frais'} #{expense.id}",
                        reference=reference,
                        date=datetime.now()
                    )
                    session.add(trans)
                else:
                    # CREDIT : Affecte le solde du fournisseur (dette)
                    if not supplier_id:
                        return False, "Fournisseur requis pour paiement CREDIT", None
                    
                    from modules.currency.repository import CurrencySupplierRepository
                    supp_repo = CurrencySupplierRepository()
                    supplier = supp_repo.get_by_id(session, supplier_id)
                    if not supplier:
                        return False, "Fournisseur introuvable", None
                        
                    supplier.balance += total_dzd
                
                # 3. NOUVEAU: Automatic commission logic for licenses (Jumerka)
                # If it's an expense type "Dédouanement" linked to a container
                if container_id:
                    exp_type = session.query(ExpenseType).get(expense_type_id)
                    if exp_type and "Dédouanement" in exp_type.name:
                        container = session.query(ContainerFile).get(container_id)
                        if container and container.license:
                            # Calculer la commission : % du montant de jumerka
                            commission = (total_dzd * container.license.commission_rate) / 100
                            if commission > 0:
                                container.license.supplier.balance += commission
                                # Optionnellement, mettre à jour container.commission_dzd
                                container.commission_dzd += commission
                
                session.commit()
                return True, "Dépense enregistrée avec succès", expense
            except Exception as e:
                session.rollback()
                return False, f"Erreur: {str(e)}", None

    def get_expense(self, expense_id: int):
        with get_session() as session:
            e = session.query(Expense).get(expense_id)
            if not e: return None
            data = {
                'id': e.id,
                'expense_type_id': e.expense_type_id,
                'amount': e.amount,
                'currency_id': e.currency_id,
                'rate': e.rate,
                'total_dzd': e.total_dzd,
                'payment_type': e.payment_type,
                'account_id': e.account_id,
                'container_id': e.container_id,
                'license_id': e.license_id,
                'reference': e.reference,
                'notes': e.notes,
                'date': e.date
            }
            return self._to_obj(data)

    def update_expense(self, expense_id: int, expense_type_id: int, amount: float, currency_id: int, 
                       rate: float = 1.0, payment_type: str = "CASH", 
                       account_id: int = None, supplier_id: int = None,
                       container_id: int = None, license_id: int = None,
                       reference: str = "", notes: str = "") -> Tuple[bool, str]:
        """Met à jour une dépense avec réversion des impacts financiers"""
        total_dzd = amount * rate
        with get_session() as session:
            try:
                expense = session.query(Expense).get(expense_id)
                if not expense: return False, "Dépense introuvable"

                # 1. RÉVERSION de l'ancien impact
                if expense.payment_type == PAYMENT_TYPE_CASH and expense.account_id:
                    # Ajouter l'ancien montant au compte
                    from modules.treasury.repository import AccountRepository
                    acc_repo = AccountRepository()
                    acc_repo.update_balance(session, expense.account_id, expense.total_dzd, False) # False = Re-Créditer (+)
                    
                    # Inactiver l'ancienne transaction
                    from core.models import Transaction
                    old_t = session.query(Transaction).filter_by(reference=expense.reference or f"EXP-{expense.id}").first()
                    # (Si on n'a pas de référence unique, on cherche par description ou on laisse ainsi)
                    if old_t: old_t.is_active = False

                # Réversion commission Jumerka
                if expense.container_id:
                    old_type = session.query(ExpenseType).get(expense.expense_type_id)
                    if old_type and "Dédouanement" in old_type.name:
                        container = session.query(ContainerFile).get(expense.container_id)
                        if container and container.license:
                            old_commission = (expense.total_dzd * container.license.commission_rate) / 100
                            container.license.supplier.balance -= old_commission
                            container.commission_dzd -= old_commission

                # 2. APPLICATION du nouvel impact
                if payment_type == PAYMENT_TYPE_CASH:
                    if not account_id: return False, "Compte requis"
                    from modules.treasury.repository import AccountRepository
                    acc_repo = AccountRepository()
                    new_acc = acc_repo.get_by_id(session, account_id)
                    if not new_acc:
                        return False, "Compte introuvable"
                    if new_acc.balance < total_dzd:
                        from modules.settings.service import SettingsService
                        allow_negative = SettingsService().get_setting("allow_negative_treasury", "False") == "True"
                        if not allow_negative:
                            return False, "Solde insuffisant"
                    
                    acc_repo.update_balance(session, account_id, total_dzd, True) # True = Débiter (-)
                    
                    # Créer nouvelle transaction
                    new_t = Transaction(
                        account_id=account_id,
                        type=TRANSACTION_TYPE_DEBIT,
                        amount=total_dzd,
                        description=f"Dépense (Modif): {reference or 'Frais'}",
                        reference=reference,
                        date=datetime.now()
                    )
                    session.add(new_t)

                # Nouvelle commission Jumerka
                if container_id:
                    new_type = session.query(ExpenseType).get(expense_type_id)
                    if new_type and "Dédouanement" in new_type.name:
                        container = session.query(ContainerFile).get(container_id)
                        if container and container.license:
                            new_commission = (total_dzd * container.license.commission_rate) / 100
                            container.license.supplier.balance += new_commission
                            container.commission_dzd += new_commission

                # 3. MISE À JOUR de l'objet dépense
                expense.expense_type_id = expense_type_id
                expense.amount = amount
                expense.currency_id = currency_id
                expense.rate = rate
                expense.total_dzd = total_dzd
                expense.payment_type = payment_type
                expense.account_id = account_id
                expense.container_id = container_id
                expense.license_id = license_id
                expense.reference = reference
                expense.notes = notes

                session.commit()
                return True, "Dépense mise à jour"
            except Exception as e:
                session.rollback()
                return False, f"Erreur: {str(e)}"

    def get_all_expenses(self, container_id: int = None, license_id: int = None, filter_status: str = "active") -> List:
        """Récupère les dépenses selon le statut (active, inactive, all)"""
        with get_session() as session:
            query = session.query(Expense)
            if filter_status == "active": query = query.filter_by(is_active=True)
            elif filter_status == "inactive": query = query.filter_by(is_active=False)
            
            if container_id: query = query.filter_by(container_id=container_id)
            if license_id: query = query.filter_by(license_id=license_id)
            
            expenses = query.order_by(Expense.date.desc()).all()
            
            # Formater pour la vue
            result = []
            for e in expenses:
                customer_name = e.customer.name if e.customer else "N/A"
                account_name = e.account.name if e.account else "N/A"
                data = {
                    'id': e.id,
                    'date': e.date,
                    'customer_name': customer_name,
                    'type_name': e.expense_type.name if e.expense_type else "Frais",
                    'amount': e.amount,
                    'currency_code': e.currency.code if e.currency else "??",
                    'total_dzd': e.total_dzd,
                    'account_name': account_name,
                    'payment_type': e.payment_type,
                    'linked_to': f"Conteneur {e.container.container_number}" if e.container else (f"Licence #{e.license_id}" if e.license_id else "Global"),
                    'reference': e.reference or "",
                    'notes': e.notes or "",
                    'is_active': e.is_active
                }
                result.append(self._to_obj(data))
            return result
    
    def delete_expense_type(self, type_id: int) -> Tuple[bool, str]:
        """Archive un type de dépense (Soft Delete)"""
        with get_session() as session:
            exp_type = session.query(ExpenseType).get(type_id)
            if not exp_type:
                return False, "Type introuvable"
            exp_type.is_active = False
            session.commit()
            return True, "Type archivé"

    def restore_expense_type(self, type_id: int) -> Tuple[bool, str]:
        """Restaure un type de dépense"""
        with get_session() as session:
            exp_type = session.query(ExpenseType).get(type_id)
            if not exp_type:
                return False, "Type introuvable"
            exp_type.is_active = True
            session.commit()
            return True, "Type restauré"

    def delete_expense(self, expense_id: int) -> Tuple[bool, str]:
        """Archive une dépense (Soft Delete)"""
        with get_session() as session:
            success = self.expense_repo.soft_delete(session, expense_id)
            session.commit()
            return success, "Dépense archivée" if success else "Échec"

    def restore_expense(self, expense_id: int) -> Tuple[bool, str]:
        """Restaure une dépense archivée"""
        with get_session() as session:
            success = self.expense_repo.restore(session, expense_id)
            session.commit()
            return success, "Dépense restaurée" if success else "Échec"

    def record_expense_split_by_license(self, license_id: int, expense_type_id: int,
                                        total_amount: float, currency_id: int, rate: float = 1.0,
                                        payment_type: str = "CASH", account_id: int = None,
                                        supplier_id: int = None, reference: str = "",
                                        notes: str = "", date: datetime = None) -> Tuple[bool, str, int]:
        """
        Enregistre une dépense sur une licence (facture) et la répartit
        équitablement sur toutes ses conteneurs actifs.
        Retourne (success, message, nb_containers).
        """
        with get_session() as session:
            try:
                lic = session.query(ImportLicense).get(license_id)
                if not lic:
                    return False, "Licence introuvable", 0

                containers = session.query(ContainerFile).filter_by(
                    license_id=license_id, is_active=True
                ).all()
                if not containers:
                    return False, "Aucune conteneur actif sur cette licence", 0

                nb = len(containers)
                amount_per = total_amount / nb
                total_dzd_per = amount_per * rate
                total_dzd = total_amount * rate

                # Vérifier solde si CASH
                if payment_type == PAYMENT_TYPE_CASH:
                    if not account_id:
                        return False, "Compte requis pour paiement CASH", 0
                    from modules.treasury.repository import AccountRepository
                    acc_repo = AccountRepository()
                    account = acc_repo.get_by_id(session, account_id)
                    if not account:
                        return False, "Compte introuvable", 0
                    if account.balance < total_dzd:
                        from modules.settings.service import SettingsService
                        allow_neg = SettingsService().get_setting("allow_negative_treasury", "False") == "True"
                        if not allow_neg:
                            return False, "Solde insuffisant", 0
                    account.balance -= total_dzd
                    # Transaction trésorerie globale
                    trans = Transaction(
                        account_id=account_id,
                        type=TRANSACTION_TYPE_DEBIT,
                        amount=total_dzd,
                        description=f"Dépense répartie Licence #{license_id} ({nb} conteneurs)",
                        reference=reference,
                        date=date or datetime.now()
                    )
                    session.add(trans)
                else:
                    if not supplier_id:
                        return False, "Fournisseur requis pour paiement CREDIT", 0
                    from modules.currency.repository import CurrencySupplierRepository
                    supp_repo = CurrencySupplierRepository()
                    supplier = supp_repo.get_by_id(session, supplier_id)
                    if not supplier:
                        return False, "Fournisseur introuvable", 0
                    supplier.balance += total_dzd

                # Créer une dépense par conteneur
                for container in containers:
                    exp = Expense(
                        expense_type_id=expense_type_id,
                        amount=amount_per,
                        currency_id=currency_id,
                        rate=rate,
                        total_dzd=total_dzd_per,
                        payment_type=payment_type,
                        account_id=account_id if payment_type == PAYMENT_TYPE_CASH else None,
                        supplier_id=supplier_id if payment_type == PAYMENT_TYPE_CREDIT else None,
                        container_id=container.id,
                        license_id=license_id,
                        reference=reference,
                        notes=f"[Réparti {nb} cont.] {notes}".strip(),
                        date=date or datetime.now()
                    )
                    session.add(exp)

                session.commit()
                return True, f"Dépense répartie sur {nb} conteneur(s)", nb
            except Exception as e:
                session.rollback()
                return False, f"Erreur: {str(e)}", 0

    def get_container_costs_summary(self, container_id: int) -> dict:
        """
        Retourne le résumé des coûts directs d'un conteneur groupés par type.
        {type_name: total_dzd, ..., '_total': total_dzd}
        """
        with get_session() as session:
            expenses = session.query(Expense).filter_by(
                container_id=container_id, is_active=True
            ).all()
            summary = {}
            for e in expenses:
                type_name = e.expense_type.name if e.expense_type else "Autres"
                summary[type_name] = summary.get(type_name, 0) + (e.total_dzd or 0)
            summary['_total'] = sum(v for k, v in summary.items() if not k.startswith('_'))
            return summary

    def get_all_containers_costs(self) -> dict:
        """
        Retourne {container_id: costs_summary} pour tous les conteneurs actifs.
        Utilisé par ContainerCostsTab pour éviter N+1 queries.
        """
        with get_session() as session:
            expenses = session.query(Expense).filter_by(is_active=True).filter(
                Expense.container_id.isnot(None)
            ).all()
            result = {}
            for e in expenses:
                cid = e.container_id
                if cid not in result:
                    result[cid] = {}
                type_name = e.expense_type.name if e.expense_type else "Autres"
                result[cid][type_name] = result[cid].get(type_name, 0) + (e.total_dzd or 0)
            for cid in result:
                result[cid]['_total'] = sum(v for k, v in result[cid].items() if not k.startswith('_'))
            return result

    def _to_obj(self, data: dict):
        class DataObj:
            pass
        obj = DataObj()
        for k, v in data.items():
            setattr(obj, k, v)
        return obj
