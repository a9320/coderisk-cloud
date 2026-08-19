# CodeRisk Cloud — 完整项目文档

> DevNetwork [API + Cloud + AI] Hackathon 2026 参赛项目
> AI溢出安全实验室 (Overflow Security Lab)
> 最后更新：2026-08-19

---

## 一、项目概述

**CodeRisk Cloud** 是 [CodeRisk Agent](https://github.com/a9320/code-risk-agent) 的 Cloud-Native API 版本，将 4-Agent 代码安全分析流水线封装为 REST API 服务。

### 核心卖点
- **本地 GPU 推理** — LLM 跑在 AMD GPU 上，源码不出基础设施
- **4-Agent 流水线** — 静态分析 → 语义理解 → 深度验证 → 报告生成
- **Nutrient DWS** — 专业 PDF 审计报告 + SHA-256 数字签名
- **多格式输出** — JSON / SARIF / PDF
- **GitHub Webhook** — Push 自动触发分析

### 技术栈
| 组件 | 技术 |
|------|------|
| API 框架 | FastAPI 0.141+ |
| 任务队列 | Celery 5.6+ (Redis broker) |
| 缓存/消息 | Redis 5.0+ |
| 数据校验 | Pydantic 2.13+ |
| HTTP 客户端 | httpx 0.27+ |
| PDF 生成 | Nutrient DWS API |
| Dashboard | Streamlit 1.30+ |
| 运行时 | Python 3.12+ |

---

## 二、目录结构

```
coderisk-cloud/
├── app/
│   ├── __init__.py          (1 行)    包初始化
│   ├── config.py            (49 行)   配置管理
│   ├── main.py              (375 行)  FastAPI 主应用 + 8 个端点
│   ├── tasks.py             (443 行)  Celery 任务 + 4-Agent 流水线
│   ├── models.py            (118 行)  Pydantic 数据模型
│   ├── nutrient_client.py   (429 行)  Nutrient DWS PDF 客户端
│   └── dashboard.py         (370 行)  Streamlit Dashboard
├── bruno/                         Bruno API 测试集 (9 个文件)
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
├── reports/                       报告输出目录（运行时生成）
│   └── uploads/                 ZIP 上传临时存储
├── backups/v1/                    v1 代码备份
├── 优化建议/                      Kimi/DeepSeek 优化建议
│   ├── 代码2/
│   ├── 代码3/                   Day 3 ZIP 上传交付
│   └── 建议31/
├── tests/                         测试文件
├── .env.example                   环境变量模板
├── .env                           环境变量（本地）
├── requirements.txt               Python 依赖
├── README.md                      项目说明
├── Day2-进展报告.md
├── demo-script.md                 英文 Demo 脚本
├── demo-script-cn.md              中文 Demo 脚本
└── 项目完整文档.md
```

**总代码量：** 7 个 Python 文件，1,785 行

---

## 三、环境配置

### 3.1 环境变量 (.env)

```env
# Redis (Celery Broker + Backend)
REDIS_URL=redis://localhost:6379/0

# API 认证
CODERISK_API_KEY=dev-key-change-in-production

# CodeRisk Agent 路径（自动探测优先级：环境变量 > ../code-risk-agent > /app/code-risk-agent）
CODERISK_PATH=/app/code-risk-agent

# Nutrient DWS (PDF 生成)
NUTRIENT_DWS_API_KEY=<your-nutrient-api-key>
NUTRIENT_DWS_API_URL=https://api.nutrient.io/build

# GitHub Webhook（可选）
GITHUB_WEBHOOK_SECRET=

# 报告存储
REPORTS_DIR=./reports

# Worker 并发数
WORKER_CONCURRENCY=2
```

### 3.2 Python 依赖 (requirements.txt)

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

### 3.3 安装与启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动 Redis
redis-server &

# 3. 启动 API 服务
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 4. 启动 Celery Worker（单独终端）
celery -A app.tasks worker --loglevel=info

# 5. 启动 Dashboard（可选，单独终端）
streamlit run app/dashboard.py --server.port 8501
```

---

## 四、API 端点详细文档

### 4.1 POST /api/v1/analyze — GitHub 仓库分析

**认证：** Bearer Token

**请求体：**
```json
{
  "source": "github",
  "repo_url": "https://github.com/user/repo",
  "branch": "main",
  "output_formats": ["json", "sarif", "pdf"],
  "callback_url": null
}
```

**请求字段：**
| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| source | string | 否 | "direct_upload" | 代码来源：github / zip / direct_upload |
| repo_url | string | source=github 时必填 | null | GitHub 仓库 URL |
| branch | string | 否 | "main" | Git 分支 |
| output_formats | string[] | 否 | ["json", "sarif"] | 输出格式：json / sarif / pdf |
| callback_url | string | 否 | null | 分析完成回调 URL |

**成功响应 (200)：**
```json
{
  "task_id": "cr-20260819-ed5ccb70",
  "status": "pending",
  "message": "Analysis task created. Use GET /api/v1/tasks/cr-20260819-ed5ccb70 to check progress."
}
```

**错误响应：**
| 状态码 | 场景 |
|--------|------|
| 400 | source=github 但缺 repo_url |
| 401 | 缺少 Authorization header |
| 403 | API Key 无效 |

---

### 4.2 POST /api/v1/analyze/upload — ZIP 文件上传分析

**认证：** Bearer Token
**Content-Type：** multipart/form-data

**表单字段：**
| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| file | File | 是 | — | ZIP 文件（≤ 100MB） |
| output_formats | string | 否 | "json,sarif,pdf" | 逗号分隔的输出格式 |
| callback_url | string | 否 | null | 回调 URL |

**安全校验：**
- ✅ 文件扩展名校验（.zip）
- ✅ 文件大小限制（100MB）
- ✅ 解压后大小限制（100MB）
- ✅ 文件数量限制（≤ 10,000）
- ✅ 路径遍历防护（拒绝 `../`）

**成功响应 (200)：**
```json
{
  "task_id": "cr-20260819-ed5ccb70",
  "status": "pending",
  "message": "ZIP upload accepted. Analysis task created. Use GET /api/v1/tasks/cr-20260819-ed5ccb70 to check progress."
}
```

**错误响应：**
| 状态码 | 场景 |
|--------|------|
| 400 | 非 ZIP 文件 / 无效输出格式 / 文件名缺失 |
| 401 | 缺少 Authorization header |
| 413 | 文件超过 100MB |

---

### 4.3 GET /api/v1/tasks/{task_id} — 查询任务状态

**认证：** Bearer Token

**成功响应 (200)：**
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

**任务状态流转：**
```
pending → analyzing → verifying → generating_report → completed
                                                    → failed
```

**错误响应：**
| 状态码 | 场景 |
|--------|------|
| 401 | 认证失败 |
| 404 | task_id 不存在 |

---

### 4.4 GET /api/v1/reports/{task_id} — 获取分析报告

**认证：** Bearer Token（需与提交任务时相同的 API Key，报告隔离）

**前置条件：** 任务状态为 `completed`

**成功响应 (200)：**
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

**错误响应：**
| 状态码 | 场景 |
|--------|------|
| 400 | 任务未完成 |
| 401 | 认证失败 |
| 403 | API Key 与提交者不匹配（报告隔离） |
| 404 | 任务或报告不存在 |

---

### 4.5 GET /api/v1/reports/{task_id}/pdf — 下载 PDF 报告

**认证：** Bearer Token（报告隔离）

**成功响应：** PDF 文件流 (`application/pdf`)

**错误响应：**
| 状态码 | 场景 |
|--------|------|
| 403 | API Key 不匹配 |
| 404 | PDF 不存在（可能未请求 pdf 格式） |

---

### 4.6 POST /api/v1/webhooks/github — GitHub Webhook

**认证：** HMAC-SHA256 签名验证（`X-Hub-Signature-256` header）

**触发条件：** GitHub Push 事件

**请求体：** GitHub Webhook payload（自动解析 `repository.clone_url` 和 `ref`）

**成功响应 (200)：**
```json
{
  "task_id": "cr-20260819-xxxxxxxx",
  "status": "pending",
  "message": "Webhook analysis started"
}
```

**安全特性：**
- HMAC-SHA256 签名验证（防伪造）
- 自动提取分支名
- 白名单域名校验（github.com / gitlab.com / gitee.com）

---

### 4.7 GET /health — 健康检查

**无需认证**

**成功响应 (200)：**
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

**降级响应 (503)：**
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

### 4.8 GET / — 根路径

**无需认证**

**响应：**
```json
{
  "name": "CodeRisk Cloud",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

---

## 五、4-Agent 分析流水线

```
┌──────────────────────────────────────────────────────────────┐
│                    Celery Task Worker                         │
├──────────────┬──────────────┬──────────────┬─────────────────┤
│  Agent 1     │  Agent 2     │  Agent 3     │  Agent 4        │
│  静态分析     │  语义分析     │  深度验证     │  报告生成        │
│  (Semgrep)   │  (LLM)       │  (交叉验证)   │  (JSON/PDF)     │
├──────────────┼──────────────┼──────────────┼─────────────────┤
│ regex 扫描   │ Qwen2.5-Coder│ 误报过滤     │ JSON 输出       │
│ Semgrep 规则 │ 语义理解      │ 置信度评估    │ SARIF 输出      │
│ CWE 映射     │ 逻辑漏洞检测  │ 交叉引用     │ PDF (Nutrient)  │
└──────┬───────┴──────┬───────┴──────┬───────┴────────┬────────┘
       │              │              │                │
       ▼              ▼              ▼                ▼
   静态发现 ──→ 合并去重 ──→ 验证结果 ──→ 最终报告
```

### 进度追踪

| 阶段 | 进度 | agent_status |
|------|------|-------------|
| 准备代码 | 5% | agent_1_static: "preparing" |
| 静态+语义并行 | 15-55% | agent_1/2: "running" → "completed" |
| 深度验证 | 75-90% | agent_3: "running" → "completed" |
| 报告生成 | 95-100% | agent_4: "running" → "completed" |

---

## 六、Nutrient DWS 集成

### PDF 报告特性
- 深色渐变 header（#0f0c29 → #302b63 → #24243e）
- 5 色 severity 统计卡片（Critical/High/Medium/Low/Info）
- Findings 列表：左色条 + severity 标签 + 文件位置 + 描述
- SHA-256 数字签名嵌入（报告底部绿色签名区块）
- 底部版权：CodeRisk Cloud © 2026 | AI溢出安全实验室

### API 调用
```
POST https://api.nutrient.io/build
Authorization: Bearer <Processor API Key>
Content-Type: multipart/form-data

instructions: {"parts":[{"html":"report.html"}]}
report.html: <HTML 内容>
```

### API Key
```
配置在 .env 中：NUTRIENT_DWS_API_KEY=<your-nutrient-api-key>
⚠️ 不要明文写入文档或提交到 git
```

---

## 七、数据模型

### 请求模型

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

### 响应模型

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

## 八、安全特性

| 特性 | 实现 |
|------|------|
| API 认证 | Bearer Token + `hmac.compare_digest`（防时序攻击） |
| 报告隔离 | API Key SHA-256 哈希绑定，不同 Key 无法互访 |
| GitHub Webhook | HMAC-SHA256 签名验证 |
| ZIP 上传安全 | 扩展名校验 + 100MB 限制 + 解压大小限制 + 文件数限制 + 路径遍历防护 |
| Git Clone 白名单 | 仅允许 github.com / gitlab.com / gitee.com |
| 防注入 | git clone 参数白名单，不拼接用户输入 |
| 临时文件清理 | finally 块自动清理 work_dir + ZIP 文件 |
| 源码隐私 | LLM 本地推理，源码不出基础设施 |

---

## 九、Bruno 测试集

使用 [Bruno](https://www.usebruno.com/) 运行，环境配置在 `bruno/environments/local.bru`。

### 测试用例清单

| 文件 | 方法 | 端点 | 测试内容 |
|------|------|------|---------|
| health-check.bru | GET | /health | 健康检查 |
| submit-github.bru | POST | /api/v1/analyze | GitHub 仓库提交 |
| submit-invalid.bru | POST | /api/v1/analyze | 无效请求 |
| missing-auth.bru | POST | /api/v1/analyze | 缺认证 → 401 |
| invalid-api-key.bru | POST | /api/v1/analyze | 错误 Key → 403 |
| get-task-status.bru | GET | /api/v1/tasks/{id} | 查询任务状态 |
| not-found.bru | GET | /api/v1/tasks/{id} | 不存在 → 404 |
| get-report.bru | GET | /api/v1/reports/{id} | 获取报告 |

---

## 十、Dashboard (Streamlit)

### 启动
```bash
streamlit run app/dashboard.py --server.port 8501
```

### 功能
- 🔍 **提交分析** — 输入 GitHub 仓库 URL + 分支 + 输出格式
- 📋 **任务列表** — 实时刷新状态、进度条、Agent 详情展开
- 📊 **报告预览** — Severity 统计卡片 + Findings 表格 + 下载按钮
- 🔏 **数字签名** — SHA-256 完整性验证展示

### 环境变量
```env
CODERISK_API_URL=http://localhost:8000
CODERISK_API_KEY=dev-key-change-in-production
```

---

## 十一、开发历程

### Day 1 (2026-08-17) ✅
- FastAPI + Celery + Redis 骨架（Kimi 写，796 行）
- v2 优化：14 项修复（Kimi 审查）
- 里程碑 M1 提前 5 天

### Day 2 (2026-08-18) ✅
- Nutrient DWS 真实 API 接入（lolo 重写 nutrient_client.py）
- Kimi 交付：dashboard.py + Bruno 测试 + Demo 脚本
- 里程碑 M2 提前 7 天

### Day 3 (2026-08-19) ✅
- ZIP 文件上传端点（Kimi 写，lolo 审核集成）
- 安全防护：ZIP 炸弹 + 路径遍历 + 文件数限制
- 端到端测试 5/5 全过

### 待做
- [ ] Docker Compose 一键部署
- [ ] GitHub Actions CI/CD
- [ ] Demo 视频录制
- [ ] DevPost 提交材料

---

## 十二、端点快速参考

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | /api/v1/analyze | Bearer | GitHub 仓库分析 |
| POST | /api/v1/analyze/upload | Bearer | ZIP 上传分析 |
| GET | /api/v1/tasks/{id} | Bearer | 任务状态 |
| GET | /api/v1/reports/{id} | Bearer | 分析报告 |
| GET | /api/v1/reports/{id}/pdf | Bearer | PDF 下载 |
| POST | /api/v1/webhooks/github | HMAC | GitHub Webhook |
| GET | /health | 无 | 健康检查 |
| GET | / | 无 | 根路径 |
| GET | /docs | 无 | Swagger UI |
| GET | /redoc | 无 | ReDoc |

---

*CodeRisk Cloud v1.0.0 — AI溢出安全实验室*
*DevNetwork [API + Cloud + AI] Hackathon 2026*
