# 🔄 دليل التزامن التلقائي مع GitHub

## المبدأ

**كل عملية عمل كبيرة = سحب تلقائي + رفع تلقائي**

```
git pull (سحب) → العمل → git push (رفع)
```

---

## الاستخدام السريع

### 1️⃣ قبل البدء بعملية كبيرة

```bash
python .claude/auto_sync.py pull
```

أو من Python:
```python
from .claude.git_helpers import auto_sync_before_work
auto_sync_before_work()
```

### 2️⃣ بعد الانتهاء من العملية

```bash
python .claude/auto_sync.py push
```

أو من Python:
```python
from .claude.git_helpers import auto_sync_after_work
auto_sync_after_work("تم إنجاز المرحلة الثانية")
```

### 3️⃣ دورة كاملة (سحب + رفع)

```bash
python .claude/auto_sync.py sync
```

---

## أمثلة الاستخدام

### مثال 1: من سطر الأوامر

```bash
# قبل البدء
python .claude/auto_sync.py pull

# ... تنفيذ العمل ...

# بعد الانتهاء
python .claude/auto_sync.py push
```

### مثال 2: من داخل Python

```python
from pathlib import Path
import sys

# إضافة مسار الـ .claude للمسار
sys.path.insert(0, str(Path(__file__).parent / ".claude"))

from git_helpers import (
    auto_sync_before_work,
    auto_sync_after_work,
    has_uncommitted_changes
)

# بدء العملية
auto_sync_before_work()

# ... تنفيذ العمل ...

# إنهاء العملية
if has_uncommitted_changes():
    auto_sync_after_work("تم إنجاز المرحلة X")
else:
    print("✅ لا توجد تغييرات جديدة")
```

---

## الأوامر المتاحة

| الأمر | الوصف |
|-------|-------|
| `pull` | سحب آخر التحديثات من GitHub |
| `push` | رفع التحديثات إلى GitHub |
| `sync` | سحب ورفع (دورة كاملة) |
| `status` | عرض حالة git الحالية |

---

## الدوال المساعدة

### `auto_sync_before_work()`
- **الاستخدام**: قبل بدء عملية عمل
- **الفائدة**: تأكد أن لديك آخر النسخة من GitHub

### `auto_sync_after_work(message=None)`
- **الاستخدام**: بعد انتهاء عملية عمل
- **الفائدة**: رفع التحديثات تلقائياً
- **المعامل**: `message` - وصف اختياري

### `sync_full_cycle(work_description=None)`
- **الاستخدام**: عند بدء مرحلة جديدة كبيرة
- **الفائدة**: يطبع رسالة ترحيب ويسحب التحديثات

### `finish_work(success=True, description="")`
- **الاستخدام**: إنهاء العملية بنجاح أو فشل
- **الفائدة**: رفع آمن فقط إذا نجحت العملية

### وظائف استفسار:
- `has_uncommitted_changes()` - هل توجد تغييرات غير مرتكبة؟
- `has_unpushed_commits()` - هل توجد commits غير مرفوعة؟
- `get_current_branch()` - اسم الفرع الحالي
- `get_last_commit()` - آخر commit

---

## سيناريوهات الاستخدام

### سيناريو 1: عملية LAYER في المشروع

```python
# البداية
auto_sync_before_work()  # سحب التحديثات

# تنفيذ LAYER 1, 2, 3...
# ... كود التعديلات ...

# الانهاء
auto_sync_after_work("LAYER 1-3: تطبيق المبدأ الذهبي")
```

### سيناريو 2: إصلاح bug طويل

```python
from git_helpers import *

# بدء الجلسة
sync_full_cycle("إصلاح bug في قسم DETTES")

# العمل...
# تشخيص...
# تطبيق الإصلاح...

# إنهاء آمن
finish_work(
    success=True,
    description="تم إصلاح bug - حماية الحساب الرئيسي"
)
```

### سيناريو 3: تحديث أمان سريع

```bash
# سريع - بدون Python
python .claude/auto_sync.py pull
# ... تغيير سريع ...
python .claude/auto_sync.py push
```

---

## التعليمات الأمان

⚠️ **تحذيرات مهمة**:

1. **أنت مسؤول عن الـ commit message**
   - اكتب وصف واضح
   - استخدم العربية للوضوح

2. **تأكد من انتهاء العملية قبل الرفع**
   - شغّل الاختبارات
   - تحقق من الترجمة (compile)
   - اعرض النتائج

3. **في حالة الخطأ أثناء الرفع**
   - راجع رسالة الخطأ
   - تحقق من الـ conflicts
   - اطلب المساعدة قبل force push

---

## الحالات الخاصة

### إذا حدث merge conflict

```bash
# قف وحل الـ conflict يدوياً
git status                    # شوف المشاكل
# عدّل الملفات المتضاربة
git add .
git commit -m "حل conflict"
git push origin main
```

### إذا أردت الرفع إلى فرع مختلف

```bash
# بدّل الاسم في الأمر
git push origin my-branch
```

### إذا حدث خطأ - الرجوع للخطوة السابقة

```bash
git reset --soft HEAD~1    # إلغاء آخر commit بدون فقدان التعديلات
# عدّل ما تريد
git commit -m "رسالة جديدة"
git push origin main
```

---

## 📞 الدعم

إذا حدثت مشاكل:
1. شغّل `python .claude/auto_sync.py status` لشوف الحالة
2. اطلب اسم الخطأ بالكامل
3. سأساعدك في الحل
