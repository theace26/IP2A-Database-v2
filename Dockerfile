# ============================
# 1) BUILDER
# ============================
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ============================
# 2) RUNTIME
# ============================
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python libs
COPY --from=builder /usr/local /usr/local

# Copy application
COPY src ./src
COPY alembic.ini .

# Create uploads directory
RUN mkdir -p /app/uploads

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
