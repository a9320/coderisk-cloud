# CodeRisk Cloud — Unified Docker Image
# Modes: API / Worker / Dashboard (overridden via docker-compose command)

FROM python:3.12-slim

LABEL maintainer="Overflow Security Lab <overflow@example.com>"
LABEL description="CodeRisk Cloud — AI-powered code security API"

WORKDIR /app

# System deps: git (clone repos), gcc (build Python packages), ca-certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    gcc \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python deps (installed once, leverages cache layers)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# code-risk-agent (git submodule, ensure initialized before build)
COPY code-risk-agent/ ./code-risk-agent/

# CVE database: skipped at build time (download too slow), built on demand at runtime
# RUN cd /app/code-risk-agent && \
#     python scripts/download_cve_data.py || echo "CVE DB build skipped (non-fatal)"
RUN echo "CVE DB build skipped (will build at runtime if needed)"

# Application code
COPY app/ ./app/

# Runtime directory
RUN mkdir -p /app/reports /app/reports/uploads

# Environment variable defaults
ENV PYTHONPATH=/app:/app/code-risk-agent
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV REDIS_URL=redis://redis:6379/0
ENV REPORTS_DIR=/app/reports
ENV CODERISK_PATH=/app/code-risk-agent
ENV WORKER_CONCURRENCY=2

# Expose ports (API + Dashboard)
EXPOSE 8000 8501

# Health check (API mode)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Default CMD runs API (docker-compose overrides to worker/dashboard)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
