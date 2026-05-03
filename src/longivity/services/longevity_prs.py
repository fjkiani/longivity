"""
Parental-lifespan PRS (27 SNP) — Timmers et al. 2019 eLife 39856 supplementary weights.

APOE coding variants (rs429358, rs7412) are excluded here; they remain in genetic_annotator.
PRS = sum_i (beta_years_i × effect_allele_dosage_i). Tertiles are defined on the partial-sum
range [min_possible, max_possible] over loci with observed genotypes only (≥ min_loci_for_tertile).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_PANEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "resources"
    / "longevity"
    / "longevity_prs_variants.json"
)

# Never fold APOE into this PRS (annotator owns diplotype).
_APOE_RSIDS = frozenset({"rs429358", "rs7412"})

_PANEL_CACHE: Optional[Dict[str, Any]] = None


def _load_panel() -> Dict[str, Any]:
    global _PANEL_CACHE
    if _PANEL_CACHE is not None:
        return _PANEL_CACHE
    raw = _PANEL_PATH.read_text(encoding="utf-8")
    _PANEL_CACHE = json.loads(raw)
    return _PANEL_CACHE


def effect_allele_dosage(genotype: Optional[str], effect_allele: str) -> Optional[int]:
    """
    Diploid dosage of effect_allele from a two-base genotype string (e.g. 'AT', 'CC').
    Unsorted order is fine; IUPAC or length != 2 → None.
    """
    if not genotype or not effect_allele:
        return None
    g = str(genotype).strip().upper().replace("/", "")
    if len(g) != 2:
        return None
    ea = effect_allele.strip().upper()
    if len(ea) != 1 or ea not in "ACGT":
        return None
    if any(b not in "ACGT" for b in g):
        return None
    return sum(1 for b in g if b == ea)


def _contrib_bounds(beta: float) -> Tuple[float, float]:
    """Min and max contribution (beta × dosage) for dosage in {0,1,2}."""
    z, t, tt = 0.0, beta * 1.0, beta * 2.0
    return min(z, t, tt), max(z, t, tt)


def score_parental_lifespan_prs(variants: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Score the 27-SNP parental lifespan PRS from the same `variants` dict used by genetic_annotator.

    Each variant entry: {"genotype": "CT", ...} keyed by rsID.
    """
    panel = _load_panel()
    rows: List[Dict[str, Any]] = list(panel.get("variants") or [])
    min_loci = int(panel.get("min_loci_for_tertile") or 10)

    if not isinstance(variants, dict) or not variants:
        return {
            "status": "NO_INPUT",
            "prs_raw": None,
            "tertile": None,
            "per_locus": [],
            "loci_scored": 0,
            "loci_missing_genotype": 0,
            "honest_caveat": _honest_caveat_text(),
            "provenance": _provenance(panel),
        }

    per_locus: List[Dict[str, Any]] = []
    prs_sum = 0.0
    min_possible = 0.0
    max_possible = 0.0
    scored = 0
    missing = 0

    for row in rows:
        rsid = row["rsid"]
        if rsid in _APOE_RSIDS:
            continue
        beta = float(row["beta_years_per_allele"])
        ea = row["effect_allele"]
        mn, mx = _contrib_bounds(beta)
        entry = variants.get(rsid)
        geno = None
        if isinstance(entry, dict):
            geno = entry.get("genotype")
        dosage = effect_allele_dosage(geno, ea) if geno else None

        if dosage is None:
            missing += 1
            per_locus.append(
                {
                    "rsid": rsid,
                    "chromosome": row.get("chromosome"),
                    "position_grch37": row.get("position_grch37"),
                    "effect_allele": ea,
                    "beta_years_per_allele": beta,
                    "dosage": None,
                    "contribution_years": None,
                }
            )
            continue

        contrib = beta * float(dosage)
        prs_sum += contrib
        min_possible += mn
        max_possible += mx
        scored += 1
        per_locus.append(
            {
                "rsid": rsid,
                "chromosome": row.get("chromosome"),
                "position_grch37": row.get("position_grch37"),
                "effect_allele": ea,
                "beta_years_per_allele": beta,
                "dosage": dosage,
                "contribution_years": round(contrib, 6),
            }
        )

    tertile: Optional[str] = None
    tertile_fraction: Optional[float] = None
    if scored < min_loci:
        status = "INSUFFICIENT_COVERAGE"
    else:
        status = "SUCCESS"
        span = max_possible - min_possible
        if span <= 1e-9:
            tertile = "AVERAGE"
            tertile_fraction = 0.5
        else:
            tertile_fraction = (prs_sum - min_possible) / span
            if tertile_fraction < 1.0 / 3.0:
                tertile = "UNFAVORABLE"
            elif tertile_fraction < 2.0 / 3.0:
                tertile = "AVERAGE"
            else:
                tertile = "FAVORABLE"

    return {
        "status": status,
        "prs_raw": round(prs_sum, 6) if scored else None,
        "prs_min_partial": round(min_possible, 6) if scored else None,
        "prs_max_partial": round(max_possible, 6) if scored else None,
        "tertile": tertile,
        "tertile_fraction": round(tertile_fraction, 6) if tertile_fraction is not None else None,
        "per_locus": per_locus,
        "loci_scored": scored,
        "loci_missing_genotype": missing,
        "panel_size": len(rows),
        "min_loci_for_tertile": min_loci,
        "honest_caveat": _honest_caveat_text(),
        "provenance": _provenance(panel),
    }


def honest_caveat_longevity_prs() -> str:
    """Public text for disclaimers / error payloads (same string used in all PRS responses)."""
    return (
        "Polygenic scores for complex traits and parental lifespan typically explain only a small "
        "fraction of phenotypic variance (often on the order of R² ≈ 0.02–0.08 depending on endpoint, "
        "cohort, and PRS construction). This score is for research context and must not be interpreted as "
        "deterministic individual risk."
    )


def _honest_caveat_text() -> str:
    return honest_caveat_longevity_prs()


def _provenance(panel: Dict[str, Any]) -> Dict[str, Any]:
    lit = panel.get("literature_context") or {}
    return {
        "weights_source": lit.get("timmers_parental_lifespan_gwas"),
        "panel_definition": panel.get("description"),
        "panel_version": panel.get("version"),
    }


def _ba_accelerated(age_acceleration: Optional[float], threshold: float = 2.0) -> Optional[bool]:
    if age_acceleration is None:
        return None
    try:
        aa = float(age_acceleration)
    except (TypeError, ValueError):
        return None
    return aa >= threshold


def synthesize_prs_and_phenoage(
    prs_block: Dict[str, Any],
    age_acceleration: Optional[float],
    ba_threshold: float = 2.0,
) -> Optional[Dict[str, Any]]:
    """
    Combine PRS tertile with PhenoAge biological-age acceleration (years).
    """
    caveat = prs_block.get("honest_caveat") or _honest_caveat_text()
    base = {"honest_caveat": caveat}

    if prs_block.get("status") != "SUCCESS" or not prs_block.get("tertile"):
        return {
            **base,
            "narrative_key": None,
            "narrative": None,
            "reason": "PRS tertile unavailable (insufficient genotyped loci or no variants).",
        }

    tert = prs_block["tertile"]
    ba_acc = _ba_accelerated(age_acceleration, ba_threshold)

    if ba_acc is None:
        return {
            **base,
            "narrative_key": None,
            "narrative": None,
            "reason": "PhenoAge age acceleration unavailable; cannot combine with PRS tertile.",
            "prs_tertile": tert,
        }

    if tert == "FAVORABLE" and ba_acc:
        key = "favorable_accelerated"
        text = (
            "Genetics protective (favorable parental-lifespan PRS tertile), biomarkers need work "
            "(accelerated biological age vs PhenoAge) — prioritize modifiable drivers and repeat labs."
        )
    elif tert == "UNFAVORABLE" and ba_acc:
        key = "unfavorable_accelerated"
        text = (
            "Both signals converge: unfavorable parental-lifespan PRS tertile and accelerated biological age — "
            "favor aggressive, evidence-based prevention and closer follow-up."
        )
    elif tert == "FAVORABLE" and not ba_acc:
        key = "favorable_normal"
        text = "Favorable PRS tertile and biological age not markedly accelerated — maintain trajectory."
    elif tert == "UNFAVORABLE" and not ba_acc:
        key = "unfavorable_normal"
        text = (
            "Unfavorable PRS tertile but biological age not markedly accelerated — protocol appears to be "
            "working against genetic headwinds; sustain protective behaviors."
        )
    else:  # AVERAGE tertile
        key = "average_mixed"
        text = (
            "PRS tertile is intermediate; integrate with PhenoAge trajectory and repeat labs over time "
            "rather than over-interpreting a single snapshot."
        )

    return {
        **base,
        "narrative_key": key,
        "narrative": text,
        "prs_tertile": tert,
        "phenoage_accelerated": ba_acc,
        "phenoage_acceleration_years": age_acceleration,
        "phenoage_acceleration_threshold_years": ba_threshold,
    }

