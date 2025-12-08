FROM python:3.12-slim

# Java(JVM) + g++ 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-21-jre-headless \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Debian 기반 OpenJDK 21 경로 기준 JAVA_HOME 설정
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app
COPY ./frontend ./frontend

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
