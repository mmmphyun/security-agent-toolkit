import sqlite3
import re

'''4교시. 고객사 질문에 답하기의 금액 순 정렬을 위한 정규식 기반 함수'''
# def parse_won(text: str) -> int:
#     clean_text = text.replace(",", "").replace(" ", "")
    
#     eok_match = re.search(r"(\d+)억", clean_text)
#     man_match = re.search(r"(\d+)만", clean_text)
    
#     eok = int(eok_match.group(1)) if eok_match else 0
#     man = int(man_match.group(1)) if man_match else 0
    
#     return (eok * 10000) + man


con = sqlite3.connect("/app/db/company.db")

'''DB 컬럼은 건들지 않고 애플리케이션 단에서 해결해보았다.'''
# rows = []
# for row in con.execute("SELECT * FROM contracts"):
#     rows.append(row)

# rows.sort(key=lambda x: parse_won(x[3]), reverse=True)
# for row in rows:
#     print(row)

for row in con.execute("SELECT a.customer, u.name, u.role FROM assignments a JOIN users u ON a.user_id = u.user_id WHERE u.employed = 1 ORDER BY a.customer"):
    print(row)

con.close()



'''
Q. SELECT user_id, COUNT(customer) FROM assignments GROUP BY user_id ORDER BY COUNT(customer) DESC와
SELECT user_id, COUNT(user_id) FROM assignments GROUP BY user_id ORDER BY COUNT(user_id) DESC가 같은 이유는?

A. 해당 테이블의 두 컬럼 모두 NOT NULL 제약 조건이 걸려 있어 NULL 데이터가 존재하지 않기 때문.
만약 customer 컬럼에 NULL 허용 설정이 되어 있고 실제로 NULL 값이 존재하는 행이 있다면, COUNT(customer)는 해당 행을 제외하고 집계하므로 COUNT(user_id)와 결과가 달라질 것.
위 구문의 의미는 각 사용자가 담당하고 있는 고객사(배정 건)가 몇 개인지 계산한다, 아래 구문의 의미는 각 사용자가 테이블에 몇 번 등장(등록)했는지 계산한다.


오늘은 사실상 SQL 기초 강의였다. 포스팅할게 있을까?
'''