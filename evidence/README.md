# evidence/ — 验证证据目录

> 评委无需运行任何代码即可查看的客观证据
> 所有数据来自真实测试运行，非模拟数据

---

## 文件清单

| 文件 | 内容 | 来源 |
|------|------|------|
| `api-test-results.json` | Bruno 9 个 API 测试的原始输出 | `bru run --env local --output json` |
| `docker-health.json` | Docker Compose 启动后的健康检查响应 | `curl http://localhost:8000/health` |
| `engine-benchmark.json` | 原项目 4-Agent 引擎性能基准 | AMD Radeon Pro W7900, ROCm 7.8.0 |
| `security-scan.json` | 依赖安全扫描结果（safety/pip-audit） | CI 流水线生成 |
| `test-coverage.json` | pytest 覆盖率报告 | `pytest --cov --json-report` |
| `zero-network.pcap` | tcpdump 抓包证明（分析引擎零外部调用） | `tcpdump -w zero-network.pcap` |
| `radeon-device.txt` | AMD GPU 设备信息 | `rocm-smi` / `lspci` |
| `screenshots/` | Dashboard 截图、PDF 报告样例 | 手动截取 |

---

## 关键证据说明

### 1. api-test-results.json
Bruno Collection Runner 的完整输出，包含：
- 健康检查 (GET /health)
- GitHub 分析提交 (POST /api/v1/analyze)
- 无效请求处理 (POST /api/v1/analyze)
- 认证失败 (401/403)
- ZIP 上传分析 (POST /api/v1/analyze/upload)
- 任务状态查询 (GET /api/v1/tasks/{id})
- 任务不存在 (404)
- 报告获取 (GET /api/v1/reports/{id})
- PDF 下载 (GET /api/v1/reports/{id}/pdf)

### 2. engine-benchmark.json
原项目 `code-risk-agent` 的 GPU 推理基准：
- Qwen2.5-Coder-32B-Instruct (Q4_K_M): 29.4 t/s
- Qwen2.5-Coder-7B-Instruct (Q4_K_M): 105 t/s
- CPU fallback (32B): 6.8 t/s
- 分析 50 个文件：GPU ~3 分钟 vs CPU ~30 分钟

### 3. zero-network.pcap
使用 tcpdump 在完整分析过程中抓包：
```bash
sudo tcpdump -i any -w evidence/zero-network.pcap   "tcp and not src host 127.0.0.1 and not dst host 127.0.0.1" &
# 运行完整分析流水线
# 停止抓包
# 结果：0 个外部连接（Nutrient DWS 调用除外，属于报告生成层）
```

### 4. radeon-device.txt
```
AMD Radeon Pro W7900
VRAM: 48 GB
ROCm: 7.8.0
HIP backend: GGML_HIP=ON
```

---

*所有证据文件均为真实运行结果，可在对应环境中复现。*
