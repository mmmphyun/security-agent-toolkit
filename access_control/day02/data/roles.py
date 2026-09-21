import sqlite3

con = sqlite3.connect("/app/db/company.db")
con.execute("""
    CREATE TABLE roles (
        role TEXT PRIMARY KEY
    )
""")
con.execute("""
    INSERT INTO roles
    VALUES ('sales')
""")
con.execute("""
    INSERT INTO roles
    VALUES ('account_admin')
""")
con.commit()

for row in con.execute("""
    SELECT *
    FROM roles
"""):
    print(row)

con.close()



'''
Q. rolse와 permissions 테이블은 단일 컬럼을 두고 목차 용도로만 사용해? 이런 테이블을 지칭하는 용어는 뭐야?
A. roles와 permissions 테이블은 단순히 식별자(이름) 하나만 두는 단일 컬럼 테이블로 끝나지 않으며, 단순 목차 역할에 그치지 않고 도메인 엔티티로서의 메타데이터를 관리합니다.

1. 테이블을 지칭하는 실무 용어

룩업 테이블 (Lookup Table) / 참조 테이블 (Reference Table): 코드성 데이터나 유효한 값의 도메인(범위)을 정의하고 외래키(FK) 무결성을 보장하기 위해 참조되는 테이블을 통칭합니다.

마스터 테이블 (Master Table): 시스템의 핵심 기준 정보(역할 마스터, 권한 마스터)를 관리하는 기준 테이블을 의미합니다.

코드 테이블 (Common Code Table): 단일 컬럼 대신 코드값, 코드명, 사용 여부 등을 통합 관리하는 엔터프라이즈 환경에서 자주 쓰이는 용어입니다.

2. 단일 컬럼으로 구성하지 않는 이유
실무에서 roles와 permissions를 단일 컬럼으로 설계하면 관리 및 운영 시 한계가 발생합니다. 일반적으로 다음과 같은 메타데이터 컬럼들을 포함합니다.

식별자 분리: 내부 식별용 대리키(id BIGINT/UUID)와 비즈니스 키(code VARCHAR, 예: ROLE_ADMIN, CONTRACT_VIEW)

관리 편의성: UI 표시명(name), 권한 및 역할에 대한 구체적 설명(description)

운영 제어: 소프트 딜리트 및 활성화 플래그(is_active, is_system), 생성/수정 일시(created_at, updated_at)

3. 관계 정의 테이블과의 구분
roles와 permissions가 개별 엔티티(마스터/룩업)라면, 둘 사이를 다대다(N:M)로 엮어주는 role_permissions는 매핑 테이블(Mapping Table) / 교차 테이블(Junction Table / Association Table)이라고 부릅니다.
'''