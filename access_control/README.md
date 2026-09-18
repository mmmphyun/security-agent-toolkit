# 3과목: 접근통제 자동화 (access_control)

이 디렉토리는 SKT ALEPH 3과목(접근통제 자동화)의 실습 소스코드와 리팩터링 결과물, 보고서 등을 관리하는 공간입니다.

---

## 1. 디렉토리 구조 표준

각 일차별 실습은 `day01`부터 `day05`까지 독립된 서브 디렉토리로 구성하며, 도커 실습에 사용되는 데이터 파일은 compose.yaml기반으로 파악합니다.

```text
network_zt/
├── README.md                           # 과목 개요 및 가이드 (본 문서)
│
├── day01/                              # 1일차 실습
│   ├── data/                           # 1일차 전용 실습 데이터
│   │   └── pcap_sample.pcap
│   ├── 01_packet_analyzer.py           # 역할별 번호 접두사 파일명
│   └── 02_zt_policy_engine.py
│
└── day02/                              # 2일차 실습
    └── ...
```

---

## 2. 파일 명명 및 주석 작성 규칙

1. **역할 기반 파일 명명:**
   - 단순 `test.py`, `main.py` 대신 `01_packet_filter.py`, `02_firewall_rule_parser.py`와 같이 교시/역할별 순번 접두사를 부여합니다.
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
