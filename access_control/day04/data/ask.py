import sqlite3

con = sqlite3.connect("/app/db/company.db")

for row in con.execute("""
    SELECT *
    FROM assignments
"""):
    print(row)
for row in con.execute("""
    SELECT COUNT(*)
    FROM access_changes
"""):
    print(row)

con.close()


'''
오늘은 궁금한 점도, 남길 말도 없다.
어제 내용에서 흐름을 그대로 타고 넘어와 사실상 이어지는 느낌이다.
파일이 많아 오히려 걱정이다.
캡스톤에서 IAM 기반으로 시나리오를 짜둔 것도 존재하는데
이번 접근통제 과목이 중요하지 않을까 생각된다.
'''