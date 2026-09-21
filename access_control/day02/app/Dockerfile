# Python 3.12가 준비된 작은 Linux 이미지에서 시작한다.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# 이 폴더의 파일을 전부 이미지 안 /app으로 복사한다. pep.py와 pdp.py가 함께 들어간다.
COPY . .
# 켤 때 어느 파일을 실행할지는 compose.yaml의 command가 정한다.
CMD ["python", "pep.py"]
