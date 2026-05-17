"""
ActionScorer — weighted scoring model for patient next actions.

The state machine (PatientStateEngine) gates WHICH actions are valid.
This module scores and ranks them by urgency.

Scoring formula:
  score = w1*data_urgency + w2*phenoage_urgency + w3*escalation_severity
        + w4*time_decay + w5*hallmark_signal

Default weights: w1=0.30, w2=0.25, w3=0.25, w4=0.10, w5=0.10
All components are clipped to [0.0, 1.0].
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from .patient_state_engine import PatientState


class ActionType(str, Enum):
    ORDER_BASELINE_PANEL   = "order_baseline_panel"
    ORDER_ESCALATION_PANEL = "order_escalation_panel"
    RUN_ASSESSMENT         = "run_assessment"
    REVIEW_ASSESSMENT      = "review_assessment"
    START_COMPOUND         = "start_compound"
    SCHEDULE_FOLLOWUP      = "schedule_followup"
    UPLOAD_RESULTS         = "upload_results"


class ActionUrgency(str, Enum):
    URGENT  = "urgent"
    HIGH    = "high"
    ROUTINE = "routine"
    LOW     = "low"


@dataclass
class ScoredAction:
    type: ActionType
    score: float          # 0.0–1.0
    label: str
    reason: str
    urgency: ActionUrgency
    cta_url: str          # relative URL for the frontend CTA button
    cta_label: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "score": round(self.score, 4),
            "label": self.label,
            "reason": self.reason,
            "urgency": self.urgency.value,
            "cta_url": self.cta_url,
            "cta_label": self.cta_label,
            "metadata": self.metadata,
        }


# ── Default weights ───────────────────────────────────────────────────────────

DEFAULT_WEIGHTS = {
    "w1": 0.30,  # data completeness
    "w2": 0.25,  # phenoage urgency
    "w3": 0.25,  # escalation severity
    "w4": 0.10,  # time decay (staleness)
    "w5": 0.10,  # hallmark signal
}


# ── Component calculators ─────────────────────────────────────────────────────

def _clip(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _data_urgency(gaps: dict) -> float:
    """1 - coverage_pct/100. 1.0 = no data, 0.0 = fully covered."""
    coverage = float(gaps.get("coverage_pct", 0.0))
    return _clip(1.0 - coverage / 100.0)


def _phenoage_urgency(assessment: Optional[dict]) -> float:
    """clip(age_acceleration / 10, 0, 1). 1.0 = +10yr acceleration."""
    if not assessment:
        return 0.0
    pa = assessment.get("phenoage_result") or assessment.get("phenoage_analysis") or {}
    accel = pa.get("age_acceleration") or pa.get("phenoage_acceleration")
    if accel is None:
        return 0.0
    return _clip(float(accel) / 10.0)


def _escalation_severity(escalation: Optional[dict]) -> float:
    """Max severity score across all triggered escalation rules. 0 if none."""
    if not escalation:
        return 0.0
    rules = escalation.get("triggered_rules", [])
    if not rules:
        return 0.0
    # Severity mapping: urgent=1.0, high=0.75, routine=0.40
    severity_map = {"urgent": 1.0, "high": 0.75, "routine": 0.40, "low": 0.20}
    scores = [severity_map.get(str(r.get("severity", "routine")).lower(), 0.40) for r in rules]
    return _clip(max(scores))


def _time_decay(timeline: list[dict]) -> float:
    """clip(days_since_last_action / 180, 0, 1). 1.0 = 6+ months stale."""
    if not timeline:
        return 1.0  # no history = maximally stale
    # Find most recent event of any type
    sorted_events = sorted(timeline, key=lambda e: e.get("event_at", ""), reverse=True)
    last_event = sorted_events[0] if sorted_events else None
    if not last_event:
        return 1.0
    last_at_str = last_event.get("event_at", "")
    try:
        last_at = datetime.fromisoformat(last_at_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days = (now - last_at).days
        return _clip(days / 180.0)
    except Exception:
        return 0.5


def _hallmark_signal(assessment: Optional[dict]) -> float:
    """Max hallmark score across all active hallmarks. 0 if no assessment."""
    if not assessment:
        return 0.0
    # From run_longevity_assessment_level0 output
    hallmark_narrative = assessment.get("hallmark_narrative", {})
    if hallmark_narrative:
        scores = []
        for h, v in hallmark_narrative.items():
            if not isinstance(v, dict):
                continue
            ps = float(v.get("phenoage_signal", 0.0))
            ss = float(v.get("supplementary_signal", 0.0))
            scores.append(max(ps, ss))
        if scores:
            return _clip(max(scores))
    # Fallback: hallmark_scores from simpler assessment format
    hr = assessment.get("hallmark_result", {})
    scores_dict = hr.get("hallmark_scores", {})
    if scores_dict:
        return _clip(max(float(v) for v in scores_dict.values()))
    return 0.0


def _compute_score(
    data_urgency: float,
    phenoage_urgency: float,
    escalation_severity: float,
    time_decay: float,
    hallmark_signal: float,
    weights: dict = DEFAULT_WEIGHTS,
) -> float:
    return _clip(
        weights["w1"] * data_urgency
        + weights["w2"] * phenoage_urgency
        + weights["w3"] * escalation_severity
        + weights["w4"] * time_decay
        + weights["w5"] * hallmark_signal
    )


def _urgency_from_score(score: float) -> ActionUrgency:
    if score >= 0.75:
        return ActionUrgency.URGENT
    if score >= 0.50:
        return ActionUrgency.HIGH
    if score >= 0.25:
        return ActionUrgency.ROUTINE
    return ActionUrgency.LOW


# ── Main scoring function ─────────────────────────────────────────────────────

def score_actions(
    state: PatientState,
    patient_id: str,
    gaps: dict,
    assessment: Optional[dict],
    escalation: Optional[dict],
    timeline: list[dict],
    weights: dict = DEFAULT_WEIGHTS,
) -> list[ScoredAction]:
    """
    Score all valid actions for a patient in the given state.

    Args:
        state: Current PatientState (from PatientStateEngine).
        patient_id: Used to build CTA URLs.
        gaps: Output of detect_gaps().
        assessment: Output of run_longevity_assessment_level0() or None.
        escalation: Output of apply_escalation_rules() or None.
        timeline: List of PatientEvent dicts.
        weights: Scoring weights dict (default: DEFAULT_WEIGHTS).

    Returns:
        List of ScoredAction, sorted by score descending.
        The first item is the recommended next action.
    """
    # Pre-compute components (shared across all actions)
    du = _data_urgency(gaps)
    pu = _phenoage_urgency(assessment)
    es = _escalation_severity(escalation)
    td = _time_decay(timeline)
    hs = _hallmark_signal(assessment)

    base_url = f"/patients/{patient_id}"
    actions: list[ScoredAction] = []

    # ── NEW: only action is to upload data ───────────────────────────────────
    if state == PatientState.NEW:
        actions.append(ScoredAction(
            type=ActionType.ORDER_BASELINE_PANEL,
            score=1.0,
            label="Upload First Lab Panel",
            reason="No biomarker data yet. Upload a lab report to begin.",
            urgency=ActionUrgency.HIGH,
            cta_url=f"{base_url}/upload",
            cta_label="Upload Labs",
        ))
        return actions

    # ── DATA_INCOMPLETE: order tests ─────────────────────────────────────────
    if state == PatientState.DATA_INCOMPLETE:
        missing_count = len(gaps.get("missing_tier1", []))
        coverage = float(gaps.get("coverage_pct", 0.0))
        n_escalation = len((escalation or {}).get("triggered_rules", []))

        if n_escalation > 0:
            # Escalation rules firing — highest priority
            top_rule = (escalation or {}).get("triggered_rules", [{}])[0]
            trigger = top_rule.get("trigger_marker", "marker")
            value = top_rule.get("trigger_value", "")
            score = _compute_score(du, pu, es, td, hs, weights)
            actions.append(ScoredAction(
                type=ActionType.ORDER_ESCALATION_PANEL,
                score=score,
                label="Order Escalation Panel",
                reason=f"{trigger}={value} triggers escalation rule. {n_escalation} rule(s) firing.",
                urgency=_urgency_from_score(score),
                cta_url=f"{base_url}/test-orders",
                cta_label="Generate Order",
                metadata={"escalation_rules": n_escalation, "top_trigger": trigger},
            ))

        if coverage < 80.0:
            # Baseline gap
            score = _compute_score(du, pu, 0.0, td, hs, weights)  # no escalation component
            missing_panels = gaps.get("missing_panels_tier1", [])
            panel_str = ", ".join(missing_panels[:3])
            if len(missing_panels) > 3:
                panel_str += f" +{len(missing_panels) - 3} more"
            actions.append(ScoredAction(
                type=ActionType.ORDER_BASELINE_PANEL,
                score=score,
                label="Complete Baseline Panel",
                reason=f"{coverage:.0f}% tier-1 coverage — {missing_count} baseline markers missing. Panels: {panel_str}.",
                urgency=_urgency_from_score(score),
                cta_url=f"{base_url}/test-orders",
                cta_label="Generate Order",
                metadata={"coverage_pct": coverage, "missing_count": missing_count},
            ))

    # ── ORDER_PENDING: waiting for approved order results ────────────────────
    elif state == PatientState.ORDER_PENDING:
        score = _compute_score(du, pu, es, td, hs, weights)
        actions.append(ScoredAction(
            type=ActionType.UPLOAD_RESULTS,
            score=score,
            label="Upload Lab Results",
            reason="Test order approved — awaiting results. Upload when received.",
            urgency=_urgency_from_score(score),
            cta_url=f"{base_url}/upload",
            cta_label="Upload Results",
        ))

    # ── ASSESSMENT_PENDING: data complete, run assessment ────────────────────
    elif state == PatientState.ASSESSMENT_PENDING:
        score = _compute_score(du, pu, es, td, hs, weights)
        actions.append(ScoredAction(
            type=ActionType.RUN_ASSESSMENT,
            score=score,
            label="Run PhenoAge Assessment",
            reason="Baseline data complete. Run assessment to compute biological age and hallmark scores.",
            urgency=_urgency_from_score(score),
            cta_url=f"{base_url}?tab=assessment",
            cta_label="Run Assessment",
        ))

    # ── COMPOUND_CANDIDATE: hallmarks active, suggest compound ───────────────
    elif state == PatientState.COMPOUND_CANDIDATE:
        # Find top compound from assessment
        compound_recs = []
        if assessment:
            compound_recs = assessment.get("compound_recommendations", [])
        top_compound = compound_recs[0] if compound_recs else None

        score = _compute_score(du, pu, es, td, hs, weights)

        if top_compound:
            compound_name = top_compound.get("display_name", top_compound.get("compound", "compound"))
            hallmark = top_compound.get("primary_match", "")
            evidence = top_compound.get("evidence_tier", "")
            label = f"Consider {compound_name}"
            reason = f"Hallmark '{hallmark}' active. {compound_name} has {evidence} evidence."
        else:
            label = "Review Compound Recommendations"
            reason = "Active hallmarks detected. Review compound recommendations."

        actions.append(ScoredAction(
            type=ActionType.START_COMPOUND,
            score=score,
            label=label,
            reason=reason,
            urgency=_urgency_from_score(score),
            cta_url=f"{base_url}?tab=assessment",
            cta_label="View Recommendations",
            metadata={"top_compound": top_compound.get("compound") if top_compound else None},
        ))

        # Also offer assessment review
        review_score = _compute_score(0.0, pu, 0.0, td, hs, weights)
        actions.append(ScoredAction(
            type=ActionType.REVIEW_ASSESSMENT,
            score=review_score,
            label="Review Full Assessment",
            reason="Review PhenoAge breakdown and hallmark narrative.",
            urgency=_urgency_from_score(review_score),
            cta_url=f"{base_url}?tab=assessment",
            cta_label="View Assessment",
        ))

    # ── MONITORING: steady state, time-based follow-up ───────────────────────
    elif state == PatientState.MONITORING:
        score = _compute_score(0.0, 0.0, 0.0, td, 0.0, weights)  # only time decay
        days = round(td * 180)
        actions.append(ScoredAction(
            type=ActionType.SCHEDULE_FOLLOWUP,
            score=score,
            label="Schedule Follow-up Panel",
            reason=f"Patient in monitoring. Last action {days}+ days ago. Consider scheduling next draw.",
            urgency=_urgency_from_score(score),
            cta_url=f"{base_url}/test-orders",
            cta_label="Plan Next Order",
        ))

        # If assessment is available, also offer review
        if assessment:
            review_score = _compute_score(0.0, pu, 0.0, 0.0, hs, weights)
            if review_score > 0.1:
                actions.append(ScoredAction(
                    type=ActionType.REVIEW_ASSESSMENT,
                    score=review_score,
                    label="Review Assessment",
                    reason="Review current biological age and hallmark status.",
                    urgency=_urgency_from_score(review_score),
                    cta_url=f"{base_url}?tab=assessment",
                    cta_label="View Assessment",
                ))

    # Sort by score descending
    actions.sort(key=lambda a: a.score, reverse=True)
    return actions


def get_scoring_breakdown(
    gaps: dict,
    assessment: Optional[dict],
    escalation: Optional[dict],
    timeline: list[dict],
    weights: dict = DEFAULT_WEIGHTS,
) -> dict:
    """Return the raw component scores for transparency/debugging."""
    return {
        "data_urgency": round(_data_urgency(gaps), 4),
        "phenoage_urgency": round(_phenoage_urgency(assessment), 4),
        "escalation_severity": round(_escalation_severity(escalation), 4),
        "time_decay": round(_time_decay(timeline), 4),
        "hallmark_signal": round(_hallmark_signal(assessment), 4),
        "weights": weights,
    }
