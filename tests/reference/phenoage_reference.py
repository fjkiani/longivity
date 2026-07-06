"""
Clean-room reference implementation of PhenoAge (Levine 2018, PMID 29676998).

This is an INDEPENDENT reimplementation from the published paper's coefficients
(Table 1 / Supplementary Table S1 / Supplementary Methods). It is NOT derived
from the system under test (src/longivity/services/longevity_phenoage_level0.py).

Key formula details (from Supplementary Methods):
  - t is in MONTHS (120 months = 10 years)
  - CRP is ln(mg/dL), NOT ln(mg/L + 1)
  - PhenoAge calibration: 141.50225 + ln(-0.00553 * ln(1 - MortalityScore)) / 0.090165

Purpose: provide an external ground truth for regression testing. If the system
under test diverges from this reference by more than ±0.5 years on any input,
that is a formula bug, not a test calibration issue.

Usage:
    from tests.reference.phenoage_reference import compute_phenoage_reference
    result = compute_phenoage_reference(
        age=58,
        albumin_g_dl=4.0,       # g/dL  (converted to g/L internally)
        creatinine_mg_dl=1.1,   # mg/dL (converted to umol/L internally)
        glucose_mg_dl=142.0,    # mg/dL (converted to mmol/L internally)
        crp_mg_l=4.8,           # mg/L  (converted to mg/dL, then ln)
        lymphocyte_pct=21.0,    # %
        mcv=94.0,               # fL
        rdw=15.2,               # %
        alkaline_phosphatase=95.0,  # U/L
        wbc=9.2,                # 10^9/L
    )
    # result["phenoage"] -> float (years)
    # result["mortality_10yr"] -> float (0-1)
    # result["age_acceleration"] -> float (years)
"""
from __future__ import annotations
import math
from typing import Optional


# ── Published coefficients (Levine 2018, Table 1 / Supplementary Table S1) ──
_INTERCEPT = -19.9067

_COEF = {
    "albumin_g_l":          -0.0336,
    "creatinine_umol_l":     0.0095,
    "glucose_mmol_l":        0.1953,
    "ln_crp_mg_dl":          0.0954,   # ln(CRP in mg/dL) — Supplementary Methods
    "lymphocyte_pct":       -0.0120,
    "mcv_fl":                0.0268,
    "rdw_pct":               0.3306,
    "alkaline_phosphatase":  0.00188,
    "wbc_e9_l":              0.0554,
    "age":                   0.0804,
}

# Gompertz parameters (Supplementary Methods)
_GAMMA = 0.0076927          # per month
_T_MONTHS = 120.0           # 10-year horizon in months

# PhenoAge calibration constants (Supplementary Methods, step 4)
_PA_OFFSET = 141.50225
_PA_LN_COEF = -0.00553
_PA_DENOM = 0.090165

# Unit conversion constants
_ALBUMIN_GDL_TO_GL = 10.0           # g/dL → g/L
_CREATININE_MGDL_TO_UMOLL = 88.42   # mg/dL → µmol/L
_GLUCOSE_MGDL_TO_MMOLL = 1.0 / 18.018  # mg/dL → mmol/L
_CRP_MGL_TO_MGDL = 0.1             # mg/L → mg/dL (÷10)


def compute_phenoage_reference(
    age: float,
    albumin_g_dl: float,
    creatinine_mg_dl: float,
    glucose_mg_dl: float,
    crp_mg_l: float,
    lymphocyte_pct: float,
    mcv: float,
    rdw: float,
    alkaline_phosphatase: float,
    wbc: float,
) -> dict:
    """
    Compute PhenoAge from the 9 biomarkers using published Levine 2018 coefficients.

    All inputs in US clinical units (g/dL, mg/dL, mg/L, %, fL, U/L, 10^9/L).
    Returns dict with phenoage (years), age_acceleration (years), mortality_10yr (0-1).
    """
    # Unit conversions to canonical Levine 2018 units
    albumin_g_l = albumin_g_dl * _ALBUMIN_GDL_TO_GL
    creatinine_umol_l = creatinine_mg_dl * _CREATININE_MGDL_TO_UMOLL
    glucose_mmol_l = glucose_mg_dl * _GLUCOSE_MGDL_TO_MMOLL
    crp_mg_dl = crp_mg_l * _CRP_MGL_TO_MGDL
    ln_crp = math.log(crp_mg_dl)  # natural log of CRP in mg/dL

    # Linear combination (xb)
    xb = (
        _INTERCEPT
        + _COEF["albumin_g_l"]          * albumin_g_l
        + _COEF["creatinine_umol_l"]    * creatinine_umol_l
        + _COEF["glucose_mmol_l"]       * glucose_mmol_l
        + _COEF["ln_crp_mg_dl"]         * ln_crp
        + _COEF["lymphocyte_pct"]       * lymphocyte_pct
        + _COEF["mcv_fl"]               * mcv
        + _COEF["rdw_pct"]              * rdw
        + _COEF["alkaline_phosphatase"] * alkaline_phosphatase
        + _COEF["wbc_e9_l"]             * wbc
        + _COEF["age"]                  * age
    )

    # 10-year mortality score (t in months, Supplementary Methods)
    mortality_10yr = 1.0 - math.exp(
        -math.exp(xb) * (math.exp(_GAMMA * _T_MONTHS) - 1.0) / _GAMMA
    )
    mortality_10yr = max(0.0, min(1.0, mortality_10yr))

    # PhenoAge calibration (Supplementary Methods, step 4)
    # PhenoAge = 141.50225 + ln(-0.00553 * ln(1 - MortalityScore)) / 0.090165
    phenoage = _PA_OFFSET + math.log(_PA_LN_COEF * math.log(1.0 - mortality_10yr)) / _PA_DENOM
    age_acceleration = phenoage - age

    return {
        "phenoage": round(phenoage, 4),
        "age_acceleration": round(age_acceleration, 4),
        "mortality_10yr": round(mortality_10yr, 6),
        "xb": round(xb, 6),
        "inputs_converted": {
            "albumin_g_l": round(albumin_g_l, 3),
            "creatinine_umol_l": round(creatinine_umol_l, 3),
            "glucose_mmol_l": round(glucose_mmol_l, 4),
            "crp_mg_dl": round(crp_mg_dl, 4),
            "ln_crp": round(ln_crp, 4),
        },
    }


# ── Canonical spot-checks against system outputs ─────────────────────────────
# These verify the reference agrees with the system under test to within ±0.5yr.
# If they diverge, one has a formula bug.
CANONICAL_CHECKS = [
    {
        "name": "Marcus (T2D, 58M)",
        "inputs": dict(age=58, albumin_g_dl=4.0, creatinine_mg_dl=1.1, glucose_mg_dl=142.0,
                       crp_mg_l=4.8, lymphocyte_pct=21.0, mcv=94.0, rdw=15.2,
                       alkaline_phosphatase=95.0, wbc=9.2),
        "system_phenoage": 73.57,
    },
    {
        "name": "Robert (CVD, 63M)",
        "inputs": dict(age=63, albumin_g_dl=3.9, creatinine_mg_dl=1.3, glucose_mg_dl=118.0,
                       crp_mg_l=6.2, lymphocyte_pct=19.0, mcv=96.0, rdw=15.8,
                       alkaline_phosphatase=105.0, wbc=10.1),
        "system_phenoage": 81.47,
    },
    {
        "name": "Elena (APOE, 52F)",
        "inputs": dict(age=52, albumin_g_dl=4.9, creatinine_mg_dl=0.78, glucose_mg_dl=82.0,
                       crp_mg_l=0.3, lymphocyte_pct=35.0, mcv=87.0, rdw=12.2,
                       alkaline_phosphatase=48.0, wbc=4.8),
        "system_phenoage": 33.1,
    },
    {
        "name": "Dorothy (Frailty, 71F)",
        "inputs": dict(age=71, albumin_g_dl=3.7, creatinine_mg_dl=0.72, glucose_mg_dl=104.0,
                       crp_mg_l=3.1, lymphocyte_pct=20.0, mcv=93.0, rdw=14.9,
                       alkaline_phosphatase=88.0, wbc=8.4),
        "system_phenoage": 75.81,
    },
    {
        "name": "James (Centenarian, 68M)",
        "inputs": dict(age=68, albumin_g_dl=4.7, creatinine_mg_dl=0.82, glucose_mg_dl=84.0,
                       crp_mg_l=0.2, lymphocyte_pct=34.0, mcv=87.0, rdw=12.1,
                       alkaline_phosphatase=50.0, wbc=4.9),
        "system_phenoage": 48.17,
    },
]


if __name__ == "__main__":
    print("=" * 65)
    print("PHENOAGE REFERENCE IMPLEMENTATION — SPOT CHECKS")
    print("Levine 2018, PMID 29676998 (Supplementary Methods)")
    print("=" * 65)
    all_pass = True
    for check in CANONICAL_CHECKS:
        ref = compute_phenoage_reference(**check["inputs"])
        delta = abs(ref["phenoage"] - check["system_phenoage"])
        status = "✓" if delta <= 0.5 else "✗ DIVERGENCE"
        if delta > 0.5:
            all_pass = False
        print(f"  {status} {check['name']}")
        print(f"     Reference: {ref['phenoage']:.2f}yr  |  System: {check['system_phenoage']:.2f}yr  |  Δ={delta:.3f}yr")
        print(f"     Accel: {ref['age_acceleration']:+.2f}yr  |  10yr mortality: {ref['mortality_10yr']*100:.1f}%")
    print()
    print(f"All within ±0.5yr: {'YES ✓' if all_pass else 'NO ✗ — formula divergence detected'}")
    print("=" * 65)
