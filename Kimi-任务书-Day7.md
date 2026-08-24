# Kimi 任务书 — Day 7（2026-08-23）

> **目标：** 让 CodeRisk Cloud 扫描 Damn-Vulnerable-Flask-Application 能检出 8-10 个漏洞（现在只有 1 个）

---

## 任务 1：扩展 static_analyzer.py 的 Flask/Web 漏洞规则（最高优先级）

**文件：** `code-risk-agent/agents/static_analyzer.py`

**现状：** 只有 C 和 Python 基础模式（eval/exec/os.system 等），Flask Web 应用的漏洞完全没覆盖。

**需要添加的规则：**

### Python Web 框架新增规则（加到 PYTHON_DANGEROUS_CALLS 或新建 PYTHON_WEB_PATTERNS）

```python
# 1. SSTI（Server-Side Template Injection）
"render_template_string": {
    "cwe": "CWE-1336",
    "severity": Severity.CRITICAL,
    "title": "SSTI via render_template_string()",
    "desc": "render_template_string() with user input can lead to Server-Side Template Injection",
    "fix": "Use render_template() with separate template files, never pass user input to render_template_string()",
}

# 2. SQL 注入
"db.execute": {
    "cwe": "CWE-89",
    "severity": Severity.HIGH,
    "title": "Potential SQL Injection via db.execute()",
    "desc": "db.execute() with string concatenation/f-string may allow SQL injection",
    "fix": "Use parameterized queries: db.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
}
# 也检查：cursor.execute, connection.execute, session.execute

# 3. 不安全的 pickle
"pickle.load": {
    "cwe": "CWE-502",
    "severity": Severity.CRITICAL,
    "title": "Deserialization via pickle.load()",
    "desc": "pickle.load() deserializing untrusted data can execute arbitrary code",
    "fix": "Use json or msgpack instead of pickle",
}

# 4. 不安全的反序列化
"marshal.loads": {
    "cwe": "CWE-502",
    "severity": Severity.HIGH,
    "title": "Deserialization via marshal.loads()",
    "desc": "marshal.loads() can execute arbitrary code from untrusted data",
    "fix": "Avoid deserializing untrusted data with marshal",
}

# 5. 命令注入（补充）
"os.popen": {
    "cwe": "CWE-78",
    "severity": Severity.HIGH,
    "title": "Command Injection via os.popen()",
    "desc": "os.popen() executes shell commands, may be injected with user input",
    "fix": "Use subprocess.run() with shell=False and a list of args",
}

# 6. 不安全的文件操作
"send_file": {
    "cwe": "CWE-22",
    "severity": Severity.HIGH,
    "title": "Path Traversal via send_file()",
    "desc": "Flask send_file() with user-controlled path can lead to path traversal",
    "fix": "Use send_from_directory() and validate the path is within allowed directory",
}

# 7. 不安全的重定向
"redirect": {
    "cwe": "CWE-601",
    "severity": Severity.MEDIUM,
    "title": "Open Redirect via redirect()",
    "desc": "Flask redirect() with user-controlled URL can lead to open redirect",
    "fix": "Validate redirect URL against a whitelist of allowed domains",
}

# 8. Debug 模式（正则匹配）
# pattern: app.run(debug=True) 或 app.debug = True
```

### 正则模式规则（加到 PYTHON_VULNERABLE_PATTERNS 或新建）

```python
# 1. 硬编码 SECRET_KEY
{
    "pattern": r"SECRET_KEY\s*=\s*['\"][^'\"]+['\"]",
    "cwe": "CWE-798",
    "severity": Severity.HIGH,
    "title": "Hard-coded Flask SECRET_KEY",
    "desc": "Flask SECRET_KEY is hard-coded, should use environment variable",
    "fix": "Use os.environ.get('SECRET_KEY') or a secrets manager",
}

# 2. Debug 模式开启
{
    "pattern": r"app\.run\s*\([^)]*debug\s*=\s*True",
    "cwe": "CWE-489",
    "severity": Severity.HIGH,
    "title": "Debug Mode Enabled in Production",
    "desc": "Flask debug mode exposes stack traces and enables the debugger",
    "fix": "Set debug=False or use environment variable",
}
# 也检查：app.debug = True

# 3. 不安全的 CORS
{
    "pattern": r"CORS\s*\(\s*app\s*\)",
    "cwe": "CWE-942",
    "severity": Severity.MEDIUM,
    "title": "Overly Permissive CORS Configuration",
    "desc": "CORS(app) allows all origins, restrict to specific domains",
    "fix": "CORS(app, origins=['https://yourdomain.com'])",
}

# 4. XSS - 不安全的 Markup
{
    "pattern": r"Markup\s*\(",
    "cwe": "CWE-79",
    "severity": Severity.MEDIUM,
    "title": "Potential XSS via Markup()",
    "desc": "Markup() without escaping can lead to XSS if user input is included",
    "fix": "Use markupsafe.escape() for user input before wrapping in Markup()",
}

# 5. XSS - Jinja2 |safe 过滤器
{
    "pattern": r"\|safe",
    "cwe": "CWE-79",
    "severity": Severity.MEDIUM,
    "title": "Potential XSS via |safe filter",
    "desc": "Jinja2 |safe filter disables auto-escaping, can lead to XSS",
    "fix": "Remove |safe or ensure the content is sanitized before rendering",
}

# 6. SQL 注入 - 字符串拼接
{
    "pattern": r"(?:execute|cursor\.execute)\s*\(\s*['\"f].*\+|.*%s.*%|f['\"].*\{",
    "cwe": "CWE-89",
    "severity": Severity.HIGH,
    "title": "SQL Injection via String Concatenation",
    "desc": "SQL query built with string concatenation or f-string, vulnerable to injection",
    "fix": "Use parameterized queries with ? placeholders",
}
```

### 语言检测扩展

`_detect_language()` 函数需要支持更多文件类型：

```python
suffix_map = {
    ".c": Language.C,
    ".h": Language.C,
    ".py": Language.PYTHON,
    ".js": Language.JAVASCRIPT,   # 新增
    ".ts": Language.JAVASCRIPT,   # 新增
    ".html": Language.HTML,        # 新增
    ".java": Language.JAVA,        # 新增
    ".go": Language.GO,            # 新增
    ".rb": Language.RUBY,          # 新增
    ".php": Language.PHP,          # 新增
}
```

同时在 `core/models.py` 的 `Language` 枚举中添加对应的值。

**注意：** `_analyze_python()` 方法需要能处理 `.py` 文件中的 Web 框架代码，不需要单独的 `_analyze_flask()` 方法——把规则加到 Python 规则集里就行。

---

## 任务 2：在 tasks.py 中调用 TaintAnalyzer + DependencyScanner

**文件：** `app/tasks.py`

**现状：** `_run_static_analysis()` 之后没有调用污点分析和依赖扫描。

**需要修改：** 在 `analyze_codebase_task()` 的静态分析之后，加两步：

```python
# 在 static_findings = future_static.result() 之后加：

# 污点分析
from core.taint_analyzer import TaintAnalyzer
taint = TaintAnalyzer()
code_files_for_taint = _scan_code_files(work_dir)
for cf in code_files_for_taint:
    if cf.language == Language.C:
        taint_flows = taint.analyze_c(cf.content, str(cf.path))
    elif cf.language == Language.PYTHON:
        taint_flows = taint.analyze_python(cf.content, str(cf.path))
    # 将 TaintFlow 转为 findings dict
    for flow in taint_flows:
        static_findings.append({
            "id": f"TAINT-{hash(str(flow)) & 0xFFFF:04x}",
            "type": flow.cwe_id,
            "title": f"Taint: {flow.source} → {flow.sink}",
            "severity": flow.severity,
            "description": flow.description,
            "file": flow.file_path if hasattr(flow, 'file_path') else "",
            "line": flow.sink_line,
            "confidence": 60 if flow.confidence == "medium" else 80,
        })

# 依赖扫描
from core.dependency_scanner import scan_project_dependencies
from pathlib import Path
dep_risks = scan_project_dependencies(Path(work_dir))
for dr in dep_risks:
    static_findings.append({
        "id": f"DEP-{hash(str(dr)) & 0xFFFF:04x}",
        "type": getattr(dr, 'cwe_id', 'CWE-1395') or 'CWE-1395',
        "title": getattr(dr, 'title', 'Vulnerable Dependency'),
        "severity": getattr(dr, 'severity', 'medium').value if hasattr(getattr(dr, 'severity', 'medium'), 'value') else str(getattr(dr, 'severity', 'medium')),
        "description": getattr(dr, 'description', ''),
        "file": str(getattr(dr, 'file_path', '')),
        "line": getattr(dr, 'line_start', 0),
        "confidence": 50,
    })
```

**注意：** `scan_project_dependencies` 返回的是 `Risk` 对象还是其他类型，需要确认。先看 `core/dependency_scanner.py` 的函数签名。

---

## 任务 3：Dockerfile 加 Semgrep + CVE 数据库

**文件：** `Dockerfile`

```dockerfile
# 在 pip install 之后加：

# 安装 Semgrep
RUN pip install --no-cache-dir semgrep

# 构建 CVE 数据库（如果脚本存在）
RUN python code-risk-agent/scripts/download_cve_data.py || echo "CVE data download skipped"
```

**文件：** `requirements.txt` — 确认 `semgrep` 已在列表中。

---

## 输出要求

请直接输出修改后的完整文件内容（不要只给 diff，要给完整文件），包括：

1. **修改后的 `code-risk-agent/agents/static_analyzer.py`** — 加入所有新增规则
2. **修改后的 `app/tasks.py`** — 加入 TaintAnalyzer + DependencyScanner 调用
3. **修改后的 `Dockerfile`** — 加入 Semgrep + CVE 数据库构建
4. **如果需要修改 `code-risk-agent/core/models.py`** — 添加新的 Language 枚举值

每个文件用完整的代码块包裹，标注文件路径。

---

## 约束

- 不要改动已有规则，只新增
- 不要改动 Agent 之间的接口（Risk/CodeFile 模型）
- 新增规则必须有 CWE ID、severity、title、description、fix
- 代码风格与现有代码保持一致（用 `self._make_risk()` 构造 Risk）
- 不需要改 docker-compose.yml（已经改好了）
