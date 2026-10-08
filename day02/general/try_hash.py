from werkzeug.security import generate_password_hash, check_password_hash

password_hash = generate_password_hash("Learn123!")
print(password_hash)
print(check_password_hash(password_hash, "Learn123!"))
print(check_password_hash(password_hash, "Wrong123!"))


'''
최근에 캡스톤하느라 바쁘기도 했고, 강의 시간에도 이론 및 실습보다는 캡스톤을 진행할 시간을 더 주셔서 주석을 뜸하게 달았다.
오늘 비밀번호 암호화를 보며 개인적으로 공부한 kms가 생각이 났다.

Q. 실제 클라우드 운영 시 사용자 정보를 암호화하는 경우가 있잖아?
이때 암호화 알고리즘을 뭘 선택하던 이를 복호화할 수 있는 키는 해당 서비스와 같은 서버에 존재하면 안돼. 맞지?
그래서 사용하는게 kms고. 암호문을 평문으로 복호화하기 위해 키를 꺼내오고 복호화 코드를 앱 서버 단에서 돌리는게 아니라, 앱 서버에서 kms로 복호화 요청만 보낼 수 있고, kms 내에서 키를 바탕으로 복호화해 평문을 앱 서버로 전달한다며?
이게 공격자가 키를 탈취해서 복호화하는 것은 막지만 결국 공격자도 복호화 요청을 보내 평문을 받을 수 있는 한계가 있다고 알아. 물론 해당 요청이 로그에 남기 때문에 이를 바탕으로 피해를 최소화하는게 목적인 것도 알고.
방법이 현재로썬 이게 최선인거야?
보안에 절대는 없지만 어쨌든 얘도 평문을 받아내는 방법이 그렇게 어렵진 않아보이는데? 로그 관제를 통해 공격자를 차단하려면 몇 개의 정보는 털릴 생각을 해야하는 거잖아.
A. 1. 전제 교정: KMS의 실제 동작 메커니즘 (봉투 암호화)

KMS의 직접 암/복호화 API(kms:Encrypt, kms:Decrypt)는 최대 4KB의 데이터만 처리 가능하며, 왕복 네트워크 레이턴시(20~50ms)와 API 비용 때문에 사용자 정보 전체를 KMS로 전송하지 않음.

```text
[암호화 시점]
앱 서버 -> KMS: kms:GenerateDataKey(KeyId)
KMS -> 앱 서버: Plaintext Data Key (32B) + Encrypted Data Key (Ciphertext Blob)
앱 서버: 메모리 상에서 Plaintext Data Key로 평문 암호화 (AES-256-GCM)
앱 서버: DB에 [Encrypted Data Key + 암호문] 저장 후 Plaintext Data Key 메모리 즉시 소거(Zeroize)
[복호화 시점]
앱 서버 -> KMS: kms:Decrypt(CiphertextBlob=Encrypted Data Key)
KMS HSM 내부: 루트 키(CMK)로 Data Key 복호화 -> Plaintext Data Key 반환
앱 서버: 반환받은 Data Key로 메모리 상에서 로컬 복호화 수행
```
KMS가 방어하는 것: FIPS 140-2/3 Level 3 HSM 경계를 통해 루트 키(Master Key)의 물리적·논리적 유출을 100% 차단. 공격자가 DB 전체를 덤프해가도 외부 오프라인 환경에서 무차별 대입(Brute-force) 복호화가 불가능함.
KMS 단독 사용의 취약점: 인스턴스 실행 컨텍스트(IAM 역할)를 획득한 공격자가 활성 세션을 악용해 온라인으로 kms:Decrypt를 반복 호출하는 행위.
2. "평문을 그냥 받아내는 문제"를 차단하는 5대 엔지니어링 방어선
(1) 비대칭 권한 격리 (Write-Heavy, Read-Zero 아키텍처)

사용자 정보(주민번호, 카드번호, 비밀번호 등)를 저장하는 서버와 조회하는 서버를 물리적/논리적으로 분리(CQRS 패턴)함.

수집/저장 서버 (99%의 워크로드): 비대칭 암호화 키 페어 중 공개키(Public Key) 또는 kms:GenerateDataKeyWithoutPlaintext 권한만 부여받음.
메커니즘: 저장 서버는 데이터를 암호화할 수만 있고, 복호화 권한(kms:Decrypt) 자체가 IAM 정책상 존재하지 않음. 공격자가 저장 서버를 완전 장악(RCE)해도 단 1건의 평문도 복호화할 수 없음.
복호화 서버: 고도로 격리된 극소수의 배치/정산 서버에만 복호화 권한을 일시적으로 허용.
(2) 암호화 컨텍스트(Encryption Context) 기반 AAD 바인딩

AES-GCM과 같은 AEAD(Authenticated Encryption with Associated Data) 알고리즘의 메커니즘을 KMS 레벨에서 강제함.

작동 원리: 암호화 시 {"user_id": "usr_9981", "tenant_id": "enterprise_a"}와 같은 임의 메타데이터(AAD)를 바인딩함.
보안 통제: 복호화 시 암호문과 함께 정확히 일치하는 컨텍스트를 제출하지 않으면 KMS HSM이 복호화를 암호학적으로 거부함.
효과: 공격자가 특정 사용자의 데이터 키를 탈취하거나 다른 암호문 레코드를 확보해도, 컨텍스트가 교차 일치하지 않으면 무차별 복호화가 차단됨. 또한 IAM 정책에서 특정 테넌트/사용자 조건(kms:EncryptionContext:tenant_id)을 컨텍스트 수준에서 인가(ABAC) 가능.
(3) 기밀 컴퓨팅 (AWS Nitro Enclaves) 및 암호학적 원격 증명 (Attestation)

공격자가 EC2 인스턴스의 Root 권한 및 OS 커널을 장악했을 때 메모리 덤프나 KMS API 프록시 호출을 원천 차단하는 하드웨어 격리 기술.

저수준 CS 메커니즘:
Nitro Hypervisor를 통해 CPU 코어와 메모리를 주 OS(Host)로부터 완전히 분리된 독립 가상 머신(Enclave)에 격리 할당.
Enclave는 외부 네트워크, 스토리지, 인라인 대화형 셸(SSH)이 전혀 없으며, 오직 로컬 vSocket(가상 소켓)으로만 Host와 통신.
KMS 암호학적 증명 연동:
Enclave 내부에서 구동되는 코드의 바이너리 해시(PCR0, PCR1, PCR2 측정값)를 Nitro 보안 프로세서가 서명한 Attestation Document로 발급.
KMS Key Policy에 kms:Recipient:AttestationDocument 조건을 설정.
결과: 호스트 OS를 장악한 공격자가 직접 aws kms decrypt를 때리면 PCR 해시 증명서가 없어 KMS가 요청을 거부함. 오직 변조되지 않은 Enclave 내부 프로세스만 복호화된 키를 수신할 수 있으며, 호스트 관리자/공격자는 Enclave 메모리를 덤프할 수 없음.
(4) 토큰화(Tokenization) 및 볼트(Vault) 격리

일반 웹/앱 서버가 데이터베이스의 암호문이나 평문에 아예 접근하지 못하도록 데이터 계층을 추상화함.

앱 서버는 데이터베이스에 실제 암호화된 사용자 정보 대신 무의미한 난수 매핑값(tok_9f8a7c6b)만 보관.
실제 데이터와 암/복호화 엔진은 폐쇄망 내 전용 Token Vault(예: HashiCorp Vault, 전용 결제 게이트웨이)에만 격리.
앱 침해 시 공격자가 획득 가능한 데이터는 외부에선 해석 불가능한 토큰뿐임.
(5) 클라이언트 종단간 암호화 (E2EE / Zero-Knowledge)

서버가 평문을 알 필요가 없는 워크로드(비밀번호, 개인 금고 데이터, 메신저 등)에 적용.

사용자의 디바이스(WebCrypto API, Secure Enclave)에서 사용자 마스터 패스워드 유도 키(Argon2, PBKDF2)로 암호화 후 전송.
서버 및 KMS는 암호화에 개입하지 않으며, 서버 침해자가 인프라 전체를 탈취해도 수학적으로 복호화 키가 서버에 존재하지 않음.
'''