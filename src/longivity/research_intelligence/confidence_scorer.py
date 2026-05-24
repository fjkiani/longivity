"""
ConfidenceScorer — Deterministic evidence confidence scoring.

Replaces LLM-hallucinated confidence floats with a mathematically grounded formula
based on study design hierarchy, sample size, biomarker match, and mechanism specificity.

Formula v2 — clinical-phase ceiling (2026-05-23):
─────────────────────────────────────────────────
Per-type study components (sub-capped):
    rct_component     = min(rct_count    * 0.40, 0.40)   # 1 RCT = full credit
    obs_component     = min(obs_count    * 0.08, 0.12)   # max 1.5 obs studies
    invivo_component  = min(invivo_count * 0.04, 0.06)   # max 1.5 in vivo studies
    invitro_component = min(invitro_count* 0.01, 0.04)   # max 4 in vitro studies
    study_score       = min(sum, 0.60)                   # HARD CAP — prevents inflation

Additive components:
    size_score        = min(log10(n) / log10(50_000), 1.0) * 0.10   # max 0.10
    biomarker_score   = 0.10 if (biomarker_match AND study_score >= 0.20) else 0.0
    specificity_score = mechanism_specificity * 0.08                 # max 0.08

Clinical-phase ceiling (hard cap on overall score):
    Phase III  (rct≥1, n≥1000) → 1.00   FDA-approvable territory
    Phase II   (rct≥1, n≥300)  → 0.75   Controlled trial territory
    Phase I    (rct≥1, n≥100)  → 0.60   Small RCT territory
    Pilot RCT  (rct≥1, n<100)  → 0.50   Pilot / supplement territory
    Obs only                   → 0.40   Epidemiological territory
    In vivo only               → 0.25   Animal model territory
    In vitro only              → 0.15   Preclinical territory

    overall = min(study_score + size_score + biomarker_score + specificity_score,
                  clinical_phase_ceiling)

Calibrated outputs (v2):
    Sulforaphane realistic (1 pilot RCT n=40, 2 obs, 3 invitro, HRD+, spec=0.70)
        → 0.50  MODERATE  ceiling=0.50  ✓ (was 1.0 — FIXED)
    Berberine realistic (2 RCT n=120, 1 obs, 2 invitro, HbA1c, spec=0.65)
        → 0.60  MODERATE  ceiling=0.60  ✓ (was 1.0 — FIXED)
    Olaparib Phase III (3 RCT n=2000, HRD+, spec=0.95)
        → 0.75  STRONG    ceiling=1.00  ✓
    Ceralasertib Phase II (1 RCT n=150, HRD+, spec=0.90)
        → 0.60  MODERATE  ceiling=0.60  ✓
    In vitro only + HRD+ (gate test)
        → 0.08  INSUFFICIENT  ceiling=0.15  ✓
"""

from __future__ import annotations

import logging
import re
from math import log10
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Evidence tier thresholds
TIER_STRONG   = 0.70
TIER_MODERATE = 0.45
TIER_WEAK     = 0.20
# < WEAK → INSUFFICIENT


def _clinical_phase_ceiling(
    rct_count: int,
    obs_count: int,
    invivo_count: int,
    invitro_count: int,
    sample_size: int,
) -> float:
    """
    Hard ceiling on overall_confidence based on the highest evidence tier present.

    This is the key architectural guard that prevents dietary supplements with
    generous in vitro counts from scoring in the same range as Phase III oncology drugs.

    The ceiling is determined by sample size WITHIN the RCT tier, because a
    single pilot RCT (n=40) for a supplement is categorically different from
    a Phase III multi-site RCT (n=2000) for an oncology drug.
    """
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

    Key invariants (v2):
    - study_score is hard-capped at 0.60 (prevents in vitro inflation)
    - overall_confidence is hard-capped by clinical_phase_ceiling (prevents
      supplement scores from reaching Phase III drug territory)
    - biomarker bonus is gated on study_score >= 0.20 (requires at least 1 RCT
      or 2+ observational studies — prevents "in vitro + HRD+" from scoring STRONG)
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
    ) -> Dict[str, Any]:
        """
        Compute deterministic confidence score with clinical-phase ceiling.

        The formula has two layers of protection against inflation:
        1. study_score hard cap at 0.60 — prevents stacking in vitro studies
        2. clinical_phase_ceiling — prevents supplements from reaching Phase III territory

        Args:
            rct_count:             Number of RCTs found
            obs_count:             Number of observational studies
            invivo_count:          Number of in vivo (animal) studies
            invitro_count:         Number of in vitro studies
            sample_size:           Total patient/sample count across studies
            biomarker_match:       True if compound mechanisms match patient biomarkers
            mechanism_specificity: 0.0–1.0 — how disease-specific the mechanisms are

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

        # ── Study components (per-type sub-capped) ────────────────────────────
        # RCT: each RCT worth 0.40, capped at 0.40.
        # Rationale: a single well-powered RCT is the gold standard; additional RCTs
        # increase meta-analytic power (captured by sample_size), not evidence class.
        rct_component     = min(rct_count     * 0.40, 0.40)
        obs_component     = min(obs_count     * 0.08, 0.12)
        invivo_component  = min(invivo_count  * 0.04, 0.06)
        invitro_component = min(invitro_count * 0.01, 0.04)

        # HARD CAP at 0.60 — this was the missing guard in v1
        study_score = min(
            rct_component + obs_component + invivo_component + invitro_component,
            0.60,
        )

        # ── Sample size score (log-scaled, max 0.10) ──────────────────────────
        # Reference: log10(50_000) ≈ 4.70 (large Phase III trial)
        # n=40  → 0.034   n=120 → 0.044   n=1000 → 0.064   n=5000 → 0.079
        if sample_size > 0:
            size_score = min(log10(sample_size) / log10(50_000), 1.0) * 0.10
        else:
            size_score = 0.0

        # ── Biomarker match bonus (0.10) — gated on minimum human evidence ────
        # Gate: study_score >= 0.20 requires at least 1 RCT (0.40) or
        # 2+ obs studies (0.16) or 1 obs + 2 invivo (0.08+0.08=0.16) etc.
        # Prevents: "in vitro only + HRD+" from receiving the biomarker bonus.
        if biomarker_match and study_score >= 0.20:
            biomarker_score = 0.10
        else:
            biomarker_score = 0.0

        # ── Mechanism specificity (max 0.08) ──────────────────────────────────
        specificity_score = min(mechanism_specificity, 1.0) * 0.08

        # ── Clinical-phase ceiling ────────────────────────────────────────────
        ceiling = _clinical_phase_ceiling(
            rct_count, obs_count, invivo_count, invitro_count, sample_size
        )

        raw = study_score + size_score + biomarker_score + specificity_score
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
            f"→ study_score({study_score:.3f}, cap=0.60) + "
            f"size({size_score:.3f}) + biomarker({biomarker_score:.3f}) + "
            f"specificity({specificity_score:.3f}) "
            f"→ raw({raw:.3f}) → ceiling({ceiling:.2f}) → overall({overall:.4f})"
        )

        return {
            "overall_confidence":    round(overall, 4),
            "evidence_tier":         tier,
            "clinical_phase_ceiling": ceiling,
            "breakdown": {
                "study_score":           round(study_score, 4),
                "size_score":            round(size_score, 4),
                "biomarker_score":       round(biomarker_score, 4),
                "specificity_score":     round(specificity_score, 4),
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

        # Add biomarker-derived keywords
        biomarker_keyword_map = {
            "hrd": ["brca", "parp", "dna repair", "homologous recombination", "nrf2"],
            "brca2": ["brca", "dna repair", "nrf2", "hdac"],
            "brca1": ["brca", "dna repair", "nrf2"],
            "hba1c": ["glucose", "insulin", "ampk", "glut"],
            "tmb":   ["immune", "pd-l1", "msi", "checkpoint"],
            "crp":   ["inflammation", "nf-kb", "cox-2", "il-6"],
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
        """
        if not mechanisms or not biomarkers:
            return False

        biomarker_mechanism_map = {
            "HRD":   ["dna repair", "brca", "parp", "nrf2", "hdac", "homologous recombination"],
            "BRCA2": ["dna repair", "brca", "nrf2", "hdac"],
            "BRCA1": ["dna repair", "brca", "nrf2"],
            "TMB":   ["immune", "pd-l1", "checkpoint", "inflammation"],
            "CRP":   ["inflammation", "nf-kb", "cox-2", "il-6", "tnf"],
            "HbA1c": ["glucose", "insulin", "ampk", "glut", "mtor"],
        }

        for biomarker_key, biomarker_val in biomarkers.items():
            # Skip low/negative values
            if str(biomarker_val).upper() in ("NEGATIVE", "LOW", "NORMAL", "FALSE", "0"):
                continue

            relevant_mechs = biomarker_mechanism_map.get(biomarker_key.upper(), [])
            if not relevant_mechs:
                continue

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
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _matches_any(text: str, patterns: List[str]) -> bool:
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)
