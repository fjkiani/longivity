from __future__ import annotations
from typing import Any
from longivity.services.longevity_phenoage_level0 import run_longevity_assessment_level0
from .state import PatientState


def biomarker_agent(state: PatientState) -> PatientState:
    """Runs PhenoAge + hallmark scoring from biomarkers in current_input."""
    try:
        result = run_longevity_assessment_level0(state["current_input"])
        state["phenoage_result"] = result.get("phenoage_analysis")
        state["hallmark_result"] = result.get("hallmark_narrative")
        state["compound_result"] = result.get("compound_recommendations")
        state["agents_run"] = state.get("agents_run", []) + ["biomarker_agent"]
    except Exception as e:
        state["errors"] = state.get("errors", []) + [f"biomarker_agent: {e}"]
    return state
