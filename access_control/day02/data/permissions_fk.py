import sqlite3

con = sqlite3.connect("/app/db/company.db")
con.execute("PRAGMA foreign_keys = ON")

con.execute("""
    CREATE TABLE permissions_new (
        role TEXT NOT NULL,
        action TEXT NOT NULL,
        PRIMARY KEY (role, action),
        FOREIGN KEY (role) REFERENCES roles(role)
    )
""")

con.execute("""
    INSERT INTO permissions_new
    SELECT *
    FROM permissions
""")
con.execute("DROP TABLE permissions")
con.execute("ALTER TABLE permissions_new RENAME TO permissions")
con.commit()

for row in con.execute("""
    SELECT *
    FROM permissions
"""):
    print(row)

con.close()



'''
Q. 금융 등 엄격한 데이터 정합성을 요구하는 분야가 아닌 이상 fk 사용을 지양하는 것으로 아는데, 그 이유는?
A. 대규모 트래픽을 처리하는 IT 서비스나 웹 서비스 환경에서 물리적 외래키(Foreign Key, 이하 FK) 제약조건을 의도적으로 제거하는 주된 이유는 성능 저하, 락(Lock) 경합, 아키텍처 확장성(샤딩/MSA)의 한계, 운영 유지보수의 병목 때문입니다.

논리적으로는 관계(Join 등)를 유지하되, 물리적 제약조건(CONSTRAINT ... FOREIGN KEY)은 DB 엔진에 위임하지 않고 애플리케이션 레이어에서 검증하는 패턴을 주로 채택합니다.

1. 동시성 저하 및 데드락(Deadlock) 유발

부모 테이블 참조 검사 락: 자식 테이블에 데이터를 INSERT하거나 UPDATE할 때, 스토리지 엔진(예: MySQL InnoDB)은 부모 테이블의 해당 레코드가 존재하는지 확인하기 위해 공유 락(S-Lock, Shared Lock)을 획득합니다.

동시성 병목: 자식 테이블에 트래픽이 몰려 대량 쓰기가 일어날 때 부모 레코드에 빈번한 S-Lock이 걸리며, 동시에 부모 레코드를 수정하려는 트랜잭션(배타적 락, X-Lock 필요)과 충돌하여 트랜잭션 지연 및 데드락 빈도가 급증합니다.

2. 샤딩(Sharding) 및 분산 DB/MSA 환경에서의 물리적 한계

인스턴스 분리 불가: 서비스 규모가 커져 DB를 수평 분할(샤딩)하거나 도메인별로 데이터베이스를 물리적으로 분리(MSA)하는 순간, RDBMS 엔진 수준의 크로스-인스턴스 FK 제약조건은 동작하지 않습니다.

초기 아키텍처 종속: 초기 모놀리스 DB에서 물리적 FK를 강하게 묶어둘 경우, 이후 서비스 분리나 샤딩으로 전환할 때 테이블 간 결합도가 높아 마이그레이션 난이도가 기하급수적으로 증가합니다.

3. 데이터 마이그레이션, 대량 배치, 테스트의 비효율

대량 적재(Bulk Insert/ETL) 속도 저하: 수백만 건 단위의 로그성 데이터나 정산 데이터를 밀어 넣을 때, 매 건마다 부모 테이블 PK 인덱스를 참조 검사하므로 쓰기 Throughput이 크게 떨어집니다.

삭제/수정 시 의존성 순서 강제: 백업 데이터 복원, 테스트 데이터 초기화, 배치 파티션 드롭 시 부모-자식 간의 실행 순서를 엄격히 맞춰야 하며, 이를 우회하기 위해 제약조건을 비활성화(FOREIGN_KEY_CHECKS = 0)하는 등의 운영 리스크가 따릅니다.

Cascade 옵션의 연쇄 잠금 위험: ON DELETE CASCADE를 설정한 경우 부모 레코드 하나를 지우는 작업이 수천~수만 건의 자식 레코드 락과 삭제로 이어져 서비스 장애를 유발할 수 있습니다.

4. 실무 대체 방식

논리적 관계 유지 + 인덱스만 생성: 외래키 제약조건은 걸지 않되, Join 성능을 확보하기 위해 자식 테이블의 외래 참조 컬럼에 일반 인덱스(B-Tree)만 생성합니다.

정합성 보증 주체 이동: 데이터 존재 유무 확인 및 유효성 검증은 애플리케이션 서비스 레이어(비즈니스 로직)나 트랜잭션 단위에서 처리합니다.


Q. 샤딩이란?
Join 성능을 확보하기 위해 자식 테이블의 외래 참조 컬럼에 일반 인덱스(B-Tree)만 생성한다는게 정확히 무엇인지?
정합성을 애플리케이션에서 처리하면 오염된 데이터로 인한 오탐이 있을 수 있지 않나?
트랜잭션 단위에서 처리하면 병목이 문제될 것 같고. 

A. ### 브리핑

질문하신 네 가지 핵심 쟁점에 대한 엔지니어링 분석입니다.

---

### 1. 샤딩(Sharding)이란?

**정의 및 동작 방식**

* 샤딩은 단일 데이터베이스 인스턴스의 용량 및 I/O 한계를 극복하기 위해, **동일한 스키마를 가진 테이블의 데이터를 여러 독립된 DB 서버(샤드, Shard)에 분산 저장**하는 수평 파티셔닝(Horizontal Partitioning) 기법입니다.
* 특정 기준 값인 **샤드 키(Shard Key)**(예: `user_id`, `tenant_id`)를 기준으로 해시(Hash) 연산이나 범위(Range)를 계산하여 어떤 샤드로 질의를 보낼지 라우팅합니다.

**물리적 FK와의 충돌**

* 샤드 A(서버 1)에 `users(user_id=100)`가 존재하고, 샤드 B(서버 2)에 `orders(user_id=100)`가 저장되는 환경에서는 단일 DB 엔진의 원자적 제약조건 검사 기능이 물리적으로 닿지 않습니다. 따라서 샤딩 도입 시 엔진 레벨의 FK는 필연적으로 제거됩니다.

---

### 2. 자식 테이블 외래 참조 컬럼의 일반 인덱스(B-Tree) 생성이란?

**개념**

* DB 스키마에 `FOREIGN KEY (role_id) REFERENCES roles(id)` 제약조건 구문을 작성하지 않는 대신, 단순 검색 가속용 인덱스인 `CREATE INDEX idx_orders_user_id ON orders(user_id)`만 부여하는 방식입니다.

**차이점 비교**

* **물리적 FK 제약조건이 있을 때:** 자식 테이블에 `INSERT` 발생 시 부모 테이블의 행 존재 여부를 검사하고 S-Lock을 겁니다. 또한 부모 행 삭제/수정 시 자식 테이블을 스캔하여 참조 여부를 차단하거나 연쇄 동작합니다.
* **일반 B-Tree 인덱스만 있을 때:** 쓰기 작업 시 부모 테이블을 일체 조회/잠금하지 않고 자신의 B-Tree 인덱스에 노드만 추가합니다.
* **Join 성능 유지 원리:**
```sql
SELECT *
FROM users u
JOIN assignments a ON u.user_id = a.user_id
WHERE u.user_id = 'minsu';

```


위 쿼리 실행 시 옵티마이저는 `assignments` 테이블을 전체 탐색(Full Table Scan)하지 않고, `a.user_id`에 걸린 B-Tree 인덱스를 타서 O(log N)으로 조인 대상 레코드만 찾아냅니다. 즉, **Join 조회 성능은 100% 확보하면서, 쓰기/수정 시의 참조 락과 무결성 오버헤드만 완전히 걷어내는 설계**입니다.

---

### 3. 애플리케이션 레벨 정합성 처리 시 데이터 오염/오탐 우려

**지적하신 오염 가능성은 실제 발생하며 타당한 지적입니다.**

* 애플리케이션 버그, 배포 도중 롤백, 비정상 프로세스 종료, 운영자의 직접 DB 조작(`DML 수기 실행`) 등으로 인해 부모가 없는 고아 데이터(Dangling Pointer / Orphan Data)가 생성될 수 있습니다.

**실무에서의 오염 방어 패턴**

1. **소프트 딜리트(Soft Delete):** 데이터를 물리적으로 `DELETE`하지 않고 `is_deleted = 1` 또는 `deleted_at` 플래그로 처리합니다. 고아 레코드가 발생할 물리적 삭제 자체를 원천 차단합니다.
2. **배치 기반 데이터 정합성 검증기(Reconciliation/Auditor Batch):** 주기적(예: 매일 새벽)으로 부모가 유실된 레코드를 탐지하는 백그라운드 배치 쿼리를 실행하여 알림을 발송하고 자동 보정합니다.
3. **방어적 조회 로직:** Join 시 부모 레코드가 누락되어도 시스템이 다운되지 않도록 `INNER JOIN`으로 유효 레코드만 걸러내거나, Null 처리를 비즈니스 로직에 기본 탑재합니다.

---

### 4. 트랜잭션 단위 검증 시 병목 문제

**정확한 분석입니다.**

* 애플리케이션에서 "부모 레코드 존재 확인(`SELECT`) $\rightarrow$ 자식 레코드 삽입(`INSERT`)"을 하나의 트랜잭션으로 묶고 격리 수준(Isolation Level)을 높이거나 잠금(Lock)을 걸면, DB 엔진이 FK를 검사할 때 발생하던 동시성 병목이 그대로 재현됩니다.

**실무 해결책: 락 없는 비즈니스 흐름 설계**

* **부모 검증 최소화:** 트래픽이 집중되는 도메인은 세션/JWT 토큰 또는 Redis 캐시 레이어에서 `user_id`의 유효성을 1차 검증(O(1))하고, DB 트랜잭션 내부에서는 부모 테이블을 락 걸고 조회하지 않습니다.
* **비동기 이벤트 기반 일관성 (Eventual Consistency):** 즉시 정합성을 포기하고, 자식 레코드 생성 후 메시지 큐(Kafka, Redis Streams 등)로 이벤트를 발행하여 비동기로 상태를 동기화합니다.
* **원자적 조건부 업데이트:**
```sql
-- 부모가 활성 상태일 때만 갱신을 허용하는 단일 쿼리 조건문 활용
UPDATE parent SET child_count = child_count + 1 WHERE id = 10 AND status = 'ACTIVE';
```
'''