#!/bin/bash
# CodeRisk Cloud — CI 触发测试脚本
# 用法: bash test-ci-commit.sh

set -e

echo "=========================================="
echo "CodeRisk Cloud — CI 触发测试"
echo "=========================================="

# 1. 确认在 git 仓库中
if [ ! -d ".git" ]; then
    echo "❌ 错误: 当前目录不是 git 仓库"
    echo "   请 cd 到 coderisk-cloud 目录"
    exit 1
fi

# 2. 确认分支是 main 或 dev
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ] && [ "$BRANCH" != "dev" ]; then
    echo "⚠️  当前分支是 $BRANCH，CI 只在 main/dev 触发"
    echo "   建议: git checkout dev"
fi

# 3. 确认文件已放入
FILES=(
    ".github/workflows/ci.yml"
    ".github/dependabot.yml"
    ".github/CODEOWNERS"
    ".pre-commit-config.yaml"
)

for f in "${FILES[@]}"; do
    if [ ! -f "$f" ]; then
        echo "❌ 缺失文件: $f"
        echo "   请先将 Kimi 生成的文件复制到仓库"
        exit 1
    fi
    echo "✅ $f"
done

# 4. 创建测试 commit（无害改动）
echo ""
echo "📦 创建测试 commit..."

# 使用双引号 heredoc 让 $(date) 展开
cat > .ci-test-marker << EOF
# CI Test Marker
# This file confirms CI pipeline is working.
# Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

git add -A
git commit -m "ci: verify unified workflow — test + e2e + security

Trigger CI to validate:
- Job 1: pytest + coverage (PYTHONPATH fixed)
- Job 2: docker compose build (cache enabled) + verify.sh (CODERISK_API_URL)
- Job 3: pip-audit + Trivy SARIF (reuses e2e image)

Refs: DevNetwork Day 5-6 CI/CD setup"

echo ""
echo "🚀 Push 到远程触发 CI..."
git push origin $BRANCH

echo ""
echo "=========================================="
echo "✅ Commit 已推送"
echo "=========================================="
echo ""
echo "查看 CI 状态:"
echo "   https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]//' | sed 's/.git$//')/actions"
echo ""
echo "等待约 5-8 分钟后检查:"
echo "   - Job 1 (test)    应该显示 pytest passed"
echo "   - Job 2 (e2e)     应该显示 docker healthy + verify.sh passed"
echo "   - Job 3 (security) 应该显示 0 HIGH/CRITICAL CVEs"
echo ""
