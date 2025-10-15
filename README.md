# custom_logger 서브모듈로 추가
- [git 사용법 참고](https://github.com/pupaxjong/Tip/blob/master/git.md)   

### 서브모듈 관련 참고
```sh
# 참고.
git submodule add <URL> <경로>             # 서브모듈 추가
git submodule update --init --recursive   # 서브모듈 초기화 및 다운로드
git submodule update --remote             # 서브모듈 최신 커밋으로 갱신. [.gitmodules] 파일에 [branch = main] 를 추가해야 된다.

# 🔧 update --init --recursive 를 사용하는 이유
# 1. 누군가가 서브모듈이 포함된 Git 저장소를 git clone으로 복제했어.
# 2. 서브모듈 디렉토리는 비어 있거나 .gitmodules 파일만 있고 코드가 없을때. 
# git submodule update --init → 서브모듈을 초기화하고 체크아웃함. 즉, 서브모듈 디렉토리에 실제 코드가 생김.
# git submodule update --init --recursive → 서브모듈 안에 또 다른 서브모듈이 있을 경우, 하위 서브모듈까지 모두 초기화함.
```

### 서브모듈 추가
- 서브모듈 추가후에 git submodule update --remote 를 사용하기 위해서 [.gitmodules] 파일에 [branch = main] 를 추가한다.
```sh
git submodule add https://github.com/pupaxjong/custom_logger.git custom_logger
```

<br> <br>   

# custom_logger
- 설치 라이버러리
```sh
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

