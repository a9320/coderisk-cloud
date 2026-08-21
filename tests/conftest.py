"""CodeRisk Cloud — Pytest shared fixtures."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient with no external dependencies."""
    return TestClient(app)
