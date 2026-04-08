# ERRORS LOG - سجل الأخطاء

هذا الملف يوثق كل الأخطاء التي واجهتنا أثناء التطوير لكي لا نكررها.

---

## 1. أخطاء PyQt6 (تكامل الإصدار 6)

### 1.1 QFont.Bold غير موجود
```python
# ❌ خطأ
QFont("Segoe UI", 16, QFont.Bold)

# ✅ صحيح
QFont("Segoe UI", 16, QFont.Weight.Bold)
```
**الملفات:** `error_dialog.py`
**السبب:** في PyQt6، القيم المنبثقة من الكلاسات تستخدم `.Attribute` وليس `Class.Attribute`

---

### 1.2 QSizePolicy.Expanding غير موجود
```python
# ❌ خطأ
QSizePolicy.Expanding, QSizePolicy.Expanding

# ✅ صحيح
QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
```
**الملفات:** `error_dialog.py`
**السبب:** نفس السبب — PyQt6 يتطلب `.Policy.Expanding`

---

### 1.3 addItems() لا تقبل tuples
```python
# ❌ خطأ
combo.addItems([
    ("Aujourd'hui", "today"),
    ("Cette Semaine", "week"),
])

# ✅ صحيح — addItem لكل عنصر
combo.addItem("Aujourd'hui", "today")
combo.addItem("Cette Semaine", "week")
```
**الملفات:** `settings/views.py`
**السبب:** `addItems()` تتوقع قائمة نصوص فقط. `addItem()` هو الذي يقبل (text, data)

---

## 2. أخطاء الاستيراد (Import Errors)

### 2.1 QWidget غير مستورد
```python
# ❌ خطأ — QWidget مستخدم لكن غير مستورد
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, ...
)

# ✅ صحيح
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, ...
)
```
**الملفات:** `shipment_wizard.py`
**القاعدة:** ALWAYS verify all widgets used are imported

---

### 2.2 confirm_action غير مستورد
```python
# ❌ خطأ — استيراد confirm_delete فقط
from components.dialogs import (
    show_error, show_success, confirm_delete, ...
)

# ✅ صحيح — استيراد الاثنين
from components.dialogs import (
    show_error, show_success, confirm_delete, confirm_action, ...
)
```
**الملفات:** `logistics/views.py`, `licenses/views.py`
**القاعدة:** `confirm_action` و `confirm_delete` هما دالتان مختلفتان — استورد الاثنين معاً

---

### 2.3 TRANSACTION_TYPE_DEBIT من مكان خاطئ
```python
# ❌ خطأ
from core.models import (TRANSACTION_TYPE_DEBIT, PAYMENT_TYPE_CASH)

# ✅ صحيح
from utils.constants import (TRANSACTION_TYPE_DEBIT, PAYMENT_TYPE_CASH)
```
**الملفات:** `logistics/service.py`
**القاعدة:** الثوابت (constants) في `utils/constants.py` وليس `core/models.py`

---

## 3. أخطاء الكلاسات غير المعرّفة

### 3.1 OpenBillDialog غير مكتوب
```python
# ❌ خطأ — الكلاس مستخدم لكن لم يُكتب أبداً
dialog = OpenBillDialog(self.service, parent=self)

# ✅ الحل — إنشاء الكلاس
class OpenBillDialog(QDialog):
    ...
```
**الملفات:** `logistics/views.py`
**القاعدة:** قبل استخدام كلاس، تأكد أنه معرّف أو مستورد

---

## 4. أخطاء الوصول (Attribute Errors)

### 4.1 self.attribute غير موجود في الكلاس
```python
# ❌ خطأ — ContainersTab لا يملك treasury_service
self.treasury_service  # في ContainersTab

# ✅ الحل — إنشاء الخدمة محلياً
from modules.treasury.service import TreasuryService
TreasuryService()
```
**الملفات:** `logistics/views.py`
**القاعدة:** تحقق من __init__ قبل الوصول لـ self.attribute

---

### 4.2 currentRow() غير موجود في EnhancedTableView
```python
# ❌ خطأ
row = self.table.currentRow()

# ✅ صحيح
selected = self.table.get_selected_rows()
if selected:
    row = selected[0]
```
**الملفات:** `licenses/views.py`
**القاعدة:** EnhancedTableView يستخدم `get_selected_rows()` وليست `currentRow()`

---

## 5. أخطاء قاعدة البيانات

### 5.1 عمود مكرر في النموذج
```python
# ❌ خطأ — عمود address مكرر
class CurrencySupplier:
    address = Column(Text)   # السطر 109
    ...
    address = Column(Text)   # السطر 124 — مكرر!

# ✅ الحل — حذف النسخة الثانية
```
**الملفات:** `core/models.py`
**القاعدة:** لا تكرر أسماء الأعمدة في نفس النموذج

---

## 6. أخطاء التعديل (Critical Editing Mistakes)

### 6.1 حذف سطور الإنشاء عند تغيير التسمية
```python
# ❌ خطأ — حذفت سطور الإنشاء عند تغيير اسم التبويب
# قبل:
self.purchases_tab = CurrencyPurchasesTab(...)  # ❌ حُذف!
self.purchases_tab.dataChanged.connect(...)     # ❌ حُذف!
self.tabs.addTab(self.purchases_tab, "🛒 Historique Achats")

# بعد (خطأ):
self.tabs.addTab(self.purchases_tab, "Achats")  # 💥 crash!

# ✅ الحل — غيّر النص فقط
self.purchases_tab = CurrencyPurchasesTab(...)  # يبقى
self.purchases_tab.dataChanged.connect(...)     # يبقى
self.tabs.addTab(self.purchases_tab, "Achats")  # غيّر النص فقط
```
**الملفات:** `currency/views.py`, `customers/views.py`, `logistics/views.py`, `licenses/views.py`
**القاعدة الذهبية:**
> **عند تغيير اسم تبويب أو حقل: غيّر النص/التسمية فقط. لا تحذف سطر الإنشاء أو الربط.**

---

## 7. أخطاء منطقية

### 7.1 get_recent يُرجع الأقدم بدلاً من الأحدث
```python
# ❌ خطأ — ترتيب تصاعدي
query = query.order_by(self.model.id)

# ✅ صحيح — ترتيب تنازلي
query = query.order_by(self.model.id.desc())
```
**الملفات:** `core/repositories.py`

---

### 7.2 GenericCatalogDialog وسائط خاطئة
```python
# ❌ خطأ — وسائط غير موجودة
GenericCatalogDialog(
    fetch_cb=lambda: [...],
    create_cb=lambda text: ...,
    delete_cb=lambda cid: ...,
)

# ✅ صحيح — الوسائط الصحيحة
GenericCatalogDialog(
    get_data_func=lambda include_inactive=False: [...],
    create_data_func=lambda name, desc: ...,
    delete_data_func=lambda tid: ...,
    restore_data_func=lambda tid: ...,
)
```
**الملفات:** `treasury/views.py`

---

## 8. القواعد الذهبية للتطوير

### عند تغيير التسميات:
1. **غيّر النص فقط** — لا تحذف سطر الإنشاء
2. **غيّر الدالة فقط** — لا تحذف سطر الربط (connect)
3. **غيّر الاسم فقط** — لا تحذف سطر التعريف

### عند إضافة ميزة جديدة:
1. تحقق من الاستيرادات أولاً
2. تحقق من أن الكلاس/الدالة موجودة
3. تحقق من توافق الوسائط

### عند التعامل مع PyQt6:
- `QFont.Bold` → `QFont.Weight.Bold`
- `QSizePolicy.Expanding` → `QSizePolicy.Policy.Expanding`
- `addItems([tuples])` → `addItem(text, data)` لكل عنصر

### عند التعامل مع EnhancedTableView:
- `currentRow()` → `get_selected_rows()`
- `get_row_data(row)` يُرجع قائمة بالقيم

---

**آخر تحديث:** 2026-04-02
**عدد الأخطاء الموثقة:** 15
