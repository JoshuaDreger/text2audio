# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

# System deps + bash (+ optional dos2unix to normalize line endings)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    bash ca-certificates \
    espeak-ng ffmpeg libasound2 libespeak-ng1 \
    poppler-utils tesseract-ocr \
    dos2unix \
    libespeak1 espeak \
 && rm -rf /var/lib/apt/lists/*


ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app

RUN mkdir -p /root/.streamlit
COPY config.toml /root/.streamlit/config.toml

# Normalize entrypoint line endings in case they came from Windows
RUN dos2unix /app/entrypoint.sh || true

# Install your package
RUN pip install --no-cache-dir -e .

# Ensure executable bit
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000 8501

# Use bash explicitly
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
