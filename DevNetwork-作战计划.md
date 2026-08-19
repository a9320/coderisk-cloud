# CodeRisk Cloud — DevNetwork 黑客松作战计划

> 吸取 AMD 黑客松教训，按获奖作品标准执行
> 2026-08-19 ~ 2026-09-03（15 天）
> 目标：Overall Winner ($12,500) + Nutrient DWS Challenge ($1,500)

---

## 核心原则（从 AMD 教训提炼）

1. **评委体验优先** — JUDGES.md 是评委看到的第一个文件
2. **可验证 > 可运行** — verify.sh 比 README 重要
3. **证据 > 声称** — evidence/ 目录比文字有说服力
4. **诚实 > 完美** — 主动报告限制比隐藏缺点更可信
5. **提交前一次性准备好** — PR 历史是公开的

---

## 每日计划

### Day 1-2（8/19-20）：评委体验 + 验证体系
- [ ] **JUDGES.md** — 3 分钟审查指南（评委第一眼看到的文件）
- [ ] **verify.sh** — 离线验证脚本（一键验证核心功能）
- [ ] **Track compliance map** — 逐条对应评分标准
- [ ] **Limitations 章节** — 明确说明系统不能做什么

### Day 3-4（8/21-22）：Docker + 部署
- [x] **Docker Compose** — 已完成（CPU + GPU 模式）
- [ ] **Docker 端到端测试** — 全新环境 `docker-compose up --build` 验证
- [ ] **credential-free fixture** — 评委无需 API Key 即可体验

### Day 5-6（8/23-24）：CI/CD + 安全
- [ ] **GitHub Actions** — ci.yml + test.yml + docker-build.yml
- [ ] **.snyk 或类似安全扫描** — 供应链安全
- [ ] **SBOM 生成** — 软件物料清单
- [ ] **.pre-commit-config.yaml** — 提交前自动检查

### Day 7-8（8/25-26）：证据收集
- [ ] **evidence/ 目录** — 基准测试原始 JSON
  - `benchmark-results.json` — 性能数据
  - `security-scan.json` — 安全扫描结果
  - `test-coverage.json` — 测试覆盖率
  - `docker-health.json` — Docker 部署验证
  - `api-test-results.json` — Bruno 测试结果
- [ ] **radeon-device.txt** — 硬件证据（AMD GPU）

### Day 9-10（8/27-28）：文档工程
- [ ] **PDF 项目规范** — 非仅 Markdown
- [ ] **幻灯片** — 3-5 页，评委快速浏览用
- [ ] **架构图** — SVG 格式
- [ ] **README 重写** — 面向评审，不是面向开发者

### Day 11-12（8/29-30）：Demo 视频
- [ ] **Demo 脚本修订** — 3-4 分钟
- [ ] **录制第一版** — 粗糙版看时长和节奏
- [ ] **录制最终版** — 剪辑 + 字幕

### Day 13-14（9/1-2）：提交材料
- [ ] **DevPost 项目页** — 项目名 + pitch + 技术栈
- [ ] **Nutrient DWS Challenge 提交语句**
- [ ] **useBruno Challenge 提交语句 + 截图**
- [ ] **GitHub 仓库清理** — 确保无敏感文件

### Day 15（9/3）：最终检查
- [ ] **全新环境验证** — git clone → docker-compose up → 一切正常
- [ ] **PR 历史检查** — 确保无敏感信息
- [ ] **提交**

---

## 提交材料清单

| 材料 | 状态 | 负责 |
|------|------|------|
| JUDGES.md | ❌ 待写 | lolo |
| verify.sh | ❌ 待写 | lolo |
| Docker Compose | ✅ 已完成 | Kimi + lolo |
| PDF 项目规范 | ❌ 待做 | Kimi |
| 幻灯片 | ❌ 待做 | Kimi |
| 架构图 SVG | ❌ 待做 | lolo |
| Demo 视频 | ❌ 待录 | Weike |
| evidence/ 目录 | ❌ 待做 | lolo |
| CI/CD | ❌ 待做 | lolo |
| DevPost 页面 | ❌ 待填 | Weike |

---

## Nutrient DWS Challenge 专用

> 评审会问："Where does DWS do the heavy lifting?"

提交语句：
"Nutrient DWS powers our deterministic PDF report generation and SHA-256 digital signatures — turning raw AI vulnerability findings into tamper-evident, regulator-ready audit documents."

---

## useBruno Challenge 专用

提交语句：
"We use Bruno for comprehensive API testing — covering health checks, successful analysis submission, error handling, authentication edge cases, and report retrieval. All 9 test cases pass against our live API."

附 Bruno Collection Runner 截图。

---

*CodeRisk Cloud — 从「能用的工具」到「令人信服的系统」*
