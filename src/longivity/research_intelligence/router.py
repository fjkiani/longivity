"""
Research Intelligence API Router — Decision-Grade Intelligence Endpoint.

Endpoints:
  POST /api/v1/research-intelligence/intelligence  — full pipeline with persona + value_synthesis
  POST /api/v1/research-intelligence/research      — legacy endpoint (backward compat)
  GET  /api/v1/research-intelligence/health        — health check

Key upgrades over the stub:
  - persona field ("patient" | "doctor" | "r&d") routes value_synthesis output
  - value_synthesizer called post-orchestration and included in response
  - query_id (UUID) generated and returned (no DB persistence yet)
  - confidence_breakdown surfaced from synthesized_findings
  - context passed through to orchestrator for disease-aware LLM prompt
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .orchestrator import ResearchIntelligenceOrchestrator
from .value_synthesizer import ValueSynthesizer

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/research-intelligence",
    tags=["research-intelligence"],
)

# Singletons — instantiated once at module load
_orch: Optional[ResearchIntelligenceOrchestrator] = None
_synthesizer: Optional[ValueSynthesizer] = None


def _get_orch() -> ResearchIntelligenceOrchestrator:
    global _orch
    if _orch is None:
        _orch = ResearchIntelligenceOrchestrator()
    return _orch


def _get_synthesizer() -> ValueSynthesizer:
    global _synthesizer
    if _synthesizer is None:
        _synthesizer = ValueSynthesizer()
    return _synthesizer


# ------------------------------------------------------------------
# Request / Response models
# ------------------------------------------------------------------

class ResearchContext(BaseModel):
    disease: str = Field(default="", description="Disease identifier, e.g. 'ovarian_cancer_hgs'")
    treatment_line: Optional[str] = Field(default=None, description="e.g. 'L1', 'L2', 'prevention'")
    biomarkers: Dict[str, Any] = Field(default_factory=dict, description="e.g. {'HRD': 'POSITIVE', 'BRCA2': 'HET'}")


class ResearchRequest(BaseModel):
    question: str = Field(..., description="Natural language research question")
    context: ResearchContext = Field(default_factory=ResearchContext)
    persona: str = Field(
        default="patient",
        description="Output persona: 'patient' | 'doctor' | 'r&d'",
    )
    portals: List[str] = Field(default=["pubmed"])
    synthesize: bool = Field(default=True)
    run_moat_analysis: bool = Field(default=True)


# Legacy request model (backward compat)
class LegacyResearchRequest(BaseModel):
    question: str
    context: Dict[str, Any] = Field(default_factory=dict)


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.get("/health")
async def health() -> Dict[str, Any]:
    """Health check — confirms orchestrator is available."""
    o = _get_orch()
    return {
        "ok": True,
        "available": o.is_available(),
        "version": "2.0.0",
        "features": ["moat_analysis", "confidence_scorer", "value_synthesis", "persona_routing"],
    }


@router.post("/intelligence")
async def research_intelligence(body: ResearchRequest) -> Dict[str, Any]:
    """
    Decision-grade research intelligence endpoint.

    Returns structured JSON with:
    - synthesized_findings: mechanisms with study_design, ic50_data, biomarker_relevance
    - synthesized_findings.overall_confidence: deterministic ConfidenceScorer output
    - synthesized_findings.confidence_breakdown: formula components
    - moat_analysis: pathways, treatment_line_analysis, biomarker_analysis (real MOAT, not stub)
    - value_synthesis: persona-routed "what this means" insights
    - query_id: UUID for this query run

    Example request (Scenario 1 — Diana Park):
    {
        "question": "What is the evidence for sulforaphane in BRCA2 heterozygous ovarian cancer prevention?",
        "context": {
            "disease": "ovarian_cancer_hgs",
            "treatment_line": "prevention",
            "biomarkers": {"BRCA2": "HET", "HRD": "POSITIVE"}
        },
        "persona": "patient"
    }
    """
    query_id = str(uuid.uuid4())
    o = _get_orch()

    # Build context dict for orchestrator (includes disease + biomarkers for LLM prompt)
    context_dict = {
        "disease": body.context.disease,
        "treatment_line": body.context.treatment_line,
        "biomarkers": body.context.biomarkers,
    }

    # Run full pipeline
    result = await o.research_question(
        question=body.question,
        context=context_dict,
    )

    # Run value synthesis (persona-routed)
    value_synthesis: Optional[Dict[str, Any]] = None
    if body.synthesize:
        try:
            synth = _get_synthesizer()
            value_synthesis = await synth.synthesize_insights(
                query_result=result,
                persona=body.persona,
            )
        except Exception as e:
            logger.warning("value_synthesis failed (non-blocking): %s", e)
            value_synthesis = None

    # Surface confidence_breakdown at top level for easy inspection
    synthesized = result.get("synthesized_findings", {})
    confidence_breakdown = synthesized.get("confidence_breakdown")

    return {
        "query_id": query_id,
        "persona": body.persona,
        **result,
        "value_synthesis": value_synthesis,
        # Convenience top-level fields
        "overall_confidence": synthesized.get("overall_confidence"),
        "evidence_tier": synthesized.get("evidence_tier"),
        "clinical_phase_ceiling": synthesized.get("clinical_phase_ceiling"),
        "confidence_breakdown": confidence_breakdown,
    }


@router.post("/research")
async def research_legacy(body: LegacyResearchRequest) -> Dict[str, Any]:
    """
    Legacy endpoint — backward compatible with existing callers.
    Passes through to orchestrator without persona or value_synthesis.
    """
    o = _get_orch()
    return await o.research_question(body.question, body.context)
