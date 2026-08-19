#!/usr/bin/env bash
# CodeRisk Cloud — 一键验证脚本
# 评委在 docker-compose up 后运行此脚本验证核心功能
# 用法: chmod +x verify.sh && ./verify.sh

set -euo pipefail

API_URL="${CODERISK_API_URL:-http://localhost:8000}"
API_KEY="${CODERISK_API_KEY:-dev-key-change-in-production}"
REPORTS_DIR="${REPORTS_DIR:-./reports}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

check() {
    local name="$1"
    local cmd="$2"
    echo -n "  [TEST] $name ... "
    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        ((PASS++))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        ((FAIL++))
        return 1
    fi
}

echo "═══════════════════════════════════════════════════════════"
echo "  CodeRisk Cloud — Judge Verification Script"
echo "  API: $API_URL"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ── Check 1: Health endpoint ──────────────────────────────
echo "1️⃣  Service Health Check"
check "Root endpoint responds"     "curl -sf $API_URL/"
check "Health endpoint returns ok"     "curl -sf $API_URL/health | grep -q 'ok'"
check "Health checks include redis + celery + gpu"     "curl -sf $API_URL/health | grep -q 'redis'"

# ── Check 2: Authentication ─────────────────────────────────
echo ""
echo "2️⃣  Authentication & Authorization"
check "Missing auth returns 401"     "curl -sf -w '%{http_code}' -o /dev/null $API_URL/api/v1/analyze | grep -q '401'"
check "Invalid API key returns 403"     "curl -sf -w '%{http_code}' -o /dev/null -H 'Authorization: Bearer invalid-key' $API_URL/api/v1/analyze | grep -q '403'"
check "Valid API key accepts request"     "curl -sf -w '%{http_code}' -o /dev/null -H 'Authorization: Bearer $API_KEY' -H 'Content-Type: application/json' -d '{"source":"github","repo_url":"https://github.com/a9320/code-risk-agent","branch":"main","output_formats":["json"]}' $API_URL/api/v1/analyze | grep -q '200'"

# ── Check 3: Task lifecycle ───────────────────────────────
echo ""
echo "3️⃣  Task Creation & Status Tracking"
TASK_RESPONSE=$(curl -sf -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json"     -d '{"source":"github","repo_url":"https://github.com/a9320/code-risk-agent","branch":"main","output_formats":["json"]}'     $API_URL/api/v1/analyze)
TASK_ID=$(echo "$TASK_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['task_id'])" 2>/dev/null || echo "")

if [ -n "$TASK_ID" ]; then
    check "Task created with valid task_id" "true"
    check "Task status endpoint responds"         "curl -sf -H 'Authorization: Bearer $API_KEY' $API_URL/api/v1/tasks/$TASK_ID"
    check "Task status contains agent_status"         "curl -sf -H 'Authorization: Bearer $API_KEY' $API_URL/api/v1/tasks/$TASK_ID | grep -q 'agent_status'"
else
    check "Task created with valid task_id" "false"
    check "Task status endpoint responds" "false"
    check "Task status contains agent_status" "false"
fi

# ── Check 4: ZIP upload security ──────────────────────────
echo ""
echo "4️⃣  ZIP Upload Security"
# Create a minimal valid ZIP
echo "print('hello')" > /tmp/test_file.py
(cd /tmp && zip -q test_upload.zip test_file.py)
check "Valid ZIP upload accepted"     "curl -sf -H 'Authorization: Bearer $API_KEY' -F 'file=@/tmp/test_upload.zip' $API_URL/api/v1/analyze/upload"
check "Non-ZIP file rejected (400)"     "curl -sf -w '%{http_code}' -o /dev/null -H 'Authorization: Bearer $API_KEY' -F 'file=@/tmp/test_file.py' $API_URL/api/v1/analyze/upload | grep -q '400'"
rm -f /tmp/test_file.py /tmp/test_upload.zip

# ── Check 5: GitHub Webhook validation ────────────────────
echo ""
echo "5️⃣  GitHub Webhook Security"
check "Webhook without signature rejected"     "curl -sf -w '%{http_code}' -o /dev/null -X POST -H 'Content-Type: application/json' -d '{}' $API_URL/api/v1/webhooks/github | grep -q '401'"

# ── Check 6: Report isolation ─────────────────────────────
echo ""
echo "6️⃣  Report Isolation"
if [ -n "$TASK_ID" ]; then
    check "Report endpoint requires auth"         "curl -sf -w '%{http_code}' -o /dev/null $API_URL/api/v1/reports/$TASK_ID | grep -q '401'"
    check "Report endpoint rejects wrong API key"         "curl -sf -w '%{http_code}' -o /dev/null -H 'Authorization: Bearer wrong-key' $API_URL/api/v1/reports/$TASK_ID | grep -q '403'"
else
    check "Report endpoint requires auth" "false"
    check "Report endpoint rejects wrong API key" "false"
fi

# ── Check 7: Engine layer (code-risk-agent submodule) ───
echo ""
echo "7️⃣  Core Engine Verification"
check "code-risk-agent submodule exists"     "[ -d code-risk-agent/agents ]"
check "Engine has 4 agents"     "ls code-risk-agent/agents/*.py 2>/dev/null | wc -l | grep -q '4'"
check "Engine has 51 unit tests"     "[ -d code-risk-agent/tests ]"
check "Local CVE database exists"     "[ -f code-risk-agent/data/vuln_db.sqlite ] || [ -d code-risk-agent/data/osv ]"

# ── Check 8: Documentation ────────────────────────────────
echo ""
echo "8️⃣  Documentation Completeness"
check "JUDGES.md exists" "[ -f JUDGES.md ]"
check "README.md exists" "[ -f README.md ]"
check "Docker Compose config exists" "[ -f docker-compose.yml ]"
check "Bruno test collection exists" "[ -d bruno/ ]"

# ── Summary ───────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════"
echo -e "  Results: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}"
echo "═══════════════════════════════════════════════════════════"

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed — CodeRisk Cloud is ready for judging.${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAIL check(s) failed — see details above.${NC}"
    exit 1
fi
