"""Assessment router — wire existing longevity services to persisted patient panels."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..core.deps import CurrentUser, DB
from ..db.models import BiomarkerPanel, Patient
from ..services.longevity_phenoage_level0 import run_longevity_assessment_level0
from ..services.longitudinal_service import compute_longitudinal_delta
from ..services.nof1_trial_engine import generate_nof1_protocol

router = APIRouter(prefix="/api/v1/patients", tags=["assessment"])


def _panel_to_biomarkers(panel: BiomarkerPanel) -> dict[str, float]:
    """Convert a stored panel's values to the biomarker dict expected by assessment services."""
    return {v.marker_key: v.value for v in (panel.values or [])}


async def _get_patient_or_404(patient_id: str, clinic_id: str, db) -> Patient:
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == clinic_id,
        )
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


async def _get_latest_panel(patient_id: str, db) -> BiomarkerPanel | None:
    result = await db.execute(
        select(BiomarkerPanel)
        .where(BiomarkerPanel.patient_id == patient_id)
        .options(selectinload(BiomarkerPanel.values))
        .order_by(BiomarkerPanel.drawn_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/{patient_id}/assessment", response_model=dict)
async def get_patient_assessment(
    patient_id: str,
    current_user: CurrentUser,
    db: DB,
    compound_queries: str | None = None,  # comma-separated compound IDs
):
    """
    Run a full longevity assessment on the patient's latest biomarker panel.

    Uses PhenoAge (Levine 2018), hallmark scoring, MR-validated compound ranking,
    and cardiovascular risk. Returns the same payload as /assessment_level0 but
    sourced from the patient's stored data.
    """
    patient = await _get_patient_or_404(patient_id, current_user.clinic_id, db)
    panel = await _get_latest_panel(patient_id, db)

    if not panel:
        raise HTTPException(
            status_code=404,
            detail="No biomarker panels found for this patient. Upload a lab report first.",
        )

    biomarkers = _panel_to_biomarkers(panel)
    age = None
    if patient.date_of_birth:
        from datetime import datetime
        try:
            dob = datetime.strptime(patient.date_of_birth, "%Y-%m-%d")
            today = datetime.now()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except Exception:
            pass

    payload: dict[str, Any] = {
        "biomarkers": biomarkers,
        "age": age,
        "chronological_age": age,
    }
    if compound_queries:
        payload["compound_queries"] = [c.strip() for c in compound_queries.split(",")]

    result = run_longevity_assessment_level0(payload)
    result["_meta"] = {
        "patient_id": patient_id,
        "panel_id": panel.id,
        "drawn_at": panel.drawn_at.isoformat(),
        "source": panel.source,
        "lab_name": panel.lab_name,
    }
    return result


@router.get("/{patient_id}/longitudinal", response_model=dict)
async def get_patient_longitudinal(
    patient_id: str,
    current_user: CurrentUser,
    db: DB,
):
    """
    Compute longitudinal biomarker trends across all stored panels.

    Returns PhenoAge trajectory, per-marker deltas between consecutive panels,
    and trend direction for each marker.
    """
    await _get_patient_or_404(patient_id, current_user.clinic_id, db)

    result = await db.execute(
        select(BiomarkerPanel)
        .where(BiomarkerPanel.patient_id == patient_id)
        .options(selectinload(BiomarkerPanel.values))
        .order_by(BiomarkerPanel.drawn_at.asc())
    )
    panels = result.scalars().all()

    if len(panels) < 2:
        return {
            "patient_id": patient_id,
            "panel_count": len(panels),
            "message": "At least 2 panels required for longitudinal analysis.",
            "panels": [
                {
                    "panel_id": p.id,
                    "drawn_at": p.drawn_at.isoformat(),
                    "biomarkers": _panel_to_biomarkers(p),
                }
                for p in panels
            ],
        }

    # Compute PhenoAge for each panel
    phenoage_trajectory = []
    for panel in panels:
        bm = _panel_to_biomarkers(panel)
        try:
            assessment = run_longevity_assessment_level0({"biomarkers": bm})
            phenoage = assessment.get("phenoage_result", {}).get("phenoage_estimate")
        except Exception:
            phenoage = None
        phenoage_trajectory.append({
            "panel_id": panel.id,
            "drawn_at": panel.drawn_at.isoformat(),
            "phenoage_estimate": phenoage,
            "biomarkers": bm,
        })

    # Compute deltas between consecutive panels
    deltas = []
    for i in range(1, len(panels)):
        prior_bm = _panel_to_biomarkers(panels[i - 1])
        current_bm = _panel_to_biomarkers(panels[i])
        try:
            delta = compute_longitudinal_delta(current_bm, prior_bm)
        except Exception as e:
            delta = {"error": str(e)}
        deltas.append({
            "from_panel": panels[i - 1].id,
            "to_panel": panels[i].id,
            "from_date": panels[i - 1].drawn_at.isoformat(),
            "to_date": panels[i].drawn_at.isoformat(),
            "delta": delta,
        })

    return {
        "patient_id": patient_id,
        "panel_count": len(panels),
        "phenoage_trajectory": phenoage_trajectory,
        "deltas": deltas,
    }


@router.get("/{patient_id}/nof1/{compound_id}", response_model=dict)
async def get_patient_nof1(
    patient_id: str,
    compound_id: str,
    current_user: CurrentUser,
    db: DB,
):
    """
    Generate a personalized N-of-1 trial protocol for a patient + compound.

    Uses the patient's latest biomarker panel as baseline.
    """
    patient = await _get_patient_or_404(patient_id, current_user.clinic_id, db)
    panel = await _get_latest_panel(patient_id, db)

    if not panel:
        raise HTTPException(
            status_code=404,
            detail="No biomarker panels found. Upload a lab report first.",
        )

    biomarkers = _panel_to_biomarkers(panel)
    age = None
    if patient.date_of_birth:
        from datetime import datetime
        try:
            dob = datetime.strptime(patient.date_of_birth, "%Y-%m-%d")
            today = datetime.now()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except Exception:
            age = 45

    protocol = generate_nof1_protocol(
        patient_id=patient_id,
        age=age or 45,
        baseline_biomarkers=biomarkers,
        compound_id=compound_id,
    )
    protocol["_meta"] = {
        "patient_id": patient_id,
        "panel_id": panel.id,
        "drawn_at": panel.drawn_at.isoformat(),
    }
    return protocol
