"""CodeRisk Cloud — Celery 任务定义"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import shutil
import sys
import tempfile
import zipfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any

import redis
from celery import Celery

from app.config import settings
from app.nutrient_client import NutrientDWSClient

# ── 日志 ──
logger = logging.getLogger("coderisk.cloud.tasks")

# ── 模块级 Redis 连接池 ──
_redis_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, max_connections=20)


def _get_redis():
    return redis.Redis(connection_pool=_redis_pool)


# ── Celery 应用 ──
celery_app = Celery(
    "coderisk",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    worker_concurrency=settings.WORKER_CONCURRENCY,
    task_time_limit=1800,      # 硬限制 30 分钟
    task_soft_time_limit=1500,   # 软限制 25 分钟，优雅收尾
)

# ── CodeRisk Agent 模块级单例导入 ──
if settings.CODERISK_PATH and settings.CODERISK_PATH not in sys.path:
    sys.path.insert(0, settings.CODERISK_PATH)

_static_analyzer = None
_semantic_analyzer = None
_deep_verifier = None


def _get_static_analyzer():
    global _static_analyzer
    if _static_analyzer is None:
        from agents.static_analyzer import StaticAnalyzer
        _static_analyzer = StaticAnalyzer()
    return _static_analyzer


def _get_semantic_analyzer():
    global _semantic_analyzer
    if _semantic_analyzer is None:
        from agents.semantic_analyzer import SemanticAnalyzer
        _semantic_analyzer = SemanticAnalyzer()
    return _semantic_analyzer


def _get_deep_verifier():
    global _deep_verifier
    if _deep_verifier is None:
        from agents.deep_verifier import DeepVerifier
        _deep_verifier = DeepVerifier()
    return _deep_verifier


# ── 进度更新 ──

def _update_progress(task_id: str, status: str, progress: int, agent_status: dict | None = None):
    """更新任务进度到 Redis（连接池复用）"""
    r = _get_redis()
    data = {
        "task_id": task_id,
        "status": status,
        "progress": progress,
        "agent_status": agent_status or {},
        "updated_at": datetime.now().isoformat(),
    }
    r.set(f"task:{task_id}:status", json.dumps(data), ex=86400)


# ── 核心分析任务 ──

@celery_app.task(bind=True, name="analyze_codebase")
def analyze_codebase_task(self, task_id: str, source_config: dict[str, Any]) -> dict:
    """
    执行代码安全分析。

    流程：
      1. 获取代码（Git clone / 解压 ZIP / 读取上传文件）
      2. Agent 1 + Agent 2: 静态分析与语义分析（并行）
      3. Agent 3: 深度验证（交叉验证）
      4. Agent 4: 报告生成（JSON/SARIF/PDF）
    """
    logger.info(f"[{task_id}] Starting analysis, source={source_config.get('source')}")
    work_dir = None
    nutrient = NutrientDWSClient()

    try:
        # 阶段 1: 准备代码
        _update_progress(task_id, "analyzing", 5, {
            "agent_1_static": "preparing",
            "agent_2_semantic": "pending",
            "agent_3_verifier": "pending",
            "agent_4_report": "pending",
        })
        work_dir = _prepare_code(task_id, source_config)
        if not work_dir:
            raise ValueError("Failed to prepare source code")
        logger.info(f"[{task_id}] Code prepared at {work_dir}")

        # 阶段 2: Agent 1 + Agent 2 并行执行
        _update_progress(task_id, "analyzing", 15, {
            "agent_1_static": "running",
            "agent_2_semantic": "running",
            "agent_3_verifier": "pending",
            "agent_4_report": "pending",
        })

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_static = executor.submit(_run_static_analysis, task_id, work_dir)
            future_semantic = executor.submit(_run_semantic_analysis, task_id, work_dir, [])

            static_findings = future_static.result()
            semantic_findings = future_semantic.result()

        _update_progress(task_id, "analyzing", 55, {
            "agent_1_static": "completed",
            "agent_2_semantic": "completed",
            "agent_3_verifier": "pending",
            "agent_4_report": "pending",
        })
        logger.info(f"[{task_id}] Static: {len(static_findings)} findings, Semantic: {len(semantic_findings)} findings")

        # 合并去重
        merged_findings = _merge_findings(static_findings, semantic_findings)

        # 阶段 3: Agent 3 — 深度验证
        _update_progress(task_id, "verifying", 75, {
            "agent_1_static": "completed",
            "agent_2_semantic": "completed",
            "agent_3_verifier": "running",
            "agent_4_report": "pending",
        })
        verified_findings = _run_verification(task_id, work_dir, merged_findings)
        _update_progress(task_id, "verifying", 90, {
            "agent_1_static": "completed",
            "agent_2_semantic": "completed",
            "agent_3_verifier": "completed",
            "agent_4_report": "pending",
        })
        logger.info(f"[{task_id}] Verified: {len(verified_findings)} findings")

        # 阶段 4: Agent 4 — 报告生成
        _update_progress(task_id, "generating_report", 95, {
            "agent_1_static": "completed",
            "agent_2_semantic": "completed",
            "agent_3_verifier": "completed",
            "agent_4_report": "running",
        })
        report = _generate_report(task_id, verified_findings, source_config.get("output_formats", ["json"]), nutrient)
        _update_progress(task_id, "completed", 100, {
            "agent_1_static": "completed",
            "agent_2_semantic": "completed",
            "agent_3_verifier": "completed",
            "agent_4_report": "completed",
        })
        logger.info(f"[{task_id}] Report generated: {report.get('total_findings', 0)} findings")

        # 保存结果
        result_path = settings.REPORTS_DIR / f"{task_id}.json"
        result_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        return {"task_id": task_id, "status": "completed", "report": report}

    except Exception as e:
        logger.exception(f"[{task_id}] Analysis failed: {e}")
        _update_progress(task_id, "failed", 0, {
            "agent_1_static": "error",
            "agent_2_semantic": "error",
            "agent_3_verifier": "error",
            "agent_4_report": "error",
        })
        return {"task_id": task_id, "status": "failed", "error": str(e)}

    finally:
        # 清理临时文件
        if work_dir and Path(work_dir).exists():
            shutil.rmtree(work_dir, ignore_errors=True)
            logger.info(f"[{task_id}] Cleaned up work dir: {work_dir}")

        # 清理上传的 ZIP 文件（如果存在）
        zip_path_str = source_config.get("zip_path")
        if zip_path_str:
            zip_path = Path(zip_path_str)
            if zip_path.exists():
                try:
                    zip_path.unlink(missing_ok=True)
                    logger.info(f"[{task_id}] Cleaned up ZIP file: {zip_path}")
                except Exception as e:
                    logger.warning(f"[{task_id}] Failed to clean up ZIP file: {e}")


# ── 内部实现 ──

def _prepare_code(task_id: str, config: dict) -> str | None:
    """准备代码：clone / 解压 / 读取"""
    work_dir = Path(tempfile.mkdtemp(prefix=f"cr-{task_id}-"))
    source = config.get("source", "direct_upload")

    if source == "github":
        repo_url = config.get("repo_url", "").strip()
        branch = config.get("branch", "main")

        if not repo_url:
            return None

        # 白名单校验 + 防注入
        allowed_hosts = ("https://github.com/", "https://gitlab.com/", "https://gitee.com/")
        if not any(repo_url.startswith(h) for h in allowed_hosts):
            raise ValueError(f"Unsupported repo URL: {repo_url}")

        import subprocess
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", "-b", branch, repo_url, str(work_dir)],
                capture_output=True,
                timeout=120,
                check=True,
            )
            return str(work_dir)
        except subprocess.CalledProcessError as e:
            logger.error(f"Git clone failed: {e.stderr.decode()[:200]}")
            return None

    elif source == "zip":
        zip_path_str = config.get("zip_path")
        if not zip_path_str:
            logger.error(f"[{task_id}] ZIP source but zip_path is empty")
            return None

        zip_path = Path(zip_path_str)
        if not zip_path.exists():
            logger.error(f"[{task_id}] ZIP file not found: {zip_path}")
            return None

        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                infolist = zf.infolist()

                # ZIP 炸弹防护 1：解压后总大小
                total_size = sum(f.file_size for f in infolist)
                MAX_DECOMPRESSED = 100 * 1024 * 1024  # 100 MB
                if total_size > MAX_DECOMPRESSED:
                    raise ValueError(
                        f"ZIP decompressed size {total_size} bytes exceeds "
                        f"limit of {MAX_DECOMPRESSED} bytes (100MB)"
                    )

                # ZIP 炸弹防护 2：文件数量
                MAX_FILES = 10000
                if len(infolist) > MAX_FILES:
                    raise ValueError(
                        f"ZIP contains {len(infolist)} files, exceeds limit of {MAX_FILES}"
                    )

                # 路径遍历防护
                for member in infolist:
                    if member.is_dir():
                        continue
                    target = work_dir / member.filename
                    try:
                        target.resolve().relative_to(work_dir.resolve())
                    except ValueError:
                        raise ValueError(
                            f"ZIP path traversal detected: {member.filename}"
                        )

                # 解压
                zf.extractall(work_dir)

            logger.info(f"[{task_id}] ZIP extracted: {len(infolist)} files to {work_dir}")
            return str(work_dir)

        except zipfile.BadZipFile:
            logger.error(f"[{task_id}] Invalid ZIP file: {zip_path}")
            return None
        except ValueError as e:
            logger.error(f"[{task_id}] ZIP validation failed: {e}")
            return None
        except Exception as e:
            logger.exception(f"[{task_id}] ZIP extraction failed: {e}")
            return None

    elif source == "direct_upload":
        # TODO: 实现文件内容写入
        return str(work_dir)

    return None


def _run_static_analysis(task_id: str, code_path: str) -> list[dict]:
    """Agent 1: 静态分析（Semgrep）"""
    try:
        analyzer = _get_static_analyzer()
        results = analyzer.analyze(code_path)
        return results if isinstance(results, list) else []
    except Exception as e:
        logger.error(f"[{task_id}] Static analysis failed: {e}")
        return [{"type": "error", "message": f"Static analysis failed: {e}", "severity": "info"}]


def _run_semantic_analysis(task_id: str, code_path: str, static_findings: list[dict]) -> list[dict]:
    """Agent 2: 语义分析（LLM）"""
    try:
        analyzer = _get_semantic_analyzer()
        results = analyzer.analyze(code_path, static_findings)
        return results if isinstance(results, list) else static_findings
    except Exception as e:
        logger.error(f"[{task_id}] Semantic analysis failed: {e}")
        return static_findings


def _run_verification(task_id: str, code_path: str, findings: list[dict]) -> list[dict]:
    """Agent 3: 深度验证（交叉验证）"""
    try:
        verifier = _get_deep_verifier()
        results = verifier.verify(code_path, findings)
        return results if isinstance(results, list) else findings
    except Exception as e:
        logger.error(f"[{task_id}] Verification failed: {e}")
        return findings


def _merge_findings(static: list[dict], semantic: list[dict]) -> list[dict]:
    """合并静态分析和语义分析结果，去重"""
    merged = {f.get("id", f.get("title", str(hash(str(f))))): f for f in static}
    for f in semantic:
        key = f.get("id", f.get("title", str(hash(str(f)))))
        if key in merged:
            # 合并：取更高 severity
            existing = merged[key]
            sev_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
            if sev_order.get(f.get("severity", "info"), 0) > sev_order.get(existing.get("severity", "info"), 0):
                merged[key] = f
        else:
            merged[key] = f
    return list(merged.values())


def _generate_report(task_id: str, findings: list[dict], formats: list[str], nutrient: NutrientDWSClient) -> dict:
    """Agent 4: 报告生成"""
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        sev = f.get("severity", "info").lower()
        if sev in summary:
            summary[sev] += 1

    report = {
        "task_id": task_id,
        "generated_at": datetime.now().isoformat(),
        "summary": summary,
        "findings": findings,
        "total_findings": len(findings),
    }

    # SARIF
    if "sarif" in formats:
        sarif_path = settings.REPORTS_DIR / f"{task_id}.sarif"
        sarif = _to_sarif(findings)
        sarif_path.write_text(json.dumps(sarif, indent=2), encoding="utf-8")
        report["sarif_path"] = str(sarif_path)

    # PDF via Nutrient DWS
    if "pdf" in formats:
        pdf_path = settings.REPORTS_DIR / f"{task_id}.pdf"
        import asyncio
        pdf_bytes = asyncio.run(nutrient.generate_pdf(report))
        if pdf_bytes:
            # 签名
            signed_bytes = asyncio.run(nutrient.sign_pdf(pdf_bytes))
            final_bytes = signed_bytes or pdf_bytes
            pdf_path.write_bytes(final_bytes)
            report["pdf_path"] = str(pdf_path)
            report["pdf_size"] = len(final_bytes)
            logger.info(f"[{task_id}] PDF saved: {pdf_path} ({len(final_bytes)} bytes)")
        else:
            report["pdf_path"] = None
            report["pdf_error"] = "Nutrient API unavailable or key not configured"
        report["digital_signature"] = "sha256:" + hashlib.sha256(json.dumps(report).encode()).hexdigest()[:32]

    return report


def _to_sarif(findings: list[dict]) -> dict:
    """转换为 SARIF 格式"""
    results = []
    for f in findings:
        results.append({
            "ruleId": f.get("type", "unknown"),
            "level": _severity_to_sarif_level(f.get("severity", "info")),
            "message": {"text": f.get("description", "")},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": f.get("file", "")},
                    "region": {"startLine": f.get("line", 0)},
                }
            }],
        })
    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/sarif-2.1/schema/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "CodeRisk Cloud", "version": "1.0.0"}},
            "results": results,
        }],
    }


def _severity_to_sarif_level(severity: str) -> str:
    mapping = {"critical": "error", "high": "error", "medium": "warning", "low": "note", "info": "none"}
    return mapping.get(severity, "none")
