"""
ConfidenceScorer — Deterministic evidence confidence scoring.

Replaces LLM-hallucinated confidence floats with a mathematically grounded formula
based on study design hierarchy, sample size, biomarker match, and mechanism specificity.

Formula (per-type sub-caps prevent low-quality evidence inflation):
    rct_component    = min(rct_count   * 0.40, 0.40)   # max 1 RCT fully counted
    obs_component    = min(obs_count   * 0.12, 0.20)   # max ~1.7 obs studies
    invivo_component = min(invivo_count* 0.06, 0.10)   # max ~1.7 in vivo studies
    invitro_component= min(invitro_count*0.02, 0.06)   # max 3 in vitro studies
    study_score      = rct_component + obs_component + invivo_component + invitro_component  (max 0.76, but...)

    size_score       = min(log10(max(sample_size, 1)) / log10(10_000), 1.0) * 0.14
    biomarker_score  = 0.15 if (biomarker_match AND study_score >= 0.12) else 0.0
                       # Gate: biomarker bonus only if there is at least human/animal evidence
    specificity_score= mechanism_specificity * 0.10

    overall = clip(study_score + size_score + biomarker_score + specificity_score, 0, 1)

Calibrated outputs:
    1 RCT, n=250, HRD+, spec=0.7  → ~0.40+0.09+0.15+0.07 = 0.71  STRONG  ✓
    0 RCT, 1 obs, 10 in vitro, HRD+ → ~0.18+0.00+0.15+0.05 = 0.38  WEAK   ✓ (was STRONG — fixed)
    3 RCT, n=600, HbA1c, spec=0.6 → ~0.40+0.11+0.15+0.06 = 0.72  STRONG  ✓
    in vitro only, no biomarker    → ~0.06+0.00+0.00+0.01 = 0.07  INSUFFICIENT ✓
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


class ConfidenceScorer:
    """
    Deterministic confidence scorer for Research Intelligence findings.

    All inputs are optional / gracefully defaulted so the scorer never crashes
    even when the LLM fails to extract study design or sample size.
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
        Compute deterministic confidence score with per-type sub-caps.

        Per-type sub-caps prevent in vitro evidence from inflating scores into
        STRONG tier. Biomarker bonus is gated on minimum human/animal evidence.

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
        rct_count         = max(0, int(rct_count or 0))
        obs_count         = max(0, int(obs_count or 0))
        invivo_count      = max(0, int(invivo_count or 0))
        invitro_count     = max(0, int(invitro_count or 0))
        sample_size       = max(0, int(sample_size or 0))
        mechanism_specificity = max(0.0, min(1.0, float(mechanism_specificity or 0.0)))

        # Per-type sub-capped study components
        # RCT: each RCT worth 0.40, but capped at 0.40 (1 RCT = full credit; 2nd RCT adds nothing)
        # Rationale: a single well-powered RCT is the gold standard; stacking RCTs doesn't
        # change the evidence class, only the meta-analytic power (captured by sample_size).
        rct_component    = min(rct_count    * 0.40, 0.40)
        obs_component    = min(obs_count    * 0.12, 0.20)
        invivo_component = min(invivo_count * 0.06, 0.10)
        invitro_component= min(invitro_count* 0.02, 0.06)

        study_score = rct_component + obs_component + invivo_component + invitro_component

        # Sample size score (log-scaled, max 0.14)
        if sample_size > 0:
            size_score = min(log10(sample_size) / log10(10_000), 1.0) * 0.14
        else:
            size_score = 0.0

        # Biomarker match bonus (0.15) — GATED on minimum human/animal evidence
        # Gate threshold: study_score >= 0.12 means at least 1 obs study or 2 in vivo studies
        # Prevents: "in vitro only + HRD+" from scoring as STRONG
        if biomarker_match and study_score >= 0.12:
            biomarker_score = 0.15
        else:
            biomarker_score = 0.0

        # Mechanism specificity (max 0.10)
        specificity_score = mechanism_specificity * 0.10

        overall = min(1.0, max(0.0,
            study_score + size_score + biomarker_score + specificity_score
        ))

        # Evidence tier
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
            f"invivo({invivo_component:.3f}) + invitro({invitro_component:.3f}) + "
            f"size({size_score:.3f}) + biomarker({biomarker_score:.3f}) + "
            f"specificity({specificity_score:.3f})"
        )

        return {
            "overall_confidence": round(overall, 4),
            "evidence_tier": tier,
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
