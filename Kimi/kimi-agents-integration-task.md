# Kimi 任务书：集成 code-risk-agent 到 Docker 镜像

> 更新时间：2026-08-22 21:40

---

## 一、当前问题

Worker 扫描只找到 1 个 info 级漏洞，日志显示：
```
Static analysis failed: No module named 'agents'
Semantic analysis failed: No module named 'agents'
Verification failed: No module named 'agents'
```

## 二、根因分析

`app/tasks.py` 中导入的 `Orchestrator` 来自 `code-risk-agent` 项目（git submodule）：

```python
# app/tasks.py 第 32 行
from orchestrator import Orchestrator
```

`Orchestrator` 依赖以下模块：
```
orchestrator.py
├── agents/
│   ├── __init__.py
│   ├── static_analyzer.py      ← 静态分析
│   ├── semantic_analyzer.py    ← 语义分析（LLM）
│   ├── deep_verifier.py        ← 深度验证
│   └── report_generator.py     ← 报告生成
├── core/
│   ├── models.py               ← 数据模型（Severity, Evidence 等）
│   ├── llm_client.py           ← LLM 调用客户端
│   ├── cve_client.py           ← CVE 数据库查询
│   ├── memory.py               ← 记忆层
│   ├── taint_analyzer.py       ← 污点分析
│   ├── dependency_scanner.py   ← 依赖扫描
│   └── semgrep_runner.py       ← Semgrep 集成
```

**但 Docker 镜像里根本没有 `code-risk-agent` 目录！**

Dockerfile 只 COPY 了 `app/`：
```dockerfile
COPY app/ ./app/
```

`code-risk-agent` 是一个 git submodule（`.gitmodules` 里定义），Docker 构建时没有初始化。

## 三、解决方案

### 需要改的文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `Dockerfile` | 修改 | 添加 git submodule 初始化 + 安装依赖 |
| `requirements.txt` | 修改 | 添加 code-risk-agent 的依赖 |
| `.dockerignore` | 检查 | 确保不排除 code-risk-agent |

### 3.1 修改 Dockerfile

在 `COPY app/ ./app/` **之前**添加 git submodule 初始化：

```dockerfile
# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    gcc \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── 新增：初始化 git submodule（code-risk-agent） ──
COPY .gitmodules .gitmodules
COPY code-risk-agent/ ./code-risk-agent/

# 应用代码
COPY app/ ./app/
```

**注意：** 不能在 Docker build 中运行 `git submodule update --init`（因为 `.git` 目录通常被 `.dockerignore` 排除）。所以需要直接 COPY submodule 目录。

### 3.2 修改 requirements.txt

添加 code-risk-agent 的依赖（在现有依赖基础上追加）：

```
# code-risk-agent 依赖
pydantic>=2.0
rich>=13.0
httpx>=0.25
tree-sitter>=0.21
semgrep>=1.0
```

**注意：** 检查现有的 `requirements.txt` 是否已有这些包，不要重复添加。

### 3.3 检查 .dockerignore

确认 `.dockerignore` 没有排除 `code-risk-agent/` 目录。

### 3.4 验证 PYTHONPATH

Dockerfile 已设置 `ENV PYTHONPATH=/app`，确保 `code-risk-agent/` 在 `/app/code-risk-agent/` 下，这样 `from agents.xxx import ...` 和 `from orchestrator import Orchestrator` 才能正确导入。

但 `app/tasks.py` 中的导入逻辑是：
```python
CODERISK_AGENT_PATH = settings.CODERISK_PATH  # = /app/code-risk-agent
if CODERISK_AGENT_PATH not in sys.path:
    sys.path.insert(0, CODERISK_AGENT_PATH)
```

这会把 `/app/code-risk-agent` 加入 `sys.path`，所以 `from agents.xxx import ...` 和 `from orchestrator import Orchestrator` 会从 `/app/code-risk-agent/agents/` 和 `/app/code-risk-agent/orchestrator.py` 导入。

**确认：** `/app/code-risk-agent/` 目录下必须有：
- `orchestrator.py`
- `agents/__init__.py`
- `agents/static_analyzer.py`
- `agents/semantic_analyzer.py`
- `agents/deep_verifier.py`
- `agents/report_generator.py`
- `core/` 目录（含 models.py, llm_client.py 等）

## 四、code-risk-agent 仓库信息

| 项目 | 值 |
|------|-----|
| GitHub 仓库 | https://github.com/a9320/code-risk-agent.git |
| 本地路径 | `D:\desk-top\coderisk-cloud\code-risk-agent\`（git submodule） |
| 版本 | v0.3.2 |
| Python 要求 | >=3.10 |

### 关键依赖
- `pydantic>=2.0` — 数据模型
- `rich>=13.0` — 终端输出
- `httpx>=0.25` — HTTP 客户端
- `tree-sitter>=0.21` — 代码解析
- `semgrep>=1.0` — 静态分析规则引擎

### Orchestrator 调用链
```
app/tasks.py
  → import Orchestrator (from /app/code-risk-agent/orchestrator.py)
    → agents.static_analyzer.StaticAnalyzer   — 正则 + 模式匹配
    → agents.semantic_analyzer.SemanticAnalyzer — LLM 语义分析
    → agents.deep_verifier.DeepVerifier       — 交叉验证
    → agents.report_generator.ReportGenerator — 生成报告
```

## 五、本地验证步骤

在改 Dockerfile 之前，先在本地验证 code-risk-agent 能正常导入：

```powershell
cd D:\desk-top\coderisk-cloud

# 1. 确认 submodule 已初始化
git submodule update --init --recursive

# 2. 确认目录存在
dir code-risk-agent\agents\
dir code-risk-agent\core\
dir code-risk-agent\orchestrator.py

# 3. 测试 Python 导入
python -c "import sys; sys.path.insert(0, 'code-risk-agent'); from orchestrator import Orchestrator; print('OK')"
```

## 六、Docker 构建验证

```powershell
# 1. 重新构建（确保 submodule 代码被 COPY 进镜像）
docker compose build --no-cache worker

# 2. 验证容器内目录
docker exec coderisk-worker ls -la /app/code-risk-agent/
docker exec coderisk-worker ls /app/code-risk-agent/agents/

# 3. 验证 Python 导入
docker exec coderisk-worker python -c "from orchestrator import Orchestrator; print('OK')"

# 4. 重启 Worker
docker compose up -d worker

# 5. 触发真实扫描
# 在 Dashboard 切到 Local 模式，点 Start Local Scan

# 6. 检查 Worker 日志，应该看到：
# Static: N findings, Semantic: M findings
# 而不是 "No module named 'agents'"
```

## 七、预期结果

修复后，扫描 Damn-Vulnerable-Flask-Application 应该能检出：
- SQL 注入
- XSS
- 命令注入
- 硬编码密钥
- 不安全反序列化
- 路径遍历
- 等多种漏洞

**预期 findings 数量：5-15 个**（取决于仓库代码量和规则覆盖）

## 八、交付物

1. 修改后的 `Dockerfile`
2. 修改后的 `requirements.txt`（如有新增依赖）
3. 修改后的 `.dockerignore`（如有必要）
