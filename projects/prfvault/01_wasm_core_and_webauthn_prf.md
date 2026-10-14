---
repo: "https://github.com/mmmphyun/PrfVault"
topic: "Zero-Server 패스워드리스 볼트의 출발점과 Rust Wasm 암호 엔진"
tags: ["Rust", "Wasm", "WebAuthn", "Crypto", "ZeroServer", "PrfVault"]
---

# 프로젝트 제목: PrfVault — Zero-Server 패스워드리스 볼트와 Rust Wasm 코어 암호 엔진

## 1. 프로젝트 시작 배경 및 문제 정의 (Why)
- **레거시 웹의 2차 인증 부재와 계정 재사용 취약점:** 대학 포털을 비롯한 국내 다수 레거시 웹 서비스가 여전히 2차 인증(MFA) 없이 단일 비밀번호 체제로 운영되고 있으며, 사용자의 기억 한계로 인해 동일 암호를 반복 재사용하여 크리덴셜 스터핑 공격에 무방비로 노출되고 있었다.
- **중앙화 패스워드 매니저의 단일 장애점(SPOF) 탈피:** 1Password, Bitwarden 등 상용 서비스는 암호화된 볼트를 중앙 클라우드 서버에 보관하므로, 서버 침해 시 전 사용자의 볼트 데이터가 유출될 단일 장애점을 안고 있었다.
- **핵심 목표:** 외부 서버와 데이터베이스를 일체 배제(Zero-Server)하고, 클라이언트 브라우저 환경에서 W3C WebAuthn Level 3 PRF(Pseudo-Random Function) 확장을 활용하여 사용자 하드웨어 바인딩 마스터 시드를 도출하는 패스워드 매니저를 구현한다.

## 2. 주요 설계 의사결정 및 기술 스택 선정 (Architecture & Trade-offs)
- **Rust 기반 Wasm 암호 코어 (`crates/crypto-core/src/lib.rs`):**
  - 자바스크립트 엔진의 런타임 메모리 분석 및 타이밍 공격 위험을 차단하기 위해 순수 Rust로 암호 연산 코어를 작성하고 `wasm-pack`으로 번들링했다.
  - 대칭키 암호화는 고속 하드웨어 가속이 지원되는 표준 `aes-gcm` (AES-256-GCM)을 채택하고, 비밀키 유도에는 `hkdf` (HMAC-SHA256 기반 HKDF-Expand)를 적용했다.
- **선형 메모리 물리 소거 (`zeroize`):**
  - 자바스크립트의 문자열 불변성(Immutability)과 가비지 컬렉터(GC) 지연으로 인한 메모리 잔류 결함을 방어하기 위해, Wasm 내부 선형 메모리에 상주하는 비밀키 및 마스터 시드를 연산 완료 즉시 `Zeroize::zeroize`를 호출하여 0x00으로 강제 물리 소거하도록 설계했다.
- **클라이언트 완결형 볼트 스토리지 (`extension/src/storage/vault-store.ts`):**
  - `chrome.storage.local`에는 오직 AES-256-GCM으로 암호화된 암호문 블록(Ciphertext + Nonce + Tag)만 영속화하며, 어떠한 키도 디스크에 저장하지 않는다.

## 3. 핵심 기술적 난관 및 트러블슈팅 (Challenges & Breakthroughs)
- **자바스크립트와 Wasm 경계 간 메모리 복사 및 잔류 방어:**
  - `Uint8Array` 버퍼가 JS 런타임으로 전달될 때 V8 힙에 복사본이 잔류하는 문제를 최소화하기 위해, 복호화 결과물은 필요한 순간에만 Wasm 내부 메모리에서 직접 역직렬화하고 호출 직후 메모리 핸들을 파괴하는 프로토콜을 수립했다.
- **HKDF 입력 엔트로피 검증 및 에러 핸들링:**
  - 하드웨어로부터 전달되는 PRF 시드의 길이가 32바이트(256비트) 정밀도에 미달하거나 비정상 데이터가 유입될 경우, 침묵 실패(Silent Failure)하지 않고 즉시 Rust 패닉 대신 `Result<T, CryptoError>` 타입으로 명시적 에러를 반환하도록 안전성을 강화했다.

## 4. 인제스터 탐색 힌트 (Key Modules & Functions)
- **핵심 파일:** `crates/crypto-core/src/lib.rs`, `extension/src/crypto/wasm-core.ts`, `extension/src/auth/webauthn-prf.ts`, `extension/src/storage/vault-store.ts`
- **주요 함수/구조체:** `derive_master_key`, `encrypt_vault`, `decrypt_vault`, `WebAuthnPrfClient.get_assertion`, `VaultStore.save_encrypted`

## 5. 결과 및 회고 (Results & Lessons Learned)
- **성과:** W3C 표준 PRF 확장을 통해 사용자 비밀번호 입력 없이 생체 인증 한 번으로 256비트 마스터 키를 도출하고, Wasm 코어 내에서 17건의 단위 테스트를 전수 통과하며 암복호화 무결성을 검증했다.
- **교훈:** 클라이언트 단독 암호학 시스템에서는 알고리즘 자체의 안전성뿐만 아니라 런타임 메모리 상의 잔류 노출 창(Window of Exposure)을 극소화하는 메모리 수명주기 통제가 핵심임을 확인했다.
