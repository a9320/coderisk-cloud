# CodeRisk Cloud - LOCAL 扫描测试脚本
# 用法：在 PowerShell 里执行此文件
# .\scan-test.ps1

$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer dev-key-change-in-production"
}

$body = '{"local_path":"/repos/Damn-Vulnerable-Flask-Application"}'

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scan-local" -Method Post -Headers $headers -Body $body
Write-Output $response

# 如果拿到 task_id，自动查询结果
$taskId = $response.task_id
if ($taskId) {
    Write-Output ""
    Write-Output "=== 等待任务完成 ==="
    Start-Sleep -Seconds 10

    $status = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/tasks/$taskId" -Headers $headers
    Write-Output ($status | ConvertTo-Json -Depth 5)

    if ($status.status -eq "completed") {
        Write-Output ""
        Write-Output "=== 报告 ==="
        $report = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/reports/$taskId" -Headers $headers
        Write-Output ($report | ConvertTo-Json -Depth 10)
    }
}
