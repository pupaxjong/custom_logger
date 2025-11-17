# safe_logger.py

# =========================================
#
# 사용법:
# try:
#     from custom_logger.safe_logger import safe_logger, LogLevel
# except ImportError:
#     safe_logger = None
#     LogLevel = None
#
# if safe_logger and LogLevel:
#     safe_logger(LogLevel.INFO, "작업 시작")
# else:
#     print("작업 시작", flush=True)
# -----------------------------------------
#
# 공통 사용예시:
# safe_logger(LogLevel.DEBUG, "디버그 메시지")
# safe_logger(LogLevel.INFO, "정보 메시지")
# safe_logger(LogLevel.WARNING, "경고 메시지")
# safe_logger(LogLevel.ERROR, "에러 메시지")
# safe_logger(LogLevel.CRITICAL, "치명적인 오류")
# =========================================


import sys
from enum import Enum, auto
from custom_logger import logger

class LogLevel(Enum):
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

def safe_logger(level: LogLevel, message: str):
    """
    optional logger + fallback print 지원
    level: LogLevel Enum
    """
    if logger:
        if level == LogLevel.DEBUG:
            logger.debug(message)
        elif level == LogLevel.INFO:
            logger.info(message)
        elif level == LogLevel.WARNING:
            logger.warning(message)
        elif level == LogLevel.ERROR:
            logger.error(message)
        elif level == LogLevel.CRITICAL:
            logger.critical(message)
    else:
        # fallback print + stdout/stderr 구분
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            print(f"[{level.name}] {message}", file=sys.stderr, flush=True)
        else:
            print(f"[{level.name}] {message}", flush=True)
