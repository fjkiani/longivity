"""
N-of-1 Trial Agent — LangGraph node that generates personalized intervention protocols.

Reads compound recommendations from state (produced by biomarker_agent or gap_detection_agent),
selects the top MR_VALIDATED or RCT compound, and generates a complete N-of-1 trial protocol.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def nof1_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node: generate N-of-1 trial protocol for top compound recommendation.

    Reads from state:
      - state["patient_id"]
      - state["age"]
      - state["biomarkers"]
      - state["compound_recommendations"] (list, from hallmark scorer)

    Writes to state:
      - state["nof1_protocol"] — complete trial protocol dict
      - state["nof1_status"] — "generated" | "no_compounds" | "error"
    """
    try:
        from longivity.services.nof1_trial_engine import generate_nof1_protocol
    except ImportError:
        try:
            from src.longivity.services.nof1_trial_engine import generate_nof1_protocol
        except ImportError:
            logger.error("nof1_trial_engine not importable")
            return {**state, "nof1_status": "error", "nof1_protocol": None}

    patient_id = state.get("patient_id", "ANON")
    age = state.get("age", 0)
    biomarkers = state.get("biomarkers", {})
    compound_recs = state.get("compound_recommendations", [])

    if not compound_recs:
        logger.info("nof1_agent: no compound recommendations in state — skipping")
        return {**state, "nof1_status": "no_compounds", "nof1_protocol": None}

    # Prefer MR_VALIDATED > RCT > OBSERVATIONAL
    tier_order = {"MR_VALIDATED": 0, "RCT": 1, "OBSERVATIONAL": 2}
    sorted_recs = sorted(
        compound_recs,
        key=lambda r: (tier_order.get(r.get("evidence_tier", "OBSERVATIONAL"), 2), -float(r.get("overall_relevance") or 0)),
    )
    top = sorted_recs[0]
    compound_id = top.get("compound") or top.get("compound_id", "")
    display_name = top.get("display_name", compound_id)
    dose_info = top.get("dose")

    # Crossover: second-best compound if available
    crossover_id = None
    if len(sorted_recs) > 1:
        crossover_id = sorted_recs[1].get("compound") or sorted_recs[1].get("compound_id")

    try:
        protocol = generate_nof1_protocol(
            patient_id=patient_id,
            age=age,
            baseline_biomarkers=biomarkers,
            compound_id=compound_id,
            compound_display_name=display_name,
            dose_info=dose_info,
            crossover_compound_id=crossover_id,
        )
        logger.info(
            "nof1_agent: generated protocol %s for compound=%s tier=%s",
            protocol.get("trial_id"),
            compound_id,
            protocol.get("evidence_tier"),
        )
        return {**state, "nof1_status": "generated", "nof1_protocol": protocol}
    except Exception as exc:
        logger.exception("nof1_agent: error generating protocol: %s", exc)
        return {**state, "nof1_status": "error", "nof1_protocol": None, "nof1_error": str(exc)}
