---
repo: "https://github.com/mmmphyun/PrfVault"
topic: "Chrome Manifest V3 제약 극복과 DOM 평문 노출 창 최소화"
tags: ["ChromeExtension", "ManifestV3", "V8Engine", "DOMInjection", "PrfVault"]
---

# 프로젝트 제목: PrfVault — Chrome Manifest V3 제약 극복과 DOM 평문 노출 창 최소화

## 1. 프로젝트 시작 배경 및 문제 정의 (Why)
- **Manifest V3의 비영속 백그라운드 제약:** Chrome Manifest V3 정책으로 인해 백그라운드 페이지가 이벤트 기반의 Service Worker로 대체되면서, 백그라운드 프로세스가 언제든 유휴 상태로 종료(Terminate)될 수 있어 메모리 내 암호화 키를 장시간 유지할 수 없었다.
- **자바스크립트 V8 엔진의 문자열 불변성(Immutability) 한계:** 브라우저 DOM 입력 필드(`input[type="password"]`)에 복호화된 평문 비밀번호를 주입하는 순간, 자바스크립트 문자열 불변성으로 인해 평문이 V8 힙에 복사본으로 남아 가비지 컬렉터(GC)가 수거하기 전까지 메모리에 노출되는 구조적 결함이 존재했다.
- **핵심 목표:** Service Worker의 비정형 생명주기를 통제하고, DOM 평문 노출 창(Window of Exposure)을 단 1개 계정의 주입 순간(수 ms)으로 극소화하는 심층 방어(Defense in Depth) 아키텍처를 구현한다.

## 2. 주요 설계 의사결정 및 기술 스택 선정 (Architecture & Trade-offs)
- **온디맨드 단일 계정 복호화 및 즉시 소거 파이프라인 (`extension/src/content/injector.ts`):**
  - 전체 볼트 데이터를 메모리에 복호화하여 올려두는 상용 확장프로그램 방식을 배제하고, Content Script가 로그인 폼 포커스를 감지했을 때 오직 해당 도메인에 바인딩된 단 1개의 자격증명만 요청하는 온디맨드 프로토콜을 설계했다.
  - Rust Wasm에서 평문 도출 -> DOM 값 설정 -> 이벤트 디스패치(`input`, `change`) 완료 직후 스코프를 닫아 평문 참조를 끊고 Wasm 선형 메모리를 즉시 0x00으로 소거했다.
- **비우회 원칙과 1회용 마스킹 클립보드 폴백 (`extension/src/content/index.ts`):**
  - 가상 키패드나 캡차(CAPTCHA), 복사/붙여넣기 방지 등 웹사이트의 보안 솔루션을 억지로 무력화하지 않는 비우회 원칙을 고수했다.
  - 자동 주입이 차단된 비표준 폼 감지 시, 사용자의 명시적 제스처 하에 1회용 마스킹된 클립보드 복사 기능을 제공하고 15초 후 클립보드를 자동 소거하는 안전한 폴백을 구축했다.

## 3. 핵심 기술적 난관 및 트러블슈팅 (Challenges & Breakthroughs)
- **비동기 Service Worker IPC 통신 유실(Dangling Promise) 방어:**
  - Content Script와 Service Worker 간 비동기 메시징 중 백그라운드 워커가 유휴 종료되거나 네이티브 호스트 응답이 지연될 때 메시지 포트가 닫히는 채널 결함을 방어하기 위해, 모든 IPC 라우터(`extension/src/ipc/router.ts`)에 타임아웃 가드와 재시도 큐를 적용했다.
- **다양한 DOM 폼 프레임워크 대응:**
  - React, Vue 등 가상 DOM 기반 프레임워크에서 `HTMLInputElement.value`를 단순 대입할 경우 내부 상태(State)가 갱신되지 않는 문제를 해결하기 위해, 네이티브 프로토타입의 setter(`Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set`)를 직접 호출하고 합성 이벤트를 트리거했다.

## 4. 인제스터 탐색 힌트 (Key Modules & Functions)
- **핵심 파일:** `extension/src/background/service-worker.ts`, `extension/src/content/injector.ts`, `extension/src/content/detector.ts`, `extension/src/ipc/router.ts`
- **주요 함수/클래스:** `CredentialInjector.inject`, `FieldDetector.find_password_fields`, `ServiceWorkerRouter.handle_message`

## 5. 결과 및 회고 (Results & Lessons Learned)
- **성과:** Manifest V3 환경에서 62건의 브라우저 확장 통합 테스트를 통과하며, 평문 비밀번호의 브라우저 힙 메모리 노출 시간을 수백 밀리초 단위로 통제하는 무결성을 실증했다.
- **교훈:** 클라이언트 보안은 결코 완벽한 무결점을 단정할 수 없으며, 플랫폼(V8/DOM)의 본질적인 한계를 투명하게 인정하고 노출 창을 수학적·시간적으로 극소화하는 심층 방어가 현실적인 엔지니어링 해법임을 도출했다.
