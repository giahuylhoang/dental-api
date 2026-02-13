# Dockerfile for Calendar API Service
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Railway sets PORT; default 8000 for local runs
ENV PORT=8000
EXPOSE 8000

# Health check (uses PORT)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Run API (run_api.py binds to PORT and survives import errors)
CMD ["python", "run_api.py"]
