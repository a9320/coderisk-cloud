# Docker 构建问题分析 — 请 Kimi 评估

**日期：** 2026-08-20
**问题来源：** Windows Docker Desktop 运行 `docker compose up --build`

---

## 问题一：uvicorn --reload 内存不足（已修复）

**报错：**
```
_rust_notify.WatchfilesRustInternalError: error in underlying watcher: Cannot allocate memory (os error 12)
```

**原因：** docker-compose.yml 里 uvicorn 带了 `--reload` 参数，它会启动 watchfiles 进程监控文件变化。Docker 容器默认内存有限，watchfiles 的 inotify watcher 分配内存失败。

**已修复：** 去掉 `--reload`，改为普通模式。
```yaml
# 修复前
command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# 修复后
command: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**影响：** 代码修改后需要手动重启容器（`docker compose restart api`），不能热重载。提交评委版本不需要热重载，所以没有影响。

**请 Kimi 评估：** 是否需要保留 `--reload` 作为开发模式？可以加一个 docker-compose.override.yml 给开发者用。

---

## 问题二：health 端点 503（已修复）

**报错：** `/health` 返回 503 Service Unavailable

**原因：** health 端点检查了 3 个组件：Redis + Celery Worker + GPU（rocm-smi）。Docker 里没有 GPU，rocm-smi 不存在，GPU 检查失败，导致整体 503。

**已修复：** GPU 改为可选检查，不影响整体健康状态。
```python
# 修复前
all_ok = all(checks.values())  # GPU 必须通过
# 修复后
core_ok = checks["redis"] and checks["celery_worker"]  # GPU 可选
```

**请 Kimi 评估：** health 端点的设计是否合理？是否需要区分 "core healthy" 和 "fully operational" 两种状态码？

---

## 问题三：Docker Hub 镜像拉取慢

**现象：** WSL 和 Windows 都遇到 Docker Hub 下载卡住（某一层 0B 进度持续 100+ 秒）

**已解决：** Docker Desktop 配置镜像加速
```json
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me"
  ]
}
```

**请 Kimi 评估：** 是否需要在 DOCKER.md 里加镜像加速配置指南？国内用户基本都需要。

---

## 问题四：base image 选择

**当前：** `python:3.12-slim`（~150MB）

**备选：** `python:3.12-alpine`（~50MB，更小但需要改 apt→apk）

**请 Kimi 评估：** 是否值得换成 alpine？优点是镜像更小、下载更快；缺点是需要改 Dockerfile 的包管理器，某些 Python 包在 alpine 上可能需要额外编译。

---

## 当前状态

- ✅ health 端点已修复（GPU 可选）
- ✅ uvicorn --reload 已去掉
- ⏳ 需要 `docker compose up --build` 重新构建验证
- ⏳ 请 Kimi 评估以上 4 个问题

---

## lolo 的建议

1. **问题一** — 去掉 --reload 是正确做法，提交版本不需要热重载
2. **问题二** — GPU 可选是正确设计，但建议返回 `"status": "ok"` + `"gpu": false` 而不是 "degraded"
3. **问题三** — DOCKER.md 应该加镜像加速章节，对国内用户是刚需
4. **问题四** — 暂时保持 slim，alpine 的兼容性风险不值得为省 100MB 冒险
