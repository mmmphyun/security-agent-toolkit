---
repo: "https://github.com/mmmphyun/aleph-project"
topic: "L7 애플리케이션 방어: WAFv2 LockToken 낙관적 락 기반 /32 IPSet 원자적 차단"
tags: ["AWS", "WAFv2", "LockToken", "OptimisticLocking", "Boto3", "CloudShield"]
---

# 프로젝트 제목: CloudShield — L7 AWS WAFv2 IPSet /32 원자적 차단 및 LockToken 동시성 제어

## 1. 프로젝트 시작 배경 및 문제 정의 (Why)
- **웹 엣지 레벨의 핀포인트 침해 차단:** Credential Stuffing, 웹 스캐닝 등 L7 애플리케이션 위협 발생 시, 인스턴스 전체를 내리지 않고 악성 요청을 유발하는 공격자의 출발지 IP만을 Regional WAF 엣지에서 즉각 차단해야 했다.
- **다중 Lambda 환경에서의 갱신 분실(Lost Update) 위험:** 여러 탐지 인스턴스가 동시에 WAF IPSet을 갱신할 경우, 분산 락 부재로 인해 앞서 등록된 차단 IP가 유실되거나 덮어쓰기 충돌이 발생하는 취약점이 존재했다.

## 2. 주요 설계 의사결정 및 기술 스택 선정 (Architecture & Trade-offs)
- **WAFv2 네이티브 LockToken 기반 낙관적 동시성 제어(OCC):**
  - AWS WAFv2의 `get_ip_set`으로 취득한 `LockToken`을 `update_ip_set` 시점에 대조하는 메커니즘을 채택했다.
  - 다른 프로세스가 중간에 토큰을 갱신하여 `WAFOptimisticLockException`이 발생할 경우, 최신 IP 목록을 재조회하여 최대 3회까지 자동 재시도하는 백오프 루프를 구현했다.
- **분산 락(Redis/DynamoDB) vs 네이티브 LockToken 트레이드오프:**
  - ElastiCache Redis나 DynamoDB 분산 락을 도입할 경우 추가 인프라 비용과 왕복 지연시간(RTT)이 증가하여 10초 관통 대응 목표에 불리하다.
  - WAFv2 네이티브 `LockToken`과 지연 없는 인메모리 재시도 루프를 결합하여 외부 인프라 의존성 없이 $O(1)$ 원자성을 달성했다.
- **오차단(Blast Radius) 방지를 위한 엄격한 `/32` CIDR 통제:**
  - 서브넷 마스크 없는 IP는 단일 호스트(`/32`)로 자동 보정하되, `/24` 등 광범위한 서브넷 대역이 인입될 경우 수백 명의 정상 사용자가 일괄 차단되는 사고를 방지하기 위해 prefixlen이 32가 아닌 요청은 작업을 즉시 거부하도록 통제했다.

## 3. 핵심 기술적 난관 및 트러블슈팅 (Challenges & Breakthroughs)
- **상태 기반 멱등성 검사를 통한 WAF API 호출 비용 절감:**
  - 차단 대상 IP(/32)가 이미 WAF IPSet 목록에 존재하는 경우 쓰기 API 호출을 즉시 생략했다. 불필요한 WAF API 요청 과금을 방지하고, 불필요한 `LockToken` 갱신으로 인한 타 Lambda와의 경합을 사전에 제거했다.
- **주소 목록 무결성 보장:**
  - 신규 주소 병합 시 `dict.fromkeys([*current_addresses, target_cidr])`를 적용하여 기존 차단 순서를 보존하면서 중복 주소 유입을 원천 차단했다.

## 4. 인제스터 탐색 힌트 (Key Modules & Functions)
- **핵심 파일:** `src/remediation/remediation.py`, `tests/unit/test_remediation.py`
- **주요 클래스/함수:** `block_ip_in_waf`, `apply_remediation`

## 5. 결과 및 회고 (Results & Lessons Learned)
- **성과:** 동시 다중 쓰기 충돌 환경에서도 재시도 루프를 통해 차단 IP 유실 0건을 달성하고, 10초 SLA 이내에 L7 엣지 차단을 완결했다.
- **교훈:** 무거운 외부 분산 락에 의존하기 전에 클라우드 네이티브 API가 제공하는 낙관적 락 메커니즘을 최대한 활용하는 것이 레이턴시와 운영 복잡도 측면에서 최적의 해법임을 실증했다.
