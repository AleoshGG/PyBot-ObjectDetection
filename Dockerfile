# Stage 1: Build stage with build-essentials to compile dependencies
FROM python:3.9.18-slim as builder

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt


# Stage 2: Final production image
FROM python:3.9.18-slim

# Set metadata labels
LABEL maintainer="Gemini"
LABEL description="Optimized Docker image for PyBot-ObjectDetection FastAPI service."

# Create a non-root user for security
RUN useradd --create-home appuser
WORKDIR /home/appuser/app

# Install required system libraries for OpenCV and other packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from the builder stage
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Change ownership of the app directory
RUN chown -R appuser:appuser /home/appuser/app

# Switch to the non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 1200

# Command to run the application using Uvicorn
# Using --workers 1 as recommended in app.py, and letting the internal thread pool handle concurrency.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "1200", "--workers", "1"]
