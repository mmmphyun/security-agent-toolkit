# Python 3.12가 준비된 작은 Linux 이미지에서 시작한다.
FROM python:3.12-slim

# 이미지 안에서 사용할 작업 폴더
WORKDIR /app

# 필요한 도구부터 설치한다. RUN은 이미지를 만들 때 실행된다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Windows 실습 폴더의 파일을 이미지 안 /app으로 복사한다.
COPY server.py company.json ./

# 컨테이너를 켤 때 실행할 명령
CMD ["python", "server.py"]
