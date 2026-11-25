---
repo: "https://github.com/mmmphyun/aleph-project"
topic: "배포 전 로컬 3단계 검증, AWS 실인프라 프로비저닝, 그리고 제어·데이터 평면 시차 실측"
tags: ["AWS", "Terraform", "Docker", "Trivy", "DataPlane", "CloudShield"]
---

# 프로젝트 제목: CloudShield — 실인프라 프로비저닝과 제어·데이터 평면 시차 실측

## 1. 프로젝트 시작 배경 및 문제 정의 (Why)
- **로컬 모의 테스트와 실제 AWS 환경 사이의 간극:** Moto 기반 단위 테스트가 모두 통과하더라도, Windows에서 패키징한 Lambda zip 안에 Linux용 C-Extension(`pydantic_core`)이 제대로 들어갔는지, Terraform IAM 정책이 실제 AWS API 제약을 통과하는지는 배포 전에 확인해야 했다.
- **실인프라 10초 차단 실측 및 원복 필요성:** 시드니 리전(`ap-southeast-2`)에 실제 VPC, EC2, DynamoDB, Lambda, WAFv2를 띄우고 네트워크 담당자의 Kali 공격과 클라우드 B의 Slack 계측을 연결해 실제 차단 시간을 재야 했으며, 테스트 직후 인스턴스를 안전하게 원복할 도구가 필요했다.

## 2. 주요 설계 의사결정 및 기술 스택 선정 (Architecture & Trade-offs)
- **배포 전 로컬 3단계 사전 검증(Pre-flight Gate):**
  1. **런타임 ABI 검증:** `scripts/package_lambda.py`로 만든 `orchestrator.zip`(2.60MB)을 공식 Linux Lambda Docker 컨테이너(`public.ecr.aws/lambda/python:3.12`)에 마운트해 `pydantic_core`와 `threat_orchestrator_handler`가 실제로 import 되는지 확인했다.
  2. **원시 로그 역주입 검증:** 모의 `auth.log`와 Nginx 로그를 파이프라인에 직접 통과시켜 파서와 룰의 오탐 여부를 확인했다.
  3. **Terraform & Trivy 정적 스캔:** `terraform validate`와 `trivy config`를 실행해 HIGH/CRITICAL 취약점 0건을 확인한 뒤 실배포에 들어갔다(기본 KMS 키 사용 LOW 2건은 데모 비용 절감을 위해 유지).
- **공격자 IP 비공개 관리와 타깃 인플레이스 배포:**
  - 공격자 공인 IP(`/32`)를 Git에 올리지 않기 위해 `.gitignore`로 빠진 `terraform.tfvars`에만 주입하고, EC2가 UserData 변경으로 재생성되는 것을 피하려고 `terraform apply -target="module.quarantine_sg"`로 보안 그룹 규칙만 갱신했다.
- **원자적 롤백 스크립트 분리 (`scripts/restore_baseline_sg.py`, `scripts/unblock_waf_ip.py`):**
  - 실측 후 테스트베드를 바로 복구하기 위해, 인스턴스 보안 그룹을 기준선 SG로 되돌리고 재조회로 확정하는 도구와 WAFv2 IPSet에서 차단 IP를 해제하는 CLI 도구를 각각 분리 구현했다.

## 3. 핵심 기술적 난관 및 트러블슈팅 (Challenges & Breakthroughs)
- **Terraform IAM 참조 오타와 AWS API의 Description 문자열 제약:**
  - `modules/lambda/main.tf`에서 선언하지 않은 정책 이름(`aws_iam_policy.least_privilege.arn`)을 참조해 `terraform validate`가 실패한 문제를 수정하고 회귀 테스트를 추가했다.
  - AWS IAM Role/Policy의 `Description` 필드는 ASCII/Latin-1 범위만 허용하므로, 한글 설명이 `ValidationError: 400`을 일으키는 문제를 영문 ASCII로 정리해 해결했다.
- **제어 평면 응답과 데이터 평면 패킷 차단 사이의 1,888ms 시차 규명 (P3-3B 실측):**
  - 현상: 2026-10-14 실인프라 SSH 공격 실측(네트워크 pcap + 클라우드 B Slack ts + 클라우드 A Lambda 계측 합동 결과)에서 5회 실패 도달부터 최초 무응답 SYN 관측까지 총 5.477초로 10초 목표는 충족했다. 그러나 Boto3 `modify_instance_attribute` 응답(13:47:52.500) 뒤 Slack 전송(13:47:54.092)이 공격자 측 무응답 SYN 관측(13:47:54.388)보다 0.296초 먼저 찍히는 현상이 나타났다.
  - 원리: Boto3 API가 200 OK를 돌려준 것은 AWS 제어 평면(Control Plane)이 규칙 변경을 접수했다는 뜻이지, 실제 EC2 하이퍼바이저 데이터 평면(Data Plane)이 패킷 드롭을 시작한 시점이 아니다.
  - 후속 개선: 제어 평면 성공만으로 안심하는 허위 성공(False Confidence)을 없애기 위해 L4 차단 직후 소켓 타임아웃으로 패킷 드롭을 직접 확인하는 `probe_socket_dropped`와, ALB·WAFv2 WebACL 결합(`modules/alb`) 및 연동 검증을 보완했다.

## 4. 인제스터 탐색 힌트 (Key Modules & Functions)
- **핵심 파일:** `scripts/restore_baseline_sg.py`, `scripts/unblock_waf_ip.py`, `src/remediation/remediation.py`, `infra/terraform/main.tf`, `infra/terraform/modules/alb/main.tf`, `docs/roles/cloud-a/2026-10-08-local-preflight-verification-report.md`, `docs/roles/cloud-a/2026-10-13-p3-2-aws-infrastructure-provisioning-report.md`, `docs/roles/cloud-a/2026-10-14-p3-3b-baseline-sg-ingress-rollback-report.md`
- **주요 클래스/함수:** `restore_baseline_security_group`, `unblock_waf_ip_entry`, `list_blocked_ips`, `probe_socket_dropped`, `restore_ec2_baseline_sg`, `unblock_ip_wafv2`, `verify_waf_traffic_restored`

## 5. 결과 및 회고 (Results & Lessons Learned)
- **성과:** 배포 전 Linux 컨테이너 기반 사전 검증 체계를 정착시켰고, 실인프라에서 5.477초 L4 차단과 1.74초 Baseline SG 복구를 실측으로 확인했다.
- **회고:** 클라우드 API의 성공 응답은 설정 반영 요청이 접수되었다는 의미일 뿐, 네트워크 패킷이 실제로 막혔다는 뜻이 아니다. 탐침 주기(1초)와 분산 호스트 간 시계 오차 한계를 문서화하고, 데이터 평면 확인 절차를 추가해 관측과 보고의 간극을 줄였다.
