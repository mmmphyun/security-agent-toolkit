---
repo: "https://github.com/mmmphyun/aleph-project"
topic: "L4 네트워크 격리: EC2 보안 그룹 원자적 전면 교체와 Connection Tracking 한계"
tags: ["AWS", "EC2", "SecurityGroup", "Boto3", "ZeroTrust", "Forensics", "CloudShield"]
---

# 프로젝트 제목: CloudShield — L4 EC2 원자적 격리 보안 그룹 교체 및 Connection Tracking 한계

## 1. 프로젝트 시작 배경 및 문제 정의 (Why)
- **침해 호스트의 횡적이동(Lateral Movement) 차단:** SSH 무차별 대입이나 취약점 공격으로 호스트가 장악되었을 때, VPC 내부 타 인스턴스나 데이터베이스로의 공격 확산과 C2 서버로의 데이터 유출을 10초 이내에 차단해야 했다.
- **보안 그룹 Ingress 룰 개별 삭제 방식의 폭발 반경(Blast Radius):** 보안 그룹은 다수의 EC2 인스턴스가 공유하는 N:M 구조이므로, 룰을 개별 삭제하면 동일 보안 그룹을 공유하는 정상 운영 인스턴스까지 서비스 다운이 발생하는 치명적 결함이 존재했다.

## 2. 주요 설계 의사결정 및 기술 스택 선정 (Architecture & Trade-offs)
- **원자적 전면 교체 API 채택 (`modify_instance_attribute`):**
  - 개별 룰 회수 대신 `ec2.modify_instance_attribute(InstanceId=..., Groups=[target_sg_id])`를 단 1회의 AWS API 트랜잭션으로 호출하여 인스턴스의 보안 그룹 목록을 격리 전용 SG로 즉각 덮어썼다.
  - 타 정상 인스턴스에 일체 영향을 주지 않고 대상 호스트만 핀포인트로 고립시켰다.
- **격리 보안 그룹 사전 검증 로직 (`validate_quarantine_security_group`):**
  - 이름이나 ID만으로 격리 성공을 판정할 경우, AWS 기본 아웃바운드 허용(`0.0.0.0/0`)이나 관리자 실수로 인바운드 룰이 잔존한 오염된 SG가 바인딩되는 결함을 방지하기 위해, 인/아웃바운드 룰이 모두 0건인지 엄격히 검증했다.
- **상태 기반 멱등성 (Idempotency) 및 결함 격리:**
  - 대상 인스턴스가 이미 유효한 격리 SG 단일 바인딩 상태인 경우 불필요한 수정 API 호출을 생략했다. API 호출 실패 시 상위 파이프라인으로 에러를 전파하지 않고 `quarantine_applied: False`로 결함을 격리했다.

## 3. 핵심 기술적 난관 및 트러블슈팅 (Challenges & Breakthroughs)
- **AWS Stateful 보안 그룹의 Connection Tracking 한계 규명:**
  - 보안 그룹을 전면 차단 SG로 교체하면 신규(NEW) 인/아웃바운드 패킷은 즉시 드롭되지만, 이미 수립되어 있던 기존 추적 연결(ESTABLISHED: 활성 SSH 세션, C2 터널)은 커널 상에서 즉시 종료되지 않고 유지되는 물리적 한계를 확인했다.
  - 이를 해결하기 위해 L4 격리 직후 SSM Run Command 또는 프로세스 강제 종료(`pkill`)를 연계해야 하는 2단계 방어선 필요성을 도출했다.
- **격리 호스트에 대한 포렌식 접근 경로 확보 딜레마:**
  - 인바운드가 전면 차단된 상태에서 침해 사고 조사를 수행하기 위해, 22번 포트를 열지 않고도 VPC 엔드포인트(443 HTTPS)를 통해 IAM 기반 셸 세션을 여는 AWS SSM Session Manager 연계 아키텍처를 설계했다.

## 4. 인제스터 탐색 힌트 (Key Modules & Functions)
- **핵심 파일:** `src/remediation/remediation.py`, `tests/unit/test_remediation.py`, `tests/conftest.py`
- **주요 클래스/함수:** `quarantine_ec2_instance`, `validate_quarantine_security_group`, `find_quarantine_security_group`

## 5. 결과 및 회고 (Results & Lessons Learned)
- **성과:** Moto 기반 가상 AWS 테스트베드에서 정상 격리, 오염 SG 거부, 멱등성 유지 등 11개 단위 테스트 케이스를 100% 통과하여 10초 이내 원자적 L4 고립을 실증했다.
- **교훈:** 클라우드 인프라 방화벽의 상태 추적(Stateful Tracking) 메커니즘을 저수준에서 이해하지 못하면 신규 패킷 차단과 세션 종료를 혼동하는 보안 설계 결함이 발생할 수 있음을 입증했다.
