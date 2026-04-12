"""
Service logistique pour la gestion des licences et conteneurs
"""
from typing import List, Tuple, Optional
from datetime import datetime

from core.database import get_session
from core.models import (
    ImportLicense, ContainerFile, ContainerExpense
)
from utils.constants import (
    TRANSACTION_TYPE_DEBIT, PAYMENT_TYPE_CASH
)
from .repository import LicenseRepository, ContainerRepository, ExpenseRepository
from modules.currency.repository import CurrencySupplierRepository, CurrencyRepository
from modules.treasury.repository import AccountRepository

class LogisticsService:
    def __init__(self):
        self.license_repo = LicenseRepository()
        self.container_repo = ContainerRepository()
        self.expense_repo = ExpenseRepository()
        self.supplier_repo = CurrencySupplierRepository()
        self.currency_repo = CurrencyRepository()
        self.account_repo = AccountRepository()

    def create_license(self, supplier_id: int, total_usd: float, total_dzd: float, 
                       commission_rate: float, license_type: str = "",
                       notes: str = "", date: datetime = None) -> Tuple[bool, str, Optional[ImportLicense]]:
        """
        Achète une licence d'importation (Opération documentaire).
        """
        with get_session() as session:
            try:
                # 1. Vérifier le fournisseur
                supplier = self.supplier_repo.get_by_id(session, supplier_id)
                if not supplier:
                    return False, "Fournisseur non trouvé", None

                # 2. Chercher la devise USD par défaut
                usd = session.query(self.currency_repo.model).filter_by(code="USD").first()
                if not usd:
                    return False, "Devise USD non trouvée", None

                # Calculer le taux interne pour référence
                rate = total_dzd / total_usd if total_usd > 0 else 0

                # 3. Créer la licence (Sans impact financier immédiat)
                license = ImportLicense(
                    supplier_id=supplier_id,
                    currency_id=usd.id,
                    total_usd=total_usd,
                    rate=rate,
                    total_dzd=total_dzd,
                    commission_rate=commission_rate,
                    license_type=license_type,
                    is_debt_generated=False,
                    notes=notes,
                    date=date if date else datetime.now()
                )
                session.add(license)
                session.commit()
                return True, f"Licence #{license.id} enregistrée ({total_usd}$)", license
            except Exception as e:
                session.rollback()
                return False, f"Erreur: {str(e)}"

    def get_all_licenses(self, filter_status: str = "active") -> List[dict]:
        """Récupère toutes les licences avec filtre de statut"""
        with get_session() as session:
            query = session.query(ImportLicense)
            if filter_status == "active":
                query = query.filter_by(is_active=True)
            elif filter_status == "inactive":
                query = query.filter_by(is_active=False)
            licenses = query.order_by(ImportLicense.id.desc()).all()

            result = []
            for lic in licenses:
                supplier_name = lic.supplier.name if lic.supplier else "N/A"
                result.append({
                    "id": lic.id,
                    "date": lic.date,
                    "supplier_name": supplier_name,
                    "license_type": lic.license_type or "",
                    "total_usd": lic.total_usd,
                    "used_usd": lic.used_usd or 0,
                    "remaining_usd": lic.total_usd - (lic.used_usd or 0),
                    "total_dzd": lic.total_dzd or 0,
                    "commission_rate": lic.commission_rate or 30.0,
                    "notes": lic.notes or "",
                    "is_active": lic.is_active,
                    "total_domiciliations": lic.total_domiciliations or 0.0,
                    "total_taxes": lic.total_taxes or 0.0,
                    "total_versements": lic.total_versements or 0.0,
                    "total_du": lic.total_du or 0.0,
                })
            return result

    def update_license(self, license_id: int, **kwargs) -> Tuple[bool, str]:
        """Met à jour une licence existante"""
        with get_session() as session:
            try:
                lic = session.query(ImportLicense).get(license_id)
                if not lic:
                    return False, "Licence introuvable"

                for key, value in kwargs.items():
                    if hasattr(lic, key) and value is not None:
                        setattr(lic, key, value)

                session.commit()
                return True, "Licence mise à jour"
            except Exception as e:
                session.rollback()
                return False, f"Erreur: {str(e)}"

    def delete_license(self, license_id: int) -> Tuple[bool, str]:
        """Archive une licence"""
        with get_session() as session:
            try:
                lic = session.query(ImportLicense).get(license_id)
                if not lic:
                    return False, "Licence introuvable"
                lic.is_active = False
                session.commit()
                return True, "Licence archivée"
            except Exception as e:
                session.rollback()
                return False, f"Erreur: {str(e)}"

    def restore_license(self, license_id: int) -> Tuple[bool, str]:
        """Restaure une licence archivée"""
        with get_session() as session:
            try:
                lic = session.query(ImportLicense).get(license_id)
                if not lic:
                    return False, "Licence introuvable"
                lic.is_active = True
                session.commit()
                return True, "Licence restaurée"
            except Exception as e:
                session.rollback()
                return False, f"Erreur: {str(e)}"

    def update_shipment_with_goods(self, container_id: int, data: dict) -> Tuple[bool, str]:
        """
        Modifie une facture (conteneur) avec ses marchandises.
        data = {
            "shipment": {bill_number, agent_id, license_id, transfer_amount_usd, ...},
            "containers": [{"number": "...", "goods": [...]}]
        }
        """
        shipment = data["shipment"]
        containers = data["containers"]

        with get_session() as session:
            try:
                from core.models import ContainerFile, CustomerGoods

                # 1. Recuperer le conteneur existant
                container = self.container_repo.get_by_id(session, container_id)
                if not container:
                    return False, "Conteneur introuvable"

                # 2. Calculer le total des marchandises
                total_usd = shipment["transfer_amount_usd"]
                cont = containers[0] if containers else {"number": container.container_number, "goods": []}
                total_cbm = sum(g["cbm"] for g in cont["goods"])
                total_cartons = sum(g["qty"] for g in cont["goods"])

                # 3. Mettre a jour le conteneur
                container.container_number = cont["number"]
                container.bill_number = shipment["bill_number"]
                container.invoice_number = shipment.get("invoice_number", "")
                container.shipping_supplier_id = shipment.get("agent_id")
                container.used_usd_amount = total_usd
                container.cbm = total_cbm
                container.cartons = total_cartons
                container.transitaire = shipment.get("transitaire", "")
                container.discharge_port = shipment.get("port", "")
                container.taux = shipment.get("exchange_rate", 0)
                container.taux_expedition = shipment.get("shipment_rate", 0)
                container.equivalent_dzd = shipment.get("equivalent_dzd", 0)
                container.equivalent_expedition = shipment.get("equivalent_expedition", 0)
                if shipment.get("date"):
                    container.shipping_date = shipment["date"]

                # 4. Supprimer les anciennes marchandises
                session.query(CustomerGoods).filter_by(container_id=container_id).delete()
                session.flush()

                # 5. Creer les nouvelles marchandises
                for g in cont["goods"]:
                    goods = CustomerGoods(
                        customer_id=g["customer_id"],
                        container_id=container_id,
                        goods_type=g["goods_type"],
                        cartons=g["qty"],
                        cbm=g["cbm"],
                        cbm_price_usd=g["price"],
                        discount_usd=g["discount"],
                        date=datetime.now()
                    )
                    session.add(goods)

                session.commit()
                return True, f"Facture mise a jour: {len(cont['goods'])} marchandise(s)"

            except Exception as e:
                session.rollback()
                return False, f"Erreur: {str(e)}"

    def update_container_file(self, container_id: int, container_number: str, 
                             used_usd: float, shipping_supplier_id: int = None,
                             bill_number: str = "", products_type: str = "",
                             discharge_port: str = "", shipping_date: datetime = None,
                             expected_arrival_date: datetime = None,
                             invoice_number: str = "", cbm: float = 0, 
                             cartons: int = 0, transitaire: str = "",
                             notes: str = "") -> Tuple[bool, str]:
        """
        Met à jour un dossier conteneur et ajuste les données financières.
        """
        with get_session() as session:
            try:
                container = self.container_repo.get_by_id(session, container_id)
                if not container: return False, "Dossier non trouvé"
                
                lic = container.license
                
                # Vérifier solde
                diff = used_usd - container.used_usd_amount
                available = lic.total_usd - lic.used_usd
                if diff > available:
                     return False, f"Solde insuffisant. Disponible: {available}$"
                
                # Ajustement Licence
                lic.used_usd += diff
                
                # Ajustement Dette Fournisseur
                if not lic.is_debt_generated:
                    old_val = (container.used_usd_amount / lic.total_usd) * lic.total_dzd if lic.total_usd > 0 else 0
                    new_val = (used_usd / lic.total_usd) * lic.total_dzd if lic.total_usd > 0 else 0
                    lic.supplier.balance += (new_val - old_val)
                
                # Mise à jour champs
                container.container_number = container_number
                container.shipping_supplier_id = shipping_supplier_id
                container.bill_number = bill_number
                container.invoice_number = invoice_number
                container.products_type = products_type
                container.used_usd_amount = used_usd
                container.cbm = cbm
                container.cartons = cartons
                container.transitaire = transitaire
                container.discharge_port = discharge_port
                container.shipping_date = shipping_date
                container.expected_arrival_date = expected_arrival_date
                container.notes = notes
                
                session.commit()
                return True, "Dossier mis à jour"
            except Exception as e:
                session.rollback()
                return False, str(e)

    def update_customs_data(self, container_id: int, customs_value: float) -> Tuple[bool, str]:
        """
        Met à jour la valeur de jumerka et calcule la commission.
        """
        with get_session() as session:
            try:
                container = self.container_repo.get_by_id(session, container_id)
                if not container:
                    return False, "Dossier non trouvé"
                
                container.customs_value_dzd = customs_value
                # Commission = Customs Value * Commission Rate / 100
                old_commission = container.commission_dzd
                new_commission = (customs_value * container.license.commission_rate) / 100
                container.commission_dzd = new_commission
                
                # Ajouter la différence de commission à la dette du fournisseur de licence
                commission_diff = new_commission - old_commission
                if commission_diff != 0:
                    container.license.supplier.balance += commission_diff
                
                session.commit()
                return True, f"Données jumerka mises à jour (Commission: {new_commission:,.2f} DA)"
            except Exception as e:
                session.rollback()
                return False, str(e)

    def get_all_containers(self, filter_status: str = "active") -> List[dict]:
        """Récupère tous les dossiers conteneurs selon le statut (active, inactive, all)"""
        with get_session() as session:
            query = session.query(self.container_repo.model)
            if filter_status == "active": query = query.filter_by(is_active=True)
            elif filter_status == "inactive": query = query.filter_by(is_active=False)
            
            containers = query.order_by(self.container_repo.model.id.desc()).all()
            return [
                {
                    'id': c.id,
                    'container_number': c.container_number,
                    'bill_number': c.bill_number or "N/A",
                    'invoice_number': c.invoice_number or "",
                    'license_id': c.license_id,
                    'supplier_name': c.license.supplier.name if c.license.supplier else "N/A",
                    'shipping_supplier_id': c.shipping_supplier_id,
                    'shipping_supplier_name': c.shipping_supplier.name if c.shipping_supplier else "N/A",
                    'used_usd_amount': c.used_usd_amount,
                    'cbm': c.cbm,
                    'cartons': c.cartons,
                    'transitaire': c.transitaire or "",
                    'customs_value_dzd': c.customs_value_dzd,
                    'commission_dzd': c.commission_dzd,
                    'status': c.status,
                    'date_opened': c.date_opened,
                    'discharge_port': c.discharge_port or "N/A",
                    'shipping_date': c.shipping_date,
                    'expected_arrival_date': c.expected_arrival_date,
                    'products_type': c.products_type or "N/A",
                    'is_active': c.is_active,
                    'notes': c.notes or "",
                    'shipping_cost': c.shipping_cost or 0.0,
                    'licence_fee': c.licence_fee or 0.0,
                    'tax_amount': c.tax_amount or 0.0,
                    'charge_percentage': c.charge_percentage or 0.0,
                    'charge_da': c.charge_da or 0.0,
                    'charge_port': c.charge_port or 0.0,
                    'surestarie': c.surestarie or 0.0,
                } for c in containers
            ]

    def delete_container(self, container_id: int) -> Tuple[bool, str]:
        """Archive un dossier conteneur (Soft Delete)"""
        with get_session() as session:
            success = self.container_repo.soft_delete(session, container_id)
            session.commit()
            return success, "Dossier archivé" if success else "Échec de l'archivage"

    def restore_container(self, container_id: int) -> Tuple[bool, str]:
        """Restaure un dossier conteneur archivé"""
        with get_session() as session:
            success = self.container_repo.restore(session, container_id)
            session.commit()
            return success, "Dossier restauré" if success else "Échec de la restauration"

    # [FIX] 2026-03-31: Suppression du code dupliqué (get_all_containers)
    # L'ancienne version utilisait 'include_inactive' et était morte car non appelée.
    # La version active (ligne 293) utilise 'filter_status' et fonctionne correctement.

    def create_shipment_with_goods(self, data: dict) -> Tuple[bool, str]:
        """
        Crée une shavنة avec conteneurs et marchandises en une seule opération.
        data = {
            "shipment": {date, bill_number, agent_id, license_id, transfer_amount_usd, ...},
            "containers": [{"number": "MSKU", "goods": [{"customer_id", "goods_type", "cbm", ...}]}]
        }
        """
        shipment = data["shipment"]
        containers = data["containers"]

        with get_session() as session:
            try:
                from core.models import ContainerFile, CustomerGoods

                # 1. Verifier la licence
                lic = self.license_repo.get_by_id(session, shipment["license_id"])
                if not lic:
                    return False, "Licence introuvable"

                total_usd = shipment["transfer_amount_usd"]
                if (lic.total_usd - lic.used_usd) < total_usd:
                    return False, f"Solde insuffisant. Restant: {lic.total_usd - lic.used_usd}$"

                # 2. Creer les conteneurs
                container_ids = []
                amount_per_container = total_usd / len(containers) if containers else 0

                for cont in containers:
                    total_cbm = sum(g["cbm"] for g in cont["goods"])
                    total_cartons = sum(g["qty"] for g in cont["goods"])

                    container = ContainerFile(
                        license_id=shipment["license_id"],
                        shipping_supplier_id=shipment.get("agent_id"),
                        container_number=cont["number"],
                        bill_number=shipment["bill_number"],
                        invoice_number=shipment.get("invoice_number", ""),
                        products_type="",
                        used_usd_amount=amount_per_container,
                        cbm=total_cbm,
                        cartons=total_cartons,
                        transitaire=shipment.get("transitaire", ""),
                        discharge_port=shipment.get("port", ""),
                        shipping_date=shipment["date"],
                        taux=shipment.get("exchange_rate", 0),
                        taux_expedition=shipment.get("shipment_rate", 0),
                        equivalent_dzd=shipment.get("equivalent_dzd", 0),
                        equivalent_expedition=shipment.get("equivalent_expedition", 0),
                        status="OPEN",
                        date_opened=datetime.now()
                    )
                    session.add(container)
                    session.flush()
                    container_ids.append(container.id)

                    # 3. Creer les marchandises pour ce conteneur
                    for g in cont["goods"]:
                        goods = CustomerGoods(
                            customer_id=g["customer_id"],
                            container_id=container.id,
                            goods_type=g["goods_type"],
                            cartons=g["qty"],
                            cbm=g["cbm"],
                            cbm_price_dzd=g["price"],
                            cbm_price_usd=g.get("price_usd", 0),
                            discount=g["discount"],
                            discount_usd=g.get("discount_usd", 0),
                            date=datetime.now()
                        )
                        session.add(goods)

                # 4. Mettre a jour la licence
                lic.used_usd += total_usd

                session.commit()
                return True, f"Facture creee: {len(containers)} conteneur(s), {sum(len(c['goods']) for c in containers)} marchandise(s)"
            except Exception as e:
                session.rollback()
                return False, f"Erreur: {str(e)}"

    def update_container_warehouse(self, container_id: int, warehouse_id: int, status: str):
        """Met a jour le statut du conteneur dans le warehouse"""
        try:
            with get_session() as session:
                container = self.container_repo.get_by_id(session, container_id)
                if not container:
                    return False, "Conteneur non trouve"
                
                # Store warehouse info in notes for now
                current_notes = container.notes or ""
                container.notes = f"{current_notes}|Warehouse:{warehouse_id}:{status}"
                
                session.commit()
                return True, "Statut mis a jour"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    # ========================================================================
    # FRAIS INDIRECTS (Indirect Expenses)
    # ========================================================================

    def create_indirect_expense(self, expense_type_id: int, account_id: int,
                                amount: float, currency_id: int, rate: float = 1.0,
                                commission: float = 0.0, lot_id: int = None,
                                reference: str = "", notes: str = "",
                                date: datetime = None) -> Tuple[bool, str, Optional[int]]:
        """
        Crée une dépense indirecte et déduit le montant de la trésorerie.
        Si devise étrangère: déduit du LOT sélectionné.
        """
        from modules.currency.repository import CurrencyPurchaseRepository
        from modules.treasury.repository import TransactionRepository
        from utils.constants import TRANSACTION_TYPE_DEBIT

        is_valid, error = validate_amount(amount)
        if not is_valid:
            return False, error, None

        try:
            with get_session() as session:
                total_dzd = (amount * rate) + commission

                # 1. Créer la dépense
                expense = Expense(
                    expense_type_id=expense_type_id,
                    account_id=account_id,
                    amount=amount,
                    currency_id=currency_id,
                    rate=rate,
                    total_dzd=total_dzd,
                    commission=commission,
                    lot_id=lot_id,
                    payment_type="CASH",
                    date=date or datetime.now(),
                    reference=reference,
                    notes=notes,
                    is_active=True
                )
                session.add(expense)
                session.flush()

                # 2. Débiter le compte trésorerie
                self.account_repo.update_balance(session, account_id, total_dzd, True)

                # Créer la transaction DEBIT
                trans_repo = TransactionRepository()
                trans_repo.create(
                    session,
                    account_id=account_id,
                    type=TRANSACTION_TYPE_DEBIT,
                    amount=total_dzd,
                    description=f"Frais Indirect: {expense.expense_type.name if expense.expense_type else 'N/A'}",
                    reference=reference or f"EXP-{expense.id}",
                    date=date or datetime.now()
                )

                # 3. Si LOT sélectionné (devise étrangère), consommer du LOT
                if lot_id and lot_id > 0:
                    purchase_repo = CurrencyPurchaseRepository()
                    lot = purchase_repo.get_by_id(session, lot_id)
                    if lot:
                        consumed = getattr(lot, 'consumed', 0.0)
                        lot.consumed = consumed + amount

                session.commit()
                return True, "Frais indirect enregistré avec succès", expense.id
        except Exception as e:
            return False, f"Erreur: {str(e)}", None

    def get_all_indirect_expenses(self, limit: int = 200, filter_status: str = "active") -> List[dict]:
        """Récupère tous les frais indirects"""
        with get_session() as session:
            query = session.query(Expense).filter(
                Expense.container_id == None,
                Expense.license_id == None
            )
            if filter_status == "active":
                query = query.filter(Expense.is_active == True)
            elif filter_status == "inactive":
                query = query.filter(Expense.is_active == False)

            expenses = query.order_by(Expense.date.desc()).limit(limit).all()
            return [
                {
                    'id': e.id,
                    'date': e.date,
                    'type_name': e.expense_type.name if e.expense_type else "N/A",
                    'account_name': e.account.name if e.account else "N/A",
                    'amount': e.amount,
                    'currency_code': e.currency.code if e.currency else "DA",
                    'rate': e.rate,
                    'commission': getattr(e, 'commission', 0.0),
                    'total_dzd': e.total_dzd,
                    'lot_info': f"LOT #{e.lot.id}" if e.lot else "",
                    'reference': e.reference or "",
                    'notes': e.notes or "",
                    'is_active': e.is_active
                } for e in expenses
            ]

    def delete_indirect_expense(self, expense_id: int) -> Tuple[bool, str]:
        """Annule un frais indirect et réajuste les soldes"""
        try:
            with get_session() as session:
                expense = self.expense_repo.get_by_id(session, expense_id)
                if not expense:
                    return False, "Frais introuvable"
                if not expense.is_active:
                    return False, "Déjà annulé"

                # Réajuster le compte
                self.account_repo.update_balance(session, expense.account_id, expense.total_dzd, False)

                # Réajuster le LOT si utilisé
                if expense.lot_id:
                    from modules.currency.repository import CurrencyPurchaseRepository
                    purchase_repo = CurrencyPurchaseRepository()
                    lot = purchase_repo.get_by_id(session, expense.lot_id)
                    if lot:
                        consumed = getattr(lot, 'consumed', 0.0)
                        lot.consumed = max(0, consumed - expense.amount)

                expense.is_active = False
                session.flush()
                return True, "Frais annulé avec succès"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def restore_indirect_expense(self, expense_id: int) -> Tuple[bool, str]:
        """Restaure un frais indirect annulé"""
        try:
            with get_session() as session:
                expense = self.expense_repo.get_by_id(session, expense_id)
                if not expense:
                    return False, "Frais introuvable"
                if expense.is_active:
                    return False, "Déjà actif"

                # Réappliquer le débit
                self.account_repo.update_balance(session, expense.account_id, expense.total_dzd, True)

                # Réappliquer la consommation du LOT
                if expense.lot_id:
                    from modules.currency.repository import CurrencyPurchaseRepository
                    purchase_repo = CurrencyPurchaseRepository()
                    lot = purchase_repo.get_by_id(session, expense.lot_id)
                    if lot:
                        consumed = getattr(lot, 'consumed', 0.0)
                        lot.consumed = consumed + expense.amount

                expense.is_active = True
                session.flush()
                return True, "Frais restauré avec succès"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def get_container_goods(self, container_id: int) -> List[dict]:
        """Recupere les marchandises d'un conteneur"""
        from core.models import CustomerGoods
        with get_session() as session:
            goods = session.query(CustomerGoods).filter(
                CustomerGoods.container_id == container_id,
                CustomerGoods.is_active == True
            ).all()
            
            # Get container exchange rate
            container = self.container_repo.get_by_id(session, container_id)
            exchange_rate = container.taux if container and container.taux else 150
            
            return [
                {
                    'id': g.id,
                    'customer_id': g.customer_id,
                    'customer_name': g.customer.name if g.customer else "N/A",
                    'goods_type': g.goods_type,
                    'cartons': g.cartons,
                    'cbm': g.cbm,
                    'cbm_price_dzd': g.cbm_price_dzd or 0,
                    'cbm_price_usd': g.cbm_price_usd,
                    'discount_dzd': g.discount or 0,
                    'discount_usd': g.discount_usd or 0,
                    'exchange_rate': exchange_rate
                } for g in goods
            ]

    def update_container_warehouse_info(self, container_id: int, warehouse_id: int, 
                                        status: str, received_data: list = None) -> Tuple[bool, str]:
        """Met a jour le statut du conteneur dans le warehouse avec les donnees de reception"""
        try:
            import json
            with get_session() as session:
                container = self.container_repo.get_by_id(session, container_id)
                if not container:
                    return False, "Conteneur non trouve"
                
                container.warehouse_id = warehouse_id
                container.warehouse_status = status
                container.warehouse_received_date = datetime.now()
                
                if received_data:
                    container.warehouse_notes = json.dumps(received_data)
                
                session.commit()
                return True, "Statut mis a jour"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    # ========================================================================
    # FRAIS INDIRECTS (Indirect Expenses)
    # ========================================================================

    def create_indirect_expense(self, expense_type_id: int, account_id: int,
                                amount: float, currency_id: int, rate: float = 1.0,
                                commission: float = 0.0, lot_id: int = None,
                                reference: str = "", notes: str = "",
                                date: datetime = None) -> Tuple[bool, str, Optional[int]]:
        """
        Crée une dépense indirecte et déduit le montant de la trésorerie.
        Si devise étrangère: déduit du LOT sélectionné.
        """
        from modules.currency.repository import CurrencyPurchaseRepository
        from modules.treasury.repository import TransactionRepository
        from utils.constants import TRANSACTION_TYPE_DEBIT

        is_valid, error = validate_amount(amount)
        if not is_valid:
            return False, error, None

        try:
            with get_session() as session:
                total_dzd = (amount * rate) + commission

                # 1. Créer la dépense
                expense = Expense(
                    expense_type_id=expense_type_id,
                    account_id=account_id,
                    amount=amount,
                    currency_id=currency_id,
                    rate=rate,
                    total_dzd=total_dzd,
                    commission=commission,
                    lot_id=lot_id,
                    payment_type="CASH",
                    date=date or datetime.now(),
                    reference=reference,
                    notes=notes,
                    is_active=True
                )
                session.add(expense)
                session.flush()

                # 2. Débiter le compte trésorerie
                self.account_repo.update_balance(session, account_id, total_dzd, True)

                # Créer la transaction DEBIT
                trans_repo = TransactionRepository()
                trans_repo.create(
                    session,
                    account_id=account_id,
                    type=TRANSACTION_TYPE_DEBIT,
                    amount=total_dzd,
                    description=f"Frais Indirect: {expense.expense_type.name if expense.expense_type else 'N/A'}",
                    reference=reference or f"EXP-{expense.id}",
                    date=date or datetime.now()
                )

                # 3. Si LOT sélectionné (devise étrangère), consommer du LOT
                if lot_id and lot_id > 0:
                    purchase_repo = CurrencyPurchaseRepository()
                    lot = purchase_repo.get_by_id(session, lot_id)
                    if lot:
                        consumed = getattr(lot, 'consumed', 0.0)
                        lot.consumed = consumed + amount

                session.commit()
                return True, "Frais indirect enregistré avec succès", expense.id
        except Exception as e:
            return False, f"Erreur: {str(e)}", None

    def get_all_indirect_expenses(self, limit: int = 200, filter_status: str = "active") -> List[dict]:
        """Récupère tous les frais indirects"""
        with get_session() as session:
            query = session.query(Expense).filter(
                Expense.container_id == None,
                Expense.license_id == None
            )
            if filter_status == "active":
                query = query.filter(Expense.is_active == True)
            elif filter_status == "inactive":
                query = query.filter(Expense.is_active == False)

            expenses = query.order_by(Expense.date.desc()).limit(limit).all()
            return [
                {
                    'id': e.id,
                    'date': e.date,
                    'type_name': e.expense_type.name if e.expense_type else "N/A",
                    'account_name': e.account.name if e.account else "N/A",
                    'amount': e.amount,
                    'currency_code': e.currency.code if e.currency else "DA",
                    'rate': e.rate,
                    'commission': getattr(e, 'commission', 0.0),
                    'total_dzd': e.total_dzd,
                    'lot_info': f"LOT #{e.lot.id}" if e.lot else "",
                    'reference': e.reference or "",
                    'notes': e.notes or "",
                    'is_active': e.is_active
                } for e in expenses
            ]

    def delete_indirect_expense(self, expense_id: int) -> Tuple[bool, str]:
        """Annule un frais indirect et réajuste les soldes"""
        try:
            with get_session() as session:
                expense = self.expense_repo.get_by_id(session, expense_id)
                if not expense:
                    return False, "Frais introuvable"
                if not expense.is_active:
                    return False, "Déjà annulé"

                # Réajuster le compte
                self.account_repo.update_balance(session, expense.account_id, expense.total_dzd, False)

                # Réajuster le LOT si utilisé
                if expense.lot_id:
                    from modules.currency.repository import CurrencyPurchaseRepository
                    purchase_repo = CurrencyPurchaseRepository()
                    lot = purchase_repo.get_by_id(session, expense.lot_id)
                    if lot:
                        consumed = getattr(lot, 'consumed', 0.0)
                        lot.consumed = max(0, consumed - expense.amount)

                expense.is_active = False
                session.flush()
                return True, "Frais annulé avec succès"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def restore_indirect_expense(self, expense_id: int) -> Tuple[bool, str]:
        """Restaure un frais indirect annulé"""
        try:
            with get_session() as session:
                expense = self.expense_repo.get_by_id(session, expense_id)
                if not expense:
                    return False, "Frais introuvable"
                if expense.is_active:
                    return False, "Déjà actif"

                # Réappliquer le débit
                self.account_repo.update_balance(session, expense.account_id, expense.total_dzd, True)

                # Réappliquer la consommation du LOT
                if expense.lot_id:
                    from modules.currency.repository import CurrencyPurchaseRepository
                    purchase_repo = CurrencyPurchaseRepository()
                    lot = purchase_repo.get_by_id(session, expense.lot_id)
                    if lot:
                        consumed = getattr(lot, 'consumed', 0.0)
                        lot.consumed = consumed + expense.amount

                expense.is_active = True
                session.flush()
                return True, "Frais restauré avec succès"
        except Exception as e:
            return False, f"Erreur: {str(e)}"
