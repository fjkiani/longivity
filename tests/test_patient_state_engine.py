"""Tests for PatientStateEngine — state machine."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from datetime import datetime, timezone, timedelta
from longivity.services.patient_state_engine import (
    PatientState, compute_patient_state, _last_event, _is_after
)


def _ts(offset_days: int = 0) -> str:
    """Return ISO timestamp offset_days from now."""
    dt = datetime.now(timezone.utc) + timedelta(days=offset_days)
    return dt.isoformat()


def _event(event_type: str, offset_days: int = 0, payload: dict = None) -> dict:
    return {
        "event_type": event_type,
        "event_at": _ts(offset_days),
        "payload": payload or {},
        "source": "system",
    }


EMPTY_GAPS = {"coverage_pct": 0.0, "missing_tier1": [], "escalation_triggered": []}
FULL_GAPS = {"coverage_pct": 100.0, "missing_tier1": [], "escalation_triggered": []}
PARTIAL_GAPS = {"coverage_pct": 50.0, "missing_tier1": ["apob", "lpa"], "escalation_triggered": []}
ESCALATION_GAPS = {
    "coverage_pct": 85.0,
    "missing_tier1": [],
    "escalation_triggered": [{"rule_id": "ESC-001", "trigger_marker": "glucose", "trigger_value": 108.0}],
}


class TestHelpers:
    def test_last_event_returns_most_recent(self):
        # Capture the event object so we compare the same timestamp string
        ev_minus5 = _event("panel_uploaded", -5)
        timeline = [
            _event("panel_uploaded", -10),
            ev_minus5,
            _event("assessment_run", -3),
        ]
        result = _last_event(timeline, "panel_uploaded")
        assert result is not None
        assert result["event_at"] == ev_minus5["event_at"]

    def test_last_event_returns_none_if_not_found(self):
        timeline = [_event("panel_uploaded", -5)]
        assert _last_event(timeline, "assessment_run") is None

    def test_last_event_accepts_frozenset(self):
        timeline = [_event("panel_uploaded", -5), _event("panel_created_manual", -3)]
        result = _last_event(timeline, frozenset({"panel_uploaded", "panel_created_manual"}))
        assert result["event_type"] == "panel_created_manual"

    def test_is_after_basic(self):
        assert _is_after(_ts(-1), _ts(-5)) is True
        assert _is_after(_ts(-5), _ts(-1)) is False
        assert _is_after(None, _ts(-1)) is False
        assert _is_after(_ts(-1), None) is True


class TestPatientStateNew:
    def test_no_panels_is_new(self):
        assert compute_patient_state([], EMPTY_GAPS) == PatientState.NEW

    def test_only_non_panel_events_is_new(self):
        timeline = [_event("intelligence_computed", -1)]
        assert compute_patient_state(timeline, EMPTY_GAPS) == PatientState.NEW


class TestPatientStateDataIncomplete:
    def test_low_coverage_is_data_incomplete(self):
        timeline = [_event("panel_uploaded", -5)]
        assert compute_patient_state(timeline, PARTIAL_GAPS) == PatientState.DATA_INCOMPLETE

    def test_zero_coverage_is_data_incomplete(self):
        timeline = [_event("panel_uploaded", -5)]
        assert compute_patient_state(timeline, EMPTY_GAPS) == PatientState.DATA_INCOMPLETE

    def test_escalation_firing_is_data_incomplete(self):
        timeline = [_event("panel_uploaded", -5)]
        assert compute_patient_state(timeline, ESCALATION_GAPS) == PatientState.DATA_INCOMPLETE

    def test_escalation_with_pending_order_is_order_pending(self):
        timeline = [
            _event("panel_uploaded", -10),
            _event("test_order_generated", -5),
        ]
        assert compute_patient_state(timeline, ESCALATION_GAPS) == PatientState.ORDER_PENDING

    def test_escalation_with_approved_order_is_data_incomplete(self):
        # Order was generated AND approved — no longer pending
        timeline = [
            _event("panel_uploaded", -10),
            _event("test_order_generated", -5),
            _event("test_order_approved", -3),
        ]
        assert compute_patient_state(timeline, ESCALATION_GAPS) == PatientState.DATA_INCOMPLETE


class TestPatientStateOrderPending:
    def test_generated_not_approved_is_order_pending(self):
        timeline = [
            _event("panel_uploaded", -10),
            _event("test_order_generated", -5),
        ]
        assert compute_patient_state(timeline, PARTIAL_GAPS) == PatientState.ORDER_PENDING

    def test_approved_after_generated_is_not_order_pending(self):
        timeline = [
            _event("panel_uploaded", -10),
            _event("test_order_generated", -5),
            _event("test_order_approved", -3),
        ]
        # Still data incomplete (coverage 50%)
        assert compute_patient_state(timeline, PARTIAL_GAPS) == PatientState.DATA_INCOMPLETE


class TestPatientStateAssessmentPending:
    def test_full_coverage_no_assessment_is_assessment_pending(self):
        timeline = [_event("panel_uploaded", -5)]
        assert compute_patient_state(timeline, FULL_GAPS) == PatientState.ASSESSMENT_PENDING

    def test_assessment_before_panel_is_assessment_pending(self):
        timeline = [
            _event("assessment_run", -10),
            _event("panel_uploaded", -5),  # new panel after assessment
        ]
        assert compute_patient_state(timeline, FULL_GAPS) == PatientState.ASSESSMENT_PENDING

    def test_assessment_after_panel_is_not_assessment_pending(self):
        timeline = [
            _event("panel_uploaded", -10),
            _event("assessment_run", -5),
        ]
        # No hallmarks → MONITORING
        assert compute_patient_state(timeline, FULL_GAPS, assessment={}) == PatientState.MONITORING


class TestPatientStateCompoundCandidate:
    def _assessment_with_hallmarks(self) -> dict:
        return {
            "hallmark_narrative": {
                "nutrient_sensing": {
                    "status": "PRIMARY_DRIVER",
                    "phenoage_signal": 0.5,
                    "supplementary_signal": 0.3,
                }
            }
        }

    def test_active_hallmarks_no_compound_is_compound_candidate(self):
        timeline = [
            _event("panel_uploaded", -10),
            _event("assessment_run", -5),
        ]
        assert compute_patient_state(
            timeline, FULL_GAPS, self._assessment_with_hallmarks()
        ) == PatientState.COMPOUND_CANDIDATE

    def test_compound_started_is_monitoring(self):
        timeline = [
            _event("panel_uploaded", -20),
            _event("assessment_run", -15),
            _event("compound_started", -10),
        ]
        assert compute_patient_state(
            timeline, FULL_GAPS, self._assessment_with_hallmarks()
        ) == PatientState.MONITORING

    def test_compound_stopped_is_compound_candidate_again(self):
        timeline = [
            _event("panel_uploaded", -30),
            _event("assessment_run", -25),
            _event("compound_started", -20),
            _event("compound_stopped", -5),
        ]
        assert compute_patient_state(
            timeline, FULL_GAPS, self._assessment_with_hallmarks()
        ) == PatientState.COMPOUND_CANDIDATE


class TestPatientStateMonitoring:
    def test_full_coverage_fresh_assessment_no_hallmarks_is_monitoring(self):
        timeline = [
            _event("panel_uploaded", -10),
            _event("assessment_run", -5),
        ]
        assert compute_patient_state(timeline, FULL_GAPS, {}) == PatientState.MONITORING

    def test_monitoring_after_compound_started(self):
        timeline = [
            _event("panel_uploaded", -30),
            _event("assessment_run", -25),
            _event("compound_started", -20),
        ]
        assessment = {
            "hallmark_narrative": {
                "nutrient_sensing": {"status": "PRIMARY_DRIVER", "phenoage_signal": 0.5, "supplementary_signal": 0.0}
            }
        }
        assert compute_patient_state(timeline, FULL_GAPS, assessment) == PatientState.MONITORING
