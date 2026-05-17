"""Biomarker panel router — store and retrieve blood draw panels."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..core.deps import CurrentUser, DB
from ..db.models import BiomarkerPanel, Patient, PanelValue
from ..services.patient_event_service import record_panel_created_manual

router = APIRouter(prefix="/api/v1/patients", tags=["panels"])


async def _trigger_recompute_bg(patient_id: str, clinic_id: str) -> None:
    """Fire-and-forget: recompute patient intelligence after new panel."""
    import logging
    logger = logging.getLogger(__name__)
    try:
        from ..db.database import AsyncSessionLocal
        from ..db.models import Patient
        from sqlalchemy import select
        from ..services.patient_intelligence_service import compute_patient_intelligence
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Patient).where(Patient.id == patient_id, Patient.clinic_id == clinic_id)
            )
            patient = result.scalar_one_or_none()
            if patient:
                await compute_patient_intelligence(patient, db, force_refresh=True)
                await db.commit()
    except Exception as e:
        logger.warning(f"Background recompute failed for patient {patient_id}: {e}")


# ── Schemas ──────────────────────────────────────────────────────────────────

class PanelValueInput(BaseModel):
    marker_key: str
    marker_display: str | None = None
    value: float
    unit: str | None = None
    ref_low: float | None = None
    ref_high: float | None = None
    flag: str | None = None


class PanelCreate(BaseModel):
    drawn_at: str  # ISO datetime string
    source: str = "manual"
    lab_name: str | None = None
    notes: str | None = None
    values: list[PanelValueInput]


def _panel_to_dict(panel: BiomarkerPanel) -> dict:
    return {
        "id": panel.id,
        "patient_id": panel.patient_id,
        "drawn_at": panel.drawn_at.isoformat(),
        "source": panel.source,
        "lab_name": panel.lab_name,
        "notes": panel.notes,
        "created_at": panel.created_at.isoformat(),
        "values": [
            {
                "marker_key": v.marker_key,
                "marker_display": v.marker_display,
                "value": v.value,
                "unit": v.unit,
                "ref_low": v.ref_low,
                "ref_high": v.ref_high,
                "flag": v.flag,
            }
            for v in (panel.values or [])
        ],
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/{patient_id}/panels", response_model=list[dict])
async def list_panels(patient_id: str, current_user: CurrentUser, db: DB):
    """Return all panels for a patient, ordered by draw date."""
    # Verify patient belongs to clinic
    p_result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == current_user.clinic_id,
        )
    )
    if not p_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Patient not found")

    result = await db.execute(
        select(BiomarkerPanel)
        .where(BiomarkerPanel.patient_id == patient_id)
        .options(selectinload(BiomarkerPanel.values))
        .order_by(BiomarkerPanel.drawn_at.desc())
    )
    panels = result.scalars().all()
    return [_panel_to_dict(p) for p in panels]


@router.post("/{patient_id}/panels", response_model=dict, status_code=201)
async def create_panel(patient_id: str, body: PanelCreate, current_user: CurrentUser, db: DB, background_tasks: BackgroundTasks):
    """Manually create a biomarker panel for a patient."""
    p_result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == current_user.clinic_id,
        )
    )
    if not p_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Patient not found")

    try:
        drawn_at = datetime.fromisoformat(body.drawn_at.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid drawn_at format: {body.drawn_at}")

    panel = BiomarkerPanel(
        patient_id=patient_id,
        drawn_at=drawn_at,
        source=body.source,
        lab_name=body.lab_name,
        notes=body.notes,
    )
    db.add(panel)
    await db.flush()

    for v in body.values:
        pv = PanelValue(panel_id=panel.id, **v.model_dump(exclude_none=True))
        db.add(pv)

    await db.flush()

    # Reload with values
    result = await db.execute(
        select(BiomarkerPanel)
        .where(BiomarkerPanel.id == panel.id)
        .options(selectinload(BiomarkerPanel.values))
    )
    panel = result.scalar_one()

    # Record clinical event
    await record_panel_created_manual(
        db=db,
        patient_id=patient_id,
        clinic_id=current_user.clinic_id,
        panel_id=panel.id,
        marker_count=len(body.values) if hasattr(body, 'values') else 0,
        actor_id=current_user.id,
    )
    await db.commit()

    # Trigger background intelligence recompute
    background_tasks.add_task(_trigger_recompute_bg, patient_id, current_user.clinic_id)

    return _panel_to_dict(panel)


@router.get("/{patient_id}/panels/{panel_id}", response_model=dict)
async def get_panel(patient_id: str, panel_id: str, current_user: CurrentUser, db: DB):
    p_result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == current_user.clinic_id,
        )
    )
    if not p_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Patient not found")

    result = await db.execute(
        select(BiomarkerPanel)
        .where(BiomarkerPanel.id == panel_id, BiomarkerPanel.patient_id == patient_id)
        .options(selectinload(BiomarkerPanel.values))
    )
    panel = result.scalar_one_or_none()
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")
    return _panel_to_dict(panel)


@router.delete("/{patient_id}/panels/{panel_id}", status_code=204)
async def delete_panel(patient_id: str, panel_id: str, current_user: CurrentUser, db: DB):
    p_result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == current_user.clinic_id,
        )
    )
    if not p_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Patient not found")

    result = await db.execute(
        select(BiomarkerPanel)
        .where(BiomarkerPanel.id == panel_id, BiomarkerPanel.patient_id == patient_id)
    )
    panel = result.scalar_one_or_none()
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")
    await db.delete(panel)
