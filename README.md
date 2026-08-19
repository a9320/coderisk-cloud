# CodeRisk Cloud

> AI-powered code security API with local AMD GPU inference — zero source code leaves your infrastructure.

## Overview

CodeRisk Cloud is the cloud-native version of [CodeRisk Agent](https://github.com/a9320/code-risk-agent), wrapping the 4-Agent security analysis pipeline as a REST API service.

### Key Features

- **Local GPU Inference** — LLM runs on AMD GPU, source code never leaves your infrastructure
- **4-Agent Pipeline** — Static analysis → Semantic understanding → Deep verification → Report generation
- **Nutrient DWS Integration** — Professionally formatted, digitally signed PDF audit reports
- **GitHub Actions** — Push-to-analysis workflow with PR comment integration
- **SARIF Output** — IDE-compatible security findings format

## Quick Start

### Prerequisites

- Python 3.12+
- Redis
- CodeRisk Agent (included as dependency)

### Install

```bash
pip install -r requirements.txt
```

### Run

```bash
# Start Redis
redis-server &

# Start API Gateway
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Start Celery Worker
celery -A app.tasks worker --loglevel=info
```

### Docker

```bash
docker-compose up -d
```

## API Usage

### Submit Analysis

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "github",
    "repo_url": "https://github.com/user/repo",
    "branch": "main",
    "output_formats": ["json", "sarif", "pdf"]
  }'
```

### Check Status

```bash
curl http://localhost:8000/api/v1/tasks/cr-20260817-abc12345 \
  -H "Authorization: Bearer your-api-key"
```

### Get Report

```bash
curl http://localhost:8000/api/v1/reports/cr-20260817-abc12345 \
  -H "Authorization: Bearer your-api-key"
```

## Architecture

```
GitHub Action → Kong Gateway → FastAPI + Celery + Redis → CodeRisk Worker (AMD GPU) → Nutrient DWS (PDF)
```

## License

MIT
