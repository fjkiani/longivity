"""
N-of-1 Trial Engine for Personalized Longevity Interventions.

Generates a structured single-subject crossover trial protocol for a given
compound + biomarker panel. Tracks expected delta per biomarker per compound
based on published effect sizes, and produces a monitoring schedule.

Design:
  Phase A (Baseline)   → 4 weeks observation, no intervention
  Phase B (Treatment)  → 8 weeks intervention
  Phase C (Washout)    → 4 weeks washout
  Phase D (Re-measure) → 4 weeks re-measure (optional crossover to second compound)

Each trial arm is anchored to:
  - Compound evidence tier (MR_VALIDATED > RCT > OBSERVATIONAL)
  - Expected biomarker deltas from published effect sizes
  - Monitoring frequency (weekly wearable + monthly lab)
  - Primary endpoint: PhenoAge delta at 12 weeks
  - Secondary endpoints: per-biomarker z-score change

References:
  - Lillie 2011 (BMJ) — N-of-1 trial methodology
  - Duan 2013 (JAMA) — N-of-1 aggregation
  - Fabian 2025 (Human Genomics) — MR anchor for omega_3
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from .mr_evidence_registry import (
    get_evidence_tier,
    get_best_mr_record,
    evidence_tier_label,
)

# ---------------------------------------------------------------------------
# Expected biomarker effect sizes per compound (from published RCT/MR data)
# Format: compound_id → {biomarker_canonical_key: {"delta_mean": float, "unit": str, "pmid": str}}
# Negative delta = reduction (protective direction for most biomarkers)
# ---------------------------------------------------------------------------

COMPOUND_BIOMARKER_EFFECTS: Dict[str, Dict[str, Dict]] = {
    "omega_3": {
        "crp_mg_l": {
            "delta_mean": -0.5,
            "delta_sd": 0.3,
            "unit": "mg/L",
            "direction": "decrease",
            "pmid": "20085953",
            "note": "EPA/DHA 2g/day → CRP reduction in RCT meta-analysis",
        },
        "triglycerides": {
            "delta_mean": -25.0,
            "delta_sd": 10.0,
            "unit": "mg/dL",
            "direction": "decrease",
            "pmid": "20085953",
            "note": "Omega-3 triglyceride lowering (well-established)",
        },
    },
    "berberine": {
        "glucose_serum": {
            "delta_mean": -15.0,
            "delta_sd": 8.0,
            "unit": "mg/dL",
            "direction": "decrease",
            "pmid": "34956436",
            "note": "Berberine 1500mg/day → fasting glucose reduction (meta-analysis of RCTs)",
        },
        "hba1c": {
            "delta_mean": -0.5,
            "delta_sd": 0.2,
            "unit": "%",
            "direction": "decrease",
            "pmid": "34956436",
            "note": "HbA1c reduction in T2DM RCTs",
        },
    },
    "metformin": {
        "glucose_serum": {
            "delta_mean": -20.0,
            "delta_sd": 10.0,
            "unit": "mg/dL",
            "direction": "decrease",
            "pmid": "34385711",
            "note": "Metformin fasting glucose reduction (clinical pharmacology)",
        },
        "crp_mg_l": {
            "delta_mean": -0.3,
            "delta_sd": 0.2,
            "unit": "mg/L",
            "direction": "decrease",
            "pmid": "34385711",
            "note": "Metformin anti-inflammatory effect (secondary endpoint)",
        },
    },
    "vitamin_d3": {
        "crp_mg_l": {
            "delta_mean": -0.4,
            "delta_sd": 0.3,
            "unit": "mg/L",
            "direction": "decrease",
            "pmid": "36055464",
            "note": "Vitamin D3 supplementation → CRP reduction (MR-supported)",
        },
    },
    "nmn": {
        "nad_whole_blood": {
            "delta_mean": 40.0,
            "delta_sd": 15.0,
            "unit": "μM",
            "direction": "increase",
            "pmid": "34906454",
            "note": "NMN 300mg/day → whole blood NAD+ increase (RCT)",
        },
    },
    "urolithin_a": {
        "mitochondrial_function_score": {
            "delta_mean": 0.15,
            "delta_sd": 0.08,
            "unit": "normalized",
            "direction": "increase",
            "pmid": "35817964",
            "note": "Urolithin A → mitophagy improvement (RCT)",
        },
    },
    "glycine": {
        "crp_mg_l": {
            "delta_mean": -0.3,
            "delta_sd": 0.2,
            "unit": "mg/L",
            "direction": "decrease",
            "pmid": "33234399",
            "note": "Glycine supplementation → CRP reduction (RCT)",
        },
        "albumin": {
            "delta_mean": 0.1,
            "delta_sd": 0.05,
            "unit": "g/dL",
            "direction": "increase",
            "pmid": "33234399",
            "note": "Glycine → albumin synthesis support",
        },
    },
    "rapamycin": {
        "crp_mg_l": {
            "delta_mean": -0.2,
            "delta_sd": 0.15,
            "unit": "mg/L",
            "direction": "decrease",
            "pmid": None,
            "note": "mTOR inhibition → inflammatory marker reduction (preclinical extrapolation; human data limited)",
        },
    },
}

# Monitoring schedule templates
MONITORING_SCHEDULE = {
    "weekly_wearable": [
        "resting_heart_rate",
        "hrv_rmssd",
        "sleep_efficiency_pct",
        "steps_per_day",
        "spo2_avg",
    ],
    "monthly_lab": [
        "crp_mg_l",
        "glucose_serum",
        "albumin",
        "creatinine",
        "wbc_1000_ul",
        "lymphocyte_pct",
        "rdw_pct",
        "mcv_fl",
        "alkaline_phosphatase_u_l",
    ],
    "primary_endpoint": "phenoage_estimate",
    "primary_endpoint_timepoints_weeks": [0, 8, 16],
}


def generate_nof1_protocol(
    patient_id: str,
    age: int,
    baseline_biomarkers: Dict[str, float],
    compound_id: str,
    compound_display_name: Optional[str] = None,
    dose_info: Optional[Dict] = None,
    crossover_compound_id: Optional[str] = None,
    start_date: Optional[date] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a complete N-of-1 trial protocol for a single patient + compound.

    Parameters
    ----------
    patient_id : str
        De-identified patient identifier.
    age : int
        Patient age in years.
    baseline_biomarkers : dict
        Current biomarker values (canonical keys).
    compound_id : str
        Compound to test (must match longevity_compound_hallmark_map.json keys).
    compound_display_name : str, optional
        Human-readable compound name.
    dose_info : dict, optional
        Dose information dict (range_mg, frequency, etc.).
    crossover_compound_id : str, optional
        Second compound for crossover arm (Phase D).
    start_date : date, optional
        Trial start date. Defaults to today.
    notes : str, optional
        Clinician notes.

    Returns
    -------
    dict
        Complete N-of-1 protocol with phases, monitoring schedule, expected deltas,
        evidence tier, and MR anchor if available.
    """
    trial_id = f"NOF1-{uuid.uuid4().hex[:8].upper()}"
    start = start_date or date.today()

    evidence_tier = get_evidence_tier(compound_id)
    mr_record = get_best_mr_record(compound_id)
    expected_effects = COMPOUND_BIOMARKER_EFFECTS.get(compound_id, {})

    # Build phase timeline
    phases = _build_phases(start, compound_id, crossover_compound_id, dose_info)

    # Build expected delta table for biomarkers present in baseline
    delta_table = _build_delta_table(baseline_biomarkers, compound_id, expected_effects)

    # Build monitoring plan
    monitoring = _build_monitoring_plan(start, phases)

    # Primary endpoint power note
    power_note = _power_note(evidence_tier, len(delta_table))

    protocol = {
        "trial_id": trial_id,
        "patient_id": patient_id,
        "age": age,
        "compound_id": compound_id,
        "compound_display_name": compound_display_name or compound_id,
        "evidence_tier": evidence_tier,
        "evidence_tier_label": evidence_tier_label(evidence_tier),
        "mr_anchor": {
            "clock": mr_record["clock"],
            "method": mr_record["method"],
            "p_value": mr_record["p_value"],
            "direction": mr_record["direction"],
            "citation": mr_record["citation"],
            "doi": mr_record.get("doi"),
            "pmid": mr_record.get("pmid"),
            "note": mr_record["note"],
        } if mr_record else None,
        "design": {
            "type": "single_subject_crossover",
            "phases": phases,
            "total_duration_weeks": sum(p["duration_weeks"] for p in phases),
            "primary_endpoint": MONITORING_SCHEDULE["primary_endpoint"],
            "primary_endpoint_timepoints_weeks": MONITORING_SCHEDULE["primary_endpoint_timepoints_weeks"],
            "secondary_endpoints": list(expected_effects.keys()),
        },
        "baseline_biomarkers": baseline_biomarkers,
        "expected_deltas": delta_table,
        "monitoring_schedule": monitoring,
        "power_note": power_note,
        "clinician_notes": notes or "",
        "ruo_disclaimer": (
            "Research Use Only. This protocol is generated by an algorithmic system "
            "and does not constitute medical advice. All interventions require physician oversight."
        ),
        "methodology_references": [
            {"citation": "Lillie 2011", "pmid": "21406327", "note": "N-of-1 trial methodology (BMJ)"},
            {"citation": "Duan 2013", "pmid": "23839752", "note": "N-of-1 aggregation for evidence synthesis (JAMA)"},
        ],
    }

    if crossover_compound_id:
        protocol["crossover_compound_id"] = crossover_compound_id
        protocol["crossover_evidence_tier"] = get_evidence_tier(crossover_compound_id)

    return protocol


def _build_phases(
    start: date,
    compound_id: str,
    crossover_id: Optional[str],
    dose_info: Optional[Dict],
) -> List[Dict]:
    """Build the 4-phase timeline."""
    phases = []
    cursor = start

    # Phase A: Baseline
    phases.append({
        "phase": "A",
        "name": "Baseline Observation",
        "start_date": cursor.isoformat(),
        "duration_weeks": 4,
        "end_date": (cursor + timedelta(weeks=4)).isoformat(),
        "intervention": None,
        "instructions": "No new supplements. Maintain stable diet and exercise. Collect baseline labs at week 0 and week 4.",
    })
    cursor += timedelta(weeks=4)

    # Phase B: Treatment
    dose_str = ""
    if dose_info:
        dose_str = f"{dose_info.get('range_mg', '')} mg, {dose_info.get('frequency', 'daily')}"
    phases.append({
        "phase": "B",
        "name": f"Treatment — {compound_id}",
        "start_date": cursor.isoformat(),
        "duration_weeks": 8,
        "end_date": (cursor + timedelta(weeks=8)).isoformat(),
        "intervention": compound_id,
        "dose": dose_str or "per clinician guidance",
        "instructions": (
            f"Begin {compound_id} at prescribed dose. "
            "Weekly wearable check-ins. Lab draw at week 4 and week 8 of this phase."
        ),
    })
    cursor += timedelta(weeks=8)

    # Phase C: Washout
    phases.append({
        "phase": "C",
        "name": "Washout",
        "start_date": cursor.isoformat(),
        "duration_weeks": 4,
        "end_date": (cursor + timedelta(weeks=4)).isoformat(),
        "intervention": None,
        "instructions": "Discontinue compound. Monitor for rebound effects. Lab draw at end of washout.",
    })
    cursor += timedelta(weeks=4)

    # Phase D: Re-measure / crossover
    if crossover_id:
        phases.append({
            "phase": "D",
            "name": f"Crossover — {crossover_id}",
            "start_date": cursor.isoformat(),
            "duration_weeks": 8,
            "end_date": (cursor + timedelta(weeks=8)).isoformat(),
            "intervention": crossover_id,
            "dose": "per clinician guidance",
            "instructions": (
                f"Begin {crossover_id} at prescribed dose. "
                "Weekly wearable check-ins. Final lab draw at end of phase."
            ),
        })
    else:
        phases.append({
            "phase": "D",
            "name": "Re-measure",
            "start_date": cursor.isoformat(),
            "duration_weeks": 4,
            "end_date": (cursor + timedelta(weeks=4)).isoformat(),
            "intervention": None,
            "instructions": "Final biomarker panel. Compare to Phase A baseline and Phase B endpoint.",
        })

    return phases


def _build_delta_table(
    baseline: Dict[str, float],
    compound_id: str,
    effects: Dict[str, Dict],
) -> List[Dict]:
    """Build expected delta table for biomarkers present in baseline."""
    rows = []
    for bm_key, effect in effects.items():
        baseline_val = baseline.get(bm_key)
        row: Dict[str, Any] = {
            "biomarker": bm_key,
            "baseline_value": baseline_val,
            "expected_delta_mean": effect["delta_mean"],
            "expected_delta_sd": effect["delta_sd"],
            "unit": effect["unit"],
            "direction": effect["direction"],
            "pmid": effect.get("pmid"),
            "note": effect.get("note", ""),
            "baseline_present": baseline_val is not None,
        }
        if baseline_val is not None:
            row["expected_post_value"] = round(baseline_val + effect["delta_mean"], 2)
        rows.append(row)

    # Also include biomarkers in baseline that have no known effect (for monitoring)
    known_bms = set(effects.keys())
    for bm_key, val in baseline.items():
        if bm_key not in known_bms:
            rows.append({
                "biomarker": bm_key,
                "baseline_value": val,
                "expected_delta_mean": None,
                "expected_delta_sd": None,
                "unit": None,
                "direction": "unknown",
                "pmid": None,
                "note": "No published effect size for this compound-biomarker pair; monitor for unexpected changes.",
                "baseline_present": True,
                "expected_post_value": None,
            })
    return rows


def _build_monitoring_plan(start: date, phases: List[Dict]) -> Dict:
    """Build monitoring schedule with specific dates."""
    lab_dates = []
    wearable_start = start.isoformat()

    for phase in phases:
        phase_start = date.fromisoformat(phase["start_date"])
        phase_end = date.fromisoformat(phase["end_date"])
        # Lab at start and end of each phase
        lab_dates.append({
            "date": phase_start.isoformat(),
            "phase": phase["phase"],
            "type": "lab_draw",
            "panel": MONITORING_SCHEDULE["monthly_lab"],
        })
        lab_dates.append({
            "date": phase_end.isoformat(),
            "phase": phase["phase"],
            "type": "lab_draw",
            "panel": MONITORING_SCHEDULE["monthly_lab"],
        })

    return {
        "wearable_tracking": {
            "start_date": wearable_start,
            "frequency": "continuous",
            "metrics": MONITORING_SCHEDULE["weekly_wearable"],
        },
        "lab_draws": lab_dates,
        "primary_endpoint_draws": [
            {
                "week": w,
                "date": (start + timedelta(weeks=w)).isoformat(),
                "measure": MONITORING_SCHEDULE["primary_endpoint"],
            }
            for w in MONITORING_SCHEDULE["primary_endpoint_timepoints_weeks"]
        ],
    }


def _power_note(evidence_tier: str, n_biomarkers: int) -> str:
    """Generate a power/confidence note based on evidence tier."""
    if evidence_tier == "MR_VALIDATED":
        return (
            "MR_VALIDATED tier: Mendelian Randomization evidence supports causal effect on aging clock endpoint. "
            "N-of-1 design is well-powered to detect expected delta given published effect sizes. "
            "Primary endpoint (PhenoAge) change at 8 weeks is the pre-specified primary outcome."
        )
    elif evidence_tier == "RCT":
        return (
            "RCT tier: Human randomized trial evidence available. "
            "N-of-1 design can detect within-person changes; "
            "interpret with caution given single-subject design. "
            "Aggregate with other N-of-1 results for population-level inference."
        )
    else:
        return (
            "OBSERVATIONAL tier: Limited human causal evidence. "
            "This N-of-1 trial is exploratory. "
            "Biomarker changes should be interpreted as hypothesis-generating, not confirmatory."
        )
