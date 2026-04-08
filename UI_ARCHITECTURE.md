# 🏗️ المعمارية التقنية للواجهة — UI Architecture
# Shipping Company Application
# =============================================
# هذا الملف يشرح "لماذا" اتُّخذت القرارات التقنية.
# لمن يأتي من بعدنا: اقرأ هذا قبل تعديل أي مكون.
# =============================================

---

## 🌳 الشجرة الأساسية: EnhancedTableView

### ما هو؟
`components/enhanced_table.py` هو **المكون الأب** لكل جدول في البرنامج.

### لماذا وُجد؟
قبل وجوده، كان كل module يبني جدوله الخاص يدوياً، مما أدى إلى:
- تكرار الكود في 8+ ملفات.
- عدم التناسق البصري بين الوحدات.
- صعوبة تغيير أي شيء شامل (كان يتطلب تعديل 8 ملفات).

### ماذا يوفر؟
```
EnhancedTableView
├── شريط أدوات موحد (Toolbar)
│   ├── Nouveau      ← إضافة
│   ├── Modifier     ← تعديل (يُفعَّل عند اختيار صف)
│   ├── Supprimer    ← حذف (يُفعَّل عند اختيار صف)
│   ├── Restaurer    ← استعادة (مخفي بالافتراضي)
│   ├── Rafraîchir   ← تحديث
│   ├── PDF          ← تصدير PDF
│   ├── Excel        ← تصدير Excel
│   ├── Imprimer     ← طباعة
│   └── Importer     ← استيراد CSV
├── بحث ذكي (Smart Search)
├── فلتر الحالة (Status Filter)
├── تذييل مع الإحصاءات (Footer)
└── تخزين عرض الأعمدة (Column Width Persistence)
```

### كيف يُستخدم في الوحدات؟
```python
# الاستخدام القياسي (Standard Usage)
self.table = EnhancedTableView(table_id="my_module")
self.table.set_headers(["N°", "Nom", "Montant"])
self.table.addClicked.connect(self.on_add)
self.table.editClicked.connect(self.on_edit)
```

---

## ⚠️ الاستثناءات الموثقة (Documented Exceptions)

### [CUSTOM-001] btn_smart_activate في world_dialog.py
**الملف:** `modules/currency/world_dialog.py` السطر ~86

**ما يفعله:**
زر يظهر فقط عند كتابة اسم عملة في البحث. يقترح تفعيل عملة من الكتالوج العالمي دون الحاجة لنموذج إضافة تقليدي.

**لماذا هو مخصص (Custom) وليس آلي؟**
هذا الزر يعمل بمنطق "Smart Discovery" فريد لا يتوفر في `EnhancedTableView`:
- يظهر/يختفي ديناميكياً حسب نص البحث.
- يرتبط بكتالوج خارجي (`GLOBAL_CURRENCY_CATALOG`).
- يضيف العملة لقائمة "انتظار تأكيد" قبل الحفظ الفعلي.
- له تصميم بصري مختلف (Banner أخضر).

**هل يمكن إدخاله في الشجرة؟** لا، لأن طبيعته مختلفة جداً عن أزرار CRUD القياسية.

**من أضافه ومتى:** تمت إضافته في 2026-03 كجزء من تطوير مكتبة العملات العالمية.

---

### [CUSTOM-002] أزرار صفحة الإعدادات في settings/views.py
**الملف:** `modules/settings/views.py`

**ما تفعله:**
أزرار حفظ (Enregistrer) في كل قسم: المعلومات، الإعدادات المالية، التفضيلات، النسخ الاحتياطي.

**لماذا هي مخصصة وليست آلية؟**
صفحة الإعدادات **ليست جدول بيانات**. إنها نماذج (Forms) متعددة في تبويبات مستقلة. `EnhancedTableView` مصمم للجداول وليس للنماذج، لذا لا يمكن استخدامه هنا.

**هل يمكن توحيدها؟** نعم، بإنشاء مكون `StandardButton` مستقبلاً، لكن هذا قرار معماري يستلزم استشارة المالك أولاً.

**ملاحظة:** تم إزالة الرموز التعبيرية (Emojis) من هذه الأزرار كجزء من توحيد 2026-03-29.

---

### [CUSTOM-003] add_custom_action في world_dialog.py
**الملف:** `modules/currency/world_dialog.py` السطر ~54

**ما يفعله:**
زر "Devise Personnalisée" يُضاف في بداية شريط الأدوات الموروث من `EnhancedTableView`.

**لماذا هو مخصص؟**
```python
# [CUSTOM-003] إضافة زر "Devise Personnalisée" في بداية الـ toolbar
# [WHY]: مكتبة العملات تحتاج زر إضافة عملة مخصصة بالإضافة لآلية Smart Discovery.
#        يُدرج في البداية ليكون أول ما يراه المستخدم.
# [DATE]: 2026-03
self.add_custom_action = QAction("Devise Personnalisée", self)
self.table.toolbar.insertAction(self.table.toolbar.actions()[0], self.add_custom_action)
```

هذا الزر **يُضاف على الشجرة** (toolbar الموروثة)، وليس بديلاً عنها. وهذا نمط مقبول للتخصيص.

---

## 🎨 نظام الثيمات

### كيف يعمل؟
```
1. عند تشغيل البرنامج:
   main.py → يقرأ "active_theme" من DB → يطبق get_theme_qss()

2. عند تغيير الثيم:
   settings/views.py → يحفظ في DB → يطبق على QApplication مباشرة

3. كل theme يحتوي على:
   - accent: لون رئيسي
   - bg_dark: خلفية داكنة
   - bg_medium: خلفية متوسطة
   - text_primary: لون النص الرئيسي
   - success/warning/danger: ألوان النظام
```

### أين تُعرَّف الثيمات؟
`core/themes.py` → قاموس `THEMES` ← يمكن إضافة ثيمات جديدة هنا.

---

## 🔄 آلية تحديث البيانات (Data Refresh)

```
المستخدم يُعدِّل بيانات في module A
        ↓
module A يُصدر إشارة dataChanged
        ↓
main.py يستقبل الإشارة → refresh_all()
        ↓
كل الـ modules تُحدَّث (currency_view.refresh(), treasury_view.refresh(), ...)
```

**لماذا هذا النظام؟**
لضمان تناسق البيانات بين الوحدات. مثلاً: عند إضافة دفعة في العملاء، يجب أن تُحدَّث لوحة التحكم والخزينة تلقائياً.

---

## 📌 قرارات معمارية مهمة

| القرار | السبب | تاريخ القرار |
|--------|--------|--------------|
| نصوص فقط في الأزرار (لا أيقونات) | التوحيد الكامل + التحكم من نقطة واحدة | 2026-03-29 |
| French UI | لغة العمل الرسمية للمشروع | منذ البداية |
| SQLite كقاعدة بيانات | خفيف + لا يحتاج server + يعمل offline | منذ البداية |
| EnhancedTableView كجذر وحيد | تجنب التكرار + سهولة التحديث الشامل | 2026-03 |
| IconManager موجود لكن غير مفعَّل في الجداول | متاح للاستخدام المخصص مستقبلاً | 2026-03-29 |
| ShipmentWizard يستخدم EnhancedTableView مع toolbar مخفي | Wizard لا يحتاج PDF/Excel/Importer، فقط جدول + بحث | 2026-04-04 |
| حذف بالنقر المزدوج في Wizard | بديل أزرار X اليدوية، أنظف وأبسط | 2026-04-04 |
| المبالغ محاذات يميناً (AlignRight) | الأعمدة التي تحتوي DA/EUR/USD/$/€ أو أرقام → يمين | 2026-04-04 |
| عمود N° محاذات وسط (AlignCenter) | الترقيم التلقائي يكون في المنتصف | 2026-04-04 |
| مجاميع Footer محاذات يميناً | تتوافق مع محاذاة الأعمدة الرقمية | 2026-04-04 |
| كشف تلقائي متقدم (Auto-Detection) | 9 أنواع: N°, Dates, Codes, Status, Phones, %, Amounts, Numbers, Text | 2026-04-04 |
| تعديل marchandises بالنقر المزدوج | النقر المزدوج يملأ النموذج + زر Modifier + Annuler | 2026-04-04 |
| تعديل conteneurs بالنقر المزدوج | النقر المزدوج يملأ حقل الإدخال + زر Modifier + Annuler | 2026-04-04 |
| Quick Add Client في Wizard Step 3 | زر [+] → SmartFormDialog لإضافة عميل جديد | 2026-04-04 |
| Catalogue Types de Marchandises | زر [+] → GenericCatalogDialog لإدارة الأنواع | 2026-04-04 |
| توحيد تصميم جدول Reception | EnhancedTableView مع toolbar مخفي في ReceiveWarehouseDialog | 2026-04-04 |
| إصلاح حفظ cbm_price_dzd و discount | `create_shipment_with_goods()` يحفظ الآن السعر والخصم بالدينار | 2026-04-04 |
| Quick Add حسابات الخزينة | TreasuryTransferDialog، ReceivePaymentDialog، LicenseToBankTransferDialog — زر [+] للحسابات | 2026-04-04 |
| Quick Add العملاء | ReceivePaymentDialog — زر [+] للعملاء والحسابات | 2026-04-04 |
| توحيد سلوك القوائم المنسدلة (setup_combo) | كل Combo يمر عبر create_quick_add_layout() → قابل للكتابة + تصفية فورية | 2026-04-04 |
| تحسينات Dettes Externes | فلترة بالعملة، Quick Add للخزينة، سعر الصرف، 5 أعمدة جديدة | 2026-04-05 |
| أعمدة ديناميكية Dettes Externes | exchange_rate + amount_da لتوحيد الحسابات بالدينار | 2026-04-05 |
