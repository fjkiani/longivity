from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from datetime import datetime, timezone, timedelta
from threading import Lock
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from .services.longevity_phenoage_level0 import run_longevity_assessment_level0
from .services.longevity_report_builder import run_longevity_full_assessment
from .services.cardiovascular_risk import compute_ascvd_from_biomarkers
from .services.longitudinal_service import compute_longitudinal_delta
from .services.wearable_service import score_wearables

router = APIRouter(prefix="/api/v1/longevity", tags=["longevity"])

# ─────────────────────────────────────────────────────────────────────────────
# In-memory run registry (TTL: 1 hour)
# ─────────────────────────────────────────────────────────────────────────────

_RUN_REGISTRY: dict = {}
_REGISTRY_LOCK = Lock()
_REGISTRY_TTL_HOURS = 1


def _register_run(run_id: str, audit_log: list, pipeline_health: dict) -> None:
    with _REGISTRY_LOCK:
        _evict_expired()
        _RUN_REGISTRY[run_id] = {
            "run_id": run_id,
            "audit_log": audit_log,
            "pipeline_health": pipeline_health,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }


def _evict_expired() -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=_REGISTRY_TTL_HOURS)
    expired = [k for k, v in _RUN_REGISTRY.items()
               if datetime.fromisoformat(v["registered_at"]) < cutoff]
    for k in expired:
        del _RUN_REGISTRY[k]


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


class EpigeneticClockRequest(BaseModel):
    """
    Pre-computed epigenetic clock values for normalization (RUO).

    Accepts values from external methylation array analysis (e.g., Illumina EPIC array).
    Supported clocks: grimAge, dunedinPACE, horvath, hannum, phenoAgeDNAm
    """
    clock_values: Dict[str, float] = Field(
        ...,
        description="Clock name -> value. e.g. {'grimAge': 65.0, 'dunedinPACE': 1.12}",
        example={"grimAge": 65.0, "dunedinPACE": 1.12},
    )
    chronological_age: Optional[int] = Field(
        default=None,
        description="Chronological age in years (used for acceleration calculation)",
    )


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
    epigenetic_clocks: Optional[Dict[str, float]] = Field(
        default=None,
        description="Pre-computed epigenetic clock values (grimAge, dunedinPACE, etc.)"
    )


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


@router.post("/epigenetic_clock")
async def epigenetic_clock(body: EpigeneticClockRequest) -> Dict[str, Any]:
    """
    Normalize pre-computed epigenetic clock values against published population references (RUO).

    Accepts values from external methylation array analysis.
    Returns clock_acceleration, pace_interpretation, and hallmark_implications.
    """
    from .services.epigenetic_clock_service import score_epigenetic_clocks
    return score_epigenetic_clocks(body.clock_values, body.chronological_age)


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
        # Try packaged path first (editable install with repo root on sys.path),
        # then fall back to bare 'agents' module (repo root on PYTHONPATH)
        try:
            from longivity.agents import get_longevity_graph, PatientState
        except ModuleNotFoundError:
            from agents import get_longevity_graph, PatientState  # type: ignore[no-redef]
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
        "epigenetic_clocks": body.epigenetic_clocks,
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
        "audit_log": [],
        "pipeline_health": None,
        "epigenetic_clock_result": None,
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
        # Register run for status polling
        audit_log = final_state.get("audit_log") or []
        pipeline_health = final_state.get("pipeline_health") or {}
        _register_run(run_id, audit_log, pipeline_health)
        report["audit_log"] = audit_log
        report["pipeline_health"] = pipeline_health
        report["run_id"] = run_id
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent pipeline error: {e}")


@router.get("/pipeline/status/{run_id}")
async def pipeline_status(run_id: str) -> Dict[str, Any]:
    """Return audit_log and pipeline_health for a completed run (TTL: 1 hour)."""
    with _REGISTRY_LOCK:
        _evict_expired()
        record = _RUN_REGISTRY.get(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found or expired.")
    return record




# ─────────────────────────────────────────────────────────────────────────────
# N-of-1 Trial Engine
# ─────────────────────────────────────────────────────────────────────────────

class Nof1Request(BaseModel):
    patient_id: str = Field(default="ANON", description="De-identified patient ID")
    age: int = Field(..., ge=18, le=120)
    biomarkers: Dict[str, float] = Field(..., description="Current biomarker values (canonical keys)")
    compound_id: str = Field(..., description="Compound to test (e.g. omega_3, berberine)")
    compound_display_name: Optional[str] = None
    dose_info: Optional[Dict[str, Any]] = None
    crossover_compound_id: Optional[str] = Field(
        default=None,
        description="Optional second compound for crossover arm"
    )
    notes: Optional[str] = None


@router.post("/nof1/protocol")
async def nof1_protocol(body: Nof1Request) -> Dict[str, Any]:
    """
    Generate a personalized N-of-1 trial protocol for a given compound.

    Returns a complete 4-phase crossover design (Baseline → Treatment → Washout → Re-measure)
    with expected biomarker deltas, monitoring schedule, and MR causal anchor if available.
    """
    from .services.nof1_trial_engine import generate_nof1_protocol
    return generate_nof1_protocol(
        patient_id=body.patient_id,
        age=body.age,
        baseline_biomarkers=body.biomarkers,
        compound_id=body.compound_id,
        compound_display_name=body.compound_display_name,
        dose_info=body.dose_info,
        crossover_compound_id=body.crossover_compound_id,
        notes=body.notes,
    )

@router.get("/healthz")
async def healthz() -> Dict[str, Any]:
    return {"status": "ok", "service": "longivity", "version": "0.2.0"}
