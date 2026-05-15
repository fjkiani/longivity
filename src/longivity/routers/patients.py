"""Patient CRUD router."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ..core.deps import CurrentUser, DB
from ..db.models import Patient, BiomarkerPanel

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str | None = None  # YYYY-MM-DD
    sex: str | None = None  # male | female | other
    mrn: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str | None = None


class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: str | None = None
    sex: str | None = None
    mrn: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str | None = None


class PatientResponse(BaseModel):
    id: str
    clinic_id: str
    first_name: str
    last_name: str
    date_of_birth: str | None
    sex: str | None
    mrn: str | None
    email: str | None
    phone: str | None
    notes: str | None
    is_active: bool
    created_at: str
    panel_count: int = 0
    latest_panel_date: str | None = None
    age: int | None = None


def _calc_age(dob_str: str | None) -> int | None:
    if not dob_str:
        return None
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d")
        today = datetime.now()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        return None


def _patient_to_response(p: Patient, panel_count: int = 0, latest_panel_date: str | None = None) -> dict:
    return {
        "id": p.id,
        "clinic_id": p.clinic_id,
        "first_name": p.first_name,
        "last_name": p.last_name,
        "date_of_birth": p.date_of_birth,
        "sex": p.sex,
        "mrn": p.mrn,
        "email": p.email,
        "phone": p.phone,
        "notes": p.notes,
        "is_active": p.is_active,
        "created_at": p.created_at.isoformat(),
        "panel_count": panel_count,
        "latest_panel_date": latest_panel_date,
        "age": _calc_age(p.date_of_birth),
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=list[dict])
async def list_patients(current_user: CurrentUser, db: DB):
    """List all patients for the current clinic."""
    result = await db.execute(
        select(Patient)
        .where(Patient.clinic_id == current_user.clinic_id, Patient.is_active == True)
        .order_by(Patient.last_name, Patient.first_name)
    )
    patients = result.scalars().all()

    # Get panel counts in one query
    panel_counts_result = await db.execute(
        select(BiomarkerPanel.patient_id, func.count(BiomarkerPanel.id).label("cnt"))
        .where(BiomarkerPanel.patient_id.in_([p.id for p in patients]))
        .group_by(BiomarkerPanel.patient_id)
    )
    panel_counts = {row.patient_id: row.cnt for row in panel_counts_result}

    # Get latest panel dates
    latest_panels_result = await db.execute(
        select(BiomarkerPanel.patient_id, func.max(BiomarkerPanel.drawn_at).label("latest"))
        .where(BiomarkerPanel.patient_id.in_([p.id for p in patients]))
        .group_by(BiomarkerPanel.patient_id)
    )
    latest_panels = {row.patient_id: row.latest.isoformat() if row.latest else None
                     for row in latest_panels_result}

    return [
        _patient_to_response(p, panel_counts.get(p.id, 0), latest_panels.get(p.id))
        for p in patients
    ]


@router.post("", response_model=dict, status_code=201)
async def create_patient(body: PatientCreate, current_user: CurrentUser, db: DB):
    patient = Patient(
        clinic_id=current_user.clinic_id,
        **body.model_dump(exclude_none=True),
    )
    db.add(patient)
    await db.flush()
    return _patient_to_response(patient)


@router.get("/{patient_id}", response_model=dict)
async def get_patient(patient_id: str, current_user: CurrentUser, db: DB):
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == current_user.clinic_id,
        )
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Panel count + latest
    pc_result = await db.execute(
        select(func.count(BiomarkerPanel.id)).where(BiomarkerPanel.patient_id == patient_id)
    )
    panel_count = pc_result.scalar() or 0

    lp_result = await db.execute(
        select(func.max(BiomarkerPanel.drawn_at)).where(BiomarkerPanel.patient_id == patient_id)
    )
    latest = lp_result.scalar()
    return _patient_to_response(patient, panel_count, latest.isoformat() if latest else None)


@router.patch("/{patient_id}", response_model=dict)
async def update_patient(patient_id: str, body: PatientUpdate, current_user: CurrentUser, db: DB):
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == current_user.clinic_id,
        )
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(patient, field, value)
    patient.updated_at = datetime.now(timezone.utc)
    return _patient_to_response(patient)


@router.delete("/{patient_id}", status_code=204)
async def delete_patient(patient_id: str, current_user: CurrentUser, db: DB):
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == current_user.clinic_id,
        )
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient.is_active = False  # soft delete
