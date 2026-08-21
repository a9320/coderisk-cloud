# DevPost 项目页 — CodeRisk Cloud

---

## Project Name
**CodeRisk Cloud**

## Tagline
4-Agent AI security pipeline with AMD GPU local inference — zero source code leaves your infrastructure.

## Elevator Pitch（<500 字符）

Development teams merge dozens of times per day, but security review still happens at release time — too late. Traditional SAST tools drown engineers in false positives (>70%). LLM-based tools are smart but can't explain *why* something is a vulnerability.

**CodeRisk Cloud** solves this with a **4-Agent AI pipeline** that runs entirely on your infrastructure (AMD GPU local inference — source code never leaves your servers). It produces **tamper-evident PDF audit reports** via Nutrient DWS, complete with SHA-256 digital signatures.

Zero config: `docker-compose up` and you're running. Zero risk: your code stays local.

---

## The Problem

| Pain Point | Why It Hurts |
|-----------|-------------|
| **Source code leaves your infrastructure** | Cloud-based security scanners require uploading proprietary code to third-party servers. Compliance teams hate this. |
| **SAST tools have >70% false positive rate** | Developers stop trusting security alerts. Alert fatigue kills security culture. |
| **Security review happens at release time** | Finding a vulnerability in production costs 100x more than finding it in development. |
| **No audit trail for compliance** | SOC 2 / ISO 27001 auditors need tamper-evident reports. Screenshots of CLI output don't count. |

---

## The Solution

### 4-Agent Pipeline

```
Code Input -> Agent 1 (Static) -> Agent 2 (Semantic) -> Agent 3 (Verify) -> Agent 4 (Report)
                AST/Semgrep          LLM Understanding      Cross-check/CVE       JSON/SARIF/PDF
```

| Agent | Role | What It Does |
|-------|------|-------------|
| **Agent 1 — Static Analysis** | Foundation | AST parsing, Semgrep rules, taint analysis. Finds the obvious stuff fast. |
| **Agent 2 — Semantic Analysis** | Intelligence | LLM understands code context, call chains, data flow. Catches logic vulnerabilities that static analysis misses. |
| **Agent 3 — Deep Verifier** | Quality Gate | Cross-validates Agent 1 & 2 results, filters false positives, queries CVE database, scans dependencies. |
| **Agent 4 — Report Generator** | Output | Produces JSON (structured), SARIF 2.1 (standard), and **Nutrient DWS PDF with SHA-256 signature** (compliance-ready). |

**Average pipeline time: 5.4 seconds.**

### Cloud-Native Architecture

- **FastAPI** gateway with Bearer Token auth and rate limiting
- **Celery + Redis** async task queue — submit analysis without blocking
- **Docker Compose** single-command deployment (CPU or GPU mode)
- **Web Dashboard** for real-time progress and historical tasks

---

## Key Differentiators

### 1. Nutrient DWS — Tamper-Evident PDF Reports

> "Where does DWS do the heavy lifting?"

**Nutrient DWS powers our deterministic PDF report generation and SHA-256 digital signatures** — turning raw AI vulnerability findings into tamper-evident, regulator-ready audit documents.

- HTML report template (5 sections: Summary -> Findings -> Details -> Recommendations -> Appendix)
- Nutrient DWS API converts to professional PDF
- Local SHA-256 signature ensures report integrity
- Graceful degradation: if no API key configured, skips PDF without breaking core analysis

### 2. AMD GPU Local Inference — Zero Data Exfiltration

- Agent 2 (Semantic Analysis) runs LLM inference via **llama.cpp server** on local AMD ROCm GPU
- Source code never leaves your infrastructure
- Compliance-friendly: no third-party data processing agreements needed

### 3. SARIF 2.1.0 Output

Industry-standard format. Drop the output into any SARIF-compatible tool (GitHub Advanced Security, VS Code SARIF viewer, etc.).

### 4. Zero-Config Experience

```bash
git clone --recursive https://github.com/a9320/coderisk-cloud
cd coderisk-cloud
docker-compose up --build
# API: http://localhost:8000/docs
# Dashboard: http://localhost:8501
```

No API keys needed for basic operation. The `/demo` endpoint returns 9 pre-loaded vulnerability samples instantly.

---

## Try It in 30 Seconds

### Option A: Zero-Config Demo
```bash
curl http://localhost:8000/demo
```
Returns 9 real vulnerability findings (SQL injection, XSS, hardcoded secrets, etc.) — zero wait, zero setup.

### Option B: Analyze a GitHub Repo
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Authorization: Bearer dev-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{"source": "github", "repo_url": "https://github.com/a9320/coderisk-cloud"}'
```
Response:
```json
{
  "task_id": "cr-20260820-3288f97c",
  "status": "pending",
  "message": "Analysis queued successfully"
}
```

### Option C: Full Stack (Docker)
```bash
docker-compose up --build
```
Spins up 4 services: Redis, FastAPI, Celery Worker, Web Dashboard.

---

## Architecture

![Architecture](docs/architecture.svg)

**Data Flow:**
1. **Input** — GitHub Webhook / REST API / ZIP Upload / Web Dashboard
2. **Gateway** — FastAPI validates auth, routes to Celery
3. **Queue** — Celery distributes tasks to workers via Redis
4. **Engine** — 4-Agent pipeline executes sequentially (avg 5.4s)
5. **Output** — JSON + SARIF + Nutrient DWS Signed PDF
6. **Feedback** — Results posted back to GitHub PR comments via Webhook

---

## Evidence

All claims are reproducible. See `evidence/` directory:

| File | Proof |
|------|-------|
| `benchmark-results.json` | API p50 12ms, 4-Agent pipeline 5.4s avg, 100 concurrent 99% success |
| `test-coverage.json` | 8 files, 76.3% coverage (models/config/demo_fixture at 100%) |
| `api-test-results.json` | **9/9 Bruno tests pass** in 3.2s |
| `docker-health.json` | 4 containers all healthy |
| `security-scan.json` | **0 critical/high/medium CVEs**, 0 hardcoded secrets |
| `bruno-runner.png` | Collection Runner screenshot — all green |

---

## Built With

- **FastAPI** — API gateway
- **Celery + Redis** — Async task queue
- **Python 3.12** — Core language
- **AMD ROCm + llama.cpp** — Local GPU inference
- **Semgrep + Tree-sitter** — Static analysis engine
- **Nutrient DWS** — PDF generation & digital signatures
- **Web Dashboard** — Real-time progress UI
- **Bruno** — API testing (9 test cases)
- **Docker + Docker Compose** — Deployment
- **GitHub Actions** — CI/CD

---

## What's Next

| Phase | Feature | Impact |
|-------|---------|--------|
| **Short-term** | GitHub Action Marketplace plugin | Push-to-scan in any repo |
| **Short-term** | VS Code Extension | Inline vulnerability highlighting |
| **Mid-term** | Multi-language support (Go, Rust, Java) | Broader codebase coverage |
| **Mid-term** | Private repository OAuth | Enterprise GitHub integration |
| **Long-term** | Continuous learning from user feedback | Agent 3 false-positive rate <10% |

---

## Team

**AI溢出安全实验室** — Building security tools that engineers actually trust.

---

*Built for DevNetwork 2026. From "a tool that works" to "a system you can trust."*
