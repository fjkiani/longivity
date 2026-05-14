"""
Tests for epigenetic clock service and API endpoint.
"""
import pytest
from fastapi.testclient import TestClient


class TestEpigeneticClockEndpoint:

    def test_epigenetic_clock_endpoint_200(self, client: TestClient):
        """POST /epigenetic_clock must return 200 with valid clock data."""
        resp = client.post("/api/v1/longevity/epigenetic_clock", json={
            "clock_values": {"grimAge": 65.0, "dunedinPACE": 1.12},
            "chronological_age": 55,
        })
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["status"] == "ok"
        assert "clock_results" in data

    def test_grimAge_acceleration_positive(self, client: TestClient):
        """grimAge > chronological_age should yield positive clock_acceleration."""
        resp = client.post("/api/v1/longevity/epigenetic_clock", json={
            "clock_values": {"grimAge": 65.0},
            "chronological_age": 55,
        })
        assert resp.status_code == 200
        data = resp.json()
        grim = data["clock_results"]["grimAge"]
        assert grim["clock_acceleration"] > 0, "grimAge 65 vs chrono 55 should be positive acceleration"

    def test_dunedinPACE_fast_interpretation(self, client: TestClient):
        """dunedinPACE > 1.10 should yield FAST interpretation."""
        resp = client.post("/api/v1/longevity/epigenetic_clock", json={
            "clock_values": {"dunedinPACE": 1.15},
            "chronological_age": 50,
        })
        assert resp.status_code == 200
        data = resp.json()
        pace = data["clock_results"]["dunedinPACE"]
        assert pace["pace_interpretation"] == "FAST"

    def test_no_clock_data_returns_no_clock_data_status(self, client: TestClient):
        """Empty clock_values should return status NO_CLOCK_DATA."""
        resp = client.post("/api/v1/longevity/epigenetic_clock", json={
            "clock_values": {},
            "chronological_age": 50,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "NO_CLOCK_DATA"

    def test_grimAge_slow_interpretation(self, client: TestClient):
        """grimAge well below chronological_age should yield SLOW interpretation."""
        resp = client.post("/api/v1/longevity/epigenetic_clock", json={
            "clock_values": {"grimAge": 50.0},
            "chronological_age": 60,
        })
        assert resp.status_code == 200
        data = resp.json()
        grim = data["clock_results"]["grimAge"]
        assert grim["pace_interpretation"] == "SLOW"
        assert grim["clock_acceleration"] < 0

    def test_dunedinPACE_slow_interpretation(self, client: TestClient):
        """dunedinPACE < 0.90 should yield SLOW interpretation."""
        resp = client.post("/api/v1/longevity/epigenetic_clock", json={
            "clock_values": {"dunedinPACE": 0.85},
        })
        assert resp.status_code == 200
        data = resp.json()
        pace = data["clock_results"]["dunedinPACE"]
        assert pace["pace_interpretation"] == "SLOW"

    def test_hallmark_implications_populated(self, client: TestClient):
        """Clock results should include hallmark_implications."""
        resp = client.post("/api/v1/longevity/epigenetic_clock", json={
            "clock_values": {"grimAge": 65.0, "dunedinPACE": 1.12},
            "chronological_age": 55,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["hallmark_implications"]) > 0
        assert "epigenetic_alterations" in data["hallmark_implications"]

    def test_unknown_clock_skipped_with_warning(self, client: TestClient):
        """Unknown clock names should be skipped and appear in warnings."""
        resp = client.post("/api/v1/longevity/epigenetic_clock", json={
            "clock_values": {"unknownClock": 55.0, "grimAge": 65.0},
            "chronological_age": 55,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "grimAge" in data["clock_results"]
        assert "unknownClock" not in data["clock_results"]
        assert any("unknownClock" in w for w in data.get("warnings", []))

    def test_overall_pace_interpretation_worst_case(self, client: TestClient):
        """overall_pace_interpretation should reflect worst-case across clocks."""
        resp = client.post("/api/v1/longevity/epigenetic_clock", json={
            "clock_values": {"grimAge": 55.0, "dunedinPACE": 1.15},
            "chronological_age": 55,
        })
        assert resp.status_code == 200
        data = resp.json()
        # grimAge = NORMAL (0 acceleration), dunedinPACE = FAST → overall FAST
        assert data["overall_pace_interpretation"] == "FAST"

    def test_no_chronological_age_uses_zscore(self, client: TestClient):
        """Without chronological_age, grimAge should use population mean for z-score."""
        resp = client.post("/api/v1/longevity/epigenetic_clock", json={
            "clock_values": {"grimAge": 72.0},
        })
        assert resp.status_code == 200
        data = resp.json()
        grim = data["clock_results"]["grimAge"]
        # grimAge 72 vs population_mean 60.2 → acceleration = 11.8 → FAST
        assert grim["pace_interpretation"] == "FAST"
        assert grim["z_score"] is not None

    def test_ruo_disclaimer_present(self, client: TestClient):
        """Response must include ruo_disclaimer."""
        resp = client.post("/api/v1/longevity/epigenetic_clock", json={
            "clock_values": {"horvath": 45.0},
            "chronological_age": 45,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "ruo_disclaimer" in data
        assert len(data["ruo_disclaimer"]) > 0

    def test_all_five_clocks(self, client: TestClient):
        """All five supported clocks should be processable in one request."""
        resp = client.post("/api/v1/longevity/epigenetic_clock", json={
            "clock_values": {
                "grimAge": 65.0,
                "dunedinPACE": 1.05,
                "horvath": 58.0,
                "hannum": 57.0,
                "phenoAgeDNAm": 60.0,
            },
            "chronological_age": 55,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert len(data["clocks_analyzed"]) == 5
        assert set(data["clocks_analyzed"]) == {
            "grimAge", "dunedinPACE", "horvath", "hannum", "phenoAgeDNAm"
        }
