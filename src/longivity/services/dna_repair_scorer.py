"""
DNA repair capacity scorer — behavior aligned with longevity/DNA-Repair.ipynb Module 2.
Panel: resources/longevity/dna_repair_gene_panel.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_PANEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "resources"
    / "longevity"
    / "dna_repair_gene_panel.json"
)
_WEIGHT_EPS = 1e-5

# Loaded lazily; verified once.
_DNA_REPAIR_PANEL_CACHE: Optional[Dict[str, Any]] = None


def _load_dna_repair_panel() -> Dict[str, Any]:
    global _DNA_REPAIR_PANEL_CACHE
    if _DNA_REPAIR_PANEL_CACHE is not None:
        return _DNA_REPAIR_PANEL_CACHE
    raw = _PANEL_PATH.read_text(encoding="utf-8")
    panel = json.loads(raw)
    _verify_panel_integrity(panel)
    _DNA_REPAIR_PANEL_CACHE = panel
    logger.debug("dna_repair_scorer: loaded panel version=%s", panel.get("version"))
    return _DNA_REPAIR_PANEL_CACHE


def _verify_panel_integrity(panel: Dict[str, Any]) -> None:
    pathways = panel.get("pathways") or {}
    pw_sum = sum(float(p["weight"]) for p in pathways.values())
    if abs(pw_sum - 1.0) > _WEIGHT_EPS:
        raise ValueError(f"DNA repair panel pathway weights sum to {pw_sum}, expected 1.0")
    for name, pdata in pathways.items():
        genes = pdata.get("genes") or {}
        gw = sum(float(g["weight"]) for g in genes.values())
        if abs(gw - 1.0) > _WEIGHT_EPS:
            raise ValueError(
                f"DNA repair panel pathway {name!r} gene weights sum to {gw}, expected 1.0"
            )


def get_dna_repair_panel() -> Dict[str, Any]:
    """Return the verified panel (for tests / inspection)."""
    return _load_dna_repair_panel()


# R01–R07 rules (see notebook)
DEFAULT_ACTIVITY = 0.75
COMPOUND_FLOOR = 0.30

SEVERITY_BANDS = [
    (0.95, 1.001, "INTACT"),
    (0.80, 0.95, "MILDLY_REDUCED"),
    (0.60, 0.80, "REDUCED"),
    (0.30, 0.60, "IMPAIRED"),
    (0.00, 0.30, "CRITICAL"),
]

COMPOUND_TARGETS = {
    "homologous_recombination": ["Vitamin D3", "Omega-3"],
    "mismatch_repair": ["Folate (5-MTHF)", "Vitamin D3"],
    "base_excision_repair": ["NAC", "Folate (5-MTHF)", "Magnesium", "Zinc"],
    "nucleotide_excision_repair": ["NAC", "Zinc"],
    "nhej": ["Zinc", "Magnesium"],
}
COMPOUND_THRESHOLD = 0.80


def _get_band(score: Optional[float]) -> str:
    if score is None:
        return "UNTESTED"
    for lo, hi, band in SEVERITY_BANDS:
        if lo <= score < hi:
            return band
    return "UNKNOWN"


def _normalize_clinvar_class(clinvar_class: Optional[str]) -> Optional[str]:
    """Lowercase + strip + spaces→underscore so PATHOGENIC / mixed case match panel intent."""
    if clinvar_class is None:
        return None
    if not isinstance(clinvar_class, str):
        return None
    t = clinvar_class.strip().lower().replace(" ", "_")
    if t == "likelypathogenic":
        t = "likely_pathogenic"
    return t or None


def _score_gene(
    clinvar_class: Optional[str],
    zygosity: Optional[str],
    gene_data: Dict[str, Any],
    variant_info: Dict[str, Any],
) -> tuple[float, Optional[str]]:
    cc = _normalize_clinvar_class(clinvar_class)

    if cc is None or cc in (
        "benign",
        "likely_benign",
        "likelybenign",
        "no_variant",
    ):
        return 1.0, None

    if cc in ("pathogenic", "likely_pathogenic"):
        if zygosity in ("homozygous", "compound_het"):
            return 0.00, "biallelic P/LP — ARM BROKEN"
        return 0.50, "het P/LP"

    if cc == "vus":
        return 0.50, "VUS"

    if cc == "functional_polymorphism":
        rsid = variant_info.get("rsid")
        poly_entry = None
        if rsid and rsid in gene_data.get("polymorphisms", {}):
            poly_entry = gene_data["polymorphisms"][rsid]
        else:
            variant_name = variant_info.get("variant", "")
            for _rsid, _poly in gene_data.get("polymorphisms", {}).items():
                if _poly.get("hgvs") == variant_name:
                    poly_entry = _poly
                    break

        if poly_entry is None:
            return DEFAULT_ACTIVITY, f"functional SNP (no panel data, default {DEFAULT_ACTIVITY})"

        if zygosity == "homozygous":
            raw = poly_entry.get("enzyme_activity_score_hom")
            score = float(raw) if raw is not None else DEFAULT_ACTIVITY
        else:
            raw = poly_entry.get("enzyme_activity_score_het")
            score = float(raw) if raw is not None else DEFAULT_ACTIVITY
        return score, f"{poly_entry.get('hgvs', '?')} {zygosity} (activity={score:.2f})"

    return 1.0, None


def _score_gene_compound(scores: List[float]) -> float:
    """R07: multiply variant scores for same gene, floor at COMPOUND_FLOOR."""
    result = 1.0
    for s in scores:
        result *= s
    return max(result, COMPOUND_FLOOR)


def score_dna_repair(
    patient_genotype: Optional[Dict[str, Any]] = None,
    panel: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    patient_genotype: {GENE: {variant, clinvar_class, zygosity, rsid?}}
    Genes absent → score 1.0 (intact) for that gene.
    """
    patient_genotype = patient_genotype or {}
    if panel is None:
        panel = _load_dna_repair_panel()

    pathway_results: Dict[str, Any] = {}
    overall_inputs: List[Dict[str, Any]] = []
    all_priority: List[Dict[str, Any]] = []
    all_compound_targets: set[str] = set()

    for pw_name, pw_data in panel["pathways"].items():
        numerator = 0.0
        denominator = 0.0
        flags: List[str] = []
        variant_count = 0
        pathway_has_biallelic_zero = False

        for gene_name, gene_data in pw_data["genes"].items():
            gene_weight = float(gene_data["weight"])
            patient_var = patient_genotype.get(gene_name)

            if patient_var is None:
                numerator += 1.0 * gene_weight
                denominator += gene_weight
                continue

            clinvar_class = patient_var.get("clinvar_class", "no_variant")
            zygosity = patient_var.get("zygosity")
            variant_name = patient_var.get("variant", "?")

            gene_score, flag_text = _score_gene(clinvar_class, zygosity, gene_data, patient_var)
            variant_count += 1
            if gene_score == 0.0:
                pathway_has_biallelic_zero = True

            numerator += gene_score * gene_weight
            denominator += gene_weight

            if flag_text:
                flags.append(f"{gene_name} {flag_text}")

            if gene_score < 0.60:
                all_priority.append(
                    {
                        "gene": gene_name,
                        "pathway": pw_name,
                        "score": gene_score,
                        "band": _get_band(gene_score),
                        "variant": variant_name,
                    }
                )

        pw_score = round(numerator / denominator, 4) if denominator > 0 else None
        pw_band = _get_band(pw_score)
        if pathway_has_biallelic_zero and pw_band in ("INTACT", "MILDLY_REDUCED"):
            pw_band = "IMPAIRED"
            flags.append("— override: biallelic loss detected")

        if pw_score is not None and pw_score < COMPOUND_THRESHOLD:
            for c in COMPOUND_TARGETS.get(pw_name, []):
                all_compound_targets.add(c)

        pathway_results[pw_name] = {
            "score": pw_score,
            "band": pw_band,
            "flag": "; ".join(flags) if flags else None,
            "genes_with_variants": variant_count,
        }

        overall_inputs.append({"score": pw_score, "weight": float(pw_data["weight"])})

    o_num = sum(p["score"] * p["weight"] for p in overall_inputs if p["score"] is not None)
    o_den = sum(p["weight"] for p in overall_inputs if p["score"] is not None)
    overall = round(o_num / o_den, 4) if o_den > 0 else None
    overall_band = _get_band(overall)

    return {
        "dna_repair_capacity": {
            "overall": overall,
            "overall_band": overall_band,
            "by_pathway": pathway_results,
            "priority_findings": sorted(all_priority, key=lambda x: x["score"]),
            "compound_targets": sorted(all_compound_targets),
            "hallmark": "genomic_instability",
        },
        "provenance": {
            "panel_version": panel.get("version", "unknown"),
            "scoring_rules": "R01-R07 per CrisPRO DNA Repair Scorer v1.0",
            "severity_bands": ">=0.95 INTACT | 0.80-0.94 MILDLY_REDUCED | 0.60-0.79 REDUCED | 0.30-0.59 IMPAIRED | <0.30 CRITICAL",
            "functional_snp_default": f"null activity → {DEFAULT_ACTIVITY}",
            "compound_floor": f"R07 floor = {COMPOUND_FLOOR}",
        },
        "disclaimer": "Research Use Only. Not a diagnostic.",
    }

