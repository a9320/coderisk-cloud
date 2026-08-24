# CodeRisk Cloud — 当前状态与测试结果

## 项目概况

- **仓库：** https://github.com/a9320/coderisk-cloud
- **子模块：** https://github.com/a9320/code-risk-agent
- **本地路径：** D:\desk-top\coderisk-cloud
- **技术栈：** FastAPI + Celery + Redis + Docker + code-risk-agent 引擎

## 架构

```
┌─────────────────────────────────────────────┐
│  API 层 (app/)                               │
│  main.py — FastAPI 路由（11 个端点）          │
│  tasks.py — Celery 任务（4 Agent 流水线）     │
│  config.py — 配置管理                        │
│  models.py — Pydantic 数据模型               │
│  dashboard.py — Streamlit 看板               │
│  demo_fixture.py — Demo 端点预置数据         │
│  nutrient_client.py — PDF 生成客户端         │
├─────────────────────────────────────────────┤
│  引擎层 (code-risk-agent/)                   │
│  agents/static_analyzer.py — 模式匹配        │
│  agents/semantic_analyzer.py — LLM 语义分析  │
│  agents/deep_verifier.py — 交叉验证          │
│  agents/report_generator.py — 报告生成       │
│  core/models.py — 数据模型（CodeFile/Risk）   │
│  core/taint_analyzer.py — 污点分析           │
│  core/dependency_scanner.py — 依赖扫描       │
│  core/cve_client.py — CVE 查询（本地+API）    │
│  core/llm_client.py — LLM 客户端             │
├─────────────────────────────────────────────┤
│  Docker 4 容器                               │
│  redis / api / worker / dashboard            │
└─────────────────────────────────────────────┘
```

## 分析流水线（4 Agent）

```
代码输入
  ↓
Agent 1: 静态分析（StaticAnalyzer.analyze_batch）
  ├── C 语言模式（缓冲区溢出、格式化字符串等）
  └── Python/Flask 模式（20 条规则：SQL注入/SSTI/XSS/命令注入等）
  ↓
Agent 1b: 污点分析（TaintAnalyzer）
  ├── C: argv/getenv/scanf → system/exec/sprintf
  └── Python: request.args/form → eval/exec/os.system
  ↓
Agent 1c: 依赖扫描（scan_project_dependencies）
  ├── requirements.txt → 本地 OSV 数据库
  └── package.json → 本地漏洞字典
  ↓
Agent 2: 语义分析（SemanticAnalyzer，需 LLM）
  └── LLM 不可用时跳过
  ↓
Agent 3: 深度验证（DeepVerifier.verify_batch）
  ├── 交叉验证：模式匹配 + 污点分析结果去重
  ├── CVE 查询：本地 SQLite → NVD API 回退
  └── 置信度调整
  ↓
Agent 4: 报告生成（JSON/SARIF/PDF）
```

## Cloud↔引擎 数据转换

**问题：** API 层用 `dict` 传递数据，引擎层用 `Risk`/`CodeFile` Pydantic 对象。两层之间需要转换。

**转换函数（在 tasks.py 中）：**

| 函数 | 方向 | 说明 |
|------|------|------|
| `_scan_code_files(work_dir)` | 目录 → `list[CodeFile]` | 扫描 .c/.h/.py 文件，调用 `CodeFile.from_path()` |
| `_dict_to_risk(finding)` | `dict` → `Risk` | severity/confidence/language 健壮映射，含 Evidence 构造 |
| `_risk_to_dict(risk)` | `Risk` → `dict` | 提取 evidence snippet/agent，输出 category/cwe/code_snippet |

**调用链：**
- `_run_static_analysis` → `_scan_code_files` + `analyzer.analyze_batch` + `_risk_to_dict`
- `_run_semantic_analysis` → `_scan_code_files` + `analyzer.analyze` + `_risk_to_dict`
- `_run_verification` → `_scan_code_files` + `_dict_to_risk` × N + `verifier.verify_batch` + `_risk_to_dict` × N

## 已完成的修复

### 1. static_analyzer.py 正则语法错误（已修复）
- **问题：** `r"SECRET_KEY\s*=\s*['\"][^'"]+['\"]"` — `\"` 在原始字符串里导致字符串提前闭合
- **影响：** 20 条 Flask 规则全部无法加载，Python 项目扫描结果为 0
- **修复：** 改为非原始字符串 `"SECRET_KEY\\s*=\\s*['\"][^'"]+['\"]"`

### 2. tasks.py _run_dependency_scan 字典当对象访问（已修复）
- **问题：** `scan_project_dependencies()` 返回 `list[dict]`，但代码用 `r.severity.value` 访问
- **影响：** `AttributeError`，依赖扫描直接崩溃
- **修复：** 改为 `r.get("cwe")` 等字典访问

### 3. tasks.py _run_verification confidence 硬编码（已修复）
- **问题：** 所有 findings 的 confidence 被设为 `Confidence.LOW`
- **影响：** 报告中所有漏洞置信度都是 LOW
- **修复：** 根据百分比映射回 HIGH(>=70)/MEDIUM(>=40)/LOW(<40)

### 4. llm_client.py ChatML token 错误（已修复）
- **问题：** `_IM_START = "<im_start>"` 应为 `"<|im_start|>"`
- **影响：** 本地 llama-cpp-python 推理时 prompt 格式错误
- **修复：** 与 Qwen2.5 tokenizer 对齐

### 5. CVE 数据库构建太慢（已修复）
- **问题：** Docker build 时下载 NVD 数据（4 年，几百 MB），从国内下载超时
- **修复：** Dockerfile 跳过 CVE 下载，CVEClient 增加 NVD API 回退

## 测试结果

### 修复前（2026-08-24 13:49）
```
task_id: cr-20260824-dab24f77
结果：1 CRITICAL + 1 INFO

CRITICAL: TAINT-8071 CWE-95 eval 注入（app.py:120）— 污点分析
INFO: 静态分析报错 — SyntaxError on line 360（正则 bug）
```

### 修复后（2026-08-24 22:01）
```
task_id: cr-20260824-b970c74a
结果：3 CRITICAL + 1 HIGH

CRITICAL  80%  eval() 代码注入 (CWE-95)           app.py:120  静态分析
CRITICAL  80%  SSTI 模板注入 (CWE-1336)            app.py:205  静态分析
CRITICAL  50%  污点分析: HTTP→eval (CWE-95)         app.py:120  污点分析
HIGH      50%  依赖漏洞: requests 2.28.1 (CWE-295)  requirements.txt  依赖扫描
```

### 改进幅度
- 漏洞检出数：2 → 4（+100%）
- CRITICAL 检出：1 → 3（+200%）
- 静态分析：从崩溃（0 条）→ 正常工作（2 条）
- 依赖扫描：从崩溃（0 条）→ 正常工作（1 条）
- CVE 交叉验证：成功附带 CVE 编号 + CVSS 评分

## 已知问题

### 未修复
1. **_scan_code_files 只支持 .c/.h/.py** — JS/Java/Go 等语言跳过
2. **nutrient_client.py sign_pdf 是空操作** — PDF 签名形同虚设
3. **hmac.compare_digest 非 ASCII 字符问题** — API Key 含非 ASCII 会 500
4. **TaintFlow `→` 显示为 `â`** — UTF-8 编码问题（title 里 `→` 显示为 `â`）

### 待优化
1. **SSTI 规则误报** — `render_template_string()` 不一定有用户输入，当前是静态匹配
2. **依赖扫描 CVE 匹配精度** — `requests 2.28.1` 匹配到了 `CVE-2002-0862`（2002 年的 Windows 漏洞），不对
3. **Agent 2 语义分析跳过** — 无 LLM 时完全跳过，可以考虑用规则补充

## Docker 配置

```yaml
# docker-compose.yml 关键配置
services:
  redis:  redis:7-alpine
  api:    uvicorn app.main:app --host 0.0.0.0 --port 8000
  worker: celery -A app.tasks worker --loglevel=info --concurrency=2
  dashboard: streamlit run app/dashboard.py --server.port=8501

# 环境变量
CODERISK_API_KEY=dev-key-change-in-production
PYTHONPATH=/app:/app/code-risk-agent
CODERISK_PATH=/app/code-risk-agent
```

## API 端点

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | / | 根路径信息 | ❌ |
| GET | /health | 健康检查 | ❌ |
| GET | /demo | Demo 预置结果 | ❌ |
| POST | /api/v1/analyze | GitHub 仓库分析 | ✅ |
| POST | /api/v1/analyze/upload | ZIP 上传分析 | ✅ |
| POST | /api/v1/scan-local | 本地目录扫描 | ✅ |
| GET | /api/v1/tasks/{id} | 任务状态 | ✅ |
| GET | /api/v1/reports/{id} | 获取报告 | ✅ |
| GET | /api/v1/reports/{id}/pdf | 下载 PDF | ✅ |
| POST | /api/v1/webhooks/github | GitHub Webhook | 签名 |

## 文件清单（核心文件）

```
app/
├── main.py              # FastAPI 路由（11 端点）
├── config.py            # 配置管理（环境变量读取）
├── models.py            # Pydantic 数据模型
├── tasks.py             # Celery 任务（4 Agent 流水线 + 转换层）
├── dashboard.py         # Streamlit 看板
├── demo_fixture.py      # Demo 预置数据（9 条漏洞）
└── nutrient_client.py   # Nutrient PDF 生成客户端

code-risk-agent/
├── agents/
│   ├── static_analyzer.py    # 模式匹配（C 27条 + Python 20条规则）
│   ├── semantic_analyzer.py  # LLM 语义分析
│   ├── deep_verifier.py      # 交叉验证 + CVE 查询
│   └── report_generator.py   # 报告生成（JSON/SARIF/终端）
├── core/
│   ├── models.py             # CodeFile/Risk/Severity/Confidence
│   ├── taint_analyzer.py     # 污点分析（C + Python）
│   ├── dependency_scanner.py # 依赖扫描（OSV + 本地字典）
│   ├── cve_client.py         # CVE 查询（本地 SQLite + NVD API 回退）
│   ├── llm_client.py         # LLM 客户端（HTTP + llama-cpp-python）
│   ├── memory.py             # 记忆层
│   ├── semgrep_runner.py     # Semgrep 集成
│   ├── attack_knowledge.py   # 攻击知识库
│   └── retry.py              # 重试工具
├── scripts/
│   ├── download_cve_data.py  # CVE 数据库构建
│   └── download_osv_data.py  # OSV 数据下载
└── tests/                    # 引擎层测试

Docker
├── Dockerfile
├── docker-compose.yml
├── docker-compose.gpu.yml
└── requirements.txt

测试
├── tests/conftest.py
├── tests/test_health.py
├── tests/test_demo.py
├── tests/test_auth.py
└── verify.sh
```
