# معايير التصميم — Shipping Company

## 1️⃣ معايير Dialog الإدخال

### الترتيب الموحد (من الأعلى للأسفل)

```
┌─────────────────────────────────────────┐
│  Informations de base (GroupBox)        │
│  ─────────────────────────────────────  │
│  1. التاريخ (Date)          [QDateEdit] │
│  2. العملة (Devise)         [QComboBox]│
│  3. المبلغ (Montant)        [Amount]   │
│  4. المرجع (Référence)      [QLineEdit]│
│  5. الملاحظات (Notes)       [QTextEdit]│
│                                         │
│  [فئة/نوع أو معلومات أخرى]  (GroupBox)│
│  ─────────────────────────────────────  │
│  [تفاصيل حسب السياق]                    │
│                                         │
│  [التفاصيل السياقية]        (GroupBox) │
│  ─────────────────────────────────────  │
│  [حقول تظهر/تختفي حسب الاختيار]         │
│                                         │
│        [إلغاء]          [حفظ]           │
└─────────────────────────────────────────┘
```

### المبادئ الأساسية

- **كل GroupBox** يحتوي على `QFormLayout` مع `setSpacing(8)`
- **التاريخ دائماً رقم 1** في "معلومات الأساس"
- **الأزرار في الأسفل** مباشرة قبل الإغلاق
- **الحقول المشتركة أولاً** (التاريخ، العملة، المبلغ، المرجع، الملاحظات)
- **ثم الحقول السياقية** (تختلف حسب نوع البيانات)
- **استخدام QButtonGroup للخيارات الثنائية** (Radio buttons)
- **استخدام QGroupBox + QHBoxLayout** لـ Radio buttons التي تظهر في صف واحد

### مثال كود صحيح

```python
def _setup_ui(self):
    main_layout = QVBoxLayout(self)
    main_layout.setSpacing(12)

    # ── المعلومات الأساسية ─────────────────────
    common_group = QGroupBox("معلومات الأساس")
    common_form = QFormLayout(common_group)
    common_form.setSpacing(8)

    # 1. التاريخ (أول حقل)
    self.date_input = QDateEdit()
    self.date_input.setDate(QDate.currentDate())
    self.date_input.setCalendarPopup(True)
    common_form.addRow("التاريخ:", self.date_input)

    # 2. العملة
    self.currency_combo = QComboBox()
    common_form.addRow("العملة:", self.currency_combo)

    # 3. المبلغ
    self.amount_input = AmountInput(currency_symbol="DA")
    common_form.addRow("المبلغ:", self.amount_input)

    # 4. المرجع
    self.ref_input = QLineEdit()
    common_form.addRow("المرجع:", self.ref_input)

    # 5. الملاحظات
    self.notes_input = QTextEdit()
    self.notes_input.setMaximumHeight(55)
    common_form.addRow("الملاحظات:", self.notes_input)

    main_layout.addWidget(common_group)

    # ── نوع/فئة ────────────────────────────────
    cat_group = QGroupBox("النوع")
    cat_layout = QHBoxLayout(cat_group)
    
    self.radio_a = QRadioButton("خيار أ")
    self.radio_b = QRadioButton("خيار ب")
    self.radio_a.setChecked(True)
    
    self._cat_group = QButtonGroup()
    self._cat_group.addButton(self.radio_a, 0)
    self._cat_group.addButton(self.radio_b, 1)
    
    cat_layout.addWidget(self.radio_a)
    cat_layout.addWidget(self.radio_b)
    main_layout.addWidget(cat_group)

    # ── تفاصيل سياقية ─────────────────────────
    detail_group = QGroupBox("تفاصيل")
    detail_form = QFormLayout(detail_group)
    detail_form.setSpacing(8)
    
    self.field1 = QComboBox()
    detail_form.addRow("الحقل 1:", self.field1)
    
    main_layout.addWidget(detail_group)

    # ── الأزرار ────────────────────────────────
    btns = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Save | 
        QDialogButtonBox.StandardButton.Cancel
    )
    btns.accepted.connect(self.save)
    btns.rejected.connect(self.reject)
    main_layout.addWidget(btns)
```

---

## 2️⃣ معايير الجداول (EnhancedTableView)

### ترتيب الأعمدة

1. **N° (تلقائي)**
2. **ID (الرقم الداخلي)**
3. **التاريخ**
4. **المعلومات الأساسية** (الاسم، العنوان، إلخ)
5. **الكميات/الأرقام**
6. **الأموال** (مبالغ، أرصدة)
7. **الحالة/الملاحظات**

### أمثلة

**جدول التكاليف:**
```
N° | ID | التاريخ | النوع | المبلغ | العملة | الإجمالي DA | الحساب | الدفع
```

**جدول الحاويات:**
```
N° | ID | التاريخ | الحاوية | الفاتورة | الوكيل | CBM | الكمية | التكاليف | الإيراد | الفائدة
```

### إضافة عمود جديد

- لا تضف أكثر من 15 عمود
- استخدم `format_amount()` للأموال
- استخدم `format_date()` للتواريخ
- خيّف الأعمدة المساعدة بـ `hide_column(idx)`

---

## 3️⃣ معايير الألوان

- استخدم **دائماً** `get_active_colors()` من `core.themes`
- لا تستخدم أبداً ألوان مشفرة مثل `#ffffff` في الواجهات الحية
- للنصوص: `c['text_main']`, `c['text_secondary']`
- للخلفيات: `c['bg_main']`, `c['bg_secondary']`, `c['accent']`
- لتنسيق الأخطاء: `c['error']`

---

## 4️⃣ معايير GroupBox

```python
group = QGroupBox("العنوان")
layout = QFormLayout(group)  # أو QHBoxLayout للخيارات

# ضبط التباعد
layout.setSpacing(8)

# إضافة العناصر
layout.addRow("التسمية:", widget)

# إضافة الفاصل (إن لزم)
sep = QFrame()
sep.setFrameShape(QFrame.Shape.HLine)
layout.addRow(sep)

main_layout.addWidget(group)
```

---

## 5️⃣ معايير Signals والاتصالات

- استخدم `dataChanged = pyqtSignal()` في كل View
- اتصل بـ `self.dataChanged.emit()` بعد التحديث
- استخدم `_on_*_changed()` للدوال التي تستجيب للتغييرات
- استخدم `_load_*()` للدوال التي تجلب البيانات

---

## 6️⃣ معايير Service

- كل دالة تجلب بيانات تُرجع `List[dict]`
- كل دالة تُنشئ/تُعدّل ترجع `Tuple[bool, str, Optional[id]]`
- استخدم `with get_session()` دائماً
- استخدم `try/except` مع `session.rollback()` عند الخطأ

---

## 7️⃣ معايير الأعمدة الجديدة

عند إضافة أعمدة جديدة:

```python
# احسبها من البيانات الموجودة
costs = service.get_costs_for_item(item_id)
revenue = service.get_revenue_for_item(item_id)
profit = revenue - costs

# أضفها بالتنسيق الصحيح
self.table.add_row([
    ...
    format_amount(costs, "DA"),
    format_amount(revenue, "DA"),
    format_amount(profit, "DA"),
], is_active=is_active)
```

---

## 📋 قائمة التدقيق (Checklist) لكل Dialog جديد

- [ ] التاريخ أول حقل؟
- [ ] العملة والمبلغ والمرجع والملاحظات موجودة؟
- [ ] الأزرار في الأسفل؟
- [ ] كل GroupBox لديه `QFormLayout` مع `setSpacing(8)`؟
- [ ] استخدام `get_active_colors()` للألوان؟
- [ ] استخدام `QButtonGroup` للخيارات الثنائية؟
- [ ] وجود دالة `refresh()`؟
- [ ] إرسال `dataChanged.emit()` بعد الحفظ؟

---

## 📋 قائمة التدقيق لكل جدول جديد

- [ ] N°، ID، التاريخ أولاً؟
- [ ] الأموال بـ `format_amount()`؟
- [ ] التواريخ بـ `format_date()`؟
- [ ] أقل من 15 عمود؟
- [ ] الحقول المساعدة مخفية بـ `hide_column()`؟
- [ ] وجود دالة `refresh()`؟

---

**آخر تحديث:** 2026-04-17  
**المسؤول:** تصميم التطبيق
