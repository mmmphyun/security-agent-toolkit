# 3교시. 오케스트레이션 — 함수로 묶어 한 줄로 잇기

from mini_pipeline_func import run_desk
from mini_pipeline_func import run_report
from mini_pipeline_func import notify_mini

judgment = run_desk()
report = run_report(judgment)
notify_mini(report)
print("[파이프라인 완료]")

'''
Q. notify_mini(run_report(run_desk())) 형태로 실행하지 않는 이유
A. 가독성, 디버깅 용이성, 에러 처리(예외 격리), 로깅 및 모니터링 관점에서의 치명적인 한계 때문
    디버깅 및 장애 분석 불가, 단계별 유효성 검증(Validation) 불가, 인지 부하(Cognitive Load) 증가
'''

'''
Q. 해당 파일 실행 후 __pycache__와 하위 파일이 생성됨. 목적과 이유는?
A. __pycache__ 폴더와 하위 파일(.pyc)은 파이썬 인터프리터(CPython)가 소스 코드를 컴파일하여 생성한 바이트코드(Bytecode) 캐시.
    파이썬은 스크립트를 플랫폼 독립적인 가상 머신 명령어인 바이트코드로 컴파일한 뒤 PVM(Python Virtual Machine)에서 실행.
    로딩 및 구문 분석(Parsing) 시간 단축, 시작(Startup) 속도 개선의 성능 최적화 목적.
'''