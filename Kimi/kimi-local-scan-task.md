# Kimi 任务书：支持本地目录扫描（真实分析）

## 背景

Docker 容器无法连接 github.com（ConnectionRefusedError），导致真实扫描失败。httpbin.org 能通，说明容器网络本身没问题，是 github.com 被特定阻断。

**目标：** 支持扫描本地目录（宿主机挂载），实现真实分析而不是 demo 预置数据。

## 整体方案

### 架构变更

```
宿主机 D:\desk-top\repos\        Docker 容器
  └── Damn-Vulnerable-Flask-Application/   →   /repos/Damn-Vulnerable-Flask-Application/  (volume mount)
                                    ↓
                              Worker 扫描本地目录
                                    ↓
                              API 返回真实结果
```

### 需要改的文件

1. **docker-compose.yml** — 给 Worker 和 API 添加 volume 挂载
2. **app/tasks.py**（Worker）— 支持 `source: "local"` 模式，直接读本地目录
3. **app/api.py**（API）— 新增 `/scan-local` 端点，接受本地路径
4. **dashboard.py** — 新增 "Local Scan" 选项

---

## 需求 1：docker-compose.yml 添加 volume 挂载

```yaml
# 在 worker 服务下添加 volumes
worker:
  volumes:
    - ./repos:/repos:ro  # 宿主机 repos 目录挂载到容器内 /repos

# 在 api 服务下也添加（如果 API 需要验证路径存在）
api:
  volumes:
    - ./repos:/repos:ro
```

## 需求 2：Worker 支持本地目录扫描

修改 `app/tasks.py` 中的 `analyze_codebase_task` 函数：

当前逻辑：
```python
# 只支持 github 克隆
if source == "github":
    git clone repo_url → /tmp/task_id/
    scan /tmp/task_id/
```

新增逻辑：
```python
# 支持本地目录
if source == "local":
    local_path = payload.get("local_path")  # 例如 "/repos/Damn-Vulnerable-Flask-Application"
    if not os.path.isdir(local_path):
        raise ValueError(f"Local path not found: {local_path}")
    scan_dir = local_path  # 直接扫描，不需要克隆
```

关键点：
- 本地模式跳过 git clone 步骤
- 其余扫描流程（静态分析、语义分析、验证）保持不变
- 确保路径规范化，防止路径遍历攻击（只允许 /repos/ 下的路径）

## 需求 3：API 新增 `/scan-local` 端点

在 `app/api.py` 中新增：

```python
@app.post("/scan-local")
async def scan_local(request: Request):
    """
    扫描本地目录（用于 Docker 环境无法访问 GitHub 的场景）
    Body: {"local_path": "/repos/Damn-Vulnerable-Flask-Application"}
    """
    body = await request.json()
    local_path = body.get("local_path", "")
    
    # 安全校验：只允许 /repos/ 开头的路径
    if not local_path.startswith("/repos/"):
        raise HTTPException(400, "Path must be under /repos/")
    
    # 提交 Celery 任务
    task = analyze_codebase.delay(
        source="local",
        local_path=local_path,
        # ... 其他参数
    )
    return {"task_id": task.id, "status": "pending"}
```

## 需求 4：Dashboard 添加 Local Scan 选项

在 Dashboard 的 "Submit New Analysis" 表单中：

1. 添加一个 "Scan Mode" 选择器：`GitHub` / `Local`
2. 选择 `Local` 时：
   - 隐藏 "Repository URL" 和 "Branch" 输入框
   - 显示 "Local Path" 输入框（下拉选择 /repos/ 下的目录）
   - 或者显示一个固定的 demo 路径：`/repos/Damn-Vulnerable-Flask-Application`
3. 点击 "Start Analysis" 时调用 `/scan-local` 端点

### 具体 UI 变更

```
Scan Mode:  [GitHub ▼]  [Local]

选择 Local 后：
┌─────────────────────────────────┐
│ Local Path                       │
│ [/repos/flask-vulnerable-app ▼] │
│                                  │
│ [🚀 Start Analysis]             │
└─────────────────────────────────┘
```

## 需求 5：宿主机准备测试仓库

部署前在宿主机执行：

```powershell
# 创建 repos 目录
mkdir D:\desk-top\coderisk-cloud\repos

# 测试仓库已克隆
cd D:\desk-top\coderisk-cloud\repos
# 已有：Damn-Vulnerable-Flask-Application/
```

## 验证流程

```powershell
# 1. 测试仓库已就绪
# D:\desk-top\coderisk-cloud\repos\Damn-Vulnerable-Flask-Application\

cd D:\desk-top\coderisk-cloud
docker compose up --build -d

# 2. 测试 API
curl.exe -X POST http://localhost:8000/scan-local -H "Content-Type: application/json" -d "{\"local_path\": \"/repos/Damn-Vulnerable-Flask-Application\"}"

# 4. 查看任务状态（用返回的 task_id）
curl.exe http://localhost:8000/tasks/<task_id>

# 5. 打开 Dashboard，选择 Local 模式，点击 Start Analysis
# 6. 等待真实扫描完成，截图
```

## 交付物

1. 修改后的 `docker-compose.yml`
2. 修改后的 `app/tasks.py`
3. 修改后的 `app/api.py`
4. 修改后的 `dashboard.py`

## 验证标准

1. `docker compose up --build -d` 构建成功
2. `/scan-local` 端点返回 task_id
3. Worker 真实扫描本地目录（不是瞬间返回预置数据）
4. 扫描完成后 Dashboard 显示真实漏洞结果
5. 结果与 `/demo` 端点的预置数据不同（证明是真实分析）
