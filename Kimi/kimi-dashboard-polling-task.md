# Kimi 任务书：Dashboard 任务状态轮询 + 完整扫描结果展示

## 背景

Dashboard（Streamlit）的"Start Local Scan"功能已基本打通，但有两个关键问题导致无法用于 Demo 录制。

---

## 问题 1：任务状态不自动刷新（最关键）

### 现象
- 点击 "Start Local Scan" 后，任务卡片出现在 Analysis Tasks 列表，状态为 ⏳ PENDING
- Worker 实际在 0.2 秒内就完成了扫描（日志确认 status=completed）
- 但 Dashboard 上的任务**永远停在 PENDING**，进度条不动
- 只有手动刷新浏览器页面才能看到最新状态

### 根因
Dashboard 用 `st.session_state.tasks` 存储任务列表，任务创建时 status="pending"。之后没有任何代码去轮询 API 检查任务是否完成。

### 期望行为
1. 任务提交后，Dashboard 自动轮询 `GET /api/v1/tasks/{task_id}` 检查状态
2. 当任务状态变为 completed 时：
   - 更新任务卡片：PENDING → ✅ COMPLETED
   - 进度条从 0% → 100%
   - 自动获取报告数据（findings、summary）
   - 自动选中该任务并在 Report Preview 显示结果
3. 轮询间隔：2 秒
4. 任务完成后停止轮询

### 技术参考

API 返回的任务状态格式：
```json
{
  "task_id": "cr-20260822-33c1909a",
  "status": "completed",
  "progress": 100,
  "agent_status": {
    "agent_1_static": "completed",
    "agent_2_semantic": "completed",
    "agent_3_verifier": "completed",
    "agent_4_report": "completed"
  },
  "updated_at": "2026-08-22T10:25:46.594360"
}
```

### Streamlit 实现思路

```python
# 方案 1：st.rerun() + time.sleep 循环
import time

# 在任务列表渲染后，如果有 pending 任务，自动刷新
has_pending = any(t["status"] == "pending" for t in st.session_state.tasks)
if has_pending:
    time.sleep(2)
    # 调用 API 获取最新状态
    for task in st.session_state.tasks:
        if task["status"] == "pending":
            code, data = api_get(f"{API_BASE}/api/v1/tasks/{task['task_id']}")
            if code == 200 and data:
                task["status"] = data.get("status", "pending")
                task["progress"] = data.get("progress", 0)
                if task["status"] == "completed":
                    # 获取报告数据
                    report_code, report = api_get(f"{API_BASE}/api/v1/reports/{task['task_id']}")
                    if report_code == 200:
                        task["findings"] = report.get("findings", [])
                        task["summary"] = report.get("summary", {})
    st.rerun()
```

```python
# 方案 2：st.empty() + 轮询占位符（更流畅）
placeholder = st.empty()
for i in range(30):  # 最多轮询 60 秒
    # 检查所有 pending 任务
    all_done = True
    for task in st.session_state.tasks:
        if task["status"] == "pending":
            code, data = api_get(...)
            if data and data["status"] == "completed":
                task["status"] = "completed"
                # ... 更新任务数据
            else:
                all_done = False
    if all_done:
        break
    time.sleep(2)
st.rerun()
```

### 注意事项
- 轮询时不要阻塞整个页面，用户应该还能看到其他内容
- 轮询超过 60 秒没完成就停止，显示"扫描超时"
- 已完成的任务不要重复轮询

---

## 问题 2：扫描结果太少（只有 1 个 info 级漏洞）

### 现象
Worker 日志显示：
```
[cr-20260822-74e784a3] Static analysis failed: No module named 'agents'
[cr-20260822-74e784a3] Semantic analysis failed: No module named 'agents'
[cr-20260822-74e784a3] Verification failed: No module named 'agents'
Static: 1 findings, Semantic: 0 findings
```

### 根因
`app/tasks.py` 中导入的 `Orchestrator`（来自 `code-risk-agent` 项目）依赖 `agents` 模块，但 Docker 容器中没有这个模块。

环境变量 `CODERISK_PATH=/app/code-risk-agent` 指向的目录在容器中可能不存在或不完整。

### 期望行为
- 扫描应该能检出多个漏洞（至少 5+ 个）
- Damn-Vulnerable-Flask-Application 仓库包含 SQL 注入、XSS、命令注入等多种漏洞

### 可能的解决方案

**方案 A：确保 agents 模块在容器中可用**
- 检查 Dockerfile 是否 COPY 了 code-risk-agent 目录
- 检查 requirements.txt 是否包含 agents 模块的依赖

**方案 B：降级处理**
- 如果 agents 模块不可用，用内置的基础扫描器（正则匹配 + 模式匹配）
- 保证至少能检出常见漏洞（hardcoded secrets、debug mode、known CVE 等）

**方案 C：分离关注点**
- 先不管 agents 模块的问题
- 用 `/demo` 端点的 9 个漏洞数据作为展示
- Dashboard 轮询功能做好后，demo 数据也能自动显示

### 建议
**优先修问题 1（轮询），问题 2 可以用 demo 数据绕过。**

---

## 交付物

修改后的 `dashboard.py`，实现：
1. ✅ 任务状态自动轮询（2 秒间隔）
2. ✅ 任务完成后自动更新 UI（状态、进度条、findings）
3. ✅ 完成后自动选中任务并在 Report Preview 显示结果
4. ✅ 轮询超时处理（60 秒）

## 验证标准

1. `docker compose up --build -d dashboard` 构建成功
2. 点击 "Start Local Scan" 后，任务卡片在 2-5 秒内自动从 PENDING 变为 COMPLETED
3. Report Preview 自动显示漏洞详情
4. 录屏时能看到完整的"提交→扫描→完成→展示结果"流程
