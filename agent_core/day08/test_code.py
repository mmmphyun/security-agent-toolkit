# 4교시. 코드 리뷰와 테스트 — 사람 눈과 기계 눈

import json

def parse_judgment(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print("[파싱 실패] JSON이 아니다:", text[:40])
        return None


assert parse_judgment('{"severity": "high"}') == {"severity": "high"}
assert parse_judgment('그럴듯한 문장입니다') is None, "깨진 입력은 None이어야 한다"
assert parse_judgment('') is None
print("[테스트 통과] parse_judgment 3건 모두 정상")

'''
Q. 테스트 코드는 함수가 존재하는 파일 내에 해당 함수 테스트 코드를 적는게 맞아? 아니면 모듈화된 함수들의 테스트 코드를 한 파일 내에 모아서 돌리는게 맞아?
A. 테스트 코드는 프로덕션 소스 코드와 완전히 분리된 별도 디렉터리(tests/)에 모듈별로 1:1 대응하여 작성하는 것이 표준 아키텍처.
    - 함수 파일 내부에 테스트 코드를 작성하는 방식의 문제점: 프로덕션 코드 오염, 불필요한 의존성 전파, 배포 및 보안 리스크
    - 한 파일에 모든 테스트 코드를 모아서 돌리는 방식의 문제점: 유지보수 불가, 테스트 격리 실패, 부분 실행 및 CI/CD 비효율

```실무 예시 구조
my_project/
├── config.json
├── config_loader.py
├── ask_llm.py
└── tests/
    ├── __init__.py
    ├── test_config_loader.py  # config_loader.py 단위 테스트
    └── test_ask_llm.py        # ask_llm.py 단위 테스트 (외부 API Mocking)
```

Q. 강의 자료 상 파일을 읽는 함수의 경우 테스트 용 파일을 만들고 테스트 후 지운다던데, 테스트 용 파일 생성도 테스트 코드 파일 내에서 함께 진행해?
A. 방식 1: 인메모리 Mocking (가장 권장되는 표준) - 실제로 디스크에 파일을 쓰지 않고, 파이썬 내장 unittest.mock.mock_open을 사용해 파일 읽기 동작만 메모리 상에서 가로챔.
            => 실제 디스크 I/O가 발생하지 않아 테스트 속도가 압도적으로 빠르고, 권한 문제나 테스트 중단 시 찌꺼기 파일이 남을 위험이 0%
    방식 2: 격리된 임시 디렉터리 픽스처 (실제 파일 I/O가 반드시 필요한 경우) - 테스트 프레임워크가 제공하는 임시 파일 픽스처(Fixture) 또는 tempfile 표준 모듈을 사용.
            => 테스트 러너가 OS의 임시 디렉터리(/tmp 등)에 격리된 공간을 생성하고, 테스트 성공/실패/예외 발생 여부와 관계없이 사후 정리(Teardown)를 100% 보장

**강의 자료처럼 테스트 코드 본문 안에서 open("test.json", "w")을 직접 쓰고 마지막에 os.remove("test.json")을 호출하는 방식은,**
**테스트 도중 assert 실패나 예외가 터졌을 때 삭제 라인까지 도달하지 못해 테스트 디렉터리가 오염되므로 실무에서 엄격히 금지**

강의 자료를 보고 느낀 쎄함과 의문을 직접 알아보고 정정 및 해결함.
'''