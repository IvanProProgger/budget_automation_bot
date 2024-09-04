FROM python:3.12.0 AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

FROM python:3.12.0-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /app /app
COPY . .

RUN rm -rf /app/__pycache__*

CMD ["python", "main.py"]