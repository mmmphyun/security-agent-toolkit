---
title: "파이썬 기반 로그 파서 리팩터링: 관심사 분리와 예외 처리 강화"
slug: "c01-agent-core-day02-log-parser-refactoring"
description: "손상된 CSV 보안 로그 파싱 과정에서 발생한 부작용을 제거하고, 순수 함수 구조와 리포팅 레이어로 분리한 엔지니어링 기록입니다."
pubDate: 2026-08-29
tags: ["Python", "Security Automation", "Refactoring", "Logging"]
category: "AI·보안 자동화"
status: "published"
---

## 1. 개요 및 학습 맥락 (Context & Objective)

보안 관제 자동화의 출발점은 다양한 이종 시스템에서 수집되는 비정형 및 반정형 로그 텍스트를 손실 없이 파싱하고 구조화하는 작업이다. 실제 운영 환경의 로그 파일은 무작위 네트워크 절단, 디스크 쓰기 중단, 인코딩 깨짐 등으로 인해 일부 라인이 손상(Broken)되어 전달되는 경우가 빈번하다.

이번 과제의 목표는 불완전한 텍스트 로그 데이터(`log_broken.csv`)를 안전하게 파싱하고, 파싱 성공 데이터와 에러 라인을 정확히 분리하는 로그 분석 에이전트를 구축하는 것이다. 집계된 결과를 바탕으로 미인가 로그인 시도 사용자와 IP를 식별하여 보안 위협을 사전에 포착하는 파이프라인을 구현한다.

---

## 2. 기본 구현의 한계점 (Limitation of Naive Approach)

초기 작성된 `day02_practice.py` 코드는 기능 구동 자체는 가능했으나, 구조적 및 보안 관점에서 다음과 같은 한계점을 지니고 있었다.

### 1. 단일 책임 원칙(SRP) 위반 및 부작용(Side-Effect) 발생
`csv2dict` 함수는 파일 I/O 및 데이터 파싱을 담당해야 하는 로직 내부에서 `print()` 함수를 통해 콘솔 출력을 직접 수행한다. 이는 비즈니스 로직과 데이터 표현(Presentation) 레이어가 강하게 결합되어, 로그 파서를 다른 모듈이나 CLI, 웹 API 환경에서 재사용할 때 원치 않는 콘솔 출력이 발생하는 부작용을 초과한다.

### 2. 예외 상태 정보의 유실
파싱 과정에서 발견된 손상된 라인 번호(`errors`)를 함수 내부에서 출력하고 버린다. 호출자(`main`) 입장에서는 파일 내 몇 번째 라인이 왜 손상되었는지 알 수 없으며, 파싱 성공 데이터만 전달받기 때문에 데이터 파이프라인 상의 추적성이 단절된다.

### 3. 비효율적이고 비파이썬적인(Unpythonic) 반복문 사용
`for l in range(len(lines)):`와 같이 인덱스 배열에 기반한 명시적 루프를 사용했다. 이는 코드 가독성을 해치고 파이썬 고유의 `enumerate()` 래퍼 함수 활용을 제약한다.

### 4. 엄격한 컬럼 검증 부재 및 KeyError 붕괴 위험
CSV 파일의 필드 개수가 정해진 스키마(`keys`)와 일치하지 않을 때, 단순 `zip()` 구조는 짧은 쪽에 맞추어 파싱이 진행되면서 필드가 누락되는 정적 오류를 방지하지 못한다. 또한 파싱 결과 출력부에서 `ips[user]` 형태의 딕셔너리 직접 참조는 해당 키가 존재하지 않을 경우 프로그램 전체를 중단시키는 `KeyError` 위험을 내포한다.

---

## 3. 엔지니어링 의사결정 및 리팩터링 (Engineering Decisions)

기존 코드의 한계점을 해결하기 위해 `day02_llm.py` 구조로 리팩터링을 진행했다.

### 주요 의사결정사항 (Q&A)

**Q. 파싱 함수 내부의 콘솔 출력을 어떻게 처리해야 하는가?**  
**A.** 데이터 파싱 함수 `csv2dict` 내의 모든 `print()` 구문을 제거한다. 대신 `tuple[list[dict[str, str]], list[int]]` 형태의 튜플 반환 타입을 도입하여, 정상 파싱 데이터와 에러 라인 인덱스 리스트를 호출자에게 동시 반환하도록 변경한다. 콘솔 리포팅은 독립된 뷰 함수 `print_summary_report()`에 전담시킨다.

**Q. CSV 라인의 데이터 무결성을 어떻게 보장하는가?**  
**A.** Python 3.10에 도입된 `zip(..., strict=True)` 키워드 인자를 사용한다. 헤더 키(`keys`)의 개수와 읽어들인 CSV 컬럼 요소 수가 일치하지 않으면 즉시 `ValueError`가 발생하므로, 손상된 라인을 정교하게 포착하여 `errors` 리스트에 수집하고 표준 로거(`logging.warning`)로 추적 기록한다.

**Q. 데이터 참조 시 예외 안정성은 어떻게 확보하는가?**  
**A.** 의심 사용자 IP 매핑 데이터 참조 시 직접 인덱싱(`ips[user]`) 대신 `suspect_ips.get(user, 'N/A')` 패턴을 적용하여 데이터 누락 시에도 안전하게 기본값을 반환하도록 수정한다.

### 리팩터링 대조 코드

```python
# [기존 naive 코드: day02_practice.py]
def csv2dict(file: str) -> List[Dict[str, str]]:
    # ...
    for l in range(len(lines)):
        try:
            logs.append(dict(zip(keys, lines[l].split(","), strict = True)))
        except ValueError as e:
            errors.append(l)
            logging.warning(...)
            continue

    if errors is not None:
        print(f"[경고] 오류 {len(errors)}회, {file}의 라인 {errors}")
    print(f"[요약] 정상 {len(logs)}건, 오류 {len(errors)}건")
    return logs  # 에러 라인 인덱스 정보 유실
```

```python
# [리팩터링 후 코드: day02_llm.py]
def csv2dict(file: str) -> tuple[list[dict[str, str]], list[int]]:
    """CSV 파일 파싱 및 순수 데이터/에러 라인 반환 (콘솔 출력 부작용 제거)"""
    try:
        logging.info(f"파싱 시작: {file}")
        with open(file, encoding="utf-8") as f:
            keys = ["time", "user", "event", "ip"]
            lines = f.read().splitlines()
            logs, errors = [], []

            for l_idx, line in enumerate(lines):
                try:
                    logs.append(dict(zip(keys, line.split(","), strict=True)))
                except ValueError as e:
                    errors.append(l_idx)
                    logging.warning(f"{e}, at {file}, line {l_idx} ({line or '빈 줄'})")
                    continue

            logging.info(f"{len(logs)} 줄 파싱 완료")
            return logs, errors
    except FileNotFoundError as e:
        logging.error(f"Code: {e.errno}, Message: {e.strerror}, Target: {e.filename}")
        logging.critical("비정상 종료")
        return [], []
```

---

## 4. 시스템 아키텍처 흐름도 (Mermaid Diagram)

전체 시스템 흐름은 아래 파이프라인과 같이 데이터 수집, 파싱 검증, 분석 집계, 뷰 출력의 단계로 분리되어 수행된다.

```mermaid
sequenceDiagram
    autonumber
    participant Main as main() 모듈
    participant Parser as csv2dict() 파서
    participant Analyzer as 분석 모듈
    participant View as print_summary_report() 뷰

    Main->>Parser: csv2dict(LOGS_TO_ANALYZE) 호출
    Parser->>Parser: 라인 단위 분할 및 zip(strict=True) 검증
    alt 파싱 성공
        Parser-->>Main: tuple(logs, errors) 반환
    else 파일 부재 (FileNotFoundError)
        Parser->>Parser: logging.critical 기록
        Parser-->>Main: [], [] 반환
    end

    Main->>Analyzer: find_suspects(logs)
    Analyzer-->>Main: counts, ips 반환
    Main->>Analyzer: analyze_events(logs)
    Analyzer-->>Main: events 반환

    Main->>View: print_summary_report(...) 데이터 전달
    View->>View: 콘솔 최종 표준 리포트 출력
```

---

## 5. 검증 및 회고 (Verification & Takeaway)

### 검증 결과
손상된 텍스트 로그 파일(`log_broken.csv`)을 통한 실행 테스트 결과는 다음과 같다.

1. **에러 라인 정확 분리**: 무결성이 훼손된 라인 인덱스가 `errors` 리스트에 안전하게 격리되며, 파일 전체 파싱 실패로 전이되지 않음을 확인했다.
2. **로그 추적성 확보**: 발생한 오류 내역이 `agent.log`에 `WARNING` 및 `CRITICAL` 레벨로 기록되어, 콘솔의 깨끗한 출력과 시스템 감사 기록 보존이 동시 성취되었다.
3. **이상 징후 포착**: 실패 임계값(`ALERT_LIMIT = 2`) 이상의 비정상 접근 시도 사용자와 해당 발신 IP 주소를 정확히 추출하여 표시했다.

### 핵심 배움 (Takeaway)

* **관심사의 분리(Separation of Concerns)**: 파싱 로직, 통계 로직, 뷰 로직이 단일 함수 내에 엉켜 있을 경우 코드 확장성은 급격히 떨어진다. 데이터의 수집과 표현을 분리하는 구조 설계가 자동화 시스템의 기본 요건이다.
* **`zip(..., strict=True)`의 무결성 보장**: 파이썬 3.10에 도입된 `strict` 옵션은 CSV 파싱 시 예기치 못한 스키마 변형이나 누락 라인을 인라인 단계에서 가장 확실히 차단하는 안전장치이다.
* **Logging과 Print의 명확한 역할 구별**: 개발자 및 운용자를 위한 감성/디버그 정보는 구조화된 `logging`으로 전송하고, 최종 사용자나 관제 화면 출력은 표준 인터페이스 뷰로 전담시키는 엄격함이 필요하다.