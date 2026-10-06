# mini-watch 3일차 시작 코드

일반 서비스는 로그인과 게시글 조회를, 감시 서비스는 일반 서비스가 보낸 요청 결과를 수집하고 저장·조회한다. 사용자 로그인과 게시글 요청은 일반 서비스 5100으로 직접 보낸다. 두 Flask 서버는 Windows의 로컬 환경에서 실행한다. PostgreSQL 서버 하나에 `general_db`와 `monitor_db`를 만든다.

이 브랜치는 2일차에 완성한 코드와 초기 SQL을 담은 3일차 시작 자료다. `git clone`으로 소스와 Git 이력을 함께 받는다. PostgreSQL 데이터, 가상환경, 실제 `.env`는 따로 준비한다. 현재 수업 폴더가 정상이라면 그 폴더를 계속 사용한다.

## 폴더

```text
mini-watch-day03-start/
├─ .gitignore
├─ README.md
├─ general/
│  ├─ app.py
│  ├─ db.py
│  ├─ requirements.txt
│  ├─ .env.example
│  ├─ create_user.py
│  ├─ try_db.py
│  ├─ try_hash.py
│  ├─ try_login.py
│  ├─ try_record.py
│  ├─ try_send_event.py
│  ├─ try_events.py
│  └─ sql/
│     ├─ create_database.sql
│     ├─ posts.sql
│     └─ users.sql
└─ monitor/
   └─ backend/
      ├─ app.py
      ├─ db.py
      ├─ requirements.txt
      ├─ .env.example
      ├─ try_event.py
      └─ sql/
         ├─ create_database.sql
         └─ http_events.sql
```

## 1 설치 환경

Python과 PostgreSQL이 필요하다. pgAdmin은 PostgreSQL에 SQL을 실행할 때 사용하는 도구다. 새 DB에서 시작하는 경우에만 아래 초기 SQL을 순서대로 실행한다. 이미 수업을 진행한 DB는 다시 만들지 않는다.

VS Code에서 방금 복제한 프로젝트 폴더를 연다. 교안의 명령대로 받았다면 `mini-watch-day03-start` 폴더다. `Ctrl+Shift+P`를 누르고 `Terminal: Select Default Profile`을 검색한 뒤 **Command Prompt(CMD, 명령 프롬프트)**를 선택한다. 기존 터미널은 자동으로 바뀌지 않으므로 이후 실습은 새로 연 CMD에서 진행한다.

명령은 파일을 더블클릭하지 않고 CMD에 입력한다. 이번 자료는 서비스별 `venv` 폴더를 사용한다. 기존 `.venv` 폴더를 이름만 바꾸어 사용하지 말고, 아래 순서로 `venv`를 새로 만든다.

## 2 일반 서비스 패키지

VS Code에서 general 폴더를 오른쪽 클릭해 통합 터미널을 연다. 터미널이 CMD인지 확인한다. 새로 복제한 폴더에서 가상환경을 처음 한 번 만든다.

```bat
python -m venv venv
```

가상환경을 켠다. 입력 줄 앞에 `(venv)`가 붙으면 활성화된 것이다.

```bat
venv\Scripts\activate
```

목록을 설치한다.

```bat
python -m pip install -r requirements.txt
```

## 3 일반 DB 접속 정보

general/.env.example을 열어 같은 폴더에 `.env`라는 이름으로 저장한다. DB_PASSWORD를 설치 때 정한 비밀번호로 바꾼다. 다른 주소·포트·접속 계정을 쓰는 경우도 각 항목에 맞게 입력한다. 값에 `#` 등 설정 문법 문자가 있다면 따옴표로 감싼다.

실제 `.env`는 DB 접속 항목 다섯 개를 담는다. `.env`를 Git에 올리지 않고 `.env.example`에는 자리표시자만 남긴다.

## 4 일반 DB 준비

pgAdmin에서 다음 순서를 따른다. Query Tool의 편집 내용을 한 파일의 SQL로 바꾼 다음 실행한다.

1. `postgres` DB의 Query Tool에서 general/sql/create_database.sql 실행.
2. Databases를 새로 고치고 `general_db`의 Query Tool을 새로 열기.
3. `SELECT current_database();`로 general_db 연결 확인.
4. general/sql/posts.sql 실행: 기본 게시글 두 건 생성.
5. general/sql/users.sql 실행: 사용자 표 생성.

general 터미널에서 교실 실습 계정을 만든다.

```bat
python create_user.py
```

아이디는 `student`, 비밀번호는 `Learn123!`다. 이는 교실 실습을 위해 공개한 예시이며 실제 계정에 사용하는 비밀번호가 아니다. 같은 아이디가 이미 있으면 기존 계정을 유지한다.

## 5 감시 서비스 준비

VS Code에서 monitor 아래 backend 폴더를 오른쪽 클릭해 새 CMD를 연다. 일반 서비스와 별개의 가상환경을 이 폴더에 처음 한 번 만든다.

```bat
python -m venv venv
```

가상환경을 켠다.

```bat
venv\Scripts\activate
```

입력 줄 앞의 `(venv)`를 확인한 뒤 목록을 설치한다.

```bat
python -m pip install -r requirements.txt
```

backend/.env.example을 같은 폴더의 `.env`로 저장하고 DB_PASSWORD를 설정한다. DB_NAME은 `monitor_db`다. 일반 서비스와 감시 서비스의 DB_NAME을 구별한다.

pgAdmin에서 아래 순서로 실행한다.

1. `postgres` DB의 Query Tool에서 monitor/backend/sql/create_database.sql 실행.
2. Databases를 새로 고치고 `monitor_db`의 Query Tool을 새로 열기.
3. `SELECT current_database();`로 monitor_db 연결 확인.
4. monitor/backend/sql/http_events.sql 실행.

## 6 두 서버 실행

가상환경이 켜진 general 터미널에서 실행한다. 주소는 5100이다.

```bat
python app.py
```

가상환경이 켜진 backend 터미널에서도 실행한다. 주소는 5200이다.

```bat
python app.py
```

새 CMD를 열었으면 해당 폴더에서 `venv\Scripts\activate`로 가상환경부터 켜고 `(venv)` 표시를 확인한다. 서버 코드를 바꾸면 서버 터미널에서 Ctrl+C 후 같은 명령으로 다시 실행한다.

## 7 요청과 기록 확인

general 폴더에서 요청용 CMD를 하나 더 열고 가상환경을 켠다.

```bat
venv\Scripts\activate
```

```bat
python try_events.py
```

일반 서비스 5100에서 로그인 실패 401 → 로그인 성공 200 → 게시글 조회 200 → 없는 게시글 404를 확인한다. 일반 서비스는 각 요청의 메서드·경로·상태 코드만 감시 서비스 5200의 `/api/events`로 보낸다. 아이디·비밀번호·쿠키는 보내지 않는다. 로그인 API는 입력을 검사하는 단계이며 로그인 상태를 유지하지 않는다. 게시글은 로그인 여부와 관계없이 조회할 수 있다.

`python try_login.py`로 정상 로그인200·틀린비밀번호401·없는아이디401·비밀번호누락400도 확인할 수 있다. 일반 터미널에는 각 요청의 세 필드 JSON이 출력된다.

크롬 주소창에 아래 주소를 입력한다.

- 감시 서버 실행 확인: http://127.0.0.1:5200/health
- 전체 최근 기록: http://127.0.0.1:5200/api/events
- 로그인 실패 기록: http://127.0.0.1:5200/api/events?event_type=login_failure

조회는 최신 50개까지 반환한다. `occurred_at`은 감시 DB가 기록을 저장한 시각이다. 감시 서비스에는 사용자 로그인이나 게시글 API가 없다.

감시 서비스가 꺼져 있거나 기록 저장에 실패해도 일반 서비스는 원래 로그인·게시글 응답을 돌려주고 터미널에 경고를 남긴다. 기록 전송은 0.5초의 요청 타임아웃을 두며, 실패한 기록을 다시 보내거나 보관하는 기능은 아직 없다.

`try_record.py`는 고정된 딕셔너리를 JSON으로 출력하는 연습이며 실제 요청을 보내지 않는다. `try_send_event.py`는 일반 서비스를 거치지 않고 고정된 예시 한 건을 수집 API에 보내는 연습 파일이다. `monitor/backend/try_event.py`는 감시 DB에 SQL로 한 행을 넣고 읽는 연습이다. 실제 사용자 흐름은 `try_events.py`로 확인한다.

## 다음 시간에 이어 쓸 것

두 폴더와 DB를 그대로 보관한다. 다른 PC에서는 이 문서 순서로 초기 DB와 실습 계정을 만든 뒤 새 요청을 보내 기록을 쌓는다. 기존 PC에서 작성한 게시글 수정이나 HTTP 기록까지 옮기는 DB 백업은 Git 저장소에 포함되지 않는다.

현재 서버는 127.0.0.1에서 실행하는 로컬 수업용이다. 감시 조회 API의 접근 권한, 로그인 상태 유지와 서비스 배포는 뒤 단계에서 다룬다.
