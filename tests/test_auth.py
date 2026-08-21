"""Tests for authentication on protected endpoints."""

VALID_PAYLOAD = {
    "source": "github",
    "repo_url": "https://github.com/a9320/coderisk-cloud",
    "output_formats": ["json"]
}


def test_missing_auth_returns_401(client):
    resp = client.post("/api/v1/analyze", json=VALID_PAYLOAD)
    assert resp.status_code == 401


def test_invalid_key_returns_403(client):
    resp = client.post(
        "/api/v1/analyze",
        json=VALID_PAYLOAD,
        headers={"Authorization": "Bearer invalid-key-12345"}
    )
    assert resp.status_code == 403


def test_valid_key_returns_200_or_422(client):
    """Valid key should pass auth; 422 means payload validation (no repo_url etc)."""
    resp = client.post(
        "/api/v1/analyze",
        json={"source": "github", "repo_url": "https://github.com/a9320/coderisk-cloud"},
        headers={"Authorization": "Bearer dev-key-change-in-production"}
    )
    # Either 200 (queued) or 422 (missing branch/output_formats) is acceptable
    assert resp.status_code in (200, 422)


def test_task_status_missing_auth_returns_401(client):
    resp = client.get("/api/v1/tasks/fake-task-id")
    assert resp.status_code == 401


def test_report_missing_auth_returns_401(client):
    resp = client.get("/api/v1/reports/fake-task-id")
    assert resp.status_code == 401
