# CodeRisk Cloud — Full Project Documentation

> DevNetwork [API + Cloud + AI] Hackathon 2026 entry
> AI Overflow Security Lab (Overflow Security Lab)
> Last updated: 2026-08-19

---

## 1. Project Overview

**CodeRisk Cloud** is the Cloud-Native API version of [CodeRisk Agent](https://github.com/a9320/code-risk-agent), wrapping the 4-Agent code security analysis pipeline as a REST API service.

### Core Value Propositions
- **Local GPU Inference** — the LLM runs on AMD GPU, source code never leaves your infrastructure
- **4-Agent Pipeline** — static analysis → semantic understanding → deep verification → report generation
- **Nutrient DWS** — professional PDF audit reports + SHA-256 digital signatures
- **Multi-format Output** — JSON / SARIF / PDF
- **GitHub Webhook** — automatic analysis on push

### Tech Stack
| Component | Technology |
|-----------|------------|
| API framework | FastAPI 0.141+ |
| Task queue | Celery 5.6+ (Redis broker) |
| Cache / messaging | Redis 5.0+ |
| Data validation | Pydantic 2.13+ |
| HTTP client | httpx 0.27+ |
| PDF generation | Nutrient DWS API |
| Dashboard | Streamlit 1.30+ |
| Runtime | Python 3.12+ |

---

## 2. Directory Structure

```
coderisk-cloud/
├── app/
│   ├── __init__.py          (1 line)     Package initialization
│   ├── config.py            (49 lines)   Configuration management
│   ├── main.py              (375 lines)  FastAPI main app + 8 endpoints
│   ├── tasks.py             (443 lines)  Celery tasks + 4-Agent pipeline
│   ├── models.py            (118 lines)  Pydantic data models
│   ├── nutrient_client.py   (429 lines)  Nutrient DWS PDF client
│   └── dashboard.py         (370 lines)  Streamlit Dashboard
├── bruno/                         Bruno API test collection (9 files)
│   ├── environments/local.bru
│   ├── analyze/
│   │   ├── submit-github.bru
│   │   ├── submit-invalid.bru
│   │   ├── invalid-api-key.bru
│   │   └── missing-auth.bru
│   ├── tasks/
│   │   ├── get-task-status.bru
│   │   └── not-found.bru
│   ├── reports/
│   │   └── get-report.bru
│   └── health/
│       └── health-check.bru
├── reports/                        Report output directory (runtime)
│   └── uploads/                 Temporary storage for ZIP uploads
├── backups/v1/                    v1 code backup
├── tests/                         Test files
├── .env.example                   Environment variable template
├── .env                           Environment variables (local)
├── requirements.txt               Python dependencies
├── README.md                      Project description
└── Project-Documentation.md
```

**Total code size:** 7 Python files, 1,785 lines

---

## 3. Environment Configuration

### 3.1 Environment Variables (.env)

```env
# Redis (Celery Broker + Backend)
REDIS_URL=redis://localhost:6379/0

# API authentication
CODERISK_API_KEY=dev-key-change-in-production

# CodeRisk Agent path (auto-detection priority: env var > ../code-risk-agent > /app/code-risk-agent)
CODERISK_PATH=/app/code-risk-agent

# Nutrient DWS (PDF generation)
NUTRIENT_DWS_API_KEY=<your-nutrient-api-key>
NUTRIENT_DWS_API_URL=https://api.nutrient.io/build

# GitHub Webhook (optional)
GITHUB_WEBHOOK_SECRET=

# Report storage
REPORTS_DIR=./reports

# Worker concurrency
WORKER_CONCURRENCY=2
```

### 3.2 Python Dependencies (requirements.txt)

```
fastapi>=0.115.0
uvicorn[standard]>=0.34.0
celery[redis]>=5.4.0
redis>=5.0.0
pydantic>=2.0.0
httpx>=0.27.0
python-multipart>=0.0.9
streamlit>=1.30.0
```

### 3.3 Installation & Startup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Redis
redis-server &

# 3. Start the API service
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 4. Start the Celery worker (separate terminal)
celery -A app.tasks worker --loglevel=info

# 5. Start the Dashboard (optional, separate terminal)
streamlit run app/dashboard.py --server.port 8501
```

---

## 4. API Endpoint Documentation

### 4.1 POST /api/v1/analyze — GitHub repository analysis

**Auth:** Bearer Token

**Request body:**
```json
{
  "source": "github",
  "repo_url": "https://github.com/user/repo",
  "branch": "main",
  "output_formats": ["json", "sarif", "pdf"],
  "callback_url": null
}
```

**Request fields:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| source | string | No | "direct_upload" | Code source: github / zip / direct_upload |
| repo_url | string | Required when source=github | null | GitHub repository URL |
| branch | string | No | "main" | Git branch |
| output_formats | string[] | No | ["json", "sarif"] | Output formats: json / sarif / pdf |
| callback_url | string | No | null | Callback URL when analysis completes |

**Success response (200):**
```json
{
  "task_id": "cr-20260819-ed5ccb70",
  "status": "pending",
  "message": "Analysis task created. Use GET /api/v1/tasks/cr-20260819-ed5ccb70 to check progress."
}
```

**Error responses:**
| Status code | Scenario |
|-------------|----------|
| 400 | source=github but repo_url missing |
| 401 | Missing Authorization header |
| 403 | Invalid API key |

---

### 4.2 POST /api/v1/analyze/upload — ZIP upload analysis

**Auth:** Bearer Token
**Content-Type:** multipart/form-data

**Form fields:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| file | File | Yes | — | ZIP file (≤ 100MB) |
| output_formats | string | No | "json,sarif,pdf" | Comma-separated output formats |
| callback_url | string | No | null | Callback URL |

**Security validation:**
- ✅ File extension validation (.zip)
- ✅ File size limit (100MB)
- ✅ Extracted size limit (100MB)
- ✅ File count limit (≤ 10,000)
- ✅ Path traversal protection (rejects `../`)

**Success response (200):**
```json
{
  "task_id": "cr-20260819-ed5ccb70",
  "status": "pending",
  "message": "ZIP upload accepted. Analysis task created. Use GET /api/v1/tasks/cr-20260819-ed5ccb70 to check progress."
}
```

**Error responses:**
| Status code | Scenario |
|-------------|----------|
| 400 | Non-ZIP file / invalid output format / missing filename |
| 401 | Missing Authorization header |
| 413 | File exceeds 100MB |

---

### 4.3 GET /api/v1/tasks/{task_id} — Query task status

**Auth:** Bearer Token

**Success response (200):**
```json
{
  "task_id": "cr-20260819-ed5ccb70",
  "status": "completed",
  "progress": 100,
  "agent_status": {
    "agent_1_static": "completed",
    "agent_2_semantic": "completed",
    "agent_3_verifier": "completed",
    "agent_4_report": "completed"
  },
  "created_at": "2026-08-19T12:02:53",
  "updated_at": "2026-08-19T12:03:45",
  "error": null
}
```

**Task state flow:**
```
pending → analyzing → verifying → generating_report → completed
                                                    → failed
```

**Error responses:**
| Status code | Scenario |
|-------------|----------|
| 401 | Authentication failed |
| 404 | task_id does not exist |

---

### 4.4 GET /api/v1/reports/{task_id} — Get analysis report

**Auth:** Bearer Token (must use same API key as the submitting task; reports are isolated)

**Precondition:** Task status is `completed`

**Success response (200):**
```json
{
  "task_id": "cr-20260819-ed5ccb70",
  "summary": {
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 1,
    "info": 0
  },
  "findings": [
    {
      "type": "command_injection",
      "severity": "critical",
      "title": "OS Command Injection via os.system()",
      "file": "src/vuln.py",
      "line": 5,
      "description": "...",
      "cwe": "CWE-78"
    }
  ],
  "report_urls": {
    "json": "/reports/cr-20260819-ed5ccb70/report.json",
    "sarif": "/reports/cr-20260819-ed5ccb70/report.sarif",
    "pdf": "/reports/cr-20260819-ed5ccb70/report.pdf"
  },
  "digital_signature": "sha256:a1b2c3d4...",
  "completed_at": "2026-08-19T12:03:45"
}
```

**Error responses:**
| Status code | Scenario |
|-------------|----------|
| 400 | Task not completed |
| 401 | Authentication failed |
| 403 | API key does not match the submitter (report isolation) |
| 404 | Task or report does not exist |

---

### 4.5 GET /api/v1/reports/{task_id}/pdf — Download PDF report

**Auth:** Bearer Token (report isolation)

**Success response:** PDF file stream (`application/pdf`)

**Error responses:**
| Status code | Scenario |
|-------------|----------|
| 403 | API key mismatch |
| 404 | PDF does not exist (possibly PDF format was not requested) |

---

### 4.6 POST /api/v1/webhooks/github — GitHub Webhook

**Auth:** HMAC-SHA256 signature verification (`X-Hub-Signature-256` header)

**Trigger:** GitHub Push event

**Request body:** GitHub webhook payload (automatically parses `repository.clone_url` and `ref`)

**Success response (200):**
```json
{
  "task_id": "cr-20260819-xxxxxxxx",
  "status": "pending",
  "message": "Webhook analysis started"
}
```

**Security features:**
- HMAC-SHA256 signature verification (anti-forgery)
- Automatic branch name extraction
- Allowlisted domains (github.com / gitlab.com / gitee.com)

---

### 4.7 GET /health — Health check

**No auth required**

**Success response (200):**
```json
{
  "status": "ok",
  "checks": {
    "redis": true,
    "celery_worker": true,
    "gpu": true
  },
  "version": "1.0.0"
}
```

**Degraded response (503):**
```json
{
  "status": "degraded",
  "checks": {
    "redis": true,
    "celery_worker": false,
    "gpu": false
  },
  "version": "1.0.0"
}
```

---

### 4.8 GET / — Root path

**No auth required**

**Response:**
```json
{
  "name": "CodeRisk Cloud",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

---

## 5. 4-Agent Analysis Pipeline

```
┌──────────────────────────────────────────────────────────────┐
│                    Celery Task Worker                         │
├──────────────┬──────────────┬──────────────┬─────────────────┤
│  Agent 1     │  Agent 2     │  Agent 3     │  Agent 4        │
│  Static      │  Semantic    │  Deep        │  Report         │
│  Analysis    │  Analysis    │  Verification│  Generation     │
│  (Semgrep)   │  (LLM)       │  (Cross-     │  (JSON/PDF)     │
│              │              │  validation) │                 │
├──────────────┼──────────────┼──────────────┼─────────────────┤
│ regex scan   │ Qwen2.5-Coder│ false-       │ JSON output     │
│ Semgrep rules│ semantic     │ positive     │ SARIF output    │
│ CWE mapping  │ understanding│ filtering    │ PDF (Nutrient)  │
│              │ logic vuln   │ confidence   │                 │
│              │ detection    │ assessment   │                 │
│              │              │ cross-       │                 │
│              │              │ referencing  │                 │
└──────┬───────┴──────┬───────┴──────┬───────┴────────┬────────┘
       │              │              │                │
       ▼              ▼              ▼                ▼
  Static findings → Merge/dedup → Verified results → Final report
```

### Progress Tracking

| Stage | Progress | agent_status |
|-------|----------|-------------|
| Prepare code | 5% | agent_1_static: "preparing" |
| Static + semantic in parallel | 15-55% | agent_1/2: "running" → "completed" |
| Deep verification | 75-90% | agent_3: "running" → "completed" |
| Report generation | 95-100% | agent_4: "running" → "completed" |

---

## 6. Nutrient DWS Integration

### PDF Report Features
- Dark gradient header (#0f0c29 → #302b63 → #24243e)
- 5-color severity stat cards (Critical/High/Medium/Low/Info)
- Findings list: left color bar + severity tag + file location + description
- SHA-256 digital signature embedded (green signature block at bottom of report)
- Footer copyright: CodeRisk Cloud © 2026 | AI Overflow Security Lab

### API Call
```
POST https://api.nutrient.io/build
Authorization: Bearer <Processor API Key>
Content-Type: multipart/form-data

instructions: {"parts":[{"html":"report.html"}]}
report.html: <HTML content>
```

### API Key
```
Configured in .env: NUTRIENT_DWS_API_KEY=<your-nutrient-api-key>
⚠️ Do not write the key in plaintext in docs or commit it to git
```

---

## 7. Data Models

### Request Models

```python
class CodeSource(str, Enum):
    GITHUB = "github"
    ZIP = "zip"
    DIRECT_UPLOAD = "direct_upload"

class AnalyzeRequest(BaseModel):
    source: CodeSource = "direct_upload"
    repo_url: Optional[str] = None
    branch: str = "main"
    callback_url: Optional[str] = None
    output_formats: list[str] = ["json", "sarif"]
```

### Response Models

```python
class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    ANALYZING = "analyzing"
    VERIFYING = "verifying"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    FAILED = "failed"

class AnalyzeResponse(BaseModel):
    task_id: str
    status: TaskStatus
    message: str

class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    progress: int          # 0-100
    agent_status: dict
    created_at: Optional[str]
    updated_at: Optional[str]
    error: Optional[str]

class ReportResponse(BaseModel):
    task_id: str
    summary: FindingSummary
    findings: list[dict]
    report_urls: ReportURLs
    digital_signature: Optional[str]
    completed_at: Optional[str]
```

---

## 8. Security Features

| Feature | Implementation |
|---------|----------------|
| API authentication | Bearer Token + `hmac.compare_digest` (timing-attack safe) |
| Report isolation | Bound to SHA-256 hash of API key; different keys cannot access each other |
| GitHub Webhook | HMAC-SHA256 signature verification |
| ZIP upload security | Extension validation + 100MB limit + extracted-size limit + file-count limit + path traversal protection |
| Git clone allowlist | Only github.com / gitlab.com / gitee.com |
| Injection prevention | git clone parameters allowlisted; user input is never concatenated |
| Temp file cleanup | `finally` block automatically cleans up work_dir + ZIP files |
| Source privacy | LLM runs local inference; source code never leaves your infrastructure |

---

## 9. Bruno Test Collection

Run with [Bruno](https://www.usebruno.com/); environment configured in `bruno/environments/local.bru`.

### Test Case List

| File | Method | Endpoint | Test content |
|------|--------|----------|-------------|
| health-check.bru | GET | /health | Health check |
| submit-github.bru | POST | /api/v1/analyze | GitHub repository submission |
| submit-invalid.bru | POST | /api/v1/analyze | Invalid request |
| missing-auth.bru | POST | /api/v1/analyze | Missing auth → 401 |
| invalid-api-key.bru | POST | /api/v1/analyze | Wrong key → 403 |
| get-task-status.bru | GET | /api/v1/tasks/{id} | Query task status |
| not-found.bru | GET | /api/v1/tasks/{id} | Not exist → 404 |
| get-report.bru | GET | /api/v1/reports/{id} | Get report |

---

## 10. Dashboard (Streamlit)

### Startup
```bash
streamlit run app/dashboard.py --server.port 8501
```

### Features
- 🔍 **Submit Analysis** — enter GitHub repo URL + branch + output formats
- 📋 **Task List** — real-time status refresh, progress bars, expandable Agent details
- 📊 **Report Preview** — severity stat cards + Findings table + download buttons
- 🔏 **Digital Signature** — SHA-256 integrity verification display

### Environment Variables
```env
CODERISK_API_URL=http://localhost:8000
CODERISK_API_KEY=dev-key-change-in-production
```

---

## 11. Development History

### Day 1 (2026-08-17) ✅
- FastAPI + Celery + Redis skeleton (written by Kimi, 796 lines)
- v2 optimization: 14 fixes (Kimi review)
- Milestone M1 completed 5 days early

### Day 2 (2026-08-18) ✅
- Nutrient DWS real API integration (lolo rewrote nutrient_client.py)
- Kimi delivered: dashboard.py + Bruno tests + demo script
- Milestone M2 completed 7 days early

### Day 3 (2026-08-19) ✅
- ZIP file upload endpoint (Kimi wrote, lolo reviewed and integrated)
- Security protections: ZIP bomb + path traversal + file-count limit
- End-to-end tests 5/5 passing

### Planned
- [ ] Docker Compose one-click deployment
- [ ] GitHub Actions CI/CD
- [ ] Demo video recording
- [ ] DevPost submission materials

---

## 12. Endpoint Quick Reference

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/v1/analyze | Bearer | GitHub repository analysis |
| POST | /api/v1/analyze/upload | Bearer | ZIP upload analysis |
| GET | /api/v1/tasks/{id} | Bearer | Task status |
| GET | /api/v1/reports/{id} | Bearer | Analysis report |
| GET | /api/v1/reports/{id}/pdf | Bearer | PDF download |
| POST | /api/v1/webhooks/github | HMAC | GitHub Webhook |
| GET | /health | None | Health check |
| GET | / | None | Root path |
| GET | /docs | None | Swagger UI |
| GET | /redoc | None | ReDoc |

---

*CodeRisk Cloud v1.0.0 — AI Overflow Security Lab*
*DevNetwork [API + Cloud + AI] Hackathon 2026*
