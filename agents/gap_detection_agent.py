from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .state import PatientState

# ─────────────────────────────────────────────────────────────────────────────
# PhenoAge canonical biomarker keys (9 required for full estimate)
# ─────────────────────────────────────────────────────────────────────────────
_PHENOAGE_REQUIRED = frozenset({
    "albumin",
    "creatinine",
    "glucose_serum",   # or glucose_mg_dl
    "crp_log",         # or crp_mg_l / hscrp
    "lymphocyte_percent",
    "mcv",
    "rdw",
    "alkaline_phosphatase",
    "wbc",
})

# Friendly names for gap messages
_PHENOAGE_FRIENDLY: Dict[str, str] = {
    "albumin":             "Albumin (g/dL)",
    "creatinine":          "Creatinine (mg/dL)",
    "glucose_serum":       "Fasting Glucose (mg/dL or mmol/L)",
    "crp_log":             "hsCRP / CRP (mg/L)",
    "lymphocyte_percent":  "Lymphocyte % (CBC diff)",
    "mcv":                 "MCV (fL)",
    "rdw":                 "RDW (%)",
    "alkaline_phosphatase":"Alkaline Phosphatase (U/L)",
    "wbc":                 "WBC (×10³/µL)",
}

# Severity ordering for sorting
_SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def _normalize_keys(bio: Dict[str, Any]) -> Dict[str, Any]:
    """Case/spacing-insensitive key normalization (mirrors longevity_phenoage_level0)."""
    return {
        str(k).strip().replace("-", "_").replace("/", "_").lower(): v
        for k, v in bio.items()
    }


def _detect_phenoage_markers_present(bio_norm: Dict[str, Any]) -> frozenset:
    """Return which PhenoAge canonical keys are present in the normalized biomarker dict."""
    present = set()
    # albumin
    if any(k in bio_norm for k in ("albumin", "albumin_g_dl", "albumin_g_l")):
        present.add("albumin")
    # creatinine
    if any(k in bio_norm for k in ("creatinine", "creatinine_mg_dl", "creatinine_umol_l")):
        present.add("creatinine")
    # glucose
    if any(k in bio_norm for k in ("glucose_mg_dl", "glucose_mmol", "glucose_serum", "serum_glucose_mmol")):
        present.add("glucose_serum")
    # CRP
    if any(k in bio_norm for k in ("crp_log", "crp_ln_mg_dl", "crp_mg_l", "hscrp", "crp",
                                    "hscrp_mg_l", "hs_crp_mg_l", "hs_crp")):
        present.add("crp_log")
    # lymphocyte %
    if any(k in bio_norm for k in ("lymphocyte_percent", "lymphocytes_percent", "lymphocyte_pct", "lymphocyte")):
        present.add("lymphocyte_percent")
    # MCV
    if any(k in bio_norm for k in ("mcv", "mcv_fl")):
        present.add("mcv")
    # RDW
    if any(k in bio_norm for k in ("rdw", "rdw_percent", "rdw_pct")):
        present.add("rdw")
    # ALP
    if any(k in bio_norm for k in ("alkaline_phosphatase", "alk_phos", "alp", "alkaline_phosphatase_u_l", "alp_u_l")):
        present.add("alkaline_phosphatase")
    # WBC
    if any(k in bio_norm for k in ("wbc", "white_blood_cell_count", "wbc_thousand", "white_blood_cells")):
        present.add("wbc")
    return frozenset(present)


def _make_gap(
    category: str,
    severity: str,
    message: str,
    recommended_action: str,
    data_needed: List[str],
) -> Dict[str, Any]:
    return {
        "gap_id": str(uuid.uuid4()),
        "category": category,
        "severity": severity,
        "message": message,
        "recommended_action": recommended_action,
        "data_needed": data_needed,
    }


def gap_detection_agent(state: PatientState) -> PatientState:
    """
    Analyzes the patient state and identifies what data is MISSING that would
    improve the longevity assessment. Produces a prioritized gap list.
    """
    ci: Dict[str, Any] = state.get("current_input", {})
    bio_raw: Dict[str, Any] = ci.get("biomarkers", {}) or {}
    bio: Dict[str, Any] = _normalize_keys(bio_raw)
    visit_history: List[Any] = state.get("visit_history", []) or []
    errors = list(state.get("errors", []))
    agents_run = list(state.get("agents_run", []))

    gaps: List[Dict[str, Any]] = []

    # ── 1. PHENOAGE_INCOMPLETE ────────────────────────────────────────────────
    present_markers = _detect_phenoage_markers_present(bio)
    missing_markers = _PHENOAGE_REQUIRED - present_markers
    if missing_markers:
        missing_friendly = [_PHENOAGE_FRIENDLY.get(m, m) for m in sorted(missing_markers)]
        n_present = len(present_markers)
        n_total = len(_PHENOAGE_REQUIRED)
        severity = "HIGH" if n_present < 5 else "MEDIUM"
        gaps.append(_make_gap(
            category="PHENOAGE_INCOMPLETE",
            severity=severity,
            message=(
                f"PhenoAge panel incomplete ({n_present}/{n_total} biomarkers present) — "
                f"full biological age estimate requires all 9. "
                f"Missing: {', '.join(missing_friendly)}."
            ),
            recommended_action=(
                "Order CBC with differential (WBC, lymphocyte %, MCV, RDW) + "
                "CMP (albumin, creatinine, glucose, alkaline phosphatase) + hsCRP."
            ),
            data_needed=missing_friendly,
        ))

    # ── 2. NO_LIPID_PANEL ─────────────────────────────────────────────────────
    has_ldl = any(k in bio for k in ("ldl_cholesterol", "ldl", "ldl_c"))
    has_hdl = any(k in bio for k in ("hdl_cholesterol", "hdl", "hdl_c"))
    has_trig = any(k in bio for k in ("triglycerides", "triglyceride", "trig"))
    if not has_ldl and not has_hdl and not has_trig:
        gaps.append(_make_gap(
            category="NO_LIPID_PANEL",
            severity="HIGH",
            message=(
                "Standard lipid panel missing — cardiovascular risk cannot be computed. "
                "LDL, HDL, and triglycerides are all absent."
            ),
            recommended_action=(
                "Order fasting lipid panel: total cholesterol, LDL-C, HDL-C, triglycerides."
            ),
            data_needed=["Total Cholesterol (mg/dL)", "LDL-C (mg/dL)", "HDL-C (mg/dL)", "Triglycerides (mg/dL)"],
        ))

    # ── 3. NO_GENETICS ────────────────────────────────────────────────────────
    has_variants = bool(ci.get("variants"))
    has_genotype = bool(ci.get("patient_genotype"))
    if not has_variants and not has_genotype:
        gaps.append(_make_gap(
            category="NO_GENETICS",
            severity="MEDIUM",
            message=(
                "Genetic panel not provided — APOE, FOXO3, MTHFR status unknown. "
                "Longevity PRS and DNA repair capacity cannot be scored."
            ),
            recommended_action=(
                "Provide SNP genotyping data (rs429358, rs7412 for APOE; rs1801133, rs1801131 for MTHFR) "
                "or upload raw genome file for full genetic longevity assessment."
            ),
            data_needed=["APOE (rs429358, rs7412)", "MTHFR (rs1801133, rs1801131)", "FOXO3 (rs2802292)",
                         "DNA repair gene panel (BRCA1/2, ERCC1, XRCC1, etc.)"],
        ))

    # ── 4. NO_HORMONES ────────────────────────────────────────────────────────
    has_dheas = any(k in bio for k in ("dhea_s", "dheas", "dhea_sulfate", "dehydroepiandrosterone_sulfate"))
    has_free_t = any(k in bio for k in ("free_testosterone", "testosterone_free", "free_t"))
    has_igf1 = any(k in bio for k in ("igf_1", "igf1", "igf_i", "insulin_like_growth_factor_1"))
    if not has_dheas and not has_free_t and not has_igf1:
        gaps.append(_make_gap(
            category="NO_HORMONES",
            severity="MEDIUM",
            message=(
                "Hormone panel missing — DHEA-S, free testosterone, and IGF-1 are all absent. "
                "Hormonal aging trajectory cannot be assessed."
            ),
            recommended_action=(
                "Order hormone panel: DHEA-S, free testosterone (or total + SHBG), IGF-1, "
                "and consider cortisol AM for HPA axis assessment."
            ),
            data_needed=["DHEA-S (µg/dL)", "Free Testosterone (pg/mL)", "IGF-1 (ng/mL)", "Cortisol AM (µg/dL)"],
        ))

    # ── 5. NO_INFLAMMATION_DEEP ───────────────────────────────────────────────
    has_il6 = any(k in bio for k in ("il_6", "il6", "interleukin_6", "interleukin6"))
    has_tnfa = any(k in bio for k in ("tnf_alpha", "tnfa", "tnf_a", "tumor_necrosis_factor_alpha"))
    if not has_il6 and not has_tnfa:
        gaps.append(_make_gap(
            category="NO_INFLAMMATION_DEEP",
            severity="MEDIUM",
            message=(
                "Deep inflammation markers missing — IL-6 and TNF-α are both absent. "
                "Inflammaging burden cannot be fully characterized (hsCRP alone is insufficient)."
            ),
            recommended_action=(
                "Order deep inflammation panel: IL-6 (pg/mL), TNF-α (pg/mL). "
                "Consider also IL-18, MCP-1 for comprehensive inflammaging assessment."
            ),
            data_needed=["IL-6 (pg/mL)", "TNF-α (pg/mL)", "IL-18 (pg/mL)"],
        ))

    # ── 6. NO_WEARABLES ───────────────────────────────────────────────────────
    has_wearables = bool(ci.get("wearables"))
    if not has_wearables:
        gaps.append(_make_gap(
            category="NO_WEARABLES",
            severity="LOW",
            message=(
                "Wearable data (HRV, VO2max, sleep) not integrated. "
                "Functional fitness and autonomic health cannot be assessed."
            ),
            recommended_action=(
                "Connect wearable device (Apple Watch, Garmin, Oura Ring, WHOOP) to provide "
                "HRV, resting heart rate, VO2max estimate, sleep stages, and activity data."
            ),
            data_needed=["HRV (ms)", "VO2max (mL/kg/min)", "Resting HR (bpm)",
                         "Sleep duration (hrs)", "Deep sleep %", "Daily steps"],
        ))

    # ── 7. NO_BODY_COMPOSITION ────────────────────────────────────────────────
    has_body_comp = bool(ci.get("body_composition"))
    has_dexa = any(k in bio for k in ("visceral_fat", "lean_mass", "bone_density", "body_fat_percent",
                                       "dexa_visceral_fat", "appendicular_lean_mass"))
    if not has_body_comp and not has_dexa:
        gaps.append(_make_gap(
            category="NO_BODY_COMPOSITION",
            severity="LOW",
            message=(
                "Body composition (visceral fat, lean mass, bone density) not assessed. "
                "Sarcopenia risk and metabolic body composition cannot be evaluated."
            ),
            recommended_action=(
                "Order DEXA scan for body composition: visceral adipose tissue (VAT), "
                "appendicular lean mass index (ALMI), bone mineral density (BMD)."
            ),
            data_needed=["Visceral Fat Area (cm²)", "Appendicular Lean Mass Index (kg/m²)",
                         "Bone Mineral Density (g/cm²)", "Body Fat % (DEXA)"],
        ))

    # ── 8. NO_EPIGENETIC_CLOCK ────────────────────────────────────────────────
    has_epigenetic = any(k in bio for k in ("dnam_age", "grimage", "grimace", "dunedinpace",
                                             "epigenetic_age", "horvath_age", "pheno_dnam_age"))
    has_epigenetic_result = bool(ci.get("epigenetic_clock"))
    if not has_epigenetic and not has_epigenetic_result:
        gaps.append(_make_gap(
            category="NO_EPIGENETIC_CLOCK",
            severity="MEDIUM",
            message=(
                "Epigenetic clock (GrimAge, DunedinPACE) not run. "
                "DNA methylation-based biological age is the most validated aging biomarker."
            ),
            recommended_action=(
                "Order methylation array (Illumina EPIC) or commercial epigenetic age test "
                "(TruAge, Elysium Index, Chronomics) to obtain GrimAge and DunedinPACE."
            ),
            data_needed=["GrimAge (years)", "DunedinPACE (pace of aging)", "Horvath DNAmAge (years)"],
        ))

    # ── 9. NO_MICROBIOME ──────────────────────────────────────────────────────
    has_microbiome = any(k in bio for k in ("microbiome_diversity", "gut_diversity", "shannon_diversity",
                                             "microbiome_score", "gut_health_score"))
    has_microbiome_result = bool(ci.get("microbiome"))
    if not has_microbiome and not has_microbiome_result:
        gaps.append(_make_gap(
            category="NO_MICROBIOME",
            severity="LOW",
            message=(
                "Gut microbiome diversity not assessed. "
                "Microbiome composition is linked to inflammaging, metabolic health, and longevity."
            ),
            recommended_action=(
                "Order gut microbiome sequencing (16S rRNA or shotgun metagenomics) "
                "via Viome, Biomesight, or clinical lab to assess diversity and keystone species."
            ),
            data_needed=["Shannon Diversity Index", "Firmicutes/Bacteroidetes ratio",
                         "Akkermansia muciniphila abundance", "Bifidobacterium abundance"],
        ))

    # ── 10 & 11. LONGITUDINAL GAPS ────────────────────────────────────────────
    if not visit_history:
        gaps.append(_make_gap(
            category="LONGITUDINAL_FIRST_VISIT",
            severity="LOW",
            message=(
                "First visit — no prior assessment data available. "
                "Establish baseline for longitudinal biological age tracking."
            ),
            recommended_action=(
                "Schedule follow-up assessment in 3–6 months to establish trajectory. "
                "Ensure all biomarkers are collected consistently for valid delta computation."
            ),
            data_needed=["Repeat full biomarker panel in 3–6 months"],
        ))
    else:
        # Check if last visit was > 6 months ago
        last_visit = visit_history[-1]
        last_ts_str = last_visit.get("timestamp", "")
        days_since: Optional[int] = None
        try:
            last_dt = datetime.fromisoformat(last_ts_str.replace("Z", "+00:00"))
            now_dt = datetime.now(timezone.utc)
            days_since = (now_dt - last_dt).days
        except Exception:
            days_since = None

        if days_since is not None and days_since > 180:
            gaps.append(_make_gap(
                category="LONGITUDINAL_GAP",
                severity="MEDIUM",
                message=(
                    f"Last assessment was {days_since} days ago — recommend re-assessment. "
                    "Longitudinal tracking requires assessments every 3–6 months for meaningful trajectory."
                ),
                recommended_action=(
                    "Schedule comprehensive biomarker re-assessment. "
                    "Prioritize PhenoAge panel, lipids, and inflammation markers for delta computation."
                ),
                data_needed=["Full PhenoAge panel", "Lipid panel", "hsCRP", "Hormone panel"],
            ))

    # ── Sort by severity (HIGH → MEDIUM → LOW) ────────────────────────────────
    gaps.sort(key=lambda g: _SEVERITY_ORDER.get(g["severity"], 99))

    state["detected_gaps"] = gaps
    state["gap_priority_order"] = [g["category"] for g in gaps]
    agents_run.append("gap_detection_agent")
    state["agents_run"] = agents_run
    state["errors"] = errors
    return state
