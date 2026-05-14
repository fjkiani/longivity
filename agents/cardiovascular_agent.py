from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from .state import PatientState

# ─────────────────────────────────────────────────────────────────────────────
# Pooled Cohort Equations (PCE) — PMID 24222018
# Goff DC Jr et al. JACC 2014;63(25 Pt B):2935-59
# Coefficients from Table A (Supplement) — use exactly as published.
# ─────────────────────────────────────────────────────────────────────────────

_PCE_COEFFICIENTS: Dict[str, Dict[str, float]] = {
    # ── White Women ──────────────────────────────────────────────────────────
    "white_female": {
        "ln_age":                  -7.990,
        "ln_total_chol":            4.475,
        "ln_age_x_total_chol":     -0.914,
        "ln_hdl":                  -7.275,
        "ln_age_x_hdl":             1.795,
        "ln_treated_sbp":           4.884,
        "ln_age_x_treated_sbp":    -1.665,
        "ln_untreated_sbp":         2.019,
        "ln_age_x_untreated_sbp":   0.0,
        "current_smoker":           7.574,
        "ln_age_x_smoker":         -1.665,
        "diabetes":                 0.661,
        "mean_coef_sum":          -29.799,
        "baseline_survival":        0.9665,
    },
    # ── White Men ────────────────────────────────────────────────────────────
    "white_male": {
        "ln_age":                  12.344,
        "ln_total_chol":           11.853,
        "ln_age_x_total_chol":     -2.664,
        "ln_hdl":                  -7.990,
        "ln_age_x_hdl":             1.769,
        "ln_treated_sbp":           1.797,
        "ln_age_x_treated_sbp":     0.0,
        "ln_untreated_sbp":         1.764,
        "ln_age_x_untreated_sbp":   0.0,
        "current_smoker":           7.837,
        "ln_age_x_smoker":         -1.795,
        "diabetes":                 0.658,
        "mean_coef_sum":           61.18,
        "baseline_survival":        0.9144,
    },
    # ── African-American Women ────────────────────────────────────────────────
    "aa_female": {
        "ln_age":                  17.1141,
        "ln_total_chol":            0.9396,
        "ln_age_x_total_chol":      0.0,      # not published for AA women
        "ln_hdl":                 -18.9196,
        "ln_age_x_hdl":             0.0,      # not published for AA women
        "ln_treated_sbp":          29.2907,
        "ln_age_x_treated_sbp":     0.0,
        "ln_untreated_sbp":        27.8197,
        "ln_age_x_untreated_sbp":   0.0,
        "current_smoker":           0.8738,
        "ln_age_x_smoker":          0.0,
        "diabetes":                 0.8738,
        "mean_coef_sum":           86.6081,
        "baseline_survival":        0.9533,
    },
    # ── African-American Men ──────────────────────────────────────────────────
    "aa_male": {
        "ln_age":                   2.469,
        "ln_total_chol":            0.302,
        "ln_age_x_total_chol":      0.0,      # not published for AA men
        "ln_hdl":                  -0.307,
        "ln_age_x_hdl":             0.0,      # not published for AA men
        "ln_treated_sbp":           1.916,
        "ln_age_x_treated_sbp":     0.0,
        "ln_untreated_sbp":         1.809,
        "ln_age_x_untreated_sbp":   0.0,
        "current_smoker":           0.549,
        "ln_age_x_smoker":          0.0,
        "diabetes":                 0.645,
        "mean_coef_sum":           19.54,
        "baseline_survival":        0.8954,
    },
}

_RISK_CATEGORIES = [
    (0.05,  "LOW",          "< 5%"),
    (0.075, "BORDERLINE",   "5% – 7.5%"),
    (0.20,  "INTERMEDIATE", "7.5% – 20%"),
    (1.01,  "HIGH",         "≥ 20%"),
]


def _risk_category(risk: float) -> str:
    for threshold, label, _ in _RISK_CATEGORIES:
        if risk < threshold:
            return label
    return "HIGH"


def _select_cohort(sex: str, race: str) -> str:
    """Map sex + race to PCE cohort key."""
    s = sex.strip().upper()
    r = race.strip().lower()
    is_aa = r in ("aa", "african_american", "african american", "black")
    if s in ("F", "FEMALE"):
        return "aa_female" if is_aa else "white_female"
    return "aa_male" if is_aa else "white_male"


def compute_pce_risk(
    age: float,
    sex: str,
    total_cholesterol: float,
    hdl_cholesterol: float,
    systolic_bp: float,
    bp_treatment: bool,
    diabetes: bool,
    smoker: bool,
    race: str = "white",
) -> Dict[str, Any]:
    """
    Compute 10-year ASCVD risk using the Pooled Cohort Equations.

    Returns dict with 10yr_ascvd_risk, risk_category, inputs_used, caveat.
    """
    cohort = _select_cohort(sex, race)
    c = _PCE_COEFFICIENTS[cohort]

    ln_age = math.log(age)
    ln_tc = math.log(total_cholesterol)
    ln_hdl = math.log(hdl_cholesterol)
    ln_sbp = math.log(systolic_bp)

    individual_sum = (
        c["ln_age"] * ln_age
        + c["ln_total_chol"] * ln_tc
        + c["ln_age_x_total_chol"] * ln_age * ln_tc
        + c["ln_hdl"] * ln_hdl
        + c["ln_age_x_hdl"] * ln_age * ln_hdl
        + (c["ln_treated_sbp"] * ln_sbp + c["ln_age_x_treated_sbp"] * ln_age * ln_sbp
           if bp_treatment else
           c["ln_untreated_sbp"] * ln_sbp + c["ln_age_x_untreated_sbp"] * ln_age * ln_sbp)
        + c["current_smoker"] * (1.0 if smoker else 0.0)
        + c["ln_age_x_smoker"] * ln_age * (1.0 if smoker else 0.0)
        + c["diabetes"] * (1.0 if diabetes else 0.0)
    )

    exponent = individual_sum - c["mean_coef_sum"]
    risk = 1.0 - c["baseline_survival"] ** math.exp(exponent)
    risk = max(0.0, min(1.0, risk))

    return {
        "10yr_ascvd_risk": round(risk, 6),
        "10yr_ascvd_risk_pct": round(risk * 100, 2),
        "risk_category": _risk_category(risk),
        "cohort_used": cohort,
        "individual_sum": round(individual_sum, 6),
        "inputs_used": {
            "age": age,
            "sex": sex,
            "race": race,
            "total_cholesterol_mgdl": total_cholesterol,
            "hdl_cholesterol_mgdl": hdl_cholesterol,
            "systolic_bp_mmhg": systolic_bp,
            "bp_treatment": bp_treatment,
            "diabetes": diabetes,
            "smoker": smoker,
        },
        "missing_inputs": [],
        "caveat": (
            "Pooled Cohort Equations (PMID 24222018). Validated for ages 40–79, "
            "non-Hispanic White and African-American adults. "
            "Research Use Only — not a substitute for clinical cardiovascular risk assessment."
        ),
        "source_pmid": "24222018",
    }


def cardiovascular_agent(state: PatientState) -> PatientState:
    """
    Computes 10-year ASCVD risk using the Pooled Cohort Equations.

    Reads from state["current_input"]. Gracefully handles missing lipids/SBP
    by returning a partial result with caveat.
    """
    ci: Dict[str, Any] = state.get("current_input", {})
    bio: Dict[str, Any] = ci.get("biomarkers", {})
    errors = list(state.get("errors", []))
    agents_run = list(state.get("agents_run", []))

    # ── Extract inputs ────────────────────────────────────────────────────────
    age = ci.get("age") or ci.get("chronological_age") or state.get("age")
    sex = ci.get("sex") or state.get("sex") or ""
    race = ci.get("race", "white")

    total_chol = bio.get("total_cholesterol")
    hdl = bio.get("hdl_cholesterol")
    sbp = bio.get("systolic_bp") or bio.get("systolic_blood_pressure")
    bp_treatment = bool(bio.get("bp_treatment", False) or ci.get("bp_treatment", False))
    diabetes = bool(bio.get("diabetes", False) or ci.get("diabetes", False))
    smoker = bool(bio.get("smoker", False) or ci.get("smoker", False) or ci.get("current_smoker", False))

    missing: List[str] = []
    if age is None:
        missing.append("age")
    if not sex:
        missing.append("sex")
    if total_chol is None:
        missing.append("total_cholesterol")
    if hdl is None:
        missing.append("hdl_cholesterol")
    if sbp is None:
        missing.append("systolic_bp")

    # ── Partial result if critical inputs missing ─────────────────────────────
    if missing:
        partial_result: Dict[str, Any] = {
            "status": "PARTIAL",
            "10yr_ascvd_risk": None,
            "10yr_ascvd_risk_pct": None,
            "risk_category": None,
            "missing_inputs": missing,
            "inputs_used": {
                "age": age,
                "sex": sex,
                "race": race,
                "total_cholesterol_mgdl": total_chol,
                "hdl_cholesterol_mgdl": hdl,
                "systolic_bp_mmhg": sbp,
                "bp_treatment": bp_treatment,
                "diabetes": diabetes,
                "smoker": smoker,
            },
            "caveat": (
                f"Cardiovascular risk calculation incomplete — missing: {', '.join(missing)}. "
                "Provide age, sex, total cholesterol, HDL, and systolic BP for full PCE computation. "
                "Pooled Cohort Equations (PMID 24222018). Research Use Only."
            ),
            "source_pmid": "24222018",
        }
        state["cardiovascular_risk"] = partial_result
        agents_run.append("cardiovascular_agent_partial")
        state["agents_run"] = agents_run
        state["errors"] = errors
        return state

    # ── Full PCE computation ──────────────────────────────────────────────────
    try:
        result = compute_pce_risk(
            age=float(age),
            sex=str(sex),
            total_cholesterol=float(total_chol),
            hdl_cholesterol=float(hdl),
            systolic_bp=float(sbp),
            bp_treatment=bp_treatment,
            diabetes=diabetes,
            smoker=smoker,
            race=str(race),
        )
        result["status"] = "SUCCESS"
        state["cardiovascular_risk"] = result
    except Exception as e:
        errors.append(f"cardiovascular_agent: {e}")
        state["cardiovascular_risk"] = {
            "status": "ERROR",
            "error": str(e),
            "missing_inputs": missing,
            "caveat": "PCE computation failed — see errors.",
        }

    agents_run.append("cardiovascular_agent")
    state["agents_run"] = agents_run
    state["errors"] = errors
    return state
