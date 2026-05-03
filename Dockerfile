FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y \
    gcc make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY decoder/ ./decoder/
RUN cd decoder && make

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /app/decoder/goertzel.so ./decoder/
COPY app/ ./app/
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
CMD ["python", "app/app.py"]