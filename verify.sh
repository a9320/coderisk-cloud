#!/usr/bin/env bash
# CodeRisk Cloud — 一键验证脚本 v3
# 修复了 health 503 降级响应和 webhook 400 响应的兼容性问题
# 用法: chmod +x verify.sh && ./verify.sh
# 详细模式: VERIFY_VERBOSE=1 ./verify.sh

set -uo pipefail

API_URL="${CODERISK_API_URL:-http://localhost:8000}"
API_KEY="${CODERISK_API_KEY:-dev-key-change-in-production}"
VERBOSE="${VERIFY_VERBOSE:-0}"
TIMEOUT="${VERIFY_TIMEOUT:-5}"
MAX_RETRIES="${VERIFY_MAX_RETRIES:-3}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

# ── Helper functions ──────────────────────────────────────

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARN++))
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取 HTTP 状态码
http_status() {
    local url="$1"
    shift
    curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$@" "$url" 2>/dev/null
}

# 获取响应体
http_body() {
    local url="$1"
    shift
    curl -s --max-time "$TIMEOUT" "$@" "$url" 2>/dev/null
}

# 标准检查
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
        if [ "$VERBOSE" = "1" ]; then
            echo "         Command: $cmd"
            eval "$cmd" 2>&1 | sed 's/^/         /'
        fi
        return 1
    fi
}

# HTTP 状态码检查（单值）
check_http() {
    local name="$1"
    local expected="$2"
    shift 2
    local url="$1"
    shift

    echo -n "  [TEST] $name ... "

    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$@" "$url" 2>/dev/null)

    if [ "$status" = "$expected" ]; then
        echo -e "${GREEN}PASS${NC} (${status})"
        ((PASS++))
        return 0
    else
        echo -e "${RED}FAIL${NC} (expected ${expected}, got ${status:-no response})"
        ((FAIL++))
        if [ "$VERBOSE" = "1" ] && [ -n "$status" ]; then
            local body
            body=$(curl -s --max-time "$TIMEOUT" "$@" "$url" 2>/dev/null | head -c 500)
            if [ -n "$body" ]; then
                echo "         Response: $body"
            fi
        fi
        return 1
    fi
}

# HTTP 状态码检查（多值，任一匹配即通过）
check_http_any() {
    local name="$1"
    local expected_list="$2"
    shift 2
    local url="$1"
    shift

    echo -n "  [TEST] $name ... "

    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$@" "$url" 2>/dev/null)

    if echo "$expected_list" | grep -qw "$status"; then
        echo -e "${GREEN}PASS${NC} (${status})"
        ((PASS++))
        return 0
    else
        echo -e "${RED}FAIL${NC} (expected one of [${expected_list}], got ${status:-no response})"
        ((FAIL++))
        if [ "$VERBOSE" = "1" ] && [ -n "$status" ]; then
            local body
            body=$(curl -s --max-time "$TIMEOUT" "$@" "$url" 2>/dev/null | head -c 500)
            if [ -n "$body" ]; then
                echo "         Response: $body"
            fi
        fi
        return 1
    fi
}

# 等待服务就绪
wait_for_service() {
    local url="$1"
    local retries="$2"
    local delay="$3"

    log_info "Waiting for service at $url ..."
    for i in $(seq 1 "$retries"); do
        local status
        status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "$url" 2>/dev/null)
        if [ "$status" = "200" ] || [ "$status" = "503" ]; then
            log_info "Service is ready (attempt $i/$retries, status=$status)"
            return 0
        fi
        if [ "$i" -lt "$retries" ]; then
            echo "  Retry $i/$retries: service not ready (status=${status:-none}), waiting ${delay}s..."
            sleep "$delay"
        fi
    done
    return 1
}

# ── Header ────────────────────────────────────────────────

echo "═══════════════════════════════════════════════════════════"
echo "  CodeRisk Cloud — Judge Verification Script v3"
echo "  API: $API_URL"
echo "  Timeout: ${TIMEOUT}s | Retries: $MAX_RETRIES"
echo "  Verbose: $([ "$VERBOSE" = "1" ] && echo "ON" || echo "OFF")"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ── Pre-check: Service availability ───────────────────────

echo "🔍 Pre-check: Service Availability"
echo ""

if ! command -v curl >/dev/null 2>&1; then
    log_error "curl is not installed. Please install curl first."
    echo ""
    echo "  Windows (Git Bash): curl should be bundled with Git"
    echo "  Ubuntu/Debian:    sudo apt-get install curl"
    echo "  macOS:            brew install curl"
    exit 1
fi

if ! wait_for_service "$API_URL/health" "$MAX_RETRIES" 2; then
    echo ""
    log_error "Cannot connect to API at $API_URL"
    echo ""
    echo "  Possible causes:"
    echo "    1. API server is not running"
    echo "    2. API is running on a different port/host"
    echo "    3. Docker container is not started"
    echo ""
    echo "  To start the service:"
    echo "    docker-compose up --build"
    echo "  or:"
    echo "    uvicorn app.main:app --host 0.0.0.0 --port 8000"
    echo ""
    echo "  To use a different API URL:"
    echo "    CODERISK_API_URL=http://localhost:8080 ./verify.sh"
    echo ""
    exit 1
fi

# ── Check 1: Health endpoint ──────────────────────────────
echo ""
echo "1️⃣  Service Health Check"
check_http "Root endpoint responds" "200" "$API_URL/"

# Health endpoint 接受 200 (ok) 或 503 (degraded)，都是合法响应
check_http_any "Health endpoint responds" "200 503" "$API_URL/health"

# 检查 health 响应体结构（不强制 status=ok，因为 503 返回 degraded）
HEALTH_BODY=$(http_body "$API_URL/health")
if echo "$HEALTH_BODY" | grep -q '"status"'; then
    echo -e "       ${GREEN}✓${NC} response contains 'status' field"
else
    echo -e "       ${RED}✗${NC} response missing 'status' field"
    ((FAIL++))
fi

if echo "$HEALTH_BODY" | grep -q '"checks"'; then
    echo -e "       ${GREEN}✓${NC} response contains 'checks' field"
else
    echo -e "       ${YELLOW}⚠${NC} response missing 'checks' field"
    ((WARN++))
fi

if echo "$HEALTH_BODY" | grep -q '"version"'; then
    echo -e "       ${GREEN}✓${NC} response contains 'version' field"
else
    echo -e "       ${YELLOW}⚠${NC} response missing 'version' field"
    ((WARN++))
fi

# 如果 status 是 degraded，给出友好提示
if echo "$HEALTH_BODY" | grep -q '"status".*"degraded"'; then
    echo -e "       ${YELLOW}⚠${NC} Service is in DEGRADED mode (some components unavailable)"
    echo -e "         This is normal if Celery worker or GPU is not running."
    ((WARN++))
fi

# ── Check 2: Authentication ───────────────────────────────
echo ""
echo "2️⃣  Authentication & Authorization"
check_http "Missing auth returns 401" "401" "$API_URL/api/v1/analyze" -X POST -H "Content-Type: application/json" -d '{}'
check_http "Invalid API key returns 403" "403" "$API_URL/api/v1/analyze" -X POST -H "Authorization: Bearer invalid-key" -H "Content-Type: application/json" -d '{}'
check_http "Valid API key accepts request" "200" "$API_URL/api/v1/analyze" -X POST -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json" -d '{"source":"github","repo_url":"https://github.com/a9320/code-risk-agent","branch":"main","output_formats":["json"]}'

# ── Check 3: Task lifecycle ───────────────────────────────
echo ""
echo "3️⃣  Task Creation & Status Tracking"

TASK_RESPONSE=$(curl -s --max-time "$TIMEOUT" -X POST \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"source":"github","repo_url":"https://github.com/a9320/code-risk-agent","branch":"main","output_formats":["json"]}' \
    "$API_URL/api/v1/analyze" 2>/dev/null)

TASK_ID=$(echo "$TASK_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('task_id',''))" 2>/dev/null || echo "")

if [ -n "$TASK_ID" ]; then
    echo -e "       ${GREEN}✓${NC} Created task: $TASK_ID"
    check "Task created with valid task_id" "true"
    check_http "Task status endpoint responds" "200" "$API_URL/api/v1/tasks/$TASK_ID" -H "Authorization: Bearer $API_KEY"

    TASK_STATUS_BODY=$(http_body "$API_URL/api/v1/tasks/$TASK_ID" -H "Authorization: Bearer $API_KEY")
    if echo "$TASK_STATUS_BODY" | grep -q 'agent_status'; then
        echo -e "       ${GREEN}✓${NC} Task status contains agent_status"
        ((PASS++))
    else
        echo -e "       ${RED}✗${NC} Task status missing agent_status"
        ((FAIL++))
    fi
else
    echo -e "       ${RED}✗${NC} Failed to create task or parse response"
    echo "         Response: $TASK_RESPONSE"
    check "Task created with valid task_id" "false"
    check "Task status endpoint responds" "false"
    check "Task status contains agent_status" "false"
fi

# ── Check 4: ZIP upload security ──────────────────────────
echo ""
echo "4️⃣  ZIP Upload Security"

TEST_DIR=$(mktemp -d)
echo "print('hello')" > "$TEST_DIR/test_file.py"
(cd "$TEST_DIR" && zip -q test_upload.zip test_file.py)

check_http "Valid ZIP upload accepted" "200" "$API_URL/api/v1/analyze/upload" -X POST -H "Authorization: Bearer $API_KEY" -F "file=@$TEST_DIR/test_upload.zip"
check_http "Non-ZIP file rejected (400)" "400" "$API_URL/api/v1/analyze/upload" -X POST -H "Authorization: Bearer $API_KEY" -F "file=@$TEST_DIR/test_file.py"

rm -rf "$TEST_DIR"

# ── Check 5: GitHub Webhook validation ────────────────────
echo ""
echo "5️⃣  GitHub Webhook Security"
# Webhook 缺少签名时可能返回 400（请求体/Content-Type 校验失败）或 401（签名校验失败）
# 两者都是合法的安全拒绝响应
check_http_any "Webhook without signature rejected" "400 401" "$API_URL/api/v1/webhooks/github" -X POST -H "Content-Type: application/json" -d '{}'

# ── Check 6: Report isolation ───────────────────────────
echo ""
echo "6️⃣  Report Isolation"
if [ -n "$TASK_ID" ]; then
    check_http "Report endpoint requires auth" "401" "$API_URL/api/v1/reports/$TASK_ID"
    check_http "Report endpoint rejects wrong API key" "403" "$API_URL/api/v1/reports/$TASK_ID" -H "Authorization: Bearer wrong-key"
else
    log_warn "Skipping report isolation checks (no task created)"
fi

# ── Check 7: Core Engine ──────────────────────────────────
echo ""
echo "7️⃣  Core Engine Verification"

check "code-risk-agent submodule exists" "[ -d code-risk-agent ]"
check "Engine agents directory exists" "[ -d code-risk-agent/agents ]"
check "Engine has 4 agent modules" "test \$(ls code-risk-agent/agents/*.py 2>/dev/null | wc -l) -ge 4"
check "Engine has unit tests" "[ -d code-risk-agent/tests ]"
check "Engine has core modules" "[ -d code-risk-agent/core ]"
check "Engine has local CVE data scripts" "[ -f code-risk-agent/scripts/download_cve_data.py ]"

# ── Check 8: Documentation ──────────────────────────────────
echo ""
echo "8️⃣  Documentation Completeness"
check "JUDGES.md exists" "[ -f JUDGES.md ]"
check "README.md exists" "[ -f README.md ]"
check "Docker Compose config exists" "[ -f docker-compose.yml ]"
check "Bruno test collection exists" "[ -d bruno/ ]"
check "requirements.txt exists" "[ -f requirements.txt ]"

# ── Check 9: Environment validation ───────────────────────
echo ""
echo "9️⃣  Environment Validation"

check ".env.example exists" "[ -f .env.example ]"

if [ -f .env ]; then
    echo -e "       ${GREEN}✓${NC} .env file found"
else
    echo -e "       ${YELLOW}⚠${NC} .env not found (using defaults)"
    ((WARN++))
fi

PYTHON_VERSION=$(python3 --version 2>/dev/null || python --version 2>/dev/null || echo "unknown")
if echo "$PYTHON_VERSION" | grep -q "3.1[0-9]"; then
    echo -e "       ${GREEN}✓${NC} Python version: $PYTHON_VERSION"
else
    echo -e "       ${YELLOW}⚠${NC} Python version: $PYTHON_VERSION (recommended: 3.10+)"
    ((WARN++))
fi

if command -v redis-cli >/dev/null 2>&1; then
    REDIS_PING=$(redis-cli ping 2>/dev/null)
    if [ "$REDIS_PING" = "PONG" ]; then
        echo -e "       ${GREEN}✓${NC} Redis is running"
    else
        echo -e "       ${YELLOW}⚠${NC} Redis CLI available but server not responding"
        ((WARN++))
    fi
else
    echo -e "       ${YELLOW}⚠${NC} redis-cli not found (Redis may be in Docker)"
    ((WARN++))
fi

# ── Summary ───────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════"
if [ $FAIL -eq 0 ]; then
    echo -e "  Results: ${GREEN}$PASS passed${NC}, ${YELLOW}$WARN warnings${NC}"
    echo -e "  ${GREEN}✅ All critical checks passed!${NC}"
else
    echo -e "  Results: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}, ${YELLOW}$WARN warnings${NC}"
    echo -e "  ${RED}❌ $FAIL check(s) failed — see details above.${NC}"
fi
echo "═══════════════════════════════════════════════════════════"

if [ $FAIL -eq 0 ]; then
    exit 0
else
    exit 1
fi
