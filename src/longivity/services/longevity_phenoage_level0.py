"""
longivity: Longevity Assessment Level 0 — PhenoAge Gompertz (PMID 29676998) + hallmark narrative
from biomarker_hallmark_map.json only (no invented PMID bridges). Supplementary biomarkers are
threshold-scored separately (never blended into PhenoAge mortality math).

Per-component "acceleration" is CrisPRO UX (threshold comparison), not a PhenoAge classification.
"""

from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .longevity_hallmark_scorer import _SHIPPABLE, get_longevity_hallmark_scorer

_RESOURCES = Path(__file__).resolve().parent.parent / "resources" / "longevity"

# Canonical PhenoAge keys -> biomarker_id in biomarker_hallmark_map.json (hallmarks only).
PHENOAGE_KEY_TO_MAP_ID: Dict[str, str] = {
    "albumin": "serum_albumin_g_l",
    "creatinine": "serum_creatinine_umol_l",
    "glucose_serum": "serum_glucose_mmol",
    "crp_log": "hscrp",
    "lymphocyte_percent": "lymphocyte_percent",
    "mcv": "mcv",
    "rdw": "rdw",
    "alkaline_phosphatase": "alkaline_phosphatase",
    "wbc": "wbc",
}

PHENOAGE_BIOMARKER_MAP_IDS = frozenset(PHENOAGE_KEY_TO_MAP_ID.values())

ACCEL_METHOD = "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)"

GLUCOSE_MGDL_TO_MMOLL = 1.0 / 18.018
MG_L_CRP_TO_MG_DL = 0.1
CREAT_MGDL_TO_UMOLL = 88.42
ALBUMIN_GDL_TO_GL = 10.0


def _normalize_biomarker_keys(bio: Dict[str, Any]) -> Dict[str, Any]:
    """Case/spacing-insensitive key map for lab payloads (e.g. RDW_percent, hsCRP_mg_l)."""
    out: Dict[str, Any] = {}
    if not isinstance(bio, dict):
        return out
    for k, v in bio.items():
        nk = str(k).strip().replace("-", "_").replace("/", "_").lower()
        if nk not in out:
            out[nk] = v
    return out


def _load_phenoage_coefficients() -> Dict[str, Any]:
    path = _RESOURCES / "phenoage_gompertz_coefficients_levine2018.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_coeff_by_key(coeff: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for b in coeff["biomarkers"]:
        out[b["canonical_key"]] = b
    return out


def _coerce_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _extract_age(payload: Dict[str, Any]) -> Optional[int]:
    for k in ("age", "chronological_age"):
        a = _coerce_float(payload.get(k))
        if a is not None:
            return int(round(a))
    return None


def extract_phenoage_marker_values(payload: Dict[str, Any]) -> Tuple[Dict[str, float], Dict[str, Any]]:
    """
    Map request biomarkers dict to PhenoAge canonical units.
    Returns (canonical_key -> value) and provenance_notes for conversions.
    """
    bio = payload.get("biomarkers") or payload
    if not isinstance(bio, dict):
        bio = {}
    L = _normalize_biomarker_keys(bio)
    notes: Dict[str, Any] = {}
    out: Dict[str, float] = {}

    aa: Optional[float] = None
    if L.get("albumin_g_l") is not None:
        aa = _coerce_float(L["albumin_g_l"])
    elif L.get("albumin_g_dl") is not None:
        aa = float(L["albumin_g_dl"]) * ALBUMIN_GDL_TO_GL
        notes["albumin"] = "converted albumin_g_dl -> g/L (*10)"
    elif L.get("albumin") is not None:
        raw = _coerce_float(L["albumin"])
        if raw is not None:
            # US-style CMP often reports albumin in g/dL (e.g. 4.5) without a suffix.
            if raw <= 12.0:
                aa = raw * ALBUMIN_GDL_TO_GL
                notes["albumin"] = "bare 'albumin' interpreted as g/dL -> g/L (*10)"
            else:
                aa = raw
                notes["albumin"] = "bare 'albumin' interpreted as g/L"
    if aa is not None:
        out["albumin"] = aa
        if aa < 15 or aa > 70:
            prev = notes.get("albumin")
            msg = "albumin g/L outside expected serum range — verify units"
            notes["albumin"] = f"{prev}; {msg}" if prev else msg

    cr = _coerce_float(L.get("creatinine_umol_l") or L.get("creatinine_umol"))
    if cr is None and L.get("creatinine_mg_dl") is not None:
        cr = float(L["creatinine_mg_dl"]) * CREAT_MGDL_TO_UMOLL
        notes["creatinine"] = "converted creatinine_mg_dl -> µmol/L (*88.42)"
    if cr is None and L.get("creatinine") is not None:
        raw = _coerce_float(L["creatinine"])
        if raw is not None:
            if raw <= 10.0:
                cr = raw * CREAT_MGDL_TO_UMOLL
                notes["creatinine"] = "bare 'creatinine' interpreted as mg/dL -> µmol/L (*88.42)"
            else:
                cr = raw
                notes["creatinine"] = "bare 'creatinine' interpreted as µmol/L"
    if cr is not None:
        if cr < 10 or cr > 2000:
            notes["creatinine"] = ((notes.get("creatinine") or "") + "; " if notes.get("creatinine") else "") + "creatinine µmol/L outside expected range — verify units"
        out["creatinine"] = cr

    a1c_chk = _coerce_float(L.get("hba1c_percent") or L.get("hba1c_pct") or L.get("hba1c"))
    if a1c_chk is not None and (a1c_chk < 3.0 or a1c_chk > 20.0):
        notes["hba1c"] = "HbA1c value outside expected % range — verify units"

    gl = _coerce_float(L.get("glucose_mmol") or L.get("glucose_serum") or L.get("serum_glucose_mmol"))
    if gl is None and L.get("glucose_mg_dl") is not None:
        raw_g_mgdl = _coerce_float(L["glucose_mg_dl"])
        if raw_g_mgdl is not None and (raw_g_mgdl < 30 or raw_g_mgdl > 500):
            notes["glucose_mg_dl"] = "glucose value outside expected range for mg/dL — verify units"
        gl = float(L["glucose_mg_dl"]) * GLUCOSE_MGDL_TO_MMOLL
        notes["glucose_serum"] = "converted glucose_mg_dl -> mmol/L (/18.018)"
    if gl is not None:
        out["glucose_serum"] = gl
        if gl < 1.5 or gl > 45:
            prev = notes.get("glucose_serum")
            msg = "glucose mmol/L outside expected range — verify units (mg/dL vs mmol/L)"
            notes["glucose_serum"] = f"{prev}; {msg}" if prev else msg

    # CRP: model uses ln(mg/dL). Prefer explicit ln; else mg/L or mg/dL.
    crp_log = _coerce_float(L.get("crp_log") or L.get("crp_ln_mg_dl"))
    if crp_log is None:
        crp_mg_l = _coerce_float(
            L.get("crp_mg_l")
            or L.get("hscrp")
            or L.get("crp")
            or L.get("hscrp_mg_l")
            or L.get("hs_crp_mg_l")
            or L.get("hs_crp")
        )
        if crp_mg_l is None:
            for k in ("hscrp_mg_l", "hs_crp_mg_l", "hscrp", "hs_crp", "crp_mg_l", "crp"):
                if k in L:
                    crp_mg_l = _coerce_float(L[k])
                    if crp_mg_l is not None:
                        break
        if crp_mg_l is not None:
            mg_dl = crp_mg_l * MG_L_CRP_TO_MG_DL
            if mg_dl > 0:
                crp_log = math.log(mg_dl)
                ln_part = f"{crp_log:.6f}"
            else:
                crp_log = float("-inf")
                ln_part = "-inf (CRP mg/dL≤0; invalid)"
            notes["crp_log"] = (
                f"hsCRP/CRP mg/L={crp_mg_l} → CRP mg/dL={mg_dl} (÷10) → ln(mg/dL)={ln_part}; "
                "aliases: crp_mg_l, hscrp, hs_crp_mg_l, hsCRP_mg_l (case-insensitive keys)"
            )
    elif crp_log is not None:
        notes["crp_log"] = "used raw crp_log as ln(mg/dL)"
    if crp_log is not None and math.isfinite(crp_log):
        out["crp_log"] = crp_log

    lp = _coerce_float(L.get("lymphocyte_percent") or L.get("lymphocytes_percent") or L.get("lymphocyte_pct"))
    if lp is None and L.get("lymphocyte") is not None:
        raw = _coerce_float(L["lymphocyte"])
        if raw is not None and 0 < raw <= 100:
            lp = raw
            notes["lymphocyte_percent"] = "bare 'lymphocyte' interpreted as % (0–100)"
    if lp is not None:
        out["lymphocyte_percent"] = lp
        if lp < 1 or lp > 99:
            notes["lymphocyte_percent"] = "lymphocyte % outside 1–99 — verify units"

    for key, aliases in (
        ("mcv", ("mcv", "mcv_fl")),
        ("rdw", ("rdw", "rdw_percent", "rdw_pct", "rdx_percent")),
        (
            "alkaline_phosphatase",
            (
                "alkaline_phosphatase",
                "alk_phos",
                "alp",
                "alkaline_phosphatase_u_l",
                "alp_u_l",
            ),
        ),
        ("wbc", ("wbc", "white_blood_cell_count", "wbc_thousand", "white_blood_cells")),
    ):
        for a in aliases:
            v = _coerce_float(L.get(a))
            if v is not None:
                out[key] = v
                break

    wbc_v = out.get("wbc")
    if wbc_v is not None and (wbc_v < 1.0 or wbc_v > 50.0):
        notes["wbc"] = "WBC count outside expected range (×10³/µL) — verify units"
    mcv_v = out.get("mcv")
    if mcv_v is not None and (mcv_v < 50 or mcv_v > 130):
        notes["mcv"] = "MCV fL outside expected range — verify units"
    rdw_v = out.get("rdw")
    if rdw_v is not None and (rdw_v < 8 or rdw_v > 30):
        notes["rdw"] = "RDW % outside expected range — verify units"

    return out, notes


def phenoage_panel_diagnosis(body: Dict[str, Any], markers: Dict[str, float], age: Optional[int]) -> Dict[str, Any]:
    """Audit trail: which raw keys normalized, which PhenoAge canonical markers filled, what's missing for FULL."""
    bio = body.get("biomarkers") or body
    L = _normalize_biomarker_keys(bio if isinstance(bio, dict) else {})
    need = frozenset(PHENOAGE_KEY_TO_MAP_ID.keys())
    have = frozenset(markers.keys())
    return {
        "normalized_biomarker_keys": sorted(L.keys()),
        "phenoage_canonical_recognized": sorted(have),
        "phenoage_canonical_missing_for_full": sorted(need - have),
        "chronological_age_present": age is not None,
        "full_phenoage_eligible": need <= have and age is not None,
    }


def _tier_for_crp_log_as_hscrp_mg_l(value_ln_mg_dl: float, scorer: Any) -> Tuple[float, str]:
    """Convert ln(mg/dL) back to mg/L for hsCRP tiering in longevity map."""
    mg_dl = math.exp(value_ln_mg_dl)
    mg_l = mg_dl / MG_L_CRP_TO_MG_DL if MG_L_CRP_TO_MG_DL else mg_dl * 10.0
    bdef = scorer._biomarkers_by_id["hscrp"]
    parsed = scorer._score_numeric_biomarker(bdef, mg_l)
    if parsed is None:
        return 0.5, "MODERATE"
    return parsed


def _acceleration_from_tier(tier: str) -> str:
    if tier == "HIGH_RISK":
        return "ACCELERATING"
    if tier == "OPTIMAL":
        return "PROTECTIVE"
    return "NORMAL"


def _component_acceleration(
    scorer: Any,
    map_id: str,
    value_for_tiering: float,
    canonical_key: str,
) -> Tuple[str, str, float, str]:
    """Returns tier, acceleration_status, tier_score (0/0.5/1), tier_score_label."""
    if map_id == "hscrp" and canonical_key == "crp_log":
        sc, tier = _tier_for_crp_log_as_hscrp_mg_l(value_for_tiering, scorer)
    else:
        bdef = scorer._biomarkers_by_id.get(map_id)
        if not bdef:
            return "MODERATE", "NORMAL", 0.5, "UNKNOWN_BIOMARKER_DEF"
        parsed = scorer._score_numeric_biomarker(bdef, value_for_tiering)
        if parsed is None:
            return "MODERATE", "NORMAL", 0.5, "NON_NUMERIC_RULE"
        sc, tier = parsed
    accel = _acceleration_from_tier(tier)
    return tier, accel, sc, "OK"


def _value_for_tiering(canonical_key: str, value_phenoage: float) -> float:
    """Biomarker map thresholds use lab units (mg/L for hsCRP, etc.)."""
    if canonical_key == "crp_log":
        mg_dl = math.exp(value_phenoage)
        return mg_dl / MG_L_CRP_TO_MG_DL
    return value_phenoage


def _mortality_from_xb(xb: float, gamma: float, t_months: float) -> float:
    inner = math.exp(xb) * (math.exp(gamma * t_months) - 1.0) / gamma
    inner = max(min(inner, 50.0), 1e-15)
    return 1.0 - math.exp(-inner)


def _phenotypic_age(m: float, cal: Dict[str, float]) -> Optional[float]:
    m = max(min(m, 1.0 - 1e-15), 1e-15)
    ln_1m = math.log(1.0 - m)
    inner = float(cal["ln_numerator_coefficient"]) * ln_1m
    if inner <= 0 or not math.isfinite(inner):
        return None
    return float(cal["offset"]) + math.log(inner) / float(cal["denominator"])


def _nutrient_insulin_resistance_triad(body: Dict[str, Any], linear_terms: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """When glucose, fasting insulin, and HbA1c are all present, attach triad + HOMA-IR-style proxy (RUO)."""
    bio = body.get("biomarkers") or body
    if not isinstance(bio, dict):
        return None
    L = _normalize_biomarker_keys(bio)
    g = _coerce_float(L.get("glucose_mmol") or L.get("glucose_serum") or L.get("serum_glucose_mmol"))
    if g is None and L.get("glucose_mg_dl") is not None:
        try:
            g = float(L["glucose_mg_dl"]) * GLUCOSE_MGDL_TO_MMOLL
        except (TypeError, ValueError):
            g = None
    ins = _coerce_float(L.get("fasting_insulin") or L.get("fasting_insulin_uu_ml") or L.get("fasting_insulin_uiu_ml"))
    a1c = _coerce_float(L.get("hba1c_percent") or L.get("hba1c_pct") or L.get("hba1c"))
    if g is None or ins is None or a1c is None:
        return None
    homa = (ins * g) / 22.5 if g > 0 and ins > 0 else None
    pheno_glucose = next((r for r in linear_terms if r.get("canonical_key") == "glucose_serum"), None)
    out: Dict[str, Any] = {
        "glucose_mmol": round(g, 4),
        "fasting_insulin_uu_ml": ins,
        "hba1c_percent": round(a1c, 2),
        "homa_ir_proxy": round(homa, 3) if homa is not None else None,
        "pattern": "insulin_resistance_triad",
        "interpretation": (
            "Triangulates fasting glucose (mmol/L), fasting insulin (µU/mL), and HbA1c (%). "
            "Glucose may look optimal while insulin and HbA1c indicate insulin resistance. "
            "HOMA-IR proxy = (fasting insulin × glucose mmol/L) / 22.5 — research surrogate, not diagnostic."
        ),
    }
    if pheno_glucose:
        out["phenoage_glucose_tier"] = pheno_glucose.get("tier")
        out["phenoage_glucose_acceleration"] = pheno_glucose.get("acceleration_status")
    return out


def run_longevity_assessment_level0(body: Dict[str, Any]) -> Dict[str, Any]:
    coeff_root = _load_phenoage_coefficients()
    pmid = str(coeff_root.get("_provenance", {}).get("pmid") or "29676998")
    gm = coeff_root["gompertz_model"]
    intercept = float(gm["xb_intercept_constant"])
    gamma = float(gm["gamma_months"])
    t_months = float(gm["mortality_horizon_months"])
    pa_cal = gm["phenotypic_age_calibration"]
    age_w = float(coeff_root["chronological_age"]["gompertz_weight"])

    by_key = _get_coeff_by_key(coeff_root)
    scorer = get_longevity_hallmark_scorer()

    age = _extract_age(body)
    markers, conv_notes = extract_phenoage_marker_values(body)

    components_total = 9
    linear_terms: List[Dict[str, Any]] = []
    xb_partial = intercept

    crp_used = "crp_log" in markers

    for ck in sorted(by_key.keys()):
        spec = by_key[ck]
        w = float(spec["gompertz_weight"])
        if ck not in markers:
            continue
        val = markers[ck]
        term = w * val
        xb_partial += term
        map_id = PHENOAGE_KEY_TO_MAP_ID.get(ck, ck)
        # crp_log is ln(mg/dL); tiering must use that value, not mg/L from _value_for_tiering.
        tier_input = val if ck == "crp_log" else _value_for_tiering(ck, val)
        tier, accel, tscore, _ = _component_acceleration(scorer, map_id, tier_input, ck)

        assoc = scorer._biomarkers_by_id.get(map_id, {})
        hallmarks = [
            a.get("hallmark")
            for a in (assoc.get("hallmark_associations") or [])
            if a.get("hallmark") in _SHIPPABLE
        ]
        primary_hallmark = hallmarks[0] if hallmarks else None

        linear_terms.append(
            {
                "canonical_key": ck,
                "biomarker": ck,
                "label": spec.get("label"),
                "value": round(val, 6),
                "unit": spec.get("units"),
                "coefficient": w,
                "linear_term": round(term, 6),
                "tier": tier,
                "acceleration_status": accel,
                "acceleration_method": ACCEL_METHOD,
                "tier_score": tscore,
                "hallmarks_from_map": hallmarks,
                "primary_hallmark": primary_hallmark,
                "biomarker_map_id": map_id,
                "source": f"PhenoAge (Levine 2018, PMID {pmid})",
            }
        )

    # Age term (always add if age present — for partial xb display only)
    xb_with_age = xb_partial
    if age is not None:
        xb_with_age += age_w * age

    complete_keys = set(by_key.keys())
    have_keys = set(markers.keys())
    is_complete = complete_keys <= have_keys and age is not None

    phenoage_estimate: Optional[float] = None
    mortality_score: Optional[float] = None
    age_acceleration: Optional[float] = None
    completeness_mode = "PARTIAL"
    if is_complete:
        xb = intercept + sum(float(by_key[k]["gompertz_weight"]) * markers[k] for k in sorted(by_key.keys()))
        xb += age_w * float(age)
        mortality_score = _mortality_from_xb(xb, gamma, t_months)
        phenoage_estimate = _phenotypic_age(mortality_score, pa_cal)
        if phenoage_estimate is not None and age is not None:
            age_acceleration = phenoage_estimate - float(age)
        completeness_mode = "FULL_9BIOMARKERS_PLUS_AGE"

    top_accel_all = sorted(linear_terms, key=lambda r: abs(r["linear_term"]), reverse=True)
    top_accel = sorted(
        [r for r in linear_terms if r["acceleration_status"] == "ACCELERATING"],
        key=lambda r: abs(r["linear_term"]),
        reverse=True,
    )

    # PhenoAge-weighted hallmark signals (ACCELERATING only): sum |beta*x| per hallmark.
    pheno_hall: Dict[str, float] = {h: 0.0 for h in _SHIPPABLE}
    drivers: Dict[str, List[str]] = {h: [] for h in _SHIPPABLE}

    for row in linear_terms:
        if row["acceleration_status"] != "ACCELERATING":
            continue
        mag = abs(float(row["linear_term"]))
        ck = row["canonical_key"]
        for hm in row.get("hallmarks_from_map") or []:
            if hm in pheno_hall:
                pheno_hall[hm] += mag
                drivers[hm].append(ck)

    # Supplementary biomarkers: in map, not used as PhenoAge components; never merge into PA.
    resolved = scorer._parse_resolved_biomarkers(body.get("biomarkers") or body)
    egfr_side = resolved.pop("_egfr_for_cystatin", None)
    skip_ids = set(PHENOAGE_BIOMARKER_MAP_IDS)
    if crp_used:
        skip_ids.add("hscrp")
    supplementary: Dict[str, Any] = {}
    for bid, val in sorted(resolved.items()):
        if bid.startswith("_"):
            continue
        if bid in skip_ids:
            continue
        if bid not in scorer._biomarkers_by_id:
            continue
        bdef = scorer._biomarkers_by_id[bid]
        if bdef.get("direction") == "HIGH_CYSTATIN_LOW_EGFR_IS_VULNERABLE":
            continue
        if bid == "cystatin_c_egfr":
            if egfr_side is None:
                continue
            sc, tier = scorer._score_cystatin_egfr(float(val), float(egfr_side))
        else:
            parsed = scorer._score_numeric_biomarker(bdef, val)
            if parsed is None:
                continue
            sc, tier = parsed
        hall_list = [
            a.get("hallmark")
            for a in (bdef.get("hallmark_associations") or [])
            if a.get("hallmark") in _SHIPPABLE
        ]
        supplementary[bid] = {
            "value": val,
            "tier": tier,
            "tier_score": sc,
            "hallmarks": hall_list,
            "calibration": "threshold-based (not mortality-calibrated)",
        }

    # Hallmark narrative: separate phenoage_signal vs supplementary_signal (no blend).
    supp_hall: Dict[str, float] = {h: 0.0 for h in _SHIPPABLE}
    supp_detail: Dict[str, List[str]] = {h: [] for h in _SHIPPABLE}
    for bid, pay in supplementary.items():
        ts = float(pay.get("tier_score") or 0)
        for hm in pay.get("hallmarks") or []:
            if hm in supp_hall:
                supp_hall[hm] += ts
                supp_detail[hm].append(bid)

    # Partial panel: if PhenoAge top accelerator is weak linearly but supplementary tier sums are strong,
    # surface dominant supplementary hallmark first (UX + compound narrative alignment).
    dominant_supp_hm: Optional[str] = None
    supplementary_dominates = False
    if completeness_mode == "PARTIAL" and supp_hall:
        candidates = [(hm, float(v)) for hm, v in supp_hall.items() if float(v) > 1.5]
        pheno_top_signal = 0.0
        if top_accel:
            tph = top_accel[0].get("primary_hallmark")
            if tph:
                pheno_top_signal = float(pheno_hall.get(tph) or 0.0)
        if candidates and pheno_top_signal < 0.1:
            dominant_supp_hm = max(candidates, key=lambda kv: kv[1])[0]
            supplementary_dominates = True

    max_p = max(pheno_hall.values()) if pheno_hall else 0.0
    hallmark_narrative: Dict[str, Any] = {}
    for hm in sorted(_SHIPPABLE):
        ps = pheno_hall.get(hm) or 0.0
        ss = supp_hall.get(hm) or 0.0
        if ps <= 0 and ss <= 0:
            continue
        base_primary = ps >= max_p and ps > 0
        if supplementary_dominates and dominant_supp_hm:
            if hm == dominant_supp_hm:
                status = "PRIMARY_DRIVER"
            elif base_primary:
                status = "SECONDARY_DRIVER"
            elif ps <= 0:
                status = "SUPPLEMENTARY_ONLY"
            else:
                status = "SECONDARY_DRIVER"
        else:
            status = "PRIMARY_DRIVER" if base_primary else ("SUPPLEMENTARY_ONLY" if ps <= 0 else "SECONDARY_DRIVER")
        hallmark_narrative[hm] = {
            "status": status,
            "phenoage_signal": round(ps, 4),
            "supplementary_signal": round(ss, 4),
            "supplementary_signal_note": "Sum of threshold tier_scores (0/0.5/1) for this hallmark — not blended with PhenoAge.",
            "driving_biomarkers_phenoage": drivers.get(hm) or [],
            "driving_biomarkers_supplementary": supp_detail.get(hm) or [],
            "explanation": (
                f"PhenoAge-linear-term magnitude from accelerating components mapped to this hallmark "
                f"({len(drivers.get(hm) or [])} analytes). Supplementary tier scores add a separate, non-mortality-calibrated signal."
            ),
        }

    triad = _nutrient_insulin_resistance_triad(body, linear_terms)
    if triad:
        ns = hallmark_narrative.setdefault("nutrient_sensing", {})
        ns["insulin_resistance_triad"] = triad

    scored_tiers: List[str] = [str(r.get("tier") or "") for r in linear_terms]
    scored_tiers.extend(str(pay.get("tier") or "") for pay in supplementary.values())
    all_optimal = bool(scored_tiers) and all(t == "OPTIMAL" for t in scored_tiers)

    # Compound relevance: PhenoAge linear magnitudes when accelerating; else normalized supplementary tier sum.
    compound_queries = body.get("compound_queries") or []
    meds = body.get("patient_medications") or []
    vuln_for_compounds: Dict[str, Dict[str, Any]] = {}
    for h in _SHIPPABLE:
        ph = float(pheno_hall.get(h) or 0.0)
        sh = float(supp_hall.get(h) or 0.0)
        supp_ids = supp_detail.get(h) or []
        n_supp = len(supp_ids)
        force_supp = supplementary_dominates and dominant_supp_hm and h == dominant_supp_hm and sh > 0 and n_supp > 0
        if force_supp:
            norm = sh / float(n_supp)
            vuln_for_compounds[h] = {
                "vulnerability": min(1.0, norm),
                "tier": "SUPPLEMENTARY_TIER_NORMALIZED",
                "calibration_label": "threshold-based (not mortality-calibrated)",
                "scoring_source": "supplementary",
                "driven_biomarkers": list(supp_ids),
            }
        elif ph > 0:
            vuln_for_compounds[h] = {
                "vulnerability": ph,
                "tier": "PHENOAGE_LINEAR_MAGNITUDE",
                "calibration_label": "PhenoAge-calibrated (mortality-validated)",
                "scoring_source": "phenoage",
                "driven_biomarkers": drivers.get(h) or [],
            }
        elif sh > 0 and n_supp > 0:
            norm = sh / float(n_supp)
            vuln_for_compounds[h] = {
                "vulnerability": min(1.0, norm),
                "tier": "SUPPLEMENTARY_TIER_NORMALIZED",
                "calibration_label": "threshold-based (not mortality-calibrated)",
                "scoring_source": "supplementary",
                "driven_biomarkers": list(supp_ids),
            }

    if all_optimal:
        vuln_for_compounds = {}

    supple_driven_hallmarks = [
        h
        for h in _SHIPPABLE
        if (float(pheno_hall.get(h) or 0.0) <= 0) and (float(supp_hall.get(h) or 0.0) > 0)
    ]
    if is_complete:
        scoring_calibration = (
            "PhenoAge full panel — compound relevance uses mortality-validated "
            "PhenoAge linear-term magnitudes for accelerating hallmarks; supplementary tier only when no PhenoAge signal for that hallmark."
        )
    elif supple_driven_hallmarks and compound_queries:
        scoring_calibration = "threshold-based — provide full CBC+CMP+CRP for mortality-calibrated PhenoAge scoring"
    else:
        scoring_calibration = (
            "PhenoAge partial panel — compound relevance uses accelerating PhenoAge components where present; "
            "otherwise normalized supplementary biomarker tiers with explicit per-match labels."
        )

    if supplementary_dominates:
        scoring_calibration += " (supplementary biomarkers dominant due to limited PhenoAge panel)"

    if supplementary_dominates and dominant_supp_hm is not None:
        sumv = float(supp_hall.get(dominant_supp_hm) or 0.0)
        supp_syn_row: Dict[str, Any] = {
            "canonical_key": None,
            "biomarker": "supplementary_panel",
            "label": f"Dominant supplementary signal — {dominant_supp_hm.replace('_', ' ')}",
            "value": None,
            "unit": None,
            "coefficient": None,
            "linear_term": None,
            "tier": "HIGH_RISK",
            "acceleration_status": "ACCELERATING",
            "acceleration_method": ACCEL_METHOD,
            "tier_score": round(sumv, 4),
            "hallmarks_from_map": [dominant_supp_hm],
            "primary_hallmark": dominant_supp_hm,
            "biomarker_map_id": None,
            "source": (
                "Supplementary tier_score sum for this hallmark exceeds 1.5 while the top PhenoAge "
                "ACCELERATOR hallmark linear signal is <0.1 (partial panel)."
            ),
            "supplementary_dominance": True,
            "driving_supplementary_biomarkers": list(supp_detail.get(dominant_supp_hm) or []),
        }
        display_top_accel: List[Dict[str, Any]] = [supp_syn_row] + top_accel[:11]
    else:
        display_top_accel = top_accel[:12]

    recs = scorer.score_compounds_for_hallmarks(
        {h: (vuln_for_compounds.get(h) if h in vuln_for_compounds else None) for h in _SHIPPABLE},
        list(compound_queries),
        patient_medications=list(meds),
    )
    compound_out = []
    for r in recs:
        d = r.as_dict()
        matches = d.get("hallmark_matches") or []
        primary = matches[0]["hallmark"] if matches else None
        compound_out.append(
            {
                "compound": d["compound"],
                "display_name": d["display_name"],
                "overall_relevance": d["overall_relevance"],
                "primary_match": primary,
                "hallmark_matches": matches,
                "dose": d.get("dose"),
                "interactions": d.get("interactions"),
                "safety_flags": d.get("safety_flags"),
                "scoring_note": (
                    "Per hallmark_match: PhenoAge-calibrated when scoring_source=phenoage; "
                    "threshold-based when scoring_source=supplementary (not mortality-calibrated). Never blended without labels."
                ),
            }
        )

    run_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    return {
        "status": "SUCCESS",
        "level": 0,
        "phenoage_analysis": {
            "components_available": len(markers),
            "components_total": components_total,
            "age_years": age,
            "xb_partial_if_complete_else_absent_note": "xb (full published form) computed only when all 9 lab components and age are present.",
            "phenoage_estimate": round(phenoage_estimate, 2) if phenoage_estimate is not None else None,
            "mortality_score_10yr": round(mortality_score, 6) if mortality_score is not None else None,
            "age_acceleration": round(age_acceleration, 2) if age_acceleration is not None else None,
            "completeness_mode": completeness_mode,
            "top_accelerators": display_top_accel,
            "top_by_linear_term_magnitude": top_accel_all[:12],
            "all_components": linear_terms,
            "conversion_notes": conv_notes,
            "source_pmid": pmid,
            "calibration_note": (
                "Coefficients from Gompertz PH model (Supplementary Table S1 / Table 1, PMID 29676998). "
                "PhenotypicAge and 10-year mortality require all nine biomarkers in published units plus chronological age; "
                f"partial inputs yield per-component linear terms only. {ACCEL_METHOD}"
            ),
        },
        "supplementary_biomarkers": supplementary,
        "hallmark_narrative": hallmark_narrative,
        "scoring_calibration": scoring_calibration,
        "compound_recommendations": compound_out,
        "data_completeness": {
            "phenoage_components": len(markers),
            "phenoage_total": components_total,
            "phenoage_complete_for_full_estimate": is_complete,
            "supplementary_biomarkers": len(supplementary),
            "hallmarks_scoreable": len(hallmark_narrative),
            "phenoage_panel_diagnosis": phenoage_panel_diagnosis(body, markers, age),
            "all_optimal": all_optimal,
            "recommendation": (
                "maintain current protocol"
                if all_optimal
                else (
                    "Provide CBC, CMP (including glucose, albumin, creatinine, alk phos), CRP (or hsCRP), and age for full PhenoAge."
                    if not is_complete
                    else "Panel complete for published PhenoAge mortality step."
                )
            ),
        },
        "provenance": {
            "framework": "CrisPRO Longevity Assessment v1.0 Level 0",
            "scoring_engine": "PhenoAge Gompertz coefficients (PMID 29676998)",
            "hallmark_framework": "Lopez-Otin 2013 (PMID 23746838) / 2023 (PMID 36599349) — associations from biomarker_hallmark_map.json only",
            "compound_source": "longevity_compound_hallmark_map.json (PMID-verified links where flagged)",
            "biomarker_source": "biomarker_hallmark_map.json + phenoage_gompertz_coefficients_levine2018.json",
            "timestamp": ts,
            "run_id": run_id,
        },
        "disclaimer": (
            "Research Use Only. Biological age estimation follows published PhenoAge transforms; "
            "acceleration labels are CrisPRO UX thresholds, not PhenoAge classifications. "
            "Do not use for clinical decisions without a qualified clinician."
        ),
    }

