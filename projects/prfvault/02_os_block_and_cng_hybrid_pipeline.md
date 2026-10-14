---
repo: "https://github.com/mmmphyun/PrfVault"
topic: "운영체제 PRF 차단 실증과 Windows CNG TPM 2.0 Native Host 하이브리드 폴백"
tags: ["WindowsCNG", "TPM2", "NativeMessaging", "Rust", "FFI", "PrfVault"]
---

# 프로젝트 제목: PrfVault — 운영체제 PRF 차단 실증과 Windows CNG TPM 2.0 Native Host 하이브리드 폴백

## 1. 프로젝트 시작 배경 및 문제 정의 (Why)
- **표준의 배신: 브라우저와 운영체제 계층의 불일치:** W3C WebAuthn Level 3 명세상 브라우저가 PRF 확장을 지원함에도 불구하고, 실제 Windows 11 환경에서 내장 TPM 2.0 인증자를 호출할 때 운영체제(`webauthn.dll`)가 PRF 확장을 명시적으로 거부(`{"prf": {"enabled": false}}`)하는 현상이 실측되었다.
- **글로벌 생태계 한계와 서비스 마비:** 이는 Bitwarden Issue #19858에서도 확인된 플랫폼 레벨의 구조적 결함으로, Windows Hello 내장 TPM 인증자 환경에서는 웹 표준 PRF 단독 구현만으로는 사용자 키 유도가 원천 불가능했다.
- **핵심 목표:** 웹 표준 호출 실패 시 즉시 Chrome Native Messaging Host로 무중단 전환되어 운영체제 내장 TPM 2.0 하드웨어 엔클레이브에서 대칭키를 직접 파생하는 자동 폴백 파이프라인을 구축한다.

## 2. 주요 설계 의사결정 및 기술 스택 선정 (Architecture & Trade-offs)
- **표준 우선주의 하이브리드 파이프라인 (`extension/src/background/service-worker.ts`):**
  - 운영체제 차단이 확인되었다고 해서 웹 표준을 포기하지 않고, 1차로 W3C WebAuthn PRF를 호출한 뒤 거부 감지 시 2차로 Chrome Native Messaging Host로 자동 전환되는 페일오버 구조를 채택했다.
- **순수 C-FFI 시스템 바인딩 (`crates/native-host/src/windows_hello.rs`):**
  - 외부 비공식 암호화 라이브러리에 의존하지 않고, Rust `windows-sys`를 활용해 Windows CNG 시스템 라이브러리(`ncrypt.dll`)를 직접 바인딩했다.
  - `NCryptOpenStorageProvider`, `NCryptOpenKey`, `NCryptSecretAgreement`, `NCryptDeriveKey` API를 통해 Windows Hello 생체 인증 프롬프트를 트리거하고 TPM 2.0 엔클레이브 내부에서 256비트 대칭키를 유도했다.
- **Chrome Native Messaging 프로토콜 구현 (`crates/native-host/src/protocol.rs`):**
  - 표준 입출력(stdin/stdout) 기반의 4바이트 리틀 엔디안(Little-Endian) 길이 프리픽스 바이너리 패킷 규약을 Rust 표준 라이브러리로 직접 파싱 및 직렬화했다.

## 3. 핵심 기술적 난관 및 트러블슈팅 (Challenges & Breakthroughs)
- **Windows CNG API 권한 및 메모리 누수 방어:**
  - `NCRYPT_PROV_HANDLE` 및 `NCRYPT_KEY_HANDLE` 등 네이티브 핸들이 비정상 종료 시 시스템에 잔류하지 않도록 RAII 패턴의 커스텀 래퍼를 구현하여 `NCryptFreeObject`가 기계적으로 호출되도록 강제했다.
- **IPC 데이터 무결성과 리틀 엔디안 버퍼 경계:**
  - Chrome Native Messaging 호스트 통신 중 버퍼 오버플로우나 부분 읽기(Partial Read)가 발생하지 않도록 4바이트 프리픽스를 엄격히 검증하고, 최대 메시지 크기(1MB) 초과 시 즉시 프로토콜 에러를 반환하는 경계 가드를 수립했다.

## 4. 인제스터 탐색 힌트 (Key Modules & Functions)
- **핵심 파일:** `crates/native-host/src/windows_hello.rs`, `crates/native-host/src/protocol.rs`, `crates/native-host/src/main.rs`, `extension/src/background/native-ipc.ts`
- **주요 함수/구조체:** `WindowsHelloProvider::derive_key`, `read_message`, `write_message`, `NativeIpcClient.send_request`

## 5. 결과 및 회고 (Results & Lessons Learned)
- **성과:** W3C PRF가 거부되는 Windows 11 환경에서도 Windows Hello 생체 인증과 연동된 TPM 2.0 엔클레이브를 통해 100% 무결한 256비트 하드웨어 키 파생 파이프라인을 실증했다.
- **교훈:** 표준 명세서상 완전해 보이는 웹 기술이라도 하위 운영체제 권한 계층(Privilege Hierarchy)의 지원 범위에 종속되며, 실전 엔지니어링에서는 네이티브 폴백을 설계할 수 있는 시스템 저수준 이해도가 필수적임을 도출했다.
