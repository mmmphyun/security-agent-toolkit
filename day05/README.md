# Next.js 메모 앱 (`next-practice`)

Next.js App Router와 React Client Component 기반의 메모 관리 애플리케이션입니다.

---

## 1. 실행 방법

### 사전 요구사항
- Node.js (v18 이상 권장)
- npm

### 설치 및 실행 순서
```bash
# 1. 프로젝트 디렉터리 이동
cd c:/work/mini-watch-standalone/day05/next-practice

# 2. 의존성 설치 (필요시)
npm install

# 3. 개발 서버 실행
npm run dev

# 4. 프로덕션 빌드 및 실행 검증
npm run build
npm run start
```
- 브라우저 접속: `http://localhost:3000`

---

## 2. 화면 및 컴포넌트 구조

- [app/layout.js](file:///c:/work/mini-watch-standalone/day05/next-practice/app/layout.js): 전역 네비게이션 헤더 및 공통 쉘 레이아웃 (홈과 메모 페이지 간 Next.js `Link` 이동 제공)
- [app/page.js](file:///c:/work/mini-watch-standalone/day05/next-practice/app/page.js): 홈 대시보드 화면 및 Counter 컴포넌트 마운트
- [components/Counter.js](file:///c:/work/mini-watch-standalone/day05/next-practice/components/Counter.js): `useState` 기반 숫자 증가 및 초기화 Client Component
- [app/notes/page.js](file:///c:/work/mini-watch-standalone/day05/next-practice/app/notes/page.js): 메모 메인 화면 및 Notes 컴포넌트 연결
- [components/Notes.js](file:///c:/work/mini-watch-standalone/day05/next-practice/components/Notes.js): 메모 CRUD(등록, 수정, 취소, 삭제 confirm), 유효성 검증, 빈 목록 UI 처리 Client Component

---

## 3. 핵심 개념 정리

### 1) Next.js와 React의 관계, `page.js`와 `layout.js`의 역할
- **Next.js와 React**: React는 UI 뷰를 구성하는 클라이언트 사이드 라이브러리인 반면, Next.js는 React를 기반으로 파일 시스템 기반 라우팅, 서버 컴포넌트(RSC), 번들링 최적화(Turbopack) 등을 제공하는 풀스택 프레임워크입니다.
- **`layout.js`**: 여러 페이지 간에 공유되는 공통 레이아웃을 정의합니다. 라우트 이동 시 상태를 유지하며 불필요한 전체 리렌더링을 방지합니다.
- **`page.js`**: 특정 URL 경로(Route Segment)에 대응하는 고유한 UI 화면을 정의합니다.

### 2) `"use client"` 지시어를 붙인 컴포넌트와 그 이유
- **적용 대상**: `components/Counter.js`, `components/Notes.js`
- **이유**: Next.js App Router의 컴포넌트는 기본적으로 서버에서 렌더링되는 Server Component입니다. 버튼 클릭 이벤트(`onClick`), 입력값 바인딩(`onChange`), 동적 상태 추적(`useState`)과 같은 브라우저 런타임 인터랙션 및 리액트 훅을 실행하기 위해서는 명시적으로 `"use client"`를 선언하여 클라이언트 컴포넌트로 분리해야 합니다.

### 3) 새로고침 시 메모가 초기 상태로 돌아오는 이유와 DB 저장의 차이
- **브라우저 메모리(State) 기반 동작**: 본 앱의 메모 데이터는 브라우저 프로세스의 힙 메모리(React State)에만 존재합니다. 따라서 새로고침(F5)을 실행하면 브라우저 컨텍스트가 재초기화되어 코드에 선언된 `INITIAL_NOTES`로 되돌아갑니다.
- **데이터베이스(DB) 영속 저장과의 차이**: PostgreSQL/MySQL 등의 영속 저장소(RDBMS)나 백엔드 API 서버를 연결하면 데이터가 디스크 저장소에 커밋되어 트랜잭션 단위로 보존됩니다. 따라서 서버가 재시작되거나 클라이언트 브라우저를 새로고침하더라도 영속적으로 데이터가 유지됩니다.

---

## 4. 동작 확인 검증 결과

1. **카운터 동작**: 홈 화면에서 '증가' 버튼 클릭 시 숫자 증가, '초기화' 버튼 클릭 시 0으로 초기화 확인.
2. **화면 이동**: 상단 네비게이션의 `Link`를 통해 새로고침 없이 홈(`http://localhost:3000/`)과 메모(`http://localhost:3000/notes`) 간 부드러운 전환 확인.
3. **메모 등록 및 고유 ID 식별**: 동일한 내용의 메모 2개를 연속 등록해도 `Date.now()` 기반 고유 ID가 부여되어 각각 독립된 항목으로 렌더링 및 개별 조작 가능.
4. **수정 및 취소**: 특정 메모 '수정' 클릭 시 폼에 기존 텍스트 로드. '수정 취소' 시 원본 텍스트 보존. 내용 수정 후 '수정 저장' 시 해당 ID 메모만 변경.
5. **입력 유효성 검증**: 빈 값 또는 공백 문자열 입력 시 등록/수정을 차단하고 경고 문구 표시.
6. **삭제 처리**: `window.confirm` 확인 시에만 해당 메모 삭제. 수정 진행 중인 메모를 삭제할 경우 입력 폼이 즉시 초기화.
7. **빈 목록 안내**: 모든 메모를 삭제하면 "등록된 메모가 없습니다" 안내 카드 표시.
8. **프로덕션 빌드**: `npm run build` 성공 및 정적 라우트 (`/`, `/notes`) 최적화 생성 확인.
