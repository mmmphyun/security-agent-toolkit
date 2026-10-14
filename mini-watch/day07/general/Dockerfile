FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=5000
EXPOSE 5000
CMD ["sh", "-c", "exec waitress-serve --host=0.0.0.0 --port=$PORT app:app"]
