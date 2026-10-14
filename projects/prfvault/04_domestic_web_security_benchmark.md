---
repo: "https://github.com/mmmphyun/PrfVault"
topic: "국내 50대 웹사이트 보안 벤치마크 실측과 비표준 보안의 역효과"
tags: ["Playwright", "Benchmark", "ShannonEntropy", "VirtualKeypad", "CredentialStuffing", "PrfVault"]
---

# 프로젝트 제목: PrfVault — 국내 50대 웹사이트 보안 벤치마크 실측과 비표준 보안의 역효과

## 1. 프로젝트 시작 배경 및 문제 정의 (Why)
- **가상 키패드와 암호 길이 제한의 보안 역설:** 국내 금융, 공공, 주요 포털 웹사이트들은 보안 명목으로 가상 키패드와 16자 안팎의 엄격한 비밀번호 길이 상한을 강제하고 있으나, 이것이 패스워드 매니저의 긴 무작위 암호 생성과 자동완성을 방해하는 장애 요인으로 작용하고 있었다.
- **실증 데이터의 부재:** 국내 웹 생태계의 비표준 보안 관행이 초래하는 실제 위험도를 정량화된 수치로 증명한 선행 벤치마크가 부족했다.
- **핵심 목표:** Playwright 기반의 헤드리스 브라우저 자동화 스캐너를 구축하여 국내 50대 주요 웹사이트의 로그인 폼을 전수 진단하고, 섀넌 엔트로피 손실률과 자동완성 차단율을 정량 계측한다.

## 2. 주요 설계 의사결정 및 기술 스택 선정 (Architecture & Trade-offs)
- **Playwright 자동화 벤치마크 파이프라인 (`scripts/benchmark/scanner.ts`):**
  - Chromium 헤드리스 브라우저 인스턴스를 격리 생성하여 국내 50개 웹사이트(`scripts/benchmark/targets.ts`: 금융 15개소, 공공 10개소, 포털/빅테크 10개소, 이커머스 15개소)의 로그인 페이지를 순차 방문했다.
  - DOM 파싱 및 폼 속성 검사를 통해 가상 키패드 로딩 여부, `maxlength` 속성, `autocomplete` 속성, 그리고 패스워드 입력 필드 조작 차단 이벤트를 기계적으로 수집했다.
- **섀넌 정보 엔트로피 및 손실률 산출 알고리즘 (`scripts/benchmark/analyzer.ts`):**
  - NIST SP 800-63B 표준 권고 기준($L=20, N=94$)의 섀넌 엔트로피 131.09 bits 대비, 국내 주요 사이트의 글자 수 제한($L=16$)으로 인해 발생하는 엔트로피 손실률을 수학적으로 모델링했다.

## 3. 핵심 기술적 난관 및 트러블슈팅 (Challenges & Breakthroughs)
- **동적 가상 키패드 렌더링 캡처 및 타이밍 제약:**
  - 단순 정적 HTML 분석으로는 동적으로 삽입되는 보안 솔루션(nProtect, TouchEn nxKey 등)의 가상 키패드와 iframe 기반 인풋 필드를 식별할 수 없었다.
  - MutationObserver와 네트워크 유휴 상태(`networkidle`) 대기 전략을 결합하여 가상 키패드 캔버스 및 DOM 조작 이벤트를 정확하게 포착했다.
- **2026년 9월 신한은행 대출모집인(M신한) 유출 사고와의 대조 분석:**
  - 벤치마크 데이터를 수집하던 중 발생한 2만 5천여 명 규모의 신한은행 크리덴셜 스터핑 사고를 심층 분석했다.
  - 단일 비밀번호 체제와 비표준 입력 제한이 이용자들의 암호 재사용을 조장하고 궁극적으로 대규모 계정 탈취로 이어지는 보안의 역설을 실증 데이터로 뒷받침했다.

## 4. 인제스터 탐색 힌트 (Key Modules & Functions)
- **핵심 파일:** `scripts/benchmark/scanner.ts`, `scripts/benchmark/analyzer.ts`, `scripts/benchmark/targets.ts`, `scripts/results/benchmark-analysis.json`
- **주요 함수:** `scan_target_site`, `calculate_shannon_entropy`, `evaluate_compliance_score`

## 5. 결과 및 회고 (Results & Lessons Learned)
- **성과:**
  - 국내 50대 웹사이트 전수 조사 결과: 16자 길이 제한 사이트의 섀넌 엔트로피 104.87 bits 기록 (표준 대비 **20.0% 엔트로피 손실** 실측).
  - 가상 키패드로 인한 표준 자동 완성 차단율 6.7% 계측.
- **교훈:** 레거시 비표준 보안 도구가 사용자 편의성을 저해할 뿐만 아니라 패스워드 매니저와의 연동을 차단하여 암호 재사용을 유발하는 구조적 역효과를 수치로 증명했다.
