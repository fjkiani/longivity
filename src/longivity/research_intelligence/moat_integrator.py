"""
MOATIntegrator stub — referenced by orchestrator.py but not present in org.backend repo.

This stub returns empty/passthrough results so the orchestrator doesn't crash.
Replace with real implementation when the MOAT scoring layer is available.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class MOATIntegrator:
    """
    Stub implementation of the MOAT (Mechanism Of Action Targeting) integrator.
    
    The real implementation scores compounds/trials by mechanism-of-action fit
    against a patient's active hallmarks. This stub passes through without scoring.
    """

    def __init__(self):
        logger.debug("MOATIntegrator: using stub implementation")

    async def integrate_with_moat(
        self,
        research_results: dict,
        patient_context: dict | None = None,
        **kwargs,
    ) -> dict:
        """
        Stub: returns research_results unchanged with empty moat_scores.
        """
        return {
            **research_results,
            "moat_scores": {},
            "moat_note": "MOAT integration not yet implemented — stub passthrough",
        }

    async def rank_trials_by_mechanism_fit(
        self,
        trials: list,
        patient_hallmarks: list | None = None,
        **kwargs,
    ) -> list:
        """
        Stub: returns trials in original order without mechanism-fit ranking.
        """
        return trials

    async def score_compound_fit(
        self,
        compound_id: str,
        patient_hallmarks: list,
        **kwargs,
    ) -> dict:
        """
        Stub: returns neutral fit score.
        """
        return {
            "compound": compound_id,
            "fit_score": 0.5,
            "hallmark_coverage": [],
            "note": "MOAT scoring not yet implemented",
        }
