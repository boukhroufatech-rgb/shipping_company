"""
Constantes de l'application
"""

# ============================================================================
# FORMATS DE DATE/TEMPS
# ============================================================================
DATE_FORMAT = "%d/%m/%Y"
DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"
AMOUNT_DECIMAL_PLACES = 2
AMOUNT_FORMAT_DEFAULT = "dot"  # [UNIFIED] 2026-04-08 - Default format (dot = Windows style)
CURRENCY_DECIMAL_PLACES = 4

# ============================================================================
# TYPES D'OPÉRATIONS DE TRÉSORERIE
# ============================================================================
TRANSACTION_TYPE_DEBIT = "DEBIT"
TRANSACTION_TYPE_CREDIT = "CREDIT"

# Types de comptes
ACCOUNT_TYPE_CAISSE = "CAISSE"  # Caisse
ACCOUNT_TYPE_COMPTE = "COMPTE"  # Compte bancaire
ACCOUNT_TYPE_CCP = "CCP"        # Compte CCP

# Types d'opérations de dettes externes
EXT_OP_LEND = "LEND"                     # Prêter (Sortie Caisse -> Créance)
EXT_OP_REPAY_LEND = "REPAY_LEND"         # Récupérer Prêt (Entrée Caisse -> Moins Créance)
EXT_OP_BORROW = "BORROW"                 # Emprunter (Entrée Caisse -> Dette)
EXT_OP_REPAY_BORROW = "REPAY_BORROW"     # Rembourser Emprunt (Sortie Caisse -> Moins Dette)

# Types d'opérations d'audit
AUDIT_ACTION_CREATE = "CREATE"
AUDIT_ACTION_UPDATE = "UPDATE"
AUDIT_ACTION_DELETE = "DELETE"

# Types de paiement
PAYMENT_TYPE_CASH = "CASH"
PAYMENT_TYPE_CREDIT = "CREDIT"

# Types de contacts pour dettes externes
CONTACT_TYPE_LENDER = "LENDER"  # Prêteur (nous avons emprunté)
CONTACT_TYPE_BORROWER = "BORROWER"  # Emprunteur (nous avons prêté)

# Types de fournisseurs
SUPPLIER_TYPE_CURRENCY = "CURRENCY"  # Fournisseur de devise
SUPPLIER_TYPE_LICENSE = "LICENSE"    # Titulaire de Licence
SUPPLIER_TYPE_SHIPPING = "SHIPPING"  # Agent Maritime

# Types d'opérations de prêt
LOAN_TYPE_GIVEN = "LOAN_GIVEN"  # Prêt accordé
LOAN_TYPE_RECEIVED = "LOAN_RECEIVED"  # Emprunt reçu

# Statuts de prêt
LOAN_STATUS_ACTIVE = "ACTIVE"
LOAN_STATUS_PAID = "PAID"
LOAN_STATUS_PARTIAL = "PARTIAL"

# Devise par défaut
DEFAULT_CURRENCY_CODE = "DA"
DEFAULT_CURRENCY_NAME = "Dinar Algérien"
DEFAULT_CURRENCY_SYMBOL = "DA"

# ============================================================================
# TYPES DE TRANSACTIONS POUR RENTABILITÉ (Profitability)
# ============================================================================
# [CUSTOM] Ajout pour supporter le calcul de profitabilité
# [WHY] Les opérations financières doivent être classées pour répondre à la question: "L'entreprise est-elle rentable?"
# [DATE] 2026-04-03

TRANSACTION_TYPE_REVENU = "REVENU"      # إيراد - Revenu
TRANSACTION_TYPE_EXPENSE = "EXPENSE"    # مصروف - Dépense  
TRANSACTION_TYPE_INVEST = "INVEST"      # استثمار - Investissement

# ============================================================================
# SCHEMAS CENTRALISÉS (Tree System - Root Components)
# ============================================================================
# [FIX] 2026-03-31: Déplacement des schemas ici pour éviter la duplication
# Maintenant tous les modules importent depuis ce fichier central

# ============================================================================
# MESSAGES D'ERREUR ET DE SUCCÈS
# ============================================================================

# Erreurs
ERROR_INSUFFICIENT_BALANCE = "Solde insuffisant pour cette opération"
ERROR_CANNOT_DELETE_MAIN_ACCOUNT = "Impossible de supprimer le compte principal"
ERROR_ACCOUNT_NOT_FOUND = "Compte non trouvé"
ERROR_INVALID_AMOUNT = "Montant invalide"
ERROR_INVALID_DATE = "Date invalide"
ERROR_ACCOUNT_ALREADY_EXISTS = "Un compte avec ce code existe déjà"

# Succès
SUCCESS_OPERATION_CREATED = "Opération créée avec succès"
SUCCESS_ACCOUNT_CREATED = "Compte créé avec succès"
SUCCESS_ACCOUNT_UPDATED = "Compte mis à jour avec succès"
SUCCESS_ACCOUNT_DELETED = "Compte supprimé avec succès"
SUCCESS_TRANSACTION_CREATED = "Transaction créée avec succès"
SUCCESS_TRANSFER_COMPLETED = "Transfert terminé avec succès"

# Erreurs Currency
ERROR_CANNOT_DELETE_DEFAULT_CURRENCY = "Impossible de supprimer la devise par défaut"
ERROR_CURRENCY_NOT_FOUND = "Devise non trouvée"
ERROR_INVALID_EXCHANGE_RATE = "Taux de change invalide"
SUCCESS_CURRENCY_CREATED = "Devise créée avec succès"
SUCCESS_CURRENCY_UPDATED = "Devise mise à jour avec succès"
SUCCESS_CURRENCY_DELETED = "Devise supprimée avec succès"
SUCCESS_RATE_UPDATED = "Taux de change mis à jour"

# Erreurs License
ERROR_LICENSE_NOT_FOUND = "Licence non trouvée"
ERROR_LICENSE_INSUFFICIENT_BALANCE = "Solde insuffisant dans la licence"
SUCCESS_LICENSE_CREATED = "Licence créée avec succès"

# Erreurs Logistique
ERROR_CONTAINER_NOT_FOUND = "Conteneur non trouvé"
ERROR_EXPENSE_NOT_FOUND = "Dépense non trouvée"

# Erreurs Partners
ERROR_PARTNER_NOT_FOUND = "Associé non trouvé"
ERROR_INVALID_CONTRIBUTION = "Contribution invalide"

# Erreurs External Debt
ERROR_CONTACT_NOT_FOUND = "Contact non trouvé"
ERROR_OPERATION_NOT_FOUND = "Opération non trouvée"

# ============================================================================
# CATALOGUE DES DEVISES MONDIALES
# ============================================================================
# [CUSTOM] Alias pour compatibilité - le vrai catalogue est dans currency_catalog.py
# [DATE] 2026-04-03
try:
    from utils.currency_catalog import GLOBAL_CURRENCY_CATALOG as WORLD_CURRENCIES
except ImportError:
    WORLD_CURRENCIES = []

ACCOUNT_SCHEMA = [
    {'name': 'name', 'label': 'Nom du Compte', 'type': 'text', 'required': True},
    {'name': 'code', 'label': 'Code unique', 'type': 'text', 'required': True},
    {'name': 'account_type', 'label': 'Type', 'type': 'dropdown', 'options': ["CAISSE", "BANQUE", "CCP"], 'required': True},
    {'name': 'currency_id', 'label': 'Devise', 'type': 'dropdown', 'options': [("Dinar Algérien (DA)", 1)], 'required': True},
    {'name': 'initial_balance', 'label': 'Solde Initial', 'type': 'number', 'default': 0.0},
    {'name': 'description', 'label': 'Description', 'type': 'multiline'},
]

TRANSACTION_SCHEMA = [
    {'name': 'date', 'label': 'Date', 'type': 'date', 'required': True},
    {'name': 'account_id', 'label': 'Compte', 'type': 'dropdown', 'options': [], 'required': True},
    {'name': 'type', 'label': "Type d'opération", 'type': 'dropdown', 'options': [
        ("ENTRÉE (CRÉDIT +)", TRANSACTION_TYPE_CREDIT),
        ("SORTIE (DÉBIT -)", TRANSACTION_TYPE_DEBIT)
    ], 'required': True},
    {'name': 'amount', 'label': 'Montant', 'type': 'number', 'required': True, 'validation': {'min': 0.01}},
    {'name': 'description', 'label': 'Description', 'type': 'text', 'required': True},
    {'name': 'reference', 'label': 'Référence', 'type': 'text'},
    
    # ✨ NOUVEAUX CHAMPS
    {'name': 'payment_method', 'label': 'Moyen de paiement', 'type': 'dropdown', 'options': [
        ("Espèces 💵", "ESPECES"),
        ("Chèque 📝", "CHEQUE"),
        ("Virement 🏦", "VIREMENT"),
        ("Traite", "TRAITE"),
        ("Effet", "EFFET"),
        ("Autre", "AUTRE")
    ], 'default': 'ESPECES'},
    
    {'name': 'category', 'label': 'Catégorie', 'type': 'dropdown', 'options': [
        ("Dépôt", "DEPOT"),
        ("Retrait", "RETRAIT"),
        ("Transfert", "TRANSFERT"),
        ("Paiement client", "PAIEMENT_CLIENT"),
        ("Paiement fournisseur", "PAIEMENT_FOURNISSEUR"),
        ("Frais", "FRAIS"),
        ("Divers", "DIVERS")
    ], 'default': 'DIVERS'},
    
    {'name': 'status', 'label': 'Statut', 'type': 'dropdown', 'options': [
        ("✅ Validée", "VALIDEE"),
        ("⏳ En attente", "EN_ATTENTE"),
        ("🔄 En cours", "EN_COURS"),
        ("❌ Annulée", "ANNULEE")
    ], 'default': 'VALIDEE'},
    
    {'name': 'notes', 'label': 'Observation', 'type': 'multiline'},
]
