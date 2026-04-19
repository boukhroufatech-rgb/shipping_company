#!/usr/bin/env python3
"""
Auto-Sync Script - تزامن تلقائي مع GitHub
يسحب التحديثات قبل البدء ويرفع بعد الانتهاء

الاستخدام:
    python auto_sync.py pull      # سحب التحديثات
    python auto_sync.py push      # رفع التحديثات
    python auto_sync.py sync      # سحب ورفع
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

# المجلد الرئيسي للمشروع
PROJECT_ROOT = Path(__file__).parent.parent

def run_git_command(cmd: list) -> tuple[bool, str]:
    """تنفيذ أمر git وإرجاع النتيجة والرسالة"""
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
        return False, str(e)

def git_pull() -> bool:
    """سحب التحديثات من GitHub"""
    print(f"⬇️  [{datetime.now().strftime('%H:%M:%S')}] سحب التحديثات من GitHub...")
    success, msg = run_git_command(['git', 'pull', 'origin', 'main'])

    if success:
        if "Already up to date" in msg:
            print("✅ البرنامج محدّث بالفعل")
        else:
            print(f"✅ تم السحب بنجاح\n{msg}")
    else:
        print(f"❌ خطأ في السحب:\n{msg}")

    return success

def git_push() -> bool:
    """رفع التحديثات إلى GitHub"""
    print(f"⬆️  [{datetime.now().strftime('%H:%M:%S')}] رفع التحديثات إلى GitHub...")

    # التحقق من وجود تغييرات
    success, status = run_git_command(['git', 'status', '--short'])
    if success and not status.strip():
        print("✅ لا توجد تغييرات للرفع")
        return True

    # الرفع
    success, msg = run_git_command(['git', 'push', 'origin', 'main'])

    if success:
        print(f"✅ تم الرفع بنجاح")
        if msg:
            print(msg)
    else:
        print(f"❌ خطأ في الرفع:\n{msg}")

    return success

def git_status() -> str:
    """عرض حالة git الحالية"""
    success, msg = run_git_command(['git', 'status'])
    return msg if success else "❌ خطأ في الحصول على الحالة"

def main():
    if len(sys.argv) < 2:
        action = "sync"
    else:
        action = sys.argv[1].lower()

    print(f"🔄 تزامن تلقائي مع GitHub [{action.upper()}]")
    print("=" * 60)

    if action == "pull":
        git_pull()
    elif action == "push":
        git_push()
    elif action == "sync":
        print("\n📋 خطوة 1: سحب التحديثات...")
        git_pull()
        print("\n📋 خطوة 2: رفع التحديثات...")
        git_push()
    elif action == "status":
        print(git_status())
    else:
        print(f"❌ أمر غير معروف: {action}")
        print("الأوامر المتاحة: pull | push | sync | status")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ انتهى التزامن")

if __name__ == "__main__":
    main()
