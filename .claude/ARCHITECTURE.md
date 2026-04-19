# 🏛️ المعمارية الشاملة للتطبيق

## المبادئ الأساسية

### 1. **المبدأ الذهبي (Golden Principle)**
```
Backend (Raw Data) ≠ Frontend (Display Formatting)

Backend يمرر:
  - أرقام خام (floats): 1234.56
  - تواريخ ISO: 2026-04-19
  - نصوص نقية: "Active"

Frontend (EnhancedTableView) تتولى:
  - الترجمة المعمارية (1,234.56 DA)
  - التنسيق حسب الـ Schema
  - المحاذات التلقائية
  - الألوان والأنماط
```

---

## نظام الـ TREE SYSTEM (شجرة التعريفات)

### البنية الهرمية:

```
┌─────────────────────────────────────────┐
│   column_definitions.py (مصدر وحيد)     │
│   Single Source of Truth (SSOT)         │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
 SCHEMAS    TYPES     ALIGNMENTS
    │            │            │
    ├─> Logistics
    ├─> Treasury
    ├─> Currency
    ├─> Customers
    ├─> Expenses
    └─> Catalogs (اختياري)
```

### المزايا:

✅ **توحيد كامل**
  - غير التعريف مرة واحدة = تأثير على كل الجداول

✅ **قابلية الصيانة**
  - كل التعريفات في ملف واحد

✅ **الاتساق المرئي**
  - نفس القواعد في كل الجداول

---

## الفرق بين أنواع الجداول

### 📊 **النوع 1: جداول المعاملات (TRANSACTION TABLES)**

```python
# مثال: treasury_accounts, customers, shipments

المواصفات:
├─ بيانات ديناميكية (Dynamic)
├─ تتغير باستمرار
├─ لها schema كامل محدد مسبقاً
├─ SSOT في column_definitions.py
└─ يستخدمون: set_headers_from_schema()

الاستخدام:
  self.table.set_headers_from_schema("treasury_accounts")
  self.table.add_row([raw_data...])  # Backend يمرر raw
  # EnhancedTableView تتولى التنسيق
```

### 📚 **النوع 2: جداول الكاتالوجات (CATALOG TABLES)**

```python
# مثال: license_goods, expense_types, currencies

المواصفات:
├─ بيانات مرجعية (Reference Data)
├─ تتغير نادراً
├─ بنية موحدة: N°, ID, Name, Description
├─ Generic Dialog يدير الـ CRUD
└─ يستخدمون: GenericCatalogDialog

الاستخدام:
  dialog = GenericCatalogDialog(
    title="Marchandises",
    get_data_func=service.get_all_goods,
    headers=["N°", "ID", "Nom", "Description"]
  )
```

---

## السؤال الأساسي: هل الكاتالوجات تدخل في TREE SYSTEM؟

### 🔴 **الحالة الحالية (Status Quo):**

| الجانب | المعاملات | الكاتالوجات |
|--------|-----------|------------|
| Schema | ✅ محدف | ❌ لا |
| Dialog | EnhancedTableView | GenericCatalogDialog |
| Headers | من `column_definitions.py` | يدويًا في الـ Dialog |
| تنسيق | آلي حسب Schema | يدويًا (محدود) |

**المشاكل:**
```
❌ عدم توحيد
❌ صعوبة الصيانة إذا أردنا تغيير محاذة الكاتالوج
❌ تكرار الـ headers يدويًا في كل catalog
```

### 🟢 **الحل المقترح 1: شمول الكاتالوجات في TREE SYSTEM**

```python
# في column_definitions.py:

# Catalogs Section
LICENSE_GOODS_COLUMNS = [
    {"name": "n",    "label": "N°",         "type": "number", "width": 50,  "align": "center"},
    {"name": "id",   "label": "ID",         "type": "number", "width": 60,  "hidden": True},
    {"name": "name", "label": "Marchandise","type": "text",   "width": 200},
    {"name": "desc", "label": "Description","type": "text",   "width": 250},
]

EXPENSE_TYPES_COLUMNS = [
    {"name": "n",    "label": "N°",    "type": "number", "width": 50,  "align": "center"},
    {"name": "id",   "label": "ID",    "type": "number", "width": 60,  "hidden": True},
    {"name": "name", "label": "Type",  "type": "text",   "width": 200},
    {"name": "desc", "label": "Desc.", "type": "text",   "width": 250},
]

COLUMN_SCHEMAS = {
    ...
    # Catalogs
    "license_goods":  LICENSE_GOODS_COLUMNS,
    "expense_types":  EXPENSE_TYPES_COLUMNS,
}
```

**الفوائد:**
```
✅ توحيد كامل
✅ سهل الصيانة
✅ نفس المنطق المعماري
✅ احترافي جداً
```

### 🟡 **الحل المقترح 2: الحفاظ على الفصل (Status Quo محسّن)**

```python
# تترك الكاتالوجات بدون Schemas
# لكن تحسّن GenericCatalogDialog بـ:

class GenericCatalogDialog(QDialog):
    def __init__(self, ..., alignment_map=None):
        self.alignment_map = alignment_map or {}
        # ...
    
    def load_data(self):
        for item in items:
            self.table.add_row(
                [item['n'], item['id'], item['name'], item['desc']],
                alignment_map=self.alignment_map
            )
```

**الفوائد:**
```
✅ مرونة أكثر للكاتالوجات الخاصة
✅ فصل واضح (معاملات ≠ مراجع)
⚠️  تكرار قليل في التعريفات
```

---

## نظام المحاذات (Alignment System)

### 📐 **القواعد الموجودة:**

```python
align: "center"  →  N°, Dates, Status, Currencies, Counts
align: "right"   →  Amounts, Rates, Percentages
align: "left"    →  Text (Names, Addresses, Description)
```

### ⚠️ **المشكلة الحالية:**

```python
# ❌ بدون محاذة صريحة (يعتمد على auto-detection)
{"name": "chiffre_affaire", "type": "amount", ...}  # بدون "align"

# ✅ محاذة صريحة
{"name": "cbm", "type": "amount", "align": "right", ...}
```

### 🎯 **الحل:**

```
قاعدة ذهبية:
- كل عمود "type": "amount" يجب أن يكون "align": "right"
- كل عمود "type": "percentage" يجب أن يكون "align": "right"
- كل عمود "type": "date" يجب أن يكون "align": "center"
- كل عمود "type": "number" و لا count يجب "align": "right"
```

---

## التدفق الكامل (End-to-End Flow)

### مثال: جدول الفواتير

```
1️⃣  Schema Definition (column_definitions.py)
    ├─ تعريف الأعمدة
    ├─ الأنواع (text, amount, date)
    └─ المحاذات الصريحة

2️⃣  Backend Layer (service.py)
    ├─ جلب البيانات من DB
    ├─ تمرير raw values:
    │   └─ floats: 1234.56 (بدون DA)
    │   └─ dates: 2026-04-19 (ISO format)
    │   └─ strings: "pending"
    └─ لا formatting!

3️⃣  View Layer (views.py)
    ├─ استدعاء set_headers_from_schema("invoices")
    ├─ استدعاء add_row(raw_data)
    └─ لا formatting!

4️⃣  EnhancedTableView (Enhanced Logic)
    ├─ قراءة _column_types من schema
    ├─ تطبيق التنسيق:
    │   └─ amount → "1,234.56 DA"
    │   └─ date → "19/04/2026"
    │   └─ percentage → "45.50%"
    ├─ تطبيق المحاذات من schema
    ├─ تخزين raw في UserRole
    └─ عرض مُنسّق في UI

5️⃣  Footer Calculations
    ├─ قراءة UserRole (القيم الخام)
    ├─ حساب دقيق (بدون parsing)
    └─ عرض المجموع مُنسّق
```

---

## الفروقات الدقيقة

### ❓ **متى نستخدم "align": "right"؟**

```
✅ يجب RIGHT:
   - amounts (أرقام مالية)
   - rates (أسعار صرف)
   - percentages (نسب)
   - counts (كميات) - نقطة جدل ⚠️

⚠️  النقطة الغامضة:
   - counts: هل تحتاج RIGHT أم CENTER؟
     - رأي 1: RIGHT لأنها أرقام
     - رأي 2: CENTER لأنها وصفية (عدد الفواتير)
     - الحالي: CENTER في أغلب الحالات
```

### ❓ **هل نحتاج Schema لكل catalog؟**

```
حسب الاستخدام:

1️⃣  إذا كان الـ Catalog بسيط جداً:
   └─ لا داعي لـ Schema (الحالي)
   
2️⃣  إذا كان له محاذات مخصصة أو أعمدة إضافية:
   └─ نعم، أضفه للـ Schema (مقترح)

مثال:
  ✅ License Goods (بسيط) → Schema اختياري
  ❌ Account Transactions (معقد) → Schema إجباري
```

---

## الخيارات المتاحة

### ✅ **الخيار 1: شمول كامل (Inclusive)**

```
الفلسفة: "كل جدول = Schema"

المزايا:
+ توحيد 100%
+ سهل الصيانة
+ احترافي جداً
+ scalable للمستقبل

العيوب:
- تعريفات إضافية قد لا تُستخدم
- قد تكون زيادة على أبسط الحالات
```

### ⚠️ **الخيار 2: فصل محفوظ (Separated)**

```
الفلسفة: "معاملات = Schema" "مراجع = Generic"

المزايا:
+ واضح المسؤوليات
+ مرنة للكاتالوجات الخاصة
+ أخف وزناً

العيوب:
- قد يكون صعب للصيانة لاحقاً
- غير موحد 100%
```

### 🟢 **الخيار 3: هجين ذكي (Hybrid)**

```
الفلسفة: "Schemas فقط للجداول المعقدة"

المزايا:
+ أفضل من الاثنين
+ عملي وواقعي
+ scalable

تطبيق:
- Treasury, Logistics → Schema إجباري
- Catalogs بسيطة → بدون Schema
- Catalogs معقدة → Schema اختياري
```

---

## الأسئلة المفتوحة

### 1️⃣ **محاذة الأرقام (Counts)**

```
السؤال: هل "عدد الفواتير" يجب RIGHT أم CENTER؟

الحالي: CENTER
البديل: RIGHT (تعاملها كأرقام)

رأيك؟
```

### 2️⃣ **شمول الكاتالوجات**

```
السؤال: هل نضيف Schemas لكل الكاتالوجات؟

الخيارات:
A) نعم، كل شيء موحد
B) لا، اترك الكاتالوجات كما هي
C) هجين (فقط المعقدة)

رأيك؟
```

### 3️⃣ **العملات في المحاذات**

```
السؤال: كيف نتعامل مع رموز العملات؟

الحالي: 
  - المبلغ + العملة معاً: "1,234.56 DA"
  - محاذة: RIGHT (من نوع amount)

البديل:
  - المبلغ وحده: "1,234.56" → RIGHT
  - العملة وحدها: "DA" → CENTER (في عمود منفصل)

أيهما أفضل؟
```

### 4️⃣ **الـ Auto-detection vs Explicit**

```
السؤال: هل نترك auto-detection للمحاذات أم نجعل كل شيء explicit؟

الحالي: مختلط (بعضها explicit، بعضها auto)

المقترح: كل شيء explicit (أكثر وضوحاً)

الفائدة:
  - لا التباس
  - أسهل للقراءة
  - احترافي
```

---

## الخلاصة: ما تحتاج توضيح؟

| السؤال | الإجابة الحالية | المقترحة |
|--------|----------------|---------| 
| هل الكاتالوجات في Schema؟ | لا | اختياري (خيار 3) |
| محاذة الأرقام؟ | CENTER | ? |
| محاذة المبالغ؟ | RIGHT (محسّن) | ✅ |
| هل كل شيء explicit؟ | مختلط | نعم (مقترح) |

---

## ما التالي؟

بعد النقاش واتخاذ القرارات:

1. تحديد القواعد الموحدة
2. إصلاح الـ Schemas
3. تطبيق على كل الجداول
4. اختبار شامل
5. توثيق المعمارية النهائية

---

**اضغط عليّ بأسئلتك! 🚀**
