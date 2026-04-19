#!/usr/bin/env python3
"""
Script مختصر للتزامن السريع - شغّله من جذر المشروع

الاستخدام:
    python sync.py pull      # سحب
    python sync.py push      # رفع
    python sync.py sync      # كامل
    python sync.py status    # الحالة
"""

import sys
from pathlib import Path

# إضافة .claude للمسار
sys.path.insert(0, str(Path(__file__).parent / ".claude"))

from auto_sync import main

if __name__ == "__main__":
    main()
