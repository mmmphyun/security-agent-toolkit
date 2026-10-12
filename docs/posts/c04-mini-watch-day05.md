---
title: "Next.js App Router 전환과 GitHub Flow 협업 체계 — Client Component 상태 격리와 다중 브랜치 병합"
slug: "c04-mini-watch-day05"
description: "React SPA 구조를 Next.js App Router 기반의 서버·클라이언트 컴포넌트로 분리하고 불변 상태 기반 메모 CRUD 구현과 GitHub Flow 브랜치 협업 및 병합 동기화 체계를 정립한 과정을 다룬다."
pubDate: "2026-10-12"
category: "이상탐지 자동화"
tags:
  - "Next.js"
  - "React"
  - "Git"
  - "GitHub"
  - "AppRouter"
status: "published"
---

## 1. 개요 및 학습 개념 요약

[Day 04 React 컴포넌트 분리와 Vite 프록시 연동](/posts/c04-mini-watch-day04)에서는 단일 Vite 개발 서버와 프록시를 통해 Flask API와 통신하는 단일 페이지 애플리케이션 구조를 구성했다.

이번 5일차 실습에서는 화면 인터페이스를 Next.js App Router 환경으로 전환하여 파일 시스템 기반 라우팅과 컴포넌트 렌더링 경계를 분리했다.

> 인터랙션이 요구되는 영역만 클라이언트 컴포넌트로 격리하고 협업 시에는 작업 브랜치와 풀 리퀘스트를 통해 메인 스트림의 무결성을 보장한다.

공통 네비게이션 셸과 경로 세그먼트를 분리하고 브라우저 상태 조작이 필요한 영역에 한해 `"use client"` 지시어를 선언했다. 메모 관리 컴포넌트에서는 배열 불변성을 유지하는 상태 연산으로 등록, 수정, 삭제, 유효성 검증을 구현했다.

후반부 실습에서는 독립된 두 로컬 작업 환경에서 동일 원격 저장소를 대상으로 작업 브랜치를 분기했다. 풀 리퀘스트 생성과 머지 커밋 병합, 최신 기준점 동기화로 이어지는 GitHub Flow 협업 파이프라인을 정립했다.

## 2. 전체 산출물 구조 및 진단/파이프라인 체계

Next.js App Router 화면 계층과 GitHub Flow 기반 협업 파이프라인의 구성 요소 및 입출력 데이터를 다음 표로 정리했다.

| 계층 및 단계 | 파일 및 대상 경로 | 핵심 역할 | 입출력 및 처리 데이터 |
| :--- | :--- | :--- | :--- |
| 공통 셸 레이아웃 | `app/layout.js` | 전역 네비게이션 헤더 및 공통 HTML 셸 정의 | Link 컴포넌트 기반 클라이언트 라우팅 전환 |
| 홈 라우트 세그먼트 | `app/page.js` | 대시보드 진입점 및 카운터 컴포넌트 배치 | 서버 컴포넌트 정적 렌더링 |
| 메모 라우트 세그먼트 | `app/notes/page.js` | 메모 관리 전용 라우트 세그먼트 구성 | Notes 컴포넌트 래핑 및 라우트 메타데이터 |
| 클라이언트 상태 관리 | `components/Notes.js` | 불변 배열 상태 기반 메모 CRUD 인터랙션 | useState 훅, 이벤트 객체, Date.now 식별자 |
| 기능 분기 및 변경 격리 | `feature/minsu`, `feature/jiyun` | 작업자별 독립 브랜치 분기 및 로컬 커밋 | minsu.md, jiyun.md 파일 격리 수정 |
| 원격 검토 및 통합 | GitHub PR #1, #2, #3 | 코드 리뷰 기반 머지 커밋 생성 및 main 병합 | 브랜치 diff 비교, 승인 후 Merge commit 생성 |
| 로컬 기준점 동기화 | 로컬 main 브랜치 | 원격 변경 사항의 무충돌 고속 전진 병합 | git pull origin main (Fast-forward 동기화) |

## 3. 기존 체계의 한계와 도전 과제: 브라우저 메모리의 휘발성과 단일 브랜치 동시 수정의 충돌 위험

단일 페이지 애플리케이션 환경에서는 라우팅 상태와 뷰 컴포넌트가 브라우저 런타임에 결합되어 페이지 이동 시 레이아웃 상태를 유지하기 어렵고 코드 규모가 확장될수록 라우트 세그먼트 관리가 복잡해진다.

동시에 브라우저 힙 메모리의 useState에만 의존하는 메모 데이터는 새로고침 이벤트 발생 시 모든 상태가 초기화된다. 이는 [Day 02 보안 감사 이벤트 스키마와 데이터베이스 영속 적재 파이프라인](/posts/c04-mini-watch-day02)에서 다룬 관계형 데이터베이스와 달리 영속성을 제공하지 못하는 구조적 한계를 갖는다.

협업 관점에서는 모든 작업자가 단일 main 브랜치에 직접 커밋하고 푸시할 경우 원격 저장소 이력과 로컬 작업 간 충돌이 빈번하게 일어난다. 코드 리뷰 없이 메인 스트림에 변경 사항이 유입되어 결함 추적과 롤백이 어려워지는 문제가 발생한다.

## 4. 엔지니어링 의사결정 및 리팩터링

### 4.1. App Router 파일 시스템 라우팅과 "use client" 경계 분리

Next.js의 App Router는 파일 시스템 디렉터리 구조를 기준으로 URL 라우트 세그먼트를 자동 구성한다.

`app/layout.js`에 공통 네비게이션 헤더를 배치하여 하위 페이지 전환 시에도 레이아웃 상태를 보존하고 전체 DOM 재구축 비용을 제거했다.

```javascript
// mini-watch/day05/app/layout.js: 공통 네비게이션 셸 및 하위 세그먼트 래핑
import Link from "next/link";
import "./globals.css";

export const metadata = {
  title: "Next.js 메모 앱",
  description: "Next.js App Router 기반 메모 및 카운터 애플리케이션",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body>
        <header>
          <nav>
            <Link href="/">홈</Link>
            <Link href="/notes">메모</Link>
          </nav>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
```

Next.js App Router의 컴포넌트는 기본적으로 서버 컴포넌트로 실행된다.

브라우저 이벤트 리스너와 useState 같은 훅을 실행해야 하는 컴포넌트는 파일 최상단에 `"use client"` 지시어를 선언하여 클라이언트 렌더링 영역으로 분리했다.

### 4.2. 불변 배열 연산 기반의 메모 CRUD 상태 관리와 예외 방어

`components/Notes.js`에서는 등록, 수정, 삭제 인터랙션을 구현하면서 리액트의 상태 불변성을 유지했다.

입력값 검증에서는 공백 문자열 등록을 방지하기 위해 `trim()` 메서드로 공백을 정제하고 빈 값 입력 시 경고 메시지를 표시한 뒤 실행을 중단했다.

```javascript
// mini-watch/day05/components/Notes.js: 등록 및 수정 분기 처리 로직
const handleSubmit = (e) => {
  e.preventDefault();
  const trimmed = inputText.trim();

  if (!trimmed) {
    setErrorMessage("메모 내용을 1자 이상 입력해주세요 (공백 불가).");
    return;
  }
  setErrorMessage("");

  if (editingId !== null) {
    setNotes((prev) =>
      prev.map((item) => (item.id === editingId ? { ...item, text: trimmed } : item))
    );
    setEditingId(null);
    setInputText("");
  } else {
    const newNote = { id: Date.now(), text: trimmed };
    setNotes((prev) => [...prev, newNote]);
    setInputText("");
  }
};
```

수정 시에는 `editingId` 상태를 식별자로 삼아 `map` 메서드로 대상 객체만 복사 갱신했다.

삭제 처리 시에는 `filter` 메서드를 사용해 대상 식별자를 제외한 새 배열을 반환하도록 구성했다. 현재 수정 중인 메모가 삭제될 경우 폼 상태를 즉시 초기화하여 유효하지 않은 식별자 참조를 차단했다.

```javascript
// mini-watch/day05/components/Notes.js: 메모 삭제 및 수정 폼 초기화 연계
const handleDelete = (id) => {
  const confirmed = window.confirm("해당 메모를 삭제하시겠습니까?");
  if (!confirmed) {
    return;
  }
  setNotes((prev) => prev.filter((item) => item.id !== id));
  if (editingId === id) {
    setEditingId(null);
    setInputText("");
    setErrorMessage("");
  }
};
```

### 4.3. 격리된 작업 브랜치 분기와 GitHub PR 기반의 코드 리뷰 루프

원격 저장소의 `main` 브랜치를 직접 수정하지 않고 `git checkout -b` 명령으로 기능별 독립 브랜치를 생성했다.

작업자별로 `minsu.md`와 `jiyun.md` 파일을 작성하고 커밋한 뒤 원격 브랜치로 푸시했다. GitHub CLI 명령을 통해 풀 리퀘스트를 생성하여 변경 사항에 대한 검토를 요청했다.

```text
# 기능 브랜치 생성, 커밋 및 원격 푸시
PS C:\work\git-practice-minsu> git checkout -b feature/minsu
PS C:\work\git-practice-minsu> git add minsu.md
PS C:\work\git-practice-minsu> git commit -m "feat: 민수 작업 일지 추가"
PS C:\work\git-practice-minsu> git push -u origin feature/minsu

# GitHub CLI를 통한 풀 리퀘스트 생성
PS C:\work> gh pr create --repo mmmphyun/git-collaboration-practice --base main --head feature/minsu --title "feat: 민수 작업 일지 추가"
```

풀 리퀘스트 제출 후 추가된 요구사항은 별도 PR을 만들지 않고 동일 브랜치에 보완 커밋을 푸시하여 기존 PR에 자동 반영되도록 구성했다.

코드 리뷰 완료 후 머지 커밋 방식으로 병합을 수행하여 각 기능 브랜치의 이력과 통합 시점을 보존했다.

### 4.4. Fast-Forward Pull 동기화와 역할 잠금 기반 충돌 방지 거버넌스

원격 저장소에서 풀 리퀘스트가 병합된 이후에는 로컬 `main` 브랜치로 전환하여 최신 이력을 동기화했다.

원격 `main`의 변경 사항이 로컬 `main`의 선형적 연장선상에 위치하여 고속 전진 방식으로 충돌 없이 병합을 완료했다.

```text
# 원격 main 변경 사항의 로컬 동기화 및 완료 브랜치 삭제
PS C:\work\git-practice-minsu> git checkout main
PS C:\work\git-practice-minsu> git pull origin main
Updating 186a151..fa058bb
Fast-forward
 jiyun.md | 3 +++
 minsu.md | 5 +++++
 2 files changed, 8 insertions(+)
 create mode 100644 jiyun.md
 create mode 100644 minsu.md

PS C:\work\git-practice-minsu> git branch -d feature/minsu
Deleted branch feature/minsu (was b069d20).
```

동일 파일 동시 수정으로 인한 병합 충돌을 원천 차단하기 위해 작업 영역을 물리적으로 격리하는 역할 잠금 거버넌스를 도출했다.

실제 CloudShield 팀 프로젝트([aleph-project](https://github.com/mmmphyun/aleph-project)) 협업 경험을 바탕으로, 단일 소유권 매트릭스를 적용해 경계선 파일의 수정 권한을 분리하고 열린 PR이 존재하는 동안 신규 작업을 제한하는 1인 1작업 WIP 원칙을 수립했다.

## 5. 검증 및 회고

### 5.1. 프로덕션 빌드와 다중 브랜치 병합 이력 검증

`npm run build` 명령을 실행하여 Next.js 애플리케이션의 프로덕션 정적 최적화 빌드를 수행했다.

루트 경로(`/`)와 메모 관리 경로(`/notes`)가 정적 페이지로 생성되었으며 `npm run start`를 통해 빌드 아티팩트의 정상 동작을 확인했다.

로컬 저장소에서 `git log --oneline --graph` 명령을 실행하여 다중 브랜치 병합 이력을 검증했다.

```text
PS C:\work\git-practice-minsu> git log --oneline --graph -n 10
*   10c2754 Merge pull request #3 from feature/checklist
|\  
| * 72bbc6c feat: 협업 점검표 checklist.md 추가
|/  
*   fa058bb Merge pull request #2 from feature/jiyun
|\  
| * 5abbee5 feat: 지윤 작업 일지 추가
* |   a89444e Merge pull request #1 from feature/minsu
|\ \  
| |/  
|/|   
| * b069d20 docs: 민수 작업 일지 상세 보완
| * 5066a81 feat: 민수 작업 일지 추가
|/  
* 186a151 docs: 초기 README 생성
```

PR #1, PR #2, PR #3이 순차적으로 머지 커밋을 형성하며 `main` 브랜치에 통합된 그래프 구조를 확인했다.

### 5.2. 현실적 회고 및 교훈

브라우저 메모리 기반의 상태 관리는 단일 세션 내에서 빠른 반응성을 제공하지만 새로고침 시 데이터가 휘발되는 구조적 한계를 보였다.

실제 관제 시스템이나 서비스 환경에서는 클라이언트 상태에 머무르지 않고 백엔드 API와 영속 데이터베이스로 데이터를 보존해야 함을 실증했다.

협업 파이프라인에서는 격리된 작업 브랜치와 풀 리퀘스트 검토 단계를 거침으로써 메인 스트림의 무결성을 안정적으로 유지할 수 있었다.

단순한 Git 명령어 조작을 넘어 디렉터리 수준의 역할 격리와 단일 작업 WIP 제한 거버넌스를 병행할 때 다중 작업자 환경의 충돌을 원천 차단할 수 있다는 기술적 결론을 도출했다.
