# Bruno Collection — CodeRisk Cloud

## 文件清单

```
bruno/
├── environments/
│   └── local.bru              # 环境变量（baseUrl, apiKey, taskId）
├── health/
│   └── health-check.bru       # 健康检查（无需认证）
├── analyze/
│   ├── submit-github.bru      # GitHub 仓库分析（自动设置 taskId）
│   ├── submit-invalid.bru     # 无效请求测试
│   ├── missing-auth.bru       # 无认证拒绝测试
│   ├── invalid-api-key.bru    # 错误 Key 拒绝测试
│   └── submit-zip.bru         # ZIP 上传分析（需 sample-code.zip）
├── tasks/
│   ├── get-task-status.bru    # 查询任务状态（依赖 submit-github 的 taskId）
│   └── not-found.bru          # 任务不存在测试
└── reports/
    └── get-report.bru         # 下载报告（含 pre-request 轮询等待）
```

## 运行方式

### GUI（推荐）
1. 打开 Bruno App
2. File → Open Collection → 选择 `bruno/` 目录
3. 右上角选择 Environment: `local`
4. 点击 Collection Runner → Run

### CLI
```bash
cd bruno
bru run --env local
```

## 关键修复说明

### 修复 1：认证头（解决 403 问题）
所有需认证请求统一使用：
```
auth: none
headers {
  Authorization: Bearer {{apiKey}}
}
```

### 修复 2：taskId 自动传递
`submit-github.bru` 成功后自动执行：
```javascript
bru.setVar("taskId", res.body.task_id);
```

### 修复 3：Report 异步轮询
`get-report.bru` 添加了 `script:pre-request`，在请求报告前轮询任务状态最多 30 秒，等待 `completed` 或 `failed`。

### 修复 4：ZIP 样本文件
`sample-code.zip` 已包含在 collection 目录中，内含 SQL 注入、硬编码密钥、命令注入样本代码。

## 预期结果

```
[1/9] health-check          → 200 OK ✅
[2/9] submit-github         → 200 OK + taskId 自动设置 ✅
[3/9] submit-invalid        → 422 ✅
[4/9] missing-auth          → 401 ✅
[5/9] invalid-api-key       → 403 ✅
[6/9] get-task-status       → 200 OK ✅
[7/9] not-found             → 404 ✅
[8/9] get-report            → 200/202（轮询等待后）✅
[9/9] submit-zip            → 200 OK ✅
```
