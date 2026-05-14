from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .state import PatientState

_STABLE_THRESHOLD = 0.05  # ±5% change → STABLE


def _direction(current: float, prior: float) -> str:
    """
    Determine direction of change.
    Uses ±5% threshold relative to prior value.
    Note: for some biomarkers (e.g. CRP, RDW) lower is better;
    for others (albumin, lymphocyte %) higher is better.
    We report raw direction here — interpretation is left to the report assembler.
    """
    if prior == 0:
        return "STABLE"
    pct_change = (current - prior) / abs(prior)
    if abs(pct_change) <= _STABLE_THRESHOLD:
        return "STABLE"
    return "IMPROVING" if pct_change < 0 else "WORSENING"


def _biomarker_direction_is_lower_better(key: str) -> bool:
    """
    Returns True if a lower value is generally better for this biomarker.
    Used to correctly label IMPROVING vs WORSENING.
    """
    lower_is_better = {
        "crp_log", "crp_mg_l", "hscrp", "rdw", "wbc", "glucose_mg_dl",
        "glucose_serum", "creatinine", "alkaline_phosphatase",
        "ldl_cholesterol", "triglycerides", "total_cholesterol",
        "il_6", "il6", "tnf_alpha", "tnfa",
        "hba1c", "hba1c_percent", "fasting_insulin",
    }
    return key.lower() in lower_is_better


def _smart_direction(key: str, current: float, prior: float) -> str:
    """Direction accounting for whether lower or higher is better."""
    if prior == 0:
        return "STABLE"
    pct_change = (current - prior) / abs(prior)
    if abs(pct_change) <= _STABLE_THRESHOLD:
        return "STABLE"
    went_down = pct_change < 0
    lower_better = _biomarker_direction_is_lower_better(key)
    if went_down and lower_better:
        return "IMPROVING"
    if went_down and not lower_better:
        return "WORSENING"
    if not went_down and lower_better:
        return "WORSENING"
    return "IMPROVING"


def _compute_biomarker_deltas(
    current_bio: Dict[str, Any],
    prior_bio: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Compute per-biomarker deltas for keys present in both visits."""
    deltas = []
    all_keys = set(current_bio.keys()) | set(prior_bio.keys())
    for key in sorted(all_keys):
        cur_val = current_bio.get(key)
        pri_val = prior_bio.get(key)
        if cur_val is None or pri_val is None:
            continue
        try:
            cur_f = float(cur_val)
            pri_f = float(pri_val)
        except (TypeError, ValueError):
            continue
        delta = cur_f - pri_f
        direction = _smart_direction(key, cur_f, pri_f)
        pct_change = round((delta / abs(pri_f)) * 100, 2) if pri_f != 0 else None
        deltas.append({
            "biomarker": key,
            "prior_value": pri_f,
            "current_value": cur_f,
            "delta": round(delta, 6),
            "pct_change": pct_change,
            "direction": direction,
        })
    return deltas


def _compute_phenoage_delta(
    current_phenoage: Optional[Dict[str, Any]],
    prior_phenoage: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Compute delta for PhenoAge estimate between visits."""
    if not current_phenoage or not prior_phenoage:
        return None
    cur_est = current_phenoage.get("phenoage_estimate")
    pri_est = prior_phenoage.get("phenoage_estimate")
    if cur_est is None or pri_est is None:
        return None
    try:
        cur_f = float(cur_est)
        pri_f = float(pri_est)
    except (TypeError, ValueError):
        return None
    delta = cur_f - pri_f
    # For PhenoAge: lower is better (younger biological age)
    if abs(delta) / max(abs(pri_f), 1e-9) <= _STABLE_THRESHOLD:
        direction = "STABLE"
    elif delta < 0:
        direction = "IMPROVING"
    else:
        direction = "WORSENING"
    return {
        "prior_phenoage_estimate": round(pri_f, 2),
        "current_phenoage_estimate": round(cur_f, 2),
        "delta_years": round(delta, 2),
        "direction": direction,
        "prior_age_acceleration": prior_phenoage.get("age_acceleration"),
        "current_age_acceleration": current_phenoage.get("age_acceleration"),
    }


def _compute_hallmark_deltas(
    current_hallmarks: Optional[Dict[str, Any]],
    prior_hallmarks: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Compute delta for each hallmark signal between visits."""
    if not current_hallmarks or not prior_hallmarks:
        return []
    deltas = []
    all_hallmarks = set(current_hallmarks.keys()) | set(prior_hallmarks.keys())
    for hm in sorted(all_hallmarks):
        cur_hm = current_hallmarks.get(hm, {})
        pri_hm = prior_hallmarks.get(hm, {})
        if not isinstance(cur_hm, dict) or not isinstance(pri_hm, dict):
            continue
        cur_signal = cur_hm.get("phenoage_signal") or cur_hm.get("supplementary_signal") or 0.0
        pri_signal = pri_hm.get("phenoage_signal") or pri_hm.get("supplementary_signal") or 0.0
        try:
            cur_f = float(cur_signal)
            pri_f = float(pri_signal)
        except (TypeError, ValueError):
            continue
        delta = cur_f - pri_f
        # Lower hallmark signal = less aging stress = improving
        if abs(delta) <= 0.05:
            direction = "STABLE"
        elif delta < 0:
            direction = "IMPROVING"
        else:
            direction = "WORSENING"
        deltas.append({
            "hallmark": hm,
            "prior_signal": round(pri_f, 4),
            "current_signal": round(cur_f, 4),
            "delta": round(delta, 4),
            "direction": direction,
        })
    return deltas


def _overall_trajectory(biomarker_deltas: List[Dict[str, Any]]) -> str:
    """
    Compute overall trajectory from biomarker deltas.
    IMPROVING / STABLE / WORSENING / MIXED based on majority.
    """
    if not biomarker_deltas:
        return "INSUFFICIENT_DATA"
    counts: Dict[str, int] = {"IMPROVING": 0, "STABLE": 0, "WORSENING": 0}
    for d in biomarker_deltas:
        direction = d.get("direction", "STABLE")
        if direction in counts:
            counts[direction] += 1
    total = sum(counts.values())
    if total == 0:
        return "INSUFFICIENT_DATA"
    improving = counts["IMPROVING"]
    worsening = counts["WORSENING"]
    stable = counts["STABLE"]
    # Majority rule with MIXED for contested cases
    if improving > worsening and improving > stable:
        return "IMPROVING"
    if worsening > improving and worsening > stable:
        return "WORSENING"
    if stable >= improving and stable >= worsening:
        return "STABLE"
    return "MIXED"


def longitudinal_agent(state: PatientState) -> PatientState:
    """
    Computes deltas between current visit and most recent prior visit.

    If visit_history has at least 1 prior entry:
      - Biomarker deltas (current - prior, direction)
      - PhenoAge estimate delta
      - Hallmark signal deltas
      - Days between visits
      - Overall trajectory

    If no prior history: sets longitudinal_delta to FIRST_VISIT status.
    """
    visit_history: List[Any] = state.get("visit_history", []) or []
    errors = list(state.get("errors", []))
    agents_run = list(state.get("agents_run", []))

    if not visit_history:
        state["longitudinal_delta"] = {
            "status": "FIRST_VISIT",
            "message": "No prior visit data for comparison",
        }
        agents_run.append("longitudinal_agent")
        state["agents_run"] = agents_run
        state["errors"] = errors
        return state

    # ── Get most recent prior visit ───────────────────────────────────────────
    prior_visit = visit_history[-1]
    current_input: Dict[str, Any] = state.get("current_input", {})

    # ── Days between visits ───────────────────────────────────────────────────
    days_between: Optional[int] = None
    try:
        prior_ts = prior_visit.get("timestamp", "")
        current_ts = state.get("timestamp", "")
        if prior_ts and current_ts:
            prior_dt = datetime.fromisoformat(prior_ts.replace("Z", "+00:00"))
            current_dt = datetime.fromisoformat(current_ts.replace("Z", "+00:00"))
            days_between = (current_dt - prior_dt).days
    except Exception as e:
        errors.append(f"longitudinal_agent.days_between: {e}")

    # ── Biomarker deltas ──────────────────────────────────────────────────────
    current_bio: Dict[str, Any] = current_input.get("biomarkers", {}) or {}
    prior_bio: Dict[str, Any] = prior_visit.get("biomarkers", {}) or {}
    biomarker_deltas: List[Dict[str, Any]] = []
    try:
        biomarker_deltas = _compute_biomarker_deltas(current_bio, prior_bio)
    except Exception as e:
        errors.append(f"longitudinal_agent.biomarker_deltas: {e}")

    # ── PhenoAge delta ────────────────────────────────────────────────────────
    phenoage_delta: Optional[Dict[str, Any]] = None
    try:
        prior_assessment = prior_visit.get("assessment_result") or {}
        prior_phenoage = prior_assessment.get("phenoage_analysis") or prior_assessment.get("phenoage_result")
        current_phenoage = state.get("phenoage_result")
        phenoage_delta = _compute_phenoage_delta(current_phenoage, prior_phenoage)
    except Exception as e:
        errors.append(f"longitudinal_agent.phenoage_delta: {e}")

    # ── Hallmark deltas ───────────────────────────────────────────────────────
    hallmark_deltas: List[Dict[str, Any]] = []
    try:
        prior_assessment = prior_visit.get("assessment_result") or {}
        prior_hallmarks = prior_assessment.get("hallmark_narrative") or prior_assessment.get("hallmark_result")
        current_hallmarks = state.get("hallmark_result")
        hallmark_deltas = _compute_hallmark_deltas(current_hallmarks, prior_hallmarks)
    except Exception as e:
        errors.append(f"longitudinal_agent.hallmark_deltas: {e}")

    # ── Overall trajectory ────────────────────────────────────────────────────
    trajectory = _overall_trajectory(biomarker_deltas)

    state["longitudinal_delta"] = {
        "status": "SUCCESS",
        "days_between_visits": days_between,
        "prior_visit_timestamp": prior_visit.get("timestamp"),
        "current_visit_timestamp": state.get("timestamp"),
        "trajectory": trajectory,
        "biomarker_deltas": biomarker_deltas,
        "biomarkers_compared": len(biomarker_deltas),
        "phenoage_delta": phenoage_delta,
        "hallmark_deltas": hallmark_deltas,
        "summary": {
            "improving": sum(1 for d in biomarker_deltas if d["direction"] == "IMPROVING"),
            "stable": sum(1 for d in biomarker_deltas if d["direction"] == "STABLE"),
            "worsening": sum(1 for d in biomarker_deltas if d["direction"] == "WORSENING"),
        },
    }

    agents_run.append("longitudinal_agent")
    state["agents_run"] = agents_run
    state["errors"] = errors
    return state
