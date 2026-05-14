from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from .services.longevity_phenoage_level0 import run_longevity_assessment_level0
from .services.longevity_report_builder import run_longevity_full_assessment
from .services.cardiovascular_risk import compute_ascvd_from_biomarkers
from .services.longitudinal_service import compute_longitudinal_delta
from .services.wearable_service import score_wearables

router = APIRouter(prefix="/api/v1/longevity", tags=["longevity"])


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response models
# ─────────────────────────────────────────────────────────────────────────────

class LongevityAssessmentLevel0Request(BaseModel):
    """Level 0: PhenoAge Gompertz (PMID 29676998) + hallmark narrative + optional compound ranking (RUO)."""

    biomarkers: Dict[str, Any] = Field(default_factory=dict)
    age: Optional[int] = None
    chronological_age: Optional[int] = None
    compound_queries: Optional[List[str]] = Field(default=None)
    patient_medications: Optional[List[str]] = Field(default=None)
    medications: Optional[List[str]] = Field(
        default=None,
        description="Alias for patient_medications (same semantics).",
    )

    @model_validator(mode="after")
    def merge_medication_aliases(self):
        if self.medications:
            if not self.patient_medications:
                self.patient_medications = list(self.medications)
            else:
                seen: set = set()
                merged: List[str] = []
                for x in list(self.patient_medications) + list(self.medications):
                    if x and str(x) not in seen:
                        seen.add(str(x))
                        merged.append(str(x))
                self.patient_medications = merged
        return self


class LongevityFullAssessmentRequest(LongevityAssessmentLevel0Request):
    """Level 0 plus optional Module 1 (variants) and Module 2 (patient_genotype for DNA repair)."""

    patient_id: Optional[str] = Field(default=None)
    variants: Optional[Dict[str, Any]] = Field(default=None)
    patient_genotype: Optional[Dict[str, Any]] = Field(default=None)


class CardiovascularRiskRequest(BaseModel):
    age: int
    sex: str = Field(..., description="M or F")
    race: str = Field(default="white", description="white or aa")
    biomarkers: Dict[str, Any] = Field(default_factory=dict)
    bp_treatment: bool = False
    diabetes: bool = False
    smoker: bool = False


class LongitudinalDeltaRequest(BaseModel):
    current: Dict[str, Any]
    prior: Dict[str, Any]
    higher_is_better: Optional[List[str]] = None


class WearableRequest(BaseModel):
    wearable_data: Dict[str, Any] = Field(default_factory=dict)
    patient_id: Optional[str] = None


class AgenticAssessRequest(BaseModel):
    """
    Full agentic assessment via LangGraph multi-agent pipeline.

    Runs: biomarker_agent → (optional) genetic_agent → (optional) cardiovascular_agent
          → longitudinal_agent → gap_detection_agent → report_assembler_agent

    Returns a unified patient report with biological age, hallmarks, genetics,
    cardiovascular risk, longitudinal delta, gap detection, and data completeness score.
    """
    patient_id: Optional[str] = Field(default=None, description="Patient identifier (UUID or string)")
    age: Optional[int] = Field(default=None, description="Chronological age in years")
    sex: Optional[str] = Field(default=None, description="Patient sex: male / female")
    biomarkers: Dict[str, Any] = Field(default_factory=dict, description="Biomarker key-value pairs")
    variants: Optional[List[Dict[str, Any]]] = Field(default=None, description="SNP variant list [{rsid, genotype}]")
    patient_genotype: Optional[Dict[str, Any]] = Field(default=None, description="DNA repair gene panel genotype")
    wearables: Optional[Dict[str, Any]] = Field(default=None, description="Wearable device data")
    body_composition: Optional[Dict[str, Any]] = Field(default=None, description="DEXA / body composition data")
    visit_history: Optional[List[Dict[str, Any]]] = Field(default=None, description="Prior visit records")
    compound_queries: Optional[List[str]] = Field(default=None, description="Compounds to evaluate")
    patient_medications: Optional[List[str]] = Field(default=None, description="Current medications")


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/assessment_level0")
async def longevity_assessment_level0(body: LongevityAssessmentLevel0Request) -> Dict[str, Any]:
    payload = body.model_dump(exclude_none=True)
    return run_longevity_assessment_level0(payload)


@router.post("/full_assessment")
async def longevity_full_assessment(body: LongevityFullAssessmentRequest) -> Dict[str, Any]:
    payload = body.model_dump(exclude_none=True)
    result = run_longevity_full_assessment(payload)
    if result.get("status") == "ERROR":
        raise HTTPException(
            status_code=422,
            detail=result.get("error", "No usable input for longevity assessment."),
        )
    return result


@router.post("/cardiovascular_risk")
async def cardiovascular_risk(body: CardiovascularRiskRequest) -> Dict[str, Any]:
    payload = body.model_dump()
    payload["biomarkers"] = payload.get("biomarkers") or {}
    return compute_ascvd_from_biomarkers(payload)


@router.post("/longitudinal_delta")
async def longitudinal_delta(body: LongitudinalDeltaRequest) -> Dict[str, Any]:
    return compute_longitudinal_delta(body.current, body.prior, body.higher_is_better)


@router.post("/wearable_integration")
async def wearable_integration(body: WearableRequest) -> Dict[str, Any]:
    return score_wearables(body.wearable_data)


@router.post("/agent/assess")
async def agentic_assess(body: AgenticAssessRequest) -> Dict[str, Any]:
    """
    Full multi-agent longevity assessment via LangGraph pipeline.

    Orchestrates 6 specialized agents in a conditional state machine:
    biomarker → genetics (if data) → cardiovascular (if data) →
    longitudinal → gap_detection → report_assembler

    Returns unified patient report with data completeness score (0–100).
    """
    try:
        from longivity.agents import get_longevity_graph, PatientState
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"LangGraph agent pipeline not available: {e}. Install langgraph>=0.2.0.",
        )

    run_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    # Build PatientState from request
    current_input: Dict[str, Any] = {
        "biomarkers": body.biomarkers or {},
        "age": body.age,
        "sex": body.sex,
        "variants": body.variants,
        "patient_genotype": body.patient_genotype,
        "wearables": body.wearables,
        "body_composition": body.body_composition,
        "compound_queries": body.compound_queries,
        "patient_medications": body.patient_medications,
    }
    # Remove None values
    current_input = {k: v for k, v in current_input.items() if v is not None}

    initial_state: PatientState = {
        "patient_id": body.patient_id or run_id,
        "age": body.age,
        "sex": body.sex,
        "current_input": current_input,
        "visit_history": body.visit_history or [],
        "phenoage_result": None,
        "hallmark_result": None,
        "genetic_result": None,
        "dna_repair_result": None,
        "prs_result": None,
        "compound_result": None,
        "cardiovascular_risk": None,
        "wearable_result": None,
        "body_composition_result": None,
        "detected_gaps": None,
        "gap_priority_order": None,
        "longitudinal_delta": None,
        "final_report": None,
        "errors": [],
        "agents_run": [],
        "run_id": run_id,
        "timestamp": timestamp,
    }

    try:
        graph = get_longevity_graph()
        final_state = graph.invoke(initial_state)
        report = final_state.get("final_report") or {}
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent pipeline error: {e}")


@router.get("/healthz")
async def healthz() -> Dict[str, Any]:
    return {"status": "ok", "service": "longivity", "version": "0.2.0"}
