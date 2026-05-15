"""
Biomarker Registry Service — loads and queries the master biomarker registry,
test panel catalog, hallmark-to-panel map, and escalation rules.

All data is loaded once at import time from JSON files in resources/.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_RESOURCES = Path(__file__).parent.parent / "resources"


# ─────────────────────────────────────────────────────────────────────────────
# Loaders (cached at module level)
# ─────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_registry() -> Dict[str, Any]:
    path = _RESOURCES / "biomarker_registry.json"
    with open(path) as f:
        data = json.load(f)
    markers = data.get("biomarkers", [])
    # Build lookup dict
    by_key: Dict[str, Dict] = {}
    for m in markers:
        key = m.get("marker_key")
        if key:
            by_key[key] = m
    return {"markers": markers, "by_key": by_key, "metadata": data.get("_metadata", {})}


@lru_cache(maxsize=1)
def _load_panels() -> Dict[str, Any]:
    path = _RESOURCES / "test_panels.json"
    with open(path) as f:
        data = json.load(f)
    panels = data.get("panels", [])
    by_id: Dict[str, Dict] = {p["panel_id"]: p for p in panels}
    return {"panels": panels, "by_id": by_id, "metadata": data.get("_metadata", {})}


@lru_cache(maxsize=1)
def _load_hallmark_map() -> Dict[str, Any]:
    path = _RESOURCES / "hallmark_to_panels.json"
    with open(path) as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_escalation_rules() -> List[Dict]:
    path = _RESOURCES / "escalation_rules.json"
    with open(path) as f:
        data = json.load(f)
    return data.get("rules", [])


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def get_all_markers() -> List[Dict]:
    """Return all markers in the registry."""
    return _load_registry()["markers"]


def get_marker(marker_key: str) -> Optional[Dict]:
    """Look up a single marker by key. Returns None if not found."""
    return _load_registry()["by_key"].get(marker_key)


def get_markers_by_domain(domain: str) -> List[Dict]:
    """Return all markers in a given domain."""
    return [m for m in get_all_markers() if m.get("domain") == domain]


def get_markers_by_tier(tier: str) -> List[Dict]:
    """Return all markers with a given ordering_tier (tier_1 / tier_2 / tier_3)."""
    return [m for m in get_all_markers() if m.get("ordering_tier") == tier]


def get_all_panels() -> List[Dict]:
    """Return all orderable test panels."""
    return _load_panels()["panels"]


def get_panel(panel_id: str) -> Optional[Dict]:
    """Look up a single panel by ID."""
    return _load_panels()["by_id"].get(panel_id)


def get_panels_by_tier(tier: str) -> List[Dict]:
    """Return panels for a given ordering tier."""
    return [p for p in get_all_panels() if p.get("ordering_tier") == tier]


def get_hallmark_map() -> Dict[str, Any]:
    """Return the full hallmark-to-panels mapping."""
    return _load_hallmark_map().get("hallmark_panel_map", {})


def get_panels_for_hallmark(hallmark: str, tier: Optional[str] = None) -> List[str]:
    """
    Return panel_ids recommended for a given hallmark.
    If tier is specified (tier_1/tier_2/tier_3), return only that tier's panels.
    """
    hmap = get_hallmark_map()
    entry = hmap.get(hallmark, {})
    if tier:
        return entry.get(f"{tier}_panels", [])
    # Return all tiers combined
    result = []
    for t in ["tier_1", "tier_2", "tier_3"]:
        result.extend(entry.get(f"{t}_panels", []))
    return result


def get_escalation_rules() -> List[Dict]:
    """Return all escalation rules."""
    return _load_escalation_rules()


def get_escalation_rules_for_marker(marker_key: str) -> List[Dict]:
    """Return escalation rules triggered by a specific marker."""
    return [r for r in get_escalation_rules() if r.get("trigger_marker") == marker_key]


def get_registry_metadata() -> Dict:
    """Return registry metadata (version, counts, domains)."""
    return _load_registry()["metadata"]


def get_panels_metadata() -> Dict:
    """Return panels metadata."""
    return _load_panels()["metadata"]


def evaluate_marker_status(
    marker_key: str,
    value: float,
    sex: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Evaluate a single marker value against clinical and longevity-optimal ranges.

    Returns:
        {
            "marker_key": str,
            "value": float,
            "unit": str,
            "clinical_status": "normal" | "low" | "high" | "unknown",
            "longevity_status": "optimal" | "suboptimal_low" | "suboptimal_high" | "unknown",
            "clinical_low": float | None,
            "clinical_high": float | None,
            "longevity_optimal_low": float | None,
            "longevity_optimal_high": float | None,
        }
    """
    marker = get_marker(marker_key)
    if not marker:
        return {
            "marker_key": marker_key,
            "value": value,
            "unit": None,
            "clinical_status": "unknown",
            "longevity_status": "unknown",
            "clinical_low": None,
            "clinical_high": None,
            "longevity_optimal_low": None,
            "longevity_optimal_high": None,
        }

    # Resolve sex-specific ranges
    sex_norm = (sex or "").lower()
    if marker.get("sex_specific") and sex_norm in ("male", "female"):
        prefix = "male" if sex_norm == "male" else "female"
        clin_low = marker.get(f"{prefix}_clinical_low") or marker.get("clinical_low")
        clin_high = marker.get(f"{prefix}_clinical_high") or marker.get("clinical_high")
        opt_low = marker.get(f"{prefix}_longevity_optimal_low") or marker.get("longevity_optimal_low")
        opt_high = marker.get(f"{prefix}_longevity_optimal_high") or marker.get("longevity_optimal_high")
    else:
        clin_low = marker.get("clinical_low")
        clin_high = marker.get("clinical_high")
        opt_low = marker.get("longevity_optimal_low")
        opt_high = marker.get("longevity_optimal_high")

    # Clinical status
    if clin_low is None and clin_high is None:
        clinical_status = "unknown"
    elif clin_low is not None and value < clin_low:
        clinical_status = "low"
    elif clin_high is not None and value > clin_high:
        clinical_status = "high"
    else:
        clinical_status = "normal"

    # Longevity-optimal status
    if opt_low is None and opt_high is None:
        longevity_status = "unknown"
    elif opt_low is not None and value < opt_low:
        longevity_status = "suboptimal_low"
    elif opt_high is not None and value > opt_high:
        longevity_status = "suboptimal_high"
    else:
        longevity_status = "optimal"

    return {
        "marker_key": marker_key,
        "value": value,
        "unit": marker.get("unit"),
        "clinical_status": clinical_status,
        "longevity_status": longevity_status,
        "clinical_low": clin_low,
        "clinical_high": clin_high,
        "longevity_optimal_low": opt_low,
        "longevity_optimal_high": opt_high,
    }
