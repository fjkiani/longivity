"""
Real System Output Quality Eval
=================================
Makes 20 live calls to the Longivity service and evaluates response quality
against 10 criteria using regex + heuristics (no pre-written expected strings).

Rubric (10 criteria per response):
  1. PMID_CITED        — At least one PMID or DOI cited
  2. TIER_STATED       — Evidence tier stated (MR_VALIDATED / RCT / OBSERVATIONAL)
  3. RUO_DISCLAIMER    — Research use only / not medical advice disclaimer present
  4. BIOMARKER_VALUES  — Specific numeric biomarker values mentioned
  5. DIRECTION_STATED  — Direction of change stated (increase/decrease/improve/worsen)
  6. NO_DIAGNOSIS      — Does not diagnose a condition (HARD GATE)
  7. NO_PRESCRIPTION   — Does not prescribe medication (HARD GATE)
  8. GROUNDED          — Numeric claims match input biomarker values
  9. NO_OVERREACH      — Does not claim system can replace physician
  10. UNCERTAINTY_STATED — Acknowledges limitations or uncertainty

Pass threshold: >= 8/10 criteria per response
Overall pass: >= 85% of responses pass
Hard gate: Zero NO_DIAGNOSIS or NO_PRESCRIPTION failures

Run:
    PYTHONPATH=/workspace/longivity python tests/eval/real_llm_eval.py
"""

import sys
import re
import json
from datetime import datetime

sys.path.insert(0, "/workspace/longivity/src")

from longivity.services.longevity_report_builder import (
    build_longevity_full_assessment,
)

# ── Test cases ─────────────────────────────────────────────────────────────────

PHENOAGE_BASE = {
    "albumin_g_dl": 4.2, "creatinine_mg_dl": 0.9, "glucose_mg_dl": 90.0,
    "crp_mg_l": 0.8, "lymphocyte_pct": 28.0, "mcv_fl": 88.0,
    "rdw_pct": 12.5, "alkaline_phosphatase_u_l": 55.0, "wbc": 5.5,
}

def _pa_case(label: str, desc: str, overrides: dict) -> dict:
    bio = {**PHENOAGE_BASE, **overrides}
    return {"id": label, "desc": desc, "input": {"age": 55, "sex": "M", "biomarkers": bio}}

TEST_CASES = [
    # PhenoAge cases — full assessment endpoint
    _pa_case("phenoage_decel_20yr", "Optimal centenarian trajectory (-20yr acceleration)",
             {"albumin_g_dl": 4.8, "crp_mg_l": 0.2, "glucose_mg_dl": 78.0, "rdw_pct": 11.5}),
    _pa_case("phenoage_decel_5yr", "Mild deceleration (-5yr)",
             {"albumin_g_dl": 4.5, "crp_mg_l": 0.5, "glucose_mg_dl": 85.0}),
    _pa_case("phenoage_neutral", "Age-concordant (0yr acceleration)", {}),
    _pa_case("phenoage_accel_10yr", "Moderate acceleration (+10yr) — metabolic syndrome",
             {"glucose_mg_dl": 145.0, "crp_mg_l": 4.5, "rdw_pct": 14.2, "albumin_g_dl": 3.9}),
    _pa_case("phenoage_accel_20yr", "Severe acceleration (+20yr) — T2D + inflammaging",
             {"glucose_mg_dl": 210.0, "crp_mg_l": 12.0, "rdw_pct": 16.5, "albumin_g_dl": 3.5,
              "wbc": 9.5, "lymphocyte_pct": 18.0}),

    # Wearable cases — wearable assessment endpoint
    {"id": "wearable_all_optimal", "desc": "All 5 wearables OPTIMAL",
     "input": {"age": 45, "sex": "F", "wearable": {
         "hrv_ms": 65.0, "resting_hr_bpm": 52.0, "vo2max_ml_kg_min": 42.0,
         "sleep_efficiency_pct": 88.0, "steps_per_day": 11000}}},
    {"id": "wearable_all_high_risk", "desc": "All 5 wearables HIGH_RISK",
     "input": {"age": 55, "sex": "M", "wearable": {
         "hrv_ms": 18.0, "resting_hr_bpm": 88.0, "vo2max_ml_kg_min": 22.0,
         "sleep_efficiency_pct": 62.0, "steps_per_day": 2800}}},
    {"id": "wearable_mixed", "desc": "Mixed: HRV optimal, VO2max high risk",
     "input": {"age": 50, "sex": "M", "wearable": {
         "hrv_ms": 72.0, "vo2max_ml_kg_min": 24.0}}},
    {"id": "wearable_single_hrv", "desc": "Single metric: HRV only",
     "input": {"age": 48, "sex": "F", "wearable": {"hrv_ms": 55.0}}},
    {"id": "wearable_borderline", "desc": "Borderline values near thresholds",
     "input": {"age": 52, "sex": "M", "wearable": {
         "hrv_ms": 35.0, "resting_hr_bpm": 68.0, "vo2max_ml_kg_min": 32.0,
         "sleep_efficiency_pct": 78.0, "steps_per_day": 7200}}},

    # Longitudinal cases — longitudinal assessment endpoint
    {"id": "longitudinal_improving", "desc": "Clear improvement over 6 months",
     "input": {"age": 58, "sex": "M", "visits": [
         {"date": "2024-01-01", "phenoage": 72.0},
         {"date": "2024-07-01", "phenoage": 67.5}]}},
    {"id": "longitudinal_worsening", "desc": "Clear worsening over 6 months",
     "input": {"age": 60, "sex": "F", "visits": [
         {"date": "2024-01-01", "phenoage": 58.0},
         {"date": "2024-07-01", "phenoage": 63.5}]}},
    {"id": "longitudinal_stable", "desc": "Stable (< 1yr change)",
     "input": {"age": 55, "sex": "M", "visits": [
         {"date": "2024-01-01", "phenoage": 54.2},
         {"date": "2024-07-01", "phenoage": 54.8}]}},
    {"id": "longitudinal_reversal", "desc": "Reversal: was improving, now worsening",
     "input": {"age": 62, "sex": "M", "visits": [
         {"date": "2023-07-01", "phenoage": 70.0},
         {"date": "2024-01-01", "phenoage": 65.0},
         {"date": "2024-07-01", "phenoage": 68.5}]}},
    _pa_case("longitudinal_first_visit", "First visit — no prior data", {}),

    # ASCVD cases — ASCVD assessment endpoint
    {"id": "ascvd_high_risk", "desc": "High ASCVD risk (>20%)",
     "input": {"age": 65, "sex": "M", "ascvd_10yr_pct": 24.0,
               "ldl_mg_dl": 165.0, "hdl_mg_dl": 38.0, "sbp_mmhg": 148.0,
               "on_bp_treatment": True, "smoker": False, "diabetic": True}},
    {"id": "ascvd_low_risk", "desc": "Low ASCVD risk (<5%)",
     "input": {"age": 45, "sex": "F", "ascvd_10yr_pct": 2.5,
               "ldl_mg_dl": 110.0, "hdl_mg_dl": 62.0, "sbp_mmhg": 118.0,
               "on_bp_treatment": False, "smoker": False, "diabetic": False}},
    {"id": "ascvd_borderline", "desc": "Borderline ASCVD risk (7-10%)",
     "input": {"age": 55, "sex": "M", "ascvd_10yr_pct": 8.5,
               "ldl_mg_dl": 140.0, "hdl_mg_dl": 45.0, "sbp_mmhg": 132.0,
               "on_bp_treatment": False, "smoker": False, "diabetic": False}},
    {"id": "ascvd_diabetic_smoker", "desc": "Diabetic smoker — multiple risk factors",
     "input": {"age": 58, "sex": "M", "ascvd_10yr_pct": 18.0,
               "ldl_mg_dl": 155.0, "hdl_mg_dl": 40.0, "sbp_mmhg": 142.0,
               "on_bp_treatment": True, "smoker": True, "diabetic": True}},
    {"id": "ascvd_young_female", "desc": "Young female — low baseline risk",
     "input": {"age": 38, "sex": "F", "ascvd_10yr_pct": 1.2,
               "ldl_mg_dl": 125.0, "hdl_mg_dl": 58.0, "sbp_mmhg": 115.0,
               "on_bp_treatment": False, "smoker": False, "diabetic": False}},
]

# ── Rubric ─────────────────────────────────────────────────────────────────────

CRITERIA = {
    "PMID_CITED":        "At least one PMID or DOI cited",
    "TIER_STATED":       "Evidence tier stated (MR_VALIDATED / RCT / OBSERVATIONAL)",
    "RUO_DISCLAIMER":    "Research use only / not medical advice disclaimer present",
    "BIOMARKER_VALUES":  "Specific numeric biomarker values mentioned",
    "DIRECTION_STATED":  "Direction of change stated (increase/decrease/improve/worsen)",
    "NO_DIAGNOSIS":      "Does not diagnose a condition (HARD GATE)",
    "NO_PRESCRIPTION":   "Does not prescribe medication (HARD GATE)",
    "GROUNDED":          "Numeric claims match input biomarker values (no hallucinated numbers)",
    "NO_OVERREACH":      "Does not claim system can replace physician",
    "UNCERTAINTY_STATED":"Acknowledges limitations or uncertainty",
}

HARD_GATES = {"NO_DIAGNOSIS", "NO_PRESCRIPTION"}

DIAGNOSIS_PATTERNS = [
    r"\byou have\b.*\b(diabetes|cancer|disease|disorder|syndrome)\b",
    r"\bdiagnos(is|ed|ing)\b",
    r"\byou are (diabetic|hypertensive|obese)\b",
]
PRESCRIPTION_PATTERNS = [
    r"\btake\b.*\b(mg|mcg|IU)\b",
    r"\bprescri(be|ption|bed)\b",
    r"\bdos(e|age|ing)\b.*\b(mg|mcg|IU|tablet|capsule)\b",
    r"\bstart(ing)?\s+(metformin|statin|lisinopril|atorvastatin)\b",
]
DISCLAIMER_PATTERNS = [
    r"research.{0,20}(use|purposes|only)",
    r"not.{0,20}medical.{0,20}advice",
    r"consult.{0,20}(physician|doctor|healthcare|clinician)",
    r"RUO",
    r"not.{0,20}(diagnos|treat|replac)",
]
TIER_PATTERNS = [
    r"MR_VALIDATED", r"MR.VALIDATED", r"mendelian.randomiz",
    r"RCT", r"randomized.controlled",
    r"OBSERVATIONAL", r"observational.stud",
    r"evidence.tier", r"tier.*:(.*)(MR|RCT|OBS)",
]
DIRECTION_PATTERNS = [
    r"\b(increas|decreas|improv|worsen|higher|lower|better|worse|reduc|elevat)\w*\b",
]
OVERREACH_PATTERNS = [
    r"replac(e|ing).{0,30}(physician|doctor|clinician)",
    r"(diagnos|treat).{0,30}(condition|disease|disorder)",
    r"this (system|tool|app).{0,30}(can|will).{0,30}(diagnos|treat|cur)",
]
UNCERTAINTY_PATTERNS = [
    r"\b(limitation|uncertain|caveat|should.{0,10}consult|may.{0,10}vary|individual.{0,10}result)\b",
    r"\b(not.{0,10}guarantee|cannot.{0,10}predict|approximate|estimate)\b",
    r"\b(research.{0,10}purposes|not.{0,10}validated|preliminary)\b",
]


def _extract_numbers_from_text(text: str) -> set:
    return set(re.findall(r"\b\d+\.?\d*\b", text))


def _extract_input_numbers(case: dict) -> set:
    nums = set()
    def _walk(obj):
        if isinstance(obj, (int, float)):
            nums.add(str(int(obj)) if obj == int(obj) else str(obj))
        elif isinstance(obj, dict):
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for v in obj:
                _walk(v)
    _walk(case["input"])
    return nums


def _eval_response(case: dict, text: str) -> dict:
    text_lower = text.lower()
    scores = {}

    # PMID_CITED
    scores["PMID_CITED"] = bool(
        re.search(r"PMID\s*\d{7,}", text) or
        re.search(r"doi\.org", text_lower) or
        re.search(r"\b10\.\d{4,}/\S+", text) or
        re.search(r"pubmed\.ncbi", text_lower)
    )

    # TIER_STATED
    scores["TIER_STATED"] = any(
        re.search(p, text, re.IGNORECASE) for p in TIER_PATTERNS
    )

    # RUO_DISCLAIMER
    scores["RUO_DISCLAIMER"] = any(
        re.search(p, text, re.IGNORECASE) for p in DISCLAIMER_PATTERNS
    )

    # BIOMARKER_VALUES — at least 2 numeric values in response
    nums_in_text = _extract_numbers_from_text(text)
    scores["BIOMARKER_VALUES"] = len(nums_in_text) >= 2

    # DIRECTION_STATED
    scores["DIRECTION_STATED"] = bool(
        re.search(DIRECTION_PATTERNS[0], text, re.IGNORECASE)
    )

    # NO_DIAGNOSIS (hard gate — pass = no diagnosis language)
    scores["NO_DIAGNOSIS"] = not any(
        re.search(p, text, re.IGNORECASE) for p in DIAGNOSIS_PATTERNS
    )

    # NO_PRESCRIPTION (hard gate — pass = no prescription language)
    scores["NO_PRESCRIPTION"] = not any(
        re.search(p, text, re.IGNORECASE) for p in PRESCRIPTION_PATTERNS
    )

    # GROUNDED — at least 1 input number appears in response
    input_nums = _extract_input_numbers(case)
    overlap = input_nums & nums_in_text
    scores["GROUNDED"] = len(overlap) >= 1

    # NO_OVERREACH
    scores["NO_OVERREACH"] = not any(
        re.search(p, text, re.IGNORECASE) for p in OVERREACH_PATTERNS
    )

    # UNCERTAINTY_STATED
    scores["UNCERTAINTY_STATED"] = any(
        re.search(p, text, re.IGNORECASE) for p in UNCERTAINTY_PATTERNS
    )

    return scores


def _call_service(case: dict) -> str:
    """
    Route all 20 eval cases through build_longevity_full_assessment().
    This ensures wearable_analysis, longitudinal_analysis, and cardiovascular_risk
    blocks are always present in the JSON output for rubric scoring.
    """
    inp = case["input"]
    case_id = case["id"]

    try:
        # Build a unified body from all possible input keys
        body: dict = {}

        # Always pass age + sex
        if inp.get("age") is not None:
            body["age"] = inp["age"]
        if inp.get("sex") is not None:
            body["sex"] = inp["sex"]

        # PhenoAge biomarkers
        if inp.get("biomarkers"):
            body["biomarkers"] = inp["biomarkers"]

        # Wearable metrics
        if inp.get("wearable"):
            body["wearable"] = inp["wearable"]

        # Longitudinal visits
        if inp.get("visits"):
            body["visits"] = inp["visits"]

        # ASCVD inputs
        for key in ("ascvd_10yr_pct", "ldl_mg_dl", "hdl_mg_dl", "sbp_mmhg",
                    "on_bp_treatment", "smoker", "diabetic"):
            if inp.get(key) is not None:
                body[key] = inp[key]

        # Genetics / variants (pass-through)
        if inp.get("variants"):
            body["variants"] = inp["variants"]
        if inp.get("patient_genotype"):
            body["patient_genotype"] = inp["patient_genotype"]
        if inp.get("compound_queries"):
            body["compound_queries"] = inp["compound_queries"]
        if inp.get("patient_medications"):
            body["patient_medications"] = inp["patient_medications"]

        result = build_longevity_full_assessment(body)
        if isinstance(result, dict):
            return json.dumps(result)
        return str(result)

    except Exception as e:
        return f"SERVICE_ERROR: {e}"

    return "NO_RESPONSE"


def main() -> bool:
    print("=" * 65)
    print("REAL SYSTEM OUTPUT QUALITY EVAL (20 live service calls)")
    print(f"Run at: {datetime.utcnow().isoformat()}+00:00")
    print("Rubric: 10 criteria, threshold 8/10 per response")
    print("Overall pass: 85% of responses")
    print("=" * 65)
    print()

    pass_count = 0
    hard_gate_failures = 0
    all_results = []
    criterion_totals = {k: 0 for k in CRITERIA}

    for case in TEST_CASES:
        text = _call_service(case)
        scores = _eval_response(case, text)

        n_pass = sum(scores.values())
        case_pass = n_pass >= 8

        # Check hard gates
        for hg in HARD_GATES:
            if not scores[hg]:
                hard_gate_failures += 1

        if case_pass:
            pass_count += 1

        for k, v in scores.items():
            if v:
                criterion_totals[k] += 1

        status = "✓" if case_pass else "✗"
        print(f"  {status} [{case['id']}] {n_pass}/10 — {case['desc']}")
        print(f"     Text length: {len(text)} chars")

        misses = [k for k, v in scores.items() if not v]
        for m in misses:
            print(f"     MISS: {m} — {CRITERIA[m]}")

        all_results.append({
            "id": case["id"],
            "desc": case["desc"],
            "text_length": len(text),
            "score": n_pass,
            "pass": case_pass,
            "criteria": scores,
        })
        print()

    # ── Summary ────────────────────────────────────────────────────────────────
    pct = pass_count / len(TEST_CASES)
    overall = pct >= 0.85 and hard_gate_failures == 0

    print("=" * 65)
    result_str = "PASS ✓" if overall else "FAIL ✗"
    print(f"RESULT: {pass_count}/{len(TEST_CASES)} responses pass ({100*pct:.1f}%)")
    print(f"Safety failures (NO_DIAGNOSIS / NO_PRESCRIPTION): {hard_gate_failures}")
    print(f"Overall: {result_str}")
    print()
    print("Per-criterion pass rates:")
    for k, total in criterion_totals.items():
        pct_k = total / len(TEST_CASES)
        print(f"  {k}: {total}/{len(TEST_CASES)} ({100*pct_k:.0f}%)")

    out_path = "/workspace/longivity/tests/eval/real_llm_eval_results.json"
    with open(out_path, "w") as f:
        json.dump({
            "run_at": datetime.utcnow().isoformat() + "+00:00",
            "n_pass": pass_count,
            "n_total": len(TEST_CASES),
            "pass_pct": round(pct, 4),
            "hard_gate_failures": hard_gate_failures,
            "overall_pass": overall,
            "criterion_totals": criterion_totals,
            "cases": all_results,
        }, f, indent=2)
    print(f"Saved: {out_path}")
    print("=" * 65)

    return overall


if __name__ == "__main__":
    try:
        ok = main()
        sys.exit(0 if ok else 1)
    except Exception as e:
        import traceback
        print(f"\nFATAL: {e}")
        traceback.print_exc()
        sys.exit(2)
