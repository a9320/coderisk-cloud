# CodeRisk Cloud — Demo Video Script v1

> DevNetwork [API + Cloud + AI] Hackathon 2026
> 目标：Overall Winner ($12,500) + Nutrient DWS Challenge ($1,500)
> 时长：3 分钟（180 秒）
> 语言：英文（旁白 + 字幕）

---

## [00:00 - 00:15] Opening — The Problem

**画面：**
- 00:00-00:03：黑屏渐入，显示新闻标题截图（可 mock）
  - "Major data breach exposes 50M user records — root cause: unpatched vulnerability in production code"
  - "Supply chain attack via compromised dependency"
- 00:03-00:08：快速切换开发者写代码的屏幕录制（加速 2x）
- 00:08-00:15：画面定格在 GitHub PR 页面，红字提示 "Security check failed"

**旁白：**
> "Every day, developers push code with hidden vulnerabilities. But enterprise security teams face a dilemma."

**字幕：**
Every day, developers push code with hidden vulnerabilities.
But enterprise security teams face a dilemma.

**BGM：** 紧张感电子乐，节奏渐强

---

## [00:15 - 00:30] The Dilemma

**画面：**
- 00:15-00:20：左右分屏对比
  - 左侧：Snyk / GitHub Copilot Security 界面 → 红色箭头指向 "Uploading source code to cloud..."
  - 右侧：企业合规文档（HIPAA / GDPR / 等保 2.0）→ 红色高亮 "Source code must not leave premises"
- 00:20-00:25：中间出现巨大红色 ❌，文字 "Compliance Violation Risk"
- 00:25-00:30：画面变暗，出现问号 "Is there a way to have both AI-powered security AND full data sovereignty?"

**旁白：**
> "Cloud AI tools require uploading your source code — violating HIPAA, GDPR, and corporate policy. But local tools like Semgrep cannot understand code logic, leading to floods of false positives."

**字幕：**
Cloud AI tools require uploading your source code.
But local tools cannot understand code logic.

---

## [00:30 - 00:45] Solution Introduction

**画面：**
- 00:30-00:35：CodeRisk Cloud Logo 动画（🛡️ + 文字）
- 00:35-00:40：架构图动画（从本地 CLI 向上生长为 Cloud API）
  - 底部：AMD GPU 图标 + "192GB HBM3"
  - 中部：4-Agent 流水线（Static → Semantic → Verifier → Report）
  - 顶部：FastAPI Gateway + Nutrient DWS PDF
- 00:40-00:45：画面定格，出现 One-Liner：
  **"Local AI inference. Cloud API delivery. Zero code leaves your infrastructure."**

**旁白：**
> "Meet CodeRisk Cloud. The only AI code security API that runs LLM inference locally on AMD GPUs. Your source code never leaves your infrastructure."

**字幕：**
CodeRisk Cloud.
Local AI inference. Cloud API delivery.
Zero code leaves your infrastructure.

**BGM：** 转为科技感、向上的旋律

---

## [00:45 - 01:15] Live Demo Part 1 — Submit Analysis

**画面：**
- 00:45-00:50：终端窗口（字体放大到 24px，确保评审看得清）
  ```bash
  $ curl -X POST http://api.coderisk.cloud/api/v1/analyze \
      -H "Authorization: Bearer $API_KEY" \
      -d '{
        "source": "github",
        "repo_url": "https://github.com/a9320/code-risk-agent",
        "output_formats": ["json", "sarif", "pdf"]
      }'
  ```
- 00:50-00:55：回车执行，JSON 响应高亮显示
  ```json
  {
    "task_id": "cr-20260818-b7e5ec64",
    "status": "pending",
    "message": "Analysis task created..."
  }
  ```
- 00:55-01:05：切换到 Dashboard（Streamlit 界面）
  - 任务列表出现新行：cr-20260818-b7e5ec64 | 🔄 ANALYZING | 进度条从 0% → 55%
  - Agent Pipeline 展开：Static ✅ → Semantic 🔄 → Verifier ⏳ → Report ⏳
- 01:05-01:15：切换到 Celery Worker 日志（终端）
  - 显示 Agent 1 completed, Agent 2 running...
  - 强调文字："Running on AMD MI300X — 192GB VRAM"

**旁白：**
> "Submit a repository via our REST API. The 4-Agent pipeline kicks in immediately. Agent 1 runs static pattern matching on CPU, while Agent 2 performs semantic analysis on the AMD GPU — in parallel."

**字幕：**
Submit via REST API.
4-Agent pipeline: Static + Semantic in parallel.
Running on AMD MI300X with 192GB VRAM.

---

## [01:15 - 01:45] Live Demo Part 2 — The Report

**画面：**
- 01:15-01:25：Dashboard 刷新，状态变为 ✅ COMPLETED
  - 点击 "📄 Report" 按钮
  - Severity Summary 卡片弹出：CRITICAL 1 | HIGH 2 | MEDIUM 3
- 01:25-01:35：Findings 表格展示
  - 第一行高亮：🔴 CRITICAL | SQL Injection | app/db.py:42 | CWE-89
  - 第二行：🟠 HIGH | Hardcoded API Key | config.py:12 | CWE-798
  - 点击一行，展开 description 和 fix suggestion
- 01:35-01:45：点击 "⬇️ PDF Report" 下载
  - 屏幕分屏：左侧终端显示 `ls -lh reports/`，右侧打开 PDF
  - PDF 展示：
    - 第 1 页：Header + Severity Summary 卡片（5 色渐变）
    - 第 1 页：Findings 列表，带左色条和 pill badge
    - 第 2 页：🔏 Digitally Signed — SHA-256 哈希值
    - 底部："Powered by Nutrient DWS"

**旁白：**
> "Within seconds, you get a complete security report. JSON and SARIF for your CI/CD pipeline. And a professionally formatted PDF — digitally signed for audit compliance — powered by Nutrient DWS."

**字幕：**
JSON + SARIF for CI/CD.
PDF report: professionally formatted, digitally signed.
Powered by Nutrient DWS.

---

## [01:45 - 02:10] Technical Deep Dive

**画面：**
- 01:45-01:55：架构图再次展示，逐个高亮组件
  - Kong API Gateway（Auth, Rate Limit, Routing）
  - FastAPI + Celery + Redis（异步任务队列）
  - AMD GPU Worker（llama.cpp + ROCm + Qwen2.5-Coder-32B）
  - Nutrient DWS（PDF Conversion + Digital Signature + Viewer）
- 01:55-02:05：关键数据展示（大字体）
  - "4.3× Speedup" — GPU vs CPU inference
  - "Zero external network calls" — tcpdump 截图（来自原 README）
  - "51 unit tests + 9 Bruno API tests" — 代码质量
- 02:05-02:10：GitHub Actions YAML 文件展示
  ```yaml
  - name: CodeRisk Cloud Scan
    run: |
      curl -X POST ${{ secrets.CODERISK_API }} ...
  ```
  - 模拟 PR 评论："⚠️ 3 vulnerabilities found. View full report."

**旁白：**
> "Under the hood, Kong API Gateway handles authentication and rate limiting. Celery distributes tasks across workers. And our AMD GPU runs 32-billion-parameter models locally — four times faster than CPU, with zero external network calls."

**字幕：**
Kong API Gateway + FastAPI + Celery.
AMD GPU: 32B params, 4.3× faster than CPU.
Zero external network calls.

---

## [02:10 - 02:35] Nutrient DWS Sponsor Highlight

**画面：**
- 02:10-02:18：Nutrient DWS Logo + 文字 "Deterministic Document Platform"
- 02:18-02:28：PDF 报告特写（放大）
  - 高亮："Deterministic output" — 每次分析相同输入产生相同报告结构
  - 高亮："Full audit trail" — 报告底部时间戳 + 签名哈希
  - 高亮："Human in the loop" — DWS Viewer 嵌入 Dashboard 的截图
- 02:28-02:35：合规场景展示
  - 金融："SOC 2 Type II audit requires tamper-evident security reports"
  - 医疗："HIPAA mandates documented vulnerability remediation"
  - 政府："等保 2.0 要求源代码不出境"
  - 所有场景 → 都指向 CodeRisk Cloud + Nutrient DWS

**旁白：**
> "Nutrient DWS transforms our raw AI findings into regulator-ready documents. Deterministic output. Full audit trails. And human review via the DWS Viewer — exactly where AI confidence needs a second pair of eyes."

**字幕：**
Nutrient DWS: deterministic output, full audit trails.
Human review where AI needs a second pair of eyes.

**BGM：** 达到高潮

---

## [02:35 - 02:55] Business Model & Vision

**画面：**
- 02:35-02:42：三层架构图（商业模型）
  - 底层：开源 CLI（免费）→ 个人开发者、开源社区
  - 中层：Cloud API（Pay-per-scan）→ 中小企业
  - 顶层：Enterprise（私有化部署）→ 金融、医疗、政府
- 02:42-02:50：快速展示技术路线图
  - "Now: C + Python"
  - "Q4 2026: Java + Go + Rust"
  - "2027: IDE plugins + CI/CD native integration"
- 02:50-02:55：画面定格，出现项目信息
  - GitHub: github.com/a9320/code-risk-agent
  - DevPost: CodeRisk Cloud
  - "Built for DevNetwork Hackathon 2026"

**旁白：**
> "CodeRisk Cloud is designed to become a sustainable business. Open source core for adoption. Cloud API for convenience. And enterprise私有化部署 for regulated industries. From code risk to content trust — our 4-Agent architecture scales across domains."

**字幕：**
Open source → Cloud API → Enterprise.
From code risk to content trust.

---

## [02:55 - 03:00] Closing — Call to Action

**画面：**
- 02:55-02:58：CodeRisk Cloud Logo 居中，背景为深色渐变
- 02:58-03:00：文字逐个弹出
  - "Local Trust."
  - "Global Scale."
  - "CodeRisk Cloud."

**旁白：**
> "Local trust. Global scale. CodeRisk Cloud."

**字幕：**
Local Trust. Global Scale.
CodeRisk Cloud.

**BGM：** 收尾，渐弱至静音

---

## 附录：录制技术规范

### 画面规格
- 分辨率：1920×1080（16:9）
- 终端字体：JetBrains Mono / Fira Code, 24px+
- 浏览器缩放：125%（确保 UI 元素清晰）
- 鼠标高亮：启用光标高亮（如 KeyCastr）

### 音频规格
- 旁白：清晰、中等语速（约 150 WPM）
- BGM：科技感、无歌词、音量低于旁白 12dB
- 总时长：严格控制在 2:55 - 3:05 之间

### 字幕规范
- 字体：Inter / Roboto, 48px
- 位置：画面底部 10%，安全区域内
- 样式：白色文字 + 黑色描边（确保任何背景可读）
- 出现时机：比旁白早 0.2 秒，消失比旁白晚 0.5 秒

### 关键帧截图（建议单独保存，用于 DevPost 封面）
1. 00:30 架构图全屏
2. 01:25 PDF 报告 Severity Summary
3. 02:18 Nutrient DWS 签名特写
4. 02:58 结尾 Logo

---

## 附录：Demo 数据准备

### 推荐扫描目标
- **首选：** `https://github.com/a9320/code-risk-agent`（自己的项目，真实）
- **备选：** `https://github.com/WebGoat/WebGoat`（已知漏洞，展示效果好）
- **Mock 数据：** 如果真实扫描来不及，用以下 4 条 findings：

```json
[
  {
    "severity": "critical",
    "title": "SQL Injection in user_query()",
    "file": "app/db.py",
    "line": 42,
    "rule_id": "CWE-89",
    "description": "User input from request.args directly interpolated into SQL string via f-string. Use parameterized queries.",
    "confidence": 95
  },
  {
    "severity": "high",
    "title": "Hardcoded API Key",
    "file": "config/settings.py",
    "line": 12,
    "rule_id": "CWE-798",
    "description": "Stripe secret key hardcoded as string literal. Move to environment variables or secret manager.",
    "confidence": 92
  },
  {
    "severity": "medium",
    "title": "Missing CSRF Protection",
    "file": "app/views.py",
    "line": 88,
    "rule_id": "CWE-352",
    "description": "POST endpoint /transfer lacks CSRF token validation. Add @csrf_exempt only for intended APIs.",
    "confidence": 78
  },
  {
    "severity": "low",
    "title": "Verbose Error Messages",
    "file": "app/handlers.py",
    "line": 15,
    "rule_id": "CWE-209",
    "description": "Stack trace exposed to client in production. Set DEBUG=False and use generic error pages.",
    "confidence": 85
  }
]
```

> ⚠️ **重要提示：** 如果使用 mock 数据，必须在 Demo 视频开头或结尾明确说明：
> "This demonstration uses pre-populated findings to illustrate the report format. In production, all findings are generated by the 4-Agent analysis pipeline on real code."

---

*脚本版本: v1.0*
*编写: Kimi*
*审核: Weike / lolo*
*目标赛事: DevNetwork [API + Cloud + AI] Hackathon 2026*
