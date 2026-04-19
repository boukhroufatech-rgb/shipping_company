#!/usr/bin/env python3
"""
قالب معياري للعمل على المشروع
استخدمه كمرجع لكل عملية عمل كبيرة

الخطوات:
1. انسخ هذا الملف
2. بدّل WORK_NAME و WORK_DESC
3. أضف كودك في القسم المناسب
4. شغّل الملف
"""

import sys
from pathlib import Path

# إضافة مسار الـ .claude للمسار
sys.path.insert(0, str(Path(__file__).parent))

from git_helpers import (
    auto_sync_before_work,
    finish_work,
    has_uncommitted_changes,
    get_current_branch
)

# ============================================================================
# التكوين
# ============================================================================

WORK_NAME = "LAYER_X_NEW_FEATURE"  # ✏️ غدّل اسم العملية
WORK_DESC = "شرح كامل لما تفعله هذه العملية"  # ✏️ اكتب الوصف
LAYERS = ["LAYER 1", "LAYER 2", "LAYER 3"]  # ✏️ قائمة الخطوات

# ============================================================================
# الدالة الرئيسية
# ============================================================================

def main():
    """دالة العمل الرئيسية"""

    print("\n" + "=" * 70)
    print(f"🚀 {WORK_NAME}")
    print(f"📝 {WORK_DESC}")
    print("=" * 70)

    # الخطوة 1: السحب من GitHub
    print(f"\n📋 الفرع الحالي: {get_current_branch()}")
    print("\n📥 سحب آخر التحديثات...")
    auto_sync_before_work()

    # الخطوة 2: العمل
    try:
        for layer in LAYERS:
            print(f"\n{'='*70}")
            print(f"⚙️  {layer}")
            print('='*70)

            # ✏️ أضف كودك هنا
            # ============================================================

            # مثال:
            # - Read files
            # - Modify code
            # - Verify (compile)
            # - Commit

            # ============================================================

            print(f"✅ {layer} انتهى")

        # الخطوة 3: التحقق النهائي
        print(f"\n{'='*70}")
        print("🔍 التحقق النهائي")
        print('='*70)

        if has_uncommitted_changes():
            print("⚠️  توجد تغييرات غير مرتكبة")
        else:
            print("✅ جميع التغييرات محفوظة")

        # الخطوة 4: الرفع إلى GitHub
        success = finish_work(
            success=True,
            description=WORK_DESC
        )

        if success:
            print(f"\n🎉 انتهى {WORK_NAME} بنجاح!")
        else:
            print(f"\n⚠️  تحذير: فشل الرفع")

        return success

    except Exception as e:
        print(f"\n❌ خطأ: {str(e)}")
        print("\n⚠️  لم يتم الرفع (فشل العملية)")
        return False

# ============================================================================
# تشغيل
# ============================================================================

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
