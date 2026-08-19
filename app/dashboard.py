"""CodeRisk Cloud — Streamlit Dashboard

启动方式:
    streamlit run app/dashboard.py --server.port 8501

环境变量:
    CODERISK_API_URL=http://localhost:8000
    CODERISK_API_KEY=dev-key-change-in-production

前置依赖（lolo 需配合在 main.py 中实现）:
    • GET /api/v1/tasks/{id}      — 已有
    • GET /api/v1/reports/{id}    — 已有
    • GET /api/v1/reports/{id}/pdf — 建议新增，用于 PDF 直接下载
    • StaticFiles 挂载 /reports    — 建议新增，用于文件下载
"""

from __future__ import annotations

import os
from datetime import datetime

import requests
import streamlit as st

# ── 配置 ──
API_BASE = os.getenv("CODERISK_API_URL", "http://localhost:8000")
API_KEY = os.getenv("CODERISK_API_KEY", "dev-key-change-in-production")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}

# ── 页面设置 ──
st.set_page_config(
    page_title="CodeRisk Cloud",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 自定义样式 ──
st.markdown("""
<style>
    .main-header { font-size: 2.4rem; font-weight: 800; color: #1e293b; letter-spacing: -0.5px; }
    .sub-header { font-size: 1.05rem; color: #64748b; margin-bottom: 2rem; }
    .stat-card { padding: 1.2rem 0.8rem; border-radius: 0.75rem; text-align: center; border: 1.5px solid; }
    .stat-critical { background: #fef2f2; border-color: #fecaca; color: #dc2626; }
    .stat-high { background: #fff7ed; border-color: #fed7aa; color: #ea580c; }
    .stat-medium { background: #fefce8; border-color: #fde047; color: #a16207; }
    .stat-low { background: #f0fdf4; border-color: #bbf7d0; color: #16a34a; }
    .stat-info { background: #f8fafc; border-color: #e2e8f0; color: #64748b; }
    .agent-box { padding: 8px; border-radius: 6px; text-align: center; font-size: 0.8rem; }
    .agent-done { background: #dcfce7; color: #166534; }
    .agent-run { background: #dbeafe; color: #1e40af; }
    .agent-wait { background: #f1f5f9; color: #64748b; }
</style>
""", unsafe_allow_html=True)


# ── 工具函数 ──
def api_post(endpoint: str, payload: dict | None = None) -> dict | None:
    try:
        resp = requests.post(
            f"{API_BASE}{endpoint}",
            headers=HEADERS,
            json=payload or {},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("🔴 Cannot connect to API. Is `uvicorn app.main:app` running?")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"API Error {e.response.status_code}: {e.response.text[:200]}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None


def api_get(endpoint: str) -> dict | None:
    try:
        resp = requests.get(
            f"{API_BASE}{endpoint}",
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.HTTPError:
        return None
    except Exception:
        return None


def check_health() -> bool:
    try:
        r = requests.get(f"{API_BASE}/health", timeout=3)
        return r.status_code == 200 and r.json().get("status") == "ok"
    except Exception:
        return False


# ── Session State ──
if "tasks" not in st.session_state:
    st.session_state.tasks = []          # {task_id, repo_url, branch, status, progress, submitted_at}
if "selected_task" not in st.session_state:
    st.session_state.selected_task = None


# ═════════════════════════════════════════════════════════════
# Sidebar
# ═════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🛡️ CodeRisk Cloud")
    st.caption("AI-Powered Code Security API")
    st.divider()

    is_online = check_health()
    st.markdown(f"**API:** `{API_BASE}`")
    st.markdown(f"**Status:** {'🟢 Online' if is_online else '🔴 Offline'}")

    if not is_online:
        st.warning("API appears offline. Make sure the FastAPI server is running.")

    st.divider()
    st.markdown("### Quick Links")
    st.markdown("• [API Docs](http://localhost:8000/docs)")
    st.markdown("• [GitHub Repo](https://github.com/a9320/code-risk-agent)")
    st.markdown("• [Nutrient DWS](https://nutrient.io)")

    st.divider()
    with st.expander("ℹ️ About"):
        st.markdown("""
        **CodeRisk Cloud** runs LLM inference locally on AMD GPUs.
        Your source code never leaves your infrastructure.

        **Tech Stack:**
        - FastAPI + Celery + Redis
        - Qwen2.5-Coder-32B (ROCm)
        - Nutrient DWS (PDF + Signature)
        """)


# ═════════════════════════════════════════════════════════════
# Main Header
# ═════════════════════════════════════════════════════════════
st.markdown('<div class="main-header">🛡️ CodeRisk Cloud Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Local AI code security analysis with Cloud API delivery</div>',
    unsafe_allow_html=True,
)


# ═════════════════════════════════════════════════════════════
# 提交新分析
# ═════════════════════════════════════════════════════════════
with st.container(border=True):
    st.subheader("🔍 Submit New Analysis")

    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        repo_url = st.text_input(
            "Repository URL",
            placeholder="https://github.com/user/repo",
            help="Public GitHub repository to analyze",
        )
    with c2:
        branch = st.text_input("Branch", value="main")
    with c3:
        output_formats = st.multiselect(
            "Output",
            options=["json", "sarif", "pdf"],
            default=["json", "sarif", "pdf"],
        )

    btn_col1, btn_col2 = st.columns([1, 6])
    with btn_col1:
        submit = st.button("🚀 Start Analysis", type="primary", disabled=not repo_url or not is_online)
    with btn_col2:
        if submit and repo_url:
            with st.spinner("Submitting task to CodeRisk Cloud..."):
                result = api_post("/api/v1/analyze", {
                    "source": "github",
                    "repo_url": repo_url,
                    "branch": branch,
                    "output_formats": output_formats,
                })
                if result:
                    tid = result.get("task_id")
                    st.session_state.tasks.append({
                        "task_id": tid,
                        "repo_url": repo_url,
                        "branch": branch,
                        "status": "pending",
                        "progress": 0,
                        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    })
                    st.success(f"Task created: `{tid}`")
                    st.balloons()


# ═════════════════════════════════════════════════════════════
# 任务列表
# ═════════════════════════════════════════════════════════════
st.header("📋 Analysis Tasks", divider="blue")

if not st.session_state.tasks:
    st.info("No tasks yet. Submit a repository URL above to get started.")
else:
    # 刷新所有未完成任务的状态
    progress_placeholder = st.empty()
    for task in st.session_state.tasks:
        if task["status"] not in ("completed", "failed"):
            status_data = api_get(f"/api/v1/tasks/{task['task_id']}")
            if status_data:
                task["status"] = status_data.get("status", "unknown")
                task["progress"] = status_data.get("progress", 0)
                task["agent_status"] = status_data.get("agent_status", {})
                task["error"] = status_data.get("error")

    # 按时间倒序展示
    for idx, task in enumerate(reversed(st.session_state.tasks)):
        with st.container(border=True):
            top_cols = st.columns([2.2, 2.5, 1.2, 1.5, 1])

            # Task ID
            top_cols[0].code(task["task_id"], language=None)

            # Repo URL
            url_display = task["repo_url"]
            if len(url_display) > 45:
                url_display = url_display[:42] + "..."
            top_cols[1].markdown(f"`{url_display}`<br><small>branch: {task['branch']}</small>", unsafe_allow_html=True)

            # Status
            status = task["status"]
            emoji_map = {
                "pending": "⏳", "queued": "📥", "analyzing": "🔄",
                "verifying": "🔍", "generating_report": "📄",
                "completed": "✅", "failed": "❌",
            }
            emoji = emoji_map.get(status, "❓")
            top_cols[2].markdown(f"{emoji} **{status.replace('_', ' ').upper()}**")

            # Progress
            prog = task.get("progress", 0)
            top_cols[3].progress(prog / 100, text=f"{prog}%")

            # Actions
            if status == "completed":
                if top_cols[4].button("📄 Report", key=f"btn_report_{idx}", use_container_width=True):
                    st.session_state.selected_task = task["task_id"]
                    st.rerun()
            elif status == "failed":
                top_cols[4].error("Failed")
            else:
                top_cols[4].button("⏳ Wait", key=f"btn_wait_{idx}", disabled=True, use_container_width=True)

            # Agent 状态展开
            agent_status = task.get("agent_status", {})
            if agent_status:
                with st.expander("🔍 Agent Pipeline Details"):
                    a_cols = st.columns(4)
                    agents = [
                        ("🛠️ Static", agent_status.get("agent_1_static", "pending")),
                        ("🧠 Semantic", agent_status.get("agent_2_semantic", "pending")),
                        ("✅ Verifier", agent_status.get("agent_3_verifier", "pending")),
                        ("📊 Report", agent_status.get("agent_4_report", "pending")),
                    ]
                    for acol, (name, ast) in zip(a_cols, agents):
                        css = "agent-done" if ast == "completed" else "agent-run" if ast == "running" else "agent-wait"
                        emoji = "✅" if ast == "completed" else "🔄" if ast == "running" else "⏳" if ast == "pending" else "⚠️"
                        acol.markdown(
                            f'<div class="agent-box {css}">'
                            f'<div style="font-size:1.2rem">{emoji}</div>'
                            f'<div style="font-weight:700">{name}</div>'
                            f'<div style="opacity:0.8;text-transform:capitalize">{ast}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

            # 错误信息
            if task.get("error"):
                st.error(f"Error: {task['error']}")


# ═════════════════════════════════════════════════════════════
# 报告预览
# ═════════════════════════════════════════════════════════════
st.header("📊 Report Preview", divider="green")

selected = st.session_state.get("selected_task")
if selected:
    report_data = api_get(f"/api/v1/reports/{selected}")
    if report_data:
        summary = report_data.get("summary", {})

        # Severity 统计卡片
        st.subheader("Severity Summary")
        scols = st.columns(5)
        stats = [
            ("CRITICAL", summary.get("critical", 0), "stat-critical"),
            ("HIGH", summary.get("high", 0), "stat-high"),
            ("MEDIUM", summary.get("medium", 0), "stat-medium"),
            ("LOW", summary.get("low", 0), "stat-low"),
            ("INFO", summary.get("info", 0), "stat-info"),
        ]
        for scol, (label, count, css_class) in zip(scols, stats):
            scol.markdown(
                f'<div class="stat-card {css_class}">'
                f'<div style="font-size:2.2rem;font-weight:800;line-height:1">{count}</div>'
                f'<div style="font-size:0.75rem;font-weight:700;letter-spacing:0.5px;margin-top:6px">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Findings 表格
        st.subheader(f"Findings ({report_data.get('total_findings', 0)} total)")
        findings = report_data.get("findings", [])
        if findings:
            table_data = []
            for f in findings:
                sev = f.get("severity", "info").upper()
                sev_emoji = {
                    "CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡",
                    "LOW": "🟢", "INFO": "⚪",
                }.get(sev, "⚪")
                table_data.append({
                    "Severity": f"{sev_emoji} {sev}",
                    "Title": f.get("title", "")[:55],
                    "Location": f"{f.get('file', '')}:{f.get('line', 0)}",
                    "Rule": f.get("rule_id", f.get("type", "N/A")),
                })
            st.table(table_data)
        else:
            st.info("No findings detected in this scan.")

        # 下载按钮
        st.subheader("Downloads")
        dcols = st.columns(4)
        report_urls = report_data.get("report_urls", {})

        # JSON
        if report_urls.get("json"):
            dcols[0].link_button("⬇️ JSON Report", f"{API_BASE}{report_urls['json']}", use_container_width=True)
        # SARIF
        if report_urls.get("sarif"):
            dcols[1].link_button("⬇️ SARIF Report", f"{API_BASE}{report_urls['sarif']}", use_container_width=True)
        # PDF
        if report_urls.get("pdf"):
            dcols[2].link_button("⬇️ PDF Report", f"{API_BASE}{report_urls['pdf']}", use_container_width=True)
        # Nutrient Viewer
        viewer_url = report_data.get("viewer_url")
        if viewer_url:
            dcols[3].link_button("👁️ Viewer", f"{API_BASE}{viewer_url}", use_container_width=True)

        # 数字签名
        sig = report_data.get("digital_signature")
        if sig:
            st.success(f"🔏 Digitally Signed: `{sig}`")
            st.caption("SHA-256 integrity verification embedded. Report tamper-evident.")
    else:
        st.error("Failed to load report. The task may still be processing or the report was not found.")
else:
    st.info("Select a completed task above (click 📄 Report) to view the full analysis report.")
