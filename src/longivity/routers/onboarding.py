"""
Onboarding Router — Longivity
Self-serve clinic onboarding: seed demo patients, track checklist.

Endpoints:
  POST /api/v1/onboarding/start          — trigger async demo seeding
  GET  /api/v1/onboarding/{id}/status    — poll seeding progress
  POST /api/v1/onboarding/complete       — mark onboarding done
  GET  /api/v1/onboarding/checklist      — per-clinic 4-step checklist
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import CurrentUser, DB
from ..db.models import (
    BiomarkerPanel, BiomarkerValue, Clinic, OnboardingJob, Patient
)

logger = logging.getLogger("longivity.onboarding")

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class OnboardingStartRequest(BaseModel):
    plan: Literal["trial", "pro", "enterprise"] = "trial"
    seed_demo: bool = True


class OnboardingStartResponse(BaseModel):
    onboarding_id: str
    status: str
    eta_seconds: int
    message: str


class OnboardingStatusResponse(BaseModel):
    onboarding_id: str
    status: str
    patients_created: int
    error: str | None
    started_at: str
    completed_at: str | None
    next_step: str


class OnboardingCompleteResponse(BaseModel):
    message: str
    completed_at: str
    checklist: list[dict]


class ChecklistResponse(BaseModel):
    clinic_id: str
    onboarding_complete: bool
    steps: list[dict]


# ── Demo patient seed data ────────────────────────────────────────────────────
# 3 archetypes: T2D (Marcus), CVD (Robert), Centenarian (James)
# Biomarker values validated against production PhenoAge engine (PMID 29676998)

DEMO_SEED_PATIENTS = [
    {
        "first_name": "Marcus",
        "last_name": "T. (Demo)",
        "date_of_birth": "1968-03-15",
        "sex": "male",
        "mrn": "ONBOARD-001",
        "notes": "Demo: T2D archetype. PhenoAge 73.6yr (+15.6yr acceleration). Metformin MR_VALIDATED.",
        "panel": {
            "drawn_at": "2026-01-15T08:00:00Z",
            "source": "manual",
            "lab_name": "Demo Lab",
            "notes": "Onboarding demo panel — T2D archetype",
            "values": [
                {"marker_key": "albumin",              "value": 4.0,  "unit": "g/dL",    "ref_low": 3.5,  "ref_high": 5.0,  "flag": None},
                {"marker_key": "creatinine",           "value": 1.1,  "unit": "mg/dL",   "ref_low": 0.7,  "ref_high": 1.3,  "flag": None},
                {"marker_key": "glucose_mg_dl",        "value": 142.0,"unit": "mg/dL",   "ref_low": 70,   "ref_high": 99,   "flag": "H"},
                {"marker_key": "crp",                  "value": 4.8,  "unit": "mg/L",    "ref_low": 0,    "ref_high": 3.0,  "flag": "H"},
                {"marker_key": "lymphocyte_percent",   "value": 21.0, "unit": "%",       "ref_low": 20,   "ref_high": 40,   "flag": None},
                {"marker_key": "mcv",                  "value": 94.0, "unit": "fL",      "ref_low": 80,   "ref_high": 100,  "flag": None},
                {"marker_key": "rdw",                  "value": 15.2, "unit": "%",       "ref_low": 11.5, "ref_high": 14.5, "flag": "H"},
                {"marker_key": "alkaline_phosphatase", "value": 95.0, "unit": "U/L",     "ref_low": 44,   "ref_high": 147,  "flag": None},
                {"marker_key": "wbc",                  "value": 9.2,  "unit": "10^3/uL", "ref_low": 4.5,  "ref_high": 11.0, "flag": None},
            ],
        },
    },
    {
        "first_name": "Robert",
        "last_name": "C. (Demo)",
        "date_of_birth": "1963-07-22",
        "sex": "male",
        "mrn": "ONBOARD-002",
        "notes": "Demo: CVD archetype. PhenoAge 81.5yr (+18.5yr acceleration). Omega-3 MR_VALIDATED.",
        "panel": {
            "drawn_at": "2026-01-15T08:00:00Z",
            "source": "manual",
            "lab_name": "Demo Lab",
            "notes": "Onboarding demo panel — CVD archetype",
            "values": [
                {"marker_key": "albumin",              "value": 3.9,  "unit": "g/dL",    "ref_low": 3.5,  "ref_high": 5.0,  "flag": None},
                {"marker_key": "creatinine",           "value": 1.3,  "unit": "mg/dL",   "ref_low": 0.7,  "ref_high": 1.3,  "flag": None},
                {"marker_key": "glucose_mg_dl",        "value": 118.0,"unit": "mg/dL",   "ref_low": 70,   "ref_high": 99,   "flag": "H"},
                {"marker_key": "crp",                  "value": 6.2,  "unit": "mg/L",    "ref_low": 0,    "ref_high": 3.0,  "flag": "H"},
                {"marker_key": "lymphocyte_percent",   "value": 19.0, "unit": "%",       "ref_low": 20,   "ref_high": 40,   "flag": "L"},
                {"marker_key": "mcv",                  "value": 96.0, "unit": "fL",      "ref_low": 80,   "ref_high": 100,  "flag": None},
                {"marker_key": "rdw",                  "value": 15.8, "unit": "%",       "ref_low": 11.5, "ref_high": 14.5, "flag": "H"},
                {"marker_key": "alkaline_phosphatase", "value": 105.0,"unit": "U/L",     "ref_low": 44,   "ref_high": 147,  "flag": None},
                {"marker_key": "wbc",                  "value": 10.1, "unit": "10^3/uL", "ref_low": 4.5,  "ref_high": 11.0, "flag": None},
            ],
        },
    },
    {
        "first_name": "James",
        "last_name": "L. (Demo)",
        "date_of_birth": "1958-11-03",
        "sex": "male",
        "mrn": "ONBOARD-003",
        "notes": "Demo: Centenarian archetype. PhenoAge 48.2yr (−19.8yr acceleration). All wearables OPTIMAL.",
        "panel": {
            "drawn_at": "2026-01-15T08:00:00Z",
            "source": "manual",
            "lab_name": "Demo Lab",
            "notes": "Onboarding demo panel — centenarian archetype",
            "values": [
                {"marker_key": "albumin",              "value": 4.7,  "unit": "g/dL",    "ref_low": 3.5,  "ref_high": 5.0,  "flag": None},
                {"marker_key": "creatinine",           "value": 0.82, "unit": "mg/dL",   "ref_low": 0.7,  "ref_high": 1.3,  "flag": None},
                {"marker_key": "glucose_mg_dl",        "value": 84.0, "unit": "mg/dL",   "ref_low": 70,   "ref_high": 99,   "flag": None},
                {"marker_key": "crp",                  "value": 0.2,  "unit": "mg/L",    "ref_low": 0,    "ref_high": 3.0,  "flag": None},
                {"marker_key": "lymphocyte_percent",   "value": 34.0, "unit": "%",       "ref_low": 20,   "ref_high": 40,   "flag": None},
                {"marker_key": "mcv",                  "value": 87.0, "unit": "fL",      "ref_low": 80,   "ref_high": 100,  "flag": None},
                {"marker_key": "rdw",                  "value": 12.1, "unit": "%",       "ref_low": 11.5, "ref_high": 14.5, "flag": None},
                {"marker_key": "alkaline_phosphatase", "value": 50.0, "unit": "U/L",     "ref_low": 44,   "ref_high": 147,  "flag": None},
                {"marker_key": "wbc",                  "value": 4.9,  "unit": "10^3/uL", "ref_low": 4.5,  "ref_high": 11.0, "flag": None},
            ],
        },
    },
]


# ── Background seeding task ───────────────────────────────────────────────────

async def _seed_demo_patients(job_id: str, clinic_id: str, db: AsyncSession) -> None:
    """
    Background task: create 3 demo patients + biomarker panels for a new clinic.
    Updates OnboardingJob.status as it progresses.
    """
    from ..db.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        try:
            job = await session.get(OnboardingJob, job_id)
            if not job:
                return

            patients_created = 0
            for profile in DEMO_SEED_PATIENTS:
                patient = Patient(
                    clinic_id=clinic_id,
                    first_name=profile["first_name"],
                    last_name=profile["last_name"],
                    date_of_birth=profile["date_of_birth"],
                    sex=profile["sex"],
                    mrn=profile["mrn"],
                    notes=profile["notes"],
                )
                session.add(patient)
                await session.flush()

                panel_data = profile["panel"]
                panel = BiomarkerPanel(
                    patient_id=patient.id,
                    drawn_at=datetime.fromisoformat(panel_data["drawn_at"].replace("Z", "+00:00")),
                    source=panel_data["source"],
                    lab_name=panel_data["lab_name"],
                    notes=panel_data["notes"],
                )
                session.add(panel)
                await session.flush()

                for v in panel_data["values"]:
                    bv = BiomarkerValue(
                        panel_id=panel.id,
                        marker_key=v["marker_key"],
                        marker_display=v.get("marker_display", v["marker_key"].replace("_", " ").title()),
                        value=v["value"],
                        unit=v.get("unit"),
                        ref_low=v.get("ref_low"),
                        ref_high=v.get("ref_high"),
                        flag=v.get("flag"),
                    )
                    session.add(bv)

                patients_created += 1
                job.patients_created = patients_created
                await session.commit()
                await asyncio.sleep(0.5)

            job.status = "complete"
            job.completed_at = datetime.now(timezone.utc)

            clinic = await session.get(Clinic, clinic_id)
            if clinic:
                clinic.plan = job.plan

            await session.commit()
            logger.info(f"Onboarding complete: clinic={clinic_id}, patients={patients_created}")

        except Exception as e:
            logger.error(f"Onboarding seeding failed: {e}")
            try:
                job = await session.get(OnboardingJob, job_id)
                if job:
                    job.status = "failed"
                    job.error = str(e)
                    await session.commit()
            except Exception:
                pass


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/start", response_model=OnboardingStartResponse, status_code=202)
async def start_onboarding(
    body: OnboardingStartRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DB,
):
    """
    Trigger async clinic onboarding. Seeds 3 demo patients if seed_demo=True.
    Call immediately after POST /api/v1/auth/register.
    Poll GET /api/v1/onboarding/{id}/status for progress.
    """
    clinic = await db.get(Clinic, current_user.clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    if clinic.onboarding_completed_at:
        raise HTTPException(status_code=409, detail="Clinic already onboarded")

    job = OnboardingJob(
        clinic_id=current_user.clinic_id,
        plan=body.plan,
        seed_demo=body.seed_demo,
        status="seeding" if body.seed_demo else "complete",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    if body.seed_demo:
        background_tasks.add_task(_seed_demo_patients, job.id, current_user.clinic_id, db)

    return OnboardingStartResponse(
        onboarding_id=job.id,
        status=job.status,
        eta_seconds=30 if body.seed_demo else 0,
        message=(
            "Seeding 3 demo patients (Marcus T2D, Robert CVD, James centenarian). Poll /status for progress."
            if body.seed_demo else
            "Onboarding started without demo patients."
        ),
    )


@router.get("/{onboarding_id}/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    onboarding_id: str,
    current_user: CurrentUser,
    db: DB,
):
    """Poll onboarding progress. Returns status: seeding | complete | failed."""
    job = await db.get(OnboardingJob, onboarding_id)
    if not job:
        raise HTTPException(status_code=404, detail="Onboarding job not found")

    if job.clinic_id != current_user.clinic_id:
        raise HTTPException(status_code=403, detail="Not your onboarding job")

    next_step_map = {
        "seeding": f"Seeding demo patients ({job.patients_created}/3 created). Refresh in 5 seconds.",
        "complete": "Onboarding complete. Visit /dashboard to see your patients.",
        "failed": f"Seeding failed: {job.error}. Contact support@longivity.ai.",
    }

    return OnboardingStatusResponse(
        onboarding_id=job.id,
        status=job.status,
        patients_created=job.patients_created,
        error=job.error,
        started_at=job.started_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        next_step=next_step_map.get(job.status, "Unknown status"),
    )


@router.post("/complete", response_model=OnboardingCompleteResponse)
async def complete_onboarding(
    current_user: CurrentUser,
    db: DB,
):
    """Mark onboarding done. Sets clinic.onboarding_completed_at."""
    clinic = await db.get(Clinic, current_user.clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    now = datetime.now(timezone.utc)
    clinic.onboarding_completed_at = now
    await db.commit()

    checklist = await _build_checklist(current_user.clinic_id, db)

    return OnboardingCompleteResponse(
        message="Onboarding complete. Welcome to Longivity.",
        completed_at=now.isoformat(),
        checklist=checklist,
    )


@router.get("/checklist", response_model=ChecklistResponse)
async def get_checklist(
    current_user: CurrentUser,
    db: DB,
):
    """Returns per-clinic 4-step checklist. Computed live from DB state."""
    clinic = await db.get(Clinic, current_user.clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    checklist = await _build_checklist(current_user.clinic_id, db)

    return ChecklistResponse(
        clinic_id=current_user.clinic_id,
        onboarding_complete=clinic.onboarding_completed_at is not None,
        steps=checklist,
    )


async def _build_checklist(clinic_id: str, db: AsyncSession) -> list[dict]:
    """Compute 4-step checklist from live DB state."""
    from ..db.models import TestOrder, PatientEvent

    patient_result = await db.execute(
        select(func.count(Patient.id)).where(Patient.clinic_id == clinic_id)
    )
    patient_count = patient_result.scalar() or 0

    panel_result = await db.execute(
        select(func.count(BiomarkerPanel.id))
        .join(Patient, BiomarkerPanel.patient_id == Patient.id)
        .where(Patient.clinic_id == clinic_id)
    )
    panel_count = panel_result.scalar() or 0

    assessment_result = await db.execute(
        select(func.count(PatientEvent.id))
        .where(
            PatientEvent.clinic_id == clinic_id,
            PatientEvent.event_type == "assessment_run",
        )
    )
    assessment_count = assessment_result.scalar() or 0

    order_result = await db.execute(
        select(func.count(TestOrder.id))
        .join(Patient, TestOrder.patient_id == Patient.id)
        .where(Patient.clinic_id == clinic_id)
    )
    order_count = order_result.scalar() or 0

    return [
        {
            "id": "first_patient",
            "label": "Add your first patient",
            "description": "Create a patient record or use a demo patient.",
            "completed": patient_count > 0,
            "count": patient_count,
        },
        {
            "id": "first_panel",
            "label": "Upload a biomarker panel",
            "description": "Import lab results via PDF or manual entry.",
            "completed": panel_count > 0,
            "count": panel_count,
        },
        {
            "id": "first_assessment",
            "label": "Run your first assessment",
            "description": "Compute PhenoAge acceleration and hallmark scores.",
            "completed": assessment_count > 0,
            "count": assessment_count,
        },
        {
            "id": "first_order",
            "label": "Generate a test order",
            "description": "Let the AI agent recommend the next lab panel.",
            "completed": order_count > 0,
            "count": order_count,
        },
    ]
