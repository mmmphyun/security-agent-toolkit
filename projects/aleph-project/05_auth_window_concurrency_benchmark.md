---
repo: "https://github.com/mmmphyun/aleph-project"
topic: "동시성 벤치마크와 탐지 정확도: Cloudflare 가중 카운터의 이산적 붕괴와 타임스탬프 슬라이딩 로그 전환"
tags: ["Concurrency", "Benchmark", "DynamoDB", "SlidingLog", "FalsePositive", "CloudShield"]
---

# 프로젝트 제목: CloudShield — 인증 실패 누적 윈도우 동시성 벤치마크와 통계적 근사의 붕괴

## 1. 프로젝트 시작 배경 및 문제 정의 (Why)
- **CI 멀티스레드 레이스 컨디션 실패 (Incident):** 커밋 `280a020` 실행 중 `test_concurrent_record_failure_race_condition`에서 `AssertionError: assert 4 == 5`가 간헐적으로 발생했다. 5개 스레드가 동일 키에 동시 인입될 때 단일 키 낙관적 락(OCC)의 재시도 소진으로 1건의 업데이트가 유실(Lost Update)되었다.
- **3대 트레이드오프 딜레마:** 10초 관통 SLA 지연시간 예산 준수, 동시 스레드 인입 시 데이터 유실 0%, 5분 윈도우 경계면 및 비균등 버스트 트래픽에 대한 오탐(FP)/미탐(FN) 0%를 동시에 만족해야 했다.

## 2. 주요 설계 의사결정 및 기술 스택 선정 (Architecture & Trade-offs)
- **4대 아키텍처 대안 실측 비교:**
  - **대안 A (단일 키 OCC):** 스레드 증가 시 재시도 소진으로 인한 Lost Update 발생, 테일 레이턴시 스파이크.
  - **대안 B (고정 텀블링 윈도우):** 경계면 분할로 인해 5회 임계치 공격에 대해 100% 탐지 누락 발생.
  - **대안 C (가중 2-버킷 카운터 / Cloudflare 모델):** 선형 시간 감쇠 가중합 추정 적용.
  - **대안 D (3-버킷 타임스탬프 슬라이딩 로그, 최종 채택):** 버킷 파티셔닝 + `list_append` 락 프리 원자적 누적 및 양방향 유효 구간 정밀 필터링.

## 3. 핵심 기술적 난관 및 트러블슈팅 (Challenges & Breakthroughs)
- **Cloudflare 가중 카운터 모델의 이산적 붕괴 실증:**
  - 대규모 트래픽($N \gg 1000$)에서는 대수의 법칙으로 오차가 0%에 수렴하지만, 보안 공격 특유의 **극단적 소규모 이산 임계치($N=5, 2$)**와 **비균등 버스트(Burst)** 환경에서는 단 1회 왜곡이 20~50% 오차를 유발했다.
  - 151초 내 5회 집중 공격 탐지 누락(FN 2건), 301초 전 만료 이벤트로 인한 오차단(FP 2건)이 실측 계측으로 증명되었다.
- **3-버킷 타임스탬프 슬라이딩 로그의 8대 시나리오 100% 완결:**
  - 경계면 균등 분할, 비균등 버스트, 만료 이벤트 격리, 역순/지연 인입(Lambda 비동기 스케줄링으로 인한 t=450 후 t=299 인입) 등 8대 전 시나리오에서 오탐/미탐 0건(정확도 100%)을 증명했다.

## 4. 인제스터 탐색 힌트 (Key Modules & Functions)
- **핵심 파일:** `src/remediation/auth_window.py`, `tests/unit/test_auth_window.py`, `docs/roles/cloud-a/2026-09-23-auth-window-concurrency-benchmark.md`
- **주요 클래스/함수:** `record_failure`, `check_threat`, `test_concurrent_record_failure_race_condition`

## 5. 결과 및 회고 (Results & Lessons Learned)
- **성과:** 15개 동시 스레드 환경에서도 유실율 0.0%, P50 지연시간 36.47ms, 8대 공격 시나리오 탐지 정확도 100%를 달성했다.
- **교훈:** 대규모 CDN 트래픽 제어에 성공한 알고리즘(가중 윈도우)이라도, 이산적이고 비균등한 보안 침해사고 도메인에 맹목적으로 차용할 경우 통계적 가정이 붕괴할 수 있음을 실측으로 입증했다.
