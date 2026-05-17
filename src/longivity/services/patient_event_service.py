"""
PatientEventService — helpers for writing PatientEvent records.

Import and call these from any router that needs to record a clinical event.
All functions are async and accept an open DB session.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import PatientEvent


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def record_event(
    db: AsyncSession,
    patient_id: str,
    clinic_id: str,
    event_type: str,
    payload: Optional[dict] = None,
    actor_id: Optional[str] = None,
    source: str = "system",
) -> PatientEvent:
    """
    Write a PatientEvent to the database.
    Call this from any router after a significant clinical action.
    """
    event = PatientEvent(
        patient_id=patient_id,
        clinic_id=clinic_id,
        event_type=event_type,
        event_at=_now(),
        source=source,
        actor_id=actor_id,
        payload=payload or {},
    )
    db.add(event)
    # Note: caller is responsible for db.commit() or db.flush()
    return event


# ── Convenience wrappers for each event type ─────────────────────────────────

async def record_panel_uploaded(
    db: AsyncSession,
    patient_id: str,
    clinic_id: str,
    panel_id: str,
    source: str,
    marker_count: int,
    drawn_at: str,
    actor_id: Optional[str] = None,
) -> PatientEvent:
    return await record_event(
        db, patient_id, clinic_id,
        event_type="panel_uploaded",
        payload={
            "panel_id": panel_id,
            "source": source,
            "marker_count": marker_count,
            "drawn_at": drawn_at,
        },
        actor_id=actor_id,
        source="clinician" if actor_id else "system",
    )


async def record_panel_created_manual(
    db: AsyncSession,
    patient_id: str,
    clinic_id: str,
    panel_id: str,
    marker_count: int,
    actor_id: Optional[str] = None,
) -> PatientEvent:
    return await record_event(
        db, patient_id, clinic_id,
        event_type="panel_created_manual",
        payload={"panel_id": panel_id, "marker_count": marker_count},
        actor_id=actor_id,
        source="clinician",
    )


async def record_assessment_run(
    db: AsyncSession,
    patient_id: str,
    clinic_id: str,
    panel_id: str,
    phenoage_estimate: Optional[float],
    age_acceleration: Optional[float],
    hallmarks_activated: list[str],
    actor_id: Optional[str] = None,
) -> PatientEvent:
    return await record_event(
        db, patient_id, clinic_id,
        event_type="assessment_run",
        payload={
            "panel_id": panel_id,
            "phenoage_estimate": round(phenoage_estimate, 2) if phenoage_estimate is not None else None,
            "age_acceleration": round(age_acceleration, 2) if age_acceleration is not None else None,
            "hallmarks_activated": hallmarks_activated,
        },
        actor_id=actor_id,
        source="clinician" if actor_id else "system",
    )


async def record_test_order_generated(
    db: AsyncSession,
    patient_id: str,
    clinic_id: str,
    order_id: str,
    panels_recommended: int,
    total_cost: float,
    actor_id: Optional[str] = None,
) -> PatientEvent:
    return await record_event(
        db, patient_id, clinic_id,
        event_type="test_order_generated",
        payload={
            "order_id": order_id,
            "panels_recommended": panels_recommended,
            "total_cost": total_cost,
        },
        actor_id=actor_id,
        source="agent",
    )


async def record_test_order_approved(
    db: AsyncSession,
    patient_id: str,
    clinic_id: str,
    order_id: str,
    panels_approved: int,
    actor_id: Optional[str] = None,
) -> PatientEvent:
    return await record_event(
        db, patient_id, clinic_id,
        event_type="test_order_approved",
        payload={
            "order_id": order_id,
            "panels_approved": panels_approved,
        },
        actor_id=actor_id,
        source="clinician",
    )


async def record_intelligence_computed(
    db: AsyncSession,
    patient_id: str,
    clinic_id: str,
    current_state: str,
    urgency_score: float,
    next_action_label: str,
    next_action_type: str,
) -> PatientEvent:
    return await record_event(
        db, patient_id, clinic_id,
        event_type="intelligence_computed",
        payload={
            "current_state": current_state,
            "urgency_score": round(urgency_score, 4),
            "next_action_label": next_action_label,
            "next_action_type": next_action_type,
        },
        source="system",
    )
