"""
Benchmark API Router — Longivity
Exposes cohort validation results and eval scores for the frontend BenchmarkPanel.

Endpoints:
  GET /api/v1/longevity/benchmark/cohorts   — cohort validation summary
  GET /api/v1/longevity/benchmark/evals     — API + LLM eval scores
  GET /api/v1/longevity/benchmark/trust     — trust anchor manifest
"""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone

router = APIRouter(prefix="/api/v1/longevity/benchmark", tags=["benchmark"])

RESOURCES_DIR = Path(__file__).parent.parent / "resources" / "benchmark"
TESTS_DIR = Path(__file__).parent.parent.parent.parent / "tests"


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Resource not found: {path.name}")
    with open(path) as f:
        return json.load(f)


@router.get("/cohorts")
async def get_cohort_results():
    """
    Returns cohort validation summary: pass/fail per patient archetype.
    Source: tests/cohorts/cohort_validation_results.json
    """
    results_path = TESTS_DIR / "cohorts" / "cohort_validation_results.json"
    data = _load_json(results_path)

    # Shape for frontend BenchmarkPanel
    patients = []
    for p in data.get("patients", []):
        patients.append({
            "patient_id": p["patient_id"],
            "patient_name": p["patient_name"],
            "disease_context": p["disease_context"],
            "pass_count": p["pass_count"],
            "total_assertions": p["total_assertions"],
            "all_passed": p["all_passed"],
            "elapsed_s": p.get("elapsed_s"),
        })

    return {
        "run_at": data.get("timestamp"),
        "total_assertions": data["total_assertions"],
        "total_passed": data["total_passed"],
        "overall_pass_rate_pct": data["overall_pass_rate_pct"],
        "all_cohorts_pass": data["all_cohorts_pass"],
        "patients": patients,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/evals")
async def get_eval_scores():
    """
    Returns API correctness + LLM output quality eval scores.
    Sources: tests/eval/api_eval_results.json + tests/eval/llm_eval_results.json
    """
    api_path = TESTS_DIR / "eval" / "api_eval_results.json"
    llm_path = TESTS_DIR / "eval" / "llm_eval_results.json"

    api_data = _load_json(api_path) if api_path.exists() else None
    llm_data = _load_json(llm_path) if llm_path.exists() else None

    result = {"retrieved_at": datetime.now(timezone.utc).isoformat()}

    if api_data:
        result["api_eval"] = {
            "run_at": api_data.get("run_at"),
            "total_tests": api_data.get("total_tests"),
            "passed": api_data.get("passed"),
            "failed": api_data.get("failed"),
            "pass_rate_pct": api_data.get("pass_rate_pct"),
            "ci_threshold_pct": api_data.get("ci_threshold_pct"),
            "ci_pass": api_data.get("ci_pass"),
        }

    if llm_data:
        result["llm_eval"] = {
            "run_at": llm_data.get("run_at"),
            "rubric_criteria": llm_data.get("rubric_criteria"),
            "threshold_per_response": llm_data.get("threshold_per_response"),
            "n_responses": llm_data.get("n_responses"),
            "n_passed": llm_data.get("n_passed"),
            "overall_pass_rate_pct": llm_data.get("overall_pass_rate_pct"),
            "overall_pass": llm_data.get("overall_pass"),
        }

    return result


@router.get("/trust")
async def get_trust_anchors():
    """
    Returns trust anchor manifest: deterministic formulas, MR evidence, published thresholds.
    Source: src/longivity/resources/benchmark/trust_anchors.json
    """
    trust_path = RESOURCES_DIR / "trust_anchors.json"
    data = _load_json(trust_path)

    # Summarize by type for frontend
    by_type: dict = {}
    for anchor in data.get("anchors", []):
        t = anchor.get("type", "UNKNOWN")
        by_type.setdefault(t, []).append({
            "id": anchor["id"],
            "name": anchor["name"],
            "citation": anchor.get("citation", {}),
            "key_claim": anchor.get("key_claim", ""),
        })

    return {
        "version": data.get("version"),
        "generated_at": data.get("generated_at"),
        "total_anchors": len(data.get("anchors", [])),
        "by_type": by_type,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }
