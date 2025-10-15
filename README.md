# custom_logger
-[git 서브모듈 추가 참고](https://github.com/pupaxjong/Tip/blob/master/git.md)   

```sh
# 설치 라이버러리
pip install colorama
```

```
main.py 에 사용.
- 알림 받을 메신저 설정

from custom_logger import setup_logger, logger
import logging


# 한 번만 설정. 아래 메신서별 초기화. 로그 레벨에 따라 다른 메신저 또는 다른 채널로 받고 싶을때
  ddefault 만 잇으면 level 이상만 메신저로 알림 받음.
alert_channels={
    "default": {
        "channel": "slack",
        "config": {...},
        "level": logging.WARNING  # 기본 알림 레벨
    },
    'WARNING': {
        'channel': 'discord',
        'config': {'webhook_url': 'https://discord.com/api/webhooks/XXX/YYY'}
    }
    'ERROR': {
        'channel': 'slack',
        'config': {'webhook_url': 'https://hooks.slack.com/services/XXX/YYY/ZZZ'}
    },  
    'CRITICAL': {
        'channel': 'telegram',
        'config': {'bot_token': '123456:ABCDEF', 'chat_id': '987654321'}
    }
}

# 메시지 받고 싶지 않으면 인자 넣지 말것.
setup_logger(alert_channels, 
    alert_keywords=['DB 오류', '결제 실패']  # 키워드가 있을 경우만 전송됨
    alert_prefix='[hahaha@web01]'
)

# 테스트 로그
logger.debug("디버그 메시지")                     # ❌ 전송 안 됨
logger.info("정보 메시지")                        # ❌ 전송 안 됨
logger.warning("경고 메시지")                     # ❌ 전송 안 됨
logger.error("사용자 로그인 실패")                # ❌ 키워드 없음 → 전송 안 됨
logger.error("DB 오류 발생! 연결 끊김")           # ✅ 키워드 포함 → 해당 메신저 전송
logger.critical("결제 실패: 카드 오류")           # ✅ 키워드 포함 → 해당 메신저 전송
logger.critical("서버 다운됨")                     # ❌ 키워드 없음 → 전송 안 됨
=======================



다른 py 파일에서 사용할때
from custom_logger import logger

logger.debug("모듈 A에서 디버그 로그")
```

