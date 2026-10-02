# 4-5과목: 미니 프로젝트

이 디렉토리는 SKT ALEPH 4과목과 5과목을 하나의 미니 프로젝트로 만들어 소스코드와 리팩터링 결과물, 보고서 등을 관리하는 공간입니다.

---

## 1. 디렉토리 구조 표준

각 일차별 실습은 day00 형태의 디렉토리 내 존재하며, 하위 산출물은 강의 노션 페이지를 참고하여 확인합니다.

예시: 4과목 1일차 - general/, monitor/, clients/, requirements.txt, README·Git 이력과 GitHub의 mini-watch 저장소, monitor/logs/http_events.jsonl
예시 출처 (https://app.notion.com/p/Day-1-3b9ae3d1800c815db6c8e4747b254b76)

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
   - 위 규칙에 따라 코드를 커밋하고 원격 저장소에 푸시하면, 매일 17:00 KST에 `pipeline/generate_draft.py`가 자동으로 `docs/posts/c03-access-control-dayXX.md` 초안을 생성하여 Pull Request를 오픈합니다.
