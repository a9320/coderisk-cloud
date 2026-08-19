# 🎯 CodeRisk Cloud — 3-Minute Judge Guide

> **DevNetwork [API + Cloud + AI] Hackathon 2026**  
> **Track:** API + Cloud + AI  
> **Team:** AI溢出安全实验室 (Overflow Security Lab)  
> **Repository:** `coderisk-cloud`  
> **Upstream:** [`code-risk-agent`](https://github.com/a9320/code-risk-agent) — AMD AI DevMaster Hackathon 项目  

---

## ⚡ 30-Second Pitch

**CodeRisk Cloud** 是 [`code-risk-agent`](https://github.com/a9320/code-risk-agent) 的 Cloud-Native API 演进版。

原项目是一个**纯本地 CLI 工具**：4-Agent AI 代码安全分析引擎，零外部网络调用，AMD GPU 本地推理，51 个单元测试，tcpdump 验证离线。  
**CodeRisk Cloud 把它变成了 REST API 服务**：GitHub Webhook 自动触发 → Celery 任务队列 → 同样的 4-Agent 引擎 → 带 SHA-256 数字签名的 PDF 审计报告。

**一句话：** *我们把一个经过验证的本地安全引擎，封装成了企业可用的 Cloud-Native API。*

---

## 🚀 2-Minute Quick Start

### 方式 A：Docker Compose 一键启动（推荐）

```bash
git clone https://github.com/a9320/coderisk-cloud.git
cd coderisk-cloud
docker-compose up --build

# 验证服务
curl http://localhost:8000/health
# → {"status": "ok", "checks": {"redis": true, "celery_worker": true}}

# 运行验证脚本
chmod +x verify.sh && ./verify.sh
# → ✅ All checks passed
```

### 方式 B：Bruno API 测试集（9 个用例）

```bash
cd bruno/
# Bruno CLI: bru run --env local
# 覆盖：健康检查、GitHub 分析、ZIP 上传、认证失败、任务查询、报告获取
```

### 方式 C：Streamlit Dashboard

```bash
streamlit run app/dashboard.py --server.port 8501
# 浏览器打开 http://localhost:8501
# 提交 GitHub 仓库 → 看实时进度 → 下载 PDF 报告
```

---

## 🏗️ 架构：不是重写，是封装

```
┌─────────────────────────────────────────────────────────────┐
│                    CodeRisk Cloud (NEW)                     │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  FastAPI     │  Celery      │  Redis       │  Streamlit   │
│  Gateway     │  Worker      │  Queue       │  Dashboard   │
│  (8 端点)    │  (任务调度)   │  (状态/缓存)  │  (可视化)    │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬────────┘
       │              │              │              │
       └──────────────┴──────┬───────┴──────────────┘
                             │
                    ┌────────▼────────┐
                    │  code-risk-agent │  ← 原项目核心引擎
                    │  (git submodule) │     零改动接入
                    └────────┬────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                     │
       ▼                     ▼                     ▼
  ┌─────────┐          ┌─────────┐          ┌─────────┐
  │ Agent 1 │          │ Agent 2 │          │ Agent 3 │
  │ Static  │    →     │Semantic │    →     │ Deep    │
  │(27 rules│          │(LLM/GPU)│          │Verifier │
  └─────────┘          └─────────┘          └─────────┘
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Agent 4       │
                    │ Report Generator│
                    │ JSON/SARIF/PDF  │
                    └─────────────────┘
```

**关键设计：Cloud 层与引擎层解耦**
- Cloud 层（FastAPI/Celery/Redis/Webhook）负责**接入、调度、交付**
- 引擎层（`code-risk-agent` git submodule）负责**分析、验证、推理**
- 引擎层**零外部网络调用**，Cloud 层仅有 Nutrient DWS PDF 生成一个外部依赖

---

## 📊 能力矩阵：原项目 vs Cloud 版本

| 能力 | 原项目 (CLI) | Cloud 版本 (API) | 说明 |
|------|-------------|-----------------|------|
| 4-Agent 分析引擎 | ✅ 完整 | ✅ 复用原引擎 | 通过 git submodule 接入，零改动 |
| 27 条内置规则 | ✅ C+Python | ✅ 同上 | 静态分析层 |
| 污点分析 | ✅ 单函数追踪 | ✅ 同上 | 数据流追踪 |
| 本地 CVE/OSV 数据库 | ✅ SQLite+JSON | ✅ 同上 | 零网络依赖 |
| 双重记忆系统 | ✅ Correct+Error | ✅ 同上 | 跨扫描学习 |
| AMD ROCm GPU 加速 | ✅ 29.4 t/s | ✅ 同上 | Qwen2.5-Coder-32B |
| 51 个单元测试 | ✅ pytest | ✅ 复用 | `tests/` 目录 |
| **REST API** | ❌ | ✅ 8 端点 | FastAPI + Pydantic v2 |
| **GitHub Webhook** | ❌ | ✅ HMAC 签名 | Push 自动触发 |
| **ZIP 上传分析** | ❌ | ✅ 安全防护 | 炸弹/遍历/大小限制 |
| **任务队列** | ❌ | ✅ Celery+Redis | 异步 + 水平扩展 |
| **PDF 审计报告** | ❌ Markdown | ✅ Nutrient DWS | SHA-256 数字签名 |
| **SARIF 输出** | ✅ | ✅ 扩展 | 兼容 GitHub Code Scanning |
| **Streamlit 面板** | ❌ | ✅ 实时监控 | 进度条 + Agent 状态 |
| **Bruno 测试** | ❌ | ✅ 9 个用例 | API 全链路覆盖 |
| **Docker Compose** | ❌ | ✅ CPU+GPU 模式 | 一键部署 |

**新增代码量：** Cloud 层 1,785 行（FastAPI/Celery/Dashboard/Client），引擎层复用原项目。

---

## ✅ 已完成验证

| 验证项 | 结果 | 位置 |
|-------|------|------|
| Docker Compose 启动 | ✅ | `docker-compose up --build` |
| 健康检查端点 | ✅ | `GET /health` |
| Bruno API 测试（9 个） | 9/9 通过 | `bruno/` |
| ZIP 安全上传 | ✅ | 炸弹/遍历/大小/数量限制 |
| GitHub Webhook HMAC | ✅ | `X-Hub-Signature-256` 验证 |
| 报告隔离 | ✅ | API Key 哈希绑定 |
| Nutrient DWS PDF 生成 | ✅ | 真实 API 调用 |
| 原项目 51 个单元测试 | ✅ | `tests/`（pytest） |
| 零网络调用（分析引擎） | ✅ | 引擎层无外部调用 |

---

## ⚠️ 已知限制（Honest Limitations）

1. **Nutrient DWS 外部依赖**：PDF 生成需要 Nutrient DWS API Key，这是 Cloud 版本唯一的外部网络调用。无 Key 时回退到 JSON/SARIF 输出。
2. **GPU 可选但影响深度**：Agent 2（语义分析）优先使用本地 AMD GPU。CPU 模式下分析深度降低（参考原项目基准：GPU 29.4 t/s vs CPU 6.8 t/s）。
3. **单租户部署**：当前为单实例设计，多租户需要额外反向代理层。
4. **语言覆盖**：引擎层支持 C + Python，Java/Go/Rust 在原项目 Roadmap 中。
5. **LLM 幻觉不可完全消除**：Agent 3（深度验证）过滤误报，但无法做到 100%。
6. **记忆系统需多次扫描**：双重记忆在首次扫描时未激活，需要 2+ 次同一代码库扫描才能发挥效果。

---

## 🎥 Demo 视频

- **时长：** 3 分 45 秒
- **流程：** GitHub Push → Webhook 触发 → Dashboard 实时 4-Agent 进度 → PDF 报告下载 → SHA-256 签名验证
- **链接：** [待补充]

---

## 🏆 为什么我们应该赢

| 维度 | 我们的做法 | 常见做法 |
|------|-----------|---------|
| **引擎深度** | 4-Agent + 污点分析 + 双重记忆 + 本地 CVE 库 | 单 Agent 或简单 LLM 调用 |
| **隐私保障** | 源码不出基础设施（本地 GPU + 本地 DB） | 发送到 OpenAI/Claude API |
| **可信度** | SHA-256 签名 PDF + 三重交叉验证 | 普通文本报告 |
| **自动化** | GitHub Webhook → Celery 队列 → 自动交付 | 仅手动上传 |
| **可验证** | verify.sh + 51 个引擎测试 + 9 个 API 测试 | 仅 README 说明 |
| **演进清晰** | CLI → API 的明确演进路径，非从零造轮子 | 缺乏上游项目支撑 |

---

## 📬 联系

- **Cloud 版本：** [@a9320/coderisk-cloud](https://github.com/a9320/coderisk-cloud)
- **原引擎：** [@a9320/code-risk-agent](https://github.com/a9320/code-risk-agent)
- **详细文档：** `项目完整文档.md`（中文，12 章）

---

*CodeRisk Cloud v1.0.0 — 从「本地安全引擎」到「企业 Cloud-Native API」*  
*AI溢出安全实验室 | DevNetwork Hackathon 2026*
