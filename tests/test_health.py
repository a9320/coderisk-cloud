"""Tests for public health/demo endpoints."""


def test_root_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "name" in data or "version" in data or "status" in data


def test_health_returns_200_with_status(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["status"] in ("ok", "healthy", "up")


def test_docs_returns_200(client):
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


def test_demo_returns_200_with_9_findings(client):
    resp = client.get("/demo")
    assert resp.status_code == 200
    data = resp.json()
    assert "findings" in data
    assert len(data["findings"]) == 9
    # Verify structure of first finding
    first = data["findings"][0]
    assert "id" in first
    assert "severity" in first
    assert "type" in first
    assert "file" in first
