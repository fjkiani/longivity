"""
PatientIntelligenceService — conductor for unified patient intelligence.

Orchestrates all existing engines (PhenoAge, gap detection, escalation rules)
and feeds their outputs into the PatientStateEngine + ActionScorer to produce
a single IntelligenceResponse per patient.

Cache strategy:
  - Result stored in Patient.intelligence_cache (JSONB) + intelligence_computed_at
  - Cache is valid if no new BiomarkerPanel was created after intelligence_computed_at
  - Cache is invalidated by new panel uploads (checked via PatientEvent timeline)
  - force_refresh=True bypasses cache

No LLM. All logic is deterministic and auditable.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Patient, BiomarkerPanel, PanelValue, PatientEvent
from ..services.patient_state_engine import (
    PatientState, compute_patient_state, state_label, state_color,
    PANEL_EVENT_TYPES,
)
from ..services.action_scorer import score_actions, get_scoring_breakdown, DEFAULT_WEIGHTS
from ..services.patient_event_service import record_intelligence_computed

logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_float(v: Any) -> Optional[float]:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


async def _load_patient_panels_as_dicts(patient_id: str, db: AsyncSession) -> list[dict]:
    """Load all panels + values for a patient as plain dicts, newest first."""
    result = await db.execute(
        select(BiomarkerPanel)
        .where(BiomarkerPanel.patient_id == patient_id)
        .order_by(BiomarkerPanel.drawn_at.desc())
    )
    panels = result.scalars().all()

    panel_dicts = []
    for panel in panels:
        vals_result = await db.execute(
            select(PanelValue).where(PanelValue.panel_id == panel.id)
        )
        values = vals_result.scalars().all()
        panel_dicts.append({
            "id": panel.id,
            "drawn_at": panel.drawn_at.isoformat() if panel.drawn_at else None,
            "source": panel.source,
            "values": [
                {"marker_key": v.marker_key, "value": v.value, "unit": v.unit, "flag": v.flag}
                for v in values
            ],
        })
    return panel_dicts


async def _load_timeline(patient_id: str, db: AsyncSession) -> list[dict]:
    """Load all PatientEvents for a patient as plain dicts."""
    result = await db.execute(
        select(PatientEvent)
        .where(PatientEvent.patient_id == patient_id)
        .order_by(PatientEvent.event_at.desc())
    )
    events = result.scalars().all()
    return [
        {
            "event_type": e.event_type,
            "event_at": e.event_at.isoformat() if e.event_at else None,
            "payload": e.payload or {},
            "source": e.source,
        }
        for e in events
    ]


def _is_cache_valid(patient: Patient, timeline: list[dict]) -> bool:
    """
    Cache is valid if:
    1. intelligence_cache is not None, AND
    2. No panel event exists after intelligence_computed_at
    """
    if patient.intelligence_cache is None or patient.intelligence_computed_at is None:
        return False

    computed_at_str = patient.intelligence_computed_at.isoformat()

    for event in timeline:
        if event.get("event_type") in PANEL_EVENT_TYPES:
            event_at = event.get("event_at", "")
            if event_at > computed_at_str:
                return False  # new panel after last computation

    return True


# ── PhenoAge engine wrapper ───────────────────────────────────────────────────

def _run_phenoage(patient: Patient, panels: list[dict]) -> dict:
    """Call existing run_longevity_assessment_level0 — no changes to that service."""
    from ..services.longevity_phenoage_level0 import run_longevity_assessment_level0

    if not panels:
        return {}

    latest_panel = panels[0]
    biomarkers = {v["marker_key"]: v["value"] for v in latest_panel.get("values", [])}

    age: Optional[int] = None
    if patient.date_of_birth:
        try:
            from datetime import date
            dob = date.fromisoformat(patient.date_of_birth)
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except Exception:
            pass

    try:
        return run_longevity_assessment_level0({
            "biomarkers": biomarkers,
            "age": age,
            "chronological_age": age,
        })
    except Exception as e:
        logger.warning(f"PhenoAge engine failed (non-fatal): {e}")
        return {}


# ── Gap engine wrapper ────────────────────────────────────────────────────────

def _run_gaps(patient: Patient, panels: list[dict]) -> dict:
    """Call existing detect_gaps — no changes to that service."""
    from ..services.test_ordering_agent import detect_gaps

    existing_keys = {v["marker_key"] for p in panels for v in p.get("values", [])}
    return detect_gaps(existing_keys, sex=patient.sex)


# ── Escalation engine wrapper ─────────────────────────────────────────────────

def _run_escalation(panels: list[dict], gap_result: dict) -> dict:
    """Call existing apply_escalation_rules — no changes to that service."""
    from ..services.test_ordering_agent import apply_escalation_rules

    if not panels:
        return {"triggered_rules": [], "recommended_panels": []}

    latest_values = {v["marker_key"]: v["value"] for v in panels[0].get("values", [])}
    existing_keys = {v["marker_key"] for p in panels for v in p.get("values", [])}

    try:
        result = apply_escalation_rules(latest_values, existing_keys)
        # Inject escalation_triggered into gap_result for state machine
        gap_result["escalation_triggered"] = result.get("triggered_rules", [])
        return result
    except Exception as e:
        logger.warning(f"Escalation engine failed (non-fatal): {e}")
        return {"triggered_rules": [], "recommended_panels": []}


# ── Response assembly ─────────────────────────────────────────────────────────

def _assemble_response(
    patient: Patient,
    current_state: PatientState,
    scored_actions: list,
    phenoage_result: dict,
    gap_result: dict,
    escalation_result: dict,
    timeline: list[dict],
    weights: dict,
) -> dict:
    """Assemble the full IntelligenceResponse dict."""
    now = _now()

    # Next action (top-scored)
    next_action = scored_actions[0].to_dict() if scored_actions else {
        "type": "schedule_followup",
        "score": 0.0,
        "label": "No action required",
        "reason": "Patient is up to date.",
        "urgency": "low",
        "cta_url": f"/patients/{patient.id}",
        "cta_label": "View Patient",
    }

    # Urgency score = top action score
    urgency_score = float(next_action.get("score", 0.0))

    # Biological summary
    pa = phenoage_result.get("phenoage_result") or phenoage_result.get("phenoage_analysis") or {}
    phenoage_estimate = _safe_float(pa.get("phenoage_estimate"))
    age_acceleration = _safe_float(pa.get("age_acceleration"))
    accel_tier = pa.get("accel_tier") or pa.get("completeness_mode", "PARTIAL")

    hallmark_narrative = phenoage_result.get("hallmark_narrative", {})
    hallmarks_activated = [
        h for h, v in hallmark_narrative.items()
        if isinstance(v, dict) and v.get("status") in ("PRIMARY_DRIVER", "SECONDARY_DRIVER")
    ]

    top_accelerators = pa.get("top_accelerators") or []
    top_accelerator = top_accelerators[0].get("canonical_key") if top_accelerators else None

    # Top compound
    compound_recs = phenoage_result.get("compound_recommendations", [])
    top_compound = None
    if compound_recs:
        c = compound_recs[0]
        top_compound = {
            "compound_id": c.get("compound"),
            "display_name": c.get("display_name"),
            "relevance_score": _safe_float(c.get("overall_relevance")),
            "hallmark": c.get("primary_match"),
            "evidence_tier": c.get("evidence_tier"),
        }

    # Timeline summary
    panel_events = [e for e in timeline if e.get("event_type") in PANEL_EVENT_TYPES]
    assessment_events = [e for e in timeline if e.get("event_type") == "assessment_run"]
    order_events = [e for e in timeline if e.get("event_type") == "test_order_approved"]

    first_panel_date = None
    latest_panel_date = None
    if panel_events:
        sorted_panels = sorted(panel_events, key=lambda e: e.get("event_at", ""))
        first_panel_date = sorted_panels[0].get("event_at", "")[:10]
        latest_panel_date = sorted_panels[-1].get("event_at", "")[:10]

    last_assessment_date = None
    if assessment_events:
        last_assessment_date = sorted(assessment_events, key=lambda e: e.get("event_at", ""), reverse=True)[0].get("event_at", "")[:10]

    last_order_date = None
    if order_events:
        last_order_date = sorted(order_events, key=lambda e: e.get("event_at", ""), reverse=True)[0].get("event_at", "")[:10]

    # Days since last action
    days_since_last_action = 0
    if timeline:
        last_event = sorted(timeline, key=lambda e: e.get("event_at", ""), reverse=True)[0]
        try:
            last_at = datetime.fromisoformat(last_event["event_at"].replace("Z", "+00:00"))
            days_since_last_action = (now - last_at).days
        except Exception:
            pass

    # Scoring breakdown
    scoring_breakdown = get_scoring_breakdown(gap_result, phenoage_result, escalation_result, timeline, weights)

    age = None
    if patient.date_of_birth:
        try:
            from datetime import date
            dob = date.fromisoformat(patient.date_of_birth)
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except Exception:
            pass

    return {
        "patient_id": patient.id,
        "patient_name": f"{patient.first_name} {patient.last_name}",
        "computed_at": now.isoformat(),
        "cache_hit": False,  # caller sets this to True when returning from cache
        "current_state": current_state.value,
        "current_state_label": state_label(current_state),
        "current_state_color": state_color(current_state),
        "urgency_score": round(urgency_score, 4),
        "next_action": next_action,
        "available_actions": [a.to_dict() for a in scored_actions],
        "biological_summary": {
            "phenoage_estimate": round(phenoage_estimate, 2) if phenoage_estimate is not None else None,
            "chronological_age": age,
            "age_acceleration": round(age_acceleration, 2) if age_acceleration is not None else None,
            "accel_tier": accel_tier,
            "hallmarks_activated": hallmarks_activated,
            "top_accelerator": top_accelerator,
            "data_completeness_pct": float(gap_result.get("coverage_pct", 0.0)),
        },
        "gap_summary": {
            "tier1_coverage_pct": float(gap_result.get("coverage_pct", 0.0)),
            "missing_tier1_count": len(gap_result.get("missing_tier1", [])),
            "missing_panels": gap_result.get("missing_panels_tier1", []),
            "escalation_rules_firing": len(escalation_result.get("triggered_rules", [])),
        },
        "top_compound": top_compound,
        "timeline_summary": {
            "first_panel_date": first_panel_date,
            "latest_panel_date": latest_panel_date,
            "panel_count": len(panel_events),
            "last_assessment_date": last_assessment_date,
            "last_order_date": last_order_date,
            "days_since_last_action": days_since_last_action,
        },
        "scoring_breakdown": scoring_breakdown,
    }


# ── Main service ──────────────────────────────────────────────────────────────

async def compute_patient_intelligence(
    patient: Patient,
    db: AsyncSession,
    force_refresh: bool = False,
    weights: dict = DEFAULT_WEIGHTS,
) -> dict:
    """
    Compute (or return cached) intelligence for a single patient.

    Args:
        patient: Patient ORM object (already loaded).
        db: Async DB session.
        force_refresh: If True, bypass cache and recompute.
        weights: Scoring weights (default: DEFAULT_WEIGHTS).

    Returns:
        IntelligenceResponse dict.
    """
    # 1. Load timeline
    timeline = await _load_timeline(patient.id, db)

    # 2. Check cache
    if not force_refresh and _is_cache_valid(patient, timeline):
        cached = dict(patient.intelligence_cache)
        cached["cache_hit"] = True
        return cached

    # 3. Load panels
    panels = await _load_patient_panels_as_dicts(patient.id, db)

    # 4. Run engines (gap + escalation are fast; phenoage is pure Python)
    gap_result = _run_gaps(patient, panels)
    escalation_result = _run_escalation(panels, gap_result)  # also injects escalation_triggered into gap_result
    phenoage_result = _run_phenoage(patient, panels)

    # 5. Compute state
    current_state = compute_patient_state(timeline, gap_result, phenoage_result)

    # 6. Score actions
    scored_actions = score_actions(
        state=current_state,
        patient_id=patient.id,
        gaps=gap_result,
        assessment=phenoage_result,
        escalation=escalation_result,
        timeline=timeline,
        weights=weights,
    )

    # 7. Assemble response
    response = _assemble_response(
        patient, current_state, scored_actions,
        phenoage_result, gap_result, escalation_result, timeline, weights,
    )

    # 8. Write cache to Patient row
    try:
        patient.intelligence_cache = response
        patient.intelligence_computed_at = _now()
        patient.current_state = current_state.value
        patient.urgency_score = response["urgency_score"]
        await db.flush()
    except Exception as e:
        logger.warning(f"Failed to write intelligence cache for patient {patient.id}: {e}")

    # 9. Append intelligence_computed event
    try:
        next_action = response.get("next_action", {})
        await record_intelligence_computed(
            db=db,
            patient_id=patient.id,
            clinic_id=patient.clinic_id,
            current_state=current_state.value,
            urgency_score=response["urgency_score"],
            next_action_label=next_action.get("label", ""),
            next_action_type=next_action.get("type", ""),
        )
        await db.flush()
    except Exception as e:
        logger.warning(f"Failed to write intelligence_computed event for patient {patient.id}: {e}")

    return response
