# 📋 سجل التغييرات — CHANGELOG
# Shipping Company Application
# =============================================
# ⚠️ كل تعديل يُسجَّل هنا قبل تطبيقه.
# ⚠️ Every change must be logged here BEFORE being applied.
# =============================================
# الصيغة / Format:
#
# ## [YYYY-MM-DD] — وصف التغيير
# **النوع / Type:** BUG_FIX | FEATURE | REFACTOR | CUSTOM | ARCHITECTURE
# **الملفات المتأثرة / Files:** ...
# **المشكلة / Problem:** ...
# **الحل / Solution:** ...
# **سبب التخصيص / Custom Reason:** (إذا كان CUSTOM)
# **كيفية الرجوع / Rollback:** ...
# =============================================

---

## [2026-04-05] — Colonnes dynamiques Dettes Externes (Multi-Devises → DA)

**النوع:** FEATURE + ARCHITECTURE

**الملفات المتأثرة:**
- `core/models.py` — ExternalTransaction (exchange_rate, amount_da)
- `modules/external_debt/service.py` — create_operation, update_operation_full, _get_contact_totals, get_all_history, get_contact_history
- `modules/external_debt/repository.py` — get_contact_balance
- `modules/external_debt/views.py` — OperationDialog, ContactListTab, DebtJournalTab, HistoryDialog

**المشكلة / الهدف:**
كانت العمليات بالعملات المختلفة (USD, EUR...) تُخزن بالمبلغ الأصلي فقط، مما يجعل جمع الأرصدة معقداً.
المطلوب: تخزين المبلغ بالدينار دائماً لتسهيل الحسابات والعرض.

**الحل / ما تم:**
1. **نموذج ExternalTransaction:**
   - إضافة `exchange_rate` (سعر الصرف المستخدم)
   - إضافة `amount_da` (المبلغ بالدينار = amount × exchange_rate)

2. **Service:**
   - `create_operation()` يحسب `amount_da` تلقائياً عند الحفظ
   - `update_operation_full()` يُحدّث `amount_da` عند التعديل
   - `_get_contact_totals()` يستخدم `amount_da` للحساب
   - `get_all_history()` و `get_contact_history()` يُرجعان `currency_code`, `exchange_rate`, `amount_da`

3. **Repository:**
   - `get_contact_balance()` يستخدم `amount_da` للحساب الموحد

4. **Views:**
   - **OperationDialog:** حقل سعر الصرف يظهر للعملات الأجنبية فقط
   - **ContactListTab:** 5 أعمدة جديدة (Total Prêté, Total Reçu, Total Emprunté, Total Remboursé, Solde Net) بالدينار
   - **DebtJournalTab:** أعمدة جديدة (Montant, Devise, Taux, Montant (DA))
   - **HistoryDialog:** نفس الأعمدة الجديدة

**مثال عملي:**
```
عملية: 5,000 USD بسعر صرف 135.50
→ amount = 5,000
→ exchange_rate = 135.50
→ amount_da = 677,500 DA

الرصيد الصافي = مجموع جميع amount_da بالدينار
```

**كيفية الرجوع / Rollback:**
لاستعادة الكود القديم:
```bash
git checkout HEAD~1 -- core/models.py modules/external_debt/
```

---

## [2026-04-05] — Améliorations du module Dettes Externes

**النوع:** FEATURE

**الملفات المتأثرة:**
- `modules/external_debt/views.py` — OperationDialog, ContactListTab
- `modules/external_debt/service.py` — get_all_contacts, _get_contact_totals

**المشكلة / الهدف:**
1. لم يكن هناك فلترة للحسابات حسب العملة في عملية جديدة.
2. لم يكن هناك Quick Add لحسابات الخزينة.
3. لم يكن هناك حقل لسعر الصرف عند التعامل بعملات أجنبية.
4. كانت قائمة المتعاملين تعرض عمود واحد فقط للأرصدة.

**الحل / ما تم:**
1. **فلترة الحسابات بالعملة:** قائمة منسدلة لاختيار العملة → تُظهر حسابات تلك العملة فقط.
2. **Quick Add للخزينة:** زر `[+]` بجانب قائمة الحسابات لإضافة حساب جديد بسرعة.
3. **حقل سعر الصرف:** يظهر فقط عند اختيار عملة أجنبية (USD, EUR...) لإدخال سعر الصرف اليومي.
4. **أعمدة جديدة في قائمة المتعاملين:**
   - Total Prêté (إجمالي ما أُقرض)
   - Total Reçu (إجمالي ما استُلم من سداد قروض)
   - Total Emprunté (إجمالي ما اقتُرض)
   - Total Remboursé (إجمالي ما سُدد من ديون)
   - Solde Net (الرصيد الصافي بالألوان)
5. **المحاكاة المحسّنة:** تعرض المبلغ بالعملة الأصلية + المكافئ بالدينار.

**سبب التخصيص:**
لا يوجد تخصيص — تحسينات واجهة المستخدم ومنطق الأعمال.

**كيفية الرجوع / Rollback:**
لاستعادة الكود القديم:
```bash
git checkout HEAD~1 -- modules/external_debt/views.py modules/external_debt/service.py
```

---

## [2026-04-04] — إصلاح الكشف التلقائي للمحاذاة (الافتراضي كان 'left' بدلاً من 'auto')

**النوع:** BUG_FIX + ARCHITECTURE

**الملفات المتأثرة:**
- `components/enhanced_table.py`

**المشكلة:**
المحاذاة التلقائية لم تكن تعمل على أي جدول!
السبب: `align_type = self._header_align_map.get(col_idx, 'left')`
الافتراضي كان `'left'` → شرط `if align_type == 'auto':` لم يتحقق أبداً → الكشف التلقائي لم يعمل!

**الحل / ما تم:**
- تغيير الافتراضي من `'left'` إلى `'auto'`.
- الآن الكشف التلقائي يعمل على كل الجداول تلقائياً.

**كيفية الرجوع / Rollback:**
لاستعادة السلوك القديم (بدون كشف تلقائي):
```python
align_type = self._header_align_map.get(col_idx, 'left')
```

---

## [2026-04-04] — توحيد سلوك القوائم المنسدلة (setup_combo)

**النوع:** REFACTOR + ARCHITECTURE

**الملفات المتأثرة:**
- `components/dialogs.py` — إضافة `setup_combo()`

**المشكلة / الهدف:**
القوائم المنسدلة في كل البرنامج كانت مختلطة:
- بعضها قابل للكتابة، بعضها لا.
- بعضها فيه تصفية، بعضها لا.
- لا نمط موحد → صعوبة الصيانة.

**الحل / ما تم:**
- إضافة دالة `setup_combo()` في `components/dialogs.py`.
- كل `QComboBox` يمر عبر `create_quick_add_layout()` يُهيّأ تلقائياً بـ:
  1. `setEditable(True)` — قابل للكتابة
  2. `NoInsert` — لا يُدخل قيم جديدة تلقائياً
  3. `PlaceholderText` — "Rechercher..."
  4. `QCompleter` — تصفية فورية (MatchContains, CaseInsensitive)
- هذا تغيير في الجذر (Tree System) → كل القوائم التي تستخدم `create_quick_add_layout()` تتأثر تلقائياً.

**سبب التخصيص:**
لا يوجد تخصيص — تغيير آلي في الجذر يتبع القاعدة الأولى (نظام الشجرة).

**كيفية الرجوع / Rollback:**
لاستعادة السلوك القديم، احذف استدعاء `setup_combo(combo)` من `create_quick_add_layout()`.

---

## [2026-04-04] — Quick Add pour les comptes de trésorerie (3 modules)

**النوع:** FEATURE

**الملفات المتأثرة:**
- `modules/treasury/views.py` — TreasuryTransferDialog (`from_account`, `to_account`)
- `modules/customers/views.py` — ReceivePaymentDialog (`customer_combo`, `account_combo`)
- `modules/licenses/views.py` — LicenseToBankTransferDialog (`cmb_source`, `cmb_dest`)

**المشكلة / الهدف:**
القوائم المهمة لم تكن تدعم Quick Add `[+]`:
- حسابات الخزينة في TreasuryTransferDialog
- العملاء والحسابات في ReceivePaymentDialog
- حسابات المصدر والوجهة في LicenseToBankTransferDialog

**الحل / ما تم:**
- إضافة زر `[+]` بجانب كل قائمة مهمة عبر `create_quick_add_layout()`.
- `_quick_add_account()` في TreasuryTransferDialog — يستخدم `ACCOUNT_SCHEMA` الأصلي.
- `_quick_add_customer()` و `_quick_add_account()` في ReceivePaymentDialog.
- `_quick_add_account()` في LicenseToBankTransferDialog.
- جميع الدوال تستدعي النماذج الأصلية فقط (لا تصميم جديد).

**سبب التخصيص:**
لا يوجد تخصيص — تطبيق القاعدة 10 (Quick Add Pattern).

**كيفية الرجوع / Rollback:**
لاستعادة الكود القديم:
```bash
git checkout HEAD~1 -- modules/treasury/views.py modules/customers/views.py modules/licenses/views.py
```

---

## [2026-04-04] — Quick Add Client يستدعي CUSTOMER_SCHEMA الأصلي فقط

**النوع:** REFACTOR

**الملفات المتأثرة:**
- `modules/logistics/shipment_wizard.py`

**المشكلة / الهدف:**
Quick Add Client كان يُعيد تصميم النموذج. الصحيح هو استدعاء `CUSTOMER_SCHEMA` الأصلي فقط.

**الحل / ما تم:**
- `_quick_add_customer()` يستدعي `CUSTOMER_SCHEMA` من `customers/views.py`.
- لا تصميم جديد — فقط استدعاء للنموذج الأصلي.
- نفس النمط المستخدم في `CustomerGoodsTab` و `CustomerPaymentsTab`.

**كيفية الرجوع / Rollback:**
لاستعادة الكود القديم:
```bash
git checkout HEAD~1 -- modules/logistics/shipment_wizard.py
```

---

## [2026-04-04] — تحسين Quick Add Client لاستخدام CUSTOMER_SCHEMA الأصلي

**النوع:** REFACTOR

**الملفات المتأثرة:**
- `modules/logistics/shipment_wizard.py`

**المشكلة / الهدف:**
Quick Add Client في ShipmentWizard كان يستخدم 3 حقول فقط (name, phone, address).
الأصل هو استخدام `CUSTOMER_SCHEMA` الأصلي من `customers/views.py` الذي يحتوي على 5 حقول:
1. Nom du Client (required)
2. Téléphone
3. Adresse (multiline)
4. Solde Initial (DA)
5. Notes

**الحل / ما تم:**
- استيراد `CUSTOMER_SCHEMA` الأصلي من `modules.customers.views`.
- استخدام نفس النموذج الأصلي لضمان التوحيد.

**كيفية الرجوع / Rollback:**
لاستعادة الكود القديم:
```bash
git checkout HEAD~1 -- modules/logistics/shipment_wizard.py
```

---

## [2026-04-04] — إصلاح خطأ Quick Add Client في ShipmentWizard

**النوع:** BUG_FIX

**الملفات المتأثرة:**
- `modules/logistics/shipment_wizard.py`

**المشكلة:**
```
TypeError: cannot unpack non-iterable Customer object
```
`create_customer()` يُرجع كائن `Customer` مباشرة وليس tuple `(success, msg, client_id)`.

**الحل / ما تم:**
- تغيير `_quick_add_customer()` لاستقبال كائن `Customer` مباشرة.
- استخدام `customer.id` للحصول على المعرف.
- إضافة `try/except` لمعالجة الأخطاء.

**كيفية الرجوع / Rollback:**
لاستعادة الكود القديم:
```bash
git checkout HEAD~1 -- modules/logistics/shipment_wizard.py
```

---

## [2026-04-04] — إصلاح حفظ cbm_price_dzd و discount عند إنشاء البضائع

**النوع:** BUG_FIX

**الملفات المتأثرة:**
- `modules/logistics/service.py`

**المشكلة:**
عند إنشاء بضائع عبر `create_shipment_with_goods()`، لم يتم حفظ `cbm_price_dzd` و `discount` في قاعدة البيانات.
كان يُحفظ فقط `cbm_price_usd` و `discount_usd`.
النتيجة: جدول Reception يعرض 0 للأعمدة الثلاثة الأخيرة (Prix, Remise, Total).

**الحل / ما تم:**
- إضافة `cbm_price_dzd=g["price"]` عند إنشاء `CustomerGoods`.
- إضافة `discount=g["discount"]` عند إنشاء `CustomerGoods`.
- الاحتفاظ بـ `cbm_price_usd` و `discount_usd` كحقول اختيارية.

**سبب التخصيص:**
لا يوجد تخصيص — إصلاح خطأ في حفظ البيانات.

**كيفية الرجوع / Rollback:**
لاستعادة الكود القديم:
```bash
git checkout HEAD~1 -- modules/logistics/service.py
```

---

## [2026-04-04] — توحيد تصميم جدول Reception (ReceiveWarehouseDialog)

**النوع:** REFACTOR + ARCHITECTURE

**الملفات المتأثرة:**
- `modules/logistics/views.py`

**المشكلة / الهدف:**
`ReceiveWarehouseDialog` كان يستخدم `QTableWidget` يدوي التصميم لعرض بضائع الحاوية عند الاستلام.
هذا يخالف القاعدة الأولى (نظام الشجرة) ويجعل التحكم في التصميم صعباً.

**الحل / ما تم:**
- استبدال `QTableWidget` بـ `EnhancedTableView(table_id="reception_goods")`.
- إخفاء شريط الأدوات (toolbar) وفلتر الحالة (status filter) والـ footer.
- تحديث `_load_goods()` لاستخدام `add_row()` و `clear_rows()`.
- الاحتفاظ بكل الحسابات والمنطق كما هو (CBM, Prix, Remise, Total).

**سبب التخصيص:**
- `[CUSTOM] 2026-04-04` - EnhancedTableView في Reception مع toolbar/status_filter مخفيين.
- `[WHY]`: Dialogue de reception لا يحتاج أزرار PDF/Excel/Importer. الجدول الموحد مع البحث كافٍ.

**كيفية الرجوع / Rollback:**
لاستعادة QTableWidget اليدوي، أعد نسخ الكود القديم من Git:
```bash
git checkout HEAD~1 -- modules/logistics/views.py
```

---

## [2026-04-04] — Quick Add Client + Catalogue Marchandises (Wizard Step 3)

**النوع:** FEATURE

**الملفات المتأثرة:**
- `modules/logistics/shipment_wizard.py`

**المشكلة / الهدف:**
المرحلة 3 من ShipmentWizard لم تكن تدعم إضافة عميل جديد أو نوع بضاعة جديد مباشرة من النموذج.
كان يجب مغادرة النافذة لإضافة هذه البيانات (يخالف القاعدة 10 و 11).

**الحل / ما تم:**
- زر `[+]` بجانب `Client` → يفتح `SmartFormDialog` لإضافة عميل جديد.
- زر `[+]` بجانب `Type de Marchandise` → يفتح `GenericCatalogDialog` لإدارة أنواع البضائع.
- `_quick_add_customer()` دالة جديدة للإضافة السريعة للعملاء.
- `_open_goods_catalog()` دالة جديدة لفتح كتالوج أنواع البضائع.
- `_load_goods_types()` دالة موحدة لتحميل الأنواع من `LicenseGoodsCatalog`.

**سبب التخصيص:**
لا يوجد تخصيص — تطبيق القاعدة 10 (Quick Add) والقاعدة 11 (Catalog Management).

**كيفية الرجوع / Rollback:**
لاستعادة الحقول بدون أزرار `[+]`، أعد `form.addRow("Client:", self.customer_combo)` و `form.addRow("Type de Marchandise:", self.goods_type_combo)`.

---

## [2026-04-04] — تعديل أسطر conteneurs بالنقر المزدوج (Wizard Step 2)

**النوع:** FEATURE

**الملفات المتأثرة:**
- `modules/logistics/shipment_wizard.py`

**المشكلة / الهدف:**
المرحلة 2 من ShipmentWizard (Conteneurs) لم تكن تدعم تعديل أرقام الحاويات المُدخلة.
الحذف كان بالنقر المزدوج (غير واضح)، والتعديل غير موجود.

**الحل / ما تم:**
- النقر المزدوج على سطر يملأ حقل الإدخال برقم الحاوية للتعديل.
- زر `+ Ajouter` يتحول إلى `✓ Modifier` (لون أصفر) في وضع التعديل.
- زر `Annuler` يظهر لإلغاء التعديل.
- `_editing_container_index` يتتبع الحاوية المُعدّلة.
- `_cancel_container_edit()` دالة جديدة للخروج من وضع التعديل.
- `_add_or_edit_container()` دالة موحدة للإضافة والتعديل.

**سبب التخصيص:**
لا يوجد تخصيص — تحسين واجهة المستخدم في Wizard (نفس نمط المرحلة 3).

**كيفية الرجوع / Rollback:**
لاستعادة الحذف بالنقر المزدوج، أعد `_on_container_double_clicked` لحذف الحاوية مباشرة.

---

## [2026-04-04] — تعديل أسطر marchandises بالنقر المزدوج (Wizard Step 3)

**النوع:** FEATURE

**الملفات المتأثرة:**
- `modules/logistics/shipment_wizard.py`

**المشكلة / الهدف:**
المرحلة 3 من ShipmentWizard (Marchandises) لم تكن تدعم تعديل الأسطر المُدخلة.
الحذف كان بالنقر المزدوج (غير واضح)، والتعديل غير موجود.

**الحل / ما تم:**
- النقر المزدوج على سطر يملأ النموذج بالبيانات للتعديل.
- زر `+ Ajouter` يتحول إلى `✓ Modifier` (لون أصفر) في وضع التعديل.
- زر `Annuler` يظهر لإلغاء التعديل والعودة للوضع العادي.
- `_editing_row_index` يتتبع السطر المُعدّل.
- `_clear_goods_form()` دالة جديدة لتفريغ النموذج.
- `_cancel_edit()` دالة جديدة للخروج من وضع التعديل.
- عند تغيير الحاوية → إلغاء التعديل تلقائياً.

**سبب التخصيص:**
لا يوجد تخصيص — تحسين واجهة المستخدم في Wizard.

**كيفية الرجوع / Rollback:**
لاستعادة الحذف بالنقر المزدوج، أعد `_on_good_double_clicked` لحذف السطر مباشرة.

---

## [2026-04-04] — تحسين تلقائي للمحاذاة في كل الجداول (Auto-Detection Avancée)

**النوع:** REFACTOR + ARCHITECTURE

**الملفات المتأثرة:**
- `components/enhanced_table.py`

**المشكلة / الهدف:**
بعض أنواع الحقول لم تكن تُكتشف تلقائياً:
- التواريخ (`2026-04-04`, `04/04/2026`) كانت محاذات لليسار
- الرموز (`MAIN_DZD`, `EUR`, `CAISSE`) كانت محاذات لليسار
- الحالات (`Actif`, `Validée`, `OPEN`) كانت محاذات لليسار
- الهواتف (`0555123456`) كانت محاذات لليسار
- النسب المئوية (`30%`) كانت محاذات لليسار

**الحل / ما تم:**
إضافة 4 دوال كشف تلقائي جديدة في `EnhancedTableView`:
- `_is_date()` → كشف التواريخ → محاذاة وسط
- `_is_status()` → كشف الحالات → محاذاة وسط
- `_is_code()` → كشف الرموز → محاذاة وسط
- `_is_phone()` → كشف الهواتف → محاذاة وسط
- `%` → كشف النسب → محاذاة يمين

**جدول المحاذاة الكامل الآن:**

| النوع | المحاذاة | أمثلة |
|-------|----------|-------|
| N° | وسط | `1`, `2`, `3` |
| التواريخ | وسط | `2026-04-04`, `04/04/2026` |
| الرموز/الأكواد | وسط | `MAIN_DZD`, `EUR`, `CAISSE` |
| الحالات | وسط | `Actif`, `Validée`, `OPEN` |
| الهواتف | وسط | `0555123456`, `+213 555...` |
| المبالغ | يمين | `1,500.00 DA`, `200.00 $` |
| النسب % | يمين | `30%`, `15.5%` |
| الأرقام | يمين | `12.5000`, `50` |
| النصوص | يسار | `أحمد`, `Chaussures` |

**سبب التخصيص:**
لا يوجد تخصيص — تغيير آلي في الجذر (Tree System) يؤثر على كل الجداول.

**كيفية الرجوع / Rollback:**
لاستعادة المحاذاة البسيطة، احذف الدوال `_is_date`, `_is_status`, `_is_code`, `_is_phone` وأعد شرط `else: align_type = 'left'`.

---

## [2026-04-04] — محاذاة المبالغ يميناً في كل الجداول (Tree System Change)

**النوع:** REFACTOR + ARCHITECTURE

**الملفات المتأثرة:**
- `components/enhanced_table.py`

**المشكلة / الهدف:**
كل المبالغ والأرقام في كل جداول البرنامج كانت محاذات لليسار رغم وجود كشف تلقائي للمبالغ (`'DA'`, `'EUR'`, `'USD'`, `'$'`, `'€'`).
السبب: الكود يكتشف النوع `'amount'` لكن يجبر المحاذاة على اليسار بتعليق `# TOUT À GAUCHE selon règle`.

**الحل / ما تم:**
- تغيير محاذاة `'amount'` و `'right'` من `AlignLeft` إلى `AlignRight` في `add_row()`.
- تغيير محاذاة المجاميع في الـ footer من `AlignLeft` إلى `AlignRight`.
- محاذاة `'center'` تُطبق `AlignCenter` (لعمود N°).
- هذا تغيير في الجذر (Tree System) → ينعكس تلقائياً على **كل الجداول** في البرنامج.

**سبب التخصيص:**
لا يوجد تخصيص — هذا تغيير آلي في الجذر يتبع القاعدة الأولى (نظام الشجرة).

**كيفية الرجوع / Rollback:**
لاستعادة المحاذاة اليسرى، أعد تغيير `AlignRight` إلى `AlignLeft` في `add_row()` و `_update_footer()`.

---

## [2026-04-04] — توحيد تصميم جداول ShipmentWizard (EnhancedTableView)

**النوع:** REFACTOR + ARCHITECTURE

**الملفات المتأثرة:**
- `modules/logistics/shipment_wizard.py`

**المشكلة / الهدف:**
المرحلة 2 (Conteneurs) والمرحلة 3 (Marchandises) في ShipmentWizard كانتا تستخدمان `QTableWidget` يدوي التصميم.
هذا يخالف القاعدة الأولى (نظام الشجرة) ويجعل التحكم في التصميم صعباً (يتطلب تعديل كل جدول على حدة).

**الحل / ما تم:**
- استبدال `QTableWidget` بـ `EnhancedTableView` في `_build_step2()` و `_build_step3()`.
- إخفاء شريط الأدوات (toolbar) وفلتر الحالة (status filter) والـ footer لأنهما غير ضروريين في Wizard.
- تحديث `_refresh_containers_table()` و `_refresh_goods_table()` لاستخدام `add_row()` و `clear_rows()`.
- حذف العناصر يتم الآن بالنقر المزدوج على الصف بدلاً من أزرار X يدوية.
- الاحتفاظ بكل الحسابات والمنطق كما هو (CBM, Prix, Remise, Total).

**سبب التخصيص:**
- `[CUSTOM] 2026-04-04` - EnhancedTableView في Wizard مع toolbar/status_filter مخفيين.
- `[WHY]`: Wizard لا يحتاج أزرار PDF/Excel/Importer. الجدول الموحد مع البحث كافٍ.
- التصميم الآن يتبع الشجرة: أي تغيير في EnhancedTableView ينعكس تلقائياً.

**كيفية الرجوع / Rollback:**
لاستعادة QTableWidget اليدوي، أعد نسخ الكود القديم من Git:
```bash
git checkout HEAD~1 -- modules/logistics/shipment_wizard.py
```

---

## [2026-03-29] — إصلاح مشكلة اختفاء العملات (Root Cause Analysis)

**النوع:** BUG_FIX + ARCHITECTURE

**الملفات المتأثرة:**
- `main.py`
- `core/init_data.py`

**المشكلة (كما وردت):**
"العملات لا تضهر" (Currencies are not showing in the summary tab).
بعد تطبيق استراتيجية تشخيص محترفة (عزل واجهة المستخدم والاتصال المباشر بقاعدة البيانات عبر سكربت اختباري)، تبين أن دالة المجموع `get_currency_financial_summary()` لا تفشل، بل تُرجع `[]` سريعاً جداً (0.09 ثانية).
بالفحص المباشر لجداول `SQLite` اتضح أن جدول `currencies` كان **فارغاً تماماً (0 row)**!

**السبب الجذري (Root Cause):**
البرنامج كان يقوم بإنشاء جداول قاعدة البيانات عند البدء عبر `create_tables()` ولكنه **لا يقوم بحقن البيانات الافتراضية** (كالعملة الافتراضية DZD والعملات العالمية). حقن البيانات كان يتم فقط في دالة `reset_database()` الموجودة في الإعدادات. مما يعني أن أي تشغيل محلي جديد للبرنامج على قاعدة بيانات جديدة سيؤدي إلى جداول فارغة تماماً.

**الحل / ما تم:**
تم إضافة استدعاء `initialize_system_data()` في `main.py` مباشرة بعد `sync_database_schema()`.
الآن، عند كل إقلاع، يتأكد البرنامج من وجود البيانات الأساسية (DZD, USD, EUR وحسابات الخزينة)، وإذا لم يجدها يقوم بإنشائها، مما يمنع نهائياً مشكلة "الجداول الفارغة".

---

## [2026-03-29] — إصلاح بطء الإقلاع (4 ثوانٍ) وتحديث العملات

**النوع:** ARCHITECTURE + REFACTOR

**الملفات المتأثرة:**
- `main.py`
- `components/enhanced_table.py`
- `modules/settings/views.py`
- `modules/currency/world_dialog.py`

**المشكلة:**
كانت أزرار البرنامج تعمل بطريقتين مختلفتين:
1. أزرار موحدة عبر `EnhancedTableView` (الشجرة).
2. أزرار يدوية في كل module بشكل مستقل (شاذة عن الشجرة).
هذا يعني أن تغيير النمط البصري لا يحدث بشكل شامل، بل يتطلب التعديل في كل ملف على حدة.

**الحل:**
- إعادة كل أزرار `EnhancedTableView` لنصوص فقط (`ToolButtonTextOnly`).
- إزالة كل استدعاءات `IconManager` من الجداول.
- إزالة الأيقونات SVG من تبويبات `main.py`.
- توثيق الأزرار "المخصصة" التي لا يمكن إدخالها في الشجرة.

**كيفية الرجوع:**
لاستعادة نظام الأيقونات SVG في الجداول، أعد نسخ الكود التالي في `_create_toolbar()`:
```python
# إضافة الأيقونة للزر: QAction(IconManager.get_icon("plus", color), "Nouveau", self)
# وتفعيل: toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
```

---

## [2026-03-29] — إصلاح خطأ SyntaxError في نظام الثيمات

**النوع:** BUG_FIX

**الملفات المتأثرة:**
- `core/themes.py`

**المشكلة:**
```
SyntaxError: unexpected character after line continuation character
```
كان الخطأ في استخدام `\"\"\"` داخل docstring بطريقة خاطئة أدت لعدم تشغيل البرنامج.

**الحل:**
إعادة كتابة docstring المتأثرة باستخدام علامات صحيحة للتعريق.

**كيفية الرجوع:**
الخطأ كان نحوياً فقط، لا يوجد rollback مطلوب.

---

## [2026-03-29] — إضافة نظام الأيقونات SVG (IconManager)

**النوع:** FEATURE

**الملفات المتأثرة:**
- `utils/icon_manager.py` ← [NEW]
- `assets/icons/*.svg` ← [NEW] (19 أيقونة)

**الوصف:**
إنشاء محرك أيقونات ذكي يقوم بـ:
1. تحميل ملفات SVG من `assets/icons/`.
2. تلوينها ديناميكياً بلون Accent الثيم النشط.
3. إرجاعها كـ `QIcon` استخدامها في أي مكان.

**ملاحظة:**
تم لاحقاً إزالة الأيقونات من الجداول والتبويبات للعودة لنمط النصوص الصرفة. الـ `IconManager` لا يزال موجوداً ومتاحاً للاستخدام في الأزرار المخصصة حيث يكون ذلك مبرراً.

---

## [2026-03-29] — إضافة 10 ثيمات جديدة

**النوع:** FEATURE

**الملفات المتأثرة:**
- `core/themes.py`

**الثيمات المضافة:**
1. Emerald (الافتراضي) — أخضر زمردي
2. Ocean Blue — أزرق محيطي
3. Crimson — قرمزي داكن
4. Golden — ذهبي ملكي
5. Purple Haze — بنفسجي
6. Arctic — رمادي جليدي
7. Sunset — برتقالي غروب
8. Rose Gold — وردي ذهبي
9. Matrix — أخضر نيون
10. Monochrome — أبيض وأسود

**كيف يعمل نظام الثيمات:**
- يُحفظ الثيم النشط في قاعدة البيانات (جدول `settings`).
- عند فتح البرنامج، يُقرأ ويُطبَّق تلقائياً عبر `get_theme_qss()`.
- يمكن تغييره من `Paramètres > Thème`.

---

## [2026-03-29] — إضافة منظومة التوثيق (هذا الملف)

**النوع:** ARCHITECTURE

**الملفات المضافة:**
- `GOLDEN_RULES.md` ← القواعد الذهبية الإلزامية
- `CHANGELOG.md` ← هذا الملف (سجل التغييرات)
- `UI_ARCHITECTURE.md` ← القرارات التقنية التفصيلية

**السبب:**
في كل جلسة عمل جديدة، كان يضيع وقت كبير في إعادة شرح فلسفة المشروع وقواعده للوكيل الذكي. هذا الحل يضمن استمرارية الفهم بدون تكرار.

---

## 📝 قالب إضافة تغيير جديد (Copy & Paste)

```markdown
## [YYYY-MM-DD] — عنوان التغيير

**النوع:** BUG_FIX | FEATURE | REFACTOR | CUSTOM | ARCHITECTURE
**الملفات المتأثرة:**
- `path/to/file.py`

**المشكلة / الهدف:**
...

**الحل / ما تم:**
...

**سبب التخصيص (إن وُجد):**
...

**كيفية الرجوع (Rollback):**
...
```
