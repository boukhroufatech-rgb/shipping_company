"""
Initialisation des données de base du système (Devises, Comptes par défaut, Entités génériques)
"""
from core.database import get_session
from core.models import Currency, Account, ExpenseType, Customer, Warehouse, CurrencySupplier
from utils.constants import (
    DEFAULT_CURRENCY_CODE, DEFAULT_CURRENCY_NAME, DEFAULT_CURRENCY_SYMBOL,
    SUPPLIER_TYPE_CURRENCY
)

def initialize_system_data():
    """Initialise toutes les données par défaut nécessaires au fonctionnement du système"""
    with get_session() as session:
        # 1. DEVISES (DA, USD, etc.)
        da = session.query(Currency).filter(Currency.code == DEFAULT_CURRENCY_CODE).first()
        
        if not da:
            da = Currency(
                code=DEFAULT_CURRENCY_CODE,
                name=DEFAULT_CURRENCY_NAME,
                symbol=DEFAULT_CURRENCY_SYMBOL,
                is_default=True,
                is_deletable=False,
                is_active=True,
                country="Algérie"
            )
            session.add(da)
            session.flush()
            print(f"✓ Devise par défaut créée: {DEFAULT_CURRENCY_CODE}")
        else:
            da.is_active = True
            da.is_default = True
            da.is_deletable = False
            session.flush()
        
        other_currencies = [
            ("USD", "Dollar Américain", "$", "États-Unis"),
            ("EUR", "Euro", "€", "Union Européenne"),
            ("CNY", "Yuan Chinois", "¥", "Chine"),
            ("AED", "Dirham Émirati", "د.إ", "Émirats Arabes Unis"),
            ("TND", "Dinar Tunisien", "د.ت", "Tunisie")
        ]

        for code, name, symbol, country in other_currencies:
            exists = session.query(Currency).filter_by(code=code).first()
            if not exists:
                # Toutes les devises sont activées par défaut
                new_curr = Currency(code=code, name=name, symbol=symbol, country=country, is_active=True)
                session.add(new_curr)
            else:
                exists.is_active = True
        
        session.flush()
        
        # 2. COMPTE PRINCIPAL
        main_account = session.query(Account).filter(Account.is_main == True).first()
        if not main_account:
            main_account = Account(
                name="Caisse Principale",
                code="MAIN_DZD",
                account_type="CAISSE",
                currency_id=da.id,
                is_main=True,
                is_active=True,
                balance=0.0,
                description="Compte principal en Dinar Algérien"
            )
            session.add(main_account)
            session.flush()
            print("✓ Compte principal créé.")

        # 3. COMPTES PARA-DEVISES (Caisses USD, EUR...)
        all_active_currencies = session.query(Currency).filter(Currency.code != DEFAULT_CURRENCY_CODE).all()
        for curr in all_active_currencies:
            acc_exists = session.query(Account).filter_by(currency_id=curr.id).first()
            if not acc_exists:
                session.add(Account(
                    name=f"Caisse {curr.code}",
                    code=f"CAISSE_{curr.code}",
                    account_type="CAISSE",
                    currency_id=curr.id,
                    is_main=False,
                    is_active=True,
                    balance=0.0,
                    description=f"Compte de caisse en {curr.name}"
                ))

        # 3.5. FOURNISSEUR DE DEVISES PAR DÉFAUT (Changeur)
        default_supplier = session.query(CurrencySupplier).filter(
            CurrencySupplier.name == "Changeur de Devises",
            CurrencySupplier.supplier_type == SUPPLIER_TYPE_CURRENCY
        ).first()
        if not default_supplier:
            default_supplier = CurrencySupplier(
                name="Changeur de Devises",
                contact="",
                phone="",
                email="",
                address="",
                balance=0.0,
                currency_id=da.id,  # Dinar Algérien uniquement
                supplier_type=SUPPLIER_TYPE_CURRENCY,
                is_active=True,
                notes="Fournisseur de devises par défaut (Changeur). Devise de traitement : Dinar Algérien (DA)."
            )
            session.add(default_supplier)
            session.flush()
            print("✓ Fournisseur de devises par défaut créé (Changeur).")
        
        # 4. TYPES DE FRAIS PAR DÉFAUT
        default_types = [
            ("Transit (Dédouanement)", True, "Frais liés au passage en douane"),
            ("Logistique / Port", True, "Frais de manutention et magasinage"),
            ("Transport / Fret", True, "Coûts de transport international"),
            ("Charges Globales", False, "Frais de fonctionnement divers")
        ]
        for name, is_direct, desc in default_types:
            exists = session.query(ExpenseType).filter_by(name=name).first()
            if not exists:
                session.add(ExpenseType(name=name, is_direct=is_direct, description=desc))
        
        # 5. ENTITÉS GÉNÉRIQUES (DIVERS)
        if not session.query(Customer).filter_by(name="C-000 | CLIENT DIVERS").first():
            session.add(Customer(name="C-000 | CLIENT DIVERS", phone="00-00-00", notes="Générique"))
        
        # 6. ENTREPÔT PRINCIPAL (المخزن الرئيسي)
        from core.models import Warehouse
        main_warehouse = session.query(Warehouse).filter(Warehouse.is_main == True).first()
        if not main_warehouse:
            main_warehouse = Warehouse(
                name="المخزن الرئيسي",
                address="",
                is_main=True,
                is_active=True,
                notes="المخزن الرئيسي الافتراضي"
            )
            session.add(main_warehouse)
            session.flush()
            print("✓ Entrepôt principal créé.")

        session.commit()
        
        # Utiliser logger au lieu de print pour éviter les erreurs Unicode
        from utils.logger import log_success
        log_success("Système prêt et synchronisé", context="INIT")
