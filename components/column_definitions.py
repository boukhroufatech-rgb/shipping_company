"""
تعريفات مركزية للأعمدة في جميع جداول البرنامج
يحدد هذا الملف:
- أسماء الأعمدة وتسمياتها
- نوع البيانات (نص، رقم، تاريخ، إلخ)
- المحاذاة
- عرض العمود
- دوال المجموع
"""

# ============================================================================
# LOGISTICS SECTION
# ============================================================================

AGENTS_MARITIMES_COLUMNS = [
    {"name": "n", "label": "N°", "type": "number", "width": 50, "align": "center"},
    {"name": "id", "label": "ID", "type": "number", "width": 60, "hidden": True},
    {"name": "agent_name", "label": "الوكيل", "type": "text", "width": 180},
    {"name": "country", "label": "الدولة", "type": "text", "width": 100},
    {"name": "chiffre_affaire", "label": "رقم الأعمال (DA)", "type": "amount", "width": 150, "sum": True},
    {"name": "shipments", "label": "عدد الفواتير", "type": "number", "width": 120, "align": "center", "sum": "count"},
    {"name": "containers", "label": "عدد الحاويات", "type": "number", "width": 120, "align": "center", "sum": "count"},
    {"name": "payments_received", "label": "المدفوعات (DA)", "type": "amount", "width": 150, "sum": True},
    {"name": "amount_due", "label": "المستحق (DA)", "type": "amount", "width": 150, "sum": True},
    {"name": "pending_payments", "label": "المعلقة (DA)", "type": "amount", "width": 150, "sum": True},
    {"name": "balance", "label": "الرصيد (DA)", "type": "amount", "width": 150, "sum": True},
    {"name": "collection_rate", "label": "معدل التحصيل (%)", "type": "percentage", "width": 130, "align": "center", "avg": True},
    {"name": "currency", "label": "العملة", "type": "text", "width": 80, "align": "center"},
    {"name": "address", "label": "العنوان", "type": "text", "width": 200},
]

AGENT_PAYMENTS_COLUMNS = [
    {"name": "n", "label": "N°", "type": "number", "width": 50, "align": "center"},
    {"name": "id", "label": "ID", "type": "number", "width": 60, "hidden": True},
    {"name": "date", "label": "التاريخ", "type": "date", "width": 100, "align": "center"},
    {"name": "agent", "label": "الوكيل", "type": "text", "width": 150},
    {"name": "type", "label": "النوع", "type": "text", "width": 100, "align": "center"},
    {"name": "amount", "label": "المبلغ", "type": "amount", "width": 130, "sum": True},
    {"name": "status", "label": "الحالة", "type": "status", "width": 100, "align": "center"},
    {"name": "currency", "label": "العملة", "type": "text", "width": 80, "align": "center"},
    {"name": "account", "label": "الحساب", "type": "text", "width": 150},
    {"name": "bill", "label": "الفاتورة", "type": "text", "width": 100, "align": "center"},
    {"name": "reference", "label": "المرجع", "type": "text", "width": 120},
    {"name": "notes", "label": "الملاحظات", "type": "text", "width": 150},
]

CONTAINERS_COLUMNS = [
    {"name": "n", "label": "N°", "type": "number", "width": 50, "align": "center"},
    {"name": "id", "label": "ID", "type": "number", "width": 60, "hidden": True},
    {"name": "date", "label": "التاريخ", "type": "date", "width": 100, "align": "center"},
    {"name": "bill", "label": "N° BILL", "type": "text", "width": 100, "align": "center"},
    {"name": "invoice", "label": "الفاتورة", "type": "text", "width": 100, "align": "center"},
    {"name": "agent", "label": "الوكيل", "type": "text", "width": 150},
    {"name": "customers", "label": "العملاء", "type": "number", "width": 80, "align": "center"},
    {"name": "containers_count", "label": "الحاويات", "type": "number", "width": 80, "align": "center"},
    {"name": "cbm", "label": "CBM", "type": "amount", "width": 100, "align": "right"},
    {"name": "cartons", "label": "الكرتون", "type": "number", "width": 100, "align": "center"},
    {"name": "amount_usd", "label": "المبلغ ($)", "type": "amount", "width": 120, "sum": True},
    {"name": "taux", "label": "السعر", "type": "amount", "width": 100, "align": "right"},
    {"name": "equivalent_dzd", "label": "المعادل (DA)", "type": "amount", "width": 130, "sum": True},
    {"name": "taux_expedition", "label": "سعر الشحن", "type": "amount", "width": 120, "align": "right"},
    {"name": "equivalent_expedition", "label": "إيرادات (DA)", "type": "amount", "width": 130, "sum": True},
    {"name": "port", "label": "الميناء", "type": "text", "width": 100},
    {"name": "transitaire", "label": "الوسيط", "type": "text", "width": 100},
    {"name": "shipping", "label": "الشحن (DA)", "type": "amount", "width": 130, "sum": True},
    {"name": "tax", "label": "الضريبة (DA)", "type": "amount", "width": 130, "sum": True},
    {"name": "commission", "label": "العمولة (%)", "type": "percentage", "width": 110, "align": "center"},
    {"name": "charge_da", "label": "الرسوم (DA)", "type": "amount", "width": 130, "sum": True},
    {"name": "charge_port", "label": "رسوم الميناء", "type": "amount", "width": 130, "sum": True},
    {"name": "surestarie", "label": "الرسوم الإضافية", "type": "amount", "width": 130, "sum": True},
    {"name": "total_costs", "label": "إجمالي التكاليف", "type": "amount", "width": 150, "sum": True},
    {"name": "revenue", "label": "الإيرادات (DA)", "type": "amount", "width": 150, "sum": True},
    {"name": "profit", "label": "الربح (DA)", "type": "amount", "width": 150, "sum": True},
]

# ============================================================================
# MAPPING FOR BACKWARD COMPATIBILITY
# ============================================================================

COLUMN_SCHEMAS = {
    "agents_maritimes": AGENTS_MARITIMES_COLUMNS,
    "agent_payments": AGENT_PAYMENTS_COLUMNS,
    "containers": CONTAINERS_COLUMNS,
}


def get_column_schema(table_id: str) -> list:
    """الحصول على تعريف الأعمدة لجدول معين"""
    return COLUMN_SCHEMAS.get(table_id, [])


def get_headers_from_schema(schema: list) -> list:
    """استخراج قائمة الرؤوس من التعريف"""
    return [col["label"] for col in schema]


def get_align_map_from_schema(schema: list) -> dict:
    """استخراج خريطة المحاذاة من التعريف"""
    align_map = {}
    for idx, col in enumerate(schema):
        if "align" in col:
            align_map[idx] = col["align"]
    return align_map


def get_summable_columns(schema: list) -> dict:
    """الحصول على الأعمدة التي يمكن جمع قيمها"""
    summable = {}
    for idx, col in enumerate(schema):
        if "sum" in col:
            summable[idx] = col["sum"]
        elif "avg" in col:
            summable[idx] = col["avg"]
    return summable


def get_hidden_columns(schema: list) -> list:
    """الحصول على الأعمدة المخفية"""
    return [idx for idx, col in enumerate(schema) if col.get("hidden", False)]
