# custom_logger.py

""" 수동으로 루프 돌릴때 사용 - 사용하지 말것
import asyncio
import logging

loop = asyncio.new_event_loop()
logger.debug('Using selector: %s', loop._selector.__class__.__name__)
asyncio.set_event_loop(loop)
loop.run_until_complete(main())
"""


import logging
import os
import json
import requests
import threading
import time
from logging.handlers import TimedRotatingFileHandler

# 전역 로거 객체
logger = logging.getLogger()
_LOGGER_INITIALIZED = False 

# colorama 설치 여부 확인
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    print("[ERROR] colorama 라이브러리가 설치되어 있지 않습니다.")
    print("터미널에 아래 명령어를 입력하여 설치하세요:")
    print("    pip install colorama")

# 마이크로초 지원 포맷터
class MicrosecondFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        t = time.strftime("%Y-%m-%d %H:%M:%S", ct)
        s = f"{t}.{int(record.msecs * 1000):06d}"
        return s

# 색상 포맷터 정의
class ColorFormatter(MicrosecondFormatter):
    def format(self, record):
        timestamp = self.formatTime(record, self.datefmt)
        message = record.getMessage()
        if COLORAMA_AVAILABLE:
            color = {
                'DEBUG': Fore.CYAN,
                'INFO': Fore.GREEN,
                'WARNING': Fore.YELLOW,
                'ERROR': Fore.RED,
                'CRITICAL': Fore.MAGENTA
            }.get(record.levelname, Fore.WHITE)
            return f"{color}[{timestamp}] {message}{Style.RESET_ALL}"
        else:
            return f"[{timestamp}] {message}"

# 로그 레벨 필터 클래스
class LevelFilter(logging.Filter):
    def __init__(self, level_name):
        self.level = logging._nameToLevel[level_name]

    def filter(self, record):
        return record.levelno == self.level

# 알림 핸들러 정의
# 알림 핸들러 정의 (수정됨)
# 알림 핸들러 정의 (재귀 방지 필터 추가 완료)
import logging
import threading
import json
import requests


class AlertHandler(logging.Handler):
    """
    알림 핸들러 (Slack, Telegram, Discord)
    requests 사용, 무한 루프 방지 플래그 적용
    """
    def __init__(self, alert_channels=None, keywords=None, prefix=None):
        super().__init__()
        self.alert_channels = alert_channels or {}
        self.keywords = keywords or []
        self.prefix = prefix or ""
        self._sending_lock = threading.Lock()

    def emit(self, record):
        # 이미 AlertHandler에서 알림 전송 중이면 무시
        if getattr(record, "__alert_in_progress", False):
            return

        # 현재 레코드에 플래그를 심어 재귀 호출 방지
        record.__alert_in_progress = True

        try:
            level_name = record.levelname
            message = self.format(record)
            tagged_message = f"{self.prefix} {message}".strip()

            # 키워드 필터
            if not self.keywords or any(k in message for k in self.keywords):
                channel_info = self.alert_channels.get(level_name)
                if not channel_info:
                    default_info = self.alert_channels.get("default")
                    if default_info and record.levelno >= default_info.get("level", logging.ERROR):
                        channel_info = default_info

                if channel_info:
                    # 단일 스레드로 알림 전송
                    threading.Thread(
                        target=self._send_alert_fire_and_forget,
                        args=(level_name, tagged_message, channel_info),
                        daemon=True
                    ).start()
        finally:
            # 플래그 제거 (재사용 가능)
            record.__alert_in_progress = False

    def _send_alert_fire_and_forget(self, level_name, message, channel_info):
        logging.disable(logging.CRITICAL)  # 🔒 이 스레드에서 모든 로깅 차단
        """
        실제 알림 전송
        """
        try:
            channel = channel_info.get("channel")
            config = channel_info.get("config", {})

            if channel == "slack" and "webhook_url" in config:
                payload = {"text": f":rotating_light: *{level_name}*\n{message}"}
                requests.post(
                    config["webhook_url"],
                    data=json.dumps(payload),
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )

            elif channel == "telegram" and "bot_token" in config and "chat_id" in config:
                url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
                payload = {"chat_id": config["chat_id"], "text": f"[{level_name}] {message}"}
                requests.post(url, data=payload, timeout=5)

            elif channel == "discord" and "webhook_url" in config:
                payload = {"content": f"🚨 **{level_name}**\n{message}"}
                requests.post(
                    config["webhook_url"],
                    data=json.dumps(payload),
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                
        except Exception:
            # 실패해도 무시
            pass

        finally:
            logging.disable(logging.NOTSET)  # 🔓 원상복구
                    
# 파일 핸들러 생성 함수
def create_file_handler(level_name):
    os.makedirs("logs", exist_ok=True)

    # 오늘의 로그는 error.txt, info.txt 등으로 저장됨
    handler = TimedRotatingFileHandler(
        filename=f'logs/{level_name.lower()}.txt',
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )

    # 회전된 파일 이름: error.2025-10-02.txt
    handler.suffix = "%Y-%m-%d.txt"

    handler.setLevel(getattr(logging, level_name))
    handler.setFormatter(MicrosecondFormatter('[%(asctime)s] %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S.%f'))
    handler.addFilter(LevelFilter(level_name))  # 정확히 일치하는 레벨만 기록    
    return handler

# 로거 초기화 함수
def setup_logger(alert_channels=None, alert_keywords=[], alert_prefix='[hahaha@web01]'):
    global logger # 전역 logger 객체를 사용함을 명시
    global _LOGGER_INITIALIZED # 전역 플래그 사용 선언

    # 🚨 [최종 수정] 로거 초기화가 이미 완료되었다면 즉시 반환
    if _LOGGER_INITIALIZED:
        return logger

    # 1. 기존 핸들러 모두 제거 (가장 확실한 중복 방지책)
    # logger.handlers 리스트를 순회하며 핸들러를 제거합니다.
    for handler in list(logger.handlers): 
        logger.removeHandler(handler)
        # 핸들러를 닫아 리소스 해제 (특히 파일 핸들러의 경우 중요)
        try:
            handler.close()
        except:
            pass
    
    logger.setLevel(logging.DEBUG)
    logger.propagate = False   # ✅ 부모 로거로 이벤트 전파 방지

    # 🔹 urllib3 로거 차단 (이 위치에 추가)
    logging.getLogger("urllib3").propagate = False
    logging.getLogger("urllib3").disabled = True


    # 2. 콘솔 핸들러 등록
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColorFormatter('%(message)s', datefmt='%Y-%m-%d %H:%M:%S.%f'))
    logger.addHandler(console_handler)

    # 3. 파일 핸들러 등록
    for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        logger.addHandler(create_file_handler(level))

    # 4. 알림 핸들러 등록
    if alert_channels:
        # AlertHandler 클래스는 이전 답변에서 단일 스레드로 수정된 버전 사용
        alert_handler = AlertHandler(alert_channels=alert_channels, keywords=alert_keywords, prefix=alert_prefix)
        alert_handler.setFormatter(MicrosecondFormatter('[%(asctime)s] %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S.%f'))
        logger.addHandler(alert_handler)


    # ✅ requests 내부 로그 억제
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # 테스트 로그 (setup_logger가 잘 작동했는지 확인용)
    logger.debug('디버그 메시지입니다. (초기화 완료)')
    logger.info('애플리케이션 시작 (초기화 완료)')
    # ... (나머지 테스트 로그는 그대로 유지)

    logger.debug('디버그 메시지입니다.')
    logger.info('애플리케이션 시작')
    logger.warning('경고 메시지입니다.')
    logger.error('에러 발생! 메시지입니다.')
    logger.critical('치명적인 오류! 메시지입니다.')


    # 로거 설정 다 끝난 후
    _LOGGER_INITIALIZED = True   # ✅ 이 줄 반드시 필요
    
    return logger

# 사용법 출력 함수
def print_usage():
    print("\n📢 [custom_logger 사용법 안내]")
    print("1. main.py 에서 setup_logger() 한 번만 호출하여 로거 설정")
    print("2. 다른 모듈에서는 from custom_logger import logger 로 로거 가져다 사용")
    print("3. alert_channels 에 메신저별 설정을 넣어 알림 채널 지정 가능")
    print("4. alert_keywords 에 키워드 리스트를 넣어 해당 키워드가 포함된 메시지만 알림 전송")
    print("5. alert_prefix 에 접두사를 넣어 메시지 앞에 붙여 전송 (예: 서버명, 사용자명 등)")
    print("6. 메시지 받고 싶지 않으면 setup_logger() 인자 없이 호출")
    print("7. colorama 라이브러리가 설치되어 있지 않으면 컬러 출력 안됨")
    print("   - 터미널에 'pip install colorama' 입력하여 설치 권장\n")
    print("\n📘 [사용 예시]")
    print("from custom_logger import setup_logger, logger")
    print("import logging\n")
    print("setup_logger(")
    print("    alert_channels={")
    print("        \"default\": {")
    print("            \"channel\": \"slack\",")
    print("            \"config\": {...},")
    print("            \"level\": logging.WARNING")
    print("        },")
    print("        'ERROR': {")
    print("            'channel': 'slack',")
    print("            'config': {'webhook_url': 'https://hooks.slack.com/services/XXX/YYY/ZZZ'}")
    print("        },")
    print("        'CRITICAL': {")
    print("            'channel': 'telegram',")
    print("            'config': {'bot_token': '123456:ABCDEF', 'chat_id': '987654321'}")
    print("        }")
    print("    },")
    print("    alert_keywords=['DB 오류', '결제 실패'],")
    print("    alert_prefix='[hahaha@web01]'")
    print(")\n")
    print("logger.error(\"DB 오류 발생!\")       # 슬랙으로 비동기 전송")
    print("logger.critical(\"결제 실패!\")       # 텔레그램으로 비동기 전송\n")
