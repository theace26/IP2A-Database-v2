FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ../requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

CMD ["/bin/bash", "-c", "python src/scripts/preflight.py && exec uvicorn src.main:app --host 0.0.0.0 --port 8000"]
