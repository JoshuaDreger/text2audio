# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

# System deps (ffmpeg for audio, espeak-ng for pyttsx3 on Linux, poppler & tesseract optional if you OCR PDFs)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    espeak-ng ffmpeg libasound2 libespeak-ng1 \
    poppler-utils tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Avoid Python .pyc, ensure logs flush
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Streamlit: listen on all interfaces, no browser auto-open
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501

# Workdir
WORKDIR /app

# Copy only dependency files first (better build caching)
COPY requirements.txt /app/requirements.txt

# Install deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app

# Install your package (editable-like in container)
RUN pip install --no-cache-dir -e .

# Entrypoint script to launch both API and Streamlit
RUN chmod +x /app/entrypoint.sh

# Expose API and Streamlit ports
EXPOSE 8000 8501

# Default command: launch the entrypoint script
CMD ["/app/entrypoint.sh"]
