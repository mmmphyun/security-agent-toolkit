# 6교시 요청부터 계약 열람까지 전체 흐름을 완성하자
import sqlite3


def show_requests(employee_name):
    con = sqlite3.connect("/app/db/company.db")
    rows = con.execute("""
        SELECT access_requests.contract_id,
               access_requests.status
        FROM access_requests
        JOIN users
        ON access_requests.requester_id = users.user_id
        WHERE users.name = ?
    """, (employee_name,)).fetchall()
    con.close()

    labels = {
        "APPROVED": "승인",
        "REJECTED": "반려",
    }
    for contract_id, status in rows:
        print(f"{employee_name} / {contract_id}: {labels[status]}")


show_requests("한지호")
show_requests("정소라")



# 5교시 승인 상태와 결정 기록을 함께 저장하자
# import sqlite3

# con = sqlite3.connect("/app/db/company.db")
# row = con.execute("""
#     SELECT access_requests.contract_id,
#            access_requests.status,
#            access_decisions.decision
#     FROM users
#     JOIN access_requests
#     ON users.user_id = access_requests.requester_id
#     JOIN access_decisions
#     ON access_requests.request_id = access_decisions.request_id
#     WHERE users.name = ?
#     AND access_requests.contract_id = ?
# """, ("정소라", "C-1003")).fetchone()
# con.close()

# contract_id, request_status, decision = row
# if request_status == "APPROVED" and decision == "APPROVED":
#     print(f"정소라의 {contract_id} 요청은 승인되었고 두 기록이 일치합니다.")


# 4교시 승인된 사람에게 승인된 계약만 보여 주자
# import requests


# def show_contract(contract_id):
#     reply = requests.get(
#         "http://pep:5000/document",
#         params={"user": "jiho", "contract": contract_id},
#         timeout=3,
#     )
#     body = reply.json()

#     if reply.status_code == 200:
#         print(f"{contract_id}: {body['title']} / {body['amount']}")
#     else:
#         print(f"{contract_id}은 열람할 수 없습니다.")


# show_contract("C-1002")
# show_contract("C-1001")


# 3교시 직원의 요청을 서버가 접수하게 하자
# import requests

# request_id = 2

# reply = requests.get(
#     f"http://127.0.0.1:5002/requests/{request_id}",
#     timeout=3,
# )
# body = reply.json()

# if (
#     body["requester_id"] == "sora"
#     and body["contract_id"] == "C-1003"
#     and body["status"] == "PENDING"
# ):
#     print("정소라의 C-1003 요청은 아직 대기 중입니다.")




# 1, 2교시 코드
# import sqlite3
# from pathlib import Path
# from decide_request import decide_request

# employee_name = input("직원 이름: ")
# contract_id = input("계약 번호: ")

# result = decide_request(1, "doyun", "APPROVED", "장애 대응에 필요한 계약으로 확인")

# __file__: 현재 실행 중인 파이썬 스크립트의 경로 문자열
# .resolve(): 절대 경로로 정규화
# .parent: 상위 디렉터리로 (cd ..)
# /: 경로 결합 연산자
# db_path = Path(__file__).resolve().parent.parent / "db" / "company.db"
# con = sqlite3.connect(db_path)

# 1교시 쿼리
# cur = con.execute("""
#     SELECT a.status
#     FROM access_requests a
#     JOIN users u
#     ON a.requester_id = u.user_id
#     WHERE u.name = ?
#     AND a.contract_id = ?
# """, (employee_name, contract_id))

# 2교시 쿼리
# cur = con.execute("""
#     SELECT
#         requester.name,
#         ar.contract_id,
#         ar.status,
#         approver.name
#     FROM access_requests ar
#     JOIN users requester
#     ON ar.requester_id = requester.user_id
#     JOIN access_decisions ad
#     ON ar.request_id = ad.request_id
#     JOIN users approver
#     ON ad.approver_id = approver.user_id
#     WHERE ar.request_id = 1
# """)

# row = cur.fetchone()

# if result == "RECORDED":
#     if row[2] == "APPROVED":
#         print(f"{row[3]}이 {row[0]}의 {row[1]} 요청을 승인했습니다.")

# con.close()



'''
*1교시. 담당 정보와 예외 요청을 구분하자*
SELECT a.status
FROM users u
JOIN access_requests a
ON u.user_id = a.requester_id
WHERE u.name = ?
AND a.contract_id = ?
도 같은 동작. 하지만 도메인 모델링 및 성능 관점에서 FROM access_requests a JOIN users u 구조가 적절함.

두 쿼리 모두 INNER JOIN이므로 반환되는 논리적 결과 데이터는 완전히 동일함.
하지만 조회의 주체가 되는 access_requests를 FROM절에 두고, 세부 조건 검증을 위해 users를 JOIN하는 것이 표준적인 의미 체계에 부합.
일반적으로 access_requests는 요청이 누적되는 대규모 트랜잭션 테이블이고, users는 상대적으로 적은 수의 엔티티를 가짐.
만약 a.contract_id에 인덱스가 걸려 있다면, access_requests에서 특정 계약 건들을 먼저 좁힌 뒤 해당 requester_id의 u.name만 매핑하는 것이 전체 사용자 테이블에서 이름을 검색하는 것보다 검색 범위를 좁히는 데 유리


*2교시. 대기 중인 요청을 승인해 보자*
users를 2번 조인(총 3회 조인)하는 이유와 타당성:
사용자 이름(Name)을 안전하게 가져오기 위해 별칭(AS requester, AS approver)을 사용해 users를 각각 독립적으로 조인하는 것은 RDBMS 설계 표준 패턴
기본키(user_id, request_id) 기반의 인덱스 검색(Index Point Lookup)으로 실행되므로 3회 조인이라 해도 성능 부하는 극히 미미
이번 과제 요구사항에 맞게 ar.request_id = 1로 하드코딩 하였으나, 확장할 경우 파라미터화된 쿼리를 사용해 동적으로 주입해야함.
'''