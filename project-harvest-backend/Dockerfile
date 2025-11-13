# ============================================
# Project Harvest Backend - Dockerfile
# ============================================
# This file contains instructions to build our Python application container

# Start from official Python 3.11 image (slim = smaller size)
FROM python:3.11-slim

# Set working directory inside container
# All commands will run from /app
WORKDIR /app

# ============================================
# Install system dependencies
# ============================================
# Some Python packages need these to compile
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# Install Python dependencies
# ============================================
# Copy requirements.txt first (Docker layer caching optimization)
# If requirements.txt doesn't change, this layer is cached
COPY requirements.txt .

# Install all Python packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# Copy application code
# ============================================
COPY app/ ./app/

# Create data directories
RUN mkdir -p data/raw data/processed data/models

# ============================================
# Expose port 8000
# ============================================
# This is the port FastAPI will run on
EXPOSE 8000

# ============================================
# Default command
# ============================================
# Run FastAPI with uvicorn
# --host 0.0.0.0 = listen on all network interfaces
# --port 8000 = listen on port 8000
# --reload = auto-restart when code changes (dev mode)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

