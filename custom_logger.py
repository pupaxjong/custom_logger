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
class AlertHandler(logging.Handler):
    def __init__(self, alert_channels=None, keywords=None, prefix=None):
        super().__init__()
        self.alert_channels = alert_channels or {}
        self.keywords = keywords or []
        self.prefix = prefix or ""

    def emit(self, record):
        level_name = record.levelname
        message = self.format(record)

        # 키워드 필터링
        if not self.keywords or any(keyword in message for keyword in self.keywords):
            tagged_message = f"{self.prefix} {message}".strip()

            # 우선 해당 레벨에 맞는 채널 찾기
            channel_info = self.alert_channels.get(level_name)

            # 없으면 default 채널 사용
            if not channel_info:
                default_info = self.alert_channels.get("default")

                if default_info and record.levelno >= default_info.get("level", logging.ERROR):
                    channel_info = default_info
            
            # 채널 정보가 있으면 비동기 전송
            if channel_info:
                threading.Thread(target=self.send_alert, args=(level_name, tagged_message, channel_info)).start()

    def send_alert(self, level_name, message, channel_info):
        try:
            channel = channel_info.get('channel')
            config = channel_info.get('config', {})

            if channel == 'slack' and 'webhook_url' in config:
                payload = {"text": f":rotating_light: *{level_name}*\n{message}"}
                requests.post(config['webhook_url'], data=json.dumps(payload), headers={'Content-Type': 'application/json'})

            elif channel == 'telegram' and 'bot_token' in config and 'chat_id' in config:
                url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
                payload = {"chat_id": config['chat_id'], "text": f"[{level_name}] {message}"}
                requests.post(url, data=payload)

            elif channel == 'discord' and 'webhook_url' in config:
                payload = {"content": f"🚨 **{level_name}**\n{message}"}
                requests.post(config['webhook_url'], data=json.dumps(payload), headers={'Content-Type': 'application/json'})

        except Exception as e:
            print(f"[알림 전송 실패] {e}")

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
    handler.addFilter(LevelFilter(level_name))
    handler.addFilter(LevelFilter(level_name))  # 정확히 일치하는 레벨만 기록    
    return handler

# 로거 초기화 함수
def setup_logger(alert_channels=None, alert_keywords=[], alert_prefix='[hahaha@web01]'):
    logger.setLevel(logging.DEBUG)

    # 핸들러 중복 방지
    if not logger.handlers:
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColorFormatter('%(message)s', datefmt='%Y-%m-%d %H:%M:%S.%f'))
        logger.addHandler(console_handler)

        # 파일 핸들러
        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            logger.addHandler(create_file_handler(level))

        # 알림 핸들러
        if alert_channels:
            alert_handler = AlertHandler(alert_channels=alert_channels, keywords=alert_keywords, prefix=alert_prefix)
            alert_handler.setFormatter(MicrosecondFormatter('[%(asctime)s] %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S.%f'))
            logger.addHandler(alert_handler)

        logger.debug('디버그 메시지입니다.')
        logger.info('Info 메시지입니다.')
        logger.warning('경고 메시지입니다.')
        logger.error('에러 발생! 메시지입니다.')
        logger.critical('치명적인 오류! 메시지입니다.')

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
