# 🛡️ نظام إدارة الأخطاء الاحترافي
# Professional Error Handling System

## 📋 نظرة عامة

تم تطوير نظام متكامل لإدارة الأخطاء يحمي التطبيق من الانهيار ويوفر:
- ✅ تسجيل شامل للأخطاء (Logging)
- ✅ معالجة تلقائية للأخطاء (Decorators)
- ✅ واجهة احترافية لعرض الأخطاء (Error Dialogs)
- ✅ نظام تنبيهات وتقارير (Alerts & Reports)

---

## 📁 هيكل النظام

```
shipping_company/
├── utils/
│   ├── logger.py           # نظام اللوج المركزي
│   └── error_handler.py    # Decorators لإدارة الأخطاء
├── components/
│   └── error_dialog.py     # نوافذ عرض الأخطاء
├── logs/                   # مجلد اللوجات (يُنشأ تلقائياً)
│   ├── app_2026-04-01.log
│   └── errors_2026-04-01.log
└── ERROR_HANDLING.md       # هذا الملف
```

---

## 1️⃣ نظام اللوج (Logging)

### الاستخدام الأساسي

```python
from utils.logger import logger, log_error, log_success, log_warning

# تسجيل معلومة
log_info("تم بدء التطبيق", context="MainApp")

# تسجيل نجاح
log_success("تم إنشاء الحساب بنجاح", context="TreasuryService")

# تسجيل تحذير
log_warning("الرصيد منخفض", context="AccountService")

# تسجيل خطأ
try:
    result = risky_operation()
except Exception as e:
    log_error(e, context="TreasuryService.create_transaction", extra_data={
        "account_id": account_id,
        "amount": amount
    })
```

### مخرجات اللوج

1. **Console** (ملون):
   - 🔵 INFO: أزرق
   - 🟡 WARNING: أصفر
   - 🔴 ERROR: أحمر

2. **File** (ملف يومي):
   - `logs/app_YYYY-MM-DD.log`
   - يحتوي على كل اللوجات

3. **Error File** (ملف الأخطاء فقط):
   - `logs/errors_YYYY-MM-DD.log`
   - يحتوي على الأخطاء فقط لسهولة المراجعة

---

## 2️⃣ Decorators لإدارة الأخطاء

### @handle_errors

```python
from utils.error_handler import handle_errors

@handle_errors(
    default_return=(False, "فشل العملية", None),
    log_context="TreasuryService",
    error_message="حدث خطأ أثناء إنشاء المعاملة"
)
def create_transaction(self, account_id, amount, type):
    # لا حاجة لـ try/except!
    account = self.get_account(account_id)
    if account.balance < amount:
        raise ValueError("الرصيد غير كافي")
    # ...
    return (True, "تمت العملية", transaction_id)
```

### @validate_inputs

```python
from utils.error_handler import validate_inputs

@validate_inputs("name", "email")
def create_customer(self, name=None, email=None, phone=None):
    # يتم التحقق تلقائياً من وجود name و email
    # ...
```

### @retry_on_error

```python
from utils.error_handler import retry_on_error

@retry_on_error(max_attempts=3, delay=0.5)
def call_external_api(self, url):
    # يعيد المحاولة 3 مرات عند الفشل
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
```

### @transactional

```python
from utils.error_handler import transactional

@transactional(error_return=(False, "فشل التحويل"))
def transfer_funds(self, from_id, to_id, amount):
    # يضمن rollback تلقائي عند الفشل
    # ...
```

---

## 3️⃣ واجهة عرض الأخطاء

### عرض خطأ بسيط

```python
from components.error_dialog import show_error

try:
    self.service.create_account(...)
except Exception as e:
    show_error(
        self,
        message="فشل إنشاء الحساب",
        exception=e,
        title="خطأ"
    )
```

### عرض تحذير

```python
from components.error_dialog import show_warning

if account.balance < minimum_balance:
    show_warning(
        self,
        message="الرصيد منخفض جداً",
        title="تحذير"
    )
```

### عرض رسالة نجاح

```python
from components.error_dialog import show_success

show_success(
    self,
    message="تم حفظ البيانات بنجاح",
    title="نجاح"
)
```

### طلب تأكيد

```python
from components.error_dialog import confirm_action

if confirm_action(
    self,
    message="هل أنت متأكد من الحذف؟ لا يمكن التراجع عن هذا الإجراء.",
    title="تأكيد الحذف"
):
    self.service.delete(id)
```

---

## 4️⃣ أمثلة عملية شاملة

### مثال 1: Service كامل

```python
from utils.logger import log_info, log_error
from utils.error_handler import handle_errors
from components.error_dialog import show_error, show_success

class TreasuryService:
    
    @handle_errors(
        default_return=(False, "فشل إنشاء الحساب", None),
        log_context="TreasuryService"
    )
    def create_account(self, name, code, account_type, currency_id):
        log_info(f"إنشاء حساب جديد: {name}", context="create_account")
        
        # التحقق من التكرار
        if self.account_exists(code):
            log_warning(f"الكود {code} موجود مسبقاً")
            return (False, "الكود مكرر", None)
        
        # إنشاء الحساب
        account = self.repo.create(...)
        log_success(f"تم إنشاء الحساب {account.id}")
        return (True, "تم الإنشاء", account.id)
```

### مثال 2: View كامل

```python
from components.error_dialog import show_error, show_success, confirm_action

class TreasuryView:
    
    def _create_account(self):
        dialog = CreateAccountDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            
            # التحقق من البيانات
            if not self._validate_data(data):
                show_warning(self, "البيانات غير صحيحة")
                return
            
            # تأكيد
            if not confirm_action(
                self,
                f"هل تريد إنشاء حساب '{data['name']}'؟"
            ):
                return
            
            # الحفظ
            try:
                success, message, account_id = self.service.create_account(**data)
                if success:
                    show_success(self, message)
                    self.load_data()
                else:
                    show_error(self, message)
            except Exception as e:
                show_error(self, "حدث خطأ غير متوقع", exception=e)
```

---

## 5️⃣ معالجة الأخطاء في main.py

### تحديث refresh_all

```python
def refresh_all(self):
    """تحديث شامل مع حماية من الانهيار"""
    if self._is_refreshing:
        return
    
    self._is_refreshing = True
    try:
        self.status_bar.showMessage("🔄 جاري تحديث البيانات...")
        
        # تحديث كل view بشكل منفصل مع حماية
        views = [
            ("Dashboard", self.dashboard_view),
            ("Treasury", self.treasury_view),
            ("Currency", self.currency_view),
            ("Customers", self.customers_view),
            ("Licenses", self.licenses_view),
            ("Logistics", self.logistics_view),
            ("Debt", self.debt_view),
            ("Partners", self.partners_view)
        ]
        
        for name, view in views:
            try:
                view.refresh()
            except Exception as e:
                log_error(e, context=f"refresh_{name}")
                # الاستمرار في التحديث حتى لو فشل view واحد
        
        self.status_bar.showMessage("✅ البيانات محدثة", 3000)
        
    except Exception as e:
        log_error(e, context="refresh_all")
        show_error(self, "فشل تحديث البيانات", exception=e)
    finally:
        self._is_refreshing = False
```

---

## 6️⃣ أفضل الممارسات

### ✅ ما يجب فعله

1. **استخدم Decorators دائماً** في الـ Services
2. **سجّل كل الأخطاء** حتى لو عالجتها
3. **اعرض رسالة واضحة للمستخدم** بدلاً من التفاصيل التقنية
4. **استخدم confirm_action** قبل العمليات الخطرة (حذف، تحويل أموال)
5. **تأكد من وجود rollback** في المعاملات المالية

### ❌ ما لا يجب فعله

1. ~~لا تستخدم `pass` في except~~
2. ~~لا تعرض Stack Trace للمستخدم~~
3. ~~لا تتجاهل الأخطاء الصامتة~~
4. ~~لا تستخدم try/except في كل مكان (استخدم Decorators)~~

---

## 7️⃣ تطبيق النظام على الكود الحالي

### الخطوة 1: تحديث TreasuryService

```python
from utils.logger import log_info, log_error, log_success
from utils.error_handler import handle_errors

class TreasuryService:
    
    @handle_errors(
        default_return=(False, "فشل إنشاء الحساب", None),
        log_context="TreasuryService.create_account"
    )
    def create_account(self, name, code, account_type, currency_id, ...):
        log_info(f"Creating account: {name}")
        
        # ... الكود الحالي
        
        log_success(f"Account created with ID: {account.id}")
        return (True, SUCCESS_ACCOUNT_CREATED, account.id)
```

### الخطوة 2: تحديث Views

```python
from components.error_dialog import show_error, show_success

class TreasuryView:
    
    def _create_account(self):
        dialog = CreateAccountDialog(self)
        if dialog.exec():
            try:
                success, message, account_id = self.service.create_account(...)
                if success:
                    show_success(self, message)
                    self.load_data()
                else:
                    show_error(self, message)
            except Exception as e:
                show_error(self, "حدث خطأ غير متوقع", exception=e)
```

---

## 8️⃣ مراقبة اللوجات

### عرض اللوجات الحية

```bash
# في Terminal منفصل
tail -f logs/app_2026-04-01.log
```

### البحث عن الأخطاء

```bash
# عرض كل الأخطاء اليوم
grep "ERROR" logs/app_2026-04-01.log

# عرض الأخطاء في TreasuryService
grep "TreasuryService" logs/errors_2026-04-01.log
```

---

## 📊 الإحصائيات

بعد تطبيق النظام، يمكنك:

1. **معرفة عدد الأخطاء يومياً** من ملف `errors_*.log`
2. **تحديد أكثر الوحدات مشاكل** من خلال `grep` على context
3. **تتبع الأخطاء المتكررة** وأنماطها

---

## 🎯 الخلاصة

| الميزة | الفائدة |
|--------|---------|
| Logging شامل | معرفة كل ما يحدث في التطبيق |
| Decorators | كود نظيف بدون try/except مكررة |
| Error Dialogs | واجهة احترافية للمستخدم |
| حماية من الانهيار | التطبيق يستمر حتى لو فشل جزء |

---

## 📞 الدعم

لأي استفسار أو تحسين، راجع ملف `logs/` أو أضف تحسينات جديدة!
