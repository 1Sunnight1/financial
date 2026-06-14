# logger.py
import os
from datetime import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"finance_{datetime.now().strftime('%Y%m%d')}.log")

# Управление логированием: можно включать/выключать через UI
DEBUG = False          # вывод в терминал
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