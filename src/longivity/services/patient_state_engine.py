"""
PatientStateEngine — deterministic state machine for patient clinical journey.

Every patient is always in exactly one PatientState. The state is computed
from the patient's event timeline + current gap analysis + assessment result.
The state machine gates which actions are valid; ActionScorer ranks them.

States (in order of clinical progression):
  NEW → DATA_INCOMPLETE → ASSESSMENT_PENDING → ORDER_PENDING
  → COMPOUND_CANDIDATE → MONITORING

Transitions are deterministic — no LLM, no randomness.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class PatientState(str, Enum):
    NEW = "NEW"
    DATA_INCOMPLETE = "DATA_INCOMPLETE"
    ASSESSMENT_PENDING = "ASSESSMENT_PENDING"
    ORDER_PENDING = "ORDER_PENDING"
    COMPOUND_CANDIDATE = "COMPOUND_CANDIDATE"
    MONITORING = "MONITORING"


# ── Event helpers ─────────────────────────────────────────────────────────────

PANEL_EVENT_TYPES = frozenset({"panel_uploaded", "panel_created_manual"})


def _last_event(timeline: list[dict], event_types: str | frozenset | set) -> Optional[dict]:
    """Return the most recent event matching one or more event_types."""
    if isinstance(event_types, str):
        event_types = frozenset({event_types})
    else:
        event_types = frozenset(event_types)
    for event in sorted(timeline, key=lambda e: e.get("event_at", ""), reverse=True):
        if event.get("event_type") in event_types:
            return event
    return None


def _event_at(event: Optional[dict]) -> Optional[str]:
    """Return event_at string or None."""
    return event.get("event_at") if event else None


def _is_after(a: Optional[str], b: Optional[str]) -> bool:
    """Return True if timestamp string a is strictly after b. None is treated as epoch."""
    if a is None:
        return False
    if b is None:
        return True
    return a > b  # ISO strings compare correctly lexicographically


# ── State machine ─────────────────────────────────────────────────────────────

def compute_patient_state(
    timeline: list[dict],
    gaps: dict,
    assessment: Optional[dict] = None,
) -> PatientState:
    """
    Compute the current PatientState from the patient's event timeline,
    gap analysis result, and latest assessment result.

    Args:
        timeline: List of PatientEvent dicts (any order — function sorts internally).
                  Each dict has keys: event_type, event_at, payload, source.
        gaps: Output of detect_gaps() — must have keys:
              coverage_pct (float), missing_tier1 (list), escalation_triggered (list, optional).
        assessment: Output of run_longevity_assessment_level0() or None if never run.
                    Used to check hallmarks_activated.

    Returns:
        PatientState enum value.
    """
    # ── State: NEW ────────────────────────────────────────────────────────────
    has_any_panel = any(e.get("event_type") in PANEL_EVENT_TYPES for e in timeline)
    if not has_any_panel:
        return PatientState.NEW

    # ── State: DATA_INCOMPLETE or ORDER_PENDING ───────────────────────────────
    tier1_coverage = float(gaps.get("coverage_pct", 0.0))
    # escalation_triggered may come from the escalation engine result
    escalation_triggered = gaps.get("escalation_triggered", [])
    n_escalation = len(escalation_triggered) if escalation_triggered else 0

    data_is_incomplete = tier1_coverage < 80.0 or n_escalation > 0

    if data_is_incomplete:
        # Check if there's a pending (generated but not yet approved) test order
        last_order_gen = _last_event(timeline, "test_order_generated")
        last_order_approved = _last_event(timeline, "test_order_approved")

        order_is_pending = (
            last_order_gen is not None
            and not _is_after(_event_at(last_order_approved), _event_at(last_order_gen))
        )
        if order_is_pending:
            return PatientState.ORDER_PENDING
        return PatientState.DATA_INCOMPLETE

    # ── State: ASSESSMENT_PENDING ─────────────────────────────────────────────
    # Data is complete enough — check if assessment is fresh (run after latest panel)
    last_panel = _last_event(timeline, PANEL_EVENT_TYPES)
    last_assessment_event = _last_event(timeline, "assessment_run")

    assessment_is_stale = not _is_after(
        _event_at(last_assessment_event), _event_at(last_panel)
    )
    if assessment_is_stale:
        return PatientState.ASSESSMENT_PENDING

    # ── State: COMPOUND_CANDIDATE ─────────────────────────────────────────────
    # Assessment is current — check if hallmarks are active and no compound started
    hallmarks_activated: list[str] = []
    if assessment:
        # From run_longevity_assessment_level0 output
        hallmark_narrative = assessment.get("hallmark_narrative", {})
        hallmarks_activated = [
            h for h, v in hallmark_narrative.items()
            if isinstance(v, dict) and v.get("status") in ("PRIMARY_DRIVER", "SECONDARY_DRIVER")
        ]
        # Also check the simpler hallmark_result key (from assessment router)
        if not hallmarks_activated:
            hr = assessment.get("hallmark_result", {})
            hallmarks_activated = hr.get("hallmarks_activated", [])

    if hallmarks_activated:
        last_compound_started = _last_event(timeline, "compound_started")
        last_compound_stopped = _last_event(timeline, "compound_stopped")

        # No compound ever started, OR last compound was stopped
        no_active_compound = last_compound_started is None or _is_after(
            _event_at(last_compound_stopped), _event_at(last_compound_started)
        )
        if no_active_compound:
            return PatientState.COMPOUND_CANDIDATE

    # ── State: MONITORING ─────────────────────────────────────────────────────
    return PatientState.MONITORING


def state_label(state: PatientState) -> str:
    """Human-readable label for each state."""
    return {
        PatientState.NEW: "New Patient",
        PatientState.DATA_INCOMPLETE: "Data Incomplete",
        PatientState.ASSESSMENT_PENDING: "Assessment Pending",
        PatientState.ORDER_PENDING: "Order Pending",
        PatientState.COMPOUND_CANDIDATE: "Compound Candidate",
        PatientState.MONITORING: "Monitoring",
    }[state]


def state_color(state: PatientState) -> str:
    """Tailwind color class for each state (for frontend badge rendering)."""
    return {
        PatientState.NEW: "gray",
        PatientState.DATA_INCOMPLETE: "red",
        PatientState.ASSESSMENT_PENDING: "yellow",
        PatientState.ORDER_PENDING: "orange",
        PatientState.COMPOUND_CANDIDATE: "blue",
        PatientState.MONITORING: "green",
    }[state]
