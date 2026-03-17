FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p data db web

EXPOSE 8002

CMD ["sh", "-c", "uvicorn api.server:app --host 0.0.0.0 --port ${PORT:-8002}"]
