# CodeRisk Cloud — 项目背景 + 当前问题（Kimi 快速上手文档）

> 更新时间：2026-08-22 18:48

---

## 一、项目概述

**CodeRisk Cloud** 是一个 AI 驱动的代码安全分析平台，参加 DevNetwork [API + Cloud + AI] Hackathon 2026（截止 2026-09-03）。

### 核心功能
- 用户提交 GitHub 仓库 URL 或本地代码目录
- 4 个 AI Agent 自动分析代码安全漏洞（静态分析 → 语义分析 → 验证 → 报告）
- 输出 JSON / SARIF / PDF 格式的漏洞报告
- Web Dashboard 展示扫描结果

### 技术栈
- **API：** FastAPI（端口 8000）
- **任务队列：** Celery + Redis
- **Worker：** Python，运行 4-Agent 分析流水线
- **Dashboard：** Streamlit（端口 8501）
- **部署：** Docker Compose（4 个容器：redis / api / worker / dashboard）

### 仓库结构
```
coderisk-cloud/
├── docker-compose.yml          # 4 容器编排
├── Dockerfile                  # 统一镜像
├── requirements.txt
├── app/
│   ├── main.py                 # FastAPI 路由（API 端点）
│   ├── tasks.py                # Celery 任务（Worker 逻辑）
│   ├── dashboard.py            # Streamlit Dashboard
│   ├── config.py               # 配置
│   ├── models.py               # 数据模型
│   ├── demo_fixture.py         # /demo 端点的预置数据
│   └── nutrient_client.py      # PDF 签名（Nutrient DWS）
├── repos/                      # 本地扫描目录（Docker volume 挂载）
│   └── Damn-Vulnerable-Flask-Application/
├── evidence/                   # 截图证据（DevPost 提交用）
└── docs/                       # 架构图、文案等
```

### GitHub 仓库
https://github.com/a9320/coderisk-cloud

---

## 二、当前已完成的工作

### ✅ 已完成
1. FastAPI + Celery + Redis 端到端架构
2. `/demo` 端点返回预置 9 个漏洞（无需 API Key）
3. `/api/v1/analyze` 端点支持 GitHub 克隆扫描
4. `/api/v1/scan-local` 端点支持本地目录扫描（今天新增）
5. Dashboard 支持 GitHub / Local 两种扫描模式切换
6. Docker Compose 4 容器全部 Up
7. CI/CD（GitHub Actions 3 Job 全绿）
8. DevPost 文案 + 封面图 + 架构图 + PDF 截图 + CI 截图

### 🔲 待完成
1. **Dashboard 任务状态自动轮询**（当前核心问题）
2. **扫描结果完整性**（agents 模块缺失导致只找到 1 个漏洞）
3. **Demo 视频录制**
4. **Dashboard 截图（带真实数据）**

---

## 三、当前核心问题

### 问题 1：Dashboard 任务状态不自动刷新（最重要）

#### 现象
1. 用户在 Dashboard 点击 "Start Local Scan"
2. 任务卡片出现在 Analysis Tasks 列表，状态为 ⏳ PENDING
3. Worker 在 0.2 秒内完成了扫描（日志确认 `status=completed`）
4. **但 Dashboard 上的任务永远停在 PENDING，进度条不动**
5. 只有手动刷新浏览器页面才能看到最新状态

#### 根因
Dashboard 用 `st.session_state.tasks` 存储任务列表。任务创建时写入 `status="pending"`，之后**没有任何代码轮询 API 检查任务是否完成**。

#### Worker 日志（证明任务已完成）
```
[2026-08-22 10:25:46,590] [cr-20260822-66e5894d] Using local directory: /repos/Damn-Vulnerable-Flask-Application
[2026-08-22 10:25:46,594] [cr-20260822-66e5894d] Report generated: 1 findings
[2026-08-22 10:25:46,778] Task analyze_codebase succeeded in 0.19s
```

#### Redis 中的任务状态（证明已完成）
```json
{
  "task_id": "cr-20260822-66e5894d",
  "status": "completed",
  "progress": 100,
  "agent_status": {
    "agent_1_static": "completed",
    "agent_2_semantic": "completed",
    "agent_3_verifier": "completed",
    "agent_4_report": "completed"
  }
}
```

#### 期望行为
1. 任务提交后，Dashboard **每 2 秒**轮询 `GET /api/v1/tasks/{task_id}`
2. 任务状态变为 completed 时：
   - 更新任务卡片：PENDING → ✅ COMPLETED
   - 进度条 0% → 100%
   - 自动获取报告数据（findings、summary）
   - 自动选中该任务，在 Report Preview 显示漏洞详情
3. 轮询超过 60 秒未完成 → 显示"扫描超时"
4. 已完成的任务不再轮询

#### API 端点参考

**获取任务状态：**
```
GET /api/v1/tasks/{task_id}
Authorization: Bearer dev-ke…tion

返回：
{
  "task_id": "cr-20260822-66e5894d",
  "status": "completed",
  "progress": 100,
  "agent_status": {...}
}
```

**获取报告详情：**
```
GET /api/v1/reports/{task_id}
Authorization: Bearer dev-ke…tion

返回：
{
  "task_id": "...",
  "summary": {"critical": 1, "high": 2, ...},
  "findings": [
    {
      "id": "CR-001",
      "severity": "critical",
      "category": "SQL Injection",
      "file": "app/routes/users.py",
      "line": 42,
      "code_snippet": "...",
      "description": "...",
      "recommendation": "...",
      "cwe": "CWE-89",
      "confidence": 0.98,
      "agent": "agent_1_static"
    }
  ]
}
```

#### Streamlit 实现参考

```python
# 在 Dashboard 的任务列表渲染逻辑中，添加轮询：
import time

def poll_pending_tasks():
    """轮询所有 pending 任务的状态"""
    updated = False
    for task in st.session_state.tasks:
        if task["status"] != "pending":
            continue
        
        # 调用 API 获取最新状态
        code, data = api_get(f"{API_BASE}/api/v1/tasks/{task['task_id']}")
        if code == 200 and data:
            new_status = data.get("status", "pending")
            if new_status == "completed":
                task["status"] = "completed"
                task["progress"] = 100
                
                # 获取报告数据
                report_code, report = api_get(f"{API_BASE}/api/v1/reports/{task['task_id']}")
                if report_code == 200 and report:
                    task["findings"] = report.get("findings", [])
                    task["summary"] = report.get("summary", {})
                    task["analysis"] = report.get("analysis", {})
                
                # 自动选中完成的任务
                st.session_state.selected_task = task["task_id"]
                updated = True
            elif new_status == "failed":
                task["status"] = "failed"
                updated = True
            else:
                task["progress"] = data.get("progress", 0)
    
    return updated

# 在页面渲染末尾：
has_pending = any(t["status"] == "pending" for t in st.session_state.tasks)
if has_pending:
    time.sleep(2)
    poll_pending_tasks()
    st.rerun()
```

---

### 问题 2：扫描结果太少（次要，可用 demo 数据绕过）

#### 现象
Worker 日志：
```
Static analysis failed: No module named 'agents'
Semantic analysis failed: No module named 'agents'
Verification failed: No module named 'agents'
Static: 1 findings, Semantic: 0 findings
```

#### 根因
`app/tasks.py` 导入的 `Orchestrator` 依赖 `agents` 模块（来自 code-risk-agent 项目），但 Docker 容器中该模块不可用。

#### 影响
- 真实扫描只找到 1 个 info 级漏洞
- `/demo` 端点有 9 个漏洞（预置数据，不受影响）

#### 建议
**暂时不修**。先用 `/demo` 数据展示完整功能，hackathon 结束后再修 agents 模块集成。

---

## 四、当前 Dashboard 代码关键片段

### API 配置
```python
API_BASE = "http://api:8000"           # Docker 内部网络
DEMO_API = f"{API_BASE}/demo"
HEALTH_API = f"{API_BASE}/health"
SCAN_LOCAL_API = f"{API_BASE}/api/v1/scan-local"
```

### 任务数据结构（session_state）
```python
{
    "task_id": "cr-20260822-33c1909a",
    "status": "pending",              # pending / completed / failed
    "progress": 0,                    # 0-100
    "source": "local",                # local / github / demo
    "repo_url": "/repos/Damn-Vulnerable-Flask-Application",
    "branch": "N/A",
    "summary": {},                    # {"critical": 1, "high": 2, ...}
    "findings": [],                   # [{id, severity, category, file, ...}]
    "analysis": {},                   # {duration_seconds, agents_used, ...}
    "report_urls": {},
    "is_demo": False
}
```

### 当前 API Helper 函数
```python
def api_get(url, timeout=10):
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code, r.json() if r.status_code == 200 else None
    except Exception as e:
        return None, str(e)
```

---

## 五、Docker 环境信息

### 容器网络
```
coderisk-redis    → 172.18.0.2:6379
coderisk-api      → 172.18.0.3:8000
coderisk-worker   → 172.18.0.5
coderisk-dashboard → 172.18.0.4:8501
```

### Volume 挂载
```yaml
# api 和 worker 和 dashboard 都挂载了：
volumes:
  - ./repos:/repos:ro    # 宿主机 repos 目录 → 容器内 /repos
```

### 本地测试仓库
```
D:\desk-top\coderisk-cloud\repos\Damn-Vulnerable-Flask-Application\
```

---

## 六、交付要求

### 必须修改的文件
`app/dashboard.py`（只改这一个文件）

### 必须实现的功能
1. ✅ 任务提交后自动轮询状态（2 秒间隔）
2. ✅ 任务完成后自动更新 UI（状态、进度条）
3. ✅ 完成后自动获取报告数据（findings、summary）
4. ✅ 完成后自动选中任务并在 Report Preview 显示
5. ✅ 超时处理（60 秒）

### 不需要改的文件
- `main.py` — API 端点已就绪
- `tasks.py` — Worker 已就绪
- `docker-compose.yml` — 已就绪

### 验证方法
```powershell
# 1. 替换 dashboard.py 后重新构建
docker compose up --build -d dashboard

# 2. 打开 Dashboard
# http://localhost:8501

# 3. 切换到 Local 模式，选择 /repos/Damn-Vulnerable-Flask-Application
# 4. 点击 Start Local Scan
# 5. 观察：任务应在 2-5 秒内自动从 PENDING 变为 COMPLETED
# 6. Report Preview 应自动显示漏洞详情
```

---

## 七、时间线

| 时间 | 里程碑 | 状态 |
|------|--------|------|
| 8/17 | 项目启动 | ✅ |
| 8/19 | API + Celery + Redis 端到端 | ✅ |
| 8/20 | Nutrient DWS + Docker | ✅ |
| 8/21 | CI/CD + 架构图 + DevPost 文案 | ✅ |
| 8/22 | Local Scan + Dashboard 轮询 | 🔲 进行中 |
| 8/23-9/03 | Demo 视频 + 提交 | 🔲 待做 |
