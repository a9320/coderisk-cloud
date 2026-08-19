# CodeRisk Cloud — Docker 部署指南

> 一键启动 CodeRisk Cloud 全栈服务（API + Worker + Redis + Dashboard）

---

## 快速开始（30 秒）

```bash
# 1. 克隆项目
git clone https://github.com/a9320/coderisk-cloud.git
cd coderisk-cloud

# 2. 准备 CodeRisk Agent 源码（必须）
git clone https://github.com/a9320/code-risk-agent.git

# 3. 配置环境变量（复制模板并编辑）
cp .env.example .env
# 编辑 .env，填入 NUTRIENT_DWS_API_KEY 等

# 4. 一键启动
docker-compose up --build

# 5. 访问服务
# API Docs:    http://localhost:8000/docs
# Dashboard:   http://localhost:8501
# Health:      http://localhost:8000/health
```

---

## 架构说明

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Redis     │────▶│  API (FastAPI)│────▶│   Worker    │────▶│  Dashboard  │
│  (Broker)   │     │  Port 8000   │     │  (Celery)   │     │ Port 8501   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Nutrient   │
                    │  DWS API    │
                    └─────────────┘
```

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| redis | coderisk-redis | — | 任务队列 + 状态缓存 |
| api | coderisk-api | 8000 | FastAPI REST API |
| worker | coderisk-worker | — | Celery 4-Agent 分析流水线 |
| dashboard | coderisk-dashboard | 8501 | Streamlit 管理界面 |

---

## 前置条件

### 必需
- Docker 20.10+ & Docker Compose 2.20+
- 4GB+ 可用内存
- CodeRisk Agent 源码（`git clone` 到 `./code-risk-agent`）

### 可选（GPU 加速）
- AMD GPU + ROCm 驱动（用于 Worker LLM 加速）
- 或 NVIDIA GPU + CUDA（需修改 `docker-compose.gpu.yml`）

---

## 环境变量

复制 `.env.example` 为 `.env` 并配置：

```env
# 必需
CODERISK_API_KEY=your-secure-api-key

# 可选（Nutrient PDF 生成）
NUTRIENT_DWS_API_KEY=your-nutrient-key

# 可选（GitHub Webhook）
GITHUB_WEBHOOK_SECRET=your-webhook-secret

# 可选（Worker 并发）
WORKER_CONCURRENCY=2

# 可选（GPU 型号覆盖，AMD 专用）
HSA_OVERRIDE_GFX_VERSION=10.3.0
```

> ⚠️ **安全提醒**：永远不要将 `.env` 提交到 git。已配置 `.gitignore` 自动排除。

---

## 运行模式

### 模式 A：CPU 模式（默认，无 GPU）

适合评审快速体验、无 GPU 环境：

```bash
docker-compose up --build
```

- Worker 使用 CPU 运行静态分析（Agent 1）
- LLM 语义分析（Agent 2/3）需要外部 llama-server 或降级处理
- 所有功能可用，分析速度较慢

### 模式 B：AMD GPU 模式（开发/生产）

适合你的 AMD GPU 环境（192GB VRAM）：

```bash
# 确认 ROCm 可用
rocm-smi

# 启动（加载 GPU 扩展配置）
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

- Worker 容器挂载 `/dev/kfd` 和 `/dev/dri`
- 自动设置 `GGML_HIP=ON` 环境变量
- llama.cpp 利用 AMD GPU 加速推理

### 模式 C：仅 API + Dashboard（Worker 外置）

适合 Worker 在另一台 GPU 服务器运行：

```bash
# 只启动 API + Redis + Dashboard
docker-compose up api redis dashboard

# 在 GPU 服务器单独启动 Worker
celery -A app.tasks worker --loglevel=info
```

---

## 常用命令

```bash
# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f api
docker-compose logs -f worker

# 重启单个服务
docker-compose restart worker

# 进入容器调试
docker-compose exec api bash
docker-compose exec worker bash

# 完全清理
docker-compose down -v
```

---

## 验证部署

### 1. 健康检查
```bash
curl http://localhost:8000/health
```
预期：`{"status": "ok", "checks": {"redis": true, ...}}`

### 2. 提交分析任务
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Authorization: Bearer dev-key-change-in-production" \
  -d '{"source": "github", "repo_url": "https://github.com/a9320/code-risk-agent", "output_formats": ["json"]}'
```

### 3. ZIP 上传
```bash
curl -X POST http://localhost:8000/api/v1/analyze/upload \
  -H "Authorization: Bearer dev-key-change-in-production" \
  -F "file=@test-code.zip"
```

### 4. Dashboard
打开 http://localhost:8501，提交仓库 URL 并观察任务进度。

---

## 故障排查

| 问题 | 原因 | 解决 |
|------|------|------|
| `Connection refused` to Redis | Redis 未启动或端口冲突 | `docker-compose ps` 检查 redis 状态 |
| Worker 日志显示 `ModuleNotFoundError` | `code-risk-agent` 未挂载 | 确认 `./code-risk-agent` 目录存在且非空 |
| PDF 生成失败 | Nutrient Key 未配置或无效 | 检查 `.env` 中 `NUTRIENT_DWS_API_KEY` |
| GPU 模式 `rocm-smi` 报错 | ROCm 驱动未安装 | 宿主机安装 ROCm，或切换 CPU 模式 |
| ZIP 上传 413 | 文件超过 100MB | 拆分 ZIP 或调整 `client_max_body_size` |

---

## 生产部署建议

1. **更换 API Key**：将默认 `dev-key-change-in-production` 替换为强密码
2. **启用 HTTPS**：使用 Traefik / Nginx 反向代理 + Let's Encrypt
3. **持久化存储**：将 `./reports` 挂载到云存储（AWS EFS / NAS）
4. **监控**：Prometheus + Grafana 采集 Celery 指标
5. **日志聚合**：ELK / Loki 收集多容器日志

---

*CodeRisk Cloud v1.0.0 — AI溢出安全实验室*
