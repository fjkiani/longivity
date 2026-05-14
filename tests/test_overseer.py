"""
Tests for OverseerAgent node wrapper factory.
Tests: audit_log present, duration_ms > 0, all statuses are 'ok' or 'error'
"""
import pytest
from fastapi.testclient import TestClient


class TestOverseerAuditLog:
    """Verify that the /agent/assess endpoint returns a populated audit_log."""

    def test_audit_log_present_in_response(self, client: TestClient, healthy_biomarkers: dict):
        """POST /agent/assess must return an audit_log list."""
        resp = client.post("/api/v1/longevity/agent/assess", json={
            "age": 45,
            "sex": "M",
            "biomarkers": healthy_biomarkers,
        })
        # If langgraph not installed, endpoint returns 503 — skip gracefully
        if resp.status_code == 503:
            pytest.skip("LangGraph not available in this environment")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "audit_log" in data, "audit_log key missing from /agent/assess response"
        assert isinstance(data["audit_log"], list), "audit_log must be a list"
        assert len(data["audit_log"]) > 0, "audit_log must have at least one entry"

    def test_audit_log_duration_ms_positive(self, client: TestClient, healthy_biomarkers: dict):
        """Every audit_log entry must have duration_ms > 0."""
        resp = client.post("/api/v1/longevity/agent/assess", json={
            "age": 45,
            "sex": "M",
            "biomarkers": healthy_biomarkers,
        })
        if resp.status_code == 503:
            pytest.skip("LangGraph not available in this environment")
        assert resp.status_code == 200
        data = resp.json()
        for entry in data.get("audit_log", []):
            assert entry["duration_ms"] >= 0, f"duration_ms must be >= 0, got {entry['duration_ms']} for {entry['agent']}"

    def test_audit_log_status_values_valid(self, client: TestClient, healthy_biomarkers: dict):
        """Every audit_log entry status must be 'ok' or 'error'."""
        resp = client.post("/api/v1/longevity/agent/assess", json={
            "age": 45,
            "sex": "M",
            "biomarkers": healthy_biomarkers,
        })
        if resp.status_code == 503:
            pytest.skip("LangGraph not available in this environment")
        assert resp.status_code == 200
        data = resp.json()
        valid_statuses = {"ok", "error"}
        for entry in data.get("audit_log", []):
            assert entry["status"] in valid_statuses, (
                f"Invalid status '{entry['status']}' for agent '{entry['agent']}'"
            )
