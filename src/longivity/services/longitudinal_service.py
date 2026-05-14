"""
Longitudinal delta computation — compares two timestamped assessment payloads.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime

def _delta_direction(delta: float, pct_threshold: float = 0.05) -> str:
    if abs(delta) < pct_threshold * abs(delta + 1e-9):
        return "STABLE"
    return "IMPROVING" if delta < 0 else "WORSENING"

def compute_longitudinal_delta(
    current: Dict[str, Any],
    prior: Dict[str, Any],
    higher_is_better: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Compare current vs prior assessment payloads.
    higher_is_better: list of biomarker keys where higher value = better (e.g. hdl, albumin, vo2max)
    """
    higher_is_better_set = set(higher_is_better or [
        "albumin", "hdl_cholesterol", "lymphocyte_percent", "vo2max",
        "grip_strength", "25oh_vitamin_d", "igf1", "dhea_s", "free_testosterone",
        "adiponectin", "omega3_index", "klotho_serum", "bdnf_serum",
        "microbiome_diversity", "plasma_taurine",
    ])

    cur_bio = current.get("biomarkers") or {}
    pri_bio = prior.get("biomarkers") or {}

    biomarker_deltas = []
    for key in set(list(cur_bio.keys()) + list(pri_bio.keys())):
        cur_val = cur_bio.get(key)
        pri_val = pri_bio.get(key)
        if cur_val is None or pri_val is None:
            continue
        try:
            cur_f, pri_f = float(cur_val), float(pri_val)
        except (TypeError, ValueError):
            continue
        delta = cur_f - pri_f
        pct_change = (delta / pri_f * 100) if pri_f != 0 else None
        # For "higher is better" biomarkers, improvement = positive delta
        if key in higher_is_better_set:
            direction = "IMPROVING" if delta > 0 else ("WORSENING" if delta < 0 else "STABLE")
        else:
            direction = "IMPROVING" if delta < 0 else ("WORSENING" if delta > 0 else "STABLE")
        biomarker_deltas.append({
            "biomarker": key,
            "prior_value": pri_f,
            "current_value": cur_f,
            "delta": round(delta, 4),
            "pct_change": round(pct_change, 1) if pct_change is not None else None,
            "direction": direction,
        })

    # PhenoAge delta
    cur_pa = current.get("phenoage_estimate")
    pri_pa = prior.get("phenoage_estimate")
    phenoage_delta = None
    if cur_pa is not None and pri_pa is not None:
        d = float(cur_pa) - float(pri_pa)
        phenoage_delta = {
            "prior": pri_pa, "current": cur_pa, "delta": round(d, 2),
            "direction": "IMPROVING" if d < 0 else ("WORSENING" if d > 0 else "STABLE"),
            "interpretation": f"Biological age {'decreased' if d < 0 else 'increased'} by {abs(d):.1f} years",
        }

    # Days between visits
    days_between = None
    try:
        cur_ts = current.get("timestamp") or current.get("date")
        pri_ts = prior.get("timestamp") or prior.get("date")
        if cur_ts and pri_ts:
            d1 = datetime.fromisoformat(str(cur_ts).replace("Z", "+00:00"))
            d2 = datetime.fromisoformat(str(pri_ts).replace("Z", "+00:00"))
            days_between = abs((d1 - d2).days)
    except Exception:
        pass

    # Overall trajectory
    directions = [b["direction"] for b in biomarker_deltas]
    improving = directions.count("IMPROVING")
    worsening = directions.count("WORSENING")
    if improving + worsening == 0:
        trajectory = "STABLE"
    elif improving > worsening * 1.5:
        trajectory = "IMPROVING"
    elif worsening > improving * 1.5:
        trajectory = "WORSENING"
    else:
        trajectory = "MIXED"

    return {
        "status": "SUCCESS",
        "days_between_visits": days_between,
        "trajectory": trajectory,
        "phenoage_delta": phenoage_delta,
        "biomarker_deltas": sorted(biomarker_deltas, key=lambda x: x["direction"] == "WORSENING", reverse=True),
        "summary": {
            "total_biomarkers_compared": len(biomarker_deltas),
            "improving": improving,
            "worsening": worsening,
            "stable": directions.count("STABLE"),
        },
        "provenance": "CrisPRO Longitudinal Delta v1.0 (RUO)",
    }
