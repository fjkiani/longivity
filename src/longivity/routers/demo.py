"""
Demo router — public endpoints for demo environment status and reset.

GET  /api/v1/demo/status  — public, returns seeded status + demo credentials
POST /api/v1/demo/reset   — requires X-Demo-Reset-Key header
"""
from __future__ import annotations

import os
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from longivity.db.database import get_db
from longivity.db.models import Clinic, ClinicUser, Patient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])

DEMO_EMAIL = "demo@longivity.ai"
DEMO_CLINIC_NAME = "Longivity Demo Clinic"
DEMO_MRN_PREFIX = "DEMO-"
DEMO_RESET_KEY = os.getenv("DEMO_RESET_KEY", "longivity-demo-reset-2026")


@router.get("/status")
async def demo_status(db: AsyncSession = Depends(get_db)):
    """
    Public endpoint — returns demo environment status.
    Used by the /demo-login page to show what's available.
    """
    result = await db.execute(select(Clinic).where(Clinic.name == DEMO_CLINIC_NAME))
    clinic = result.scalar_one_or_none()

    if not clinic:
        return {
            "seeded": False,
            "message": "Demo environment not yet seeded. Run: python scripts/seed_demo.py",
            "credentials": None,
            "patients": [],
        }

    # Count demo patients
    result = await db.execute(
        select(Patient).where(
            Patient.clinic_id == clinic.id,
            Patient.mrn.like(f"{DEMO_MRN_PREFIX}%"),
        )
    )
    patients = result.scalars().all()

    patient_summaries = []
    for p in sorted(patients, key=lambda x: x.mrn):
        patient_summaries.append({
            "mrn": p.mrn,
            "name": f"{p.first_name} {p.last_name}",
            "age": _calc_age(p.date_of_birth),
            "sex": p.sex,
            "condition": _extract_condition(p.notes),
        })

    return {
        "seeded": True,
        "seeded_at": clinic.created_at.isoformat() if hasattr(clinic, "created_at") and clinic.created_at else None,
        "credentials": {
            "email": DEMO_EMAIL,
            "password": "DemoPass2026!",
            "note": "Research Use Only — synthetic data derived from published reference distributions",
        },
        "clinic": DEMO_CLINIC_NAME,
        "patient_count": len(patients),
        "patients": patient_summaries,
        "data_sources": [
            "NHANES III/IV (Levine 2018, PMID 29676998)",
            "LonGenity centenarian cohort (phs000451)",
            "MESA cardiovascular study (PMID 12397006)",
            "InCHIANTI aging cohort (PMID 10843354)",
            "BLSA longitudinal aging (PMID 22451492)",
            "DNA repair gene panel (BRCA1/2, MLH1/2, MUTYH, ATM, CHEK2)",
        ],
    }


@router.post("/reset")
async def demo_reset(
    x_demo_reset_key: str = Header(None, alias="X-Demo-Reset-Key"),
    db: AsyncSession = Depends(get_db),
):
    """
    Reset demo environment — wipes and re-seeds all demo patients.
    Requires X-Demo-Reset-Key header.
    """
    if x_demo_reset_key != DEMO_RESET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Demo-Reset-Key header",
        )

    # Trigger async seed with reset=True
    try:
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "scripts/seed_demo.py", "--reset"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            logger.error(f"Demo reset failed: {result.stderr}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Seed script failed: {result.stderr[:500]}",
            )

        return {
            "success": True,
            "message": "Demo environment reset successfully",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stdout": result.stdout[-1000:] if result.stdout else "",
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Seed script timed out after 120s",
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _calc_age(dob) -> int | None:
    if not dob:
        return None
    try:
        if isinstance(dob, str):
            from datetime import date
            dob = date.fromisoformat(dob)
        today = datetime.now(timezone.utc).date()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        return None


def _extract_condition(notes: str | None) -> str:
    """Extract the first sentence of notes as the condition headline."""
    if not notes:
        return "Unknown"
    # Notes format: "Condition description. More details."
    first = notes.split(".")[0].strip()
    return first[:80] if first else "Unknown"
