"""
Wearable data integration — maps HRV, sleep, VO2max, steps to longevity hallmarks.
"""
from __future__ import annotations
from typing import Any, Dict, Optional

WEARABLE_HALLMARK_MAP = {
    "hrv_rmssd": {
        "hallmarks": ["mitochondrial_dysfunction", "altered_intercellular_communication"],
        "direction": "LOW_IS_VULNERABLE",
        "thresholds": [
            {"tier": "OPTIMAL", "min": 50},
            {"tier": "MODERATE", "min": 30, "max": 50},
            {"tier": "HIGH_RISK", "max": 30},
        ],
        "unit": "ms",
        "provenance": "HRV4Training / Shaffer & Ginsberg 2017 (PMID 29034226)",
    },
    "vo2max": {
        "hallmarks": ["mitochondrial_dysfunction", "stem_cell_exhaustion", "cellular_senescence"],
        "direction": "LOW_IS_VULNERABLE",
        "thresholds": [
            {"tier": "OPTIMAL", "min": 45},
            {"tier": "MODERATE", "min": 30, "max": 45},
            {"tier": "HIGH_RISK", "max": 30},
        ],
        "unit": "mL/kg/min",
        "provenance": "AHA 2016 (PMID 27881567)",
    },
    "deep_sleep_pct": {
        "hallmarks": ["epigenetic_alterations", "mitochondrial_dysfunction"],
        "direction": "LOW_IS_VULNERABLE",
        "thresholds": [
            {"tier": "OPTIMAL", "min": 20},
            {"tier": "MODERATE", "min": 13, "max": 20},
            {"tier": "HIGH_RISK", "max": 13},
        ],
        "unit": "%",
        "provenance": "Walker 2017 (Why We Sleep)",
    },
    "rem_sleep_pct": {
        "hallmarks": ["altered_intercellular_communication", "epigenetic_alterations"],
        "direction": "LOW_IS_VULNERABLE",
        "thresholds": [
            {"tier": "OPTIMAL", "min": 20},
            {"tier": "MODERATE", "min": 15, "max": 20},
            {"tier": "HIGH_RISK", "max": 15},
        ],
        "unit": "%",
        "provenance": "Walker 2017 (Why We Sleep)",
    },
    "daily_steps": {
        "hallmarks": ["cellular_senescence", "mitochondrial_dysfunction"],
        "direction": "LOW_IS_VULNERABLE",
        "thresholds": [
            {"tier": "OPTIMAL", "min": 8000},
            {"tier": "MODERATE", "min": 5000, "max": 8000},
            {"tier": "HIGH_RISK", "max": 5000},
        ],
        "unit": "steps/day",
        "provenance": "Paluch et al. 2022 (PMID 35416941)",
    },
    "resting_heart_rate": {
        "hallmarks": ["mitochondrial_dysfunction", "altered_intercellular_communication"],
        "direction": "HIGH_IS_VULNERABLE",
        "thresholds": [
            {"tier": "OPTIMAL", "max": 60},
            {"tier": "MODERATE", "min": 60, "max": 75},
            {"tier": "HIGH_RISK", "min": 75},
        ],
        "unit": "bpm",
        "provenance": "Cooney et al. 2010 (PMID 20823386)",
    },
}

def _score_wearable_metric(key: str, value: float) -> Dict[str, Any]:
    spec = WEARABLE_HALLMARK_MAP.get(key)
    if not spec:
        return {"tier": "UNKNOWN", "hallmarks": []}
    for t in spec["thresholds"]:
        lo = t.get("min", float("-inf"))
        hi = t.get("max", float("inf"))
        if lo <= value < hi or (t.get("min") is not None and value >= t["min"] and t.get("max") is None):
            return {"tier": t["tier"], "hallmarks": spec["hallmarks"], "unit": spec["unit"]}
    return {"tier": "UNKNOWN", "hallmarks": spec["hallmarks"], "unit": spec.get("unit")}

def score_wearables(wearable_data: Dict[str, Any]) -> Dict[str, Any]:
    """Score wearable metrics and map to longevity hallmarks."""
    scored = {}
    hallmark_signals: Dict[str, float] = {}

    for key, value in wearable_data.items():
        try:
            v = float(value)
        except (TypeError, ValueError):
            continue
        result = _score_wearable_metric(key, v)
        scored[key] = {"value": v, **result}
        tier_score = {"OPTIMAL": 0.0, "MODERATE": 0.5, "HIGH_RISK": 1.0}.get(result["tier"], 0.5)
        for hm in result.get("hallmarks", []):
            hallmark_signals[hm] = hallmark_signals.get(hm, 0.0) + tier_score

    return {
        "status": "SUCCESS",
        "scored_metrics": scored,
        "hallmark_signals": hallmark_signals,
        "metrics_scored": len(scored),
        "provenance": "CrisPRO Wearable Integration v1.0 (RUO)",
        "disclaimer": "Wearable-derived metrics are consumer-grade estimates. Not clinical measurements.",
    }
