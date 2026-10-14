# 4-5과목: 미니 프로젝트

이 디렉토리는 SKT ALEPH 4과목과 5과목을 하나의 미니 프로젝트로 만들어 소스코드와 리팩터링 결과물, 보고서 등을 통합 관리하는 공간입니다.

---

## 1. 디렉토리 구조 및 과목 매핑 표준

각 일차별 실습은 `dayXX` 형태의 디렉토리 내에 존재하며, 4과목과 5과목이 연속된 일차로 통합 관리됩니다.

- **4과목 (서비스 구축과 보안 로그 수집, `c04-mini-watch-day01` - `day05`):**
  - `day01`: 일반 서비스·감시 서비스 시작 및 아키텍처 기초
  - `day02`: 로컬 PostgreSQL 기록 저장 및 조회 API
  - `day03`: HTML·JavaScript 실제 기록 조회 화면
  - `day04`: React 로그인·세션과 감시 대시보드 CRUD
  - `day05`: Next.js App Router 연결 및 GitHub Flow 협업
- **5과목 (이상 탐지·대응 자동화 SOAR, `c05-mini-watch-day06` 이후):**
  - `day06`: 5과목 Day 1 Docker 서비스 실행과 연결 (2-Compose 스택 분리 및 외부 공유망)
  - `day07`: 5과목 Day 2 Render·Supabase·Sentry 외부 배포 및 오류 확인
  - `day08`: 5과목 Day 3 서로 다른 로그 정규화 및 SIEM 통합 조회

하위 산출물은 강의 노션 페이지를 참고하여 확인합니다.

---

## 2. 파일 명명 및 주석 작성 규칙

1. **역할 기반 파일 명명:**
   - 각 일차의 교시별 노션 페이지에 명시된 파일명을 사용합니다.
2. **주석 기반 문제의식 기록:**
   - 강의 예시 대비 리팩터링한 이유, 엣지 케이스 고려 사항, Zero Trust 보안 원칙에 따른 의사결정 근거를 Q&A 주석 블록으로 상세히 남깁니다.
   - 예시:
     ```python
     '''
     Q. 정적 IP 필터링 대신 컨텍스트 기반 동적 인가(Dynamic Authorization)를 채택한 이유는?
     A. IP 스푸핑 위협을 방어하고, 사용자 신원 및 디바이스 상태 무결성을 런타임에 지속 검증(Continuous Verification)하기 위함.
     '''
     ```
3. **자동화 파이프라인 연동:**
   - 위 규칙에 따라 코드를 커밋하고 원격 저장소에 푸시하면, 매일 17:00 KST에 `pipeline/harness.py`와 올인원 파이프라인이 자동으로 `docs/posts/c04-mini-watch-dayXX.md` 또는 `docs/posts/c05-mini-watch-dayXX.md` 기술 블로그 포스트를 생성하여 배포를 준비합니다.
