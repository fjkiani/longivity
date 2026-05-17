"""
Timeline router — patient event history.

GET /api/v1/patients/{patient_id}/timeline
"""
from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from ..core.deps import CurrentUser, DB
from ..db.models import Patient, PatientEvent, ClinicUser

router = APIRouter(prefix="/api/v1/patients", tags=["timeline"])


async def _get_patient_or_404(patient_id: str, user: Any, db: Any) -> Patient:
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == user.clinic_id,
            Patient.is_active == True,
        )
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def _event_summary(event: PatientEvent) -> str:
    """Generate a human-readable summary for each event type."""
    p = event.payload or {}
    t = event.event_type
    if t == "panel_uploaded":
        return f"{p.get('source', 'Lab')} — {p.get('marker_count', '?')} markers"
    if t == "panel_created_manual":
        return f"Manual entry — {p.get('marker_count', '?')} markers"
    if t == "assessment_run":
        pa = p.get('phenoage_estimate')
        accel = p.get('age_acceleration')
        if pa is not None:
            sign = '+' if (accel or 0) >= 0 else ''
            return f"PhenoAge {pa:.1f} yrs ({sign}{accel:.1f} acceleration)"
        return "Assessment run (partial panel)"
    if t == "test_order_generated":
        n = p.get('panels_recommended', 0)
        return f"{n} panels recommended — ${p.get('total_cost', '?')}"
    if t == "test_order_approved":
        n = p.get('panels_approved', 0)
        return f"{n} panels approved"
    if t == "test_order_sent":
        return f"Sent to {p.get('lab', 'lab')}"
    if t == "test_order_resulted":
        return "Results received"
    if t == "compound_started":
        return f"Started {p.get('compound_id', 'compound')} — {p.get('dose', '')}"
    if t == "compound_stopped":
        return f"Stopped {p.get('compound_id', 'compound')} — {p.get('reason', '')}"
    if t == "intelligence_computed":
        state = p.get('current_state', '?')
        score = p.get('urgency_score', 0)
        action = p.get('next_action_label', '')
        return f"State: {state} | urgency {score:.2f} | next: {action}"
    if t == "clinician_note":
        text = p.get('note_text', '')
        return text[:80] + ('...' if len(text) > 80 else '')
    return t.replace('_', ' ').title()


@router.get("/{patient_id}/timeline", response_model=dict)
async def get_patient_timeline(
    patient_id: str,
    user: CurrentUser,
    db: DB,
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    event_type: Optional[str] = Query(None, description="Filter by event_type"),
):
    """
    Return the full clinical event timeline for a patient, newest first.

    Each event records a significant action: panel upload, assessment run,
    test order generated/approved, compound started, intelligence computed.
    The PatientIntelligenceService reads this timeline to reason about
    what has already happened and what the next action should be.
    """
    await _get_patient_or_404(patient_id, user, db)

    query = (
        select(PatientEvent)
        .where(PatientEvent.patient_id == patient_id)
        .order_by(PatientEvent.event_at.desc())
    )
    if event_type:
        query = query.where(PatientEvent.event_type == event_type)

    total_result = await db.execute(
        select(PatientEvent).where(PatientEvent.patient_id == patient_id)
    )
    total = len(total_result.scalars().all())

    result = await db.execute(query.offset(offset).limit(limit))
    events = result.scalars().all()

    # Load actor names in one query
    actor_ids = [e.actor_id for e in events if e.actor_id]
    actor_names: dict[str, str] = {}
    if actor_ids:
        actors_result = await db.execute(
            select(ClinicUser).where(ClinicUser.id.in_(actor_ids))
        )
        for actor in actors_result.scalars().all():
            actor_names[actor.id] = actor.full_name or actor.email

    return {
        "patient_id": patient_id,
        "total": total,
        "offset": offset,
        "limit": limit,
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "event_at": e.event_at.isoformat(),
                "source": e.source,
                "actor_name": actor_names.get(e.actor_id) if e.actor_id else None,
                "summary": _event_summary(e),
                "payload": e.payload,
            }
            for e in events
        ],
    }
