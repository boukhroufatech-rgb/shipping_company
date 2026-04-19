"""
Définitions centralisées des colonnes de tous les tableaux du programme.

SOURCE UNIQUE DE VÉRITÉ (Single Source of Truth):
  - Noms et labels des colonnes
  - Types de données: text | number | amount | date | status | percentage
  - Alignement (align: left | center | right)
  - Largeur par défaut
  - Colonnes sommables (sum: True)
  - Colonnes cachées (hidden: True)

RÈGLE D'OR:
  Chaque table du programme DOIT avoir son schéma ici.
  EnhancedTableView lit ce fichier pour le formatage, le footer, et l'alignement.
"""

# ============================================================================
# LOGISTICS SECTION
# ============================================================================

AGENTS_MARITIMES_COLUMNS = [
    {"name": "n",                  "label": "N°",                    "type": "number",     "width": 50,  "align": "center"},
    {"name": "id",                 "label": "ID",                    "type": "number",     "width": 60,  "hidden": True},
    {"name": "agent_name",         "label": "Agent",                 "type": "text",       "width": 180},
    {"name": "country",            "label": "Pays",                  "type": "text",       "width": 100},
    {"name": "chiffre_affaire",    "label": "Chiffre d'affaires (DA)","type": "amount",    "width": 150, "align": "right", "sum": True},
    {"name": "shipments",          "label": "Nb Factures",           "type": "number",     "width": 120, "align": "center", "sum": "count"},
    {"name": "containers",         "label": "Nb Conteneurs",         "type": "number",     "width": 120, "align": "center", "sum": "count"},
    {"name": "payments_received",  "label": "Paiements (DA)",        "type": "amount",     "width": 150, "align": "right", "sum": True},
    {"name": "amount_due",         "label": "Dû (DA)",               "type": "amount",     "width": 150, "align": "right", "sum": True},
    {"name": "pending_payments",   "label": "En attente (DA)",       "type": "amount",     "width": 150, "align": "right", "sum": True},
    {"name": "balance",            "label": "Solde (DA)",            "type": "amount",     "width": 150, "align": "right", "sum": True},
    {"name": "collection_rate",    "label": "Taux Recouvrement (%)", "type": "percentage", "width": 130, "align": "center", "avg": True},
    {"name": "currency",           "label": "Devise",                "type": "text",       "width": 80,  "align": "center"},
    {"name": "address",            "label": "Adresse",               "type": "text",       "width": 200},
]

AGENT_PAYMENTS_COLUMNS = [
    {"name": "n",         "label": "N°",        "type": "number", "width": 50,  "align": "center"},
    {"name": "id",        "label": "ID",        "type": "number", "width": 60,  "hidden": True},
    {"name": "date",      "label": "Date",      "type": "date",   "width": 100, "align": "center"},
    {"name": "agent",     "label": "Agent",     "type": "text",   "width": 150},
    {"name": "type",      "label": "Type",      "type": "text",   "width": 100, "align": "center"},
    {"name": "amount",    "label": "Montant",   "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "status",    "label": "Statut",    "type": "status", "width": 100, "align": "center"},
    {"name": "currency",  "label": "Devise",    "type": "text",   "width": 80,  "align": "center"},
    {"name": "account",   "label": "Compte",    "type": "text",   "width": 150},
    {"name": "bill",      "label": "Facture",   "type": "text",   "width": 100, "align": "center"},
    {"name": "reference", "label": "Référence", "type": "text",   "width": 120},
    {"name": "notes",     "label": "Notes",     "type": "text",   "width": 150},
]

CONTAINERS_COLUMNS = [
    {"name": "n",                    "label": "N°",               "type": "number",     "width": 50,  "align": "center"},
    {"name": "id",                   "label": "ID",               "type": "number",     "width": 60,  "hidden": True},
    {"name": "date",                 "label": "Date",             "type": "date",       "width": 100, "align": "center"},
    {"name": "bill",                 "label": "N° BILL",          "type": "text",       "width": 100, "align": "center"},
    {"name": "invoice",              "label": "Facture",          "type": "text",       "width": 100, "align": "center"},
    {"name": "agent",                "label": "Agent",            "type": "text",       "width": 150},
    {"name": "customers_count",      "label": "Clients",          "type": "number",     "width": 80,  "align": "center"},
    {"name": "containers_count",     "label": "Conteneurs",       "type": "number",     "width": 80,  "align": "center"},
    {"name": "cbm",                  "label": "CBM",              "type": "amount",     "width": 100, "align": "right"},
    {"name": "cartons",              "label": "Cartons",          "type": "number",     "width": 100, "align": "center"},
    {"name": "amount_usd",           "label": "Montant ($)",      "type": "amount",     "width": 120, "align": "right", "sum": True},
    {"name": "taux",                 "label": "Taux",             "type": "amount",     "width": 100, "align": "right"},
    {"name": "equivalent_dzd",       "label": "Équivalent (DA)",  "type": "amount",     "width": 130, "align": "right", "sum": True},
    {"name": "taux_expedition",      "label": "Taux Expédition",  "type": "amount",     "width": 120, "align": "right"},
    {"name": "equivalent_expedition","label": "Revenus (DA)",     "type": "amount",     "width": 130, "align": "right", "sum": True},
    {"name": "port",                 "label": "Port",             "type": "text",       "width": 100},
    {"name": "transitaire",          "label": "Transitaire",      "type": "text",       "width": 100},
    {"name": "shipping",             "label": "Expédition (DA)",  "type": "amount",     "width": 130, "align": "right", "sum": True},
    {"name": "tax",                  "label": "Taxe (DA)",        "type": "amount",     "width": 130, "align": "right", "sum": True},
    {"name": "commission",           "label": "Commission (%)",   "type": "percentage", "width": 110, "align": "center"},
    {"name": "charge_da",            "label": "Frais (DA)",       "type": "amount",     "width": 130, "align": "right", "sum": True},
    {"name": "charge_port",          "label": "Frais Port",       "type": "amount",     "width": 130, "align": "right", "sum": True},
    {"name": "surestarie",           "label": "Surestarie",       "type": "amount",     "width": 130, "align": "right", "sum": True},
    {"name": "total_costs",          "label": "Coûts Total",      "type": "amount",     "width": 150, "align": "right", "sum": True},
    {"name": "revenue",              "label": "Revenus (DA)",     "type": "amount",     "width": 150, "align": "right", "sum": True},
    {"name": "profit",               "label": "Bénéfice (DA)",    "type": "amount",     "width": 150, "align": "right", "sum": True},
]

LOGISTICS_EXPENSES_COLUMNS = [
    {"name": "n",          "label": "N°",          "type": "number", "width": 50,  "align": "center"},
    {"name": "id",         "label": "ID",          "type": "number", "width": 60,  "hidden": True},
    {"name": "date",       "label": "Date",        "type": "date",   "width": 100, "align": "center"},
    {"name": "client",     "label": "Client",      "type": "text",   "width": 150},
    {"name": "type",       "label": "Type Frais",  "type": "text",   "width": 150},
    {"name": "amount",     "label": "Montant (DA)","type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "reference",  "label": "Référence",   "type": "text",   "width": 120},
    {"name": "notes",      "label": "Notes",       "type": "text",   "width": 200},
]

WIZARD_CONTAINERS_COLUMNS = [
    {"name": "n",                "label": "N°",           "type": "number", "width": 50, "align": "center"},
    {"name": "container_number", "label": "N° Conteneur", "type": "text",   "width": 150},
    {"name": "goods",            "label": "Marchandise",  "type": "text",   "width": 200},
    {"name": "action",           "label": "",             "type": "text",   "width": 80},
]

WIZARD_GOODS_COLUMNS = [
    {"name": "n",          "label": "N°",               "type": "number", "width": 50,  "align": "center"},
    {"name": "customer",   "label": "Client",            "type": "text",   "width": 150},
    {"name": "goods_type", "label": "Type Marchandise",  "type": "text",   "width": 150},
    {"name": "quantity",   "label": "Quantité",          "type": "number", "width": 100, "align": "center"},
    {"name": "cbm",        "label": "CBM",               "type": "amount", "width": 100, "align": "right"},
    {"name": "unit_price", "label": "Prix Unitaire (DA)","type": "amount", "width": 120, "align": "right"},
    {"name": "discount",   "label": "Remise (DA)",       "type": "amount", "width": 120, "align": "right"},
    {"name": "total",      "label": "Total (DA)",        "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "action",     "label": "",                  "type": "text",   "width": 80},
]

# ============================================================================
# CURRENCY SECTION
# ============================================================================

CURRENCY_SUMMARY_COLUMNS = [
    {"name": "n",               "label": "N°",                  "type": "number", "width": 50,  "align": "center"},
    {"name": "code",            "label": "Devise",              "type": "text",   "width": 80,  "align": "center"},
    {"name": "name",            "label": "Nom",                 "type": "text",   "width": 150},
    {"name": "account_name",    "label": "Compte Trésorerie",   "type": "text",   "width": 150},
    {"name": "total_purchased", "label": "Total Acheté (+)",    "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "total_consumed",  "label": "Total Consommé (-)",  "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "balance",         "label": "Solde Actuel",        "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "total_value_dzd", "label": "Valeur Totale (DA)",  "type": "amount", "width": 150, "align": "right", "sum": True},
    {"name": "balance_dzd",     "label": "Solde en DA",         "type": "amount", "width": 130, "align": "right", "sum": True},
]

SUPPLIER_PAYMENTS_COLUMNS = [
    {"name": "n",           "label": "N°",            "type": "number", "width": 50,  "align": "center"},
    {"name": "id",          "label": "ID",            "type": "number", "width": 60,  "hidden": True},
    {"name": "date",        "label": "Date",          "type": "date",   "width": 100, "align": "center"},
    {"name": "supplier",    "label": "Fournisseur",   "type": "text",   "width": 150},
    {"name": "amount",      "label": "Montant Payé",  "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "account",     "label": "Caisse Source", "type": "text",   "width": 120},
    {"name": "reference",   "label": "Référence",     "type": "text",   "width": 120},
]

CURRENCY_PURCHASES_COLUMNS = [
    {"name": "n",            "label": "N°",             "type": "number", "width": 50,  "align": "center"},
    {"name": "id",           "label": "ID",             "type": "number", "width": 60,  "hidden": True},
    {"name": "date",         "label": "Date",           "type": "date",   "width": 100, "align": "center"},
    {"name": "currency",     "label": "Devise",         "type": "text",   "width": 100, "align": "center"},
    {"name": "supplier",     "label": "Fournisseur",    "type": "text",   "width": 150},
    {"name": "amount",       "label": "Montant Devise", "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "rate",         "label": "Taux Change",    "type": "amount", "width": 120, "align": "right"},
    {"name": "total_da",     "label": "Total DA",       "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "consumed",     "label": "Consommée",      "type": "amount", "width": 120, "align": "right"},
    {"name": "balance",      "label": "Solde",          "type": "amount", "width": 120, "align": "right", "sum": True},
    {"name": "payment_type", "label": "Paiement",       "type": "text",   "width": 100, "align": "center"},
    {"name": "reference",    "label": "Référence",      "type": "text",   "width": 120},
]

SUPPLIERS_COLUMNS = [
    {"name": "n",       "label": "N°",           "type": "number", "width": 50,  "align": "center"},
    {"name": "id",      "label": "ID",           "type": "number", "width": 60,  "hidden": True},
    {"name": "name",    "label": "Nom",          "type": "text",   "width": 200},
    {"name": "type",    "label": "Type",         "type": "text",   "width": 120, "align": "center"},
    {"name": "contact", "label": "Contact",      "type": "text",   "width": 150},
    {"name": "phone",   "label": "Téléphone",    "type": "text",   "width": 130, "align": "center"},
    {"name": "balance", "label": "Solde (DA)",   "type": "amount", "width": 130, "align": "right", "sum": True},
]

# ============================================================================
# CUSTOMERS SECTION
# ============================================================================

CUSTOMER_LIST_COLUMNS = [
    {"name": "n",               "label": "N°",              "type": "number", "width": 50,  "align": "center"},
    {"name": "id",              "label": "ID",              "type": "number", "width": 60,  "hidden": True},
    {"name": "name",            "label": "Nom du Client",   "type": "text",   "width": 200},
    {"name": "phone",           "label": "Téléphone",       "type": "text",   "width": 130, "align": "center"},
    {"name": "address",         "label": "Adresse",         "type": "text",   "width": 200},
    {"name": "initial_balance", "label": "Solde Initial",   "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "business_number", "label": "N° Affaires",     "type": "number", "width": 100, "align": "center"},
    {"name": "fees",            "label": "Frais (DA)",      "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "discounts",       "label": "Réductions (DA)", "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "payments",        "label": "Paiements (DA)",  "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "external_debt",   "label": "Dette Externe",   "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "current_balance", "label": "Solde Actuel (DA)","type": "amount","width": 130, "align": "right", "sum": True},
    {"name": "notes",           "label": "Notes",           "type": "text",   "width": 200},
]

CUSTOMER_GOODS_COLUMNS = [
    {"name": "n",           "label": "N°",          "type": "number", "width": 50,  "align": "center"},
    {"name": "id",          "label": "ID",          "type": "number", "width": 60,  "hidden": True},
    {"name": "date",        "label": "Date",        "type": "date",   "width": 100, "align": "center"},
    {"name": "customer",    "label": "Client",      "type": "text",   "width": 150},
    {"name": "container",   "label": "Conteneur",   "type": "text",   "width": 120, "align": "center"},
    {"name": "goods_type",  "label": "Type",        "type": "text",   "width": 150},
    {"name": "cartons",     "label": "Cartons",     "type": "number", "width": 100, "align": "center"},
    {"name": "cbm",         "label": "CBM",         "type": "amount", "width": 100, "align": "right"},
    {"name": "unit_price",  "label": "P.U (DA)",    "type": "amount", "width": 120, "align": "right"},
    {"name": "total_price", "label": "Total (DA)",  "type": "amount", "width": 130, "align": "right", "sum": True},
]

CUSTOMER_PAYMENTS_COLUMNS = [
    {"name": "n",          "label": "N°",           "type": "number", "width": 50,  "align": "center"},
    {"name": "id",         "label": "ID",           "type": "number", "width": 60,  "hidden": True},
    {"name": "date",       "label": "Date",         "type": "date",   "width": 100, "align": "center"},
    {"name": "customer",   "label": "Client",       "type": "text",   "width": 150},
    {"name": "account",    "label": "Compte",       "type": "text",   "width": 120},
    {"name": "amount",     "label": "Montant (DA)", "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "reference",  "label": "Réf",          "type": "text",   "width": 120},
    {"name": "notes",      "label": "Notes",        "type": "text",   "width": 200},
]

CUSTOMER_COSTS_COLUMNS = [
    {"name": "n",          "label": "N°",           "type": "number", "width": 50,  "align": "center"},
    {"name": "id",         "label": "ID",           "type": "number", "width": 60,  "hidden": True},
    {"name": "date",       "label": "Date",         "type": "date",   "width": 100, "align": "center"},
    {"name": "customer",   "label": "Client",       "type": "text",   "width": 150},
    {"name": "cost_type",  "label": "Type Frais",   "type": "text",   "width": 150},
    {"name": "amount",     "label": "Montant (DA)", "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "notes",      "label": "Notes",        "type": "text",   "width": 200},
]

CUSTOMER_LEDGER_COLUMNS = [
    {"name": "n",           "label": "N°",           "type": "number", "width": 50,  "align": "center"},
    {"name": "id",          "label": "ID",           "type": "number", "width": 60,  "hidden": True},
    {"name": "date",        "label": "Date",         "type": "date",   "width": 100, "align": "center"},
    {"name": "type",        "label": "Opération",    "type": "text",   "width": 120, "align": "center"},
    {"name": "description", "label": "Détails",      "type": "text",   "width": 200},
    {"name": "debit",       "label": "Débit (DA)",   "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "credit",      "label": "Crédit (DA)",  "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "balance",     "label": "Solde (DA)",   "type": "amount", "width": 130, "align": "right"},
]

# ============================================================================
# EXPENSES SECTION
# ============================================================================

EXPENSES_MAIN_COLUMNS = [
    {"name": "n",               "label": "N°",                   "type": "number", "width": 50,  "align": "center"},
    {"name": "id",              "label": "ID",                   "type": "number", "width": 60,  "hidden": True},
    {"name": "date",            "label": "Date",                 "type": "date",   "width": 100, "align": "center"},
    {"name": "category",        "label": "Catégorie",            "type": "text",   "width": 100, "align": "center"},
    {"name": "expense_type",    "label": "Type de frais",        "type": "text",   "width": 150},
    {"name": "linked_to",       "label": "Lié à",                "type": "text",   "width": 150},
    {"name": "currency",        "label": "Devise",               "type": "text",   "width": 80,  "align": "center"},
    {"name": "amount",          "label": "Montant",              "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "total_dzd",       "label": "Total (DA)",           "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "account_supplier","label": "Compte / Fournisseur", "type": "text",   "width": 150},
    {"name": "payment_type",    "label": "Paiement",             "type": "text",   "width": 100, "align": "center"},
    {"name": "reference",       "label": "Référence",            "type": "text",   "width": 120},
]

# ============================================================================
# EXTERNAL DEBT SECTION
# ============================================================================

EXTERNAL_CONTACTS_COLUMNS = [
    {"name": "n",             "label": "N°",                    "type": "number", "width": 50,  "align": "center"},
    {"name": "id",            "label": "ID",                    "type": "number", "width": 60,  "hidden": True},
    {"name": "name",          "label": "Nom",                   "type": "text",   "width": 200},
    {"name": "phone",         "label": "Téléphone",             "type": "text",   "width": 130, "align": "center"},
    {"name": "total_prete",   "label": "Total Prêté",           "type": "amount", "width": 140, "align": "right", "sum": True},
    {"name": "total_recu",    "label": "Total Reçu",            "type": "amount", "width": 140, "align": "right", "sum": True},
    {"name": "total_emprunt", "label": "Total Emprunté",        "type": "amount", "width": 140, "align": "right", "sum": True},
    {"name": "total_rembours","label": "Total Remboursé",       "type": "amount", "width": 140, "align": "right", "sum": True},
    {"name": "solde_net",     "label": "Solde Net",             "type": "amount", "width": 140, "align": "right", "sum": True},
]

EXTERNAL_JOURNAL_COLUMNS = [
    {"name": "n",          "label": "N°",           "type": "number", "width": 50,  "align": "center"},
    {"name": "id",         "label": "ID",           "type": "number", "width": 60,  "hidden": True},
    {"name": "date",       "label": "Date",         "type": "date",   "width": 100, "align": "center"},
    {"name": "contact",    "label": "Contact",      "type": "text",   "width": 150},
    {"name": "type",       "label": "Type",         "type": "text",   "width": 120, "align": "center"},
    {"name": "amount",     "label": "Montant",      "type": "amount", "width": 120, "align": "right", "sum": True},
    {"name": "currency",   "label": "Devise",       "type": "text",   "width": 80,  "align": "center"},
    {"name": "rate",       "label": "Taux",         "type": "amount", "width": 100, "align": "right"},
    {"name": "amount_da",  "label": "Montant (DA)", "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "account",    "label": "Compte",       "type": "text",   "width": 120},
    {"name": "notes",      "label": "Notes",        "type": "text",   "width": 150},
]

EXTERNAL_HISTORY_COLUMNS = [
    {"name": "n",         "label": "N°",           "type": "number", "width": 50,  "align": "center"},
    {"name": "id",        "label": "ID",           "type": "number", "width": 60,  "hidden": True},
    {"name": "date",      "label": "Date",         "type": "date",   "width": 100, "align": "center"},
    {"name": "type",      "label": "Type",         "type": "text",   "width": 120, "align": "center"},
    {"name": "amount",    "label": "Montant",      "type": "amount", "width": 120, "align": "right", "sum": True},
    {"name": "currency",  "label": "Devise",       "type": "text",   "width": 80,  "align": "center"},
    {"name": "rate",      "label": "Taux",         "type": "amount", "width": 100, "align": "right"},
    {"name": "amount_da", "label": "Montant (DA)", "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "account",   "label": "Compte",       "type": "text",   "width": 120},
    {"name": "notes",     "label": "Notes",        "type": "text",   "width": 150},
]

# ============================================================================
# LICENSES SECTION
# ============================================================================

LICENSE_BANK_ACCOUNTS_COLUMNS = [
    {"name": "n",            "label": "N°",               "type": "number", "width": 50,  "align": "center"},
    {"name": "id",           "label": "ID",               "type": "number", "width": 60,  "hidden": True},
    {"name": "owner",        "label": "Propriétaire (RC)","type": "text",   "width": 200},
    {"name": "registration", "label": "N° Registre",      "type": "text",   "width": 150, "align": "center"},
    {"name": "bank",         "label": "Banque",           "type": "text",   "width": 150},
    {"name": "balance",      "label": "Solde (DA)",       "type": "amount", "width": 130, "align": "right", "sum": True},
]

LICENSE_BANK_TRANSFERS_COLUMNS = [
    {"name": "n",        "label": "N°",           "type": "number", "width": 50,  "align": "center"},
    {"name": "id",       "label": "ID",           "type": "number", "width": 60,  "hidden": True},
    {"name": "date",     "label": "Date",         "type": "date",   "width": 100, "align": "center"},
    {"name": "amount",   "label": "Montant (DA)", "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "from_acc", "label": "De (Caisse)",  "type": "text",   "width": 150},
    {"name": "to_acc",   "label": "Vers (Banque)","type": "text",   "width": 150},
    {"name": "note",     "label": "Note",         "type": "text",   "width": 200},
]

# ============================================================================
# TREASURY SECTION
# ============================================================================

TREASURY_ACCOUNTS_COLUMNS = [
    {"name": "n",               "label": "N°",           "type": "number", "width": 50,  "align": "center"},
    {"name": "id",              "label": "ID",           "type": "number", "width": 60,  "hidden": True},
    {"name": "code",            "label": "Code",         "type": "text",   "width": 100, "align": "center", "hidden": True},
    {"name": "name",            "label": "Nom",          "type": "text",   "width": 200},
    {"name": "type",            "label": "Type",         "type": "text",   "width": 120, "align": "center"},
    {"name": "currency",        "label": "Devise",       "type": "text",   "width": 100, "align": "center"},
    {"name": "initial_balance", "label": "Solde Initial","type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "balance",         "label": "Solde",        "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "principal",       "label": "Principal",    "type": "text",   "width": 80,  "align": "center"},
]

TREASURY_TRANSACTIONS_COLUMNS = [
    {"name": "n",              "label": "N°",              "type": "number", "width": 50,  "align": "center"},
    {"name": "id",             "label": "ID",              "type": "number", "width": 60,  "hidden": True},
    {"name": "date",           "label": "Date",            "type": "date",   "width": 100, "align": "center"},
    {"name": "source",         "label": "Source",          "type": "text",   "width": 120},
    {"name": "account",        "label": "Compte",          "type": "text",   "width": 150},
    {"name": "type",           "label": "Type",            "type": "text",   "width": 120, "align": "center"},
    {"name": "amount",         "label": "Montant",         "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "payment_method", "label": "Moyen Paiement",  "type": "text",   "width": 120, "align": "center"},
    {"name": "category",       "label": "Catégorie",       "type": "text",   "width": 120},
    {"name": "status",         "label": "Statut",          "type": "status", "width": 100, "align": "center"},
    {"name": "user",           "label": "Utilisateur",     "type": "text",   "width": 100},
    {"name": "notes",          "label": "Observation",     "type": "text",   "width": 200},
]

TREASURY_TRANSFERS_COLUMNS = [
    {"name": "n",           "label": "N°",             "type": "number", "width": 50,  "align": "center"},
    {"name": "id",          "label": "ID",             "type": "number", "width": 60,  "hidden": True},
    {"name": "date",        "label": "Date",           "type": "date",   "width": 100, "align": "center"},
    {"name": "from_acc",    "label": "De (Source)",    "type": "text",   "width": 150},
    {"name": "to_acc",      "label": "À (Destination)","type": "text",   "width": 150},
    {"name": "amount",      "label": "Montant",        "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "reference",   "label": "Référence",      "type": "text",   "width": 120},
    {"name": "description", "label": "Description",    "type": "text",   "width": 200},
    {"name": "status",      "label": "Statut",         "type": "status", "width": 100, "align": "center"},
]

# ============================================================================
# WAREHOUSE SECTION
# ============================================================================

WAREHOUSES_COLUMNS = [
    {"name": "n",         "label": "N°",         "type": "number", "width": 50,  "align": "center"},
    {"name": "id",        "label": "ID",         "type": "number", "width": 60,  "hidden": True},
    {"name": "name",      "label": "Nom",        "type": "text",   "width": 200},
    {"name": "address",   "label": "Adresse",    "type": "text",   "width": 300},
    {"name": "principal", "label": "Principal",  "type": "text",   "width": 80,  "align": "center"},
    {"name": "notes",     "label": "Notes",      "type": "text",   "width": 200},
]

WAREHOUSE_STOCKS_COLUMNS = [
    {"name": "n",          "label": "N°",                "type": "number", "width": 50,  "align": "center"},
    {"name": "id",         "label": "ID",                "type": "number", "width": 60,  "hidden": True},
    {"name": "customer",   "label": "Client",            "type": "text",   "width": 150},
    {"name": "container",  "label": "Conteneur",         "type": "text",   "width": 120, "align": "center"},
    {"name": "goods_type", "label": "Type Marchandise",  "type": "text",   "width": 150},
    {"name": "quantity",   "label": "Quantité",          "type": "number", "width": 100, "align": "center"},
    {"name": "weight",     "label": "Poids (kg)",        "type": "amount", "width": 120, "align": "right"},
    {"name": "notes",      "label": "Notes",             "type": "text",   "width": 200},
]

WAREHOUSE_MOVEMENTS_COLUMNS = [
    {"name": "n",        "label": "N°",        "type": "number", "width": 50,  "align": "center"},
    {"name": "id",       "label": "ID",        "type": "number", "width": 60,  "hidden": True},
    {"name": "date",     "label": "Date",      "type": "date",   "width": 100, "align": "center"},
    {"name": "type",     "label": "Type",      "type": "text",   "width": 120, "align": "center"},
    {"name": "customer", "label": "Client",    "type": "text",   "width": 150},
    {"name": "quantity", "label": "Quantité",  "type": "number", "width": 100, "align": "center"},
    {"name": "notes",    "label": "Notes",     "type": "text",   "width": 200},
]

# ============================================================================
# PARTNERS SECTION
# ============================================================================

PARTNERS_COLUMNS = [
    {"name": "n",                 "label": "N°",              "type": "number",     "width": 50,  "align": "center"},
    {"name": "id",                "label": "ID",              "type": "number",     "width": 60,  "hidden": True},
    {"name": "name",              "label": "Nom Prénom",      "type": "text",       "width": 180},
    {"name": "phone",             "label": "N° Téléphone",    "type": "text",       "width": 130, "align": "center"},
    {"name": "email",             "label": "E-Mail",          "type": "text",       "width": 150},
    {"name": "function",          "label": "Fonction",        "type": "text",       "width": 130},
    {"name": "contributions",     "label": "M. Contributions","type": "amount",     "width": 130, "align": "right", "sum": True},
    {"name": "contribution_pct",  "label": "% Contrib.",      "type": "percentage", "width": 100, "align": "center"},
    {"name": "profit",            "label": "M. Profit",       "type": "amount",     "width": 130, "align": "right", "sum": True},
    {"name": "surplus",           "label": "M. Surchats",     "type": "amount",     "width": 130, "align": "right", "sum": True},
    {"name": "balance",           "label": "Reste",           "type": "amount",     "width": 130, "align": "right", "sum": True},
    {"name": "status",            "label": "Statut",          "type": "status",     "width": 100, "align": "center"},
]

PARTNER_HISTORY_COLUMNS = [
    {"name": "n",          "label": "N°",          "type": "number", "width": 50,  "align": "center"},
    {"name": "id",         "label": "ID",          "type": "number", "width": 60,  "hidden": True},
    {"name": "date",       "label": "Date",        "type": "date",   "width": 100, "align": "center"},
    {"name": "type",       "label": "Type",        "type": "text",   "width": 150},
    {"name": "amount",     "label": "Montant",     "type": "amount", "width": 130, "align": "right", "sum": True},
    {"name": "reference",  "label": "Réf",         "type": "text",   "width": 120},
    {"name": "treasury",   "label": "Trésorerie",  "type": "text",   "width": 120},
    {"name": "notes",      "label": "Notes",       "type": "text",   "width": 200},
]

# ============================================================================
# MAPPING — SOURCE UNIQUE (Single Source of Truth)
# ============================================================================

COLUMN_SCHEMAS = {
    # Logistics
    "agents_maritimes":     AGENTS_MARITIMES_COLUMNS,
    "agent_payments":       AGENT_PAYMENTS_COLUMNS,
    "containers":           CONTAINERS_COLUMNS,
    "logistics_containers": CONTAINERS_COLUMNS,
    "logistics_expenses":   LOGISTICS_EXPENSES_COLUMNS,
    "wizard_containers":    WIZARD_CONTAINERS_COLUMNS,
    "wizard_goods":         WIZARD_GOODS_COLUMNS,

    # Currency
    "currency_summary":          CURRENCY_SUMMARY_COLUMNS,
    "supplier_payments_history": SUPPLIER_PAYMENTS_COLUMNS,
    "currency_purchases":        CURRENCY_PURCHASES_COLUMNS,
    "suppliers":                 SUPPLIERS_COLUMNS,

    # Customers
    "customer_list":     CUSTOMER_LIST_COLUMNS,
    "customer_goods":    CUSTOMER_GOODS_COLUMNS,
    "customer_payments": CUSTOMER_PAYMENTS_COLUMNS,
    "customer_costs":    CUSTOMER_COSTS_COLUMNS,
    "customer_ledger":   CUSTOMER_LEDGER_COLUMNS,

    # Expenses
    "expenses_main": EXPENSES_MAIN_COLUMNS,

    # External Debt
    "external_contacts": EXTERNAL_CONTACTS_COLUMNS,
    "external_journal":  EXTERNAL_JOURNAL_COLUMNS,
    "external_history":  EXTERNAL_HISTORY_COLUMNS,

    # Licenses
    "license_bank_accounts":  LICENSE_BANK_ACCOUNTS_COLUMNS,
    "license_bank_transfers": LICENSE_BANK_TRANSFERS_COLUMNS,

    # Treasury
    "treasury_accounts":     TREASURY_ACCOUNTS_COLUMNS,
    "treasury_transactions": TREASURY_TRANSACTIONS_COLUMNS,
    "treasury_transfers":    TREASURY_TRANSFERS_COLUMNS,

    # Warehouse
    "warehouses":          WAREHOUSES_COLUMNS,
    "warehouse_stocks":    WAREHOUSE_STOCKS_COLUMNS,
    "warehouse_movements": WAREHOUSE_MOVEMENTS_COLUMNS,

    # Partners
    "partners_table":  PARTNERS_COLUMNS,
    "partner_history": PARTNER_HISTORY_COLUMNS,
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_column_schema(table_id: str) -> list:
    """Récupérer la définition des colonnes pour une table spécifique."""
    return COLUMN_SCHEMAS.get(table_id, [])


def get_headers_from_schema(schema: list) -> list:
    """Extraire la liste des en-têtes depuis le schéma."""
    return [col["label"] for col in schema]


def get_align_map_from_schema(schema: list) -> dict:
    """Extraire la carte d'alignement depuis le schéma."""
    align_map = {}
    for idx, col in enumerate(schema):
        if "align" in col:
            align_map[idx] = col["align"]
    return align_map


def get_summable_columns(schema: list) -> dict:
    """Récupérer les colonnes sommables (sum: True ou avg: True)."""
    summable = {}
    for idx, col in enumerate(schema):
        if "sum" in col:
            summable[idx] = col["sum"]
        elif "avg" in col:
            summable[idx] = col["avg"]
    return summable


def get_hidden_columns(schema: list) -> list:
    """Récupérer les indices des colonnes masquées."""
    return [idx for idx, col in enumerate(schema) if col.get("hidden", False)]


def get_column_types_from_schema(schema: list) -> dict:
    """
    Extraire le type de chaque colonne depuis le schéma.

    Retourne: {col_index: col_type}
    Types: 'text' | 'number' | 'amount' | 'date' | 'status' | 'percentage'

    SOURCE UNIQUE pour:
      - Formatage d'affichage dans add_row()
      - Calculs footer dans _update_footer()
      - Alignement automatique des colonnes
    """
    return {idx: col.get("type", "text") for idx, col in enumerate(schema)}
