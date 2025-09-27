FROM python:3.11-slim

# Install system deps (if needed later)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt