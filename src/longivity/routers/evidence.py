"""
Evidence router — patient-specific literature and risk synthesis endpoints.

GET  /api/v1/patients/{patient_id}/evidence/compound/{compound_id}
GET  /api/v1/patients/{patient_id}/evidence/hallmark/{hallmark}
GET  /api/v1/patients/{patient_id}/evidence/cancer-risk
POST /api/v1/research-intelligence/research  (pass-through to orchestrator)
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from longivity.db.database import get_db
from longivity.db.models import BiomarkerPanel, Patient, PanelValue
from longivity.core.auth import get_current_user
from longivity.services.evidence_service import get_evidence_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["evidence"])


# ── Request/Response models ───────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    query: str
    context: dict | None = None
    max_papers: int = 10


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_patient_or_404(patient_id: int, db: AsyncSession, current_user) -> Patient:
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == current_user.clinic_id,
        )
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


async def _get_latest_biomarkers(patient_id: int, db: AsyncSession) -> dict:
    """Get the most recent panel's biomarker values as a flat dict."""
    result = await db.execute(
        select(BiomarkerPanel)
        .where(BiomarkerPanel.patient_id == patient_id)
        .order_by(BiomarkerPanel.drawn_at.desc())
        .limit(1)
    )
    panel = result.scalar_one_or_none()
    if not panel:
        return {}

    result = await db.execute(
        select(PanelValue).where(PanelValue.panel_id == panel.id)
    )
    values = result.scalars().all()
    return {v.marker_key: v.value for v in values}


async def _get_dna_repair_genes(patient_id: int, db: AsyncSession) -> dict:
    """Extract DNA repair gene data from panel raw_json."""
    result = await db.execute(
        select(BiomarkerPanel)
        .where(BiomarkerPanel.patient_id == patient_id)
        .order_by(BiomarkerPanel.drawn_at.desc())
    )
    panels = result.scalars().all()
    for panel in panels:
        if panel.raw_json and "dna_repair" in panel.raw_json:
            return panel.raw_json["dna_repair"]
    return {}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/patients/{patient_id}/evidence/compound/{compound_id}")
async def get_compound_evidence(
    patient_id: int,
    compound_id: str,
    hallmark: str = "longevity",
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """
    Get PubMed evidence for a compound recommendation for this patient.
    
    Query params:
        hallmark: the hallmark this compound targets (default: "longevity")
    """
    patient = await _get_patient_or_404(patient_id, db, current_user)
    biomarkers = await _get_latest_biomarkers(patient_id, db)

    svc = get_evidence_service()
    result = await svc.get_compound_evidence(
        compound_id=compound_id,
        hallmark=hallmark,
        patient_context={
            "age": _calc_age(patient.date_of_birth),
            "sex": patient.sex,
            "condition": patient.notes[:100] if patient.notes else None,
            "biomarkers": biomarkers,
        },
    )
    return result


@router.get("/patients/{patient_id}/evidence/hallmark/{hallmark}")
async def get_hallmark_narrative(
    patient_id: int,
    hallmark: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """
    Get a clinical narrative for an active hallmark with this patient's biomarker context.
    """
    patient = await _get_patient_or_404(patient_id, db, current_user)
    biomarkers = await _get_latest_biomarkers(patient_id, db)

    # Filter to abnormal biomarkers only (non-None values)
    abnormal = {k: v for k, v in biomarkers.items() if v is not None}

    svc = get_evidence_service()
    result = await svc.get_hallmark_narrative(
        hallmark=hallmark,
        biomarkers=abnormal,
        patient_age=_calc_age(patient.date_of_birth),
        patient_sex=patient.sex,
    )
    return result


@router.get("/patients/{patient_id}/evidence/cancer-risk")
async def get_cancer_risk(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """
    Synthesize cancer risk from DNA repair gene panel + inflammatory biomarkers.
    Returns risk tier, genomic instability score, inflammatory burden score,
    surveillance recommendations, and literature citations.
    """
    patient = await _get_patient_or_404(patient_id, db, current_user)
    biomarkers = await _get_latest_biomarkers(patient_id, db)
    dna_repair_genes = await _get_dna_repair_genes(patient_id, db)

    if not dna_repair_genes:
        return {
            "overall_risk_tier": "UNKNOWN",
            "message": "No DNA repair gene panel data found for this patient",
            "genomic_instability_score": None,
            "inflammatory_burden_score": None,
            "synthesis": "",
            "recommended_surveillance": ["Standard age-appropriate cancer screening"],
            "citations": [],
        }

    svc = get_evidence_service()
    result = await svc.get_cancer_risk_summary(
        dna_repair_genes=dna_repair_genes,
        biomarkers=biomarkers,
        patient_age=_calc_age(patient.date_of_birth),
        patient_sex=patient.sex,
    )
    return result


@router.post("/research-intelligence/research")
async def research_passthrough(
    request: ResearchRequest,
    current_user=Depends(get_current_user),
) -> dict:
    """
    Pass-through to the research_intelligence orchestrator.
    Accepts any free-form research query with optional context.
    """
    svc = get_evidence_service()
    orchestrator = await svc._get_orchestrator()

    if orchestrator is None:
        return {
            "query": request.query,
            "synthesis": (
                "Research intelligence service unavailable. "
                "Set NCBI_USER_EMAIL and OPENROUTER_API_KEY to enable."
            ),
            "papers": [],
            "evidence_tier": "INSUFFICIENT",
            "fallback": True,
        }

    try:
        import asyncio
        result = await asyncio.wait_for(
            orchestrator.research(
                query=request.query,
                context=request.context or {},
            ),
            timeout=45.0,
        )
        return result if isinstance(result, dict) else {"synthesis": str(result)}
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Research query timed out after 45s",
        )
    except Exception as e:
        logger.error(f"Research passthrough error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ── Helper ────────────────────────────────────────────────────────────────────

def _calc_age(dob) -> int | None:
    if not dob:
        return None
    try:
        from datetime import datetime, timezone, date
        if isinstance(dob, str):
            dob = date.fromisoformat(dob)
        today = datetime.now(timezone.utc).date()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        return None
