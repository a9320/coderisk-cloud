"""CodeRisk Cloud — 配置管理"""

import os
from pathlib import Path


class Settings:
    # API
    API_TITLE = "CodeRisk Cloud"
    API_VERSION = "1.0.0"
    API_PREFIX = "/api/v1"

    # Redis (Celery Broker + Backend)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # CodeRisk Agent — 自动探测路径
    _default_paths = [
        os.getenv("CODERISK_PATH"),
        str(Path(__file__).parent.parent.parent / "code-risk-agent"),
        "/app/code-risk-agent",
        str(Path.home() / "code-risk-agent"),
    ]
    CODERISK_PATH = next(
        (p for p in _default_paths if p and Path(p).exists()),
        None
    )
    if not CODERISK_PATH:
        # 开发环境降级：允许不存在，但运行时检查
        CODERISK_PATH = os.getenv("CODERISK_PATH", "/app/code-risk-agent")

    # Nutrient DWS
    NUTRIENT_API_KEY = os.getenv("NUTRIENT_DWS_API_KEY", "")
    NUTRIENT_API_URL = os.getenv("NUTRIENT_DWS_API_URL", "https://api.nutrient.io/build")

    # Worker
    WORKER_CONCURRENCY = int(os.getenv("WORKER_CONCURRENCY", "2"))

    # Auth
    API_KEY = os.getenv("CODERISK_API_KEY", "dev-key-change-in-production")

    # Storage
    REPORTS_DIR = Path(os.getenv("REPORTS_DIR", str(Path(__file__).parent.parent / "reports")))
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Security
    GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")


settings = Settings()
