FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code.
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

# Persistent data (sqlite db + uploads + reports) lives under /app/data,
# which is bind-mounted to ./data on the host via docker-compose.
RUN mkdir -p /app/data/uploads /app/data/reports

EXPOSE 8000

# Apply migrations (alembic/env.py reads DATABASE_URL from settings), then serve.
# On first boot init_db() seeds demo data into the empty database.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
