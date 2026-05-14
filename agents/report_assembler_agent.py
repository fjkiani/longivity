"""
Report Assembler Agent — final node in the LangGraph longevity pipeline.

Assembles all upstream agent outputs into a unified patient report with:
- Biological age summary
- Hallmark summary
- Compound recommendations (deduplicated)
- Genetic profile
- Cardiovascular risk
- Wearable summary
- Longitudinal delta
- Gap detection results
- Prioritized action items
- Data completeness score (0–100)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .state import PatientState

# ─────────────────────────────────────────────────────────────────────────────
# Data completeness scoring rubric (total = 100 pts)
# ─────────────────────────────────────────────────────────────────────────────
_COMPLETENESS_RUBRIC = {
    "phenoage_complete":       25,  # All 9 PhenoAge biomarkers + age
    "lipid_panel":             10,  # LDL, HDL, or triglycerides present
    "genetics":                15,  # variants or patient_genotype provided
    "dna_repair":              10,  # patient_genotype provided (DNA repair panel)
    "wearables":               10,  # wearable data provided
    "body_composition":        10,  # DEXA / body composition data
    "deep_inflammation":        5,  # IL-6 or TNF-α present
    "hormones":                 5,  # DHEA-S, free testosterone, or IGF-1
    "epigenetic_clock":         5,  # DNAm age or epigenetic clock result
    "microbiome":               5,  # microbiome diversity score
}


def _compute_completeness_score(state: PatientState) -> Dict[str, Any]:
    """Compute 0–100 data completeness score based on filled data domains."""
    ci = state.get("current_input", {}) or {}
    bio_raw = ci.get("biomarkers", {}) or {}
    bio = {str(k).strip().replace("-", "_").replace("/", "_").lower(): v for k, v in bio_raw.items()}

    scores: Dict[str, int] = {}
    breakdown: Dict[str, bool] = {}

    # PhenoAge complete (9/9 + age)
    pa = state.get("phenoage_result") or {}
    completeness_mode = pa.get("completeness_mode", "")
    pa_complete = completeness_mode == "FULL_9BIOMARKERS_PLUS_AGE"
    breakdown["phenoage_complete"] = pa_complete
    scores["phenoage_complete"] = _COMPLETENESS_RUBRIC["phenoage_complete"] if pa_complete else 0

    # Lipid panel
    has_lipids = any(k in bio for k in ("ldl_cholesterol", "ldl", "hdl_cholesterol", "hdl", "triglycerides"))
    breakdown["lipid_panel"] = has_lipids
    scores["lipid_panel"] = _COMPLETENESS_RUBRIC["lipid_panel"] if has_lipids else 0

    # Genetics
    has_genetics = bool(ci.get("variants"))
    breakdown["genetics"] = has_genetics
    scores["genetics"] = _COMPLETENESS_RUBRIC["genetics"] if has_genetics else 0

    # DNA repair
    has_dna_repair = bool(ci.get("patient_genotype"))
    breakdown["dna_repair"] = has_dna_repair
    scores["dna_repair"] = _COMPLETENESS_RUBRIC["dna_repair"] if has_dna_repair else 0

    # Wearables
    has_wearables = bool(ci.get("wearables")) or bool(state.get("wearable_result"))
    breakdown["wearables"] = has_wearables
    scores["wearables"] = _COMPLETENESS_RUBRIC["wearables"] if has_wearables else 0

    # Body composition
    has_body_comp = bool(ci.get("body_composition")) or bool(state.get("body_composition_result"))
    breakdown["body_composition"] = has_body_comp
    scores["body_composition"] = _COMPLETENESS_RUBRIC["body_composition"] if has_body_comp else 0

    # Deep inflammation
    has_deep_inflam = any(k in bio for k in ("il_6", "il6", "tnf_alpha", "tnfa", "tnf_a"))
    breakdown["deep_inflammation"] = has_deep_inflam
    scores["deep_inflammation"] = _COMPLETENESS_RUBRIC["deep_inflammation"] if has_deep_inflam else 0

    # Hormones
    has_hormones = any(k in bio for k in ("dhea_s", "dheas", "free_testosterone", "igf1", "igf_1"))
    breakdown["hormones"] = has_hormones
    scores["hormones"] = _COMPLETENESS_RUBRIC["hormones"] if has_hormones else 0

    # Epigenetic clock
    has_epigenetic = any(k in bio for k in ("dnam_age", "grimage", "dunedinpace", "epigenetic_age",
                                             "horvath_age", "dnam_epigenetic_age"))
    breakdown["epigenetic_clock"] = has_epigenetic
    scores["epigenetic_clock"] = _COMPLETENESS_RUBRIC["epigenetic_clock"] if has_epigenetic else 0

    # Microbiome
    has_microbiome = any(k in bio for k in ("microbiome_diversity", "gut_diversity", "shannon_diversity"))
    breakdown["microbiome"] = has_microbiome
    scores["microbiome"] = _COMPLETENESS_RUBRIC["microbiome"] if has_microbiome else 0

    total = sum(scores.values())
    return {
        "total_score": total,
        "max_score": 100,
        "grade": _completeness_grade(total),
        "domain_breakdown": breakdown,
        "domain_scores": scores,
    }


def _completeness_grade(score: int) -> str:
    if score >= 80: return "COMPREHENSIVE"
    if score >= 60: return "GOOD"
    if score >= 40: return "MODERATE"
    if score >= 25: return "BASIC"
    return "MINIMAL"


def _build_action_items(state: PatientState) -> List[Dict[str, Any]]:
    """
    Build top-5 prioritized action items combining:
    1. HIGH-severity gaps (most important)
    2. PhenoAge top accelerators
    3. Genetic risk flags
    4. Worsening longitudinal trends
    """
    items: List[Dict[str, Any]] = []

    # 1. HIGH-severity gaps → action items
    gaps = state.get("detected_gaps") or []
    for gap in gaps:
        if gap.get("severity") == "HIGH" and len(items) < 3:
            items.append({
                "priority": len(items) + 1,
                "category": "data_gap",
                "summary": gap.get("message", "")[:120],
                "action": gap.get("recommended_action", ""),
                "data_needed": gap.get("data_needed", []),
                "source": "gap_detection_agent",
            })

    # 2. PhenoAge top accelerators
    pa = state.get("phenoage_result") or {}
    top_accel = pa.get("top_accelerators") or []
    for row in top_accel[:2]:
        if len(items) >= 5:
            break
        label = row.get("label") or row.get("biomarker") or "marker"
        accel = row.get("acceleration_status") or ""
        if accel == "ACCELERATING":
            items.append({
                "priority": len(items) + 1,
                "category": "phenoage_accelerator",
                "summary": f"Optimize {label} — currently accelerating biological age",
                "action": f"Review {label} with clinician; consider targeted intervention",
                "source": "biomarker_agent",
            })

    # 3. Genetic risk flags
    genetic = state.get("genetic_result") or {}
    apoe = genetic.get("apoe_status") or {}
    if isinstance(apoe, dict) and apoe.get("risk_tier") in ("ELEVATED", "HIGH_RISK"):
        if len(items) < 5:
            items.append({
                "priority": len(items) + 1,
                "category": "genetic_risk",
                "summary": f"APOE {apoe.get('genotype', '')} — {apoe.get('risk_tier', '')} cardiovascular/cognitive risk",
                "action": apoe.get("recommendation", "Discuss with clinician"),
                "source": "genetic_agent",
            })

    # 4. Worsening longitudinal trends
    ld = state.get("longitudinal_delta") or {}
    if ld.get("status") == "SUCCESS" and ld.get("trajectory") == "WORSENING":
        if len(items) < 5:
            pa_delta = ld.get("phenoage_delta") or {}
            delta_yrs = pa_delta.get("delta_years")
            msg = (
                f"Biological age increased {delta_yrs:.1f} years since last visit"
                if delta_yrs is not None
                else "Overall biomarker trajectory is worsening since last visit"
            )
            items.append({
                "priority": len(items) + 1,
                "category": "longitudinal_trend",
                "summary": msg,
                "action": "Review intervention protocol; identify worsening biomarkers",
                "source": "longitudinal_agent",
            })

    # 5. MEDIUM gaps if still under 5
    for gap in gaps:
        if len(items) >= 5:
            break
        if gap.get("severity") == "MEDIUM":
            items.append({
                "priority": len(items) + 1,
                "category": "data_gap",
                "summary": gap.get("message", "")[:120],
                "action": gap.get("recommended_action", ""),
                "data_needed": gap.get("data_needed", []),
                "source": "gap_detection_agent",
            })

    return items[:5]


def _extract_biological_age(state: PatientState) -> Dict[str, Any]:
    pa = state.get("phenoage_result") or {}
    return {
        "phenoage_estimate": pa.get("phenoage_estimate"),
        "mortality_score_10yr": pa.get("mortality_score_10yr"),
        "age_acceleration": pa.get("age_acceleration"),
        "age_years": pa.get("age_years"),
        "completeness_mode": pa.get("completeness_mode"),
        "top_accelerators": (pa.get("top_accelerators") or [])[:5],
    }


def report_assembler_agent(state: PatientState) -> PatientState:
    """Assembles all agent outputs into a unified patient report."""
    agents_run = list(state.get("agents_run", []))
    errors = list(state.get("errors", []))

    try:
        completeness = _compute_completeness_score(state)
        action_items = _build_action_items(state)
        biological_age = _extract_biological_age(state)

        report: Dict[str, Any] = {
            "status": "SUCCESS",
            "patient_id": state.get("patient_id"),
            "run_id": state.get("run_id"),
            "timestamp": state.get("timestamp"),

            # Core biological age
            "biological_age": biological_age,

            # Hallmarks
            "hallmark_summary": state.get("hallmark_result"),

            # Genetics
            "genetic_profile": state.get("genetic_result"),
            "dna_repair_capacity": state.get("dna_repair_result"),
            "longevity_prs": state.get("prs_result"),

            # Cardiovascular
            "cardiovascular_risk": state.get("cardiovascular_risk"),

            # Wearables + body composition
            "wearable_summary": state.get("wearable_result"),
            "body_composition_summary": state.get("body_composition_result"),

            # Compounds
            "compound_recommendations": state.get("compound_result") or [],

            # Longitudinal
            "longitudinal_delta": state.get("longitudinal_delta"),

            # Gaps
            "detected_gaps": state.get("detected_gaps") or [],
            "gap_priority_order": state.get("gap_priority_order") or [],

            # Prioritized actions
            "action_items": action_items,

            # Completeness
            "data_completeness": completeness,
            "data_completeness_score": completeness["total_score"],

            # Provenance
            "agents_run": agents_run + ["report_assembler_agent"],
            "errors": errors,

            "disclaimer": (
                "Research Use Only. Biological age estimation follows published PhenoAge transforms. "
                "Acceleration labels are CrisPRO UX thresholds, not PhenoAge classifications. "
                "Do not use for clinical decisions without a qualified clinician."
            ),
        }

        state["final_report"] = report
        agents_run.append("report_assembler_agent")
        state["agents_run"] = agents_run

    except Exception as e:
        errors.append(f"report_assembler_agent: {e}")
        state["errors"] = errors
        state["final_report"] = {
            "status": "ERROR",
            "error": str(e),
            "agents_run": agents_run,
        }

    return state
