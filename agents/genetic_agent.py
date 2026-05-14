from __future__ import annotations
from typing import Any, Dict, Optional

from longivity.services.genetic_annotator import annotate_genetics
from longivity.services.dna_repair_scorer import score_dna_repair
from longivity.services.longevity_prs import score_parental_lifespan_prs

from .state import PatientState


def genetic_agent(state: PatientState) -> PatientState:
    """
    Runs genetic annotation + DNA repair scoring + parental lifespan PRS.

    Only executes if `variants` or `patient_genotype` are present in current_input.
    Stores results in:
      - state["genetic_result"]   — APOE / MTHFR / BRCA annotation
      - state["dna_repair_result"] — pathway-level DNA repair capacity
      - state["prs_result"]        — 27-SNP parental lifespan PRS
    """
    ci: Dict[str, Any] = state.get("current_input", {})
    variants: Optional[Dict[str, Any]] = ci.get("variants")
    patient_genotype: Optional[Dict[str, Any]] = ci.get("patient_genotype")

    # Guard: only run if genetics data is present
    if not variants and not patient_genotype:
        state["agents_run"] = state.get("agents_run", []) + ["genetic_agent_skipped"]
        return state

    errors = list(state.get("errors", []))
    agents_run = list(state.get("agents_run", []))

    # ── 1. Genetic annotation (APOE / MTHFR / BRCA) ──────────────────────────
    if variants:
        try:
            annotation_input = {
                "patient_id": state.get("patient_id"),
                "variants": variants,
            }
            state["genetic_result"] = annotate_genetics(annotation_input)
        except Exception as e:
            errors.append(f"genetic_agent.annotate_genetics: {e}")
            state["genetic_result"] = None
    else:
        state["genetic_result"] = None

    # ── 2. DNA repair capacity scoring ───────────────────────────────────────
    if patient_genotype:
        try:
            state["dna_repair_result"] = score_dna_repair(patient_genotype=patient_genotype)
        except Exception as e:
            errors.append(f"genetic_agent.score_dna_repair: {e}")
            state["dna_repair_result"] = None
    else:
        state["dna_repair_result"] = None

    # ── 3. Parental lifespan PRS ──────────────────────────────────────────────
    if variants:
        try:
            state["prs_result"] = score_parental_lifespan_prs(variants)
        except Exception as e:
            errors.append(f"genetic_agent.score_parental_lifespan_prs: {e}")
            state["prs_result"] = None
    else:
        state["prs_result"] = None

    agents_run.append("genetic_agent")
    state["agents_run"] = agents_run
    state["errors"] = errors
    return state
