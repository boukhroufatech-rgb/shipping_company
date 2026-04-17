"""
Service pour le module Gestion des Devises
"""
from typing import Optional, Tuple, List
from datetime import datetime

from core.services import BaseService
from core.database import get_session
from .repository import (
    CurrencyRepository, ExchangeRateRepository, CurrencySupplierRepository,
    CurrencyPurchaseRepository, SupplierPaymentRepository
)
from .world_sync import WorldCurrencySyncEngine
from modules.treasury.repository import AccountRepository, TransactionRepository
from utils.constants import (
    PAYMENT_TYPE_CASH, PAYMENT_TYPE_CREDIT,
    TRANSACTION_TYPE_DEBIT, TRANSACTION_TYPE_CREDIT,
    DEFAULT_CURRENCY_CODE,
    ERROR_CANNOT_DELETE_DEFAULT_CURRENCY,
    SUCCESS_CURRENCY_CREATED, SUCCESS_OPERATION_CREATED,
    SUPPLIER_TYPE_CURRENCY, SUPPLIER_TYPE_LICENSE, SUPPLIER_TYPE_SHIPPING
)
from utils.validators import validate_amount, validate_required_field, validate_currency_code
from utils.logger import log_error


class CurrencyService(BaseService):
    """Service pour la gestion des devises"""
    
    def __init__(self):
        self.currency_repo = CurrencyRepository()
        self.rate_repo = ExchangeRateRepository()
        self.supplier_repo = CurrencySupplierRepository()
        self.purchase_repo = CurrencyPurchaseRepository()
        self.payment_repo = SupplierPaymentRepository()
        self.account_repo = AccountRepository()
        self.transaction_repo = TransactionRepository()
        self.sync_engine = WorldCurrencySyncEngine(self.currency_repo)
    
    # ========================================================================
    # GESTION DES DEVISES
    # ========================================================================
    
    def create_currency(self, code: str, name: str, symbol: str, country: str = None) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Crée une nouvelle devise et synchronise son compte de trésorerie (Équation de Synchronisation).
        """
        # Validation
        is_valid, error = validate_currency_code(code)
        if not is_valid:
            return False, error, None
        
        is_valid, error = validate_required_field(name, "Nom de la devise")
        if not is_valid:
            return False, error, None
        
        try:
            with get_session() as session:
                # Vérifier si le code existe déjà
                existing = self.currency_repo.get_by_code(session, code)
                if existing:
                    if existing.is_active:
                        return False, "Cette devise existe déjà", None
                    else:
                        # Réactiver si elle était désactivée
                        existing.is_active = True
                        currency = existing
                else:
                    # Créer la devise
                    currency = self.currency_repo.create(
                        session,
                        code=code.upper(),
                        name=name,
                        symbol=symbol,
                        country=country,
                        is_default=(code.upper() == DEFAULT_CURRENCY_CODE),
                        is_deletable=(code.upper() != DEFAULT_CURRENCY_CODE),
                        is_active=True
                    )
                
                # Equation de Synchronisation: Création auto d'une caisse devise
                if currency.code != DEFAULT_CURRENCY_CODE:
                    account_code = f"CAISSE_{currency.code}"
                    existing_acc = self.account_repo.get_by_code(session, account_code)
                    if not existing_acc:
                        self.account_repo.create(
                            session, 
                            name=f"Caisse {currency.code}", 
                            code=account_code,
                            account_type="CAISSE", 
                            currency_id=currency.id, 
                            is_active=True
                        )
                    else:
                        existing_acc.is_active = True
                
                session.commit()
                return True, SUCCESS_CURRENCY_CREATED, currency.id
        except Exception as e:
            return False, f"Erreur lors de la création: {str(e)}", None
            
    def update_currency(self, currency_id: int, name: str, symbol: str) -> Tuple[bool, str]:
        """Met à jour les informations d'une devise"""
        try:
            with get_session() as session:
                currency = self.currency_repo.get_by_id(session, currency_id)
                if not currency:
                    return False, "Devise introuvable"
                
                currency.name = name
                currency.symbol = symbol
                session.flush()
                return True, "Informations de la devise mises à jour"
        except Exception as e:
            return False, f"Erreur lors de la mise à jour: {str(e)}"
    
    def get_currency_financial_summary(self) -> List[dict]:
        """
        Calcule la synthèse financière pour chaque devise à partir des achats.
        Chaque achat est traité indépendamment (FIFO).
        Le solde est calculé : Acheté - Consommé (par achat)
        """
        from core.models import Currency, Account, CurrencyPurchase
        from core.database import get_session
        from sqlalchemy import func

        try:
            with get_session() as session:
                currencies = session.query(Currency).filter(Currency.is_active == True).all()
                result = []

                for curr in currencies:
                    # Skip default currency (DA/DZD) - son compte est géré séparément dans Treasury
                    if curr.code == DEFAULT_CURRENCY_CODE:
                        continue
                    
                    # 1. Compte de trésorerie (Caisse) - pour info uniquement
                    account = session.query(Account).filter(Account.currency_id == curr.id, Account.is_active == True).first()
                    account_name = account.code if account else "Aucun compte"

                    # 2. Total Acheté (quantité en devise étrangère)
                    total_purchased = session.query(func.sum(CurrencyPurchase.amount)).filter(
                        CurrencyPurchase.currency_id == curr.id,
                        CurrencyPurchase.is_active == True
                    ).scalar() or 0.0

                    # 3. Total Consommé (quantité utilisée)
                    total_consumed = session.query(func.sum(CurrencyPurchase.consumed)).filter(
                        CurrencyPurchase.currency_id == curr.id,
                        CurrencyPurchase.is_active == True
                    ).scalar() or 0.0

                    # 4. Valeur Totale Achetée en DA
                    total_value_dzd = session.query(func.sum(CurrencyPurchase.total_dzd)).filter(
                        CurrencyPurchase.currency_id == curr.id,
                        CurrencyPurchase.is_active == True
                    ).scalar() or 0.0

                    # 5. Calculer le taux moyen pondéré
                    avg_rate = (total_value_dzd / total_purchased) if total_purchased > 0 else 0.0

                    # 6. Solde Actuel = Total Acheté - Total Consommé
                    current_balance = total_purchased - total_consumed
                    if current_balance < 0:
                        current_balance = 0.0

                    # 7. Valeur du solde en DA
                    balance_dzd = current_balance * avg_rate if avg_rate > 0 else 0.0

                    result.append({
                        "id": curr.id,
                        "code": curr.code,
                        "name": curr.name,
                        "symbol": curr.symbol,
                        "account_name": account_name,
                        "total_purchased": total_purchased,
                        "total_consumed": total_consumed,
                        "total_value_dzd": total_value_dzd,
                        "balance": current_balance,
                        "balance_dzd": balance_dzd,
                        "is_default": curr.is_default
                    })

                # Sort: Default first, then alphabetical
                result.sort(key=lambda x: (not x['is_default'], x['code']))
                return result
        except Exception as e:
            log_error(e, context="CurrencyService.get_currency_financial_summary")
            return []

    def get_supplier_payments_history(self, filter_status: str = "active") -> List[dict]:
        """
        Récupère l'historique complet des paiements effectués aux fournisseurs de devises.
        """
        from core.models import SupplierPayment, CurrencySupplier, Account, Currency
        from core.database import get_session
        from sqlalchemy import and_

        try:
            with get_session() as session:
                if filter_status == "all":
                    payments = session.query(SupplierPayment).order_by(SupplierPayment.date.desc()).all()
                elif filter_status == "archived":
                    payments = session.query(SupplierPayment).filter(SupplierPayment.is_active == False).order_by(SupplierPayment.date.desc()).all()
                else:
                    payments = session.query(SupplierPayment).filter(SupplierPayment.is_active == True).order_by(SupplierPayment.date.desc()).all()

                result = []
                for p in payments:
                    supplier = p.supplier
                    account = p.account
                    currency = account.currency if account else None

                    result.append({
                        "id": p.id,
                        "date": p.date,
                        "supplier_name": supplier.name if supplier else "Inconnu",
                        "amount": p.amount,
                        "account_name": account.code if account else "Inconnu",
                        "currency_symbol": currency.symbol if currency else "",
                        "reference": p.reference or "-",
                        "notes": p.notes or "",
                        "is_active": p.is_active
                    })
                return result
        except Exception as e:
            log_error(e, context="CurrencyService.get_supplier_payments_history")
            return []

    def delete_supplier_payment(self, payment_id: int) -> Tuple[bool, str]:
        """Annule un paiement fournisseur (inversion)."""
        try:
            with get_session() as session:
                payment = self.payment_repo.get_by_id(session, payment_id)
                if not payment:
                    return False, "Paiement introuvable"
                if not payment.is_active:
                    return False, "Ce paiement est déjà annulé"

                # Inverser le solde du fournisseur
                supplier = payment.supplier
                if supplier:
                    supplier.balance += payment.amount  # Retour de la dette

                payment.is_active = False
                session.flush()
                return True, "Paiement annulé avec succès"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def restore_supplier_payment(self, payment_id: int) -> Tuple[bool, str]:
        """Réactive un paiement fournisseur annulé."""
        try:
            with get_session() as session:
                payment = self.payment_repo.get_by_id(session, payment_id)
                if not payment:
                    return False, "Paiement introuvable"
                if payment.is_active:
                    return False, "Ce paiement est déjà actif"

                # Réappliquer la réduction du solde
                supplier = payment.supplier
                if supplier:
                    supplier.balance -= payment.amount

                payment.is_active = True
                session.flush()
                return True, "Paiement restauré avec succès"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def get_supplier_payment(self, payment_id: int) -> Optional[dict]:
        """Récupère un paiement fournisseur par ID."""
        from core.models import SupplierPayment
        from core.database import get_session
        try:
            with get_session() as session:
                payment = session.query(SupplierPayment).filter(SupplierPayment.id == payment_id).first()
                if not payment:
                    return None
                return {
                    "id": payment.id,
                    "supplier_id": payment.supplier_id,
                    "supplier_name": payment.supplier.name if payment.supplier else "",
                    "account_id": payment.account_id,
                    "amount": payment.amount,
                    "rate": getattr(payment, 'rate', 1.0),
                    "reference": payment.reference or "",
                    "date": payment.date,
                    "is_active": payment.is_active
                }
        except Exception as e:
            log_error(e, context="CurrencyService.get_supplier_payment")
            return None

    def update_supplier_payment(self, payment_id: int, supplier_id: int, account_id: int,
                                amount: float, reference: str = "") -> Tuple[bool, str]:
        """Met à jour un paiement fournisseur."""
        try:
            with get_session() as session:
                payment = self.payment_repo.get_by_id(session, payment_id)
                if not payment:
                    return False, "Paiement introuvable"

                old_amount = payment.amount

                # Annuler l'ancien impact
                if payment.supplier:
                    payment.supplier.balance += old_amount
                if payment.account:
                    payment.account.balance += old_amount

                # Appliquer le nouvel impact
                payment.supplier_id = supplier_id
                payment.account_id = account_id
                payment.amount = amount
                payment.reference = reference

                if payment.supplier:
                    payment.supplier.balance -= amount
                if payment.account:
                    payment.account.balance -= amount

                session.flush()
                return True, "Paiement modifié avec succès"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def get_all_currencies(self) -> List[dict]:
        """Récupère toutes les devises actives (Purified Data)"""
        with get_session() as session:
            currencies = self.currency_repo.get_active(session)
            result = []
            for c in currencies:
                latest = self.rate_repo.get_latest_rate(session, c.id)
                result.append({
                    'id': c.id, 'code': c.code, 'name': c.name, 'symbol': c.symbol,
                    'is_default': c.is_default, 'is_deletable': c.is_deletable,
                    'is_active': c.is_active,
                    'latest_rate': latest.rate if latest else 1.0,
                    'rate_date': latest.date if latest else None
                })
            return result
    
    def get_currency(self, currency_id: int) -> Optional[dict]:
        """Récupère une devise par ID (Purified Data)"""
        with get_session() as session:
            c = self.currency_repo.get_by_id(session, currency_id)
            if not c: return None
            return {
                'id': c.id, 'code': c.code, 'name': c.name, 'symbol': c.symbol,
                'is_default': c.is_default, 'is_deletable': c.is_deletable
            }
    
    def delete_currency(self, currency_id: int) -> Tuple[bool, Optional[str]]:
        """Supprime une devise (Désactivation avec protection financière)"""
        try:
            with get_session() as session:
                currency = self.currency_repo.get_by_id(session, currency_id)
                if not currency:
                    return False, "Devise introuvable"
                
                if not currency.is_deletable:
                    return False, ERROR_CANNOT_DELETE_DEFAULT_CURRENCY
                
                # --- VÉRIFICATION DE SÉCURITÉ (INTÉGRITÉ FINANCIÈRE) ---
                from core.models import Transaction, CurrencyPurchase, Account
                
                # 1. Vérifier si des achats de devise existent
                purch_count = session.query(CurrencyPurchase).filter_by(currency_id=currency_id, is_active=True).count()
                if purch_count > 0:
                    return False, f"Action refusée : Cette devise est utilisée dans {purch_count} opération(s) d'achat enregistrée(s)."

                # 2. Vérifier les comptes et leurs transactions
                accounts = session.query(Account).filter_by(currency_id=currency_id, is_active=True).all()
                for acc in accounts:
                    trans_count = session.query(Transaction).filter_by(account_id=acc.id, is_active=True).count()
                    if trans_count > 0:
                        return False, f"Action refusée : Le compte '{acc.name}' possède déjà des transactions liées."
                    
                    if abs(acc.balance) > 0.001:
                        return False, f"Action refusée : Le compte '{acc.name}' possède un solde actif ({acc.balance})."
                
                # Si tout est OK : Désactiver au lieu de supprimer
                currency.is_active = False
                
                # SYNCHRO COMPTE: Désactiver le compte auto s'il existe
                account_code = f"CAISSE_{currency.code}"
                existing_acc = self.account_repo.get_by_code(session, account_code)
                if existing_acc:
                    existing_acc.is_active = False
                    
                session.flush()
                
                return True, f"La devise '{currency.code}' a été désactivée مع الحساب التابع لها بنجاح."
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    # ========================================================================
    # GESTION MONDIALE (World Reference)
    # ========================================================================

    def get_world_currency_status(self) -> List:
        """
        Compare la liste WORLD_CURRENCIES avec la DB
        """
        from utils.constants import WORLD_CURRENCIES, DEFAULT_CURRENCY_CODE
        from core.models import Transaction, CurrencyPurchase, Account
        
        try:
            from utils.constants import WORLD_CURRENCIES, DEFAULT_CURRENCY_CODE
            with get_session() as session:
                all_db_currencies = self.currency_repo.get_all(session, limit=1000)
                active_currencies = {c.code: c for c in all_db_currencies}
                
                result = []
                seen_codes = set()
                for wc in WORLD_CURRENCIES:
                    code = wc["code"]
                    seen_codes.add(code)
                    db_curr = active_currencies.get(code)
                    
                    # Vérifier si on peut désactiver (pas de transactions)
                    is_deletable = True
                    has_country = hasattr(db_curr, 'country') if db_curr else False
                    
                    if db_curr:
                        if db_curr.is_default:
                            is_deletable = False
                        else:
                            # Vérifier transactions
                            trans_count = session.query(Transaction).join(Account).filter(Account.currency_id == db_curr.id).count()
                            purch_count = session.query(CurrencyPurchase).filter(CurrencyPurchase.currency_id == db_curr.id).count()
                            is_deletable = (trans_count == 0 and purch_count == 0)

                    result.append({
                        "code": code,
                        "name": wc["name"],
                        "symbol": wc["symbol"],
                        "country": (db_curr.country if has_country and db_curr.country else wc.get("country", "Inconnu")),
                        "is_active": db_curr.is_active if db_curr else False,
                        "is_main": db_curr.is_default if db_curr else (code == DEFAULT_CURRENCY_CODE),
                        "can_disable": is_deletable
                    })
                
                # APPEND CUSTOM CURRENCIES
                for code, db_curr in active_currencies.items():
                    if code not in seen_codes:
                        is_deletable = True
                        if db_curr.is_default:
                            is_deletable = False
                        else:
                            from core.models import Transaction, CurrencyPurchase, Account
                            trans_count = session.query(Transaction).join(Account).filter(Account.currency_id == db_curr.id).count()
                            purch_count = session.query(CurrencyPurchase).filter(CurrencyPurchase.currency_id == db_curr.id).count()
                            is_deletable = (trans_count == 0 and purch_count == 0)

                        result.append({
                            "code": code,
                            "name": db_curr.name,
                            "symbol": db_curr.symbol,
                            "country": db_curr.country or "Personnalisée",
                            "is_active": db_curr.is_active,
                            "is_main": db_curr.is_default,
                            "can_disable": is_deletable
                        })
                
                # TIERCE SORT: First active ones, then alphabetically by code
                result.sort(key=lambda x: (not x['is_active'], x['code']))
                return result
        except Exception as e:
            log_error(e, context="CurrencyService.get_world_currency_status")
            return []

    def toggle_world_currency(self, code: str, enable: bool) -> Tuple[bool, str]:
        """
        Active/Désactive une devise et synchronise les comptes.
        Utilise le catalogue global pour la découverte.
        """
        from utils.currency_catalog import GLOBAL_CURRENCY_CATALOG
        try:
            if enable:
                currency_exists = False
                currency_data = None
                
                with get_session() as session:
                    currency = self.currency_repo.get_by_code(session, code)
                    if currency:
                        currency_exists = True
                        currency_data = (currency.name, currency.symbol, currency.country)
                
                if currency_exists:
                    ok, msg, _ = self.create_currency(code, *currency_data)
                    return ok, msg
                        
                wc_info = next((c for c in GLOBAL_CURRENCY_CATALOG if c["code"] == code), None)
                if not wc_info: return False, "Devise inconnue au catalogue mondial"
                ok, msg, _ = self.create_currency(code, wc_info["name"], wc_info["symbol"], wc_info.get("country"))
                return ok, msg
            else:
                # DÉSACTIVATION
                curr_id = None
                with get_session() as session:
                    currency = self.currency_repo.get_by_code(session, code)
                    if currency: curr_id = currency.id
                
                if not curr_id: return True, "Déjà désactivé"
                return self.delete_currency(curr_id) # delete_currency returns 2 values (bool, str)
                    
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def synchronize_world_catalog(self, updated_data: List[dict]) -> Tuple[bool, str]:
        """
        Synchronise en masse les changements depuis le nouveau WorldCurrenciesDialog.
        """
        success_count = 0
        errors = []
        
        # 1. Identifier les changements par rapport à la DB actuelle
        current_status = self.sync_engine.get_catalog_status()
        db_map = {s["code"]: s["is_active"] for s in current_status}
        
        for item in updated_data:
            code = item["code"]
            new_state = item["is_active"]
            old_state = db_map.get(code, False)
            
            if new_state != old_state:
                # Appliquer le changement
                ok, msg = self.toggle_world_currency(code, new_state)
                if ok:
                    success_count += 1
                else:
                    errors.append(f"{code}: {msg}")
        
        if success_count > 0 or not errors:
            msg = f"Synchronisation réussie ({success_count} modifications)."
            if errors: msg += f" (Certaines erreurs: {', '.join(errors)})"
            return True, msg
            
        return False, f"Échec de la synchronisation: {', '.join(errors)}"
    
    # ========================================================================
    # GESTION DES TAUX DE CHANGE
    # ========================================================================
    
    def create_exchange_rate(self, currency_id: int, rate: float, date: datetime = None) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Crée un nouveau taux de change.
        """
        is_valid, error = validate_amount(rate)
        if not is_valid:
            return False, error, None
        
        try:
            with get_session() as session:
                # Désactiver les anciens taux
                old_rates = self.rate_repo.get_rates_by_currency(session, currency_id)
                for old_rate in old_rates:
                    old_rate.is_active = False
                
                # Créer le nouveau taux
                exchange_rate = self.rate_repo.create(
                    session,
                    currency_id=currency_id,
                    rate=rate,
                    date=date or datetime.now(),
                    is_active=True
                )
                
                return True, "Taux de change créé avec succès", exchange_rate.id
        except Exception as e:
            return False, f"Erreur: {str(e)}", None
    
    def get_latest_rate(self, currency_id: int) -> Optional[float]:
        """Récupère le dernier taux de change d'une devise"""
        with get_session() as session:
            rate = self.rate_repo.get_latest_rate(session, currency_id)
            return rate.rate if rate else 1.0
    
    # ========================================================================
    # GESTION DES FOURNISSEURS
    # ========================================================================
    
    def create_supplier(self, name: str, supplier_type: str, contact: str = "", 
                        phone: str = "", email: str = "", currency_id: int = None,
                        commercial_register_name: str = "", register_number: str = "",
                        nif: str = "", address: str = "", bank: str = "",
                        license_goods_ids: list = None, **kwargs) -> Tuple[bool, str, Optional[int]]:
        """Crée un nouveau fournisseur"""
        is_valid, error = validate_required_field(name, "Nom du fournisseur")
        if not is_valid:
            return False, error, None
        
        try:
            with get_session() as session:
                supplier = self.supplier_repo.create(
                    session,
                    name=name,
                    supplier_type=supplier_type,
                    contact=contact,
                    phone=phone,
                    email=email,
                    currency_id=currency_id,
                    commercial_register_name=commercial_register_name,
                    register_number=register_number,
                    nif=nif,
                    address=address,
                    bank=bank,
                    balance=0.0,
                    is_active=True
                )
                # Attach license goods if provided
                if license_goods_ids:
                    from core.models import LicenseGoodsCatalog
                    goods = session.query(LicenseGoodsCatalog).filter(
                        LicenseGoodsCatalog.id.in_(license_goods_ids)
                    ).all()
                    supplier.license_goods_list = goods
                    
                session.flush()
                
                # Auto-création du compte bancaire pour les licences (Dinar -> DA)
                if supplier_type == 'LICENSE':
                    from core.models import Account, Currency
                    da_currency = session.query(Currency).filter(Currency.code.in_(['DA', 'DZD'])).first()
                    if da_currency:
                        new_account = Account(
                            name=f"({bank}) {commercial_register_name or name}",
                            code=f"REG-{supplier.id}",
                            account_type="COMPTE",
                            currency_id=da_currency.id,
                            balance=0.0,
                            is_main=False,
                            is_active=True,
                            description=f"Compte bancaire généré automatiquement pour le registre: {register_number}"
                        )
                        session.add(new_account)
                        session.flush()
                        supplier.bank_account_id = new_account.id
                        
                session.flush()
                return True, "Fournisseur créé avec succès", supplier.id
        except Exception as e:
            return False, f"Erreur lors de la création: {str(e)}", None
            
    def update_supplier(self, supplier_id: int, name: str, supplier_type: str,
                        contact: str = "", phone: str = "", email: str = "",
                        currency_id: int = None, company_name: str = "", company_address: str = "",
                        country: str = "", commercial_register_name: str = "",
                        register_number: str = "", nif: str = "", address: str = "",
                        bank: str = "", license_goods_ids: list = None, **kwargs) -> Tuple[bool, str]:
        """Met à jour un fournisseur"""
        try:
            with get_session() as session:
                supplier = self.supplier_repo.get_by_id(session, supplier_id)
                if not supplier:
                    return False, "Fournisseur introuvable"

                supplier.name = name
                supplier.supplier_type = supplier_type
                supplier.contact = contact
                supplier.phone = phone
                supplier.email = email
                supplier.currency_id = currency_id
                supplier.company_name = company_name
                supplier.company_address = company_address
                supplier.country = country
                supplier.commercial_register_name = commercial_register_name
                supplier.register_number = register_number
                supplier.nif = nif
                supplier.address = address
                supplier.bank = bank
                # Update license goods list
                if license_goods_ids is not None:
                    from core.models import LicenseGoodsCatalog
                    goods = session.query(LicenseGoodsCatalog).filter(
                        LicenseGoodsCatalog.id.in_(license_goods_ids)
                    ).all()
                    supplier.license_goods_list = goods
                session.flush()
                return True, "Fournisseur mis à jour"
        except Exception as e:
            return False, f"Erreur lors de la mise à jour: {str(e)}"
            
    def get_all_suppliers(self, supplier_type: str = None, filter_status: str = "active") -> List[dict]:
        """Récupère tous les fournisseurs avec leurs données RC et marchandises"""
        with get_session() as session:
            query = session.query(self.supplier_repo.model)
            if filter_status == "active": query = query.filter_by(is_active=True)
            elif filter_status == "inactive": query = query.filter_by(is_active=False)
            
            if supplier_type: query = query.filter_by(supplier_type=supplier_type)
            suppliers = query.all()
            return [
                {
                    'id': s.id, 'name': s.name, 'supplier_type': s.supplier_type,
                    'contact': s.contact or "", 'phone': s.phone or "", 'email': s.email or "",
                    'balance': s.balance, 'currency_id': s.currency_id, 'is_active': s.is_active,
                    'currency_code': s.currency.code if s.currency else DEFAULT_CURRENCY_CODE,
                    'currency_symbol': s.currency.symbol if s.currency else "DA",
                    'company_name': s.company_name or "",
                    'company_address': s.company_address or "",
                    'country': s.country or "",
                    'commercial_register_name': s.commercial_register_name or "",
                    'register_number': s.register_number or "",
                    'nif': s.nif or "",
                    'address': s.address or "",
                    'bank': s.bank or "",
                    'bank_account_id': s.bank_account_id,
                    'license_goods_ids': [g.id for g in s.license_goods_list],
                    'license_goods_names': [g.name for g in s.license_goods_list],
                } for s in suppliers
            ]

    def delete_supplier(self, supplier_id: int) -> Tuple[bool, str]:
        """Archive un fournisseur (Soft Delete) avec vérification de sécurité"""
        with get_session() as session:
            # 1. Vérifier s'il y a des transactions liées
            supplier = self.supplier_repo.get_by_id(session, supplier_id)
            if not supplier:
                return False, "Fournisseur introuvable"

            # Vérifier les achats de devises
            purch_count = session.query(CurrencyPurchase).filter_by(supplier_id=supplier_id, is_active=True).count()
            if purch_count > 0:
                return False, f"Action refusée : Ce fournisseur est lié à {purch_count} opération(s) d'achat enregistrée(s)."

            # Vérifier les paiements fournisseurs
            payment_count = session.query(SupplierPayment).filter_by(supplier_id=supplier_id, is_active=True).count()
            if payment_count > 0:
                return False, f"Action refusée : Ce fournisseur est lié à {payment_count} paiement(s) enregistré(s)."

            # Si tout est OK : Soft Delete
            success = self.supplier_repo.soft_delete(session, supplier_id)
            session.commit()
            return success, "Fournisseur archivé" if success else "Échec de l'archivage"

    def restore_supplier(self, supplier_id: int) -> Tuple[bool, str]:
        """Restaure un fournisseur archivé"""
        with get_session() as session:
            success = self.supplier_repo.restore(session, supplier_id)
            session.commit()
            return success, "Fournisseur restauré" if success else "Échec de la restauration"
    
    # ========================================================================
    # CATALOGUE MARCHANDISES LICENCES (License Goods Catalog)
    # ========================================================================

    def get_all_license_goods(self, include_inactive: bool = False) -> List[dict]:
        """Récupère tout le catalogue des marchandises de licences"""
        from core.models import LicenseGoodsCatalog
        with get_session() as session:
            query = session.query(LicenseGoodsCatalog)
            if not include_inactive:
                query = query.filter_by(is_active=True)
            goods = query.order_by(LicenseGoodsCatalog.name).all()
            return [{'id': g.id, 'name': g.name, 'description': g.description or '', 'is_active': g.is_active} for g in goods]

    def create_license_goods(self, name: str, description: str = "") -> Tuple[bool, str, Optional[int]]:
        """Crée un nouveau type de marchandise dans le catalogue"""
        from core.models import LicenseGoodsCatalog
        if not name or not name.strip():
            return False, "Le nom est obligatoire", None
        with get_session() as session:
            try:
                existing = session.query(LicenseGoodsCatalog).filter_by(name=name.strip()).first()
                if existing:
                    return False, "Ce type de marchandise existe déjà", None
                g = LicenseGoodsCatalog(name=name.strip(), description=description)
                session.add(g)
                session.commit()
                return True, "Marchandise ajoutée au catalogue", g.id
            except Exception as e:
                session.rollback()
                return False, str(e), None

    def update_license_goods(self, goods_id: int, name: str, description: str = "") -> Tuple[bool, str]:
        """Met à jour une entrée du catalogue"""
        from core.models import LicenseGoodsCatalog
        with get_session() as session:
            try:
                g = session.query(LicenseGoodsCatalog).get(goods_id)
                if not g:
                    return False, "Marchandise introuvable"
                g.name = name.strip()
                g.description = description
                session.commit()
                return True, "Marchandise mise à jour"
            except Exception as e:
                session.rollback()
                return False, str(e)

    def delete_license_goods(self, goods_id: int) -> Tuple[bool, str]:
        """Archive une entrée du catalogue"""
        from core.models import LicenseGoodsCatalog
        with get_session() as session:
            try:
                g = session.query(LicenseGoodsCatalog).get(goods_id)
                if not g:
                    return False, "Marchandise introuvable"
                g.is_active = False
                session.commit()
                return True, "Marchandise archivée"
            except Exception as e:
                session.rollback()
                return False, str(e)

    def restore_license_goods(self, goods_id: int) -> Tuple[bool, str]:
        """Restaure une entrée archivée du catalogue"""
        from core.models import LicenseGoodsCatalog
        with get_session() as session:
            try:
                g = session.query(LicenseGoodsCatalog).get(goods_id)
                if not g:
                    return False, "Marchandise introuvable"
                g.is_active = True
                session.commit()
                return True, "Marchandise restaurée"
            except Exception as e:
                session.rollback()
                return False, str(e)

    # ========================================================================
    # GESTION DES ACHATS DE DEVISES
    # ========================================================================
    
    def purchase_currency(self, currency_id: int, supplier_id: int, amount: float,
                         rate: float, payment_type: str, account_id: int = None,
                         reference: str = "", notes: str = "", discount: float = 0.0,
                         date: datetime = None) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Achète une devise.
        """
        # Validation
        is_valid, error = validate_amount(amount)
        if not is_valid:
            return False, error, None
        
        is_valid, error = validate_amount(rate)
        if not is_valid:
            return False, error, None
        
        if payment_type not in [PAYMENT_TYPE_CASH, PAYMENT_TYPE_CREDIT]:
            return False, "Type de paiement invalide", None
        
        if payment_type == PAYMENT_TYPE_CASH and not account_id:
            return False, "Le compte est requis pour un paiement comptant", None
        
        try:
            with get_session() as session:
                total_dzd = (amount * rate) - discount
                if total_dzd < 0:
                    total_dzd = 0
                
                purchase = self.purchase_repo.create(
                    session,
                    currency_id=currency_id,
                    supplier_id=supplier_id,
                    amount=amount,
                    rate=rate,
                    total_dzd=total_dzd,
                    discount=discount,
                    payment_type=payment_type,
                    account_id=account_id if payment_type == PAYMENT_TYPE_CASH else None,
                    date=date or datetime.now(),
                    reference=reference,
                    notes=notes
                )
                
                if payment_type == PAYMENT_TYPE_CASH:
                    self.transaction_repo.create(
                        session,
                        account_id=account_id,
                        type=TRANSACTION_TYPE_DEBIT,
                        amount=total_dzd,
                        description=f"Achat de {amount} {purchase.currency.code}",
                        reference=reference,
                        date=date or datetime.now()
                    )
                    self.account_repo.update_balance(session, account_id, total_dzd, True)
                
                if payment_type == PAYMENT_TYPE_CREDIT:
                    self.supplier_repo.update_balance(session, supplier_id, total_dzd, True)
                
                # --- SYNCHRONISATION LOGIQUE (NOUVEAU) ---
                # On crédite le compte de la devise achetée (Entrée de fonds étrangers)
                currency = self.currency_repo.get_by_id(session, currency_id)
                account_code = f"CAISSE_{currency.code}"
                curr_acc = self.account_repo.get_by_code(session, account_code)
                
                if curr_acc:
                    self.transaction_repo.create(
                        session,
                        account_id=curr_acc.id,
                        type=TRANSACTION_TYPE_CREDIT,
                        amount=amount, # Montant en devise étrangère
                        description=f"Achat n°{purchase.id} (Entrée {currency.code})",
                        reference=reference,
                        date=date or datetime.now()
                    )
                    self.account_repo.update_balance(session, curr_acc.id, amount, True)
                
                session.commit()
                return True, SUCCESS_OPERATION_CREATED, purchase.id
        except Exception as e:
            return False, f"Erreur: {str(e)}", None
    
    def get_all_purchases(self, limit: int = 100, filter_status: str = "active") -> List[dict]:
        """Récupère tous les achats selon le statut (active, inactive, all)"""
        with get_session() as session:
            query = session.query(self.purchase_repo.model)
            if filter_status == "active": query = query.filter_by(is_active=True)
            elif filter_status == "inactive": query = query.filter_by(is_active=False)

            purchases = query.order_by(self.purchase_repo.model.id.desc()).limit(limit).all()
            return [
                {
                    'id': p.id, 'date': p.date, 'currency_code': p.currency.code,
                    'supplier_name': p.supplier.name, 'amount': p.amount,
                    'rate': p.rate, 'total_dzd': p.total_dzd,
                    'consumed': getattr(p, 'consumed', 0.0),
                    'remaining': p.amount - getattr(p, 'consumed', 0.0),
                    'is_active': p.is_active,
                    'payment_type': p.payment_type, 'reference': p.reference or ""
                } for p in purchases
            ]

    def get_available_lots(self, currency_id: int) -> List[dict]:
        """
        Récupère tous les LOTs disponibles pour une devise (ceux avec un solde > 0).
        Triés par date (FIFO - le plus ancien en premier).
        """
        from core.models import CurrencyPurchase, Currency
        try:
            with get_session() as session:
                lots = session.query(CurrencyPurchase).filter(
                    CurrencyPurchase.currency_id == currency_id,
                    CurrencyPurchase.is_active == True
                ).order_by(CurrencyPurchase.date.asc()).all()

                result = []
                for lot in lots:
                    consumed = getattr(lot, 'consumed', 0.0)
                    remaining = lot.amount - consumed
                    if remaining > 0:
                        result.append({
                            'id': lot.id,
                            'date': lot.date,
                            'amount': lot.amount,
                            'consumed': consumed,
                            'remaining': remaining,
                            'rate': lot.rate,
                            'supplier_name': lot.supplier.name if lot.supplier else "Inconnu",
                            'reference': lot.reference or ""
                        })
                return result
        except Exception as e:
            log_error(e, context="CurrencyService.get_available_lots")
            return []

    def consume_from_lot(self, purchase_id: int, amount: float) -> Tuple[bool, str]:
        """
        Consomme un montant d'un LOT spécifique.
        Retourne False si le montant dépasse le reste du LOT.
        """
        try:
            with get_session() as session:
                purchase = self.purchase_repo.get_by_id(session, purchase_id)
                if not purchase:
                    return False, "LOT introuvable"

                consumed = getattr(purchase, 'consumed', 0.0)
                remaining = purchase.amount - consumed

                if amount > remaining:
                    return False, f"Montant dépasse le reste du LOT (Disponible: {remaining:.2f})"

                purchase.consumed = consumed + amount
                session.flush()
                return True, "Consommation enregistrée avec succès"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def consume_from_lots_fifo(self, currency_id: int, amount: float) -> Tuple[bool, str]:
        """
        Consomme un montant en utilisant la méthode FIFO (First In, First Out).
        Commence par le LOT le plus ancien.
        """
        try:
            available_lots = self.get_available_lots(currency_id)
            if not available_lots:
                return False, "Aucun LOT disponible"

            total_available = sum(lot['remaining'] for lot in available_lots)
            if amount > total_available:
                return False, f"Montant dépasse le total disponible ({total_available:.2f})"

            remaining_to_consume = amount
            with get_session() as session:
                for lot in available_lots:
                    if remaining_to_consume <= 0:
                        break

                    purchase = self.purchase_repo.get_by_id(session, lot['id'])
                    if not purchase:
                        continue

                    consumed = getattr(purchase, 'consumed', 0.0)
                    lot_remaining = purchase.amount - consumed

                    # Quantité à consommer de ce LOT
                    to_consume = min(remaining_to_consume, lot_remaining)
                    purchase.consumed = consumed + to_consume
                    remaining_to_consume -= to_consume

                session.flush()
                return True, "Consommation enregistrée avec succès (FIFO)"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def restore_purchase(self, purchase_id: int) -> Tuple[bool, str]:
        """Restaure un achat annulé et réapplique son impact financier"""
        try:
            with get_session() as session:
                purchase = self.purchase_repo.get_by_id(session, purchase_id)
                if not purchase: return False, "Achat introuvable"
                
                # Réappliquer impact (DZD/Dette)
                if purchase.payment_type == PAYMENT_TYPE_CASH:
                    if purchase.account_id:
                        self.transaction_repo.create(
                            session,
                            account_id=purchase.account_id,
                            type=TRANSACTION_TYPE_DEBIT,
                            amount=purchase.total_dzd,
                            description=f"Restauration Achat n°{purchase.id} ({purchase.amount} {purchase.currency.code})",
                            reference=purchase.reference,
                            date=datetime.now()
                        )
                        self.account_repo.update_balance(session, purchase.account_id, purchase.total_dzd, True)
                else:
                    self.supplier_repo.update_balance(session, purchase.supplier_id, purchase.total_dzd, True)
                
                # Réappliquer impact (Devise)
                account_code = f"CAISSE_{purchase.currency.code}"
                curr_acc = self.account_repo.get_by_code(session, account_code)
                if curr_acc:
                    self.transaction_repo.create(
                        session,
                        account_id=curr_acc.id,
                        type=TRANSACTION_TYPE_CREDIT,
                        amount=purchase.amount,
                        description=f"Restauration Achat n°{purchase.id} (Entrée {purchase.currency.code})",
                        reference=purchase.reference,
                        date=datetime.now()
                    )
                    self.account_repo.update_balance(session, curr_acc.id, purchase.amount, True)
                    
                purchase.is_active = True
                session.commit()
                return True, "Achat restauré et impact financier réappliqué"
        except Exception as e:
            return False, f"Erreur: {str(e)}"
            
    def get_purchase(self, purchase_id: int) -> Optional[dict]:
        """Récupère un achat par ID (Purified Data)"""
        with get_session() as session:
            p = self.purchase_repo.get_by_id(session, purchase_id)
            if not p: return None
            return {
                'id': p.id, 'date': p.date, 'currency_id': p.currency_id,
                'currency_code': p.currency.code, 'supplier_id': p.supplier_id,
                'supplier_name': p.supplier.name, 'amount': p.amount,
                'rate': p.rate, 'total_dzd': p.total_dzd,
                'payment_type': p.payment_type, 'reference': p.reference or "",
                'notes': p.notes or ""
            }

    def delete_purchase(self, purchase_id: int) -> Tuple[bool, str]:
        """Annule un achat et inverse son impact financier"""
        try:
            with get_session() as session:
                purchase = self.purchase_repo.get_by_id(session, purchase_id)
                if not purchase:
                    return False, "Achat introuvable"
                
                if purchase.payment_type == PAYMENT_TYPE_CASH:
                    trans_list = self.transaction_repo.search(session, purchase.reference) if purchase.reference else []
                    for t in trans_list:
                        if abs(t.amount - purchase.total_dzd) < 0.01 and t.type == TRANSACTION_TYPE_DEBIT:
                            self.account_repo.update_balance(session, t.account_id, t.amount, False)
                            t.is_active = False
                            break
                else:
                    self.supplier_repo.update_balance(session, purchase.supplier_id, purchase.total_dzd, False)
                
                # SYNCHRONISATION LOGIQUE (ANNULATION)
                # On retire le montant de la caisse devise correspondante
                acc_code = f"CAISSE_{purchase.currency.code}"
                curr_acc = self.account_repo.get_by_code(session, acc_code)
                if curr_acc:
                    self.transaction_repo.create(
                        session,
                        account_id=curr_acc.id,
                        type=TRANSACTION_TYPE_DEBIT,
                        amount=purchase.amount,
                        description=f"Annulation Achat n°{purchase.id}",
                        reference=f"REV-{purchase.id}",
                        date=datetime.now()
                    )
                    self.account_repo.update_balance(session, curr_acc.id, purchase.amount, False)

                purchase.is_active = False
                session.commit()
                return True, "Achat annulé avec succès"
        except Exception as e:
            return False, f"Erreur lors de l'annulation: {str(e)}"

    def update_purchase_currency(self, purchase_id: int, supplier_id: int, currency_id: int, amount: float,
                                rate: float, payment_type: str, account_id: int = None,
                                reference: str = "", notes: str = "", discount: float = 0.0,
                                date: datetime = None) -> Tuple[bool, str]:
        """Modifie un achat et recalcule les impacts financiers"""
        try:
            with get_session() as session:
                purchase = self.purchase_repo.get_by_id(session, purchase_id)
                if not purchase:
                    return False, "Achat introuvable"

                # 1. Inverser l'ancien impact (DZD/Dette)
                if purchase.payment_type == PAYMENT_TYPE_CASH:
                    if purchase.account_id:
                        self.transaction_repo.create(
                            session,
                            account_id=purchase.account_id,
                            type=TRANSACTION_TYPE_CREDIT, # Inversion (REMBOURSEMENT)
                            amount=purchase.total_dzd,
                            description=f"Annulation/Modif Achat n°{purchase.id}",
                            reference=f"REV-{purchase.id}",
                            date=datetime.now()
                        )
                        self.account_repo.update_balance(session, purchase.account_id, purchase.total_dzd, False)
                else:
                    self.supplier_repo.update_balance(session, purchase.supplier_id, purchase.total_dzd, False)

                # 1b. Inverser l'ancien impact (Ancienne Devise Étrangère)
                acc_code_old = f"CAISSE_{purchase.currency.code}"
                curr_acc_old = self.account_repo.get_by_code(session, acc_code_old)
                if curr_acc_old:
                    self.transaction_repo.create(
                        session,
                        account_id=curr_acc_old.id,
                        type=TRANSACTION_TYPE_DEBIT, # Inversion (SORTIE)
                        amount=purchase.amount,
                        description=f"Annulation/Modif Achat n°{purchase.id}",
                        reference=f"REV-{purchase.id}",
                        date=datetime.now()
                    )
                    self.account_repo.update_balance(session, curr_acc_old.id, purchase.amount, False)

                # 2. Appliquer le nouvel impact (DZD/Dette)
                total_dzd = (amount * rate) - discount
                if total_dzd < 0:
                    total_dzd = 0
                if payment_type == PAYMENT_TYPE_CASH:
                    if not account_id:
                        return False, "Compte requis pour paiement CASH"
                    
                    self.transaction_repo.create(
                        session,
                        account_id=account_id,
                        type=TRANSACTION_TYPE_DEBIT,
                        amount=total_dzd,
                        description=f"Correction Achat n°{purchase.id} (Nouveau Montant)",
                        reference=reference,
                        date=date or datetime.now()
                    )
                    self.account_repo.update_balance(session, account_id, total_dzd, True)
                else:
                    self.supplier_repo.update_balance(session, supplier_id, total_dzd, True)

                # 2b. Appliquer le nouvel impact (Nouvelle Devise Étrangère)
                new_currency = self.currency_repo.get_by_id(session, currency_id)
                acc_code_new = f"CAISSE_{new_currency.code}"
                curr_acc_new = self.account_repo.get_by_code(session, acc_code_new)
                
                if curr_acc_new:
                    self.transaction_repo.create(
                        session,
                        account_id=curr_acc_new.id,
                        type=TRANSACTION_TYPE_CREDIT,
                        amount=amount,
                        description=f"Correction Achat n°{purchase.id} (Nouveau Montant)",
                        reference=reference,
                        date=date or datetime.now()
                    )
                    self.account_repo.update_balance(session, curr_acc_new.id, amount, True)

                # 3. Mise à jour de l'achat
                purchase.supplier_id = supplier_id
                purchase.currency_id = currency_id
                purchase.amount = amount
                purchase.rate = rate
                purchase.total_dzd = total_dzd
                purchase.discount = discount
                purchase.payment_type = payment_type
                purchase.account_id = account_id if payment_type == PAYMENT_TYPE_CASH else None
                purchase.reference = reference
                purchase.notes = notes
                if date: purchase.date = date
                
                session.commit()
                return True, "Achat mis à jour et impacts financiers recalculés"
        except Exception as e:
            return False, f"Erreur lors de la mise à jour: {str(e)}"
    
    # ========================================================================
    # GESTION DES PAIEMENTS FOURNISSEURS
    # ========================================================================
    
    def pay_supplier(self, supplier_id: int, account_id: int, amount: float,
                    rate: float = 1.0, reference: str = "", notes: str = "",
                    date: datetime = None) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Effectue un paiement à un fournisseur.
        """
        is_valid, error = validate_amount(amount)
        if not is_valid:
            return False, error, None
        
        try:
            with get_session() as session:
                supplier = self.supplier_repo.get_by_id(session, supplier_id)
                if not supplier:
                    return False, "Fournisseur introuvable", None
                
                is_foreign = supplier.currency and supplier.currency.code != DEFAULT_CURRENCY_CODE
                deduction_amount = amount / rate if is_foreign else amount

                # Si le solde est positif, vérifier que le montant ne dépasse pas la dette
                # If balance is <= 0 (no debt), accept as advance
                if supplier.balance > 0 and deduction_amount > supplier.balance + 0.01:
                    return False, f"Le montant ({deduction_amount:.2f}) dépasse la dette ({supplier.balance:.2f})", None
                
                payment = self.payment_repo.create(
                    session,
                    supplier_id=supplier_id,
                    account_id=account_id,
                    amount=amount,
                    date=date or datetime.now(),
                    reference=reference,
                    notes=notes
                )
                
                self.transaction_repo.create(
                    session,
                    account_id=account_id,
                    type=TRANSACTION_TYPE_DEBIT,
                    amount=amount,
                    description=f"Paiement à {supplier.name} ({deduction_amount:.2f} {supplier.currency.code if supplier.currency else 'DZD'})",
                    reference=reference,
                    date=date or datetime.now()
                )
                
                self.account_repo.update_balance(session, account_id, amount, True)
                self.supplier_repo.update_balance(session, supplier_id, deduction_amount, False)
                
                return True, SUCCESS_OPERATION_CREATED, payment.id
        except Exception as e:
            return False, f"Erreur: {str(e)}", None
    
    def get_supplier_payments(self, supplier_id: int, limit: int = 100) -> List[dict]:
        """Récupère les paiements d'un fournisseur (Purified Data)"""
        with get_session() as session:
            payments = self.payment_repo.get_by_supplier(session, supplier_id, limit)
            return [
                {
                    'id': p.id, 'date': p.date, 'amount': p.amount,
                    'account_name': p.account.name, 'reference': p.reference or ""
                } for p in payments
            ]
