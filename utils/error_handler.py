"""
Decorator لإدارة الأخطاء تلقائياً
Automatic Error Handling Decorator
"""
import traceback
from functools import wraps
from typing import Optional, Callable, Tuple, Any
from utils.logger import log_error, log_warning, log_info


def handle_errors(
    default_return: Any = None,
    error_message: str = "حدث خطأ غير متوقع",
    log_context: str = "",
    raise_exception: bool = False,
    on_error_callback: Optional[Callable] = None
):
    """
    Decorator لإدارة الأخطاء بشكل تلقائي في جميع الدوال
    
    Args:
        default_return: القيمة الافتراضية للرجوع في حالة الخطأ
        error_message: رسالة الخطأ الافتراضية
        log_context: سياق اللوج (مثال: "TreasuryService")
        raise_exception: هل نعيد رمي الاستثناء أم لا
        on_error_callback: دالة تُستدعى عند الخطأ
    
    Example:
        @handle_errors(default_return=(False, "خطأ في العملية"), log_context="UserService")
        def create_user(self, name, email):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # تسجيل الخطأ بالتفصيل
                full_context = f"{log_context}.{func.__name__}" if log_context else func.__name__
                log_error(e, context=full_context, extra_data={
                    "args": str(args)[:200],  # منع الطول الزائد
                    "kwargs": str(kwargs)[:200]
                })
                
                # استدعاء callback إذا وجد
                if on_error_callback:
                    try:
                        on_error_callback(e, full_context)
                    except Exception as callback_error:
                        log_error(callback_error, context="on_error_callback")
                
                # إرجاع القيمة الافتراضية
                if default_return is not None:
                    return default_return
                
                # إرجاع رسالة خطأ افتراضية للدوال التي ترجع Tuple
                if func.__annotations__.get('return') == Tuple[bool, str]:
                    return (False, f"{error_message}: {str(e)}")
                
                # رمي الاستثناء إذا طُلب
                if raise_exception:
                    raise
                
                # افتراضي: إرجاع None
                return None
        
        return wrapper
    return decorator


def validate_inputs(*required_params: str):
    """
    Decorator للتحقق من المعاملات المطلوبة
    
    Example:
        @validate_inputs("name", "email")
        def create_user(self, name=None, email=None, age=None):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # التحقق من المعاملات المطلوبة
            missing = []
            for param in required_params:
                if param not in kwargs or kwargs[param] is None:
                    # التحقق من args أيضاً
                    found = False
                    for arg in args:
                        if arg is not None:
                            found = True
                            break
                    if not found:
                        missing.append(param)
            
            if missing:
                error_msg = f"المعاملات المطلوبة مفقودة: {', '.join(missing)}"
                log_warning(error_msg, context=func.__name__)
                return (False, error_msg, None)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def retry_on_error(max_attempts: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """
    Decorator لإعادة المحاولة عند الفشل
    
    Args:
        max_attempts: عدد المحاولات
        delay: الانتظار بين المحاولات (بالثواني)
        exceptions: أنواع الاستثناءات التي تُ触发 إعادة المحاولة
    
    Example:
        @retry_on_error(max_attempts=3, delay=0.5)
        def api_call(self):
            ...
    """
    import time
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    log_warning(
                        f"محاولة {attempt + 1}/{max_attempts} فشلت: {str(e)}",
                        context=func.__name__
                    )
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
            
            # كل المحاولات فشلت
            log_error(last_error, context=f"{func.__name__} (after {max_attempts} attempts)")
            raise last_error
        
        return wrapper
    return decorator


def transactional(error_return: Tuple[bool, str] = (False, "فشل العملية")):
    """
    Decorator للمعاملات التي تتطلب Transaction
    يضمن rollback تلقائي عند الفشل
    
    Example:
        @transactional()
        def transfer_funds(self, from_id, to_id, amount):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_error(e, context=f"TRANSACTION_FAILED.{func.__name__}")
                return error_return
        
        return wrapper
    return decorator
