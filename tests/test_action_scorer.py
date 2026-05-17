"""Tests for ActionScorer — weighted scoring model."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from datetime import datetime, timezone, timedelta
from longivity.services.action_scorer import (
    ActionType, ActionUrgency, ScoredAction,
    score_actions, get_scoring_breakdown,
    _data_urgency, _phenoage_urgency, _escalation_severity, _time_decay, _hallmark_signal,
    DEFAULT_WEIGHTS,
)
from longivity.services.patient_state_engine import PatientState


def _ts(offset_days: int = 0) -> str:
    dt = datetime.now(timezone.utc) + timedelta(days=offset_days)
    return dt.isoformat()


def _event(event_type: str, offset_days: int = 0) -> dict:
    return {"event_type": event_type, "event_at": _ts(offset_days), "payload": {}, "source": "system"}


EMPTY_GAPS = {"coverage_pct": 0.0, "missing_tier1": [], "missing_panels_tier1": [], "escalation_triggered": []}
FULL_GAPS = {"coverage_pct": 100.0, "missing_tier1": [], "missing_panels_tier1": [], "escalation_triggered": []}
PARTIAL_GAPS = {
    "coverage_pct": 31.0,
    "missing_tier1": ["apob", "lpa", "hscrp"],
    "missing_panels_tier1": ["cmp", "cbc_with_diff"],
    "escalation_triggered": [],
}
ESCALATION_RESULT = {
    "triggered_rules": [
        {"rule_id": "ESC-009", "trigger_marker": "ldl_c", "trigger_value": 145.0, "severity": "high"},
        {"rule_id": "ESC-001", "trigger_marker": "glucose", "trigger_value": 108.0, "severity": "routine"},
    ],
    "recommended_panels": ["advanced_lipids"],
}


class TestComponents:
    def test_data_urgency_zero_coverage(self):
        assert _data_urgency({"coverage_pct": 0.0}) == 1.0

    def test_data_urgency_full_coverage(self):
        assert _data_urgency({"coverage_pct": 100.0}) == 0.0

    def test_data_urgency_partial(self):
        assert abs(_data_urgency({"coverage_pct": 31.0}) - 0.69) < 0.01

    def test_phenoage_urgency_none(self):
        assert _phenoage_urgency(None) == 0.0

    def test_phenoage_urgency_no_acceleration(self):
        assert _phenoage_urgency({"phenoage_result": {"age_acceleration": 0.0}}) == 0.0

    def test_phenoage_urgency_10yr(self):
        assert _phenoage_urgency({"phenoage_result": {"age_acceleration": 10.0}}) == 1.0

    def test_phenoage_urgency_clipped(self):
        assert _phenoage_urgency({"phenoage_result": {"age_acceleration": 20.0}}) == 1.0

    def test_phenoage_urgency_negative_clipped(self):
        assert _phenoage_urgency({"phenoage_result": {"age_acceleration": -5.0}}) == 0.0

    def test_escalation_severity_none(self):
        assert _escalation_severity(None) == 0.0

    def test_escalation_severity_no_rules(self):
        assert _escalation_severity({"triggered_rules": []}) == 0.0

    def test_escalation_severity_high(self):
        result = _escalation_severity({"triggered_rules": [{"severity": "high"}]})
        assert result == 0.75

    def test_escalation_severity_urgent(self):
        result = _escalation_severity({"triggered_rules": [{"severity": "urgent"}]})
        assert result == 1.0

    def test_escalation_severity_max_of_multiple(self):
        result = _escalation_severity({
            "triggered_rules": [{"severity": "routine"}, {"severity": "high"}]
        })
        assert result == 0.75

    def test_time_decay_empty_timeline(self):
        assert _time_decay([]) == 1.0

    def test_time_decay_recent_event(self):
        timeline = [_event("panel_uploaded", -1)]
        assert _time_decay(timeline) < 0.01

    def test_time_decay_6_months(self):
        timeline = [_event("panel_uploaded", -180)]
        assert abs(_time_decay(timeline) - 1.0) < 0.05

    def test_hallmark_signal_none(self):
        assert _hallmark_signal(None) == 0.0

    def test_hallmark_signal_from_narrative(self):
        assessment = {
            "hallmark_narrative": {
                "nutrient_sensing": {"phenoage_signal": 0.8, "supplementary_signal": 0.3}
            }
        }
        assert _hallmark_signal(assessment) == 0.8

    def test_hallmark_signal_clipped(self):
        assessment = {
            "hallmark_narrative": {
                "nutrient_sensing": {"phenoage_signal": 5.0, "supplementary_signal": 0.0}
            }
        }
        assert _hallmark_signal(assessment) == 1.0


class TestScoreActions:
    def test_new_state_returns_upload_action(self):
        actions = score_actions(PatientState.NEW, "p1", EMPTY_GAPS, None, None, [])
        assert len(actions) == 1
        assert actions[0].type == ActionType.ORDER_BASELINE_PANEL
        assert actions[0].score == 1.0

    def test_data_incomplete_returns_baseline_action(self):
        timeline = [_event("panel_uploaded", -5)]
        actions = score_actions(PatientState.DATA_INCOMPLETE, "p1", PARTIAL_GAPS, None, None, timeline)
        types = [a.type for a in actions]
        assert ActionType.ORDER_BASELINE_PANEL in types

    def test_data_incomplete_with_escalation_returns_escalation_action(self):
        timeline = [_event("panel_uploaded", -5)]
        actions = score_actions(
            PatientState.DATA_INCOMPLETE, "p1", PARTIAL_GAPS, None, ESCALATION_RESULT, timeline
        )
        types = [a.type for a in actions]
        assert ActionType.ORDER_ESCALATION_PANEL in types
        # Escalation should score higher than baseline
        esc_score = next(a.score for a in actions if a.type == ActionType.ORDER_ESCALATION_PANEL)
        base_score = next((a.score for a in actions if a.type == ActionType.ORDER_BASELINE_PANEL), 0)
        assert esc_score >= base_score

    def test_assessment_pending_returns_run_assessment(self):
        timeline = [_event("panel_uploaded", -5)]
        actions = score_actions(PatientState.ASSESSMENT_PENDING, "p1", FULL_GAPS, None, None, timeline)
        assert actions[0].type == ActionType.RUN_ASSESSMENT

    def test_compound_candidate_returns_start_compound(self):
        timeline = [_event("panel_uploaded", -10), _event("assessment_run", -5)]
        assessment = {
            "compound_recommendations": [
                {"compound": "omega3", "display_name": "Omega-3", "primary_match": "nutrient_sensing", "evidence_tier": "MR_VALIDATED"}
            ],
            "hallmark_narrative": {
                "nutrient_sensing": {"status": "PRIMARY_DRIVER", "phenoage_signal": 0.5, "supplementary_signal": 0.0}
            }
        }
        actions = score_actions(PatientState.COMPOUND_CANDIDATE, "p1", FULL_GAPS, assessment, None, timeline)
        assert actions[0].type == ActionType.START_COMPOUND
        assert "Omega-3" in actions[0].label

    def test_monitoring_returns_schedule_followup(self):
        timeline = [_event("panel_uploaded", -10), _event("assessment_run", -5)]
        actions = score_actions(PatientState.MONITORING, "p1", FULL_GAPS, {}, None, timeline)
        assert actions[0].type == ActionType.SCHEDULE_FOLLOWUP

    def test_actions_sorted_by_score_descending(self):
        timeline = [_event("panel_uploaded", -5)]
        actions = score_actions(
            PatientState.DATA_INCOMPLETE, "p1", PARTIAL_GAPS, None, ESCALATION_RESULT, timeline
        )
        scores = [a.score for a in actions]
        assert scores == sorted(scores, reverse=True)

    def test_all_actions_have_required_fields(self):
        timeline = [_event("panel_uploaded", -5)]
        actions = score_actions(PatientState.DATA_INCOMPLETE, "p1", PARTIAL_GAPS, None, None, timeline)
        for a in actions:
            d = a.to_dict()
            assert "type" in d
            assert "score" in d
            assert "label" in d
            assert "reason" in d
            assert "urgency" in d
            assert "cta_url" in d
            assert "cta_label" in d

    def test_scores_in_range(self):
        timeline = [_event("panel_uploaded", -5)]
        actions = score_actions(
            PatientState.DATA_INCOMPLETE, "p1", PARTIAL_GAPS, None, ESCALATION_RESULT, timeline
        )
        for a in actions:
            assert 0.0 <= a.score <= 1.0

    def test_order_pending_returns_upload_results(self):
        timeline = [_event("panel_uploaded", -10), _event("test_order_generated", -5)]
        actions = score_actions(PatientState.ORDER_PENDING, "p1", PARTIAL_GAPS, None, None, timeline)
        assert actions[0].type == ActionType.UPLOAD_RESULTS


class TestScoringBreakdown:
    def test_breakdown_has_all_components(self):
        breakdown = get_scoring_breakdown(PARTIAL_GAPS, None, None, [])
        assert "data_urgency" in breakdown
        assert "phenoage_urgency" in breakdown
        assert "escalation_severity" in breakdown
        assert "time_decay" in breakdown
        assert "hallmark_signal" in breakdown
        assert "weights" in breakdown

    def test_breakdown_values_in_range(self):
        breakdown = get_scoring_breakdown(PARTIAL_GAPS, None, ESCALATION_RESULT, [_event("panel_uploaded", -30)])
        for k, v in breakdown.items():
            if k != "weights":
                assert 0.0 <= v <= 1.0, f"{k} = {v} out of range"
