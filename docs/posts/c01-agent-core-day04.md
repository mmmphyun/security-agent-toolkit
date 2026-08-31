---
title: "외부 REST API 연동을 통한 위협 IP 인텔리전스 인리치먼트 파이프라인 설계"
slug: "c01-agent-core-day04"
description: "requests 기반 실시간 IP 지리 정보 조회, HTTP 타임아웃 방어 및 멱등성을 고려한 경보 데이터 보강 계층 리팩터링 기록"
pubDate: 2026-08-30
tags: ["Python", "Security Automation", "Threat Intelligence", "REST API", "Refactoring"]
category: "AI·보안 자동화"
status: "published"
---

## 1. 오늘의 학습 개념 요약

보안 관제 시스템에서 탐지된 IP 주소 자체는 단순한 네트워크 식별자에 불과하다. 신속한 위협 분석과 차단 정책 수립을 위해서는 공격 출발지의 국가, ISP, ASN 등의 맥락 정보가 결합되어야 한다. 이처럼 원시 경보 데이터에 외부 위협 인텔리전스를 결합하여 데이터의 가치를 높이는 공정을 데이터 보강이라고 부른다.

파이썬의 `requests` 라이브러리를 활용하면 RESTful API 엔드포인트와 통신하여 실시간 지리 및 네트워크 정보를 수집할 수 있다. 그러나 외부 네트워크 I/O는 응답 지연이나 연결 실패 위험을 내포하므로, 타임아웃 설정과 철저한 예외 처리 계층을 구축하는 것이 파이프라인의 생존성을 결정한다.

## 2. 전체 산출물 파이프라인 구조

Day 04 실습 산출물은 `request.py`와 `request_llm.py`로 구성되며, 로컬 경보 파일 인제스트부터 외부 API 통신 및 보강 데이터 저장까지 순차적으로 동작한다.

```mermaid
flowchart LR
    A["로컬 경보 파일 (alerts.json)"] --> B["load_alerts_data (JSON 파싱)"]
    B --> C{"IP 필드 존재 검사"}
    C -->|IP 없음 (brute_force)| D["조회 건너뜀 (기존 객체 유지)"]
    C -->|IP 존재 (spraying / night)| E["fetch_ip_info (REST API 통신)"]
    E -->|HTTP GET /json/IP| F["IP-API 서비스"]
    F -->|country, isp 수신| G["단일 경보 객체 보강"]
    D & G --> H["enriched_alerts.json 저장"]
    H --> I["print_summary_report (추적 로그 출력)"]
```

## 3. 기본 구현의 한계점

강의 기본 예시 코드는 타임아웃 없이 무조건 모든 경보 객체에 접근하는 형태를 띤다.

```python
# 단순 API 호출 방식 (베이스라인 예제)
import requests

for alert in alerts:
    res = requests.get(f"http://ip-api.com/json/{alert['ip']}")
    data = res.json()
    alert["country"] = data["country"]
    alert["isp"] = data["isp"]
```

이 코드는 실제 운영 환경에서 다음과 같은 치명적 결함을 드러낸다.

1. **스레드 블로킹 위험:** `requests.get`에 `timeout` 매개변수를 지정하지 않으면 원격 서버 장애나 네트워크 패킷 유실 시 기본 소켓 타임아웃(운영체제 기본 수 분)에 도달할 때까지 파이썬 프로세스 전체가 멈춘다.
2. **KeyError 런타임 크래시:** 계정 기반 공격인 `brute_force` 경보는 `ip` 필드를 포함하지 않는다. `alert['ip']`에 무조건 접근하면 즉시 `KeyError`가 발생해 프로그램이 종료된다.
3. **네트워크 오류 미처리:** `response.raise_for_status()` 검증 없이 무조건 `res.json()`을 파싱하면 404, 500 등 HTTP 에러 페이지 HTML 응답 유입 시 `json.decoder.JSONDecodeError`로 중단된다.

## 4. 엔지니어링 의사결정 및 리팩터링

### 4.1. 1차 프로토타입 구현: 방어적 필드 검사와 상태 코드 검증
1차 구현(`request.py`)에서는 `if "ip" in alert:` 조건을 두어 IP가 존재하는 경보만 선별적으로 조회하고, API 응답의 `data["status"] == "success"` 여부를 확인한 후 데이터를 결합했다.

```python
def extract_alerts_with_ip(json_file: str):
    alerts = []
    try:
        with open(json_file, encoding="utf-8") as f:
            json2dict = json.load(f)
            alerts = json2dict["alerts"]
        
        for i, alert in enumerate(alerts):
            if "ip" in alert:
                lookup = lookup_ip(alert["ip"])
                if lookup:
                    alert["country"] = lookup["country"]
                    alert["isp"] = lookup["isp"]
                alerts[i] = alert

        json2dict["alerts"] = alerts
        return json2dict, alerts
    except FileNotFoundError:
        return {}
```

### 4.2. 2차 최적화: 타임아웃 방어선 및 메타데이터 주입
2차 최적화(`request_llm.py`)를 거치며 네트워크 계층의 방어력을 대폭 강화했다. `timeout=5`를 지정하여 무한 대기를 차단하고, 조회 성공 여부를 `lookup_success` 불리언 필드로 명시화하여 후속 파이프라인의 예측 가능성을 높였다.

```python
def fetch_ip_info(ip: str) -> Optional[Dict[str, str]]:
    """외부 API를 통해 단일 IP의 국가 및 ISP 정보를 조회한다 (타임아웃 및 예외 차단)."""
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "success":
            return {"country": data["country"], "isp": data["isp"]}
    except (requests.RequestException, KeyError):
        pass
    return None

def enrich_alert_with_ip(alert: Dict[str, Any]) -> Dict[str, Any]:
    ip = alert.get("ip")
    if not ip:
        return alert

    ip_info = fetch_ip_info(ip)
    if ip_info:
        alert["country"] = ip_info["country"]
        alert["isp"] = ip_info["isp"]
        alert["lookup_success"] = True
    else:
        alert["lookup_success"] = False

    return alert
```

## 5. 검증 및 회고

`request_llm.py`를 실행하여 3건의 경보 데이터를 보강한 결과 화면 출력은 다음과 같다.

```text
[추적] 185.220.101.34 -> Germany (Stiftung Erneuerbare Freiheit)
[추적] 211.45.12.9 -> South Korea (SamsungSDS Inc)
```

`enriched_alerts.json` 파일에도 의도한 정보가 정확히 병합되었다.

```json
{
  "file": "sample_server.log",
  "parsed": 17,
  "skipped": 5,
  "alerts": [
    {
      "rule": "brute_force",
      "user": "admin",
      "count": 5
    },
    {
      "rule": "password_spraying",
      "ip": "185.220.101.34",
      "accounts": 4,
      "country": "Germany",
      "isp": "Stiftung Erneuerbare Freiheit",
      "lookup_success": true
    },
    {
      "rule": "night_login",
      "time": "03:17:09",
      "user": "admin",
      "ip": "211.45.12.9",
      "country": "South Korea",
      "isp": "SamsungSDS Inc",
      "lookup_success": true
    }
  ]
}
```

IP 필드가 없는 첫 번째 `brute_force` 경보는 에러 없이 원형을 유지했고, 2건의 위협 IP에 대해서만 국가와 통신사 정보가 정확히 부가되었다. 외부 네트워크 통신을 수반하는 보안 자동화에서는 타임아웃과 예외 격리가 시스템 안정성의 제1원칙임을 체득했다.
