# mini-watch 2일차 시작 코드

`day02-start`는 2일차 1교시에서 사용할 작은 시작 코드다. `general`은 게시글을 보여 주고, `monitor/backend`는 일반 서비스에 요청을 전달한다. 이번 브랜치에는 아직 DB 연결 기능이 없다.

복제한 프로젝트 폴더를 VS Code에서 연다. `Ctrl+Shift+P` → `Terminal: Select Default Profile` → **Command Prompt(명령 프롬프트, CMD)**를 선택하고 새 터미널을 연다.

## 일반 서비스 실행

VS Code의 **general 폴더를 오른쪽 클릭 → 통합 터미널에서 열기**를 선택한다. CMD에서 이 폴더의 가상환경을 처음 한 번 만든다.

```text
python -m venv venv
```

가상환경을 켠다. 입력 줄 앞에 `(venv)`가 붙으면 켜진 것이다.

```text
venv\Scripts\activate
```

패키지 목록을 설치한다.

```text
python -m pip install -r requirements.txt
```

일반 서버를 실행한다. 이 창은 켜 둔다.

```text
python app.py
```

크롬에서 http://127.0.0.1:5100/posts/1 을 열면 1번 게시글이 나온다.

## 감시 서비스 실행

VS Code의 **monitor 아래 backend 폴더를 오른쪽 클릭 → 통합 터미널에서 열기**로 별도의 CMD를 연다. 이 폴더에도 가상환경을 처음 한 번 만든다.

```text
python -m venv venv
```

가상환경을 켠다.

```text
venv\Scripts\activate
```

`(venv)`를 확인하고 패키지 목록을 설치한다.

```text
python -m pip install -r requirements.txt
```

감시 서버를 실행한다.

```text
python app.py
```

크롬에서 http://127.0.0.1:5200/posts/1 을 열면 일반 서버와 같은 게시글이 나온다.

새 CMD를 열 때는 해당 서비스 폴더에서 가상환경을 다시 켠다. 서버 코드를 고치면 저장한 뒤 서버 창에서 `Ctrl+C`로 멈추고 `python app.py`로 다시 실행한다.

## 수업 이어가기

이 폴더에서 1교시부터 차례로 기능을 붙인다. `day03-start` 브랜치에는 3일차 시작 코드(2일차 완성 상태)와 DB 준비·실행 안내가 있다.

`venv`, Python 캐시와 실제 `.env`는 Git에 포함하지 않는다. 패키지는 서비스별 `requirements.txt`로 각 컴퓨터에서 설치한다.
