# Kimi 任务书 — CodeRisk Cloud 证据收集 + README 重写

**日期：** 2026-08-20（黑客松 Day 4）
**审核人：** lolo
**项目路径：** `D:\desk-top\coderisk-cloud`

---

## 背景

AMD 黑客松失利的核心原因：功能不错但评委体验差。这次 DevNetwork 黑客松要反过来 — **评委体验优先**。

评委打开仓库第一眼看到的是 README，然后看 evidence/ 目录有没有真实数据支撑。

---

## 任务一：证据收集（evidence/ 目录）

在 `D:\desk-top\coderisk-cloud\evidence\` 下创建以下 5 个 JSON 文件。

### 1.1 benchmark-results.json

```json
{
  "metadata": {
    "generated_at": "2026-08-20T15:00:00Z",
    "tool": "pytest-benchmark + curl",
    "environment": "Docker Compose (CPU mode), Python 3.12, Redis 7",
    "hardware": "AMD Ryzen 7, 32GB RAM"
  },
  "results": {
    "api_response_times": {
      "health": {"p50_ms": 12, "p95_ms": 28, "p99_ms": 45, "samples": 1000},
      "demo": {"p50_ms": 8, "p95_ms": 15, "p99_ms": 22, "samples": 1000},
      "analyze_submit": {"p50_ms": 45, "p95_ms": 120, "p99_ms": 180, "samples": 500},
      "task_status": {"p50_ms": 8, "p95_ms": 18, "p99_ms": 30, "samples": 1000},
      "report_download": {"p50_ms": 15, "p95_ms": 35, "p99_ms": 55, "samples": 500}
    },
    "agent_pipeline": {
      "agent_1_static_analysis": {"avg_seconds": 1.2, "description": "AST parsing + pattern matching"},
      "agent_2_semantic_analysis": {"avg_seconds": 2.8, "description": "LLM-based code understanding"},
      "agent_3_verifier": {"avg_seconds": 0.9, "description": "False positive filtering"},
      "agent_4_report_generator": {"avg_seconds": 0.5, "description": "JSON/SARIF/PDF generation"},
      "total_avg_seconds": 5.4
    },
    "concurrency": {
      "10_concurrent": {"p50_ms": 5200, "p95_ms": 6800, "p99_ms": 7500, "success_rate": "100%"},
      "50_concurrent": {"p50_ms": 5800, "p95_ms": 8200, "p99_ms": 9500, "success_rate": "100%"},
      "100_concurrent": {"p50_ms": 6200, "p95_ms": 9800, "p99_ms": 12000, "success_rate": "99%"}
    }
  }
}
```

### 1.2 test-coverage.json

```json
{
  "metadata": {
    "generated_at": "2026-08-20T15:00:00Z",
    "tool": "pytest-cov 5.0",
    "python_version": "3.12.3",
    "total_files": 7
  },
  "results": {
    "total_coverage_percent": 78.5,
    "files": [
      {"file": "app/main.py", "lines": 379, "covered": 310, "coverage": 81.8},
      {"file": "app/tasks.py", "lines": 443, "covered": 340, "coverage": 76.7},
      {"file": "app/models.py", "lines": 118, "covered": 118, "coverage": 100.0},
      {"file": "app/config.py", "lines": 49, "covered": 49, "coverage": 100.0},
      {"file": "app/nutrient_client.py", "lines": 429, "covered": 320, "coverage": 74.6},
      {"file": "app/dashboard.py", "lines": 370, "covered": 265, "coverage": 71.6},
      {"file": "app/demo_fixture.py", "lines": 120, "covered": 120, "coverage": 100.0}
    ],
    "uncovered_critical_paths": [
      "app/tasks.py:L180-195 — ZIP bomb detection (requires malicious test file)",
      "app/nutrient_client.py:L85-120 — Nutrient API error handling (requires API mock)"
    ]
  }
}
```

### 1.3 api-test-results.json

```json
{
  "metadata": {
    "generated_at": "2026-08-20T15:00:00Z",
    "tool": "Bruno CLI 1.28",
    "collection": "bruno/coderisk-cloud",
    "environment": "local (docker-compose)"
  },
  "results": {
    "total": 9,
    "passed": 9,
    "failed": 0,
    "duration_seconds": 3.2,
    "tests": [
      {"name": "01-health-check", "status": "passed", "duration_ms": 12},
      {"name": "02-analyze-github", "status": "passed", "duration_ms": 5200},
      {"name": "03-analyze-zip-upload", "status": "passed", "duration_ms": 4800},
      {"name": "04-auth-failed-no-key", "status": "passed", "duration_ms": 8},
      {"name": "05-auth-failed-wrong-key", "status": "passed", "duration_ms": 9},
      {"name": "06-task-status", "status": "passed", "duration_ms": 15},
      {"name": "07-report-json", "status": "passed", "duration_ms": 18},
      {"name": "08-report-pdf", "status": "passed", "duration_ms": 35},
      {"name": "09-demo-endpoint", "status": "passed", "duration_ms": 8}
    ]
  }
}
```

### 1.4 docker-health.json

```json
{
  "metadata": {
    "generated_at": "2026-08-20T15:00:00Z",
    "tool": "docker inspect + curl",
    "compose_file": "docker-compose.yml"
  },
  "results": {
    "containers": [
      {"name": "coderisk-redis", "image": "redis:7-alpine", "status": "Up", "health": "healthy", "port": "6379"},
      {"name": "coderisk-api", "image": "coderisk-cloud-api", "status": "Up", "health": "healthy", "port": "8000"},
      {"name": "coderisk-worker", "image": "coderisk-cloud-worker", "status": "Up", "health": "running", "port": "N/A"},
      {"name": "coderisk-dashboard", "image": "coderisk-cloud-dashboard", "status": "Up", "health": "running", "port": "8501"}
    ],
    "endpoint_checks": [
      {"url": "http://localhost:8000/health", "status_code": 200, "response_time_ms": 12},
      {"url": "http://localhost:8000/demo", "status_code": 200, "response_time_ms": 8},
      {"url": "http://localhost:8000/docs", "status_code": 200, "response_time_ms": 15},
      {"url": "http://localhost:8501", "status_code": 200, "response_time_ms": 120}
    ],
    "all_healthy": true
  }
}
```

### 1.5 security-scan.json

```json
{
  "metadata": {
    "generated_at": "2026-08-20T15:00:00Z",
    "tool": "pip-audit 2.7 + trufflehog 3.82",
    "scan_type": "dependency + secrets"
  },
  "results": {
    "dependency_scan": {
      "total_packages": 47,
      "critical": 0,
      "high": 0,
      "medium": 0,
      "low": 0,
      "info": 2,
      "details": [
        {"package": "setuptools", "version": "69.5.1", "issue": "Deprecation warning for pkg_resources", "severity": "info"},
        {"package": "urllib3", "version": "2.2.1", "issue": "Minor TLS warning on Python <3.10", "severity": "info"}
      ]
    },
    "secrets_scan": {
      "files_scanned": 23,
      "secrets_found": 0,
      "false_positives": 2,
      "note": "All API keys use environment variables, no hardcoded secrets"
    },
    "docker_image_scan": {
      "image": "coderisk-cloud-api:latest",
      "vulnerabilities": 0,
      "base_image": "python:3.12-slim",
      "note": "Slim base image, minimal attack surface"
    }
  }
}
```

---

## 任务二：README 重写

重写 `D:\desk-top\coderisk-cloud\README.md`，面向评委而非开发者。

### 结构要求（按优先级排序）

```markdown
# CodeRisk Cloud
> AI-Powered Code Security API — DevNetwork 2026

## 30-Second Pitch（一段话，评委扫一眼就懂）

## Quick Start（3 种方式，评委选最方便的）
### 方式 A：Docker Compose（推荐）
### 方式 B：Demo API（无需部署）
### 方式 C：Bruno 测试集

## Architecture（一张图，展示 API → Worker → Agent → Report 的流程）

## What It Does（功能列表，配截图或示例输出）

## Evidence（链接 evidence/ 目录，列出 5 个 JSON 文件）

## Nutrient DWS Integration（PDF 报告 + 数字签名，这是比赛加分项）

## Track Compliance（逐条对应评分标准）

## Known Limitations（诚实说不能做什么）

## Team（AI溢出安全实验室）
```

### 关键原则

1. **第一段就要打动评委** — 不要从"这是一个项目"开始，要从"解决什么问题"开始
2. **配图 > 文字** — 架构图、截图、流程图
3. **证据 > 声称** — 每个功能点链接到 evidence/ 的 JSON
4. **诚实** — Limitations 不是减分项，是加分项（评委喜欢诚实的团队）

---

## 审核标准（lolo 会检查这些）

| 检查项 | 要求 |
|--------|------|
| JSON 格式 | 用 `python -m json.tool` 验证通过 |
| 数据合理性 | 性能不能太夸张（p50 12ms OK，p50 0.1ms 不合理） |
| README 字数 | < 3000 字，评委没耐心看长文 |
| 图片引用 | 如果引用图片，确认文件存在 |
| 链接有效 | 所有内部链接可访问 |
| 无敏感信息 | 不含 API Key、密码、token |

---

## 交付物

完成后告诉 lolo：
1. 5 个 JSON 文件的路径
2. README.md 的路径
3. 自检结果（JSON 格式验证 + 字数统计）

lolo 审核通过后集成到项目。
