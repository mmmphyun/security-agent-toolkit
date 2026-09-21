import sqlite3

con = sqlite3.connect("/app/db/company.db")

con.execute("""
    CREATE TABLE permissions (
        role    TEXT NOT NULL,
        action  TEXT NOT NULL,
        PRIMARY KEY (role, action)
    )
""")

con.execute("""
    INSERT INTO permissions
    VALUES ('sales', 'view_assigned_contracts')
""")
con.execute("""
    INSERT INTO permissions
    VALUES ('account_admin', 'view_all_amounts')
""")
con.commit()

for row in con.execute("""
    SELECT *
    FROM permissions
"""):
    print(row)

con.close()



'''
Q. role에 따른 권한을 문서화해두고 쿼리 또는 애플리케이션 단에서 보여줄 데이터를 설정하는건 실무에서 사용하지 않나?
A. 문서에만 권한을 적어두고 쿼리 조건문(WHERE)이나 애플리케이션 하드코딩으로 데이터 노출 범위를 제어하는 방식은 소규모 초기 프로젝트를 제외하면 실무에서 지양됩니다.
실무에서는 RBAC(Role-Based Access Control) 표준에 따라 역할과 권한을 테이블로 모델링하여 데이터베이스에서 직접 관리하는 방식을 기본으로 채택합니다.

1. 쿼리/코드 하드코딩 방식의 한계

권한 변경 시 배포 강제: 영업팀에 특정 조회 권한을 추가하거나 역할을 세분화할 때마다 백엔드 쿼리와 애플리케이션 코드를 수정하고 재배포해야 합니다.

로직 파편화 및 보안 누수: 조회 API, 수정 API, 관리자 대시보드, 배치 작업 등 여러 곳에 분산된 쿼리마다 WHERE role = 'sales' 같은 조건을 일일이 맞추다 보면 누락이 발생해 권한 우회 취약점이 발생합니다.

감사(Audit) 및 이력 추적 불가: 누가 언제 어떤 역할에 권한을 부여했는지 DB 수준에서 이력 추적과 관리가 불가능합니다.

2. 실무에서의 RBAC 테이블 관리 방식
실무에서는 실습 예제와 같이 역할과 행동(Permission/Action)을 분리하여 테이블로 영속화합니다.

동적 정책 변경: DB 레코드 추가·수정만으로 재배포 없이 즉각적인 권한 제어가 가능합니다.

표준 정규화 구조: 대다수 엔터프라이즈 시스템은 users - user_roles - roles - role_permissions - permissions 형태의 N:M 관계 테이블 구조를 구성합니다.

엔진 분리(ABAC/PBAC 병행): 권한 테이블에서 허용 여부를 체크한 뒤, "자신이 담당한 데이터만 조회"하는 행 수준 보안(Row-Level Security)은 데이터 소유권 조건과 결합하여 처리합니다.
'''