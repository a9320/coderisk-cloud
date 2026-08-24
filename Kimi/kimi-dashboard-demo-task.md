# Kimi 任务书：Dashboard 加载 Demo 数据

## 背景

Dashboard（Streamlit 应用，端口 8501）目前通过 API 查询任务列表，但任务需要 Worker 实际克隆 GitHub 仓库才能完成。在 Docker 环境中 GitHub 被拒连（ConnectionRefusedError），导致任务永远卡在 PENDING/FAILED。

**目标：** 让 Dashboard 启动时自动加载 `/demo` 端点的预置数据，无需 Worker 参与，截图时能直接展示完整的扫描结果。

## 当前 Dashboard 结构（从截图分析）

- **左侧栏：** CodeRisk Cloud 品牌 + API 状态（Online）+ Quick Links（API Docs / GitHub Repo / Nutrient DWS / About）
- **主区域 1 - Submit New Analysis：** 表单（Repository URL / Branch / Output 下拉 / Start Analysis 按钮）
- **主区域 2 - Analysis Tasks：** 任务列表（Task ID / 仓库 URL / 分支 / 状态 / 进度条）
- **主区域 3 - Report Preview：** 报告预览区

## API `/demo` 端点返回的数据结构

```json
{
  "task_id": "cr-demo-20260820-001",
  "status": "completed",
  "source": "demo",
  "repo_url": "https://github.com/example/flask-vulnerable-app",
  "summary": {
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 2,
    "info": 1,
    "total": 9
  },
  "findings": [
    {
      "id": "CR-001",
      "severity": "critical",
      "category": "SQL Injection",
      "file": "app/routes/users.py",
      "line": 42,
      "code_snippet": "cursor.execute(f\"SELECT * FROM users WHERE id = {user_id}\")",
      "description": "直接使用 f-string 拼接 SQL 查询...",
      "recommendation": "使用参数化查询...",
      "cwe": "CWE-89",
      "confidence": 0.98,
      "agent": "agent_1_static"
    }
    // ... 共 9 个 findings（CR-001 到 CR-009）
  ],
  "analysis": {
    "duration_seconds": 4.2,
    "agents_used": 4,
    "files_scanned": 23,
    "lines_of_code": 1847,
    "llm_model": "Qwen2.5-Coder-7B-Instruct (local)",
    "mode": "local-gpu"
  },
  "report_urls": {
    "json": "/reports/cr-demo-20260820-001.json",
    "sarif": "/reports/cr-demo-20260820-001.sarif",
    "pdf": null
  },
  "completed_at": "2026-08-20T15:00:00Z"
}
```

## 具体修改需求

### 需求 1：Dashboard 启动时自动加载 Demo 数据

修改 Dashboard 的主页面逻辑：
1. 页面加载时，先尝试调用 `GET http://api:8000/demo` 获取 demo 数据
2. 如果成功，将 demo 数据作为"已完成任务"显示在 Analysis Tasks 区域
3. 如果失败（API 不可用），保持原来的空状态

### 需求 2：Analysis Tasks 区域展示 Demo 任务

在 Analysis Tasks 列表中显示 demo 任务卡片：
- **Task ID：** `cr-demo-20260820-001`
- **仓库 URL：** `https://github.com/example/flask-vulnerable-app`
- **分支：** `main`
- **状态：** ✅ COMPLETED（绿色）
- **进度：** 100%
- **漏洞摘要：** 🔴 1 Critical · 🟠 2 High · 🟡 3 Medium · 🟢 2 Low · ⚪ 1 Info

### 需求 3：点击任务后在 Report Preview 展示详情

点击 demo 任务卡片后，在 Report Preview 区域显示：

**3a. 漏洞摘要卡片**
- 用彩色标签/徽章展示各级别数量（Critical 红、High 橙、Medium 黄、Low 绿、Info 灰）

**3b. 漏洞详情表格**
| ID | 严重度 | 类型 | 文件 | 行号 | 置信度 | Agent |
|-----|--------|------|------|------|--------|-------|
| CR-001 | 🔴 Critical | SQL Injection | app/routes/users.py | 42 | 98% | agent_1_static |
| CR-002 | 🟠 High | Command Injection | app/utils/network.py | 18 | 95% | agent_1_static |
| ... | ... | ... | ... | ... | ... | ... |

**3c. 点击某条漏洞后展开详情**
- Code Snippet（代码高亮）
- Description（中文描述）
- Recommendation（修复建议）
- CWE 编号
- Confidence 置信度

### 需求 4：分析统计信息

在漏洞列表下方显示：
- 扫描耗时：4.2s
- 使用 Agent 数：4
- 扫描文件数：23
- 代码行数：1,847
- LLM 模型：Qwen2.5-Coder-7B-Instruct (local)
- 模式：local-gpu

## 技术约束

1. **只改 Dashboard 代码**（Streamlit 应用），不改 API/Worker
2. Dashboard 容器内 API 地址是 `http://api:8000`（Docker 内部网络）
3. 保持原有的 UI 风格（暗色主题、蓝色强调、绿色状态指示）
4. 代码改动尽量小，不要重写整个 Dashboard
5. 改完后 Weike 会在 Windows 端重新 `docker compose up --build -d` 验证

## 交付物

修改后的 Dashboard Python 文件（直接替换即可）。

## 验证标准

1. `docker compose up --build -d` 构建成功
2. 打开 `http://localhost:8501` 能看到 demo 任务
3. 点击任务后 Report Preview 显示 9 个漏洞详情
4. UI 美观，适合截图用于黑客松提交
