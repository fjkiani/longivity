"""
EnhancedEvidenceService — Diffbot + disease-context-aware LLM extraction.

Key upgrades over the original:
1. Disease-context-aware prompt: asks for IC50/Ki data, study design classification,
   sample size, and biomarker-specific relevance per mechanism.
2. LLM-returned confidence is REPLACED by ConfidenceScorer (deterministic formula).
3. Mechanisms returned as full dicts with study_design, ic50_data, biomarker_relevance.
4. Graceful on all failures — never crashes the orchestrator.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

from .llm_provider.llm_abstract import get_llm_provider
from .confidence_scorer import ConfidenceScorer

logger = logging.getLogger(__name__)

LLM_AVAILABLE = True
try:
    _probe = get_llm_provider()
    if not _probe.is_available():
        LLM_AVAILABLE = False
except Exception:
    LLM_AVAILABLE = False

_scorer = ConfidenceScorer()


class EnhancedEvidenceService:
    def __init__(self) -> None:
        self.diffbot_rate_limited = False

    # ------------------------------------------------------------------
    # Diffbot full-text extraction (unchanged)
    # ------------------------------------------------------------------

    async def _extract_full_text_with_diffbot(self, paper_url: str) -> Optional[str]:
        if self.diffbot_rate_limited:
            return None
        token = os.environ.get("DIFFBOT_TOKEN", "").strip()
        if not token:
            return None

        api_url = "https://api.diffbot.com/v3/article"
        params = {
            "token": token,
            "url": paper_url,
            "fields": "title,author,date,siteName,tags,text",
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get(api_url, params=params)
                if r.status_code == 429:
                    self.diffbot_rate_limited = True
                    logger.warning("Diffbot rate limit (429); skipping further Diffbot calls.")
                    return None
                r.raise_for_status()
                js = r.json()
            obj = (js.get("objects") or [None])[0]
            if obj and obj.get("text"):
                return str(obj.get("text"))[:10000]
            return None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                self.diffbot_rate_limited = True
            logger.debug("Diffbot HTTP error for %s: %s", paper_url[:80], e.response.status_code)
            return None
        except Exception as e:
            logger.debug("Diffbot extraction error for %s: %s", paper_url[:80], e)
            return None

    # ------------------------------------------------------------------
    # Simple LLM extraction (legacy — kept for backward compat)
    # ------------------------------------------------------------------

    async def _call_llm_agnostic(
        self,
        compound: str,
        disease: str,
        papers_text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Simple single-call LLM extraction. Used as fallback by synthesis_engine.
        Now includes disease context in prompt and replaces LLM confidence with
        ConfidenceScorer output.
        """
        if not LLM_AVAILABLE:
            logger.warning("LLM not available for evidence extraction")
            return None
        try:
            provider = get_llm_provider()
            if not provider.is_available():
                return None

            pause = float(os.environ.get("RESEARCH_INTEL_LLM_PAUSE_S", "0.2"))
            await asyncio.sleep(pause)

            context = context or {}
            biomarkers = context.get("biomarkers", {})
            treatment_line = context.get("treatment_line", "")
            biomarker_str = ", ".join(
                f"{k}={v}" for k, v in biomarkers.items()
            ) if biomarkers else "none specified"

            system_message = (
                "You are a clinical biomedical research analyst specializing in oncology and precision medicine. "
                "Extract structured, clinically actionable information from research papers."
            )

            prompt = f"""Analyze these research papers about {compound} for {disease}.

Patient context:
- Disease: {disease}
- Biomarkers: {biomarker_str}
- Treatment line: {treatment_line or "not specified"}

Papers:
{papers_text[:8000]}

Extract and return a JSON object with this EXACT structure.
For each mechanism, classify the study design and rate biomarker relevance:

{{
  "mechanisms": [
    {{
      "mechanism": "brief_name (e.g. NRF2 activation)",
      "description": "precise molecular description of how it works",
      "study_design": "RCT|observational|in_vivo|in_vitro",
      "sample_size": 0,
      "ic50_data": {{"value": "2.5 µM", "cell_line": "OVCAR-3", "source": "PMID:XXXXXXXX"}} or null,
      "biomarker_relevance": {{"HRD": "HIGH|MODERATE|LOW|NA", "BRCA2": "HIGH|MODERATE|LOW|NA"}}
    }}
  ],
  "study_counts": {{
    "rct_count": 0,
    "observational_count": 0,
    "invivo_count": 0,
    "invitro_count": 0,
    "total_sample_size": 0
  }},
  "dosage": {{
    "recommended_dose": "extracted dose or empty string",
    "evidence": "quote supporting dose"
  }},
  "safety": {{
    "concerns": ["list of safety concerns or empty"],
    "monitoring": ["what to monitor or empty"]
  }},
  "outcomes": [
    {{"outcome": "survival improvement", "details": "what the papers say", "effect_size": "HR 0.77 or empty"}}
  ],
  "evidence_summary": "2-3 sentence synthesis of the evidence"
}}

Rules:
- study_design: classify each mechanism by the BEST study supporting it
- ic50_data: only include if a specific IC50 or Ki value is mentioned in the papers
- biomarker_relevance: rate relevance to the patient's specific biomarkers ({biomarker_str})
- study_counts: count ALL papers by design type
- Return ONLY valid JSON, no markdown."""

            max_retries = 3
            response_text: Optional[str] = None
            for attempt in range(max_retries):
                try:
                    llm_response = await provider.chat(
                        message=prompt,
                        system_message=system_message,
                        max_tokens=2500,
                        temperature=0.0,
                    )
                    response_text = llm_response.text
                    break
                except Exception as e:
                    error_str = str(e).lower()
                    if (
                        "429" in error_str or "quota" in error_str or "rate limit" in error_str
                    ) and attempt < max_retries - 1:
                        delay = (2 ** attempt) * 2.0
                        logger.warning(
                            "LLM rate limit (attempt %s/%s); retry in %.1fs",
                            attempt + 1, max_retries, delay,
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error("LLM error: %s", e)
                        raise

            if not response_text:
                return None

            parsed = _parse_json_response(response_text)
            if not parsed:
                return None

            # Extract full mechanism dicts (not just names)
            mechanisms = _extract_mechanism_dicts(parsed.get("mechanisms", []))

            # Extract study counts from LLM output
            study_counts_raw = parsed.get("study_counts", {})
            study_counts = {
                "rct_count":    int(study_counts_raw.get("rct_count", 0) or 0),
                "obs_count":    int(study_counts_raw.get("observational_count", 0) or 0),
                "invivo_count": int(study_counts_raw.get("invivo_count", 0) or 0),
                "invitro_count":int(study_counts_raw.get("invitro_count", 0) or 0),
                "sample_size":  int(study_counts_raw.get("total_sample_size", 0) or 0),
            }

            # Deterministic confidence — replace LLM float
            confidence_result = _scorer.score_from_evidence(
                papers=[],  # no paper objects here, use LLM-extracted counts
                mechanisms=mechanisms,
                disease=disease,
                biomarkers=biomarkers,
            )
            # Override with LLM-extracted counts if available
            if any(v > 0 for v in study_counts.values()):
                confidence_result = _scorer.score(
                    **{k: v for k, v in study_counts.items() if k != "sample_size"},
                    sample_size=study_counts["sample_size"],
                    biomarker_match=_scorer.check_biomarker_match(mechanisms, biomarkers),
                    mechanism_specificity=_scorer.score_mechanism_specificity(
                        mechanisms, disease, biomarkers
                    ),
                )

            return {
                "mechanisms": mechanisms[:10],
                "dosage": parsed.get("dosage", {}).get("recommended_dose", "")
                    if isinstance(parsed.get("dosage"), dict) else parsed.get("dosage", ""),
                "safety": parsed.get("safety", {}).get("concerns", [])
                    if isinstance(parsed.get("safety"), dict) else parsed.get("safety", []),
                "outcomes": parsed.get("outcomes", []),
                "evidence_summary": parsed.get("evidence_summary", ""),
                # Deterministic confidence replaces LLM float
                "overall_confidence": confidence_result["overall_confidence"],
                "evidence_tier": confidence_result["evidence_tier"],
                "confidence_breakdown": confidence_result["breakdown"],
            }
        except Exception as e:
            logger.error("LLM extraction error: %s", e)
            return None

    # ------------------------------------------------------------------
    # Comprehensive LLM extraction — disease-context-aware
    # ------------------------------------------------------------------

    async def _call_llm_agnostic_comprehensive(
        self,
        compound: str,
        disease: str,
        papers_text: str,
        articles: Optional[List[Dict[str, Any]]] = None,
        sub_questions: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Comprehensive single-call LLM extraction with disease-context-aware prompt.

        Upgrades over original:
        - Passes disease + biomarker context into prompt
        - Requests IC50/Ki data, study design classification, sample size per mechanism
        - Requests biomarker_relevance per mechanism
        - Replaces LLM-returned confidence with ConfidenceScorer (deterministic)
        - Returns full mechanism dicts (not just name strings)
        """
        if not LLM_AVAILABLE:
            return None
        try:
            provider = get_llm_provider()
            if not provider.is_available():
                return None

            pause = float(os.environ.get("RESEARCH_INTEL_LLM_PAUSE_S", "0.2"))
            await asyncio.sleep(pause)

            context = context or {}
            biomarkers = context.get("biomarkers", {})
            treatment_line = context.get("treatment_line", "")
            biomarker_str = ", ".join(
                f"{k}={v}" for k, v in biomarkers.items()
            ) if biomarkers else "none specified"

            system_message = (
                "You are a clinical biomedical research analyst specializing in oncology and precision medicine. "
                "Extract structured, clinically actionable information from research papers. "
                "Be precise about study designs, sample sizes, and molecular targets. "
                "Never invent data — if IC50 or sample size is not in the papers, use null/0."
            )

            # Build the disease-context-aware prompt
            prompt_parts: List[str] = [
                f"Analyze these research papers about {compound} for {disease}.",
                "",
                "PATIENT CONTEXT (use this to rate biomarker relevance):",
                f"  Disease: {disease}",
                f"  Biomarkers: {biomarker_str}",
                f"  Treatment line: {treatment_line or 'not specified'}",
                "",
                "PAPERS:",
                papers_text[:12000],
                "",
                "Extract and return a JSON object with this EXACT structure:",
            ]

            # Core JSON schema — mechanisms now include study_design, ic50_data, biomarker_relevance
            json_structure: Dict[str, Any] = {
                "mechanisms": [
                    {
                        "mechanism": "NRF2 activation",
                        "description": "precise molecular description",
                        "study_design": "RCT|observational|in_vivo|in_vitro",
                        "sample_size": 250,
                        "ic50_data": {
                            "value": "2.5 µM",
                            "cell_line": "OVCAR-3",
                            "source": "PMID:28765432"
                        },
                        "biomarker_relevance": {
                            k: "HIGH|MODERATE|LOW|NA"
                            for k in (list(biomarkers.keys())[:4] if biomarkers else ["HRD", "BRCA2"])
                        },
                    }
                ],
                "study_counts": {
                    "rct_count": 0,
                    "observational_count": 0,
                    "invivo_count": 0,
                    "invitro_count": 0,
                    "total_sample_size": 0,
                },
                "dosage": {
                    "recommended_dose": "extracted dose or empty string",
                    "evidence": "quote supporting dose",
                },
                "safety": {
                    "concerns": ["list of safety concerns or empty"],
                    "monitoring": ["what to monitor or empty"],
                },
                "outcomes": [
                    {
                        "outcome": "survival improvement",
                        "details": "what the papers say",
                        "effect_size": "HR 0.77 or empty",
                    }
                ],
                "evidence_summary": "2-3 sentence synthesis of the evidence",
            }

            if articles:
                json_structure["article_summaries"] = [
                    {
                        "pmid": "article_pmid",
                        "title": "article_title",
                        "summary": "brief_summary",
                        "study_design": "RCT|observational|in_vivo|in_vitro",
                        "sample_size": 0,
                        "mechanisms": ["mech1"],
                        "dosage": {},
                        "safety": {},
                        "outcomes": [],
                    }
                ]
                prompt_parts.append(
                    "For each article, include it in 'article_summaries' with study_design and sample_size."
                )

            if sub_questions:
                json_structure["sub_question_answers"] = [
                    {
                        "sub_question": "question text",
                        "answer": "direct answer",
                        "confidence": 0.85,
                        "sources": ["pmid1", "pmid2"],
                        "mechanisms": ["mech1"],
                    }
                ]
                prompt_parts.append(
                    f"Answer these sub-questions: {', '.join(sub_questions[:5])}"
                )
                prompt_parts.append("Include answers in 'sub_question_answers'.")

            prompt_parts += [
                "",
                "RULES:",
                "- study_design per mechanism: classify by the BEST study supporting it",
                "- ic50_data: only if a specific IC50/Ki value is in the papers, else null",
                f"- biomarker_relevance: rate each mechanism's relevance to {biomarker_str}",
                "- study_counts: count ALL papers by design type across the full set",
                "- total_sample_size: sum of n= values from human studies only",
                "- Return ONLY valid JSON, no markdown formatting.",
                "",
                json.dumps(json_structure, indent=2),
            ]

            prompt = "\n".join(prompt_parts)

            max_retries = 3
            response_text: Optional[str] = None
            for attempt in range(max_retries):
                try:
                    llm_response = await provider.chat(
                        message=prompt,
                        system_message=system_message,
                        max_tokens=4096,
                        temperature=0.0,
                    )
                    response_text = llm_response.text
                    break
                except Exception as e:
                    error_str = str(e).lower()
                    if (
                        "429" in error_str or "quota" in error_str or "rate limit" in error_str
                    ) and attempt < max_retries - 1:
                        delay = (2 ** attempt) * 2.0
                        logger.warning(
                            "LLM rate limit comprehensive (attempt %s/%s); retry in %.1fs",
                            attempt + 1, max_retries, delay,
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error("LLM error: %s", e)
                        raise

            if not response_text:
                return None

            parsed = _parse_json_response(response_text)
            if not parsed:
                return None

            # Extract full mechanism dicts
            mechanisms = _extract_mechanism_dicts(parsed.get("mechanisms", []))

            # Extract study counts from LLM output
            study_counts_raw = parsed.get("study_counts", {})
            rct_count    = int(study_counts_raw.get("rct_count", 0) or 0)
            obs_count    = int(study_counts_raw.get("observational_count", 0) or 0)
            invivo_count = int(study_counts_raw.get("invivo_count", 0) or 0)
            invitro_count= int(study_counts_raw.get("invitro_count", 0) or 0)
            sample_size  = int(study_counts_raw.get("total_sample_size", 0) or 0)

            # If LLM didn't return study_counts, fall back to paper-list extraction
            if rct_count + obs_count + invivo_count + invitro_count == 0 and articles:
                extracted = _scorer.extract_study_counts(articles)
                rct_count    = extracted["rct_count"]
                obs_count    = extracted["obs_count"]
                invivo_count = extracted["invivo_count"]
                invitro_count= extracted["invitro_count"]
                if sample_size == 0:
                    sample_size = _scorer.extract_sample_size(articles)

            # Deterministic confidence — replaces any LLM-returned float
            biomarker_match = _scorer.check_biomarker_match(mechanisms, biomarkers)
            specificity = _scorer.score_mechanism_specificity(mechanisms, disease, biomarkers)
            confidence_result = _scorer.score(
                rct_count=rct_count,
                obs_count=obs_count,
                invivo_count=invivo_count,
                invitro_count=invitro_count,
                sample_size=sample_size,
                biomarker_match=biomarker_match,
                mechanism_specificity=specificity,
            )

            result: Dict[str, Any] = {
                "mechanisms": mechanisms[:10],
                "dosage": parsed.get("dosage", {}).get("recommended_dose", "")
                    if isinstance(parsed.get("dosage"), dict) else parsed.get("dosage", ""),
                "safety": parsed.get("safety", {}).get("concerns", [])
                    if isinstance(parsed.get("safety"), dict) else parsed.get("safety", []),
                "outcomes": parsed.get("outcomes", []),
                "evidence_summary": parsed.get("evidence_summary", ""),
                # Deterministic confidence — LLM float discarded
                "overall_confidence": confidence_result["overall_confidence"],
                "evidence_tier": confidence_result["evidence_tier"],
                "confidence_breakdown": confidence_result["breakdown"],
                "method": "llm_deep_research",
            }

            if "article_summaries" in parsed:
                result["article_summaries"] = parsed["article_summaries"]
            if "sub_question_answers" in parsed:
                result["sub_question_answers"] = parsed["sub_question_answers"]

            return result

        except Exception as e:
            logger.error("Comprehensive LLM extraction error: %s", e)
            return None


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _parse_json_response(response_text: str) -> Optional[Dict[str, Any]]:
    """Strip markdown fences and parse JSON. Returns None on failure."""
    try:
        text = response_text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except (json.JSONDecodeError, IndexError) as e:
        logger.warning("JSON parse failed: %s | raw: %s", e, response_text[:200])
        return None


def _extract_mechanism_dicts(raw: List[Any]) -> List[Dict[str, Any]]:
    """
    Normalize mechanism list to full dicts.
    Handles both legacy string lists and new dict format.
    """
    result = []
    for item in raw:
        if isinstance(item, dict):
            # Ensure required fields present with defaults
            result.append({
                "mechanism":          item.get("mechanism", ""),
                "description":        item.get("description", ""),
                "study_design":       item.get("study_design", "in_vitro"),
                "sample_size":        int(item.get("sample_size", 0) or 0),
                "ic50_data":          item.get("ic50_data"),  # None if not present
                "biomarker_relevance": item.get("biomarker_relevance", {}),
                # Keep legacy confidence field if present (for backward compat)
                # but it will be overridden by ConfidenceScorer at the top level
                "confidence":         float(item.get("confidence", 0.5) or 0.5),
            })
        elif isinstance(item, str) and item.strip():
            result.append({
                "mechanism":          item,
                "description":        "",
                "study_design":       "in_vitro",
                "sample_size":        0,
                "ic50_data":          None,
                "biomarker_relevance": {},
                "confidence":         0.5,
            })
    return result
