# 1교시. 설정 분리 — config.json

import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = "config.json"   # 이 값만 바꾸면 다른 회사가 된다
FILE_PATH = os.path.join(BASE_DIR,  CONFIG_FILE)
SEVERITY_ORDER = ["low", "medium", "high"]   # 왼쪽일수록 약하다

with open(FILE_PATH, encoding="utf-8") as f:   # 설정 파일을 읽는다 (Day 3)
    config = json.load(f)
print(f"[설정] {FILE_PATH} — 게이트 기준: {config['approve_severity']} 이상")

judgments = [
    {"rule": "port_scan", "severity": "low", "tool": "log_only"},
    {"rule": "night_login", "severity": "medium", "tool": "watch"},
    {"rule": "brute_force", "severity": "high", "tool": "lock_account"},
]

gated = 0
passed = 0
if config['approve_severity'] in SEVERITY_ORDER:
    base_severity = SEVERITY_ORDER.index(config['approve_severity'])
else:
    base_severity = SEVERITY_ORDER.index('high')
    print(f"[설정 오류] 없는 심각도 값: '{config['approve_severity']}' — high로 간주한다")

for judgment in judgments:
    severity = SEVERITY_ORDER.index(judgment['severity'])

    if severity >= base_severity:
        gated += 1
        print(f"[게이트] {judgment['rule']} ({judgment['severity']}) — 사람에게 묻는다")
    else:
        passed += 1
        print(f"[통과] {judgment['rule']} ({judgment['severity']}) — 바로 실행한다")

print(f"[요약] 게이트 {gated}건 / 통과 {passed}건")




'''
Q. 설정 분리와 함수 모듈화가 쓰이는 상황이 어떻게 다른지?
A. 변경 대상이 '데이터(상태/환경)'인가 '행위(비즈니스 로직)'인가에 따른 명확한 역할 분리.
    - 설정 분리 (Configuration) : 코드 실행 로직은 그대로 두고 '환경값'만 바꿔야 할 때
                                개발, 검증(Staging), 운영(Production) 등 배포 환경에 따라 값이 달라져야 할 때
                                빌드나 코드 재컴파일/배포 과정 없이 컨테이너 환경변수나 마운트된 설정 파일 교체만으로 런타임에 값을 주입하고자 할 때
    - 함수 모듈화 (Logic) : 재사용 가능한 제어 흐름, 프로토콜 통신 규격, 데이터 변환 등 공통 로직 캡슐화
                        HTTP 요청 전송, 에러 핸들링, 재시도(Retry), 응답 파싱 등 '어떻게 처리하는가'에 대한 알고리즘이 변경될 때
                        여러 스크립트나 서비스에서 동일한 처리 파이프라인을 호출해야 할 때
                        로직 수정 시 단위 테스트(Unit Test)를 통해 코드 검증이 필요할 때

아래는 예시.
```config.json
{
  "model": "gemini-3.5-flash-lite",
  "approve_severity": "high",
  "report_folder": "reports",
  "webhook_url": "http://127.0.0.1:5001/alert"
}
```
```config_loader.py
import json
from pathlib import Path
from typing import Any, Dict

CONFIG_FILE_NAME = "config.json"
REQUIRED_KEYS = {"model", "approve_severity", "report_folder", "webhook_url"}

_cached_config: Dict[str, Any] = {}


def load_config() -> Dict[str, Any]:
    global _cached_config
    if _cached_config:
        return _cached_config

    config_path = Path(__file__).resolve().parent / CONFIG_FILE_NAME
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Malformed JSON in {config_path}: {e}") from e

    missing = REQUIRED_KEYS - data.keys()
    if missing:
        raise KeyError(f"Missing required config keys: {missing}")

    _cached_config = data
    return _cached_config
```
```ask_llm.py
from typing import Any, Dict
import requests
from config_loader import load_config

config: Dict[str, Any] = load_config()


def ask_llm(prompt: str) -> str:
    url = "https://api.example.com/v1/chat/completions"
    headers = {"Content-Type": "application/json"}

    body = {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": "너는 보안 관제 어시스턴트다. 항상 한국어로 답한다."},
            {"role": "user", "content": prompt},
        ],
    }

    response = requests.post(url, headers=headers, json=body, timeout=30)
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]
```


'''