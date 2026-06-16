# logger.py
import os
from datetime import datetime
import functools



LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"finance_{datetime.now().strftime('%Y%m%d')}.log")

# Управление логированием: можно включать/выключать через UI
DEBUG = True          # вывод в терминал
LOGGING_ENABLED = True # запись в файл

def set_logging_enabled(enabled: bool):
    global LOGGING_ENABLED
    LOGGING_ENABLED = enabled

def log(msg, level="INFO"):
    """Записывает сообщение в файл лога (если логирование включено)"""
    if not LOGGING_ENABLED:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    full_msg = f"[{timestamp}] [{level}] {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

def log_call(level="INFO"):
    """
    Декоратор для логирования вызовов функций.
    level: уровень логирования (INFO, DEBUG, WARNING, ERROR)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Формируем строку с аргументами
            arg_str = ", ".join(
                [repr(a) for a in args] +
                [f"{k}={repr(v)}" for k, v in kwargs.items()]
            )
            log(f"▶️ Вызов {func.__name__}({arg_str})", level=level)
            try:
                result = func(*args, **kwargs)
                log(f"✅ {func.__name__} завершён -> {repr(result)[:200]}", level=level)
                return result
            except Exception as e:
                log(f"❌ Ошибка в {func.__name__}: {e}", level="ERROR")
                raise
        return wrapper
    return decorator