"""
Epigenetic clock normalization service (RUO).

Accepts pre-computed clock values (from external methylation array analysis)
and normalizes them against published population reference values.

Supported clocks:
  - grimAge (GrimAge, Lu 2019, PMID 31451800)
  - dunedinPACE (Belsky 2022, PMID 35236523)
  - horvath (Horvath 2013, PMID 24138928)
  - hannum (Hannum 2013, PMID 23177740)
  - phenoAgeDNAm (Levine 2018, PMID 29676998)

All outputs are Research Use Only (RUO).
"""
from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, List, Optional

# Path to the clock registry JSON (sibling to this file's package resources)
_RESOURCES_DIR = pathlib.Path(__file__).parent.parent / "resources" / "longevity"
_CLOCKS_JSON = _RESOURCES_DIR / "epigenetic_clocks.json"

# Clocks whose output is in "years" (age-based)
_AGE_BASED_CLOCKS = {"grimAge", "horvath", "hannum", "phenoAgeDNAm"}
# Clocks whose output is a pace ratio
_PACE_CLOCKS = {"dunedinPACE"}

# Interpretation thresholds
_AGE_ACCEL_FAST_THRESHOLD = 2.0   # years above reference → FAST
_AGE_ACCEL_SLOW_THRESHOLD = -2.0  # years below reference → SLOW
_PACE_FAST_THRESHOLD = 1.10       # pace ratio → FAST
_PACE_SLOW_THRESHOLD = 0.90       # pace ratio → SLOW

# Worst-case ordering for overall_pace_interpretation
_PACE_SEVERITY = {"FAST": 2, "NORMAL": 1, "SLOW": 0}


def _load_clock_registry() -> Dict[str, Any]:
    """Load and return the epigenetic clocks registry JSON."""
    with open(_CLOCKS_JSON, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _compute_z_score(value: float, mean: Optional[float], sd: float) -> Optional[float]:
    """Compute z-score if mean and sd are available."""
    if mean is None or sd == 0:
        return None
    return round((value - mean) / sd, 4)


def _interpret_age_based(acceleration: float) -> str:
    """Return pace interpretation for age-based clocks."""
    if acceleration > _AGE_ACCEL_FAST_THRESHOLD:
        return "FAST"
    if acceleration < _AGE_ACCEL_SLOW_THRESHOLD:
        return "SLOW"
    return "NORMAL"


def _interpret_pace_clock(pace_value: float) -> str:
    """Return pace interpretation for DunedinPACE."""
    if pace_value > _PACE_FAST_THRESHOLD:
        return "FAST"
    if pace_value < _PACE_SLOW_THRESHOLD:
        return "SLOW"
    return "NORMAL"


def _worst_case_interpretation(interpretations: List[str]) -> str:
    """Return the worst-case interpretation across all clocks (FAST > NORMAL > SLOW)."""
    if not interpretations:
        return "NORMAL"
    return max(interpretations, key=lambda x: _PACE_SEVERITY.get(x, 1))


def score_epigenetic_clocks(
    clock_values: dict,
    chronological_age: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Normalize pre-computed epigenetic clock values against published population references.

    Parameters
    ----------
    clock_values : dict
        Mapping of clock name → value.
        e.g. {"grimAge": 65.0, "dunedinPACE": 1.12, "horvath": 58.0}
    chronological_age : int or None
        Chronological age in years. Used for clock_acceleration calculation
        in age-based clocks. If None, z-score relative to population mean is used.

    Returns
    -------
    dict
        Normalized results with clock_acceleration, pace_interpretation,
        z_score, hallmark_implications, and overall_pace_interpretation.
    """
    # ── Edge case: empty input ────────────────────────────────────────────────
    if not clock_values:
        return {
            "status": "NO_CLOCK_DATA",
            "clocks_analyzed": [],
            "clock_results": {},
            "overall_pace_interpretation": None,
            "hallmark_implications": [],
            "chronological_age_used": chronological_age,
            "ruo_disclaimer": "Research Use Only. Not for clinical diagnosis or treatment decisions.",
            "warnings": ["No clock values provided."],
        }

    # ── Load registry ─────────────────────────────────────────────────────────
    registry = _load_clock_registry()
    known_clocks: Dict[str, Any] = registry.get("clocks", {})
    ruo_disclaimer = registry.get("ruo_disclaimer", "Research Use Only.")

    clock_results: Dict[str, Any] = {}
    hallmarks_union: List[str] = []
    interpretations: List[str] = []
    warnings: List[str] = []
    clocks_analyzed: List[str] = []

    for clock_name, clock_value in clock_values.items():
        # ── Unknown clock ─────────────────────────────────────────────────────
        if clock_name not in known_clocks:
            warnings.append(
                f"Unknown clock '{clock_name}' — skipped. "
                f"Supported: {list(known_clocks.keys())}"
            )
            continue

        meta = known_clocks[clock_name]
        pop_mean: Optional[float] = meta.get("population_mean")
        pop_sd: float = meta.get("population_sd", 1.0)
        pmid: str = meta.get("pmid", "")
        hallmarks: List[str] = meta.get("hallmarks", [])

        # Accumulate hallmarks
        for h in hallmarks:
            if h not in hallmarks_union:
                hallmarks_union.append(h)

        clocks_analyzed.append(clock_name)

        # ── Age-based clocks ──────────────────────────────────────────────────
        if clock_name in _AGE_BASED_CLOCKS:
            if chronological_age is not None:
                acceleration = round(clock_value - chronological_age, 4)
                interpretation = _interpret_age_based(acceleration)
                # z-score relative to population SD (acceleration / SD)
                z_score = round(acceleration / pop_sd, 4) if pop_sd else None
                clock_result: Dict[str, Any] = {
                    "value": clock_value,
                    "clock_acceleration": acceleration,
                    "pace_interpretation": interpretation,
                    "z_score": z_score,
                    "reference_pmid": pmid,
                }
            else:
                # No chronological age — use z-score relative to population mean
                if pop_mean is not None:
                    z_score = _compute_z_score(clock_value, pop_mean, pop_sd)
                    acceleration = round(clock_value - pop_mean, 4)
                    interpretation = _interpret_age_based(acceleration)
                else:
                    # No population mean available (horvath, hannum, phenoAgeDNAm)
                    z_score = None
                    acceleration = None
                    interpretation = "NORMAL"
                    warnings.append(
                        f"Clock '{clock_name}' has no population_mean; "
                        "provide chronological_age for acceleration calculation."
                    )
                clock_result = {
                    "value": clock_value,
                    "clock_acceleration": acceleration,
                    "pace_interpretation": interpretation,
                    "z_score": z_score,
                    "reference_pmid": pmid,
                }

        # ── Pace-ratio clocks (DunedinPACE) ──────────────────────────────────
        elif clock_name in _PACE_CLOCKS:
            pace_deviation = round(clock_value - 1.0, 4)
            interpretation = _interpret_pace_clock(clock_value)
            z_score = _compute_z_score(clock_value, pop_mean, pop_sd)
            clock_result = {
                "value": clock_value,
                "pace_deviation": pace_deviation,
                "pace_interpretation": interpretation,
                "z_score": z_score,
                "reference_pmid": pmid,
            }

        else:
            # Fallback for any future clock types
            z_score = _compute_z_score(clock_value, pop_mean, pop_sd)
            clock_result = {
                "value": clock_value,
                "pace_interpretation": "NORMAL",
                "z_score": z_score,
                "reference_pmid": pmid,
            }
            interpretation = "NORMAL"

        clock_results[clock_name] = clock_result
        interpretations.append(interpretation)

    overall = _worst_case_interpretation(interpretations) if interpretations else None

    return {
        "status": "ok",
        "clocks_analyzed": clocks_analyzed,
        "clock_results": clock_results,
        "overall_pace_interpretation": overall,
        "hallmark_implications": hallmarks_union,
        "chronological_age_used": chronological_age,
        "ruo_disclaimer": ruo_disclaimer,
        "warnings": warnings,
    }
