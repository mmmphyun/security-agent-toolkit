---
repo: "https://github.com/mmmphyun/aleph-project"
topic: "Grafana 코드형 무상태 프로비저닝, S3 침해 보고서 자동 렌더링, 그리고 L4/L7 통합 복구"
tags: ["Grafana", "S3", "HTMLReport", "Rollback", "Observability", "CloudShield"]
---

# 프로젝트 제목: CloudShield — Grafana 코드형 관제, S3 보고서 자동 렌더링 및 L4/L7 통합 복구

## 1. 프로젝트 시작 배경 및 문제 정의 (Why)
- **역할 경계와 구현 범위:** Grafana 대시보드의 4사분면 CloudWatch Logs Insights 쿼리 패널과 3차 복구 Slack 카드 포맷은 클라우드 B가 구현했다. 클라우드 A는 Grafana 컨테이너·데이터소스·IAM 기반 프로비저닝, S3 공문서 HTML 보고서 렌더러·버킷 인프라(`src/remediation/report_renderer.py`, `infra/terraform/modules/s3`), L4+L7 통합 롤백 엔진(`apply_rollback`), 그리고 Lambda 루트 로거 보정을 담당했다.
- **수동 관제 설정의 재현 불가 문제:** Grafana 웹 UI에서 데이터소스와 대시보드를 손으로 클릭해 등록하면 컨테이너를 내렸다 올릴 때마다 설정이 초기화되거나 팀원 환경마다 UID가 달라진다.
- **Slack 요약 카드의 감사 증적 한계와 복구 수작업:** 침해 대응 결과를 Slack 메시지로만 남기면 인쇄나 외부 공유용 정형 보고서로 쓰기 어렵고, 실증 테스트 뒤 L4 보안 그룹과 L7 WAF 차단을 매번 따로 풀어야 하는 불편함이 있었다.

## 2. 주요 설계 의사결정 및 기술 스택 선정 (Architecture & Trade-offs)
- **Grafana as Code 무상태 프로비저닝 (`infra/grafana/`):**
  - `docker-compose.yml`, `cloudwatch.yaml`, `dashboards.yaml`을 코드로 관리해 `docker compose up -d` 한 번으로 동일한 관제 환경이 뜨도록 구성했다.
  - 데이터소스 UID를 `cloudshield-cloudwatch`로 고정해 클라우드 B의 대시보드 JSON이 어느 환경에서나 깨지지 않게 맞췄고, 기본 비밀번호 제거 및 `127.0.0.1:3000` 로컬 바인딩을 적용했다.
  - Terraform에 `CloudShield-Grafana-CloudWatch-ReadOnly` 정책을 분리해 Grafana 계정이 로그·메트릭 조회(`logs:FilterLogEvents`, `logs:StartQuery`, `cloudwatch:GetMetricData`) 외에 EC2나 WAF를 수정하지 못하게 막았다.
- **S3 공문서 HTML 보고서 렌더러 (`src/remediation/report_renderer.py`, `infra/terraform/modules/s3/main.tf`):**
  - 외부 CDN이나 웹 폰트에 의존하지 않는 순수 인라인 CSS와 `@media print` A4 규격 HTML로 생성해 오프라인·폐쇄 환경에서도 브라우저 인쇄(PDF 저장) 시 표가 깨지지 않게 만들었다.
  - 로컬 디스크 임시 파일 없이 바이트 스트림(`put_object`)으로 S3에 올린 뒤 1시간(3600초) 만료 Presigned URL을 발급하고, 버킷 정책으로 사내 인가 공인 IP 접근만 허용하도록 인프라를 구성했다.
- **L4+L7 통합 복구 엔진 (`apply_rollback`):**
  - `restore_ec2_baseline_sg`와 `unblock_ip_wafv2`·`verify_waf_traffic_restored`를 하나의 복구 파이프라인으로 묶어 시연 후 단일 실행으로 두 계층을 함께 원복하도록 구현했다.

## 3. 핵심 기술적 난관 및 트러블슈팅 (Challenges & Breakthroughs)
- **공격 로그 HTML 삽입 시 XSS 방어와 S3 타임아웃 통제:**
  - 원문 로그나 공격 URI 안에는 `<script>` 같은 악성 HTML 문자열이 그대로 들어올 수 있다. `render_executive_html_report`의 모든 입력·로그 필드에 `html.escape()`를 전수 적용해 보고서 열람 시 스크립트 실행을 차단했다.
  - 2차 분석 Lambda의 전체 제한 시간이 30초이므로, S3 클라이언트 연결 타임아웃을 2초(`S3_CONNECT_TIMEOUT_SECONDS`), 읽기 타임아웃을 5초(`S3_READ_TIMEOUT_SECONDS`)로 묶어 S3 지연이 워커 전체를 멈추지 않게 했다.
- **AWS Lambda 기본 루트 로거가 INFO 상태 로그를 삼키던 문제 (PR #237):**
  - 현상: `llm_worker.py`의 `_log_analysis_status`가 `logger.info(...)`로 Bedrock 성공/Fallback 전환 상태를 남기도록 연결했지만, 실제 AWS CloudWatch Logs에 INFO 로그가 찍히지 않아 Grafana 3사분면 집계 패널이 비어 있었다.
  - 원리: AWS Lambda Python 런타임은 핸들러 코드 실행 전 루트 로거를 자체 핸들러와 함께 `WARNING` 레벨로 미리 초기화한다. 따라서 모듈에서 단순히 `logging.basicConfig(level=INFO)`를 호출해도 이미 핸들러가 붙어 있으면 무시된다.
  - 해결: `orchestrator.py`와 `llm_worker.py` 진입부에서 `LOG_LEVEL` 환경변수를 읽어 루트 로거 레벨을 명시적으로 동기화해 INFO 관제 로그가 정상 방출되도록 수정했다.

## 4. 인제스터 탐색 힌트 (Key Modules & Functions)
- **핵심 파일:** `infra/grafana/docker-compose.yml`, `infra/grafana/provisioning/datasources/cloudwatch.yaml`, `infra/grafana/provisioning/dashboards/dashboards.yaml`, `infra/terraform/modules/s3/main.tf`, `src/remediation/report_renderer.py`, `src/remediation/remediation.py`, `src/remediation/llm_worker.py`, `docs/roles/cloud-a/2026-10-28-p5-1-pipeline-deploy-and-grafana-provisioning.md`
- **주요 클래스/함수:** `render_executive_html_report`, `upload_report_and_generate_presigned_url`, `apply_rollback`, `restore_ec2_baseline_sg`, `unblock_ip_wafv2`, `execute_bedrock_analysis`

## 5. 결과 및 회고 (Results & Lessons Learned)
- **성과:** Grafana 코드형 무상태 기동, ReadOnly IAM 격리, S3 A4 공문서 HTML 자동 발급, L4+L7 통합 원복, 그리고 CloudWatch INFO 로그 방출 보정까지 연결해 관제와 사후 보고·복구 흐름을 마쳤다.
- **회고:** 로컬 Pytest 환경에서는 잘 나오던 INFO 로그가 실제 Lambda 런타임에서 사라지는 것처럼, 클라우드 관리형 런타임이 선점하는 초기화 동작은 실제 배포 환경 로그를 끝까지 확인해야만 잡을 수 있다.
