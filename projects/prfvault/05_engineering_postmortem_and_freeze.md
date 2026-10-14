---
repo: "https://github.com/mmmphyun/PrfVault"
topic: "보안 수준과 사용성의 트레이드오프와 연구 프로젝트 동결 회고"
tags: ["Postmortem", "ZeroServer", "NativeHost", "SecurityEngineering", "RepositoryFreeze", "PrfVault"]
---

# 프로젝트 제목: PrfVault — 보안 수준과 사용성의 트레이드오프와 연구 프로젝트 동결 회고

## 1. 프로젝트 시작 배경 및 문제 정의 (Why)
- **크롬 웹스토어 무설치 배포 목표의 좌절:** 당초 일반 사용자가 클릭 한 번으로 설치해 즉시 쓸 수 있는 무설치 크롬 확장프로그램으로 상용화하려 했으나, OS 계층(`webauthn.dll`)의 W3C PRF 차단으로 인해 네이티브 호스트 실행 파일(`native-host.exe`)과 윈도우 레지스트리 수동 등록이 강제되는 심각한 설치 장벽에 부딪혔다.
- **보안 철학과 사용성 간의 근본적 모순:**
  - Zero-Server 원칙(외부 서버 배제, TPM 2.0 하드웨어 바인딩)을 완벽히 지키려면 일반 사용자가 감당하기 어려운 네이티브 호스트 수동 설치를 요구해야 했다.
  - 반대로 일반 상용 서비스 수준의 무설치 편의성을 얻으려면 중앙 클라우드 서버에 암호화된 볼트를 올리거나 마스터 비밀번호 방식으로 후퇴하는 '보안적 타협'을 해야만 했다.
- **핵심 목표:** 타협을 통해 미완성 상용 서비스를 내놓기보다, 플랫폼 한계와 기술적 실측 데이터를 온전히 보존하는 학술적 연구 프로젝트로 전환하고 저장소를 공식 동결(Freeze)한다.

## 2. 주요 설계 의사결정 및 기술 스택 선정 (Architecture & Trade-offs)
- **원칙 고수: Zero-Server 아키텍처 타협 거부:**
  - 중앙 클라우드 DB 연동이나 이메일 기반 인증 등 편의성을 위한 보안 후퇴를 일체 거부하고, 하드웨어 바인딩 로컬 완결성을 프로젝트의 불변 계약으로 유지했다.
- **전수 검증 하네스 파이프라인 완결 (`scripts/test-native-host.ps1`, `cargo test`, `npm test`):**
  - 동결 전 모든 계층(Rust Wasm 17건, 브라우저 확장 62건, 네이티브 호스트 통신 3건)의 테스트 슈트를 전수 Green 상태로 정합성을 맞추고, 재현 가능한 빌드 스크립트를 완비했다.
- **공식 동결(Freeze) 선언과 라이선스 명시:**
  - 2026년 10월 6일부로 추가 기능 개발을 중단하고 보안 취약점 패치 외의 코드 수정을 영구 동결하여 연구 실증 아티팩트로 전환했다.

## 3. 핵심 기술적 난관 및 트러블슈팅 (Challenges & Breakthroughs)
- **소프트웨어 공급망과 네이티브 권한 관리의 딜레마:**
  - 네이티브 호스트 배포 시 코드 서명 인증서(Code Signing Certificate) 비용 및 윈도우 SmartScreen 경고 등 오픈소스/주니어 개발자가 현실적으로 마주하는 플랫폼 진입 장벽을 명확히 규명했다.
- **플랫폼 권한 계층(Privilege Hierarchy)의 교훈:**
  - W3C 웹 표준 명세서상 아무리 완벽한 암호학 프로토콜이라도, 하위 OS 벤더(Microsoft)와 하드웨어 드라이버 제조사(Intel)가 개방하지 않은 권한은 클라이언트 애플리케이션 계층에서 결코 온전히 통제할 수 없음을 실기 검증으로 입증했다.

## 4. 인제스터 탐색 힌트 (Key Modules & Functions)
- **핵심 파일:** `README.md`, `scripts/install-native-host.ps1`, `crates/native-host/Cargo.toml`, `extension/manifest.json`
- **주요 섹션/스크립트:** `Repository Freeze Notification`, `install-native-host.ps1`, `Windows Hello NCrypt 바인딩`

## 5. 결과 및 회고 (Results & Lessons Learned)
- **성과:**
  - 실사용 서비스 배포는 좌절되었으나, W3C WebAuthn PRF의 OS 레벨 차단 실증, Windows Hello TPM 2.0 Native Host 하이브리드 파이프라인 완결, 국내 50대 웹사이트 정량 벤치마크라는 3대 연구 목표를 100% 달성하고 동결했다.
- **교훈:**
  - 보안 엔지니어링은 단지 수학 공식을 코드로 옮기는 작업이 아니라, 플랫폼 파편화와 레거시 환경의 제약 조건을 객관적으로 계측하고 실현 가능한 대안을 모색하는 시스템 공학의 영역임을 실증했다.
