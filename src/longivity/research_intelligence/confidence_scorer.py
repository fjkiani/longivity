"""
ConfidenceScorer — Deterministic evidence confidence scoring.

Replaces LLM-hallucinated confidence floats with a mathematically grounded formula
based on study design hierarchy, sample size, biomarker match, and mechanism specificity.

Formula v3 — rct scaling + is_fda_approved + numeric biomarker parsing (2026-05-23):
──────────────────────────────────────────────────────────────────────────────────────
Per-type study components (sub-capped):
    rct_component     = min(rct_count    * 0.20, 0.60)   # 0.20/RCT, max 3 RCTs
                        # v2 was 0.40 flat cap — suppressed Phase III multi-RCT drugs
                        # v3: 1 RCT=0.20, 2 RCTs=0.40, 3+ RCTs=0.60
    obs_component     = min(obs_count    * 0.08, 0.12)   # max 1.5 obs studies
    invivo_component  = min(invivo_count * 0.04, 0.06)   # max 1.5 in vivo studies
    invitro_component = min(invitro_count* 0.01, 0.04)   # max 4 in vitro studies
    study_score       = min(sum, 0.60)                   # HARD CAP — prevents inflation

Additive components:
    size_score        = min(log10(n) / log10(50_000), 1.0) * 0.10   # max 0.10
    biomarker_score   = 0.10 if (biomarker_match AND study_score >= 0.20) else 0.0
    specificity_score = mechanism_specificity * 0.08                 # max 0.08
    soc_bonus         = 0.15 if is_fda_approved else 0.0             # SOC reward

Clinical-phase ceiling (hard cap on overall score):
    is_fda_approved=True               → 1.00   FDA-approved SOC — no ceiling
    Phase III  (rct≥1, n≥1000)        → 1.00   Large multi-site RCT
    Phase II   (rct≥1, n≥300)         → 0.75   Controlled trial
    Phase I    (rct≥1, n≥100)         → 0.60   Small RCT
    Pilot RCT  (rct≥1, n<100)         → 0.50   Supplement / exploratory
    Obs only                           → 0.40   Epidemiological
    In vivo only                       → 0.25   Animal model
    In vitro only                      → 0.15   Preclinical

    overall = min(study_score + size_score + biomarker_score + specificity_score + soc_bonus,
                  clinical_phase_ceiling)

Numeric biomarker parsing (v3 — was broken in v2):
    v2 bug: biomarker_mechanism_map used mixed-case keys ("HbA1c") but lookup
            used biomarker_key.upper() ("HBAIC") → no match → biomarker bonus lost
    v2 bug: numeric values (HbA1c=8.2) had no threshold evaluation — silently skipped
    v3 fix: all map keys normalized to UPPERCASE; numeric values evaluated against
            NUMERIC_BIOMARKER_THRESHOLDS (HbA1c>6.5=diabetic, fasting_glucose>100, etc.)

Calibrated outputs (v3):
    Sulforaphane (1 pilot RCT n=40, 2 obs, 3 invitro, HRD+, spec=0.70)
        → 0.50  MODERATE  ceiling=0.50  ✓
    Berberine (2 RCT n=120, 1 obs, 2 invitro, HbA1c=8.2 FIXED, spec=0.65)
        → 0.60  MODERATE  ceiling=0.60  ✓ (biomarker_match now True)
    Olaparib Phase III FDA (3 RCT n=2000, HRD+, spec=0.95, is_fda=True)
        → 0.9963  STRONG  ceiling=1.00  ✓ (was 0.75 — FIXED)
    Gemcitabine Phase III FDA (5 RCT n=5000, spec=0.60, is_fda=True)
        → 0.88  STRONG  ceiling=1.00  ✓
    In vitro only + HRD+ (gate test)
        → 0.08  INSUFFICIENT  ceiling=0.15  ✓
    Supplement→FDA gap: 0.50  ✓ (was 0.25)
"""

from __future__ import annotations

import logging
import re
from math import log10
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Evidence tier thresholds
TIER_STRONG   = 0.70
TIER_MODERATE = 0.45
TIER_WEAK     = 0.20
# < WEAK → INSUFFICIENT


# ── Numeric biomarker clinical thresholds ─────────────────────────────────────
# Keys are UPPERCASE. direction: "above" = elevated if value > threshold.
NUMERIC_BIOMARKER_THRESHOLDS: Dict[str, Tuple[float, str]] = {
    "HBA1C":           (6.5,   "above"),   # >6.5% = diabetic
    "FASTING_GLUCOSE": (100.0, "above"),   # >100 mg/dL = impaired fasting glucose
    "CRP":             (3.0,   "above"),   # >3.0 mg/L = high cardiovascular risk
    "PSA":             (4.0,   "above"),   # >4.0 ng/mL = elevated
    "LDL":             (130.0, "above"),   # >130 mg/dL = borderline high
    "BMI":             (25.0,  "above"),   # >25 = overweight
    "EGFR":            (60.0,  "below"),   # <60 mL/min = CKD stage 3+
    "CREATININE":      (1.2,   "above"),   # >1.2 mg/dL = elevated
    "ALT":             (40.0,  "above"),   # >40 U/L = elevated
    "AST":             (40.0,  "above"),   # >40 U/L = elevated
    "HEMOGLOBIN":      (12.0,  "below"),   # <12 g/dL = anemia
    "PLATELET":        (150.0, "below"),   # <150 K/µL = thrombocytopenia
    "WBC":             (11.0,  "above"),   # >11 K/µL = leukocytosis
    "CA125":           (35.0,  "above"),   # >35 U/mL = elevated (ovarian cancer marker)
    "CEA":             (5.0,   "above"),   # >5 ng/mL = elevated (colorectal marker)
    "AFP":             (10.0,  "above"),   # >10 ng/mL = elevated (liver marker)
    "TMB":             (10.0,  "above"),   # >10 mut/Mb = TMB-high (immunotherapy)
    "GLUCOSE":         (100.0, "above"),   # alias for fasting glucose
    "BLOOD_GLUCOSE":   (100.0, "above"),   # alias
}

# ── Biomarker → mechanism keyword map (ALL KEYS UPPERCASE) ───────────────────
# v2 bug: keys were mixed-case ("HbA1c") but lookup used .upper() ("HBAIC") → no match
# v3 fix: all keys are UPPERCASE
BIOMARKER_MECHANISM_MAP: Dict[str, List[str]] = {
    "HRD":             ["dna repair", "brca", "parp", "nrf2", "hdac", "homologous recombination"],
    "BRCA2":           ["dna repair", "brca", "nrf2", "hdac"],
    "BRCA1":           ["dna repair", "brca", "nrf2"],
    "TMB":             ["immune", "pd-l1", "checkpoint", "inflammation"],
    "CRP":             ["inflammation", "nf-kb", "cox-2", "il-6", "tnf"],
    "HBA1C":           ["glucose", "insulin", "ampk", "glut", "mtor"],
    "FASTING_GLUCOSE": ["glucose", "insulin", "ampk", "glut"],
    "GLUCOSE":         ["glucose", "insulin", "ampk", "glut"],
    "LDL":             ["ldl", "statin", "cholesterol", "oxidative"],
    "PSA":             ["androgen", "ar", "testosterone"],
    "CA125":           ["ovarian", "brca", "parp", "nrf2"],
    "CEA":             ["colorectal", "kras", "vegf", "egfr"],
    "EGFR":            ["egfr", "tyrosine kinase", "pi3k"],
    "HER2":            ["her2", "erbb2", "trastuzumab", "pi3k"],
    "ER":              ["estrogen", "aromatase", "er", "tamoxifen"],
    "PR":              ["progesterone", "pr", "hormone"],
    "KRAS":            ["kras", "ras", "mapk", "mek", "erk"],
    "BRAF":            ["braf", "mapk", "mek", "erk"],
    "MSI":             ["mismatch repair", "mmr", "immune", "checkpoint"],
    "MSS":             ["mismatch repair", "mmr"],
    "PD_L1":           ["pd-l1", "immune", "checkpoint", "immunotherapy"],
    "ALK":             ["alk", "tyrosine kinase", "crizotinib"],
    "ROS1":            ["ros1", "tyrosine kinase"],
    "NTRK":            ["ntrk", "trk", "tyrosine kinase"],
}


def _is_biomarker_elevated(key_upper: str, value: Any) -> bool:
    """
    Return True if the biomarker value indicates clinical elevation/relevance.

    Handles three value types:
    1. Qualitative strings: "POSITIVE", "HIGH", "HET", "ELEVATED" → True
                            "NEGATIVE", "LOW", "NORMAL", "FALSE", "0" → False
    2. Numeric (int/float): evaluated against NUMERIC_BIOMARKER_THRESHOLDS
                            Unknown numeric → True (conservative)
    3. Boolean: True/False directly

    This replaces the v2 bug where numeric values were cast to string and
    compared against a qualitative exclusion list, causing HbA1c=8.2 to
    silently pass the gate but then fail the map lookup.
    """
    # Boolean
    if isinstance(value, bool):
        return value

    # Numeric — evaluate against clinical threshold
    if isinstance(value, (int, float)):
        threshold_info = NUMERIC_BIOMARKER_THRESHOLDS.get(key_upper)
        if threshold_info is None:
            # Unknown numeric biomarker — assume relevant if non-zero
            return float(value) != 0.0
        threshold, direction = threshold_info
        if direction == "above":
            return float(value) > threshold
        else:  # "below"
            return float(value) < threshold

    # Qualitative string
    if isinstance(value, str):
        val_upper = value.upper().strip()
        # Exclusion list — clearly non-elevated
        if val_upper in (
            "NEGATIVE", "NEG", "LOW", "NORMAL", "FALSE", "0",
            "ABSENT", "WT", "WILDTYPE", "WILD_TYPE", "WILD TYPE",
            "NOT DETECTED", "UNDETECTED", "NONE",
        ):
            return False
        # Inclusion list — clearly elevated/relevant
        if val_upper in (
            "POSITIVE", "POS", "HIGH", "ELEVATED", "ABNORMAL",
            "HET", "HETEROZYGOUS", "HOM", "HOMOZYGOUS",
            "MUTANT", "MUT", "MUTATION", "VARIANT",
            "TRUE", "YES", "PRESENT", "DETECTED", "AMPLIFIED",
            "HIGH_RISK", "INTERMEDIATE", "BORDERLINE",
        ):
            return True
        # Unknown string — assume relevant (conservative)
        return True

    # Fallback for unexpected types
    return True


def _clinical_phase_ceiling(
    rct_count: int,
    obs_count: int,
    invivo_count: int,
    invitro_count: int,
    sample_size: int,
    is_fda_approved: bool = False,
) -> float:
    """
    Hard ceiling on overall_confidence based on the highest evidence tier present.

    is_fda_approved=True unlocks the ceiling to 1.00 regardless of study counts.
    This handles FDA-approved drugs where our database may have incomplete study counts.

    For non-FDA compounds, the ceiling is determined by sample size within the RCT tier.
    """
    if is_fda_approved:
        return 1.00   # FDA approval is the highest evidence tier — no ceiling
    if rct_count >= 1 and sample_size >= 1000:
        return 1.00   # Phase III territory — large multi-site RCT
    elif rct_count >= 1 and sample_size >= 300:
        return 0.75   # Phase II territory — controlled trial
    elif rct_count >= 1 and sample_size >= 100:
        return 0.60   # Phase I / small RCT territory
    elif rct_count >= 1:
        return 0.50   # Pilot RCT (n<100) — supplement / exploratory territory
    elif obs_count >= 1:
        return 0.40   # Observational only — epidemiological territory
    elif invivo_count >= 1:
        return 0.25   # Animal model only
    else:
        return 0.15   # In vitro only — preclinical territory


class ConfidenceScorer:
    """
    Deterministic confidence scorer for Research Intelligence findings.

    All inputs are optional / gracefully defaulted so the scorer never crashes
    even when the LLM fails to extract study design or sample size.

    Key invariants (v3):
    - rct_component scales with RCT count (0.20/RCT, max 0.60) — rewards Phase III
    - study_score hard-capped at 0.60 — prevents in vitro inflation
    - clinical_phase_ceiling hard-caps overall score by evidence tier
    - is_fda_approved unlocks ceiling to 1.00 + adds 0.15 SOC bonus
    - check_biomarker_match handles numeric values with clinical thresholds
    - biomarker map keys are UPPERCASE — no more silent lookup failures
    """

    # Study design keyword patterns (case-insensitive)
    _RCT_PATTERNS = [
        r"\brct\b", r"randomized controlled", r"randomised controlled",
        r"double.blind", r"placebo.controlled", r"phase [23] trial",
        r"clinical trial", r"randomized trial",
    ]
    _OBS_PATTERNS = [
        r"cohort study", r"case.control", r"observational", r"prospective study",
        r"retrospective study", r"epidemiolog", r"population.based",
    ]
    _INVIVO_PATTERNS = [
        r"mouse model", r"rat model", r"xenograft", r"animal model",
        r"in vivo", r"murine", r"tumor model",
    ]
    _INVITRO_PATTERNS = [
        r"in vitro", r"cell line", r"cell culture", r"ic50", r"ki\b",
        r"proliferation assay", r"apoptosis assay",
    ]

    def score(
        self,
        rct_count: int = 0,
        obs_count: int = 0,
        invivo_count: int = 0,
        invitro_count: int = 0,
        sample_size: int = 0,
        biomarker_match: bool = False,
        mechanism_specificity: float = 0.0,
        is_fda_approved: bool = False,
    ) -> Dict[str, Any]:
        """
        Compute deterministic confidence score with clinical-phase ceiling.

        Three layers of protection against inflation:
        1. Per-type sub-caps on study components
        2. study_score hard cap at 0.60
        3. clinical_phase_ceiling based on sample size + FDA status

        Args:
            rct_count:             Number of RCTs found
            obs_count:             Number of observational studies
            invivo_count:          Number of in vivo (animal) studies
            invitro_count:         Number of in vitro studies
            sample_size:           Total patient/sample count across studies
            biomarker_match:       True if compound mechanisms match patient biomarkers
            mechanism_specificity: 0.0–1.0 — how disease-specific the mechanisms are
            is_fda_approved:       True for FDA-approved SOC drugs (unlocks ceiling + SOC bonus)

        Returns:
            {
                "overall_confidence": float,
                "evidence_tier": str,
                "clinical_phase_ceiling": float,
                "breakdown": {
                    "study_score": float,
                    "size_score": float,
                    "biomarker_score": float,
                    "specificity_score": float,
                    "soc_bonus": float,
                    "formula": str,
                    "rct_component": float,
                    "obs_component": float,
                    "invivo_component": float,
                    "invitro_component": float,
                    "rct_count": int,
                    "obs_count": int,
                    "invivo_count": int,
                    "invitro_count": int,
                    "sample_size": int,
                    "biomarker_match": bool,
                    "mechanism_specificity": float,
                    "is_fda_approved": bool,
                }
            }
        """
        # Clamp inputs defensively — never crash on None or bad types
        rct_count             = max(0, int(rct_count or 0))
        obs_count             = max(0, int(obs_count or 0))
        invivo_count          = max(0, int(invivo_count or 0))
        invitro_count         = max(0, int(invitro_count or 0))
        sample_size           = max(0, int(sample_size or 0))
        mechanism_specificity = max(0.0, min(1.0, float(mechanism_specificity or 0.0)))
        is_fda_approved       = bool(is_fda_approved)

        # ── Study components ──────────────────────────────────────────────────
        # rct_component: 0.20 per RCT, max 0.60 (3 RCTs)
        # v2 was min(rct_count * 0.40, 0.40) — flat cap at 1 RCT, suppressed Phase III
        # v3: 1 RCT=0.20, 2 RCTs=0.40, 3+ RCTs=0.60 — correctly rewards multi-RCT evidence
        rct_component     = min(rct_count     * 0.20, 0.60)
        obs_component     = min(obs_count     * 0.08, 0.12)
        invivo_component  = min(invivo_count  * 0.04, 0.06)
        invitro_component = min(invitro_count * 0.01, 0.04)

        # HARD CAP at 0.60 — prevents in vitro stacking
        study_score = min(
            rct_component + obs_component + invivo_component + invitro_component,
            0.60,
        )

        # ── Sample size score (log-scaled, max 0.10) ──────────────────────────
        # Reference: log10(50_000) ≈ 4.70 (large Phase III trial)
        # n=40→0.034  n=120→0.044  n=1000→0.064  n=5000→0.079
        if sample_size > 0:
            size_score = min(log10(sample_size) / log10(50_000), 1.0) * 0.10
        else:
            size_score = 0.0

        # ── Biomarker match bonus (0.10) — gated on minimum human evidence ────
        # Gate: study_score >= 0.20 requires at least 1 RCT (0.20) or 2+ obs (0.16)
        # Prevents "in vitro only + HRD+" from receiving the biomarker bonus
        if biomarker_match and study_score >= 0.20:
            biomarker_score = 0.10
        else:
            biomarker_score = 0.0

        # ── Mechanism specificity (max 0.08) ──────────────────────────────────
        specificity_score = min(mechanism_specificity, 1.0) * 0.08

        # ── FDA-approved SOC bonus (0.15) ─────────────────────────────────────
        # Rewards validated clinical evidence. FDA approval is the highest evidence
        # tier — a drug that has passed Phase III + FDA review deserves a score
        # that reflects that, independent of what our study count database contains.
        soc_bonus = 0.15 if is_fda_approved else 0.0

        # ── Clinical-phase ceiling ────────────────────────────────────────────
        ceiling = _clinical_phase_ceiling(
            rct_count, obs_count, invivo_count, invitro_count, sample_size, is_fda_approved
        )

        raw = study_score + size_score + biomarker_score + specificity_score + soc_bonus
        overall = min(raw, ceiling)
        overall = max(0.0, overall)  # defensive floor

        # ── Evidence tier ─────────────────────────────────────────────────────
        if overall >= TIER_STRONG:
            tier = "STRONG"
        elif overall >= TIER_MODERATE:
            tier = "MODERATE"
        elif overall >= TIER_WEAK:
            tier = "WEAK"
        else:
            tier = "INSUFFICIENT"

        formula_str = (
            f"rct({rct_component:.3f}) + obs({obs_component:.3f}) + "
            f"invivo({invivo_component:.3f}) + invitro({invitro_component:.3f}) "
            f"→ study({study_score:.3f}, cap=0.60) + "
            f"size({size_score:.3f}) + biomarker({biomarker_score:.3f}) + "
            f"spec({specificity_score:.3f}) + soc({soc_bonus:.3f}) "
            f"→ raw({raw:.3f}) → ceiling({ceiling:.2f}) → overall({overall:.4f})"
        )

        return {
            "overall_confidence":     round(overall, 4),
            "evidence_tier":          tier,
            "clinical_phase_ceiling": ceiling,
            "breakdown": {
                "study_score":           round(study_score, 4),
                "size_score":            round(size_score, 4),
                "biomarker_score":       round(biomarker_score, 4),
                "specificity_score":     round(specificity_score, 4),
                "soc_bonus":             round(soc_bonus, 4),
                "formula":               formula_str,
                "rct_component":         round(rct_component, 4),
                "obs_component":         round(obs_component, 4),
                "invivo_component":      round(invivo_component, 4),
                "invitro_component":     round(invitro_component, 4),
                "rct_count":             rct_count,
                "obs_count":             obs_count,
                "invivo_count":          invivo_count,
                "invitro_count":         invitro_count,
                "sample_size":           sample_size,
                "biomarker_match":       biomarker_match,
                "mechanism_specificity": round(mechanism_specificity, 4),
                "is_fda_approved":       is_fda_approved,
            },
        }

    # ------------------------------------------------------------------
    # Study-design extraction from paper metadata
    # ------------------------------------------------------------------

    def extract_study_counts(self, papers: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Parse study design from a list of paper dicts.

        Each paper may have: title, abstract, publication_types, study_design (str).
        Returns counts per design category.
        """
        counts = {"rct_count": 0, "obs_count": 0, "invivo_count": 0, "invitro_count": 0}

        for paper in papers:
            text = " ".join([
                str(paper.get("title", "")),
                str(paper.get("abstract", "")),
                str(paper.get("study_design", "")),
                " ".join(paper.get("publication_types", [])),
            ]).lower()

            if self._matches_any(text, self._RCT_PATTERNS):
                counts["rct_count"] += 1
            elif self._matches_any(text, self._OBS_PATTERNS):
                counts["obs_count"] += 1
            elif self._matches_any(text, self._INVIVO_PATTERNS):
                counts["invivo_count"] += 1
            elif self._matches_any(text, self._INVITRO_PATTERNS):
                counts["invitro_count"] += 1
            else:
                # Default unclassified to in vitro (most conservative)
                counts["invitro_count"] += 1

        return counts

    def extract_sample_size(self, papers: List[Dict[str, Any]]) -> int:
        """
        Extract total sample size from paper metadata.
        Sums sample_size fields; falls back to regex on abstract.
        Returns 0 if nothing found (graceful).
        """
        total = 0
        for paper in papers:
            # Direct field
            ss = paper.get("sample_size") or paper.get("n") or paper.get("participants")
            if ss:
                try:
                    total += int(ss)
                    continue
                except (ValueError, TypeError):
                    pass

            # Regex fallback on abstract
            abstract = str(paper.get("abstract", ""))
            matches = re.findall(
                r"(?:n\s*=\s*|enrolled\s+|included\s+|participants\s*[=:]\s*)(\d[\d,]*)",
                abstract, re.IGNORECASE
            )
            for m in matches:
                try:
                    total += int(m.replace(",", ""))
                    break  # one per paper
                except ValueError:
                    pass

        return total

    def score_mechanism_specificity(
        self,
        mechanisms: List[Dict[str, Any]],
        disease: str,
        biomarkers: Dict[str, Any],
    ) -> float:
        """
        Score how disease/biomarker-specific the extracted mechanisms are.

        Returns 0.0–1.0.
        Higher = mechanisms are directly relevant to this disease + biomarker profile.
        """
        if not mechanisms:
            return 0.0

        disease_lower = disease.lower()
        biomarker_keys = {k.lower() for k in biomarkers.keys()}

        # Disease-specific pathway keywords
        disease_pathway_map: Dict[str, List[str]] = {
            "ovarian": ["brca", "hrd", "parp", "nrf2", "hdac", "platinum", "vdr", "dna repair"],
            "breast":  ["her2", "er", "pr", "brca", "pi3k", "cdk4", "aromatase"],
            "colorectal": ["mss", "msi", "kras", "braf", "vegf", "egfr", "wnt"],
            "diabetes": ["ampk", "mtor", "glut", "insulin", "hba1c", "glucose", "pi3k"],
            "rheumatoid": ["nf-kb", "tnf", "il-6", "cox-2", "jak", "stat3"],
            "parkinson": ["dopamine", "nac", "ros", "mitochondria", "alpha-synuclein", "nrf2"],
            "cardiovascular": ["coq10", "statins", "ldl", "oxidative", "mitochondria"],
            "aging": ["nad", "nmn", "sirt1", "mtor", "ampk", "telomere"],
        }

        # Find matching disease keywords
        relevant_keywords: List[str] = []
        for disease_key, keywords in disease_pathway_map.items():
            if disease_key in disease_lower:
                relevant_keywords.extend(keywords)

        # Add biomarker-derived keywords (lowercase for matching)
        biomarker_keyword_map = {
            "hrd":    ["brca", "parp", "dna repair", "homologous recombination", "nrf2"],
            "brca2":  ["brca", "dna repair", "nrf2", "hdac"],
            "brca1":  ["brca", "dna repair", "nrf2"],
            "hba1c":  ["glucose", "insulin", "ampk", "glut"],
            "tmb":    ["immune", "pd-l1", "msi", "checkpoint"],
            "crp":    ["inflammation", "nf-kb", "cox-2", "il-6"],
        }
        for bk in biomarker_keys:
            for bk_key, kws in biomarker_keyword_map.items():
                if bk_key in bk:
                    relevant_keywords.extend(kws)

        if not relevant_keywords:
            return 0.2  # Unknown disease — small non-zero default

        # Score each mechanism
        scores = []
        for mech in mechanisms:
            mech_text = " ".join([
                str(mech.get("mechanism", "")),
                str(mech.get("description", "")),
                str(mech.get("target", "")),
            ]).lower()

            hits = sum(1 for kw in relevant_keywords if kw in mech_text)
            mech_score = min(hits / max(len(relevant_keywords) * 0.3, 1), 1.0)
            scores.append(mech_score)

        return round(sum(scores) / len(scores), 4) if scores else 0.0

    def check_biomarker_match(
        self,
        mechanisms: List[Dict[str, Any]],
        biomarkers: Dict[str, Any],
    ) -> bool:
        """
        Return True if any mechanism is directly relevant to the patient's biomarkers.

        v3 fixes:
        1. Biomarker map keys are UPPERCASE — no more silent lookup failures
           (v2 bug: map had "HbA1c" but lookup used .upper() → "HBAIC" → no match)
        2. Numeric values evaluated against NUMERIC_BIOMARKER_THRESHOLDS
           (v2 bug: HbA1c=8.2 was cast to "8.2", not in exclusion list, but then
            failed map lookup → biomarker bonus silently lost)
        3. Qualitative strings handled with explicit inclusion/exclusion lists
        """
        if not mechanisms or not biomarkers:
            return False

        for biomarker_key, biomarker_val in biomarkers.items():
            # Normalize key to UPPERCASE for consistent map lookup
            key_upper = (
                biomarker_key.upper()
                .replace("-", "_")
                .replace(" ", "_")
            )

            # Check if this biomarker is clinically elevated/relevant
            if not _is_biomarker_elevated(key_upper, biomarker_val):
                continue

            # Get relevant mechanisms for this biomarker (UPPERCASE key)
            relevant_mechs = BIOMARKER_MECHANISM_MAP.get(key_upper, [])
            if not relevant_mechs:
                continue

            # Check if any mechanism matches
            for mech in mechanisms:
                mech_text = " ".join([
                    str(mech.get("mechanism", "")),
                    str(mech.get("description", "")),
                ]).lower()
                if any(kw in mech_text for kw in relevant_mechs):
                    return True

        return False

    # ------------------------------------------------------------------
    # Convenience: score from full paper list + mechanisms + context
    # ------------------------------------------------------------------

    def score_from_evidence(
        self,
        papers: List[Dict[str, Any]],
        mechanisms: List[Dict[str, Any]],
        disease: str,
        biomarkers: Dict[str, Any],
        is_fda_approved: bool = False,
    ) -> Dict[str, Any]:
        """
        One-shot scoring from raw paper list + mechanisms + patient context.
        Gracefully handles empty inputs at every step.
        """
        try:
            study_counts = self.extract_study_counts(papers)
        except Exception as e:
            logger.warning("extract_study_counts failed: %s", e)
            study_counts = {"rct_count": 0, "obs_count": 0, "invivo_count": 0, "invitro_count": 0}

        try:
            sample_size = self.extract_sample_size(papers)
        except Exception as e:
            logger.warning("extract_sample_size failed: %s", e)
            sample_size = 0

        try:
            biomarker_match = self.check_biomarker_match(mechanisms, biomarkers)
        except Exception as e:
            logger.warning("check_biomarker_match failed: %s", e)
            biomarker_match = False

        try:
            specificity = self.score_mechanism_specificity(mechanisms, disease, biomarkers)
        except Exception as e:
            logger.warning("score_mechanism_specificity failed: %s", e)
            specificity = 0.0

        return self.score(
            **study_counts,
            sample_size=sample_size,
            biomarker_match=biomarker_match,
            mechanism_specificity=specificity,
            is_fda_approved=is_fda_approved,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _matches_any(text: str, patterns: List[str]) -> bool:
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)
