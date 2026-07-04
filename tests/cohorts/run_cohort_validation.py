"""
Cohort Validation Runner — runs all 5 disease archetypes through the live system.

Usage:
    PYTHONPATH=/workspace/longivity python tests/cohorts/run_cohort_validation.py
    PYTHONPATH=/workspace/longivity python tests/cohorts/run_cohort_validation.py --ci-mode

Outputs:
    tests/cohorts/cohort_validation_results.json
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from longivity.services.longevity_phenoage_level0 import run_longevity_assessment_level0
from longivity.services.longevity_report_builder import run_longevity_full_assessment
from longivity.services.wearable_service import score_wearables
from longivity.services.cardiovascular_risk import compute_ascvd_from_biomarkers

from tests.cohorts.patient_archetypes import ALL_ARCHETYPES, PatientArchetype


def _extract_phenoage_block(result: Dict) -> Dict:
    """
    full_assessment uses 'biological_age' key; assessment_level0 uses 'phenoage_analysis'.
    Normalize to a single dict with phenoage_estimate, age_acceleration, mortality_score_10yr.
    """
    # Try phenoage_analysis first (level0)
    pa = result.get("phenoage_analysis")
    if pa and pa.get("phenoage_estimate") is not None:
        return pa
    # Try biological_age (full_assessment)
    ba = result.get("biological_age")
    if ba and ba.get("phenoage_estimate") is not None:
        return ba
    # Try level0 sub-key (full_assessment wraps level0)
    l0 = result.get("level0") or {}
    pa2 = l0.get("phenoage_analysis")
    if pa2 and pa2.get("phenoage_estimate") is not None:
        return pa2
    return pa or ba or {}


def _extract_hallmarks(result: Dict) -> List[str]:
    """Extract active hallmark keys from either output shape."""
    # level0 shape
    hn = result.get("hallmark_narrative")
    if isinstance(hn, dict) and hn:
        return list(hn.keys())
    # full_assessment shape
    hs = result.get("hallmark_summary")
    if isinstance(hs, dict) and hs:
        return list(hs.keys())
    # level0 nested inside full_assessment
    l0 = result.get("level0") or {}
    hn2 = l0.get("hallmark_narrative")
    if isinstance(hn2, dict) and hn2:
        return list(hn2.keys())
    return []


def _extract_compounds(result: Dict) -> List[Dict]:
    """Extract compound recommendations from either output shape."""
    comps = result.get("compound_recommendations")
    if isinstance(comps, list):
        return comps
    l0 = result.get("level0") or {}
    comps2 = l0.get("compound_recommendations")
    if isinstance(comps2, list):
        return comps2
    return []


def _extract_genetic(result: Dict) -> Dict:
    """Extract genetic profile."""
    return result.get("genetic_profile") or {}


def _get_nested(obj: Any, path: str) -> Any:
    """Traverse dot-notation path into nested dict/list."""
    parts = path.split(".")
    cur = obj
    for p in parts:
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(p)
        elif isinstance(cur, list):
            found = None
            for item in cur:
                if isinstance(item, dict) and p in item:
                    found = item[p]
                    break
            cur = found
        else:
            return None
    return cur


def _evaluate_assertion(result: Dict, assertion: Dict) -> Dict:
    path = assertion["path"]
    op = assertion["op"]
    expected = assertion["value"]
    label = assertion["label"]

    # Normalize result for assertion evaluation
    normalized = dict(result)
    pa = _extract_phenoage_block(result)
    normalized["phenoage_analysis"] = pa
    normalized["hallmark_narrative"] = {k: True for k in _extract_hallmarks(result)}
    normalized["compound_recommendations"] = _extract_compounds(result)
    normalized["genetic_profile"] = _extract_genetic(result)

    actual = _get_nested(normalized, path)

    passed = False
    detail = ""

    if op == "gt":
        passed = actual is not None and float(actual) > float(expected)
        detail = f"{actual} > {expected}"
    elif op == "lt":
        passed = actual is not None and float(actual) < float(expected)
        detail = f"{actual} < {expected}"
    elif op == "gte":
        passed = actual is not None and float(actual) >= float(expected)
        detail = f"{actual} >= {expected}"
    elif op == "eq":
        passed = str(actual).upper() == str(expected).upper()
        detail = f"{actual!r} == {expected!r}"
    elif op == "key_present":
        passed = isinstance(actual, dict) and expected in actual
        detail = f"key '{expected}' in {list(actual.keys()) if isinstance(actual, dict) else actual}"
    elif op == "any_tier":
        compounds = actual if isinstance(actual, list) else []
        passed = any(c.get("evidence_tier") == expected for c in compounds)
        tiers = [c.get("evidence_tier") for c in compounds]
        detail = f"tiers present: {tiers}"
    elif op == "compound_tier":
        compounds = actual if isinstance(actual, list) else []
        frag = expected["name_fragment"].lower()
        tier = expected["tier"]
        match = next(
            (c for c in compounds
             if frag in (c.get("display_name") or c.get("compound_id") or "").lower()),
            None
        )
        if match:
            passed = match.get("evidence_tier") == tier
            detail = f"found '{match.get('display_name')}' tier={match.get('evidence_tier')}, expected {tier}"
        else:
            passed = False
            detail = f"compound containing '{frag}' not found in recommendations"

    return {
        "label": label,
        "path": path,
        "op": op,
        "expected": str(expected),
        "actual": str(actual),
        "passed": passed,
        "detail": detail,
    }


def run_patient(archetype: PatientArchetype) -> Dict:
    t0 = time.time()
    payload = dict(archetype.payload)
    wearables = payload.pop("wearables", None)

    has_variants = bool(payload.get("variants"))
    try:
        if has_variants:
            result = run_longevity_full_assessment(payload)
        else:
            result = run_longevity_assessment_level0(payload)
    except Exception as e:
        result = {"error": str(e), "status": "ERROR"}

    wearable_result = None
    if wearables:
        try:
            wearable_result = score_wearables(wearables)
            result["wearable_assessment"] = wearable_result
        except Exception as e:
            result["wearable_assessment"] = {"error": str(e)}

    bio = payload.get("biomarkers", {})
    if "total_cholesterol" in bio and "systolic_bp" in bio:
        try:
            ascvd = compute_ascvd_from_biomarkers({
                "age": payload.get("age"),
                "sex": payload.get("sex", "M"),
                "race": "white",
                "biomarkers": bio,
                "bp_treatment": False,
                "diabetes": bio.get("glucose_mg_dl", 0) > 126,
                "smoker": False,
            })
            result["ascvd_risk"] = ascvd
        except Exception as e:
            result["ascvd_risk"] = {"error": str(e)}

    elapsed = round(time.time() - t0, 2)

    assertion_results = [_evaluate_assertion(result, a) for a in archetype.assertions]
    passed = sum(1 for a in assertion_results if a["passed"])
    total = len(assertion_results)

    pa = _extract_phenoage_block(result)
    genetic = _extract_genetic(result)
    compounds = _extract_compounds(result)
    hallmarks = _extract_hallmarks(result)

    wearable_summary = {}
    if wearable_result:
        wearable_summary = {
            k: v.get("tier") for k, v in wearable_result.get("scored_metrics", {}).items()
        }

    return {
        "patient_id": archetype.id,
        "patient_name": archetype.name,
        "disease_context": archetype.disease_context,
        "elapsed_s": elapsed,
        "pass_count": passed,
        "total_assertions": total,
        "all_passed": passed == total,
        "key_outputs": {
            "phenoage_estimate": pa.get("phenoage_estimate"),
            "age_acceleration": pa.get("age_acceleration"),
            "mortality_10yr": pa.get("mortality_score_10yr"),
            "completeness_mode": pa.get("completeness_mode"),
            "hallmarks_active": hallmarks,
            "compounds_top3": [
                {"name": c.get("display_name"), "tier": c.get("evidence_tier")}
                for c in compounds[:3]
            ],
            "apoe_genotype": (genetic.get("apoe_status") or {}).get("genotype"),
            "apoe_risk_tier": (genetic.get("apoe_status") or {}).get("risk_tier"),
            "mthfr_activity_pct": (genetic.get("mthfr_status") or {}).get("combined_activity_pct"),
            "wearable_tiers": wearable_summary,
            "wearable_hallmark_signals": (wearable_result or {}).get("hallmark_signals"),
            "ascvd_10yr_pct": (result.get("ascvd_risk") or {}).get("ten_year_ascvd_risk_pct"),
            "ascvd_category": (result.get("ascvd_risk") or {}).get("risk_category"),
        },
        "assertions": assertion_results,
        "expected_findings": archetype.expected_findings,
    }


def main(ci_mode: bool = False):
    print("=" * 70)
    print("LONGIVITY DISEASE COHORT VALIDATION")
    print(f"Run at: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)

    results = []
    total_pass = 0
    total_assertions = 0

    for archetype in ALL_ARCHETYPES:
        print(f"\n▶ {archetype.name} ({archetype.disease_context})")
        r = run_patient(archetype)
        results.append(r)

        ko = r["key_outputs"]
        print(f"  PhenoAge:     {ko['phenoage_estimate']} (accel: {ko['age_acceleration']})")
        print(f"  10yr mort:    {ko['mortality_10yr']}")
        print(f"  Hallmarks:    {ko['hallmarks_active']}")
        print(f"  Top compounds:{ko['compounds_top3']}")
        if ko.get("apoe_genotype"):
            print(f"  APOE:         {ko['apoe_genotype']} ({ko['apoe_risk_tier']})")
        if ko.get("wearable_tiers"):
            print(f"  Wearables:    {ko['wearable_tiers']}")
        if ko.get("ascvd_10yr_pct") is not None:
            print(f"  ASCVD 10yr:   {ko['ascvd_10yr_pct']}% ({ko['ascvd_category']})")

        print(f"  Assertions:   {r['pass_count']}/{r['total_assertions']} passed")
        for a in r["assertions"]:
            status = "✓" if a["passed"] else "✗"
            print(f"    {status} {a['label']}: {a['detail']}")

        total_pass += r["pass_count"]
        total_assertions += r["total_assertions"]

    overall_pass_rate = round(total_pass / total_assertions * 100, 1) if total_assertions else 0
    all_cohorts_pass = all(r["all_passed"] for r in results)

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_patients": len(results),
        "total_assertions": total_assertions,
        "total_passed": total_pass,
        "overall_pass_rate_pct": overall_pass_rate,
        "all_cohorts_pass": all_cohorts_pass,
        "patients": results,
    }

    out_path = Path(__file__).parent / "cohort_validation_results.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print("\n" + "=" * 70)
    print(f"OVERALL: {total_pass}/{total_assertions} assertions passed ({overall_pass_rate}%)")
    print(f"All cohorts pass: {all_cohorts_pass}")
    print(f"Results saved: {out_path}")
    print("=" * 70)

    if ci_mode and not all_cohorts_pass:
        sys.exit(1)

    return summary


if __name__ == "__main__":
    ci_mode = "--ci-mode" in sys.argv
    main(ci_mode=ci_mode)
