# -------------------------------------------------------
# Base image
# -------------------------------------------------------
FROM python:3.9.18-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

LABEL maintainer="Gemini"
LABEL description="FastAPI + YOLO (Ultralytics 8.0.20) - CPU optimized"

# -------------------------------------------------------
# System dependencies
# -------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------------
# App user
# -------------------------------------------------------
RUN useradd --create-home appuser
WORKDIR /home/appuser/app

# -------------------------------------------------------
# Install Python dependencies
# -------------------------------------------------------
COPY requirements.txt ./

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.0.1 torchvision==0.15.2 && \
    pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------------
# Copy source code
# -------------------------------------------------------
COPY --chown=appuser:appuser . .

RUN chown -R appuser:appuser /home/appuser/app
USER appuser

# -------------------------------------------------------
# Expose port
# -------------------------------------------------------
EXPOSE 1200

# -------------------------------------------------------
# Start API
# -------------------------------------------------------
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "1200", "--workers", "1"]
