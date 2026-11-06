FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PAX_DB_PATH=/app/data/pax_modernica.sqlite3

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
