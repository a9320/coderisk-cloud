# CodeRisk Cloud — Docker Deployment Guide

> One-command startup of the full CodeRisk Cloud stack (API + Worker + Redis + Dashboard)

---

## Quick Start (30 seconds)

```bash
# 1. Clone the project
git clone https://github.com/a9320/coderisk-cloud.git
cd coderisk-cloud

# 2. Prepare the CodeRisk Agent source (required)
git clone https://github.com/a9320/code-risk-agent.git

# 3. Configure environment variables (copy the template and edit)
cp .env.example .env
# Edit .env, fill in NUTRIENT_DWS_API_KEY etc.

# 4. Start with one command
docker-compose up --build

# 5. Access the services
# API Docs:    http://localhost:8000/docs
# Dashboard:   http://localhost:8501
# Health:      http://localhost:8000/health
```

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Redis     │────▶│  API (FastAPI)│────▶│   Worker    │────▶│  Dashboard  │
│  (Broker)   │     │  Port 8000   │     │  (Celery)   │     │ Port 8501   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Nutrient   │
                    │  DWS API    │
                    └─────────────┘
```

| Service | Container name | Port | Description |
|---------|----------------|------|-------------|
| redis | coderisk-redis | — | Task queue + state cache |
| api | coderisk-api | 8000 | FastAPI REST API |
| worker | coderisk-worker | — | Celery 4-Agent analysis pipeline |
| dashboard | coderisk-dashboard | 8501 | Streamlit admin UI |

---

## Prerequisites

### Required
- Docker 20.10+ & Docker Compose 2.20+
- 4GB+ available memory
- CodeRisk Agent source (`git clone` into `./code-risk-agent`)

### Optional (GPU acceleration)
- AMD GPU + ROCm drivers (for Worker LLM acceleration)
- Or NVIDIA GPU + CUDA (requires modifying `docker-compose.gpu.yml`)

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Required
CODERISK_API_KEY=your-secure-api-key

# Optional (Nutrient PDF generation)
NUTRIENT_DWS_API_KEY=your-nutrient-key

# Optional (GitHub Webhook)
GITHUB_WEBHOOK_SECRET=your-webhook-secret

# Optional (Worker concurrency)
WORKER_CONCURRENCY=2

# Optional (GPU model override, AMD-specific)
HSA_OVERRIDE_GFX_VERSION=10.3.0
```

> ⚠️ **Security note:** Never commit `.env` to git. `.gitignore` is already configured to exclude it automatically.

---

## Running Modes

### Mode A: CPU mode (default, no GPU)

Suitable for quick evaluation by reviewers or GPU-less environments:

```bash
docker-compose up --build
```

- Worker runs static analysis on CPU (Agent 1)
- LLM semantic analysis (Agent 2/3) requires an external llama-server or falls back to degraded processing
- All features are available; analysis is slower

### Mode B: AMD GPU mode (development/production)

Suitable for your AMD GPU environment (192GB VRAM):

```bash
# Confirm ROCm is available
rocm-smi

# Start (loads the GPU extension config)
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

- Worker container mounts `/dev/kfd` and `/dev/dri`
- Automatically sets the `GGML_HIP=ON` environment variable
- llama.cpp uses AMD GPU acceleration for inference

### Mode C: API + Dashboard only (external Worker)

Suitable when the Worker runs on a separate GPU server:

```bash
# Start only API + Redis + Dashboard
docker-compose up api redis dashboard

# Start the Worker alone on the GPU server
celery -A app.tasks worker --loglevel=info
```

---

## Common Commands

```bash
# Run in background
docker-compose up -d

# View logs
docker-compose logs -f api
docker-compose logs -f worker

# Restart a single service
docker-compose restart worker

# Enter a container for debugging
docker-compose exec api bash
docker-compose exec worker bash

# Full cleanup
docker-compose down -v
```

---

## Verifying the Deployment

### 1. Health check
```bash
curl http://localhost:8000/health
```
Expected: `{"status": "ok", "checks": {"redis": true, ...}}`

### 2. Submit an analysis task
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Authorization: Bearer dev-key-change-in-production" \
  -d '{"source": "github", "repo_url": "https://github.com/a9320/code-risk-agent", "output_formats": ["json"]}'
```

### 3. ZIP upload
```bash
curl -X POST http://localhost:8000/api/v1/analyze/upload \
  -H "Authorization: Bearer dev-key-change-in-production" \
  -F "file=@test-code.zip"
```

### 4. Dashboard
Open http://localhost:8501, submit a repository URL and observe task progress.

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `Connection refused` to Redis | Redis not started or port conflict | `docker-compose ps` to check redis status |
| Worker logs show `ModuleNotFoundError` | `code-risk-agent` not mounted | Verify `./code-risk-agent` exists and is not empty |
| PDF generation fails | Nutrient key not configured or invalid | Check `NUTRIENT_DWS_API_KEY` in `.env` |
| GPU mode `rocm-smi` error | ROCm drivers not installed | Install ROCm on the host, or switch to CPU mode |
| ZIP upload 413 | File exceeds 100MB | Split the ZIP or adjust `client_max_body_size` |

---

## Production Deployment Recommendations

1. **Change the API key**: replace the default `dev-key-change-in-production` with a strong password
2. **Enable HTTPS**: use Traefik / Nginx reverse proxy + Let's Encrypt
3. **Persistent storage**: mount `./reports` to cloud storage (AWS EFS / NAS)
4. **Monitoring**: Prometheus + Grafana to collect Celery metrics
5. **Log aggregation**: ELK / Loki to collect multi-container logs

---

*CodeRisk Cloud v1.0.0 — AI Overflow Security Lab*
