# 3교시. 오케스트레이션 — 함수로 묶어 한 줄로 잇기

def run_desk():
    print("[판단] 3건 처리")
    return ["r1", "r2", "r3"]

def run_report(results):
    print(f"[보고] {len(results)}건 보고서 작성")
    return "daily_report.md"

def notify_mini(filename):
    print(f"[알림] {filename} 생성 소식 전송")


def main():
    print("[자체 테스트]", run_desk())

if __name__ == "__main__":
    main()



'''
Q. if __name__ == "__main__": 내부에 로직을 적는 것과 main() 함수를 정의하는 것의 차이는?
A. 전역 네임스페이스 오염 방지 (Variable Scoping): 블록 내부에서 선언한 변수는 블록 스코프가 아닌 모듈 레벨의 전역 변수. 따라서 main 함수의 로컬 스코프를 가지게 하기 위함.
    메모리 해제 시점 (Garbage Collection): 전역 변수로 선언된 객체는 프로세스가 완전히 종료될 때까지 메모리에 계속 상주
    테스트 및 외부 호출 가능성 (Testability & Reusability): 해당 스크립트의 진입점을 테스트할 때, 블록 안에 직접 작성된 코드는 import해서 개별적으로 호출하거나 Mocking할 수 없음
    CPython 실행 성능 차이: 파이썬 바이트코드 수준에서 전역 변수 접근은 LOAD_GLOBAL 명령어를 사용해 딕셔너리 룩업을 수행.
                        반면 함수 내부의 지역 변수 접근은 LOAD_FAST 명령어를 사용하여 고정 크기 배열의 인덱스로 바로 접근하므로 연산 속도가 더 빠름
'''