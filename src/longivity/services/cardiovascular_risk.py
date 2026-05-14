"""
ASCVD 10-year risk — Pooled Cohort Equations (Goff et al. 2014, PMID 24222018).
Research Use Only. Not a clinical decision tool.
"""
from __future__ import annotations
import math
from typing import Any, Dict, Optional

# PCE coefficients — Table A in Goff et al. 2014 (PMID 24222018)
# Format: (ln_age, ln_total_chol, ln_age_x_total_chol, ln_hdl, ln_age_x_hdl,
#          ln_treated_sbp, ln_age_x_treated_sbp, ln_untreated_sbp, ln_age_x_untreated_sbp,
#          smoker, ln_age_x_smoker, diabetes, mean_coef_sum, baseline_survival)

PCE_COEFFICIENTS = {
    ("F", "white"): {
        "ln_age": -7.990, "ln_total_chol": 4.475, "ln_age_x_total_chol": -0.914,
        "ln_hdl": -7.275, "ln_age_x_hdl": 1.795,
        "ln_treated_sbp": 4.884, "ln_age_x_treated_sbp": -1.665,
        "ln_untreated_sbp": 2.019, "ln_age_x_untreated_sbp": 0.0,
        "smoker": 7.574, "ln_age_x_smoker": -1.665,
        "diabetes": 0.661,
        "mean_coef_sum": -29.799, "baseline_survival": 0.9665,
    },
    ("M", "white"): {
        "ln_age": 12.344, "ln_total_chol": 11.853, "ln_age_x_total_chol": -2.664,
        "ln_hdl": -7.990, "ln_age_x_hdl": 1.769,
        "ln_treated_sbp": 1.797, "ln_age_x_treated_sbp": 0.0,
        "ln_untreated_sbp": 1.764, "ln_age_x_untreated_sbp": 0.0,
        "smoker": 7.837, "ln_age_x_smoker": -1.795,
        "diabetes": 0.658,
        "mean_coef_sum": 61.18, "baseline_survival": 0.9144,
    },
    ("F", "aa"): {
        "ln_age": 17.1141, "ln_total_chol": 0.9396, "ln_age_x_total_chol": 0.0,
        "ln_hdl": -18.9196, "ln_age_x_hdl": 4.4748,
        "ln_treated_sbp": 29.2907, "ln_age_x_treated_sbp": -6.4321,
        "ln_untreated_sbp": 27.8197, "ln_age_x_untreated_sbp": -6.0873,
        "smoker": 0.8738, "ln_age_x_smoker": 0.0,
        "diabetes": 0.8738,
        "mean_coef_sum": 86.6081, "baseline_survival": 0.9533,
    },
    ("M", "aa"): {
        "ln_age": 2.469, "ln_total_chol": 0.302, "ln_age_x_total_chol": 0.0,
        "ln_hdl": -0.307, "ln_age_x_hdl": 0.0,
        "ln_treated_sbp": 1.916, "ln_age_x_treated_sbp": 0.0,
        "ln_untreated_sbp": 1.809, "ln_age_x_untreated_sbp": 0.0,
        "smoker": 0.549, "ln_age_x_smoker": 0.0,
        "diabetes": 0.645,
        "mean_coef_sum": 19.54, "baseline_survival": 0.8954,
    },
}

def _risk_category(risk: float) -> str:
    if risk < 0.05: return "LOW"
    if risk < 0.075: return "BORDERLINE"
    if risk < 0.20: return "INTERMEDIATE"
    return "HIGH"

def compute_ascvd_risk(
    age: int,
    sex: str,  # "M" or "F"
    total_cholesterol: float,  # mg/dL
    hdl_cholesterol: float,    # mg/dL
    systolic_bp: float,        # mmHg
    bp_treatment: bool = False,
    diabetes: bool = False,
    smoker: bool = False,
    race: str = "white",       # "white" or "aa"
) -> Dict[str, Any]:
    """Compute 10-year ASCVD risk using Pooled Cohort Equations."""
    race_key = "aa" if race.lower() in ("aa", "african_american", "black") else "white"
    sex_key = sex.upper()
    if sex_key not in ("M", "F"):
        return {"status": "ERROR", "error": "sex must be M or F"}

    coef = PCE_COEFFICIENTS.get((sex_key, race_key))
    if not coef:
        return {"status": "ERROR", "error": f"No coefficients for sex={sex_key} race={race_key}"}

    la = math.log(age)
    ltc = math.log(total_cholesterol)
    lhdl = math.log(hdl_cholesterol)
    lsbp = math.log(systolic_bp)

    ind_sum = (
        coef["ln_age"] * la
        + coef["ln_total_chol"] * ltc
        + coef["ln_age_x_total_chol"] * la * ltc
        + coef["ln_hdl"] * lhdl
        + coef["ln_age_x_hdl"] * la * lhdl
        + (coef["ln_treated_sbp"] * lsbp + coef["ln_age_x_treated_sbp"] * la * lsbp if bp_treatment else 0)
        + (coef["ln_untreated_sbp"] * lsbp + coef["ln_age_x_untreated_sbp"] * la * lsbp if not bp_treatment else 0)
        + coef["smoker"] * (1 if smoker else 0)
        + coef["ln_age_x_smoker"] * la * (1 if smoker else 0)
        + coef["diabetes"] * (1 if diabetes else 0)
    )

    risk = 1.0 - coef["baseline_survival"] ** math.exp(ind_sum - coef["mean_coef_sum"])
    risk = max(0.0, min(1.0, risk))

    return {
        "status": "SUCCESS",
        "ten_year_ascvd_risk": round(risk, 4),
        "ten_year_ascvd_risk_pct": round(risk * 100, 1),
        "risk_category": _risk_category(risk),
        "inputs": {
            "age": age, "sex": sex_key, "race": race_key,
            "total_cholesterol_mg_dl": total_cholesterol,
            "hdl_cholesterol_mg_dl": hdl_cholesterol,
            "systolic_bp_mmhg": systolic_bp,
            "bp_treatment": bp_treatment,
            "diabetes": diabetes,
            "smoker": smoker,
        },
        "provenance": "Pooled Cohort Equations — Goff et al. 2014 (PMID 24222018)",
        "disclaimer": "Research Use Only. PCE validated for ages 40-79 without prior CVD. Not a clinical decision tool.",
    }

def compute_ascvd_from_biomarkers(body: Dict[str, Any]) -> Dict[str, Any]:
    """Extract PCE inputs from a biomarker payload dict."""
    from longivity.services.longevity_phenoage_level0 import _coerce_float, _normalize_biomarker_keys

    age = body.get("age") or body.get("chronological_age")
    sex = body.get("sex")
    bio = _normalize_biomarker_keys(body.get("biomarkers") or {})

    if not age or not sex:
        return {
            "status": "INSUFFICIENT_DATA",
            "message": "age and sex required for ASCVD risk calculation",
            "missing": [k for k in ["age", "sex"] if not body.get(k)],
        }

    tc = _coerce_float(bio.get("total_cholesterol") or bio.get("total_chol"))
    hdl = _coerce_float(bio.get("hdl_cholesterol") or bio.get("hdl"))
    sbp = _coerce_float(bio.get("systolic_bp") or bio.get("sbp"))

    missing = []
    if tc is None: missing.append("total_cholesterol")
    if hdl is None: missing.append("hdl_cholesterol")
    if sbp is None: missing.append("systolic_bp")

    if missing:
        return {
            "status": "INSUFFICIENT_DATA",
            "message": f"Missing required inputs: {missing}",
            "missing": missing,
            "provided": {"age": age, "sex": sex},
        }

    bp_treatment = bool(body.get("bp_treatment") or bio.get("bp_treatment"))
    diabetes = bool(body.get("diabetes") or bio.get("diabetes"))
    smoker = bool(body.get("smoker") or bio.get("smoker"))
    race = str(body.get("race") or "white")

    return compute_ascvd_risk(
        age=int(age), sex=sex, total_cholesterol=tc, hdl_cholesterol=hdl,
        systolic_bp=sbp, bp_treatment=bp_treatment, diabetes=diabetes,
        smoker=smoker, race=race,
    )
