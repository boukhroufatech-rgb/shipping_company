"""
نظام تسجيل الأخطاء والعمليات المركزي
Logger System - Professional Error Tracking
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# إنشاء مجلد اللوجات
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ملف اللوج الرئيسي
LOG_FILE = LOG_DIR / f"app_{datetime.now().strftime('%Y-%m-%d')}.log"
ERROR_LOG_FILE = LOG_DIR / f"errors_{datetime.now().strftime('%Y-%m-%d')}.log"


class ColorFormatter(logging.Formatter):
    """Formatter ملون للكونسول"""
    
    grey = "\x1b[38;21m"
    blue = "\x1b[34;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: blue + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        return formatter.format(record)


def setup_logger(name: str = "ShippingApp") -> logging.Logger:
    """
    إعداد Logger احترافي مع 3 مخرجات:
    1. Console (ملون)
    2. File (كل اللوجات)
    3. Error File (الأخطاء فقط)
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # منع التكرار إذا كان موجود مسبقاً
    if logger.handlers:
        return logger
    
    # 1. Console Handler (ملون) - مع ترميز UTF-8
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColorFormatter())
    # محاولة تعيين UTF-8 للـ console
    try:
        console_handler.stream.reconfigure(encoding='utf-8')
    except:
        pass  # إذا فشل، نستخدم الافتراضي
    logger.addHandler(console_handler)
    
    # 2. File Handler (كل اللوجات)
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 3. Error File Handler (الأخطاء فقط)
    error_handler = logging.FileHandler(ERROR_LOG_FILE, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)
    
    return logger


# Logger عام للاستخدام في كل التطبيق
logger = setup_logger()


def log_error(error: Exception, context: str = "", extra_data: dict = None):
    """
    تسجيل خطأ بشكل مفصل مع السياق
    
    Args:
        error: الاستثناء الذي حدث
        context: وصف السياق (مثال: "TreasuryService.create_transaction")
        extra_data: بيانات إضافية للمساعدة في الديباج
    """
    error_msg = (
        f"[ERROR] in {context} | "
        f"Type: {type(error).__name__} | "
        f"Message: {str(error)}\n"
    )
    
    if extra_data:
        error_msg += f"   Extra: {extra_data}\n"
    
    logger.error(error_msg, exc_info=True)


def log_warning(message: str, context: str = ""):
    """تسجيل تحذير"""
    logger.warning(f"[WARNING] in {context}: {message}")


def log_info(message: str, context: str = ""):
    """تسجيل معلومة"""
    logger.info(f"[INFO] in {context}: {message}")


def log_success(message: str, context: str = ""):
    """تسجيل عملية ناجحة"""
    logger.info(f"[SUCCESS] in {context}: {message}")


def log_debug(message: str, context: str = ""):
    """تسجيل معلومات ديباج"""
    logger.debug(f"[DEBUG] in {context}: {message}")
