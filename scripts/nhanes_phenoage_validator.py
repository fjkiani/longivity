"""
NHANES PhenoAge Validator
=========================
Generates a synthetic NHANES III-style cohort (N=1000, 250 per decade: 40s/50s/60s/70s)
and validates the PhenoAge longevity service against expected biological-age trends.

Reference values from Levine 2018 (PMID 29676998) Table 1.

Usage:
    cd /workspace/longivity && python scripts/nhanes_phenoage_validator.py
"""

from __future__ import annotations

import json
import logging
import os
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

# ---------------------------------------------------------------------------
# Path setup — allow running from repo root or scripts/ directory
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from longivity.services.longevity_phenoage_level0 import run_longevity_assessment_level0  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# NHANES III reference values (Levine 2018, Table 1)
# Format: biomarker -> (mean, sd)
# ---------------------------------------------------------------------------
NHANES_REFERENCE: Dict[str, Any] = {
    "40s": {
        "age_mean": 45,
        "albumin": (4.4, 0.35),
        "creatinine": (0.95, 0.22),
        "glucose": (98, 14),
        "crp": (0.25, 0.40),
        "lymphocyte_percent": (33, 8),
        "mcv": (90, 5),
        "rdw": (13.0, 0.9),
        "alkaline_phosphatase": (68, 22),
        "wbc": (6.8, 1.8),
    },
    "50s": {
        "age_mean": 55,
        "albumin": (4.3, 0.35),
        "creatinine": (1.0, 0.22),
        "glucose": (103, 16),
        "crp": (0.30, 0.45),
        "lymphocyte_percent": (31, 8),
        "mcv": (91, 5),
        "rdw": (13.2, 0.9),
        "alkaline_phosphatase": (72, 24),
        "wbc": (6.9, 1.8),
    },
    "60s": {
        "age_mean": 65,
        "albumin": (4.2, 0.38),
        "creatinine": (1.05, 0.25),
        "glucose": (108, 18),
        "crp": (0.40, 0.55),
        "lymphocyte_percent": (29, 8),
        "mcv": (91, 5),
        "rdw": (13.5, 1.0),
        "alkaline_phosphatase": (76, 26),
        "wbc": (7.0, 1.9),
    },
    "70s": {
        "age_mean": 75,
        "albumin": (4.0, 0.40),
        "creatinine": (1.1, 0.28),
        "glucose": (112, 20),
        "crp": (0.55, 0.70),
        "lymphocyte_percent": (27, 8),
        "mcv": (92, 5),
        "rdw": (14.0, 1.1),
        "alkaline_phosphatase": (80, 28),
        "wbc": (7.2, 2.0),
    },
}

# Decade -> (start_age, end_age)
DECADE_AGE_RANGE: Dict[str, Tuple[int, int]] = {
    "40s": (40, 50),
    "50s": (50, 60),
    "60s": (60, 70),
    "70s": (70, 80),
}

N_PER_DECADE = 250
TOTAL_N = N_PER_DECADE * len(NHANES_REFERENCE)  # 1000


# ---------------------------------------------------------------------------
# Cohort generation
# ---------------------------------------------------------------------------

def _sample_biomarkers(rng: np.random.Generator, ref: Dict[str, Any]) -> Dict[str, float]:
    """Sample one patient's biomarkers from NHANES reference distributions."""

    def norm(mean: float, sd: float) -> float:
        return float(rng.normal(mean, sd))

    albumin = float(np.clip(norm(*ref["albumin"]), 2.0, 6.0))
    creatinine = float(np.clip(norm(*ref["creatinine"]), 0.4, 3.0))
    glucose = float(np.clip(norm(*ref["glucose"]), 60.0, 300.0))

    # CRP: log-normal distribution (right-skewed in population)
    crp_mean, _ = ref["crp"]
    crp_raw = float(np.exp(rng.normal(np.log(crp_mean), 0.8)))
    crp = float(np.clip(crp_raw, 0.01, 10.0))

    lymphocyte_percent = float(np.clip(norm(*ref["lymphocyte_percent"]), 5.0, 60.0))
    mcv = float(np.clip(norm(*ref["mcv"]), 70.0, 115.0))
    rdw = float(np.clip(norm(*ref["rdw"]), 10.0, 20.0))
    alkaline_phosphatase = float(np.clip(norm(*ref["alkaline_phosphatase"]), 20.0, 300.0))
    wbc = float(np.clip(norm(*ref["wbc"]), 2.0, 15.0))

    return {
        "albumin": round(albumin, 2),           # g/dL — service interprets bare albumin as g/dL
        "creatinine": round(creatinine, 3),     # mg/dL — service interprets bare creatinine as mg/dL
        "glucose_mg_dl": round(glucose, 1),     # mg/dL — explicit key triggers mmol/L conversion
        "crp": round(crp, 4),                   # mg/L — service maps bare crp to hsCRP mg/L
        "lymphocyte_percent": round(lymphocyte_percent, 1),
        "mcv": round(mcv, 1),
        "rdw": round(rdw, 2),
        "alkaline_phosphatase": round(alkaline_phosphatase, 1),
        "wbc": round(wbc, 2),
    }


def generate_cohort(rng: np.random.Generator) -> List[Dict[str, Any]]:
    """Generate N=1000 synthetic patients (250 per decade)."""
    patients: List[Dict[str, Any]] = []
    patient_id = 0

    for decade in ["40s", "50s", "60s", "70s"]:
        ref = NHANES_REFERENCE[decade]
        age_start, age_end = DECADE_AGE_RANGE[decade]

        for _ in range(N_PER_DECADE):
            chron_age = float(rng.uniform(age_start, age_end))
            biomarkers = _sample_biomarkers(rng, ref)

            patients.append(
                {
                    "patient_id": patient_id,
                    "age_decade": decade,
                    "chronological_age": round(chron_age, 2),
                    "biomarkers": biomarkers,
                }
            )
            patient_id += 1

    return patients


# ---------------------------------------------------------------------------
# Assessment runner
# ---------------------------------------------------------------------------

def run_assessments(patients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run PhenoAge assessment on each patient; skip on error."""
    results: List[Dict[str, Any]] = []

    for p in patients:
        pid = p["patient_id"]
        try:
            payload = {
                "biomarkers": p["biomarkers"],
                "age": int(round(p["chronological_age"])),
            }
            response = run_longevity_assessment_level0(payload)

            pa = response.get("phenoage_analysis", {})

            # Extract fields — handle both key variants defensively
            phenoage_estimate: Optional[float] = pa.get("phenoage_estimate")
            # Service uses "mortality_score_10yr" internally
            mortality_score: Optional[float] = (
                pa.get("mortality_score_10yr")
                or pa.get("mortality_score")
            )
            # Service uses "age_acceleration" internally
            acceleration: Optional[float] = (
                pa.get("age_acceleration")
                or pa.get("acceleration")
            )

            if phenoage_estimate is None:
                logger.warning(
                    "Patient %d: phenoage_estimate is None (completeness_mode=%s) — skipping",
                    pid,
                    pa.get("completeness_mode"),
                )
                continue

            results.append(
                {
                    "patient_id": pid,
                    "age_decade": p["age_decade"],
                    "chronological_age": p["chronological_age"],
                    "phenoage": round(float(phenoage_estimate), 2),
                    "acceleration": round(float(acceleration), 2) if acceleration is not None else None,
                    "mortality_score": round(float(mortality_score), 6) if mortality_score is not None else None,
                }
            )

        except Exception as exc:  # noqa: BLE001
            logger.warning("Patient %d: assessment failed — %s", pid, exc)

    return results


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def compute_statistics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute Pearson r, mean acceleration, and % accelerated by decade."""
    if not results:
        return {}

    chron_ages = np.array([r["chronological_age"] for r in results])
    phenoages = np.array([r["phenoage"] for r in results])

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pearson_r, pearson_p = stats.pearsonr(chron_ages, phenoages)

    n_valid = len(results)
    n_accelerated_overall = sum(1 for r in results if r["phenoage"] > r["chronological_age"])
    pct_accelerated_overall = round(100.0 * n_accelerated_overall / n_valid, 1) if n_valid else 0.0

    by_decade: Dict[str, Dict[str, Any]] = {}
    for decade in ["40s", "50s", "60s", "70s"]:
        decade_rows = [r for r in results if r["age_decade"] == decade]
        if not decade_rows:
            by_decade[decade] = {}
            continue
        accel_vals = [r["acceleration"] for r in decade_rows if r["acceleration"] is not None]
        n_dec = len(decade_rows)
        n_acc = sum(1 for r in decade_rows if r["phenoage"] > r["chronological_age"])
        by_decade[decade] = {
            "n": n_dec,
            "mean_phenoage": round(float(np.mean([r["phenoage"] for r in decade_rows])), 2),
            "mean_chronological_age": round(float(np.mean([r["chronological_age"] for r in decade_rows])), 2),
            "mean_acceleration": round(float(np.mean(accel_vals)), 2) if accel_vals else None,
            "pct_accelerated": round(100.0 * n_acc / n_dec, 1) if n_dec else 0.0,
        }

    return {
        "pearson_r": round(float(pearson_r), 4),
        "pearson_p": float(pearson_p),
        "n_patients": TOTAL_N,
        "n_valid": n_valid,
        "pct_accelerated_overall": pct_accelerated_overall,
        "by_decade": by_decade,
    }


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def save_csv(results: List[Dict[str, Any]], out_path: Path) -> None:
    """Save results to CSV."""
    import csv

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["patient_id", "age_decade", "chronological_age", "phenoage", "acceleration", "mortality_score"]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    logger.info("Saved %d rows to %s", len(results), out_path)


def save_json(summary: Dict[str, Any], out_path: Path) -> None:
    """Save summary statistics to JSON."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logger.info("Saved summary to %s", out_path)


def print_summary_table(summary: Dict[str, Any]) -> None:
    """Print a formatted summary table to stdout."""
    print("\n" + "=" * 65)
    print("  NHANES PhenoAge Validation Summary")
    print("=" * 65)
    n_patients = summary.get('n_patients', 'N/A')
    n_valid = summary.get('n_valid', 'N/A')
    pearson_r = summary.get('pearson_r')
    pearson_p = summary.get('pearson_p')
    pct_acc = summary.get('pct_accelerated_overall', 'N/A')

    print(f"  Total patients generated : {n_patients}")
    print(f"  Valid assessments        : {n_valid}")
    if pearson_r is not None and pearson_p is not None:
        print(f"  Pearson r (PA vs age)    : {pearson_r:.4f}  (p={pearson_p:.2e})")
    else:
        print("  Pearson r (PA vs age)    : N/A (no valid results)")
    print(f"  % Accelerated (overall)  : {pct_acc}%")
    print()
    print(f"  {'Decade':<8} {'N':>5} {'Mean Age':>10} {'Mean PA':>10} {'Mean Accel':>12} {'% Accel':>9}")
    print("  " + "-" * 58)
    for decade in ["40s", "50s", "60s", "70s"]:
        d = summary.get("by_decade", {}).get(decade, {})
        if not d:
            continue
        accel_str = f"{d['mean_acceleration']:+.2f}" if d.get("mean_acceleration") is not None else "N/A"
        print(
            f"  {decade:<8} {d['n']:>5} {d['mean_chronological_age']:>10.1f} "
            f"{d['mean_phenoage']:>10.1f} {accel_str:>12} {d['pct_accelerated']:>8.1f}%"
        )
    print("=" * 65 + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    repo_root = _REPO_ROOT
    datasets_dir = repo_root / "datasets"

    logger.info("Generating synthetic NHANES cohort (N=%d, seed=42) ...", TOTAL_N)
    rng = np.random.default_rng(seed=42)
    patients = generate_cohort(rng)
    logger.info("Generated %d patients across 4 decades.", len(patients))

    logger.info("Running PhenoAge assessments ...")
    results = run_assessments(patients)
    logger.info("Valid assessments: %d / %d", len(results), len(patients))

    logger.info("Computing statistics ...")
    summary = compute_statistics(results)

    # Save outputs
    csv_path = datasets_dir / "nhanes_validation_results.csv"
    json_path = datasets_dir / "nhanes_validation_summary.json"
    save_csv(results, csv_path)
    save_json(summary, json_path)

    # Print table
    print_summary_table(summary)


if __name__ == "__main__":
    main()
