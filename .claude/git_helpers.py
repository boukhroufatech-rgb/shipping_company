#!/usr/bin/env python3
"""
Git Helper Functions - مساعدات للتزامن التلقائي
يمكن استيرادها واستخدامها من أي مكان في الكود
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent

def run_git(cmd: list) -> Tuple[bool, str]:
    """تنفيذ أمر git بشكل آمن"""
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, f"خطأ: {str(e)}"

def auto_sync_before_work() -> bool:
    """
    استدعي قبل بدء عملية عمل كبيرة
    سحب آخر التحديثات من GitHub
    """
    print("🔄 سحب آخر التحديثات...")
    success, msg = run_git(['git', 'pull', 'origin', 'main', '--quiet'])
    if success:
        print("✅ تم السحب بنجاح - جاهز للعمل")
    else:
        print(f"⚠️  تحذير: فشل السحب\n{msg}")
    return success

def auto_sync_after_work(message: Optional[str] = None) -> bool:
    """
    استدعي بعد انتهاء عملية عمل كبيرة
    تلقائياً: يرفع التحديثات إلى GitHub

    Args:
        message: رسالة اختيارية لتسجيل
    """
    print("📋 التحقق من التغييرات...")
    success, status = run_git(['git', 'status', '--short'])

    if success and not status.strip():
        print("✅ لا توجد تغييرات جديدة")
        return True

    print("⬆️  رفع التحديثات...")
    success, msg = run_git(['git', 'push', 'origin', 'main', '--quiet'])

    if success:
        print("✅ تم الرفع بنجاح 🎉")
        if message:
            print(f"   📝 {message}")
    else:
        print(f"❌ فشل الرفع:\n{msg}")

    return success

def sync_full_cycle(work_description: Optional[str] = None) -> bool:
    """
    دورة كاملة: سحب + عمل + رفع
    استخدمه عند بدء مرحلة جديدة من العمل

    Args:
        work_description: وصف العمل الذي ستقوم به
    """
    if work_description:
        print(f"\n{'='*60}")
        print(f"🚀 بدء: {work_description}")
        print('='*60)

    # خطوة 1: السحب
    auto_sync_before_work()

    # خطوة 2: اليقظة (العملية الفعلية تحدث بين هنا وهناك)
    return True  # العودة True للسماح بالعملية

def finish_work(success: bool = True, description: str = "عملية منجزة") -> bool:
    """
    انهاء العملية والرفع التلقائي

    Args:
        success: هل انتهت العملية بنجاح
        description: وصف ما تم إنجازه
    """
    if not success:
        print("❌ العملية فشلت - لن يتم الرفع")
        return False

    return auto_sync_after_work(description)

# دوال مساعدة إضافية

def get_current_branch() -> str:
    """الحصول على اسم الفرع الحالي"""
    success, msg = run_git(['git', 'branch', '--show-current'])
    return msg.strip() if success else "unknown"

def get_last_commit() -> str:
    """الحصول على آخر commit"""
    success, msg = run_git(['git', 'log', '-1', '--oneline'])
    return msg.strip() if success else "unknown"

def has_uncommitted_changes() -> bool:
    """التحقق من وجود تغييرات غير مُرتكبة"""
    success, msg = run_git(['git', 'status', '--short'])
    return success and bool(msg.strip())

def has_unpushed_commits() -> bool:
    """التحقق من وجود commits غير مرفوعة"""
    success, msg = run_git(['git', 'status', '--porcelain', '--branch'])
    return success and "ahead" in msg.lower()
