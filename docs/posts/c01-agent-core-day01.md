---
title: "파이썬 문자열 파싱과 Counter를 활용한 인증 실패 로그 탐지기 설계"
slug: "c01-agent-core-day01"
description: "원시 텍스트 로그에서 공백 정규화 파싱을 적용하고 collections.Counter를 통해 무차별 대입 공격 의심 계정을 추출한 단독 설계 기록"
pubDate: 2026-08-30
tags: ["Python", "Security Automation", "Log Parsing", "Counter"]
category: "AI·보안 자동화"
status: "published"
---

## 1. 오늘의 학습 개념 요약

보안 관제와 침해사고 분석의 출발점은 비정형 텍스트 형태로 수집되는 시스템 로그를 정형 데이터로 변환하는 작업이다. 운영체제, 웹 서버, 네트워크 장비가 남기는 접근 로그는 표준 규격을 완전히 따르지 않거나 필드 간 공백 길이가 불규칙한 경우가 흔하다. 원시 로그에서 위협 징후를 식별하려면 데이터 전처리 단계에서 공백 불규칙성을 정규화하고 필드를 안전하게 분리해야 한다.

반복적인 로그인 실패 이벤트는 비인가자의 계정 탈취 시도인 무차별 대입 공격(Brute-force Attack)의 대표적인 지표다. 다량의 로그 스트림에서 계정별 실패 빈도를 빠르게 집계하기 위해 파이썬 표준 라이브러리인 `collections.Counter`를 활용한다. 복잡한 외부 프레임워크 없이 표준 라이브러리만으로 선형 시간 복잡도 내에서 위협 계정을 격리하는 집계 파이프라인의 기초를 구축했다.

## 2. 전체 산출물 파이프라인 구조

Day 01 실습 산출물은 `hello.py` 단일 스크립트로 구성되며, 원시 문자열 로그 인제스트부터 이상 징후 계정 출력까지 순차적 데이터 파이프라인을 형성한다.

```mermaid
flowchart LR
    A["원시 텍스트 로그 (raw_log)"] --> B["parse_log_data (공백 정규화 파싱)"]
    B --> C["정형 딕셔너리 리스트"]
    C --> D["find_suspects (login_failed 이벤트 필터링)"]
    D --> E["Counter 계정 빈도 집계"]
    E --> F{"임계값 검사 (count >= 2)"}
    F -->|조건 만족| G["경보 출력 (확인 필요 계정)"]
```

전체 흐름은 세부 책임을 기준으로 나뉜다.
1. `parse_log_data`: 멀티라인 문자열 로그를 줄 단위로 분리하고, 가변 공백을 처리하여 시간, 사용자명, 이벤트 유형, IP 주소로 구성된 딕셔너리 리스트를 생성한다.
2. `find_suspects`: 이벤트 유형이 `login_failed`와 일치하는 대상자의 사용자 식별자만 추출하여 리스트로 반환한다.
3. 집계 및 판정: `Counter` 객체로 사용자별 실패 빈도를 연산한 뒤, 사전 정의한 임계값(2회 이상)을 만족하는 계정만 필터링하여 이상 징후를 출력한다.

## 3. 기본 구현의 한계점

교재나 입문 튜토리얼에서 흔히 볼 수 있는 단순 구현은 다음과 같은 형태로 작성된다.

```python
# 단순 접근 방식 (베이스라인 예제)
count_dict = {}
for line in raw_log.split("\n"):
    parts = line.split(" ")
    if parts[2] == "login_failed":
        user = parts[1]
        if user in count_dict:
            count_dict[user] += 1
        else:
            count_dict[user] = 1
```

이러한 단순 구현은 실제 운영 환경에서 다음과 같은 치명적인 결함을 유발한다.

1. **고정 구분자 분할로 인한 토큰 왜곡:** 로그 생성 환경에 따라 필드 사이의 공백은 스페이스 1칸, 다중 스페이스, 탭 문자(`\t`)가 혼용된다. `line.split(" ")`처럼 고정 단일 스페이스를 구분자로 사용하면 연속 공백이 빈 문자열(`""`) 토큰으로 파싱되어 필드 인덱스가 밀리는 데이터 오염이 발생한다.
2. **비정상 라인 유입 시 프로세스 중단:** 로그 수집 중 패킷 유실이나 비정상 종료로 인해 필드 수가 부족한 결손 행이 유입되면, 고정 인덱스 참조(`parts[2]`) 시점에서 `IndexError`가 발생해 전체 파이프라인이 멈춘다.
3. **수동 상태 관리로 인한 코드 장황성:** 기본 딕셔너리를 사용하여 키 존재 여부를 매번 조건문으로 검사하는 방식은 불필요한 분기 처리를 늘리고 가독성을 저해한다.

## 4. 엔지니어링 의사결정 및 리팩터링

이러한 한계점을 해결하기 위해 `hello.py`를 단독 설계하면서 세 가지 핵심 엔지니어링 개선을 적용했다.

### 4.1. 매개변수 없는 split()을 통한 가변 공백 정규화 및 가드 클로즈
고정 문자열 분할 대신 인자 없는 `line.split()`을 채택했다. 파이썬의 `str.split()`은 인자를 전달하지 않으면 연속된 모든 공백 문자(스페이스, 탭, 개행)를 단일 구분자로 취급하여 자동으로 축약 분할한다.

```python
def parse_log_data(log_text):
    logs = []
    # 줄바꿈 기준으로 분할
    for line in log_text.strip().splitlines():
        # 공백이 2개 이상이든 탭이든 상관없이 연속된 공백을 기준으로 분할
        parts = line.split() 
        if len(parts) == 4:
            logs.append({
                "time": parts[0],
                "user": parts[1],
                "event": parts[2],
                "ip": parts[3]
            })
    return logs
```

또한 `len(parts) == 4` 가드 조건을 배치하여 비정상적으로 잘리거나 유실된 로그 라인을 메모리 적재 단계에서 사전에 배제했다.

### 4.2. 단일 책임 원칙에 기반한 함수 분리
로그 파싱(`parse_log_data`), 위협 대상 추출(`find_suspects`), 집계 및 경보 출력을 독립된 함수와 로직으로 분리했다. 파싱 함수는 원시 텍스트를 구조화된 데이터로 만드는 책임만 지며, 보안 정책에 따른 이벤트 필터링은 후속 함수가 전담한다.

```python
def find_suspects(logs):
    failed_users = []
    for log in logs:
        if log["event"] == "login_failed":
            failed_users.append(log["user"])
    return failed_users
```

### 4.3. collections.Counter를 활용한 선형 시간 집계
표준 라이브러리 `Counter`를 적용하여 실패 사용자 리스트를 단 한 번의 해시 테이블 연산으로 집계했다.

```python
logs = parse_log_data(raw_log)
counts = Counter(find_suspects(logs))

for user, count in counts.items():
    if count >= 2:
        print(f"확인 필요: {user} — 실패 {count}회")
```

키 존재 여부를 확인하는 수동 분기문 없이 해시 기반으로 $O(N)$ 시간 복잡도 내에서 집계를 완료한다.

## 5. 검증 및 회고

`hello.py`를 실행하여 샘플 로그 스트림을 주입한 결과는 다음과 같다.

```text
확인 필요: admin — 실패 3회
```

로그 상에서 3회 실패한 `admin` 계정은 정확히 탐지되었고, 1회 실패한 `park.js`는 임계값 조건(`count >= 2`)에 따라 필터링되어 오탐을 방지했다.

보안 데이터 파이프라인의 견고함은 엄격한 입력값 정규화와 표준 라이브러리의 적절한 활용에서 나온다. 외부 패키지 도입에 앞서 언어 내장 기능을 최대로 활용하는 것이 가볍고 결함 없는 보안 자동화 스크립트를 작성하는 기본기임을 확인했다.
