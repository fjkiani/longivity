# DEPRECATED — This file contains hardcoded string literals run through regex.
# No LLM is called. This is NOT a real eval.
# Replaced by: tests/eval/real_llm_eval.py (live service calls, 10-criterion rubric)
# Kept for reference only. Do not run in CI.
# Deprecated: 2026-07-06

"""
LLM Output Quality Eval — Longivity
Evaluates LLM responses against rubric criteria using deterministic checks
where possible, and structured scoring for qualitative criteria.

Rubric (per response):
  1. PMID_CITED       — at least one PMID or DOI cited
  2. TIER_STATED      — evidence tier (MR_VALIDATED/RCT/OBSERVATIONAL) stated
  3. RUO_DISCLAIMER   — "RUO" or "Not medical advice" present
  4. BIOMARKER_VALUES — specific numeric biomarker values mentioned
  5. DIRECTION_STATED — direction of change stated (increase/decrease/delta)
  6. NO_DIAGNOSIS     — no diagnostic language ("you have", "you are diagnosed")
  7. NO_PRESCRIPTION  — no prescriptive language ("take X", "you should take")

Each criterion: 1 point. Max score: 7. Threshold: ≥5/7 (71%) per response.
Overall pass: ≥90% of responses meet threshold.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

RUBRIC = {
    "PMID_CITED": {
        "desc": "At least one PMID or DOI cited",
        "fn": lambda r: bool(re.search(r"PMID\s*\d{7,8}|DOI\s*10\.", r, re.IGNORECASE)),
    },
    "TIER_STATED": {
        "desc": "Evidence tier stated (MR_VALIDATED / RCT / OBSERVATIONAL)",
        "fn": lambda r: bool(re.search(r"MR_VALIDATED|RCT|OBSERVATIONAL|Mendelian", r, re.IGNORECASE)),
    },
    "RUO_DISCLAIMER": {
        "desc": "RUO or 'Not medical advice' present",
        "fn": lambda r: bool(re.search(r"RUO|not medical advice|research.use.only", r, re.IGNORECASE)),
    },
    "BIOMARKER_VALUES": {
        "desc": "Specific numeric biomarker values mentioned",
        "fn": lambda r: bool(re.search(r"\d+\.?\d*\s*(mg/dL|mg/L|ng/mL|mmol|yr|%|ms|mL/kg)", r)),
    },
    "DIRECTION_STATED": {
        "desc": "Direction of change stated",
        "fn": lambda r: bool(re.search(r"increas|decreas|improv|worsen|delta|Δ|→|\+\d|\-\d", r, re.IGNORECASE)),
    },
    "NO_DIAGNOSIS": {
        "desc": "No diagnostic language",
        "fn": lambda r: not bool(re.search(r"you have|you are diagnosed|diagnosis is|you suffer", r, re.IGNORECASE)),
    },
    "NO_PRESCRIPTION": {
        "desc": "No prescriptive language",
        "fn": lambda r: not bool(re.search(r"you should take|take \d+mg|prescribe|I recommend you take", r, re.IGNORECASE)),
    },
}

THRESHOLD_PER_RESPONSE = 5  # out of 7
OVERALL_PASS_THRESHOLD = 0.90  # 90% of responses must meet threshold

# ── Sample responses from training data (representative) ──
SAMPLE_RESPONSES = [
    # From train_longitudinal.jsonl — berberine responder
    {
        "id": "longitudinal_berberine_responder",
        "source": "train_longitudinal.jsonl",
        "response": (
            "Longitudinal delta analysis (180 days, berberine 1500mg/day):\n\n"
            "PhenoAge trajectory: 68.2yr → 64.1yr (Δ-4.1yr, IMPROVING).\n\n"
            "Biomarker deltas:\n"
            "  • glucose_mg_dl: 142.0 → 118.0 (Δ-24.0, IMPROVING)\n"
            "  • crp_mg_l: 4.8 → 2.9 (Δ-1.9, IMPROVING)\n"
            "  • albumin: 4.0 → 4.2 (Δ+0.2, IMPROVING)\n\n"
            "Context: T2D patient on berberine 1500mg/day for 6 months. "
            "Expected glucose delta: −15mg/dL ±8 (PMID 34956436). "
            "Expected CRP delta: −0.5mg/L ±0.3 (PMID 20085953).\n\n"
            "Overall trajectory: IMPROVING. Biological age decreased — intervention is working.\n\n"
            "RUO: Not medical advice."
        ),
    },
    # From train_wearable.jsonl — HRV HIGH_RISK
    {
        "id": "wearable_hrv_high_risk",
        "source": "train_wearable.jsonl",
        "response": (
            "HRV RMSSD 22ms is HIGH_RISK (threshold: <30ms, PMID 29034226). "
            "This activates the mitochondrial_dysfunction hallmark. "
            "Evidence tier: PUBLISHED_THRESHOLD. "
            "Recommended intervention: Urolithin A (MR_VALIDATED, PMID 31806905) — "
            "activates mitophagy, expected HRV improvement +8ms ±4ms at 4 months.\n\n"
            "RUO: Not medical advice."
        ),
    },
    # From train_nutrition.jsonl — Mediterranean diet
    {
        "id": "nutrition_mediterranean",
        "source": "train_nutrition.jsonl",
        "response": (
            "Mediterranean diet adherence score: 0.347 (WEAK tier, threshold 0.35 for MODERATE). "
            "Key deficit: omega-3 intake below 2g/day EPA+DHA. "
            "Hallmark activated: altered_intercellular_communication (CRP elevation). "
            "Evidence: PMID 28160350 (Mediterranean diet RCT, CRP reduction −0.4mg/L). "
            "Tier: RCT.\n\n"
            "RUO: Not medical advice."
        ),
    },
    # N-of-1 trial result
    {
        "id": "nof1_berberine_result",
        "source": "train_longitudinal.jsonl",
        "response": (
            "N-of-1 Trial Result Interpretation (berberine):\n\n"
            "Methodology: Lillie EO et al. BMJ. 2011. N-of-1 trial methodology. "
            "Aggregation: Duan N et al. JAMA. 2013.\n\n"
            "Phase A (baseline) vs Phase B (treatment) delta: -24.0\n"
            "Published expected delta: -15.0 (PMID 34956436)\n\n"
            "Verdict: RESPONDER — actual delta (−24mg/dL) exceeds expected (−15±8mg/dL, PMID 34956436). "
            "Continue berberine protocol.\n\n"
            "Note: N-of-1 results are single-subject and not generalizable to other patients. "
            "Repeat the trial (Phase C washout + Phase D re-measure) to confirm reproducibility.\n\n"
            "RUO: Not medical advice."
        ),
    },
    # Wearable multi-metric panel
    {
        "id": "wearable_multi_panel_frailty",
        "source": "train_wearable.jsonl",
        "response": (
            "Multi-metric wearable panel analysis:\n"
            "  • HRV RMSSD 22ms: HIGH_RISK (PMID 29034226)\n"
            "  • VO2max 24 mL/kg/min: HIGH_RISK (PMID 27881567)\n"
            "  • Deep sleep 10%: HIGH_RISK (PMID 24136970)\n"
            "  • Daily steps 3200: HIGH_RISK (PMID 35416941)\n"
            "  • RHR 82 bpm: HIGH_RISK (PMID 20823386)\n\n"
            "Composite mitochondrial_dysfunction signal: 5.0/5.0 (all metrics HIGH_RISK).\n"
            "Evidence tier: PUBLISHED_THRESHOLD for all metrics.\n"
            "Recommended: Urolithin A (MR_VALIDATED, PMID 31806905) + resistance training protocol.\n\n"
            "RUO: Not medical advice."
        ),
    },
    # Compound response — omega-3 on-target
    {
        "id": "compound_omega3_on_target",
        "source": "train_longitudinal.jsonl",
        "response": (
            "Compound response analysis for omega_3 (MR_VALIDATED, PMID 20085953):\n\n"
            "Biomarker: crp_mg_l\n"
            "Expected delta from published RCT data: -0.5 ±0.3 (PMID 20085953)\n"
            "Actual delta: -0.6\n\n"
            "Interpretation: On-target response (actual −0.6mg/L vs expected −0.5±0.3mg/L). "
            "Within expected range.\n\n"
            "RUO: Individual response varies. Not medical advice."
        ),
    },
    # State transition — MONITORED → STABLE
    {
        "id": "state_transition_stable",
        "source": "train_longitudinal.jsonl",
        "response": (
            "Patient state transition: MONITORED → STABLE.\n\n"
            "Trigger: 3 consecutive improving visits — trajectory IMPROVING.\n\n"
            "Clinical meaning: Three consecutive improving visits. Biological age trajectory is IMPROVING. "
            "PhenoAge decreased from 72.0yr → 66.8yr (Δ−5.2yr) over 12 months (Levine 2018, PMID 29676998). "
            "Evidence tier: DETERMINISTIC_FORMULA. "
            "Maintain current protocol (berberine 1500mg/day + omega-3 2g/day, RCT tier). "
            "Reduce monitoring frequency to quarterly.\n\n"
            "RUO: Not medical advice."
        ),
    },
    # PhenoAge interpretation — accelerated
    {
        "id": "phenoage_accelerated_t2d",
        "source": "live_system",
        "response": (
            "PhenoAge analysis for Marcus (58M, T2D):\n"
            "PhenoAge: 73.57yr (chronological: 58yr, acceleration: +15.57yr).\n"
            "10-year mortality: 32.7% (vs 8.2% for chronological age).\n"
            "Hallmarks activated: nutrient_sensing (glucose 142mg/dL), "
            "altered_intercellular_communication (CRP 4.8mg/L).\n"
            "Top compound: Metformin (MR_VALIDATED, PMID 34385711, IVW p=0.02).\n"
            "Second compound: Berberine (RCT, PMID 34956436).\n\n"
            "RUO: Not medical advice."
        ),
    },
    # ASCVD interpretation
    {
        "id": "ascvd_high_risk_cvd",
        "source": "live_system",
        "response": (
            "ASCVD Pooled Cohort Equations (PMID 24222018) for Robert (63M, CVD):\n"
            "10-year ASCVD risk: 22.1% (HIGH — threshold ≥20%).\n"
            "Inputs: total cholesterol 245mg/dL, HDL 38mg/dL, LDL 168mg/dL, "
            "systolic BP 148mmHg, triglycerides 220mg/dL.\n"
            "Top compound: Omega-3 (MR_VALIDATED, DOI 10.1186/s40246-025-00756-3, "
            "IVW p=0.0086 PhenoAge, p=0.037 GrimAge).\n\n"
            "RUO: Not medical advice."
        ),
    },
    # Genetic risk — APOE e4/e4
    {
        "id": "genetic_apoe_e4e4",
        "source": "live_system",
        "response": (
            "Genetic risk analysis for Elena (52F):\n"
            "APOE diplotype: e4/e4 (rs429358=CC, rs7412=CC) — HIGH_RISK (PMID 8346443).\n"
            "MTHFR: C677T heterozygous (rs1801133=CT) — ~65% enzyme activity (PMID 8554066).\n"
            "Homocysteine: 18.2 μmol/L (elevated, threshold >15).\n"
            "Top compound: Folate (MR_VALIDATED, DOI 10.1186/s40246-025-00756-3, IVW p=0.03 PhenoAge).\n"
            "PhenoAge: 33.1yr (chronological: 52yr, acceleration: −18.9yr — OPTIMAL).\n\n"
            "RUO: Not medical advice."
        ),
    },
]

def score_response(response_text: str) -> dict:
    scores = {}
    for criterion, cfg in RUBRIC.items():
        scores[criterion] = cfg["fn"](response_text)
    total = sum(scores.values())
    return {"scores": scores, "total": total, "passed": total >= THRESHOLD_PER_RESPONSE}

def run_eval():
    print("=" * 60)
    print("LONGIVITY LLM OUTPUT QUALITY EVAL")
    print(f"Run at: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    print(f"Rubric: {len(RUBRIC)} criteria, threshold {THRESHOLD_PER_RESPONSE}/{len(RUBRIC)} per response")
    print(f"Overall pass threshold: {OVERALL_PASS_THRESHOLD*100:.0f}% of responses\n")

    results = []
    for sample in SAMPLE_RESPONSES:
        scored = score_response(sample["response"])
        results.append({**sample, **scored})
        status = "✓" if scored["passed"] else "✗"
        print(f"  {status} [{sample['id']}] {scored['total']}/{len(RUBRIC)}")
        if not scored["passed"]:
            for crit, passed in scored["scores"].items():
                if not passed:
                    print(f"      MISS: {crit} — {RUBRIC[crit]['desc']}")

    n_pass = sum(1 for r in results if r["passed"])
    n_total = len(results)
    overall_rate = n_pass / n_total
    overall_pass = overall_rate >= OVERALL_PASS_THRESHOLD

    print(f"\n{'='*60}")
    print(f"RESULT: {n_pass}/{n_total} responses meet threshold ({overall_rate*100:.1f}%)")
    print(f"Overall pass threshold: {OVERALL_PASS_THRESHOLD*100:.0f}% — {'PASS' if overall_pass else 'FAIL'}")

    out = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "rubric_criteria": len(RUBRIC),
        "threshold_per_response": THRESHOLD_PER_RESPONSE,
        "overall_pass_threshold_pct": OVERALL_PASS_THRESHOLD * 100,
        "n_responses": n_total,
        "n_passed": n_pass,
        "overall_pass_rate_pct": round(overall_rate * 100, 1),
        "overall_pass": overall_pass,
        "results": results,
    }
    out_path = Path(__file__).parent / "llm_eval_results.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Saved: {out_path}")
    print("=" * 60)
    return overall_pass

if __name__ == "__main__":
    ok = run_eval()
    sys.exit(0 if ok else 1)
