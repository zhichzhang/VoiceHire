# syntax=docker/dockerfile:1

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System packages that are commonly needed by your backend + LiveKit worker stack
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    ffmpeg \
    libportaudio2 \
    portaudio19-dev \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for better layer caching
COPY app/server/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

# Copy the backend source code
COPY app /app/app
COPY packages /app/packages

# Backend API port
EXPOSE 8000

# Default command = FastAPI API server
CMD ["uvicorn", "app.server.main:app", "--host", "0.0.0.0", "--port", "8000"]