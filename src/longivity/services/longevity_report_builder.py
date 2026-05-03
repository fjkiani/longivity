"""
Unified longevity full assessment — orchestrates Level 0 PhenoAge/hallmarks,
optional genetic annotation (DNA-Repair.ipynb Module 1), optional DNA repair
scoring (Module 2), merged compound queries and deduped recommendations.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

from .dna_repair_scorer import score_dna_repair
from .genetic_annotator import annotate_genetics
from .longevity_phenoage_level0 import _extract_age, run_longevity_assessment_level0
from .longevity_prs import (
    honest_caveat_longevity_prs,
    score_parental_lifespan_prs,
    synthesize_prs_and_phenoage,
)


def has_usable_longevity_input(body: Dict[str, Any]) -> bool:
    """True if at least one meaningful input slice is present (else 422)."""
    if _extract_age(body) is not None:
        return True
    bio = body.get("biomarkers")
    if isinstance(bio, dict) and any(v is not None and str(v).strip() != "" for v in bio.values()):
        return True
    v = body.get("variants")
    if isinstance(v, dict) and len(v) > 0:
        return True
    pg = body.get("patient_genotype")
    if isinstance(pg, dict) and len(pg) > 0:
        return True
    cq = body.get("compound_queries") or []
    if isinstance(cq, list) and any(str(x).strip() for x in cq):
        return True
    meds = body.get("patient_medications") or body.get("medications") or []
    if isinstance(meds, list) and any(str(x).strip() for x in meds):
        return True
    return False


def _normalize_display_for_map(s: str) -> str:
    t = (s or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t


def _dna_display_to_compound_id(display: str) -> Optional[str]:
    """Map DNA repair COMPOUND_TARGETS display string → longevity_compound_hallmark_map compound_id."""
    n = _normalize_display_for_map(display)
    direct = {
        "vitamin d3": "vitamin_d3",
        "omega-3": "omega_3",
        "omega 3": "omega_3",
        "folate (5-mthf)": "folate",
        "folate": "folate",
        "nac": "nac",
        "magnesium": "magnesium",
        "zinc": None,
    }
    if n in direct:
        return direct[n]
    if n.startswith("folate"):
        return "folate"
    if "omega" in n:
        return "omega_3"
    if "vitamin d" in n:
        return "vitamin_d3"
    return None


def _compound_ids_from_dna_targets(display_names: List[str]) -> List[str]:
    out: List[str] = []
    seen: Set[str] = set()
    for d in display_names:
        cid = _dna_display_to_compound_id(d)
        if cid and cid not in seen:
            seen.add(cid)
            out.append(cid)
    return out


def _merge_compound_queries(user: List[str], dna_ids: List[str]) -> List[str]:
    seen: Set[str] = set()
    merged: List[str] = []
    for x in list(user or []) + list(dna_ids or []):
        q = (str(x) or "").strip()
        if not q:
            continue
        key = q.lower().replace(" ", "_")
        if key in seen:
            continue
        seen.add(key)
        merged.append(q)
    return merged


def _dedupe_compound_recommendations(recs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """One row per compound id; keep max overall_relevance; merge hallmark_matches."""
    by_key: Dict[str, Dict[str, Any]] = {}
    for r in recs:
        k = (r.get("compound") or "").strip().lower()
        if not k:
            continue
        prev = by_key.get(k)
        rel = float(r.get("overall_relevance") or 0.0)
        if prev is None:
            by_key[k] = dict(r)
            continue
        prev_rel = float(prev.get("overall_relevance") or 0.0)
        if rel > prev_rel:
            base = dict(r)
        else:
            base = dict(prev)
        hm_a = list(prev.get("hallmark_matches") or [])
        hm_b = list(r.get("hallmark_matches") or [])
        sigs = {repr(m) for m in hm_a}
        merged_hm = hm_a[:]
        for m in hm_b:
            if repr(m) not in sigs:
                sigs.add(repr(m))
                merged_hm.append(m)
        base["hallmark_matches"] = merged_hm
        base["overall_relevance"] = max(prev_rel, rel)
        by_key[k] = base
    return sorted(by_key.values(), key=lambda x: -float(x.get("overall_relevance") or 0.0))


def _merge_hallmark_narrative(level0_narr: Dict[str, Any], dna_capacity: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    out = dict(level0_narr or {})
    if not dna_capacity:
        return out
    inner = dna_capacity.get("dna_repair_capacity") or dna_capacity
    if not isinstance(inner, dict):
        return out
    overall = inner.get("overall")
    band = inner.get("overall_band")
    if overall is None and band in (None, "UNTESTED"):
        return out
    dna_note = {
        "dna_repair_overall": overall,
        "dna_repair_overall_band": band,
        "priority_findings": inner.get("priority_findings") or [],
        "compound_targets_display": inner.get("compound_targets") or [],
        "source": "dna_repair_scorer (panel JSON; DNA-Repair.ipynb Module 2 alignment)",
    }
    gi = out.get("genomic_instability")
    if isinstance(gi, dict):
        gi2 = dict(gi)
        gi2["dna_repair_layer"] = dna_note
        out["genomic_instability"] = gi2
    else:
        out["genomic_instability"] = {
            "status": "DNA_REPAIR_SUPPLEMENT",
            "phenoage_signal": 0.0,
            "supplementary_signal": 0.0,
            "supplementary_signal_note": "DNA repair pathway score is orthogonal to PhenoAge linear terms.",
            "driving_biomarkers_phenoage": [],
            "driving_biomarkers_supplementary": [],
            "dna_repair_layer": dna_note,
            "explanation": "Genomic instability context from DNA repair gene panel when genotype provided.",
        }
    return out


def _build_action_items(l0: Dict[str, Any], genetic: Optional[Dict[str, Any]], dna: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    pa = l0.get("phenoage_analysis") or {}
    for row in (pa.get("top_accelerators") or [])[:4]:
        lab = row.get("label") or row.get("biomarker") or "marker"
        accel = row.get("acceleration_status") or ""
        items.append(
            {
                "category": "phenoage",
                "summary": f"Review {lab} ({accel})" if accel else f"Review {lab}",
                "detail": row.get("source") or row.get("acceleration_method"),
            }
        )
    if genetic and genetic.get("apoe_status"):
        ap = genetic["apoe_status"]
        if isinstance(ap, dict) and ap.get("risk_tier") in ("ELEVATED", "HIGH_RISK"):
            items.append(
                {
                    "category": "genetics",
                    "summary": f"APOE context: {ap.get('risk_tier', '')}",
                    "detail": ap.get("longevity_impact"),
                }
            )
    dcap = (dna or {}).get("dna_repair_capacity") or {}
    pri = dcap.get("priority_findings") or []
    for p in pri[:3]:
        if isinstance(p, dict):
            items.append(
                {
                    "category": "dna_repair",
                    "summary": f"DNA repair: {p.get('gene', 'gene')} ({p.get('band', '')})",
                    "detail": p.get("variant"),
                }
            )
    if not items and l0.get("data_completeness", {}).get("recommendation"):
        items.append(
            {
                "category": "data",
                "summary": "Improve panel completeness",
                "detail": l0["data_completeness"]["recommendation"],
            }
        )
    return items[:12]


def build_longevity_full_assessment(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build unified response. Expects caller to validate has_usable_longevity_input(body).
    """
    genetic_block: Optional[Dict[str, Any]] = None
    dna_block: Optional[Dict[str, Any]] = None
    prs_block: Optional[Dict[str, Any]] = None

    patient_genotype = body.get("patient_genotype")
    if "patient_genotype" in body:
        pg = patient_genotype if isinstance(patient_genotype, dict) else {}
        try:
            dna_block = score_dna_repair(pg)
        except Exception as e:
            dna_block = {"status": "ERROR", "error": str(e)}

    variants = body.get("variants")
    if isinstance(variants, dict) and variants:
        try:
            genetic_block = annotate_genetics(
                {
                    "patient_id": body.get("patient_id"),
                    "variants": variants,
                }
            )
        except Exception as e:
            genetic_block = {"status": "ERROR", "error": str(e)}
    try:
        if isinstance(variants, dict):
            prs_block = score_parental_lifespan_prs(variants if variants else None)
        else:
            prs_block = score_parental_lifespan_prs(None)
    except Exception as e:
        logger.exception("longevity_prs failed")
        prs_block = {
            "status": "ERROR",
            "error": str(e),
            "honest_caveat": honest_caveat_longevity_prs(),
        }

    dna_ids: List[str] = []
    if dna_block and isinstance(dna_block.get("dna_repair_capacity"), dict):
        targets = dna_block["dna_repair_capacity"].get("compound_targets") or []
        dna_ids = _compound_ids_from_dna_targets(list(targets))

    user_cq = body.get("compound_queries") or []
    if not isinstance(user_cq, list):
        user_cq = []
    merged_cq = _merge_compound_queries(user_cq, dna_ids)

    level0_body = dict(body)
    level0_body["compound_queries"] = merged_cq
    l0 = run_longevity_assessment_level0(level0_body)

    compounds = _dedupe_compound_recommendations(list(l0.get("compound_recommendations") or []))
    dna_for_merge = None
    if isinstance(dna_block, dict) and dna_block.get("status") != "ERROR":
        if "dna_repair_capacity" in dna_block:
            dna_for_merge = dna_block
    hallmark_summary = _merge_hallmark_narrative(l0.get("hallmark_narrative") or {}, dna_for_merge)

    pa = l0.get("phenoage_analysis") or {}
    biological_age = {
        "phenoage_estimate": pa.get("phenoage_estimate"),
        "mortality_score_10yr": pa.get("mortality_score_10yr"),
        "age_acceleration": pa.get("age_acceleration"),
        "age_years": pa.get("age_years"),
        "completeness_mode": pa.get("completeness_mode"),
        "top_accelerators": pa.get("top_accelerators"),
    }

    prs_phenoage_synthesis: Optional[Dict[str, Any]] = None
    if prs_block is not None:
        try:
            prs_phenoage_synthesis = synthesize_prs_and_phenoage(
                prs_block,
                biological_age.get("age_acceleration"),
            )
        except Exception as e:
            logger.exception("prs_phenoage_synthesis failed")
            prs_phenoage_synthesis = {
                "honest_caveat": (prs_block or {}).get("honest_caveat", ""),
                "narrative_key": None,
                "narrative": None,
                "reason": str(e),
            }

    dc = dict(l0.get("data_completeness") or {})
    dc["genetics_provided"] = bool(variants)
    dc["dna_repair_genotype_provided"] = "patient_genotype" in body and isinstance(body.get("patient_genotype"), dict)
    dc["compound_queries_merged_from_dna_repair"] = len(dna_ids)

    prov = dict(l0.get("provenance") or {})
    prov["modules"] = [
        "longevity_phenoage_level0",
        "genetic_annotator (optional)",
        "dna_repair_scorer (optional)",
        "longevity_prs (optional)",
    ]
    if genetic_block and genetic_block.get("provenance"):
        prov["genetics"] = genetic_block["provenance"]
    if dna_block and isinstance(dna_block.get("provenance"), dict):
        prov["dna_repair"] = dna_block["provenance"]
    if prs_block and isinstance(prs_block.get("provenance"), dict):
        prov["longevity_prs"] = prs_block["provenance"]

    disclaimers = [l0.get("disclaimer") or ""]
    if genetic_block and genetic_block.get("disclaimer"):
        disclaimers.append(str(genetic_block["disclaimer"]))
    if dna_block and isinstance(dna_block, dict) and dna_block.get("disclaimer"):
        disclaimers.append(str(dna_block["disclaimer"]))
    if prs_block and prs_block.get("honest_caveat"):
        disclaimers.append(str(prs_block["honest_caveat"]))
    disclaimer_out = " ".join(d for d in disclaimers if d).strip()

    action_items = _build_action_items(l0, genetic_block, dna_block)

    level_assessed = 0
    if genetic_block is not None and isinstance(genetic_block, dict) and genetic_block.get("status") != "ERROR":
        level_assessed = 1
    elif dna_block is not None and isinstance(dna_block, dict) and dna_block.get("status") != "ERROR":
        level_assessed = 1

    return {
        "status": "SUCCESS",
        "level_assessed": level_assessed,
        "biological_age": biological_age,
        "genetic_profile": genetic_block,
        "longevity_prs": prs_block,
        "prs_phenoage_synthesis": prs_phenoage_synthesis,
        "dna_repair_capacity": dna_block,
        "hallmark_summary": hallmark_summary,
        "compound_recommendations": compounds,
        "action_items": action_items,
        "data_completeness": dc,
        "provenance": prov,
        "disclaimer": disclaimer_out,
        "level0": l0,
        "dna_repair_compound_queries_added": dna_ids,
    }


def run_longevity_full_assessment(body: Dict[str, Any]) -> Dict[str, Any]:
    """Public entry: validates input; returns error dict or full assessment."""
    if not has_usable_longevity_input(body):
        return {
            "status": "ERROR",
            "error": "No usable input: provide age, biomarkers, variants, patient_genotype, compound_queries, and/or medications.",
        }
    return build_longevity_full_assessment(body)

