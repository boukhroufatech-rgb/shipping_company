# 🔧 .claude - مجلد أدوات التطوير

هذا المجلد يحتوي على أدوات مساعدة لتسهيل التطوير والتزامن مع GitHub.

---

## 📁 الملفات الموجودة

### 1. `auto_sync.py` - السيناريو التلقائي

**الغرض**: تزامن سهل مع GitHub من سطر الأوامر

**الاستخدام**:
```bash
python auto_sync.py pull          # سحب التحديثات
python auto_sync.py push          # رفع التحديثات
python auto_sync.py sync          # سحب ورفع
python auto_sync.py status        # عرض الحالة
```

**مثال**:
```bash
# بدء العملية
python .claude/auto_sync.py pull

# ... القيام بالعمل ...

# إنهاء العملية
python .claude/auto_sync.py push
```

---

### 2. `git_helpers.py` - مكتبة مساعدة Python

**الغرض**: استيراد دوال مساعدة من داخل Python

**الدوال الرئيسية**:
- `auto_sync_before_work()` - سحب قبل البدء
- `auto_sync_after_work(message)` - رفع بعد الانتهاء
- `sync_full_cycle(description)` - دورة كاملة
- `finish_work(success, description)` - إنهاء آمن

**الاستيراد**:
```python
from .claude.git_helpers import auto_sync_before_work, auto_sync_after_work

auto_sync_before_work()
# ... عمل ...
auto_sync_after_work("وصف العملية")
```

---

### 3. `SYNC_GUIDE.md` - دليل مفصل

**المحتوى**:
- شرح المبدأ
- الاستخدام السريع
- الأمثلة العملية
- الحالات الخاصة والمشاكل

📖 **اقرأ الدليل**: `SYNC_GUIDE.md`

---

### 4. `WORK_TEMPLATE.py` - قالب معياري

**الغرض**: نموذج جاهز لأي عملية عمل

**الاستخدام**:
```bash
# انسخ القالب
cp WORK_TEMPLATE.py my_work.py

# عدّل:
# - WORK_NAME
# - WORK_DESC
# - أضف كودك

# شغّل
python my_work.py
```

---

## 🚀 البدء السريع

### الخيار 1: من سطر الأوامر (الأسهل)

```bash
# 1. سحب التحديثات
python .claude/auto_sync.py pull

# 2. القيام بالعمل...
# (استخدم الـ editor، أو Python، أو أي أداة)

# 3. رفع التحديثات
python .claude/auto_sync.py push
```

### الخيار 2: من داخل Python

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / ".claude"))
from git_helpers import auto_sync_before_work, auto_sync_after_work

# البدء
auto_sync_before_work()

# العمل...
# كود التعديلات هنا

# الإنهاء
auto_sync_after_work("وصف ما تم إنجازه")
```

### الخيار 3: استخدام القالب

```bash
cp .claude/WORK_TEMPLATE.py my_task.py
nano my_task.py  # عدّل المتغيرات والكود
python my_task.py
```

---

## 📋 أمثلة واقعية

### مثال 1: تطبيق المبدأ الذهبي على وحدة جديدة

```bash
# 1. سحب آخر التحديثات
python .claude/auto_sync.py pull

# 2. فتح الملف وتعديله
# vim modules/new_module/views.py
# ... التعديلات ...

# 3. التحقق من الترجمة
# python -m py_compile modules/new_module/views.py

# 4. رفع التحديثات
python .claude/auto_sync.py push
```

### مثال 2: إصلاح bug معقد

```python
# repair_bug.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / ".claude"))
from git_helpers import *

# بدء الجلسة
sync_full_cycle("إصلاح bug في نظام الدفع")

# الخطوة 1: التشخيص
# ... كود التشخيص ...

# الخطوة 2: الإصلاح
# ... كود الإصلاح ...

# الخطوة 3: الاختبار
# ... كود الاختبار ...

# الإنهاء
finish_work(
    success=True,
    description="تم إصلاح bug الدفع - فعّال 100%"
)
```

---

## ⚙️ التكوين (اختياري)

### تغيير الفرع الافتراضي

في `auto_sync.py` أو `git_helpers.py`:
```python
# بدل 'main' بـ 'dev' أو أي فرع آخر
run_git(['git', 'pull', 'origin', 'dev'])
```

### إضافة دوال مخصصة

في `git_helpers.py` أضف:
```python
def my_custom_function():
    print("وظيفة مخصصة")
    # ... كودك ...
```

---

## 🔒 الأمان والتحذيرات

⚠️ **تحذيرات مهمة**:

1. **التحقق دائماً قبل الرفع**
   ```bash
   git status          # شوف التغييرات
   git diff            # راجع الفروقات
   python -m py_compile *.py  # تحقق من الترجمة
   ```

2. **لا تنسى الـ commit message**
   ```bash
   git commit -m "وصف واضح بالعربية"
   ```

3. **في حالة المشكلة - لا تفزع**
   ```bash
   python .claude/auto_sync.py status  # شوف الوضع
   git log -5 --oneline                # شوف آخر commits
   ```

---

## 📚 الموارد الإضافية

- [`SYNC_GUIDE.md`](SYNC_GUIDE.md) - دليل مفصل
- [`WORK_TEMPLATE.py`](WORK_TEMPLATE.py) - قالب جاهز
- `git_helpers.py` - البرنامج الكامل

---

## 💡 نصائح

✅ **أفضل الممارسات**:
1. سحب قبل البدء (حتى لا يحدث conflict)
2. عمل تغييرات صغيرة (أسهل للـ debug)
3. اختبار دائماً (قبل الرفع)
4. كتابة رسالة واضحة (بالعربية إن أمكن)

✅ **الجدول الموصى به**:
```
9:00  → سحب التحديثات (git pull)
9:00-12:00  → العمل الركيز
12:00  → رفع النتائج (git push)
14:00  → سحب (تحديثات جديدة من الآخرين؟)
14:00-17:00  → العمل
17:00  → رفع النتائج (git push)
```

---

## 🎯 الهدف

**جعل العمل في الفريق آمناً وسلساً**:
- ✅ لا conflicts
- ✅ لا فقدان للعمل
- ✅ كل شيء في GitHub
- ✅ سهولة التتبع والمراجعة

---

## 📞 الدعم

إذا واجهت مشكلة:
1. اقرأ `SYNC_GUIDE.md`
2. شغّل `python .claude/auto_sync.py status`
3. اطلب المساعدة مع اسم الخطأ الكامل
