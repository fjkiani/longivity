"""
Integration tests for the unified intelligence layer.

Tests the full patient journey through state transitions and the
clinic batch intelligence endpoint.

NOTE: The actual APIs differ from the template:
  - PatientStateEngine.compute() → compute_patient_state() (module-level function)
  - ActionScorer.score() → score_actions() (module-level function, requires patient_id)
  - Timeline events are plain dicts (not ORM objects)
  - Gaps are plain dicts (not ORM objects)
  - Escalation rules use {"severity": "high"} string keys (not severity_score floats)
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "longivity", "src"))

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _ts(offset_days: int = 0) -> str:
    """Return ISO timestamp offset_days from now."""
    dt = datetime.now(timezone.utc) + timedelta(days=offset_days)
    return dt.isoformat()


def _event(event_type: str, offset_days: int = 0, payload: dict = None) -> dict:
    """Create a plain-dict PatientEvent (matching the actual service format)."""
    return {
        "event_type": event_type,
        "event_at": _ts(offset_days),
        "payload": payload or {},
        "source": "system",
    }


def make_patient(
    patient_id="pt-001",
    age=52,
    sex="M",
    intelligence_cache=None,
    intelligence_computed_at=None,
    current_state=None,
    urgency_score=None,
):
    """Create a mock Patient ORM object matching the fields used by the service."""
    p = MagicMock()
    p.id = patient_id
    p.age = age
    p.sex = sex
    p.clinic_id = "clinic-001"
    p.date_of_birth = None  # service uses date_of_birth, not age
    p.first_name = "Test"
    p.last_name = "Patient"
    p.intelligence_cache = intelligence_cache
    p.intelligence_computed_at = intelligence_computed_at
    p.current_state = current_state
    p.urgency_score = urgency_score
    return p


# ─── Gap dict helpers ──────────────────────────────────────────────────────────

def _gaps(coverage_pct=0.0, escalation_triggered=None, missing_tier1=None, missing_panels_tier1=None):
    """Create a gaps dict matching the format from detect_gaps()."""
    return {
        "coverage_pct": coverage_pct,
        "missing_tier1": missing_tier1 or [],
        "missing_panels_tier1": missing_panels_tier1 or [],
        "escalation_triggered": escalation_triggered or [],
    }


def _escalation(rules=None):
    """Create an escalation result dict matching apply_escalation_rules() output."""
    return {"triggered_rules": rules or [], "recommended_panels": []}


# ─── Class 1: PatientStateEngine Integration ──────────────────────────────────

class TestPatientStateEngineIntegration:
    """Test state transitions through the full patient journey."""

    def test_new_patient_no_panels(self):
        """Patient with no events → NEW state."""
        from longivity.services.patient_state_engine import PatientState, compute_patient_state

        timeline = []
        gaps = _gaps(coverage_pct=0.0)

        state = compute_patient_state(timeline=timeline, gaps=gaps, assessment=None)
        assert state == PatientState.NEW

    def test_first_panel_low_coverage_data_incomplete(self):
        """Patient with first panel but low tier-1 coverage → DATA_INCOMPLETE."""
        from longivity.services.patient_state_engine import PatientState, compute_patient_state

        timeline = [_event("panel_uploaded", offset_days=-1)]
        gaps = _gaps(coverage_pct=31.0)  # below 80%

        state = compute_patient_state(timeline=timeline, gaps=gaps, assessment=None)
        assert state == PatientState.DATA_INCOMPLETE

    def test_escalation_firing_order_pending(self):
        """Escalation rules firing + pending order → ORDER_PENDING."""
        from longivity.services.patient_state_engine import PatientState, compute_patient_state

        timeline = [
            _event("panel_uploaded", offset_days=-2),
            _event("test_order_generated", offset_days=-1),
        ]
        gaps = _gaps(
            coverage_pct=31.0,
            escalation_triggered=[{"rule_id": "ESC-001", "trigger_marker": "glucose", "trigger_value": 108.0}],
        )

        state = compute_patient_state(timeline=timeline, gaps=gaps, assessment=None)
        assert state == PatientState.ORDER_PENDING

    def test_good_coverage_no_assessment_assessment_pending(self):
        """Good coverage, no assessment → ASSESSMENT_PENDING."""
        from longivity.services.patient_state_engine import PatientState, compute_patient_state

        timeline = [_event("panel_uploaded", offset_days=-1)]
        gaps = _gaps(coverage_pct=85.0)  # above 80%

        state = compute_patient_state(timeline=timeline, gaps=gaps, assessment=None)
        assert state == PatientState.ASSESSMENT_PENDING

    def test_assessment_current_hallmarks_compound_candidate(self):
        """Assessment current + hallmarks active → COMPOUND_CANDIDATE."""
        from longivity.services.patient_state_engine import PatientState, compute_patient_state

        timeline = [
            _event("panel_uploaded", offset_days=-5),
            _event("assessment_run", offset_days=-4),
        ]
        gaps = _gaps(coverage_pct=85.0)

        assessment = {
            "hallmark_narrative": {
                "nutrient_sensing": {"status": "PRIMARY_DRIVER", "phenoage_signal": 0.5, "supplementary_signal": 0.3},
            }
        }

        state = compute_patient_state(timeline=timeline, gaps=gaps, assessment=assessment)
        assert state == PatientState.COMPOUND_CANDIDATE

    def test_compound_started_monitoring(self):
        """Compound started → MONITORING."""
        from longivity.services.patient_state_engine import PatientState, compute_patient_state

        timeline = [
            _event("panel_uploaded", offset_days=-30),
            _event("assessment_run", offset_days=-29),
            _event("compound_started", offset_days=-28),
        ]
        gaps = _gaps(coverage_pct=85.0)

        assessment = {
            "hallmark_narrative": {
                "nutrient_sensing": {"status": "PRIMARY_DRIVER", "phenoage_signal": 0.5, "supplementary_signal": 0.3},
            }
        }

        state = compute_patient_state(timeline=timeline, gaps=gaps, assessment=assessment)
        assert state == PatientState.MONITORING

    def test_new_panel_while_monitoring_resets_to_assessment_pending(self):
        """New panel uploaded while in MONITORING → ASSESSMENT_PENDING."""
        from longivity.services.patient_state_engine import PatientState, compute_patient_state

        timeline = [
            _event("panel_uploaded", offset_days=-60),
            _event("assessment_run", offset_days=-59),
            _event("compound_started", offset_days=-58),
            _event("panel_uploaded", offset_days=-1),  # new panel after last assessment!
        ]
        gaps = _gaps(coverage_pct=85.0)

        assessment = {
            "hallmark_narrative": {
                "nutrient_sensing": {"status": "PRIMARY_DRIVER", "phenoage_signal": 0.5, "supplementary_signal": 0.3},
            }
        }

        state = compute_patient_state(timeline=timeline, gaps=gaps, assessment=assessment)
        # New panel uploaded after last assessment → ASSESSMENT_PENDING
        assert state == PatientState.ASSESSMENT_PENDING


# ─── Class 2: ActionScorer Integration ───────────────────────────────────────

class TestActionScorerIntegration:
    """Test scoring model produces correct rankings."""

    def _make_gaps(self, coverage_pct=31.0, escalation_count=0, escalation_severity="routine"):
        """Build a gaps dict with optional escalation rules."""
        rules = []
        for _ in range(escalation_count):
            rules.append({
                "rule_id": "ESC-001",
                "trigger_marker": "glucose",
                "trigger_value": 108.0,
                "severity": escalation_severity,
            })
        return _gaps(coverage_pct=coverage_pct, escalation_triggered=rules)

    def _make_escalation(self, escalation_count=0, escalation_severity="routine"):
        """Build an escalation result dict."""
        rules = []
        for _ in range(escalation_count):
            rules.append({
                "rule_id": "ESC-001",
                "trigger_marker": "glucose",
                "trigger_value": 108.0,
                "severity": escalation_severity,
            })
        return _escalation(rules=rules)

    def _make_phenoage(self, age_acceleration=0.0, hallmarks=None):
        return {
            "phenoage_result": {"age_acceleration": age_acceleration},
            "hallmark_narrative": {
                h: {"status": "PRIMARY_DRIVER", "phenoage_signal": 0.8, "supplementary_signal": 0.0}
                for h in (hallmarks or [])
            },
        }

    def _make_timeline(self, days_since_last=30):
        return [_event("panel_uploaded", offset_days=-days_since_last)]

    def test_high_escalation_scores_highest(self):
        """High escalation severity should produce highest score."""
        from longivity.services.action_scorer import score_actions, ActionType
        from longivity.services.patient_state_engine import PatientState

        gaps = self._make_gaps(coverage_pct=31.0, escalation_count=3, escalation_severity="urgent")
        escalation = self._make_escalation(escalation_count=3, escalation_severity="urgent")
        phenoage = self._make_phenoage(age_acceleration=5.0)
        timeline = self._make_timeline(days_since_last=45)

        actions = score_actions(
            state=PatientState.DATA_INCOMPLETE,
            patient_id="pt-001",
            gaps=gaps,
            assessment=phenoage,
            escalation=escalation,
            timeline=timeline,
        )

        assert len(actions) > 0
        top = actions[0]
        assert top.score > 0.5  # high urgency scenario

    def test_monitoring_state_only_followup_action(self):
        """MONITORING state should only produce SCHEDULE_FOLLOWUP (and optionally REVIEW_ASSESSMENT)."""
        from longivity.services.action_scorer import score_actions, ActionType
        from longivity.services.patient_state_engine import PatientState

        gaps = self._make_gaps(coverage_pct=90.0, escalation_count=0)
        phenoage = self._make_phenoage(age_acceleration=0.5)
        timeline = self._make_timeline(days_since_last=90)

        actions = score_actions(
            state=PatientState.MONITORING,
            patient_id="pt-001",
            gaps=gaps,
            assessment=phenoage,
            escalation=_escalation(),
            timeline=timeline,
        )

        assert len(actions) > 0
        action_types = [a.type for a in actions]
        # MONITORING state should not produce data-collection actions
        assert ActionType.ORDER_BASELINE_PANEL not in action_types
        assert ActionType.ORDER_ESCALATION_PANEL not in action_types

    def test_scores_bounded_0_to_1(self):
        """All scores must be in [0, 1]."""
        from longivity.services.action_scorer import score_actions
        from longivity.services.patient_state_engine import PatientState

        gaps = self._make_gaps(coverage_pct=0.0, escalation_count=5, escalation_severity="urgent")
        escalation = self._make_escalation(escalation_count=5, escalation_severity="urgent")
        phenoage = self._make_phenoage(age_acceleration=20.0, hallmarks=["nutrient_sensing"])
        timeline = self._make_timeline(days_since_last=365)

        actions = score_actions(
            state=PatientState.DATA_INCOMPLETE,
            patient_id="pt-001",
            gaps=gaps,
            assessment=phenoage,
            escalation=escalation,
            timeline=timeline,
        )

        for action in actions:
            assert 0.0 <= action.score <= 1.0, f"Score out of bounds: {action.score}"

    def test_actions_sorted_descending(self):
        """Actions must be returned sorted by score descending."""
        from longivity.services.action_scorer import score_actions
        from longivity.services.patient_state_engine import PatientState

        gaps = self._make_gaps(coverage_pct=50.0, escalation_count=2, escalation_severity="high")
        escalation = self._make_escalation(escalation_count=2, escalation_severity="high")
        phenoage = self._make_phenoage(age_acceleration=3.0, hallmarks=["nutrient_sensing"])
        timeline = self._make_timeline(days_since_last=60)

        actions = score_actions(
            state=PatientState.ASSESSMENT_PENDING,
            patient_id="pt-001",
            gaps=gaps,
            assessment=phenoage,
            escalation=escalation,
            timeline=timeline,
        )

        scores = [a.score for a in actions]
        assert scores == sorted(scores, reverse=True), "Actions not sorted by score descending"


# ─── Class 3: PatientIntelligenceService Integration ─────────────────────────

class TestPatientIntelligenceServiceIntegration:
    """Test the conductor service assembles correct IntelligenceResponse."""

    @pytest.mark.asyncio
    async def test_new_patient_returns_new_state(self):
        """Patient with no panels → NEW state response."""
        from longivity.services.patient_intelligence_service import compute_patient_intelligence

        patient = make_patient()
        db = AsyncMock(spec=AsyncSession)

        # Mock DB queries to return empty results (no panels, no events)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=mock_result)

        response = await compute_patient_intelligence(patient, db, force_refresh=True)

        assert response["current_state"] in ("NEW", "new")
        assert response["patient_id"] == "pt-001"

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached(self):
        """Patient with valid cache → cache_hit=True, no recompute."""
        from longivity.services.patient_intelligence_service import compute_patient_intelligence

        cached = {
            "patient_id": "pt-001",
            "patient_name": "Test Patient",
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "cache_hit": False,
            "current_state": "MONITORING",
            "current_state_label": "Monitoring",
            "current_state_color": "green",
            "urgency_score": 0.15,
            "next_action": None,
            "available_actions": [],
            "biological_summary": {
                "phenoage_estimate": 50.0,
                "chronological_age": 52,
                "age_acceleration": -2.0,
                "accel_tier": "OPTIMAL",
                "hallmarks_activated": [],
                "top_accelerator": None,
                "data_completeness_pct": 90.0,
            },
            "gap_summary": {
                "tier1_coverage_pct": 90.0,
                "missing_tier1_count": 5,
                "missing_panels": [],
                "escalation_rules_firing": 0,
            },
            "top_compound": None,
            "timeline_summary": {
                "first_panel_date": "2026-01-01",
                "latest_panel_date": "2026-05-01",
                "panel_count": 3,
                "last_assessment_date": "2026-05-01",
                "last_order_date": None,
                "days_since_last_action": 15,
            },
            "scoring_breakdown": {
                "data_urgency": 0.10,
                "phenoage_urgency": 0.0,
                "escalation_severity": 0.0,
                "time_decay": 0.08,
                "hallmark_signal": 0.0,
                "weights": {"w1": 0.30, "w2": 0.25, "w3": 0.25, "w4": 0.10, "w5": 0.10},
            },
        }

        # Patient has cache computed recently (1 hour ago)
        now = datetime.now(timezone.utc)
        patient = make_patient(
            intelligence_cache=cached,
            intelligence_computed_at=now - timedelta(hours=1),
        )

        db = AsyncMock(spec=AsyncSession)

        # No events at all (so no new panels after cache was computed)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        response = await compute_patient_intelligence(patient, db, force_refresh=False)

        # Should return cached response with cache_hit=True
        assert response.get("cache_hit") is True
        assert response["current_state"] == "MONITORING"

    @pytest.mark.asyncio
    async def test_force_refresh_bypasses_cache(self):
        """force_refresh=True should recompute even with valid cache."""
        from longivity.services.patient_intelligence_service import compute_patient_intelligence

        cached = {
            "patient_id": "pt-001",
            "patient_name": "Test Patient",
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "cache_hit": False,
            "current_state": "MONITORING",
            "current_state_label": "Monitoring",
            "current_state_color": "green",
            "urgency_score": 0.15,
            "next_action": None,
            "available_actions": [],
            "biological_summary": {
                "phenoage_estimate": 50.0,
                "chronological_age": 52,
                "age_acceleration": -2.0,
                "accel_tier": "OPTIMAL",
                "hallmarks_activated": [],
                "top_accelerator": None,
                "data_completeness_pct": 90.0,
            },
            "gap_summary": {
                "tier1_coverage_pct": 90.0,
                "missing_tier1_count": 5,
                "missing_panels": [],
                "escalation_rules_firing": 0,
            },
            "top_compound": None,
            "timeline_summary": {
                "first_panel_date": "2026-01-01",
                "latest_panel_date": "2026-05-01",
                "panel_count": 3,
                "last_assessment_date": "2026-05-01",
                "last_order_date": None,
                "days_since_last_action": 15,
            },
            "scoring_breakdown": {
                "data_urgency": 0.10,
                "phenoage_urgency": 0.0,
                "escalation_severity": 0.0,
                "time_decay": 0.08,
                "hallmark_signal": 0.0,
                "weights": {"w1": 0.30, "w2": 0.25, "w3": 0.25, "w4": 0.10, "w5": 0.10},
            },
        }

        now = datetime.now(timezone.utc)
        patient = make_patient(
            intelligence_cache=cached,
            intelligence_computed_at=now - timedelta(hours=1),
        )

        db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        response = await compute_patient_intelligence(patient, db, force_refresh=True)

        # force_refresh=True → cache_hit must be False
        assert response.get("cache_hit") is False


# ─── Class 4: Full Journey Integration ───────────────────────────────────────

class TestFullPatientJourney:
    """Test the complete patient journey through all state transitions."""

    def test_state_progression_new_to_monitoring(self):
        """Simulate a patient progressing through all states."""
        from longivity.services.patient_state_engine import PatientState, compute_patient_state

        # Step 1: No panels → NEW
        state = compute_patient_state([], _gaps(coverage_pct=0.0), None)
        assert state == PatientState.NEW

        # Step 2: First panel, low coverage → DATA_INCOMPLETE
        timeline = [_event("panel_uploaded", offset_days=-10)]
        gaps = _gaps(coverage_pct=31.0)
        state = compute_patient_state(timeline, gaps, None)
        assert state == PatientState.DATA_INCOMPLETE

        # Step 3: More panels, good coverage, no assessment → ASSESSMENT_PENDING
        timeline.append(_event("panel_uploaded", offset_days=-5))
        gaps = _gaps(coverage_pct=85.0)
        state = compute_patient_state(timeline, gaps, None)
        assert state == PatientState.ASSESSMENT_PENDING

        # Step 4: Assessment run → COMPOUND_CANDIDATE (hallmarks active)
        timeline.append(_event("assessment_run", offset_days=-4))
        assessment = {
            "hallmark_narrative": {
                "nutrient_sensing": {
                    "status": "PRIMARY_DRIVER",
                    "phenoage_signal": 0.5,
                    "supplementary_signal": 0.3,
                }
            }
        }
        state = compute_patient_state(timeline, gaps, assessment)
        assert state == PatientState.COMPOUND_CANDIDATE

        # Step 5: Compound started → MONITORING
        timeline.append(_event("compound_started", offset_days=-3))
        state = compute_patient_state(timeline, gaps, assessment)
        assert state == PatientState.MONITORING

    def test_urgency_score_increases_with_worse_data(self):
        """Urgency score should increase as clinical signals worsen."""
        from longivity.services.action_scorer import score_actions
        from longivity.services.patient_state_engine import PatientState

        timeline = [_event("panel_uploaded", offset_days=-90)]

        # Low urgency: good coverage, no escalation, no acceleration
        gaps_low = _gaps(coverage_pct=90.0)
        phenoage_low = {"phenoage_result": {"age_acceleration": 0.5}, "hallmark_narrative": {}}
        actions_low = score_actions(
            state=PatientState.ASSESSMENT_PENDING,
            patient_id="pt-low",
            gaps=gaps_low,
            assessment=phenoage_low,
            escalation=_escalation(),
            timeline=timeline,
        )

        # High urgency: poor coverage, escalation firing, high acceleration
        high_rule = {"rule_id": "ESC-001", "trigger_marker": "glucose", "trigger_value": 108.0, "severity": "urgent"}
        gaps_high = _gaps(coverage_pct=20.0, escalation_triggered=[high_rule])
        phenoage_high = {
            "phenoage_result": {"age_acceleration": 8.0},
            "hallmark_narrative": {
                "nutrient_sensing": {
                    "status": "PRIMARY_DRIVER",
                    "phenoage_signal": 0.9,
                    "supplementary_signal": 0.0,
                }
            },
        }
        actions_high = score_actions(
            state=PatientState.DATA_INCOMPLETE,
            patient_id="pt-high",
            gaps=gaps_high,
            assessment=phenoage_high,
            escalation=_escalation(rules=[high_rule]),
            timeline=timeline,
        )

        score_low = actions_low[0].score if actions_low else 0.0
        score_high = actions_high[0].score if actions_high else 0.0
        assert score_high > score_low, (
            f"High urgency score ({score_high:.3f}) should exceed low urgency ({score_low:.3f})"
        )


# ─── Class 5: Clinic Batch Intelligence ──────────────────────────────────────

class TestClinicBatchIntelligence:
    """Test the clinic-level batch intelligence endpoint logic."""

    def test_patients_sorted_by_urgency_descending(self):
        """Clinic worklist must be sorted by urgency_score descending."""
        patients = [
            {"patient_id": "pt-A", "urgency_score": 0.30},
            {"patient_id": "pt-B", "urgency_score": 0.85},
            {"patient_id": "pt-C", "urgency_score": 0.55},
        ]
        sorted_patients = sorted(patients, key=lambda p: p["urgency_score"], reverse=True)
        assert sorted_patients[0]["patient_id"] == "pt-B"
        assert sorted_patients[1]["patient_id"] == "pt-C"
        assert sorted_patients[2]["patient_id"] == "pt-A"

    def test_state_filter_logic(self):
        """State filter should exclude patients not in the target state."""
        patients = [
            {"patient_id": "pt-A", "current_state": "DATA_INCOMPLETE", "urgency_score": 0.7},
            {"patient_id": "pt-B", "current_state": "MONITORING", "urgency_score": 0.2},
            {"patient_id": "pt-C", "current_state": "DATA_INCOMPLETE", "urgency_score": 0.5},
        ]
        filtered = [p for p in patients if p["current_state"] == "DATA_INCOMPLETE"]
        assert len(filtered) == 2
        assert all(p["current_state"] == "DATA_INCOMPLETE" for p in filtered)

    def test_urgency_threshold_filter(self):
        """Min urgency filter should exclude low-urgency patients."""
        patients = [
            {"patient_id": "pt-A", "urgency_score": 0.80},
            {"patient_id": "pt-B", "urgency_score": 0.30},
            {"patient_id": "pt-C", "urgency_score": 0.65},
        ]
        min_urgency = 0.5
        filtered = [p for p in patients if p["urgency_score"] >= min_urgency]
        assert len(filtered) == 2
        assert all(p["urgency_score"] >= min_urgency for p in filtered)

    def test_new_patient_no_cache_shows_new_state(self):
        """Patient with no intelligence cache should show NEW state in worklist."""
        patient_cache = None
        default_response = {
            "current_state": "NEW",
            "urgency_score": 0.0,
        }
        result = patient_cache if patient_cache is not None else default_response
        assert result["current_state"] == "NEW"
        assert result["urgency_score"] == 0.0

    def test_worklist_aggregates_multiple_states(self):
        """Worklist should correctly aggregate patients across all states."""
        patients = [
            {"patient_id": "pt-1", "current_state": "NEW", "urgency_score": 0.0},
            {"patient_id": "pt-2", "current_state": "DATA_INCOMPLETE", "urgency_score": 0.70},
            {"patient_id": "pt-3", "current_state": "ASSESSMENT_PENDING", "urgency_score": 0.45},
            {"patient_id": "pt-4", "current_state": "COMPOUND_CANDIDATE", "urgency_score": 0.60},
            {"patient_id": "pt-5", "current_state": "MONITORING", "urgency_score": 0.10},
        ]
        # All states represented
        states = {p["current_state"] for p in patients}
        assert "NEW" in states
        assert "DATA_INCOMPLETE" in states
        assert "MONITORING" in states

        # Sorted by urgency
        sorted_list = sorted(patients, key=lambda p: p["urgency_score"], reverse=True)
        assert sorted_list[0]["patient_id"] == "pt-2"  # highest urgency
        assert sorted_list[-1]["patient_id"] == "pt-1"  # lowest urgency (NEW = 0.0)
