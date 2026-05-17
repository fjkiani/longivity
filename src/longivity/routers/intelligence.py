"""
Intelligence router — unified patient intelligence endpoints.

GET  /api/v1/patients/{patient_id}/intelligence   — individual patient
GET  /api/v1/clinic/intelligence                  — batch (all patients in clinic)
POST /api/v1/internal/patients/{patient_id}/recompute-intelligence  — background trigger
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from sqlalchemy import select

from ..core.deps import CurrentUser, DB
from ..db.models import Patient
from ..services.patient_intelligence_service import compute_patient_intelligence

logger = logging.getLogger(__name__)

router = APIRouter(tags=["intelligence"])


# ── Helpers ───────────────────────────────────────────────────────────────────

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


async def _background_recompute(patient_id: str, clinic_id: str) -> None:
    """Background task: recompute intelligence for a patient after a new panel."""
    from ..db.database import AsyncSessionLocal
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Patient).where(
                    Patient.id == patient_id,
                    Patient.clinic_id == clinic_id,
                    Patient.is_active == True,
                )
            )
            patient = result.scalar_one_or_none()
            if patient:
                await compute_patient_intelligence(patient, db, force_refresh=True)
                await db.commit()
                logger.info(f"Background intelligence recomputed for patient {patient_id}")
    except Exception as e:
        logger.warning(f"Background recompute failed for patient {patient_id}: {e}")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/api/v1/patients/{patient_id}/intelligence", response_model=dict)
async def get_patient_intelligence(
    patient_id: str,
    user: CurrentUser,
    db: DB,
    force_refresh: bool = Query(False, description="Bypass cache and recompute fresh"),
    include_full_assessment: bool = Query(False, description="Include full PhenoAge component breakdown"),
):
    """
    Return unified intelligence for a single patient.

    Combines PhenoAge, hallmark scoring, gap detection, escalation rules,
    patient state machine, and action scoring into one response.

    Cache: result is cached in Patient.intelligence_cache and returned
    immediately on subsequent calls unless a new panel was uploaded or
    force_refresh=True.

    The response includes:
    - current_state: where the patient is in their clinical journey
    - next_action: the single highest-priority recommended action
    - available_actions: all valid actions ranked by urgency score
    - biological_summary: PhenoAge, hallmarks, data completeness
    - gap_summary: missing markers and escalation rules firing
    - top_compound: highest-relevance compound recommendation
    - timeline_summary: key dates and days since last action
    - scoring_breakdown: raw component scores for transparency
    """
    patient = await _get_patient_or_404(patient_id, user, db)
    response = await compute_patient_intelligence(patient, db, force_refresh=force_refresh)
    await db.commit()

    if not include_full_assessment:
        # Strip heavy fields for default response
        response.pop("full_assessment", None)

    return response


@router.get("/api/v1/clinic/intelligence", response_model=dict)
async def get_clinic_intelligence(
    user: CurrentUser,
    db: DB,
    state: Optional[str] = Query(None, description="Filter by patient state (e.g. DATA_INCOMPLETE)"),
    min_urgency: float = Query(0.0, ge=0.0, le=1.0, description="Minimum urgency score"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    """
    Return cached intelligence for all active patients in the clinic.

    Sorted by urgency_score descending (highest urgency first).
    Reads from cache only — never triggers recomputation.
    Patients with no cached intelligence show current_state=NEW, urgency_score=0.

    Use this endpoint to power the clinic worklist and grid views.
    """
    # Load all active patients for this clinic
    result = await db.execute(
        select(Patient).where(
            Patient.clinic_id == user.clinic_id,
            Patient.is_active == True,
        ).order_by(Patient.urgency_score.desc().nullslast(), Patient.last_name)
    )
    patients = result.scalars().all()

    # Build summary cards from cached intelligence
    cards = []
    for patient in patients:
        if patient.intelligence_cache:
            cache = patient.intelligence_cache
            card = {
                "patient_id": patient.id,
                "patient_name": f"{patient.first_name} {patient.last_name}",
                "mrn": patient.mrn,
                "age": None,
                "sex": patient.sex,
                "current_state": cache.get("current_state", "NEW"),
                "current_state_label": cache.get("current_state_label", "New Patient"),
                "current_state_color": cache.get("current_state_color", "gray"),
                "urgency_score": cache.get("urgency_score", 0.0),
                "next_action": cache.get("next_action"),
                "biological_summary": cache.get("biological_summary"),
                "gap_summary": cache.get("gap_summary"),
                "top_compound": cache.get("top_compound"),
                "timeline_summary": cache.get("timeline_summary"),
                "intelligence_computed_at": patient.intelligence_computed_at.isoformat() if patient.intelligence_computed_at else None,
            }
        else:
            # No cache — patient is NEW or never computed
            card = {
                "patient_id": patient.id,
                "patient_name": f"{patient.first_name} {patient.last_name}",
                "mrn": patient.mrn,
                "age": None,
                "sex": patient.sex,
                "current_state": "NEW",
                "current_state_label": "New Patient",
                "current_state_color": "gray",
                "urgency_score": 0.0,
                "next_action": {
                    "type": "order_baseline_panel",
                    "label": "Upload First Lab Panel",
                    "reason": "No biomarker data yet.",
                    "urgency": "high",
                    "cta_url": f"/patients/{patient.id}/upload",
                    "cta_label": "Upload Labs",
                },
                "biological_summary": None,
                "gap_summary": None,
                "top_compound": None,
                "timeline_summary": None,
                "intelligence_computed_at": None,
            }

        # Compute age
        if patient.date_of_birth:
            try:
                from datetime import date
                dob = date.fromisoformat(patient.date_of_birth)
                today = date.today()
                card["age"] = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            except Exception:
                pass

        cards.append(card)

    # Apply filters
    if state:
        cards = [c for c in cards if c["current_state"] == state.upper()]
    if min_urgency > 0:
        cards = [c for c in cards if c["urgency_score"] >= min_urgency]

    total = len(cards)
    cards = cards[offset: offset + limit]

    # State distribution for dashboard stats
    all_states = [c["current_state"] for c in cards]
    state_counts: dict[str, int] = {}
    for s in all_states:
        state_counts[s] = state_counts.get(s, 0) + 1

    return {
        "clinic_id": user.clinic_id,
        "total_patients": total,
        "offset": offset,
        "limit": limit,
        "state_distribution": state_counts,
        "patients": cards,
    }


@router.post(
    "/api/v1/internal/patients/{patient_id}/recompute-intelligence",
    status_code=202,
    include_in_schema=False,  # internal endpoint — not in OpenAPI docs
)
async def trigger_recompute(
    patient_id: str,
    user: CurrentUser,
    db: DB,
    background_tasks: BackgroundTasks,
):
    """
    Internal endpoint: trigger background recomputation of patient intelligence.
    Called by upload and panels routers after a new panel is created.
    Returns 202 immediately; computation happens in background.
    """
    patient = await _get_patient_or_404(patient_id, user, db)
    background_tasks.add_task(_background_recompute, patient.id, patient.clinic_id)
    return {"status": "accepted", "patient_id": patient_id, "message": "Recomputation queued"}
