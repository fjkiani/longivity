"""
API Correctness Eval — deterministic, CI-safe.

Runs all core system functions and validates outputs against expected ranges.
No LLM calls. No external dependencies beyond the installed package.

Usage:
    PYTHONPATH=/workspace/longivity python tests/eval/run_api_eval.py
    PYTHONPATH=/workspace/longivity python tests/eval/run_api_eval.py --ci-mode
"""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from longivity.services.longevity_phenoage_level0 import run_longevity_assessment_level0
from longivity.services.cardiovascular_risk import compute_ascvd_from_biomarkers
from longivity.services.wearable_service import score_wearables
from longivity.services.longitudinal_service import compute_longitudinal_delta
from longivity.services.nutrition_service import NutritionService

HEALTHY_BIO = {
    "albumin": 4.8, "creatinine": 0.85, "glucose_mg_dl": 88.0,
    "crp_mg_l": 0.4, "lymphocyte_percent": 32.0, "mcv": 88.0,
    "rdw": 12.5, "alkaline_phosphatase": 55.0, "wbc": 5.2,
}
ACCEL_BIO = {
    "albumin": 3.5, "creatinine": 1.4, "glucose_mg_dl": 118.0,
    "crp_mg_l": 4.8, "lymphocyte_percent": 18.0, "mcv": 96.0,
    "rdw": 15.2, "alkaline_phosphatase": 110.0, "wbc": 9.8,
}

results = []

def check(name, passed, actual, expected_desc, elapsed=None):
    r = {"test": name, "passed": passed, "actual": str(actual)[:120], "expected": expected_desc}
    if elapsed: r["elapsed_s"] = elapsed
    results.append(r)
    status = "✓" if passed else "✗"
    print(f"  {status} {name}: {actual}")
    return passed

print("=" * 60)
print("LONGIVITY API CORRECTNESS EVAL")
print(f"Run at: {datetime.now(timezone.utc).isoformat()}")
print("=" * 60)

# ── PhenoAge ──────────────────────────────────────────────────
print("\n[1] PhenoAge Formula (PMID 29676998)")
t0 = time.time()
r1 = run_longevity_assessment_level0({"age": 45, "biomarkers": HEALTHY_BIO})
pa1 = (r1.get("phenoage_analysis") or {}).get("phenoage_estimate")
check("Healthy 45yo PhenoAge in [28,42]", pa1 and 28 <= pa1 <= 42, pa1, "28-42yr")

r2 = run_longevity_assessment_level0({"age": 58, "biomarkers": ACCEL_BIO})
pa2 = (r2.get("phenoage_analysis") or {}).get("phenoage_estimate")
check("Accelerated 58yo PhenoAge in [60,85]", pa2 and 60 <= pa2 <= 85, pa2, "60-85yr")

accel1 = (r1.get("phenoage_analysis") or {}).get("age_acceleration")
check("Healthy panel: negative acceleration", accel1 and accel1 < 0, accel1, "< 0")

accel2 = (r2.get("phenoage_analysis") or {}).get("age_acceleration")
check("Accelerated panel: positive acceleration", accel2 and accel2 > 0, accel2, "> 0")

# Determinism
r1a = run_longevity_assessment_level0({"age": 45, "biomarkers": HEALTHY_BIO})
pa1a = (r1a.get("phenoage_analysis") or {}).get("phenoage_estimate")
check("PhenoAge deterministic (<0.001yr)", pa1 and pa1a and abs(pa1 - pa1a) < 0.001, abs(pa1 - pa1a) if pa1 and pa1a else "N/A", "< 0.001yr")

check("Healthy < Accelerated PhenoAge", pa1 and pa2 and pa1 < pa2, f"{pa1} < {pa2}", "healthy < accelerated")

mort = (r1.get("phenoage_analysis") or {}).get("mortality_score_10yr")
check("Mortality score in [0,1]", mort is not None and 0 <= mort <= 1, mort, "[0,1]")

elapsed_pa = round(time.time() - t0, 2)
print(f"  PhenoAge tests elapsed: {elapsed_pa}s")

# ── ASCVD ─────────────────────────────────────────────────────
print("\n[2] ASCVD Pooled Cohort Equations (PMID 24222018)")
for sex, race in [("M", "white"), ("F", "white"), ("M", "aa"), ("F", "aa")]:
    r = compute_ascvd_from_biomarkers({
        "age": 55, "sex": sex, "race": race,
        "biomarkers": {"total_cholesterol": 210.0, "hdl_cholesterol": 45.0, "systolic_bp": 130.0},
        "bp_treatment": False, "diabetes": False, "smoker": False,
    })
    risk = r.get("ten_year_ascvd_risk_pct")
    check(f"ASCVD {sex}/{race} in [0,100]%", risk is not None and 0 <= float(risk) <= 100, risk, "[0,100]%")

# High-risk patient
r_high = compute_ascvd_from_biomarkers({
    "age": 63, "sex": "M", "race": "white",
    "biomarkers": {"total_cholesterol": 245.0, "hdl_cholesterol": 38.0, "systolic_bp": 148.0},
    "bp_treatment": True, "diabetes": False, "smoker": False,
})
risk_high = r_high.get("ten_year_ascvd_risk_pct")
check("High-risk CVD patient ASCVD > 15%", risk_high and float(risk_high) > 15, risk_high, "> 15%")

# ── Wearable Scoring ──────────────────────────────────────────
print("\n[3] Wearable Hallmark Scoring")
w_high = score_wearables({"hrv_rmssd": 22.0, "vo2max": 24.0, "deep_sleep_pct": 10.0, "daily_steps": 3200, "resting_heart_rate": 82.0})
for metric in ["hrv_rmssd", "vo2max", "deep_sleep_pct", "daily_steps", "resting_heart_rate"]:
    tier = (w_high.get("scored_metrics") or {}).get(metric, {}).get("tier")
    check(f"{metric} HIGH_RISK", tier == "HIGH_RISK", tier, "HIGH_RISK")

mito = (w_high.get("hallmark_signals") or {}).get("mitochondrial_dysfunction", 0)
check("Mito signal >= 3.0 (all HIGH_RISK)", mito >= 3.0, mito, ">= 3.0")

w_opt = score_wearables({"hrv_rmssd": 62.0, "vo2max": 52.0, "deep_sleep_pct": 22.0, "daily_steps": 11000, "resting_heart_rate": 52.0})
for metric in ["hrv_rmssd", "vo2max"]:
    tier = (w_opt.get("scored_metrics") or {}).get(metric, {}).get("tier")
    check(f"{metric} OPTIMAL", tier == "OPTIMAL", tier, "OPTIMAL")

mito_opt = (w_opt.get("hallmark_signals") or {}).get("mitochondrial_dysfunction", 0)
check("Mito signal = 0 (all OPTIMAL, no false positive)", mito_opt == 0.0, mito_opt, "0.0")

# ── Longitudinal Delta ────────────────────────────────────────
print("\n[4] Longitudinal Delta Engine")
prior = {"phenoage_estimate": 68.2, "biomarkers": {"glucose_mg_dl": 142.0, "crp_mg_l": 4.8, "albumin": 4.0}, "date": "2025-10-01"}
current = {"phenoage_estimate": 64.1, "biomarkers": {"glucose_mg_dl": 118.0, "crp_mg_l": 2.9, "albumin": 4.2}, "date": "2026-04-01"}
delta = compute_longitudinal_delta(current, prior)
check("Improving trajectory", delta.get("trajectory") == "IMPROVING", delta.get("trajectory"), "IMPROVING")
pa_delta = (delta.get("phenoage_delta") or {}).get("delta")
check("PhenoAge delta negative (improving)", pa_delta and pa_delta < 0, pa_delta, "< 0")
check("PhenoAge delta direction IMPROVING", (delta.get("phenoage_delta") or {}).get("direction") == "IMPROVING", (delta.get("phenoage_delta") or {}).get("direction"), "IMPROVING")

# Worsening
prior2 = {"phenoage_estimate": 60.0, "biomarkers": {"glucose_mg_dl": 95.0, "crp_mg_l": 1.2}, "date": "2025-10-01"}
current2 = {"phenoage_estimate": 65.0, "biomarkers": {"glucose_mg_dl": 128.0, "crp_mg_l": 3.8}, "date": "2026-04-01"}
delta2 = compute_longitudinal_delta(current2, prior2)
check("Worsening trajectory", delta2.get("trajectory") == "WORSENING", delta2.get("trajectory"), "WORSENING")

# ── Nutrition Scoring ─────────────────────────────────────────
print("\n[5] Nutrition Hallmark Scoring")
try:
    svc = NutritionService()
    r_med = svc.analyze_diet(["blueberries", "salmon", "broccoli", "olive oil", "walnuts", "green tea"], age=50, sex="M")
    score_med = r_med.get("overall_dietary_score", 0)
    check("Mediterranean diet score >= 0.30", score_med >= 0.30, round(score_med, 3), ">= 0.30")
    tier_med = r_med.get("overall_tier")
    check("Mediterranean diet tier WEAK or above (score 0.347)", tier_med in ("WEAK", "MODERATE", "STRONG"), tier_med, "WEAK or above")
except Exception as e:
    check("Nutrition service available", False, str(e), "no error")

# ── Compound Evidence Tiers ───────────────────────────────────
print("\n[6] MR Evidence Tier Ranking")
from longivity.services.mr_evidence_registry import get_evidence_tier
mr_compounds = ["omega_3", "vitamin_d3", "folate", "metformin"]
rct_compounds = ["berberine", "nmn"]
for c in mr_compounds:
    tier = get_evidence_tier(c)
    check(f"{c} tier=MR_VALIDATED", tier == "MR_VALIDATED", tier, "MR_VALIDATED")
for c in rct_compounds:
    tier = get_evidence_tier(c)
    check(f"{c} tier=RCT", tier == "RCT", tier, "RCT")

# ── Summary ───────────────────────────────────────────────────
passed = sum(1 for r in results if r["passed"])
total = len(results)
pass_rate = round(passed / total * 100, 1)

summary = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "total_tests": total,
    "passed": passed,
    "failed": total - passed,
    "pass_rate_pct": pass_rate,
    "ci_threshold_pct": 95.0,
    "ci_pass": pass_rate >= 95.0,
    "tests": results,
}

out_path = Path(__file__).parent / "api_eval_results.json"
with open(out_path, "w") as f:
    json.dump(summary, f, indent=2, default=str)

print(f"\n{'='*60}")
print(f"RESULT: {passed}/{total} tests passed ({pass_rate}%)")
print(f"CI threshold: 95% — {'PASS' if summary['ci_pass'] else 'FAIL'}")
print(f"Saved: {out_path}")
print("=" * 60)

if "--ci-mode" in sys.argv and not summary["ci_pass"]:
    sys.exit(1)
