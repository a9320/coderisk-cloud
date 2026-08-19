# CodeRisk Cloud — Demo 视频脚本 v1（中文版）

> DevNetwork [API + Cloud + AI] Hackathon 2026
> 目标：Overall Winner ($12,500) + Nutrient DWS Challenge ($1,500)
> 时长：3 分钟（180 秒）
> 语言：中文（旁白 + 字幕）

---

## [00:00 - 00:15] 开场 — 问题陈述

**画面：**
- 00:00-00:03：黑屏渐入，显示新闻标题截图（可 mock）
  - "重大数据泄露，5000 万用户记录曝光 — 根源：生产代码中未修补的漏洞"
  - "供应链攻击通过被污染的依赖库入侵"
- 00:03-00:08：快速切换开发者写代码的屏幕录制（2 倍速）
- 00:08-00:15：画面定格在 GitHub PR 页面，红字提示 "Security check failed"

**旁白：**
> "每一天，开发者都在推送带有隐藏漏洞的代码。但企业安全团队面临一个两难困境。"

**字幕：**
每一天，开发者都在推送带有隐藏漏洞的代码。
但企业安全团队面临一个两难困境。

**BGM：** 紧张感电子乐，节奏渐强

---

## [00:15 - 00:30] 困境

**画面：**
- 00:15-00:20：左右分屏对比
  - 左侧：Snyk / GitHub Copilot Security 界面 → 红色箭头指向 "正在上传源代码至云端..."
  - 右侧：企业合规文档（HIPAA / GDPR / 等保 2.0）→ 红色高亮 "源代码不得离开本地环境"
- 00:20-00:25：中间出现巨大红色 ❌，文字 "合规违规风险"
- 00:25-00:30：画面变暗，出现问号 "有没有一种方案，既能享受 AI 安全审计，又能保证数据主权？"

**旁白：**
> "云端 AI 工具要求上传你的源代码 — 这违反了 HIPAA、GDPR 和企业内部政策。但本地工具如 Semgrep 无法理解代码逻辑，导致大量误报。"

**字幕：**
云端 AI 工具要求上传你的源代码。
但本地工具无法理解代码逻辑。

---

## [00:30 - 00:45] 解决方案介绍

**画面：**
- 00:30-00:35：CodeRisk Cloud Logo 动画（🛡️ + 文字）
- 00:35-00:40：架构图动画（从本地 CLI 向上生长为 Cloud API）
  - 底部：AMD GPU 图标 + "192GB HBM3"
  - 中部：4-Agent 流水线（静态分析 → 语义理解 → 深度验证 → 报告生成）
  - 顶部：FastAPI Gateway + Nutrient DWS PDF
- 00:40-00:45：画面定格，出现一句话：
  **"本地 AI 推理。云端 API 交付。源代码永不离开你的基础设施。"**

**旁白：**
> "这就是 CodeRisk Cloud。唯一能在本地 AMD GPU 上运行大语言模型推理的代码安全 API。你的源代码永远不会离开你的基础设施。"

**字幕：**
CodeRisk Cloud。
本地 AI 推理。云端 API 交付。
源代码永不离开你的基础设施。

**BGM：** 转为科技感、向上的旋律

---

## [00:45 - 01:15] 现场演示 Part 1 — 提交分析

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
  - 任务列表出现新行：cr-20260818-b7e5ec64 | 🔄 分析中 | 进度条从 0% → 55%
  - Agent 流水线展开：静态分析 ✅ → 语义分析 🔄 → 深度验证 ⏳ → 报告生成 ⏳
- 01:05-01:15：切换到 Celery Worker 日志（终端）
  - 显示 Agent 1 完成，Agent 2 运行中...
  - 强调文字："运行于 AMD MI300X — 192GB 显存"

**旁白：**
> "通过 REST API 提交代码仓库。4-Agent 流水线立即启动。Agent 1 在 CPU 上运行静态模式匹配，同时 Agent 2 在 AMD GPU 上进行语义分析 — 两者并行执行。"

**字幕：**
通过 REST API 提交。
4-Agent 流水线：静态 + 语义并行分析。
运行于 AMD MI300X，192GB 显存。

---

## [01:15 - 01:45] 现场演示 Part 2 — 报告生成

**画面：**
- 01:15-01:25：Dashboard 刷新，状态变为 ✅ 已完成
  - 点击 "📄 查看报告" 按钮
  - Severity Summary 卡片弹出：严重 1 | 高危 2 | 中危 3
- 01:25-01:35：Findings 表格展示
  - 第一行高亮：🔴 严重 | SQL 注入 | app/db.py:42 | CWE-89
  - 第二行：🟠 高危 | 硬编码 API 密钥 | config.py:12 | CWE-798
  - 点击一行，展开 description 和修复建议
- 01:35-01:45：点击 "⬇️ PDF 报告" 下载
  - 屏幕分屏：左侧终端显示 `ls -lh reports/`，右侧打开 PDF
  - PDF 展示：
    - 第 1 页：Header + Severity Summary 卡片（5 色渐变）
    - 第 1 页：Findings 列表，带左色条和 pill 标签
    - 第 2 页：🔏 数字签名 — SHA-256 哈希值
    - 底部："Powered by Nutrient DWS"

**旁白：**
> "几秒钟内，你就能获得完整的安全报告。JSON 和 SARIF 格式供你的 CI/CD 流水线使用。还有专业排版的 PDF 报告 — 数字签名确保审计合规 — 由 Nutrient DWS 强力驱动。"

**字幕：**
JSON + SARIF 供 CI/CD 使用。
PDF 报告：专业排版，数字签名。
由 Nutrient DWS 强力驱动。

---

## [01:45 - 02:10] 技术深度解析

**画面：**
- 01:45-01:55：架构图再次展示，逐个高亮组件
  - Kong API Gateway（认证、限流、路由）
  - FastAPI + Celery + Redis（异步任务队列）
  - AMD GPU Worker（llama.cpp + ROCm + Qwen2.5-Coder-32B）
  - Nutrient DWS（PDF 转换 + 数字签名 + 在线预览）
- 01:55-02:05：关键数据展示（大字体）
  - "4.3 倍加速" — GPU 对比 CPU 推理
  - "零外部网络调用" — tcpdump 截图（来自原 README）
  - "51 个单元测试 + 9 个 Bruno API 测试" — 代码质量
- 02:05-02:10：GitHub Actions YAML 文件展示
  ```yaml
  - name: CodeRisk Cloud 扫描
    run: |
      curl -X POST ${{ secrets.CODERISK_API }} ...
  ```
  - 模拟 PR 评论："⚠️ 发现 3 个漏洞。查看完整报告。"

**旁白：**
> "底层架构上，Kong API Gateway 处理认证和限流。Celery 将任务分发到多个 Worker。而我们的 AMD GPU 本地运行 320 亿参数模型 — 比 CPU 快 4 倍，且零外部网络调用。"

**字幕：**
Kong API Gateway + FastAPI + Celery。
AMD GPU：320 亿参数，比 CPU 快 4.3 倍。
零外部网络调用。

---

## [02:10 - 02:35] Nutrient DWS 赞助商亮点

**画面：**
- 02:10-02:18：Nutrient DWS Logo + 文字 "确定性文档平台"
- 02:18-02:28：PDF 报告特写（放大）
  - 高亮："确定性输出" — 相同输入每次产生相同报告结构
  - 高亮："完整审计追踪" — 报告底部时间戳 + 签名哈希
  - 高亮："人机协同" — DWS Viewer 嵌入 Dashboard 的截图
- 02:28-02:35：合规场景展示
  - 金融："SOC 2 Type II 审计要求防篡改的安全报告"
  - 医疗："HIPAA 要求记录漏洞修复过程"
  - 政府："等保 2.0 要求源代码不出境"
  - 所有场景 → 都指向 CodeRisk Cloud + Nutrient DWS

**旁白：**
> "Nutrient DWS 将我们的原始 AI 发现转化为监管就绪的文档。确定性输出。完整审计追踪。通过 DWS Viewer 进行人工复核 — 在 AI 信心不足的地方，需要第二双眼睛。"

**字幕：**
Nutrient DWS：确定性输出，完整审计追踪。
在 AI 需要第二双眼睛的地方，进行人工复核。

**BGM：** 达到高潮

---

## [02:35 - 02:55] 商业模式与愿景

**画面：**
- 02:35-02:42：三层架构图（商业模型）
  - 底层：开源 CLI（免费）→ 个人开发者、开源社区
  - 中层：Cloud API（按次付费）→ 中小企业
  - 顶层：企业版（私有化部署）→ 金融、医疗、政府
- 02:42-02:50：快速展示技术路线图
  - "现在：C + Python"
  - "2026 Q4：Java + Go + Rust"
  - "2027：IDE 插件 + CI/CD 原生集成"
- 02:50-02:55：画面定格，出现项目信息
  - GitHub: github.com/a9320/code-risk-agent
  - DevPost: CodeRisk Cloud
  - "为 DevNetwork Hackathon 2026 打造"

**旁白：**
> "CodeRisk Cloud 的设计目标是成为可持续的商业产品。开源核心获取用户。Cloud API 提供便捷。企业私有化部署服务受监管行业。从代码风险到内容信任 — 我们的 4-Agent 架构可以跨领域扩展。"

**字幕：**
开源 → Cloud API → 企业版。
从代码风险到内容信任。

---

## [02:55 - 03:00] 结尾 — 行动号召

**画面：**
- 02:55-02:58：CodeRisk Cloud Logo 居中，背景为深色渐变
- 02:58-03:00：文字逐个弹出
  - "本地可信。"
  - "全球规模。"
  - "CodeRisk Cloud。"

**旁白：**
> "本地可信。全球规模。CodeRisk Cloud。"

**字幕：**
本地可信。全球规模。
CodeRisk Cloud。

**BGM：** 收尾，渐弱至静音

---

## 附录：录制技术规范

### 画面规格
- 分辨率：1920×1080（16:9）
- 终端字体：JetBrains Mono / Fira Code, 24px+
- 浏览器缩放：125%（确保 UI 元素清晰）
- 鼠标高亮：启用光标高亮（如 KeyCastr）

### 音频规格
- 旁白：清晰、中等语速（中文约 200 字/分钟）
- BGM：科技感、无歌词、音量低于旁白 12dB
- 总时长：严格控制在 2:55 - 3:05 之间

### 字幕规范
- 字体：思源黑体 / Noto Sans SC, 48px
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
    "title": "SQL 注入漏洞",
    "file": "app/db.py",
    "line": 42,
    "rule_id": "CWE-89",
    "description": "用户输入通过 f-string 直接拼接到 SQL 查询中。请使用参数化查询。",
    "confidence": 95
  },
  {
    "severity": "high",
    "title": "硬编码 API 密钥",
    "file": "config/settings.py",
    "line": 12,
    "rule_id": "CWE-798",
    "description": "Stripe 密钥以字符串字面量硬编码。请移至环境变量或密钥管理器。",
    "confidence": 92
  },
  {
    "severity": "medium",
    "title": "缺少 CSRF 防护",
    "file": "app/views.py",
    "line": 88,
    "rule_id": "CWE-352",
    "description": "POST 接口 /transfer 缺少 CSRF 令牌验证。仅在预期接口上添加 @csrf_exempt。",
    "confidence": 78
  },
  {
    "severity": "low",
    "title": "详细错误信息泄露",
    "file": "app/handlers.py",
    "line": 15,
    "rule_id": "CWE-209",
    "description": "生产环境中向客户端暴露堆栈跟踪。请设置 DEBUG=False 并使用通用错误页面。",
    "confidence": 85
  }
]
```

> ⚠️ **重要提示：** 如果使用 mock 数据，必须在 Demo 视频开头或结尾明确说明：
> "本演示使用预填充数据以展示报告格式。生产环境中，所有发现均由 4-Agent 分析流水线在真实代码上生成。"

---

*脚本版本: v1.0 中文版*
*编写: Kimi*
*审核: Weike / lolo*
*目标赛事: DevNetwork [API + Cloud + AI] Hackathon 2026*
