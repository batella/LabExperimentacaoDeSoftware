FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

VOLUME ["/app/output"]

ENTRYPOINT ["python", "main.py"]
