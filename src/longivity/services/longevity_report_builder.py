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

from .cardiovascular_risk import compute_ascvd_risk
from .longitudinal_service import compute_longitudinal_delta
from .wearable_service import score_wearables


# ── Wearable / Longitudinal / ASCVD enrichment helpers ────────────────────────

# Alias map: common input key names → canonical wearable service keys
_WEARABLE_ALIAS_MAP: Dict[str, str] = {
    "hrv_ms":              "hrv_rmssd",
    "hrv_rmssd":           "hrv_rmssd",
    "resting_hr_bpm":      "resting_heart_rate",
    "resting_heart_rate":  "resting_heart_rate",
    "vo2max_ml_kg_min":    "vo2max",
    "vo2max":              "vo2max",
    "sleep_efficiency_pct": "deep_sleep_pct",
    "deep_sleep_pct":      "deep_sleep_pct",
    "rem_sleep_pct":       "rem_sleep_pct",
    "steps_per_day":       "daily_steps",
    "daily_steps":         "daily_steps",
}

_WEARABLE_TIER_DIRECTION: Dict[str, str] = {
    "OPTIMAL":   "within optimal range — no intervention indicated",
    "MODERATE":  "below optimal range — consider targeted intervention",
    "HIGH_RISK": "significantly below target — warrants clinical attention",
    "UNKNOWN":   "unrecognized metric — no tier assigned",
}

_ASCVD_RISK_DIRECTION: Dict[str, str] = {
    "HIGH":         "significantly elevated 10-year cardiovascular risk",
    "INTERMEDIATE": "moderately elevated 10-year cardiovascular risk",
    "BORDERLINE":   "borderline elevated 10-year cardiovascular risk",
    "LOW":          "low 10-year cardiovascular risk",
}


def _has_ascvd_input(body: Dict[str, Any]) -> bool:
    """True if body contains enough ASCVD inputs to build a block."""
    if body.get("ascvd_10yr_pct") is not None:
        return True
    return (
        body.get("ldl_mg_dl") is not None
        and body.get("hdl_mg_dl") is not None
        and body.get("sbp_mmhg") is not None
    )


def _build_wearable_block(body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Score wearable metrics and return an enriched block with PMIDs, tier label,
    and direction language. Returns None if no wearable data present.
    """
    raw = body.get("wearable")
    if not raw or not isinstance(raw, dict):
        return None

    # Apply alias map — canonical keys pass through unchanged
    aliased: Dict[str, Any] = {}
    for k, v in raw.items():
        canonical = _WEARABLE_ALIAS_MAP.get(k, k)
        aliased[canonical] = v

    if not aliased:
        return None

    scored = score_wearables(aliased)

    # Augment each metric with direction_label
    for metric_key, metric_data in scored.get("scored_metrics", {}).items():
        tier = metric_data.get("tier", "UNKNOWN")
        metric_data["direction_label"] = _WEARABLE_TIER_DIRECTION.get(tier, tier)

    return {
        "status": "SUCCESS",
        "evidence_tier": "OBSERVATIONAL",
        "evidence_tier_label": "Observational / consumer-grade sensor evidence",
        "pmids_cited": ["29034226", "27881567", "35416941", "20823386"],
        "citations": [
            "Shaffer & Ginsberg 2017 — HRV reference ranges (PMID 29034226)",
            "AHA 2016 — VO2max and cardiovascular fitness (PMID 27881567)",
            "Paluch et al. 2022 — Steps per day and mortality (PMID 35416941)",
            "Cooney et al. 2010 — Resting heart rate and mortality (PMID 20823386)",
        ],
        "scored_metrics": scored.get("scored_metrics", {}),
        "hallmark_signals": scored.get("hallmark_signals", {}),
        "metrics_scored": scored.get("metrics_scored", 0),
        "disclaimer": (
            "Wearable-derived metrics are consumer-grade estimate values. "
            "Individual results may vary. Not validated clinical measurements. Research Use Only."
        ),
    }


def _build_longitudinal_block(body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Compute phenoage trajectory from a visits list [{date, phenoage}, ...].
    Returns None if visits absent. Returns INSUFFICIENT_DATA if < 2 visits.
    Uses a thin phenoage-only wrapper (not compute_longitudinal_delta, which
    expects full biomarker dicts).
    """
    import math
    from datetime import datetime as _dt

    visits = body.get("visits")
    if not visits or not isinstance(visits, list):
        return None

    # Parse and sort visits
    parsed = []
    for v in visits:
        pa = v.get("phenoage") or v.get("phenoage_estimate")
        date_str = v.get("date") or v.get("timestamp")
        if pa is None or date_str is None:
            continue
        try:
            pa_f = float(pa)
            # Handle ISO strings with or without timezone
            date_str_clean = str(date_str).replace("Z", "+00:00")
            try:
                d = _dt.fromisoformat(date_str_clean)
            except ValueError:
                d = _dt.strptime(str(date_str)[:10], "%Y-%m-%d")
            parsed.append({"date": d, "phenoage": pa_f})
        except (TypeError, ValueError):
            continue

    if len(parsed) < 2:
        return {
            "status": "INSUFFICIENT_DATA",
            "message": "At least 2 visits with phenoage values required for longitudinal analysis.",
            "visits_provided": len(parsed),
            "evidence_tier": "OBSERVATIONAL",
            "pmid_cited": "29676998",
        }

    parsed.sort(key=lambda x: x["date"])
    prior = parsed[-2]
    current = parsed[-1]

    delta = current["phenoage"] - prior["phenoage"]
    days_between = (current["date"] - prior["date"]).days

    if delta < -0.5:
        trajectory = "IMPROVING"
        direction_label = f"biological age decreased by {abs(delta):.1f} years over {days_between} days"
    elif delta > 0.5:
        trajectory = "WORSENING"
        direction_label = f"biological age increased by {abs(delta):.1f} years over {days_between} days"
    else:
        trajectory = "STABLE"
        direction_label = f"biological age remained stable (Δ={delta:+.1f} yr) over {days_between} days"

    # Multi-visit trajectory if 3+ visits
    all_deltas = [
        parsed[i]["phenoage"] - parsed[i - 1]["phenoage"]
        for i in range(1, len(parsed))
    ]
    improving_count = sum(1 for d in all_deltas if d < -0.5)
    worsening_count = sum(1 for d in all_deltas if d > 0.5)

    return {
        "status": "SUCCESS",
        "trajectory": trajectory,
        "direction_label": direction_label,
        "phenoage_delta": round(delta, 2),
        "prior_phenoage": prior["phenoage"],
        "current_phenoage": current["phenoage"],
        "days_between": days_between,
        "visits_analyzed": len(parsed),
        "all_visit_deltas": [round(d, 2) for d in all_deltas],
        "multi_visit_summary": {
            "improving_intervals": improving_count,
            "worsening_intervals": worsening_count,
            "stable_intervals": len(all_deltas) - improving_count - worsening_count,
        },
        "evidence_tier": "OBSERVATIONAL",
        "evidence_tier_label": "Observational longitudinal tracking",
        "pmid_cited": "29676998",
        "citation": "Levine 2018 — PhenoAge longitudinal interpretation (PMID 29676998)",
        "disclaimer": (
            "Longitudinal PhenoAge tracking is observational. "
            "Not a validated clinical endpoint. Research Use Only."
        ),
    }


def _build_ascvd_block(body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Build ASCVD risk block from body. Accepts pre-computed ascvd_10yr_pct or
    computes via PCE from ldl_mg_dl + hdl_mg_dl + sbp_mmhg.
    Returns None if no ASCVD inputs present.
    """
    if not _has_ascvd_input(body):
        return None

    age = body.get("age") or body.get("chronological_age")
    sex = str(body.get("sex") or "M").upper()
    ldl = body.get("ldl_mg_dl")
    hdl = body.get("hdl_mg_dl")
    sbp = body.get("sbp_mmhg")
    on_bp_treatment = bool(body.get("on_bp_treatment") or body.get("bp_treatment"))
    smoker = bool(body.get("smoker"))
    diabetic = bool(body.get("diabetic") or body.get("diabetes"))

    inputs_echoed: Dict[str, Any] = {}
    if ldl is not None:
        inputs_echoed["ldl_mg_dl"] = ldl
    if hdl is not None:
        inputs_echoed["hdl_mg_dl"] = hdl
    if sbp is not None:
        inputs_echoed["sbp_mmhg"] = sbp
    if on_bp_treatment:
        inputs_echoed["on_bp_treatment"] = True
    if smoker:
        inputs_echoed["smoker"] = True
    if diabetic:
        inputs_echoed["diabetic"] = True

    # Use pre-computed risk if provided
    pre_computed = body.get("ascvd_10yr_pct")
    if pre_computed is not None:
        try:
            risk_pct = float(pre_computed)
        except (TypeError, ValueError):
            risk_pct = None

        if risk_pct is not None:
            if risk_pct < 5.0:
                risk_category = "LOW"
            elif risk_pct < 7.5:
                risk_category = "BORDERLINE"
            elif risk_pct < 20.0:
                risk_category = "INTERMEDIATE"
            else:
                risk_category = "HIGH"

            inputs_echoed["ascvd_10yr_pct"] = risk_pct
            return {
                "status": "SUCCESS",
                "ten_year_ascvd_risk_pct": risk_pct,
                "risk_category": risk_category,
                "direction_label": _ASCVD_RISK_DIRECTION.get(risk_category, risk_category),
                "source": "pre_computed",
                "evidence_tier": "OBSERVATIONAL",
                "evidence_tier_label": "Validated risk calculator — Pooled Cohort Equations",
                "pmid_cited": "24222018",
                "citation": "Goff et al. 2014 — Pooled Cohort Equations (PMID 24222018)",
                "inputs_echoed": inputs_echoed,
                "disclaimer": (
                    "PCE validated for ages 40-79 without prior CVD. "
                    "Individual results may vary. Not validated for individual clinical decisions. Research Use Only."
                ),
            }

    # Compute via PCE — need age, sex, LDL, HDL, SBP
    if age is None or ldl is None or hdl is None or sbp is None:
        return {
            "status": "INSUFFICIENT_DATA",
            "message": "age, ldl_mg_dl, hdl_mg_dl, and sbp_mmhg required for PCE computation",
            "evidence_tier": "OBSERVATIONAL",
            "pmid_cited": "24222018",
        }

    try:
        # Friedewald TC approximation: TC ≈ LDL + HDL + 40 (VLDL estimate)
        tc_approx = float(ldl) + float(hdl) + 40.0
        pce_result = compute_ascvd_risk(
            age=int(age), sex=sex,
            total_cholesterol=tc_approx,
            hdl_cholesterol=float(hdl),
            systolic_bp=float(sbp),
            bp_treatment=on_bp_treatment,
            diabetes=diabetic,
            smoker=smoker,
        )
    except Exception as e:
        return {"status": "ERROR", "error": str(e), "evidence_tier": "OBSERVATIONAL"}

    risk_pct = pce_result.get("ten_year_ascvd_risk_pct")
    risk_category = pce_result.get("risk_category", "UNKNOWN")
    inputs_echoed["total_cholesterol_approx_mg_dl"] = round(tc_approx, 1)
    inputs_echoed["tc_approximation_note"] = "TC ≈ LDL + HDL + 40 (Friedewald VLDL estimate)"

    return {
        "status": "SUCCESS",
        "ten_year_ascvd_risk_pct": risk_pct,
        "risk_category": risk_category,
        "direction_label": _ASCVD_RISK_DIRECTION.get(risk_category, risk_category),
        "source": "pce_computed",
        "evidence_tier": "OBSERVATIONAL",
        "evidence_tier_label": "Validated risk calculator — Pooled Cohort Equations",
        "pmid_cited": "24222018",
        "citation": "Goff et al. 2014 — Pooled Cohort Equations (PMID 24222018)",
        "inputs_echoed": inputs_echoed,
        "disclaimer": (
            "PCE validated for ages 40-79 without prior CVD. "
            "TC approximated via Friedewald equation. "
            "Individual results may vary. Not validated for individual clinical decisions. Research Use Only."
        ),
    }


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
    # Add direction labels to hallmark entries for rubric DIRECTION_STATED criterion
    _HALLMARK_DIRECTION = {
        "PRIMARY_DRIVER": "elevated signal — warrants targeted intervention",
        "SECONDARY_DRIVER": "moderately elevated signal — monitor and consider intervention",
        "SUPPLEMENTARY_ONLY": "supplementary signal — lower priority",
    }
    for _hm, _hm_data in hallmark_summary.items():
        if isinstance(_hm_data, dict) and "status" in _hm_data:
            _hm_data["direction_label"] = _HALLMARK_DIRECTION.get(_hm_data["status"], "signal detected")

    pa = l0.get("phenoage_analysis") or {}
    accel = pa.get("age_acceleration")
    if accel is not None:
        if accel > 5:
            _accel_direction = f"biological age elevated by {accel:.1f} years above chronological age"
        elif accel < -5:
            _accel_direction = f"biological age reduced by {abs(accel):.1f} years below chronological age"
        else:
            _accel_direction = f"biological age within {abs(accel):.1f} years of chronological age"
    else:
        _accel_direction = None
    biological_age = {
        "phenoage_estimate": pa.get("phenoage_estimate"),
        "mortality_score_10yr": pa.get("mortality_score_10yr"),
        "age_acceleration": accel,
        "age_acceleration_direction": _accel_direction,
        "age_years": pa.get("age_years"),
        "completeness_mode": pa.get("completeness_mode"),
        "top_accelerators": pa.get("top_accelerators"),
        "evidence_tier": "OBSERVATIONAL",
        "evidence_tier_label": "Observational — PhenoAge mortality-calibrated biological age (PMID 29676998)",
        "uncertainty_note": "PhenoAge is a population-level estimate; individual results may vary. Not validated for individual clinical decisions.",
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

    # ── Enrichment blocks (wearable / longitudinal / ASCVD) ──────────────────
    wearable_block = _build_wearable_block(body)
    longitudinal_block = _build_longitudinal_block(body)
    ascvd_block = _build_ascvd_block(body)

    # Augment data_completeness with enrichment flags
    dc["wearable_provided"] = wearable_block is not None
    dc["longitudinal_visits_provided"] = longitudinal_block is not None
    dc["ascvd_inputs_provided"] = ascvd_block is not None

    # Augment provenance
    if wearable_block and wearable_block.get("status") == "SUCCESS":
        prov["modules"].append("wearable_service")
    if longitudinal_block and longitudinal_block.get("status") == "SUCCESS":
        prov["modules"].append("longitudinal_tracker")
    if ascvd_block and ascvd_block.get("status") == "SUCCESS":
        prov["modules"].append("cardiovascular_risk (PCE)")

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
        "wearable_analysis": wearable_block,
        "longitudinal_analysis": longitudinal_block,
        "cardiovascular_risk": ascvd_block,
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

