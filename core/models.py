"""
Modèles de base de données SQLAlchemy
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, 
    ForeignKey, Text, Enum as SQLEnum, CheckConstraint, Table, Numeric
)
from sqlalchemy.orm import relationship
import enum

from .database import Base
from utils.constants import (
    TRANSACTION_TYPE_DEBIT, TRANSACTION_TYPE_CREDIT,
    AUDIT_ACTION_CREATE, AUDIT_ACTION_UPDATE, AUDIT_ACTION_DELETE,
    PAYMENT_TYPE_CASH, PAYMENT_TYPE_CREDIT,
    EXT_OP_LEND, EXT_OP_REPAY_LEND, EXT_OP_BORROW, EXT_OP_REPAY_BORROW
)


# ============================================================================
# MIXINS - Classes de base réutilisables
# ============================================================================

class TimestampMixin:
    """Mixin pour ajouter created_at et updated_at"""
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class AuditMixin(TimestampMixin):
    """Mixin pour ajouter l'audit complet"""
    created_by = Column(String(100), default="system")
    updated_by = Column(String(100), default="system")


# ============================================================================
# MODULE DEVISES (CURRENCY)
# ============================================================================

class Currency(Base, AuditMixin):
    """Modèle pour les devises"""
    __tablename__ = "currencies"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(3), unique=True, nullable=False, index=True)  # EUR, USD, DZD
    name = Column(String(100), nullable=False)  # Euro, Dollar, Dinar Algérien
    symbol = Column(String(10), nullable=False)  # €, $, DA
    is_default = Column(Boolean, default=False)  # True pour DZD
    is_deletable = Column(Boolean, default=True)  # False pour DZD
    is_active = Column(Boolean, default=True)
    country = Column(String(100)) # Facultatif pour les devises manuelles
    notes = Column(Text)
    
    # Relations
    exchange_rates = relationship("ExchangeRate", back_populates="currency", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="currency")
    purchases = relationship("CurrencyPurchase", back_populates="currency")
    
    def __repr__(self):
        return f"<Currency {self.code}>"


class ExchangeRate(Base, AuditMixin):
    """Modèle pour les taux de change"""
    __tablename__ = "exchange_rates"
    
    id = Column(Integer, primary_key=True)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)
    rate = Column(Float, nullable=False)  # Taux par rapport au DZD
    date = Column(DateTime, default=datetime.now, nullable=False)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    
    # Relations
    currency = relationship("Currency", back_populates="exchange_rates")
    
    def __repr__(self):
        return f"<ExchangeRate {self.id}: {self.rate}>"


# Table d'association: Fournisseur Licence <-> Catalogue Marchandises
supplier_license_goods = Table(
    'supplier_license_goods',
    Base.metadata,
    Column('supplier_id', Integer, ForeignKey('currency_suppliers.id'), primary_key=True),
    Column('goods_id', Integer, ForeignKey('license_goods_catalog.id'), primary_key=True)
)


class LicenseGoodsCatalog(Base, AuditMixin):
    """Catalogue des types de marchandises autorisées par les licences"""
    __tablename__ = "license_goods_catalog"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)  # ex: Chaussures, Vêtements...
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<LicenseGoodsCatalog {self.name}>"


class CurrencySupplier(Base, AuditMixin):
    """Modèle pour les fournisseurs de devises"""
    __tablename__ = "currency_suppliers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    contact = Column(String(200))
    phone = Column(String(50))
    email = Column(String(100))
    address = Column(Text)
    company_name = Column(String(300))  # Nom complet de la societe
    company_address = Column(Text)      # Adresse complete de la societe
    country = Column(String(100))       # Pays d'operation
    balance = Column(Float, default=0.0)  # Dette envers le fournisseur
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=True) # Devise de traitement
    supplier_type = Column(String(50), default="CURRENCY", nullable=False) # CURRENCY, LICENSE, SHIPPING
    # [CUSTOM] Champs spécifiques aux fournisseurs de Licences (propriétaire de licence)
    # [WHY]: Le RC et la liste de marchandises agréées sont nécessaires pour valider
    #        qu'une licence couvre bien les marchandises d'une expédition.
    # [DATE]: 2026-03-30
    commercial_register_name = Column(String(300))  # Nom du registre de commerce
    register_number = Column(String(100))            # Numéro du registre de commerce
    nif = Column(String(100))                        # NIF (Numéro d'identification fiscale)
    bank = Column(String(200))                       # Banque
    bank_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True) # Compte lié dans la trésorerie
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    
    # Relations
    currency = relationship("Currency")
    purchases = relationship("CurrencyPurchase", back_populates="supplier")
    payments = relationship("SupplierPayment", back_populates="supplier")
    license_goods_list = relationship("LicenseGoodsCatalog", secondary="supplier_license_goods", lazy="subquery")
    
    def __repr__(self):
        return f"<CurrencySupplier {self.name} - Balance: {self.balance}>"


class CurrencyPurchase(Base, AuditMixin):
    """Modèle pour les achats de devises"""
    __tablename__ = "currency_purchases"
    
    id = Column(Integer, primary_key=True)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("currency_suppliers.id"), nullable=False)
    amount = Column(Float, nullable=False)  # Montant de devise acheté
    rate = Column(Float, nullable=False)  # Taux de change appliqué
    total_dzd = Column(Float, nullable=False)  # Montant total en DZD
    discount = Column(Float, default=0.0)  # Remise en DZD
    consumed = Column(Float, default=0.0)  # Montant consommé/utilisé
    payment_type = Column(String(20), nullable=False)  # CASH ou CREDIT
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True) # Selected account for cash purchases
    date = Column(DateTime, default=datetime.now, nullable=False)
    reference = Column(String(100))
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Relations
    currency = relationship("Currency", back_populates="purchases")
    supplier = relationship("CurrencySupplier", back_populates="purchases")
    account = relationship("Account")
    
    __table_args__ = (
        CheckConstraint(f"payment_type IN ('{PAYMENT_TYPE_CASH}', '{PAYMENT_TYPE_CREDIT}')"),
    )
    
    def __repr__(self):
        return f"<CurrencyPurchase {self.id} Amount: {self.amount}>"


class SupplierPayment(Base, AuditMixin):
    """Modèle pour les paiements aux fournisseurs de devises"""
    __tablename__ = "supplier_payments"
    
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("currency_suppliers.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.now, nullable=False)
    reference = Column(String(100))
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Relations
    supplier = relationship("CurrencySupplier", back_populates="payments")
    account = relationship("Account", back_populates="supplier_payments")
    
    def __repr__(self):
        return f"<SupplierPayment ID: {self.id} Amount: {self.amount}>"


# ============================================================================
# MODULE TRÉSORERIE (TREASURY)
# ============================================================================

class TreasuryAccountType(Base, AuditMixin):
    """Catalogue dynamique pour les types de comptes (CAISSE, COMPTE, CCP, etc.)"""
    __tablename__ = "treasury_account_types"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    is_fixed = Column(Boolean, default=False)  # True = Ne peut pas être supprimé (valeurs par défaut)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<TreasuryAccountType {self.name}>"


class Account(Base, AuditMixin):
    """Modèle pour les comptes de trésorerie"""
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    account_type = Column(String(100), nullable=False)  # Pointe vers le nom (ou id) du type
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)
    balance = Column(Float, default=0.0, nullable=False)
    initial_balance = Column(Float, default=0.0, nullable=False)  # Solde initial
    is_main = Column(Boolean, default=False)  # Compte principal (non supprimable)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    description = Column(Text)
    
    # Relations
    currency = relationship("Currency", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    supplier_payments = relationship("SupplierPayment", back_populates="account")
    
    # CheckConstraint retiré pour permettre le catalogue dynamique
    # __table_args__ = ()
    
    def __repr__(self):
        return f"<Account {self.code} - {self.name}: {self.balance}>"


class Transaction(Base, AuditMixin):
    """Modèle pour les opérations de trésorerie"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    type = Column(String(20), nullable=False)  # DEBIT ou CREDIT
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    reference = Column(String(100))
    date = Column(DateTime, default=datetime.now, nullable=False)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    
    # ✨ NOUVEAUX CHAMPS - Gestion avancée des transactions
    source = Column(String(50), default="CAISSE", nullable=False)  # Source: CAISSE, CLIENT, FOURNISSEUR, DEVISE, PARTNER
    source_id = Column(Integer, nullable=True)  # ID de l'opération dans le module source
    payment_method = Column(String(50), default="ESPECES")  # ESPECES, CHEQUE, VIREMENT, TRAITE, EFFET
    category = Column(String(50), default="DIVERS")  # DEPOT, RETRAIT, TRANSFERT, PAIEMENT_CLIENT, etc.
    status = Column(String(20), default="VALIDEE")  # VALIDEE, EN_ATTENTE, ANNULEE, EN_COURS
    created_by = Column(String(100), default="system")  # Utilisateur qui a créé l'opération

    # Relations
    account = relationship("Account", back_populates="transactions")
    audits = relationship("TransactionAudit", back_populates="transaction", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(f"type IN ('{TRANSACTION_TYPE_DEBIT}', '{TRANSACTION_TYPE_CREDIT}')"),
        CheckConstraint("amount > 0"),
        CheckConstraint(f"source IN ('CAISSE', 'CLIENT', 'FOURNISSEUR', 'DEVISE', 'PARTNER', 'EXPENSE')"),
        CheckConstraint(f"payment_method IN ('ESPECES', 'CHEQUE', 'VIREMENT', 'TRAITE', 'EFFET', 'AUTRE')"),
        CheckConstraint(f"status IN ('VALIDEE', 'EN_ATTENTE', 'ANNULEE', 'EN_COURS')"),
    )

    def __repr__(self):
        return f"<Transaction {self.type} {self.amount} - {self.description} ({self.source})>"


class TransactionAudit(Base, TimestampMixin):
    """Modèle pour l'audit des transactions"""
    __tablename__ = "transaction_audits"
    
    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    action = Column(String(20), nullable=False)  # CREATE, UPDATE, DELETE
    user = Column(String(100), default="system")
    old_data = Column(Text)  # JSON des anciennes données
    new_data = Column(Text)  # JSON des nouvelles données
    notes = Column(Text)
    
    # Relations
    transaction = relationship("Transaction", back_populates="audits")
    
    __table_args__ = (
        CheckConstraint(f"action IN ('{AUDIT_ACTION_CREATE}', '{AUDIT_ACTION_UPDATE}', '{AUDIT_ACTION_DELETE}')"),
    )
    
    def __repr__(self):
        return f"<TransactionAudit {self.action} by {self.user}>"


# ============================================================================
# MODULE DETTES EXTERNES (EXTERNAL DEBT)
# ============================================================================

class ExternalContact(Base, AuditMixin):
    """Modèle pour les contacts externes (Particuliers/Entités)"""
    __tablename__ = "external_contacts"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(50))
    email = Column(String(100))
    address = Column(Text)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    
    # Relations
    transactions = relationship("ExternalTransaction", back_populates="contact", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ExternalContact {self.name}>"


class ExternalTransaction(Base, AuditMixin):
    """Modèle pour les transactions de dettes (Prêts/Emprunts)"""
    __tablename__ = "external_transactions"

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey("external_contacts.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)
    type = Column(String(20), nullable=False)  # LEND, BORROW, REPAY...
    amount = Column(Float, nullable=False)  # Montant original dans la devise du compte
    
    # [NEW] 2026-04-05 - Champs pour la conversion en DA
    exchange_rate = Column(Float, default=1.0)  # Taux de change utilisé (1 USD = X DA)
    amount_da = Column(Float, nullable=False)  # Montant converti en DA (amount * exchange_rate)
    
    date = Column(DateTime, default=datetime.now, nullable=False)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)

    # Relations
    contact = relationship("ExternalContact", back_populates="transactions")
    account = relationship("Account")
    currency = relationship("Currency")

    __table_args__ = (
        CheckConstraint(f"type IN ('{EXT_OP_LEND}', '{EXT_OP_REPAY_LEND}', '{EXT_OP_BORROW}', '{EXT_OP_REPAY_BORROW}')"),
        CheckConstraint("amount > 0"),
    )

    def __repr__(self):
        return f"<ExternalTransaction {self.type} {self.amount} {self.currency.code if self.currency else ''}>"


# ============================================================================
# MODULE LOGISTIQUE (LOGISTICS)
# ============================================================================

class ImportLicense(Base, AuditMixin):
    """Modèle pour les licences/traitements d'importation"""
    __tablename__ = "import_licenses"
    
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("currency_suppliers.id"), nullable=False)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)
    total_usd = Column(Float, nullable=False)
    used_usd = Column(Float, default=0.0)
    rate = Column(Float, nullable=False)  # Taux d'achat (DZD/USD)
    total_dzd = Column(Float, nullable=False)
    commission_rate = Column(Float, default=0.0)  # % de commission sur la jumerka
    license_type = Column(String(100)) # e.g., Shoes, Clothes, etc.
    is_debt_generated = Column(Boolean, default=False)
    date = Column(DateTime, default=datetime.now, nullable=False)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # [NEW] Paiement au transporteur (Shipping Agent)
    shipping_supplier_id = Column(Integer, ForeignKey("currency_suppliers.id"), nullable=True)  # Agent de transport
    shipping_rate = Column(Float, nullable=True)  # Taux de change du agent
    shipping_amount_usd = Column(Float, default=0.0)  # Montant USD payé au transporteur
    payment_status = Column(String(20), default="EN_ATTENTE")  # EN_ATTENTE, PAYE, PARTIEL
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)  # Compte utilisé pour le paiement
    
    # [NEW] Financial totals for license tracking
    total_domiciliations = Column(Float, default=0.0)  # Total Domiciliations
    total_taxes = Column(Float, default=0.0)  # Total Taxs
    total_versements = Column(Float, default=0.0)  # Total Versements
    total_du = Column(Float, default=0.0)  # Total Dû
    
    # Relations
    supplier = relationship("CurrencySupplier", foreign_keys=[supplier_id])
    shipping_supplier = relationship("CurrencySupplier", foreign_keys=[shipping_supplier_id])
    currency = relationship("Currency")
    account = relationship("Account")
    containers = relationship("ContainerFile", back_populates="license")
    
    __table_args__ = (
        CheckConstraint(f"payment_status IN ('EN_ATTENTE', 'PAYE', 'PARTIEL')"),
    )
    
    def __repr__(self):
        return f"<ImportLicense {self.total_usd} USD from {self.supplier.name if self.supplier else 'N/A'}>"


class ContainerFile(Base, AuditMixin):
    """Modèle pour les dossiers de conteneurs"""
    __tablename__ = "container_files"
    
    id = Column(Integer, primary_key=True)
    license_id = Column(Integer, ForeignKey("import_licenses.id"), nullable=False)
    shipping_supplier_id = Column(Integer, ForeignKey("currency_suppliers.id"), nullable=True)
    container_number = Column(String(100), nullable=False)
    bill_number = Column(String(100))
    shipment_type = Column(String(50), default="MARITIME")  # MARITIME, TERRESTRIAL, AERIAL
    products_type = Column(String(200)) # Type de produits
    used_usd_amount = Column(Float, nullable=False) # Part du traitement utilisé
    customs_value_dzd = Column(Float, default=0.0) # Valeur de jumerka
    commission_dzd = Column(Float, default=0.0) # Commission calculée
    discharge_port = Column(String(100)) # Port de déchargement
    shipping_date = Column(DateTime)
    expected_arrival_date = Column(DateTime)
    status = Column(String(20), default="OPEN") # OPEN, CLOSED
    date_opened = Column(DateTime, default=datetime.now, nullable=False)
    date_closed = Column(DateTime)
    
    # Nouveaux champs pour la refonte "Open Bill"
    invoice_number = Column(String(100)) # N° Facture
    cbm = Column(Float, default=0.0) # Total CBM
    cartons = Column(Integer, default=0) # Nombre de cartons
    transitaire = Column(String(200)) # Nom du déclarant/transitaire
    taux = Column(Float, default=0.0) # Taux de change
    taux_expedition = Column(Float, default=0.0) # Taux de change expedition
    equivalent_dzd = Column(Float, default=0.0) # Equivalent en DZD
    equivalent_expedition = Column(Float, default=0.0) # Equivalent expedition (Montant × Taux expedition)
    
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Warehouse Integration - ربط المخازن
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)  # المخزن
    warehouse_status = Column(String(20), default="PENDING")  # PENDING, RECEIVED, PARTIAL, DELIVERED
    warehouse_received_date = Column(DateTime)  # تاريخ الاستلام في المخزن
    warehouse_notes = Column(Text)  # ملاحظات المخزن
    
    # Additional charges fields - champs supplémentaires pour les charges
    shipping_cost = Column(Float, default=0.0)  # Shipping
    licence_fee = Column(Float, default=0.0)  # Licence
    tax_amount = Column(Float, default=0.0)  # Tax
    charge_percentage = Column(Float, default=0.0)  # Percentage
    charge_da = Column(Float, default=0.0)  # Charge DA
    charge_port = Column(Float, default=0.0)  # Charge Port
    surestarie = Column(Float, default=0.0)  # Surestarie
    
    # Relations
    license = relationship("ImportLicense", back_populates="containers")
    shipping_supplier = relationship("CurrencySupplier")
    expenses = relationship("ContainerExpense", back_populates="container", cascade="all, delete-orphan")
    warehouse = relationship("Warehouse", back_populates="containers")
    
    def __repr__(self):
        return f"<ContainerFile {self.container_number} - Status: {self.status}>"


class ContainerExpense(Base, AuditMixin):
    """Modèle pour les frais directs sur un conteneur"""
    __tablename__ = "container_expenses"
    
    id = Column(Integer, primary_key=True)
    container_id = Column(Integer, ForeignKey("container_files.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String(200), nullable=False)
    date = Column(DateTime, default=datetime.now, nullable=False)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    
    # Relations
    container = relationship("ContainerFile", back_populates="expenses")
    account = relationship("Account")
    
    def __repr__(self):
        return f"<ContainerExpense {self.amount} for {self.container.container_number if self.container else 'N/A'}>"


class ExpenseType(Base, AuditMixin):
    """Modèle pour les types de frais (Transit, Port, etc.)"""
    __tablename__ = "expense_types"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    is_direct = Column(Boolean, default=True) # Moteur (Direct) ou Global (Indirect)
    description = Column(String(255))
    sort_order = Column(Integer, default=0)  # For ordering items in list
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    
    def __repr__(self):
        return f"<ExpenseType {self.name}>"


class Expense(Base, AuditMixin):
    """Modèle pour les dépenses réelles"""
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True)
    expense_type_id = Column(Integer, ForeignKey("expense_types.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)  # Client associe
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True) # Null si CREDIT
    supplier_id = Column(Integer, ForeignKey("currency_suppliers.id"), nullable=True) # Si CREDIT
    
    # Liens optionnels
    container_id = Column(Integer, ForeignKey("container_files.id"), nullable=True)
    license_id = Column(Integer, ForeignKey("import_licenses.id"), nullable=True)
    
    amount = Column(Float, nullable=False)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)
    rate = Column(Float, default=1.0)
    total_dzd = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)  # عمولة إضافية (أمانة/سمسرة)
    lot_id = Column(Integer, ForeignKey("currency_purchases.id"), nullable=True)  # ربط بـ LOT عند صرف عملة أجنبية

    payment_type = Column(String(20), default="CASH") # CASH, CREDIT
    date = Column(DateTime, default=datetime.now, nullable=False)
    reference = Column(String(100))
    notes = Column(Text)
    is_active = Column(Boolean, default=True)

    # Relations
    expense_type = relationship("ExpenseType")
    customer = relationship("Customer")
    account = relationship("Account")
    supplier = relationship("CurrencySupplier")
    container = relationship("ContainerFile")
    license = relationship("ImportLicense")
    currency = relationship("Currency")
    lot = relationship("CurrencyPurchase")
    
    def __repr__(self):
        return f"<Expense {self.amount} - {self.payment_type}>"


class AppSetting(Base):
    """Modèle pour les réglages de l'application"""
    __tablename__ = "app_settings"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    description = Column(String(255))
    category = Column(String(50)) # COMPANY, FINANCE, SYSTEM
    
    def __repr__(self):
        return f"<AppSetting {self.key}={self.value}>"

# ============================================================================
# MODULE PARTENAIRES (PARTNERS)
# ============================================================================

class Partner(Base, AuditMixin):
    """Modèle pour les associés/actionnaires"""
    __tablename__ = "partners"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(50))
    email = Column(String(100))
    function = Column(String(100))
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    
    # Relations
    transactions = relationship("PartnerTransaction", back_populates="partner", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Partner {self.name}>"


class PartnerTransaction(Base, AuditMixin):
    """Modèle pour les opérations des associés (Apport, Retrait, Profit)"""
    __tablename__ = "partner_transactions"
    
    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    type = Column(String(20), nullable=False)  # CONTRIBUTION, WITHDRAWAL, PROFIT_ALLOCATION
    amount = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.now, nullable=False)
    
    # Lien optionnel avec la trésorerie (pour contribution/retrait)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Relations
    partner = relationship("Partner", back_populates="transactions")
    treasury_transaction = relationship("Transaction")
    
    __table_args__ = (
        CheckConstraint("type IN ('CONTRIBUTION', 'WITHDRAWAL', 'PROFIT_ALLOCATION')"),
        CheckConstraint("amount > 0"),
    )
    
    def __repr__(self):
        return f"<PartnerTransaction {self.type} {self.amount}>"


# ============================================================================
# MODULE CLIENTS (CUSTOMERS)
# ============================================================================

class Customer(Base, AuditMixin):
    """Fiche client"""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(50))
    address = Column(Text)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    initial_balance = Column(Numeric(15, 2), default=0)  # Solde initial

    # Relations
    goods = relationship("CustomerGoods", back_populates="customer", cascade="all, delete-orphan")
    payments = relationship("CustomerPayment", back_populates="customer", cascade="all, delete-orphan")
    side_costs = relationship("CustomerSideCost", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer {self.name}>"


class SideCostType(Base, AuditMixin):
    """Types de frais annexes réutilisables (ex: Livraison, Déchargement...)"""
    __tablename__ = "side_cost_types"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)

    # Relations
    side_costs = relationship("CustomerSideCost", back_populates="cost_type")

    def __repr__(self):
        return f"<SideCostType {self.name}>"


class CustomerGoods(Base, AuditMixin):
    """Marchandises d'un client dans un conteneur"""
    __tablename__ = "customer_goods"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    container_id = Column(Integer, ForeignKey("container_files.id"), nullable=False)
    goods_type = Column(String(200), nullable=False)  # Type de marchandise
    cartons = Column(Integer, default=0)
    cbm = Column(Float, default=0.0)
    cbm_price_dzd = Column(Float, default=0.0)  # Prix par CBM en DZD
    cbm_price_usd = Column(Float, default=0.0)  # Prix par CBM en USD
    discount = Column(Float, default=0.0)  # Remise en %
    discount_usd = Column(Float, default=0.0)  # Remise en USD
    notes = Column(Text)
    date = Column(DateTime, default=datetime.now, nullable=False)
    is_active = Column(Boolean, default=True)

    # Relations
    customer = relationship("Customer", back_populates="goods")
    container = relationship("ContainerFile")

    @property
    def total_brut(self):
        return self.cbm * self.cbm_price_dzd

    @property
    def discount_amount(self):
        return self.total_brut * (self.discount / 100)

    @property
    def total_net(self):
        return self.total_brut - self.discount_amount

    def __repr__(self):
        return f"<CustomerGoods {self.customer.name if self.customer else '?'} - {self.goods_type}>"


class CustomerPayment(Base, AuditMixin):
    """Paiement reçu d'un client → crédite un compte de trésorerie"""
    __tablename__ = "customer_payments"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)  # Lien trésorerie
    amount = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.now, nullable=False)
    reference = Column(String(100))
    notes = Column(Text)
    is_active = Column(Boolean, default=True)

    # Relations
    customer = relationship("Customer", back_populates="payments")
    account = relationship("Account")
    treasury_transaction = relationship("Transaction")

    def __repr__(self):
        return f"<CustomerPayment {self.amount} DA from {self.customer.name if self.customer else '?'}>"


class CustomerSideCost(Base, AuditMixin):
    """Frais annexes facturés à un client (s'ajoutent à sa dette)"""
    __tablename__ = "customer_side_costs"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    cost_type_id = Column(Integer, ForeignKey("side_cost_types.id"), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.now, nullable=False)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)

    # Relations
    customer = relationship("Customer", back_populates="side_costs")
    cost_type = relationship("SideCostType", back_populates="side_costs")

    def __repr__(self):
        return f"<CustomerSideCost {self.cost_type.name if self.cost_type else '?'} - {self.amount} DA>"


# ============================================================================
# WAREHOUSE MODELS - نظام إدارة المخازن
# ============================================================================

class Warehouse(Base, AuditMixin):
    """المخازن - Warehouse Management"""
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)  # اسم المخزن
    address = Column(Text)  # العنوان
    is_main = Column(Boolean, default=False, nullable=False)  # مخزن رئيسي؟
    is_active = Column(Boolean, default=True)
    notes = Column(Text)

    # Relations
    stocks = relationship("WarehouseStock", back_populates="warehouse", cascade="all, delete-orphan")
    movements = relationship("WarehouseMovement", back_populates="warehouse", cascade="all, delete-orphan")
    containers = relationship("ContainerFile", back_populates="warehouse")

    def __repr__(self):
        return f"<Warehouse {self.name}>"


class WarehouseStock(Base, AuditMixin):
    """بضاعة العميل في المخزن - Customer goods in warehouse"""
    __tablename__ = "warehouse_stocks"

    id = Column(Integer, primary_key=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    container_id = Column(Integer, ForeignKey("container_files.id"), nullable=True)  # الحاوية
    goods_type = Column(String(200))  # نوع البضاعة
    quantity = Column(Integer, default=0)  # الكمية
    weight = Column(Float, default=0.0)  # الوزن (كغ)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)

    # Relations
    warehouse = relationship("Warehouse", back_populates="stocks")
    customer = relationship("Customer")
    container = relationship("ContainerFile")

    def __repr__(self):
        return f"<WarehouseStock {self.customer.name if self.customer else '?'} - {self.goods_type}>"


class WarehouseMovement(Base, AuditMixin):
    """حركات المخزن - Warehouse movements (استلام/تسليم/تحويل)"""
    __tablename__ = "warehouse_movements"

    id = Column(Integer, primary_key=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    container_id = Column(Integer, ForeignKey("container_files.id"), nullable=True)
    
    movement_type = Column(String(50), nullable=False)  # RECEIVE, DELIVER, TRANSFER
    quantity = Column(Integer, default=0)
    weight = Column(Float, default=0.0)
    notes = Column(Text)
    date = Column(DateTime, default=datetime.now, nullable=False)
    is_active = Column(Boolean, default=True)

    # Relations
    warehouse = relationship("Warehouse", back_populates="movements")
    customer = relationship("Customer")
    container = relationship("ContainerFile")

    def __repr__(self):
        return f"<WarehouseMovement {self.movement_type}>"


class Port(Base, AuditMixin):
    """Modèle pour les ports et destinations"""
    __tablename__ = "ports"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    country = Column(String(100), nullable=True)
    port_type = Column(String(50), default="AUTRE")  # EXPORT, IMPORT, TRANSIT, AUTRE
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Port {self.name}>"


class ContainerType(Base, AuditMixin):
    """Modèle pour les types de conteneurs"""
    __tablename__ = "container_types"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False, unique=True)  # ex: 20', 40'HC
    capacity_cbm = Column(Float, default=0.0)  # Capacité indicative
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<ContainerType {self.code}>"


class Transitaire(Base, AuditMixin):
    """Modèle pour les transitaires (Agents de douane)"""
    __tablename__ = "transitaires"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    contact = Column(String(200))
    phone = Column(String(50))
    email = Column(String(100))
    nif_rc = Column(String(100))  # NIF ou RC
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Transitaire {self.name}>"
