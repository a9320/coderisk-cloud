"""Additional tests for /demo endpoint consistency."""

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def test_demo_findings_have_required_fields(client):
    resp = client.get("/demo")
    assert resp.status_code == 200
    data = resp.json()
    findings = data["findings"]
    for f in findings:
        assert "id" in f and f["id"].startswith("CR-")
        assert "severity" in f
        assert f["severity"].lower() in SEVERITY_ORDER
        assert "type" in f
        assert "file" in f
        assert "line" in f
        assert "description" in f


def test_demo_findings_sorted_by_severity(client):
    resp = client.get("/demo")
    data = resp.json()
    severities = [SEVERITY_ORDER.get(f["severity"].lower(), 0) for f in data["findings"]]
    # Should be roughly descending (critical first)
    assert severities[0] >= severities[-1]
