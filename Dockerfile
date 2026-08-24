# CodeRisk Cloud — Unified Docker Image
# 支持模式：API / Worker / Dashboard（通过 docker-compose 覆盖 command）

FROM python:3.12-slim

LABEL maintainer="AI溢出安全实验室 <overflow@example.com>"
LABEL description="CodeRisk Cloud — AI-powered code security API"

WORKDIR /app

# 系统依赖：git（clone 仓库）、gcc（编译 Python 包）、ca-certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    gcc \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖（一次性安装，利用缓存层）
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# code-risk-agent（git submodule，构建前确保已初始化）
COPY code-risk-agent/ ./code-risk-agent/

# 预构建 CVE 数据库（Agent 3 交叉验证用）
RUN cd /app/code-risk-agent && \
    python scripts/download_cve_data.py || echo "CVE DB build skipped (non-fatal)"

# 应用代码
COPY app/ ./app/

# 运行时目录
RUN mkdir -p /app/reports /app/reports/uploads

# 环境变量默认值
ENV PYTHONPATH=/app:/app/code-risk-agent
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV REDIS_URL=redis://redis:6379/0
ENV REPORTS_DIR=/app/reports
ENV CODERISK_PATH=/app/code-risk-agent
ENV WORKER_CONCURRENCY=2

# 暴露端口（API + Dashboard）
EXPOSE 8000 8501

# 健康检查（API 模式）
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 默认启动 API（docker-compose 会覆盖为 worker/dashboard）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
