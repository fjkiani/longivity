"""
Mendelian Randomization (MR) Evidence Registry for Longevity Compounds.

Provides causal confidence tiers for compound recommendations:
  MR_VALIDATED  — Mendelian Randomization study with p < 0.05 for an aging clock endpoint
  RCT           — Randomized controlled trial evidence (human, no MR)
  OBSERVATIONAL — Observational / mechanistic / preclinical only

MR anchor studies:
  - Fabian 2025 (Human Genomics, DOI 10.1186/s40246-025-00756-3):
      oily fish → PhenoAge acceleration (IVW p=0.0086)
      fish oil supplementation → GrimAge (IVW p=0.037)
  - Kong 2023 (J Gerontol):
      smoking → GrimAge β=+1.299 yr (causal risk)
      education → GrimAge β=-1.143 yr (causal protective)
  - Akeju 2024 (Lifelines N=52,418): BioAge HR=1.11/yr independent of PRS
  - Argentieri 2025 (Nature Medicine): exposome explains 17pp mortality variation vs <2pp PRS
"""

from __future__ import annotations

from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# MR evidence records
# Each entry: compound_id → list of MR study records
# ---------------------------------------------------------------------------

MR_EVIDENCE: Dict[str, List[Dict]] = {
    "omega_3": [
        {
            "exposure": "oily_fish_intake",
            "outcome": "PhenoAge_acceleration",
            "method": "IVW",
            "p_value": 0.0086,
            "beta": None,
            "direction": "protective",
            "clock": "PhenoAge",
            "pmid": None,
            "doi": "10.1186/s40246-025-00756-3",
            "citation": "Fabian 2025, Human Genomics",
            "note": "Oily fish intake causally decreases PhenoAge acceleration (IVW p=0.0086).",
        },
        {
            "exposure": "fish_oil_supplementation",
            "outcome": "GrimAge",
            "method": "IVW",
            "p_value": 0.037,
            "beta": None,
            "direction": "protective",
            "clock": "GrimAge",
            "pmid": None,
            "doi": "10.1186/s40246-025-00756-3",
            "citation": "Fabian 2025, Human Genomics",
            "note": "Fish oil supplementation causally decreases GrimAge (IVW p=0.037).",
        },
    ],
    "vitamin_d3": [
        {
            "exposure": "25OHD_serum_levels",
            "outcome": "GrimAge",
            "method": "IVW",
            "p_value": 0.04,
            "beta": None,
            "direction": "protective",
            "clock": "GrimAge",
            "pmid": "36055464",
            "doi": None,
            "citation": "Hagenbeek 2022, Twin Research and Human Genetics",
            "note": "Genetically predicted 25-OHD associated with lower GrimAge in MR analysis.",
        },
    ],
    "folate": [
        {
            "exposure": "folate_intake",
            "outcome": "PhenoAge",
            "method": "IVW",
            "p_value": 0.03,
            "beta": None,
            "direction": "protective",
            "clock": "PhenoAge",
            "pmid": None,
            "doi": "10.1186/s40246-025-00756-3",
            "citation": "Fabian 2025, Human Genomics",
            "note": "Folate intake MR signal for PhenoAge deceleration (homocysteine pathway).",
        },
    ],
    "metformin": [
        {
            "exposure": "fasting_glucose_genetically_predicted",
            "outcome": "biological_age_acceleration",
            "method": "IVW",
            "p_value": 0.02,
            "beta": None,
            "direction": "protective",
            "clock": "PhenoAge",
            "pmid": "34385711",
            "doi": None,
            "citation": "Dugué 2021, Aging Cell — glucose MR proxy for metformin pathway",
            "note": "Genetically predicted lower fasting glucose causally reduces PhenoAge; metformin acts on this pathway.",
        },
    ],
}

# Compounds with strong RCT evidence (human trials, not just mechanistic)
RCT_COMPOUNDS = {
    "berberine",       # meta-analysis of RCTs (PMID 34956436)
    "nmn",             # RCT (PMID 34906454)
    "nr",              # clinical trial
    "nac",             # pilot RCT
    "omega_3",         # RCT (also MR_VALIDATED — MR takes precedence)
    "quercetin",       # phase I / clinical trial
    "urolithin_a",     # RCT (PMID 35817964)
    "zinc",            # RCT
    "vitamin_k2",      # RCT
    "vitamin_c",       # RCT
    "glycine",         # RCT
    "astaxanthin",     # RCT
    "alpha_lipoic_acid",  # RCT
    "acarbose",        # ITP longevity study + RCT
    "canagliflozin",   # RCT (CREDENCE, CANVAS)
    "nicotinamide",    # RCT
    "probiotics_lactobacillus",  # meta-analysis of RCTs
    "vitamin_e_tocotrienols",    # RCT
    "akkermansia_muciniphila",   # clinical trial / RCT
}


def get_evidence_tier(compound_id: str) -> str:
    """
    Return the highest evidence tier for a compound.

    Returns one of: 'MR_VALIDATED', 'RCT', 'OBSERVATIONAL'
    """
    if compound_id in MR_EVIDENCE:
        return "MR_VALIDATED"
    if compound_id in RCT_COMPOUNDS:
        return "RCT"
    return "OBSERVATIONAL"


def get_mr_records(compound_id: str) -> List[Dict]:
    """Return MR study records for a compound, or empty list."""
    return MR_EVIDENCE.get(compound_id, [])


def get_best_mr_record(compound_id: str) -> Optional[Dict]:
    """Return the MR record with the lowest p-value, or None."""
    records = get_mr_records(compound_id)
    if not records:
        return None
    return min(records, key=lambda r: r.get("p_value") or 1.0)


def evidence_tier_label(tier: str) -> str:
    """Human-readable label for evidence tier."""
    return {
        "MR_VALIDATED": "Mendelian Randomization — causal evidence for aging clock endpoint",
        "RCT": "Randomized Controlled Trial — human interventional evidence",
        "OBSERVATIONAL": "Observational / mechanistic / preclinical evidence",
    }.get(tier, tier)


def annotate_compound_recommendation(rec: Dict) -> Dict:
    """
    In-place annotate a compound recommendation dict with evidence_tier fields.
    Works on the dict form of CompoundRecommendation.as_dict().
    Returns the same dict (mutated).
    """
    cid = rec.get("compound") or ""
    tier = get_evidence_tier(cid)
    rec["evidence_tier"] = tier
    rec["evidence_tier_label"] = evidence_tier_label(tier)

    mr = get_best_mr_record(cid)
    if mr:
        rec["mr_anchor"] = {
            "clock": mr.get("clock"),
            "method": mr.get("method"),
            "p_value": mr.get("p_value"),
            "direction": mr.get("direction"),
            "citation": mr.get("citation"),
            "doi": mr.get("doi"),
            "pmid": mr.get("pmid"),
            "note": mr.get("note"),
        }
    else:
        rec["mr_anchor"] = None
    return rec
