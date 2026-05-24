"""
LongevityEvidenceService — wraps the research_intelligence orchestrator
for longevity-specific queries.

Provides 4 high-level methods:
  - get_compound_evidence(compound_id, hallmark) → PubMed evidence for compound → hallmark
  - get_hallmark_narrative(hallmark, biomarkers) → clinical narrative with citations
  - get_disease_risk_evidence(disease, variants) → genetic risk → disease evidence
  - get_cancer_risk_summary(dna_repair_score, biomarkers) → cancer risk synthesis

All results are cached in memory (TTL 1h) to avoid hammering PubMed.
Falls back gracefully if PubMed/LLM unavailable.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# Simple in-memory cache: key → (result, expires_at)
_CACHE: dict[str, tuple[Any, float]] = {}
_CACHE_TTL = 3600  # 1 hour


def _cache_key(*args) -> str:
    raw = json.dumps(args, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _cache_get(key: str) -> Any | None:
    if key in _CACHE:
        result, expires_at = _CACHE[key]
        if time.time() < expires_at:
            return result
        del _CACHE[key]
    return None


def _cache_set(key: str, value: Any) -> None:
    _CACHE[key] = (value, time.time() + _CACHE_TTL)


class LongevityEvidenceService:
    """
    Wraps research_intelligence orchestrator for longevity-specific queries.
    Instantiate once and reuse (singleton pattern recommended).
    """

    def __init__(self):
        self._orchestrator = None
        self._init_lock = asyncio.Lock()

    async def _get_orchestrator(self):
        """Lazy-initialize the orchestrator (imports are heavy)."""
        if self._orchestrator is not None:
            return self._orchestrator
        async with self._init_lock:
            if self._orchestrator is not None:
                return self._orchestrator
            try:
                from longivity.research_intelligence.orchestrator import ResearchOrchestrator
                self._orchestrator = ResearchOrchestrator()
                logger.info("ResearchOrchestrator initialized")
            except Exception as e:
                logger.warning(f"ResearchOrchestrator unavailable: {e}")
                self._orchestrator = None
        return self._orchestrator

    # ── Public API ────────────────────────────────────────────────────────────

    async def get_compound_evidence(
        self,
        compound_id: str,
        hallmark: str,
        patient_context: dict | None = None,
    ) -> dict:
        """
        Get PubMed evidence for a compound → hallmark link.

        Args:
            compound_id: e.g. "metformin", "omega_3", "berberine"
            hallmark: e.g. "nutrient_sensing", "altered_intercellular_communication"
            patient_context: optional dict with age, sex, condition for persona framing

        Returns:
            {
                "compound": str,
                "hallmark": str,
                "evidence_tier": "TIER_1_STRONG" | "TIER_2_MODERATE" | "TIER_3_PRELIMINARY" | "INSUFFICIENT",
                "summary": str,
                "papers": [{"pmid": str, "title": str, "year": int, "study_type": str}],
                "confidence": float,
                "cached": bool,
            }
        """
        key = _cache_key("compound_evidence", compound_id, hallmark)
        cached = _cache_get(key)
        if cached:
            return {**cached, "cached": True}

        query = (
            f"{compound_id} {hallmark.replace('_', ' ')} aging longevity "
            f"clinical trial randomized controlled"
        )
        result = await self._run_research(query, context={
            "type": "compound_evidence",
            "compound": compound_id,
            "hallmark": hallmark,
            "patient_context": patient_context or {},
        })

        output = {
            "compound": compound_id,
            "hallmark": hallmark,
            "evidence_tier": result.get("evidence_tier", "INSUFFICIENT"),
            "summary": result.get("synthesis", result.get("summary", "")),
            "papers": result.get("papers", [])[:5],
            "confidence": result.get("confidence", 0.0),
            "cached": False,
        }
        _cache_set(key, output)
        return output

    async def get_hallmark_narrative(
        self,
        hallmark: str,
        biomarkers: dict,
        patient_age: int | None = None,
        patient_sex: str | None = None,
    ) -> dict:
        """
        Get a clinical narrative for an active hallmark with biomarker context.

        Args:
            hallmark: e.g. "nutrient_sensing"
            biomarkers: dict of marker_key → value for abnormal markers
            patient_age: optional
            patient_sex: optional

        Returns:
            {
                "hallmark": str,
                "headline": str,          # 1-sentence plain English
                "narrative": str,         # 2-3 sentence clinical explanation
                "key_biomarkers": list,   # which biomarkers drove this
                "citations": list,        # PMIDs
                "evidence_tier": str,
            }
        """
        key = _cache_key("hallmark_narrative", hallmark, sorted(biomarkers.keys()))
        cached = _cache_get(key)
        if cached:
            return {**cached, "cached": True}

        # Build a focused query
        abnormal_markers = [f"{k}={v}" for k, v in biomarkers.items()]
        query = (
            f"{hallmark.replace('_', ' ')} hallmark aging "
            f"biomarkers {' '.join(list(biomarkers.keys())[:4])} "
            f"clinical significance intervention"
        )
        result = await self._run_research(query, context={
            "type": "hallmark_narrative",
            "hallmark": hallmark,
            "biomarkers": biomarkers,
            "patient_age": patient_age,
            "patient_sex": patient_sex,
        })

        output = {
            "hallmark": hallmark,
            "headline": result.get("headline", f"Elevated {hallmark.replace('_', ' ')} activity detected"),
            "narrative": result.get("synthesis", result.get("narrative", "")),
            "key_biomarkers": list(biomarkers.keys()),
            "citations": [p.get("pmid") for p in result.get("papers", [])[:3] if p.get("pmid")],
            "evidence_tier": result.get("evidence_tier", "TIER_2_MODERATE"),
            "cached": False,
        }
        _cache_set(key, output)
        return output

    async def get_disease_risk_evidence(
        self,
        disease: str,
        variants: dict,
        patient_age: int | None = None,
    ) -> dict:
        """
        Get evidence for genetic risk variants → disease.

        Args:
            disease: e.g. "alzheimers", "breast_cancer", "colorectal_cancer"
            variants: dict of rsid/gene → genotype/effect
            patient_age: optional

        Returns:
            {
                "disease": str,
                "risk_summary": str,
                "variants_explained": list,
                "prevention_evidence": list,
                "citations": list,
                "evidence_tier": str,
            }
        """
        key = _cache_key("disease_risk", disease, sorted(variants.keys()))
        cached = _cache_get(key)
        if cached:
            return {**cached, "cached": True}

        gene_list = " ".join(variants.keys())
        query = (
            f"{disease.replace('_', ' ')} genetic risk {gene_list} "
            f"prevention intervention clinical evidence"
        )
        result = await self._run_research(query, context={
            "type": "disease_risk",
            "disease": disease,
            "variants": variants,
            "patient_age": patient_age,
        })

        output = {
            "disease": disease,
            "risk_summary": result.get("synthesis", result.get("summary", "")),
            "variants_explained": [
                {"gene": k, "effect": v} for k, v in variants.items()
            ],
            "prevention_evidence": result.get("interventions", []),
            "citations": [p.get("pmid") for p in result.get("papers", [])[:5] if p.get("pmid")],
            "evidence_tier": result.get("evidence_tier", "TIER_2_MODERATE"),
            "cached": False,
        }
        _cache_set(key, output)
        return output

    async def get_cancer_risk_summary(
        self,
        dna_repair_genes: dict,
        biomarkers: dict,
        patient_age: int | None = None,
        patient_sex: str | None = None,
    ) -> dict:
        """
        Synthesize cancer risk from DNA repair gene panel + inflammatory biomarkers.

        Args:
            dna_repair_genes: dict of gene → variant info (from panel raw_json)
            biomarkers: dict of marker_key → value for cancer-relevant markers
            patient_age: optional
            patient_sex: optional

        Returns:
            {
                "overall_risk_tier": "HIGH" | "MODERATE" | "LOW",
                "genomic_instability_score": float,  # 0-1
                "inflammatory_burden_score": float,  # 0-1
                "synthesis": str,
                "recommended_surveillance": list,
                "citations": list,
                "evidence_tier": str,
            }
        """
        key = _cache_key("cancer_risk", sorted(dna_repair_genes.keys()), sorted(biomarkers.keys()))
        cached = _cache_get(key)
        if cached:
            return {**cached, "cached": True}

        # Score genomic instability
        genomic_score = _score_genomic_instability(dna_repair_genes)
        # Score inflammatory burden
        inflammatory_score = _score_inflammatory_burden(biomarkers)

        gene_list = " ".join(dna_repair_genes.keys())
        query = (
            f"cancer risk DNA repair {gene_list} "
            f"inflammatory biomarkers ferritin IL-6 CRP surveillance prevention"
        )
        result = await self._run_research(query, context={
            "type": "cancer_risk",
            "dna_repair_genes": dna_repair_genes,
            "biomarkers": biomarkers,
            "genomic_instability_score": genomic_score,
            "inflammatory_burden_score": inflammatory_score,
        })

        # Determine overall risk tier
        combined = (genomic_score * 0.6) + (inflammatory_score * 0.4)
        if combined >= 0.6:
            risk_tier = "HIGH"
        elif combined >= 0.35:
            risk_tier = "MODERATE"
        else:
            risk_tier = "LOW"

        output = {
            "overall_risk_tier": risk_tier,
            "genomic_instability_score": round(genomic_score, 3),
            "inflammatory_burden_score": round(inflammatory_score, 3),
            "synthesis": result.get("synthesis", result.get("summary", "")),
            "recommended_surveillance": _get_surveillance_recommendations(dna_repair_genes, patient_sex),
            "citations": [p.get("pmid") for p in result.get("papers", [])[:5] if p.get("pmid")],
            "evidence_tier": result.get("evidence_tier", "TIER_2_MODERATE"),
            "cached": False,
        }
        _cache_set(key, output)
        return output

    # ── Internal ──────────────────────────────────────────────────────────────

    async def _run_research(self, query: str, context: dict) -> dict:
        """Run a research query through the orchestrator, with graceful fallback."""
        orchestrator = await self._get_orchestrator()
        if orchestrator is None:
            return _fallback_response(query, context)

        try:
            result = await asyncio.wait_for(
                orchestrator.research(query=query, context=context),
                timeout=30.0,
            )
            return result if isinstance(result, dict) else {"synthesis": str(result)}
        except asyncio.TimeoutError:
            logger.warning(f"Research query timed out: {query[:80]}")
            return _fallback_response(query, context)
        except Exception as e:
            logger.warning(f"Research query failed: {e}")
            return _fallback_response(query, context)


# ── Scoring helpers ───────────────────────────────────────────────────────────

def _score_genomic_instability(dna_repair_genes: dict) -> float:
    """Score genomic instability 0-1 based on DNA repair gene variants."""
    score = 0.0
    weights = {
        "BRCA1": 0.35, "BRCA2": 0.35,
        "MLH1": 0.30, "MSH2": 0.30, "MSH6": 0.20, "PMS2": 0.20,
        "MUTYH": 0.20, "ATM": 0.25, "CHEK2": 0.20,
    }
    for gene, info in dna_repair_genes.items():
        w = weights.get(gene, 0.15)
        variant = str(info.get("variant", "")).lower()
        if "pathogenic" in variant:
            score += w
        elif "likely_pathogenic" in variant:
            score += w * 0.7
        elif "het" in variant or "CT" in str(info.get("genotype", "")):
            score += w * 0.4
    return min(score, 1.0)


def _score_inflammatory_burden(biomarkers: dict) -> float:
    """Score inflammatory burden 0-1 based on cancer-relevant biomarkers."""
    score = 0.0
    thresholds = {
        "crp": (3.0, 10.0, 0.15),
        "il6": (3.0, 10.0, 0.20),
        "ferritin_inflam": (200, 500, 0.15),
        "rdw": (14.5, 16.0, 0.10),
        "lymphocyte_percent": (20, 15, 0.15),  # inverted — low is bad
        "cea": (3.0, 10.0, 0.15),
        "ca_125": (35, 100, 0.10),
    }
    for marker, (low_thresh, high_thresh, weight) in thresholds.items():
        val = biomarkers.get(marker)
        if val is None:
            continue
        if marker == "lymphocyte_percent":
            # Low lymphocytes = bad
            if val < low_thresh:
                score += weight * min((low_thresh - val) / (low_thresh - high_thresh), 1.0)
        else:
            if val > low_thresh:
                score += weight * min((val - low_thresh) / (high_thresh - low_thresh), 1.0)
    return min(score, 1.0)


def _get_surveillance_recommendations(dna_repair_genes: dict, sex: str | None) -> list[str]:
    """Return surveillance recommendations based on DNA repair gene panel."""
    recs = []
    genes = set(dna_repair_genes.keys())

    if "BRCA1" in genes or "BRCA2" in genes:
        recs.append("Annual breast MRI + mammography (BRCA1/2 carrier protocol)")
        if sex == "female":
            recs.append("Discuss risk-reducing salpingo-oophorectomy with gynecologic oncology")
        recs.append("Pancreatic cancer surveillance if family history present")

    if any(g in genes for g in ["MLH1", "MSH2", "MSH6", "PMS2"]):
        recs.append("Colonoscopy every 1-2 years (Lynch syndrome protocol)")
        recs.append("Annual endometrial sampling if female")
        recs.append("Urinalysis + urine cytology annually")

    if "MUTYH" in genes:
        recs.append("Colonoscopy every 2-3 years (MUTYH-associated polyposis)")

    if "ATM" in genes:
        recs.append("Annual breast MRI (ATM heterozygous carrier)")

    if "CHEK2" in genes:
        recs.append("Annual mammography starting age 40 (CHEK2 carrier)")

    if not recs:
        recs.append("Standard age-appropriate cancer screening")

    return recs


def _fallback_response(query: str, context: dict) -> dict:
    """Return a minimal fallback when the orchestrator is unavailable."""
    return {
        "synthesis": (
            "Evidence synthesis unavailable — PubMed/LLM service not configured. "
            "Set NCBI_USER_EMAIL and OPENROUTER_API_KEY environment variables to enable live literature."
        ),
        "papers": [],
        "evidence_tier": "INSUFFICIENT",
        "confidence": 0.0,
        "fallback": True,
    }


# ── Singleton ─────────────────────────────────────────────────────────────────
_evidence_service: LongevityEvidenceService | None = None


def get_evidence_service() -> LongevityEvidenceService:
    global _evidence_service
    if _evidence_service is None:
        _evidence_service = LongevityEvidenceService()
    return _evidence_service
