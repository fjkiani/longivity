#!/usr/bin/env python3
"""
Integration test: Research Intelligence — Scenarios 1 and 2.

Tests the full pipeline end-to-end WITHOUT hitting the real LLM or PubMed.

Key mocking strategy:
  1. Patch LLM_AVAILABLE=True in both enhanced_evidence_service and synthesis_engine
     (these are module-level flags set at import time — must patch as attributes)
  2. Inject mock LLM provider directly onto SynthesisEngine instance
  3. Mock portal with full interface: search_with_analysis + get_top_keywords
  4. Inject pre-built research plan to bypass LLM question formulator

Run:
    cd /workspace/longivity
    python scripts/test_ri_scenarios.py

Exit 0 = all tests pass. Exit 1 = failures.
"""

import asyncio
import json
import sys
import traceback
import uuid
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, "src")

# ── Colour helpers ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):  print(f"  {GREEN}✅ {msg}{RESET}")
def fail(msg):print(f"  {RED}❌ {msg}{RESET}")
def info(msg):print(f"  {YELLOW}ℹ  {msg}{RESET}")
def hdr(msg): print(f"\n{BOLD}{msg}{RESET}")


# ── Pre-built research plans (bypass LLM formulator) ─────────────────────────

PLAN_DIANA = {
    "primary_question": "What is the evidence for sulforaphane in BRCA2 heterozygous ovarian cancer prevention?",
    "entities": {
        "compound": "sulforaphane",
        "disease": "ovarian cancer",
        "mechanisms_of_interest": ["NRF2 activation", "HDAC inhibition", "DNA repair"],
    },
    "sub_questions": [
        "What mechanisms does sulforaphane target in ovarian cancer?",
        "What RCT evidence exists for sulforaphane in ovarian cancer prevention?",
    ],
    "portal_queries": {
        "pubmed": [
            '"sulforaphane" AND ovarian cancer',
            "sulforaphane AND BRCA2 AND cancer",
            "sulforaphane AND NRF2 AND ovarian",
        ]
    },
}

PLAN_ROBERT = {
    "primary_question": "What is the evidence for berberine reducing biological age acceleration in type 2 diabetes?",
    "entities": {
        "compound": "berberine",
        "disease": "type 2 diabetes",
        "mechanisms_of_interest": ["AMPK activation", "mTOR inhibition", "gut microbiome"],
    },
    "sub_questions": [
        "What mechanisms does berberine target in type 2 diabetes?",
        "What RCT evidence exists for berberine in T2D glycemic control?",
    ],
    "portal_queries": {
        "pubmed": [
            '"berberine" AND type 2 diabetes',
            "berberine AND AMPK AND diabetes",
            "berberine AND HbA1c AND RCT",
        ]
    },
}


# ── Mock LLM response factory ─────────────────────────────────────────────────

def _make_llm_response(compound: str, disease: str) -> str:
    """Produce a realistic mock LLM JSON response for the comprehensive extraction."""
    if "sulforaphane" in compound.lower() or "ovarian" in disease.lower():
        return json.dumps({
            "mechanisms": [
                {
                    "mechanism": "NRF2 activation",
                    "description": "Sulforaphane activates NRF2 transcription factor, upregulating antioxidant response elements and BRCA1 expression, supporting homologous recombination repair.",
                    "study_design": "RCT",
                    "sample_size": 40,
                    "ic50_data": {"value": "2.5 µM", "cell_line": "OVCAR-3", "source": "PMID:28765432"},
                    "biomarker_relevance": {"HRD": "HIGH", "BRCA2": "HIGH"},
                },
                {
                    "mechanism": "HDAC inhibition",
                    "description": "Sulforaphane inhibits class I/II HDACs, restoring epigenetic silencing of tumor suppressors including BRCA1.",
                    "study_design": "observational",
                    "sample_size": 0,
                    "ic50_data": None,
                    "biomarker_relevance": {"HRD": "MODERATE", "BRCA2": "MODERATE"},
                },
                {
                    "mechanism": "TP53 pathway modulation",
                    "description": "Indirect modulation of TP53-dependent transcription via NRF2-ARE axis.",
                    "study_design": "in_vitro",
                    "sample_size": 0,
                    "ic50_data": {"value": "5.0 µM", "cell_line": "SKOV-3", "source": "PMID:31234567"},
                    "biomarker_relevance": {"HRD": "LOW", "BRCA2": "LOW"},
                },
            ],
            "study_counts": {
                "rct_count": 1,
                "observational_count": 2,
                "invivo_count": 0,
                "invitro_count": 3,
                "total_sample_size": 40,
            },
            "is_fda_approved": False,
            "dosage": {
                "recommended_dose": "30-60mg sulforaphane daily (broccoli sprout extract)",
                "evidence": "Phase II RCT used 60mg/day for 12 weeks",
            },
            "safety": {
                "concerns": ["Monitor if starting chemotherapy"],
                "monitoring": ["CBC quarterly"],
            },
            "outcomes": [
                {
                    "outcome": "DNA repair support",
                    "details": "NRF2 activation upregulates BRCA1 and RAD51 expression",
                    "effect_size": "1.8-fold increase in BRCA1 expression",
                },
            ],
            "evidence_summary": (
                "Sulforaphane demonstrates moderate evidence for DNA repair support in BRCA2 heterozygous "
                "ovarian cancer prevention. One RCT (n=250) and two observational studies support NRF2 "
                "activation and HDAC inhibition as primary mechanisms. IC50 data available (2.5 µM in OVCAR-3). "
                "Evidence is particularly relevant for HRD+ patients."
            ),
        })

    elif "berberine" in compound.lower() or "diabetes" in disease.lower():
        return json.dumps({
            "mechanisms": [
                {
                    "mechanism": "AMPK activation",
                    "description": "Berberine activates AMP-activated protein kinase (AMPK), improving insulin sensitivity and glucose uptake via GLUT4 translocation.",
                    "study_design": "RCT",
                    "sample_size": 80,
                    "ic50_data": {"value": "10 µM", "cell_line": "HepG2", "source": "PMID:19800084"},
                    "biomarker_relevance": {"HbA1c": "HIGH", "fasting_glucose": "HIGH"},
                },
                {
                    "mechanism": "mTOR inhibition",
                    "description": "Berberine inhibits mTOR signaling, reducing hepatic glucose production and improving metabolic age markers.",
                    "study_design": "RCT",
                    "sample_size": 40,
                    "ic50_data": None,
                    "biomarker_relevance": {"HbA1c": "MODERATE", "fasting_glucose": "MODERATE"},
                },
                {
                    "mechanism": "Gut microbiome modulation",
                    "description": "Berberine reshapes gut microbiota composition, increasing short-chain fatty acid producers.",
                    "study_design": "observational",
                    "sample_size": 0,
                    "ic50_data": None,
                    "biomarker_relevance": {"HbA1c": "LOW"},
                },
            ],
            "study_counts": {
                "rct_count": 2,
                "observational_count": 1,
                "invivo_count": 0,
                "invitro_count": 2,
                "total_sample_size": 120,
            },
            "is_fda_approved": False,
            "dosage": {
                "recommended_dose": "500mg berberine 3x daily with meals",
                "evidence": "Meta-analysis of 3 RCTs used 500mg TID",
            },
            "safety": {
                "concerns": ["GI side effects in 15%", "Monitor with metformin"],
                "monitoring": ["HbA1c every 3 months"],
            },
            "outcomes": [
                {
                    "outcome": "HbA1c reduction",
                    "details": "Meta-analysis of 3 RCTs shows mean HbA1c reduction of 0.9%",
                    "effect_size": "WMD -0.90% (95% CI -1.17 to -0.63)",
                },
            ],
            "evidence_summary": (
                "Berberine demonstrates strong evidence for glycemic control in T2D with 3 RCTs (n=1000 total). "
                "AMPK activation and mTOR inhibition are the primary mechanisms relevant to biological age "
                "deceleration. IC50 data available (10 µM in HepG2). Additive effect with metformin requires "
                "monitoring."
            ),
        })

    return json.dumps({
        "mechanisms": [{"mechanism": "Unknown", "description": "No data", "study_design": "in_vitro",
                        "sample_size": 0, "ic50_data": None, "biomarker_relevance": {}}],
        "study_counts": {"rct_count": 0, "observational_count": 0, "invivo_count": 0,
                         "invitro_count": 1, "total_sample_size": 0},
        "dosage": {"recommended_dose": "", "evidence": ""},
        "safety": {"concerns": [], "monitoring": []},
        "outcomes": [],
        "evidence_summary": "Insufficient data.",
    })


# ── Mock LLM provider ─────────────────────────────────────────────────────────

class MockLLMResponse:
    def __init__(self, text): self.text = text

class MockLLMProvider:
    def is_available(self): return True

    async def chat(self, message="", system_message="", max_tokens=4096, temperature=0.0, **kw):
        msg_lower = (message or "").lower()

        # Mechanism extraction calls — detect by compound/disease keywords
        if "sulforaphane" in msg_lower or "ovarian" in msg_lower or "brca2" in msg_lower:
            return MockLLMResponse(_make_llm_response("sulforaphane", "ovarian cancer"))
        if "berberine" in msg_lower or "diabetes" in msg_lower or "hba1c" in msg_lower:
            return MockLLMResponse(_make_llm_response("berberine", "type 2 diabetes"))

        # Value synthesis — patient persona
        if "will_this_help" in msg_lower or "will this help" in msg_lower or "patient" in msg_lower:
            return MockLLMResponse(json.dumps({
                "executive_summary": "Sulforaphane shows moderate-to-strong evidence for DNA repair support in BRCA2 heterozygous ovarian cancer prevention.",
                "will_this_help": "Possibly. The research shows sulforaphane activates DNA repair pathways specifically relevant to your BRCA2 mutation and HRD+ status. Evidence is moderate — 1 RCT with 250 patients.",
                "is_it_safe": "Generally safe at dietary doses (30-60mg daily). Discuss with your oncologist before starting.",
                "action_items": ["Discuss sulforaphane with your oncologist", "Target 30-60mg daily", "Monitor CA-125 quarterly"],
                "confidence": 0.7139,
            }))

        # Value synthesis — doctor persona
        if "clinical_recommendation" in msg_lower or "doctor" in msg_lower or "prescrib" in msg_lower:
            return MockLLMResponse(json.dumps({
                "executive_summary": "Berberine demonstrates strong evidence for glycemic control in T2D (3 RCTs, n=1000).",
                "clinical_recommendation": "Consider berberine 500mg TID as adjunct to metformin. Monitor HbA1c every 3 months.",
                "evidence_quality": "STRONG — 3 RCTs, WMD -0.90% HbA1c (95% CI -1.17 to -0.63)",
                "safety_considerations": "GI side effects in 15%. Additive hypoglycemia risk with metformin.",
                "next_steps": ["Baseline HbA1c", "Start 500mg TID with meals", "Review at 3 months"],
                "confidence": 0.8672,
            }))

        # Generic fallback
        return MockLLMResponse(json.dumps({
            "executive_summary": "Analysis complete.",
            "action_items": [],
            "confidence": 0.5,
        }))


# ── Mock PubMed portal (full interface) ───────────────────────────────────────

def _make_pubmed_articles(compound: str) -> list:
    if "sulforaphane" in compound.lower():
        return [
            {
                "pmid": "28765432",
                "title": "Sulforaphane activates NRF2 in ovarian cancer cells: a randomized controlled trial",
                "abstract": (
                    "Randomized controlled trial. n=250 patients enrolled. Double-blind placebo-controlled. "
                    "Sulforaphane 60mg/day for 12 weeks. Primary endpoint: NRF2 target gene expression. "
                    "Results: 1.8-fold increase in BRCA1 expression (p<0.001). HDAC inhibition confirmed."
                ),
                "authors": ["Smith J", "Jones K"],
                "year": 2023,
                "journal": "Cancer Research",
                "url": "https://pubmed.ncbi.nlm.nih.gov/28765432",
            },
            {
                "pmid": "31234567",
                "title": "HDAC inhibition by sulforaphane in BRCA-mutant ovarian cancer cells",
                "abstract": (
                    "Observational cohort study. n=180 patients. In vitro IC50=5.0µM in SKOV-3. "
                    "HDAC class I/II inhibition confirmed. BRCA1 re-expression observed."
                ),
                "authors": ["Lee A", "Park B"],
                "year": 2022,
                "journal": "Molecular Cancer",
                "url": "https://pubmed.ncbi.nlm.nih.gov/31234567",
            },
            {
                "pmid": "25489052",
                "title": "Cruciferous vegetables and ovarian cancer risk: prospective cohort",
                "abstract": (
                    "Prospective cohort study. n=1200 participants. HR 0.77 (95% CI 0.61-0.97) "
                    "for ovarian cancer mortality with high cruciferous vegetable intake."
                ),
                "authors": ["Chen C", "Wang D"],
                "year": 2021,
                "journal": "JNCI",
                "url": "https://pubmed.ncbi.nlm.nih.gov/25489052",
            },
        ]
    elif "berberine" in compound.lower():
        return [
            {
                "pmid": "19800084",
                "title": "Berberine activates AMPK and improves insulin sensitivity: RCT",
                "abstract": (
                    "Randomized controlled trial. n=600 patients with T2D. Berberine 500mg TID for 3 months. "
                    "HbA1c reduction: WMD -0.90% (95% CI -1.17 to -0.63). AMPK activation confirmed. "
                    "IC50 10µM in HepG2 cells."
                ),
                "authors": ["Zhang Y", "Li X"],
                "year": 2023,
                "journal": "Diabetes Care",
                "url": "https://pubmed.ncbi.nlm.nih.gov/19800084",
            },
            {
                "pmid": "22345678",
                "title": "Berberine inhibits mTOR and reduces hepatic glucose production: RCT",
                "abstract": (
                    "Randomized controlled trial. n=400 patients. Berberine 500mg BID. "
                    "mTOR inhibition confirmed. Fasting glucose reduction 18mg/dL (p<0.01)."
                ),
                "authors": ["Liu M", "Wang H"],
                "year": 2022,
                "journal": "Metabolism",
                "url": "https://pubmed.ncbi.nlm.nih.gov/22345678",
            },
            {
                "pmid": "33456789",
                "title": "Berberine reshapes gut microbiome in T2D: observational study",
                "abstract": (
                    "Observational study. n=120 patients. Berberine increases Akkermansia muciniphila. "
                    "Short-chain fatty acid producers increased 2.3-fold."
                ),
                "authors": ["Zhao Q", "Sun R"],
                "year": 2021,
                "journal": "Gut Microbes",
                "url": "https://pubmed.ncbi.nlm.nih.gov/33456789",
            },
        ]
    return []


class MockPubMedPortal:
    """Matches the full EnhancedPubMedPortal interface."""

    def __init__(self, compound: str):
        self._compound = compound

    async def search_with_analysis(
        self,
        query: str,
        date_range=None,
        max_results: int = 1000,
        analyze_keywords: bool = True,
        include_trends: bool = True,
    ) -> Dict[str, Any]:
        articles = _make_pubmed_articles(self._compound)
        return {
            "articles": articles,
            "keyword_analysis": {
                "top_keywords": [
                    {"keyword": self._compound, "count": 10},
                    {"keyword": "RCT", "count": 5},
                    {"keyword": "mechanism", "count": 4},
                ],
                "trends": {},
            },
            "publication_counts": {"total": len(articles)},
            "query_used": query,
            "article_count": len(articles),
        }

    def get_top_keywords(self, analysis_result: Dict[str, Any], top_n: int = 10) -> List[str]:
        """Matches EnhancedPubMedPortal.get_top_keywords interface."""
        top_keywords = analysis_result.get("keyword_analysis", {}).get("top_keywords", [])
        return [kw["keyword"] for kw in top_keywords[:top_n]]

    async def search(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Legacy search interface fallback."""
        result = await self.search_with_analysis(query, max_results=max_results)
        return {"papers": result["articles"], "total": result["article_count"]}


# ── Mock question formulator ──────────────────────────────────────────────────

class MockQuestionFormulator:
    def __init__(self, plan: Dict):
        self._plan = plan

    async def formulate_research_plan(self, question: str, context: Dict) -> Dict:
        return self._plan


# ── Main test runner ──────────────────────────────────────────────────────────

async def run_scenario(
    scenario_name: str,
    question: str,
    context: Dict[str, Any],
    persona: str,
    research_plan: Dict,
    compound: str,
    assertions: list,
) -> bool:
    """Run one scenario end-to-end and check assertions."""
    hdr(f"{'='*60}")
    hdr(f"SCENARIO: {scenario_name}")
    print(f"  Question : {question}")
    print(f"  Context  : {json.dumps(context, indent=4)}")
    print(f"  Persona  : {persona}")

    import longivity.research_intelligence.enhanced_evidence_service as ees_mod
    import longivity.research_intelligence.synthesis_engine as se_mod
    from longivity.research_intelligence.orchestrator import ResearchIntelligenceOrchestrator
    from longivity.research_intelligence.value_synthesizer import ValueSynthesizer

    mock_provider   = MockLLMProvider()
    mock_pubmed     = MockPubMedPortal(compound)
    mock_formulator = MockQuestionFormulator(research_plan)

    # Patch module-level LLM_AVAILABLE flags (set at import time, can't be patched via get_llm_provider)
    with patch.object(ees_mod, "LLM_AVAILABLE", True), \
         patch.object(se_mod,  "LLM_AVAILABLE", True), \
         patch("longivity.research_intelligence.enhanced_evidence_service.get_llm_provider",
               return_value=mock_provider), \
         patch("longivity.research_intelligence.value_synthesizer.get_llm_provider",
               return_value=mock_provider):

        orch = ResearchIntelligenceOrchestrator()
        # Inject mock LLM directly onto synthesis_engine instance (bypasses __init__ LLM_AVAILABLE check)
        orch.synthesis_engine.llm_provider = mock_provider
        # Inject mock pubmed and formulator
        orch.pubmed              = mock_pubmed
        orch.question_formulator = mock_formulator

        # Mock _deep_parse_top_papers to return pubmed articles as full_text_articles
        # (bypasses Diffbot/pubmed_parser which are unavailable in test env)
        async def _mock_deep_parse(portal_results):
            articles = portal_results.get("pubmed", {}).get("articles", [])
            # Enrich with full_text field (use abstract as proxy)
            full_text_articles = [
                {**a, "full_text": a.get("abstract", "")}
                for a in articles
            ]
            return {
                "full_text_articles": full_text_articles,
                "parsed_count": len(full_text_articles),
                "diffbot_count": 0,
                "pubmed_parser_count": len(full_text_articles),
                "pharmacogenomics_cases": [],
            }
        orch._deep_parse_top_papers = _mock_deep_parse

        result = await orch.research_question(question=question, context=context)

    # Run value synthesis
    vs = ValueSynthesizer()
    with patch("longivity.research_intelligence.value_synthesizer.get_llm_provider",
               return_value=mock_provider):
        try:
            value_synthesis = await vs.synthesize_insights(result, persona=persona)
        except Exception as e:
            info(f"value_synthesis raised: {e}")
            traceback.print_exc()
            value_synthesis = {"error": str(e)}

    # Build full response (as router would)
    synthesized = result.get("synthesized_findings", {})
    full_response = {
        "query_id": str(uuid.uuid4()),
        "persona": persona,
        **result,
        "value_synthesis": value_synthesis,
        "overall_confidence": synthesized.get("overall_confidence"),
        "evidence_tier": synthesized.get("evidence_tier"),
        "clinical_phase_ceiling": synthesized.get("clinical_phase_ceiling"),
        "confidence_breakdown": synthesized.get("confidence_breakdown"),
    }

    # Print the full JSON response
    print(f"\n{'─'*60}")
    print("FULL RESPONSE JSON:")
    full_json = json.dumps(full_response, indent=2, default=str)
    print(full_json[:10000])
    if len(full_json) > 10000:
        print(f"  ... [truncated — full response saved to /tmp/scenario_{compound}_response.json]")
        with open(f"/tmp/scenario_{compound}_response.json", "w") as f:
            f.write(full_json)

    # Run assertions
    print(f"\n{'─'*60}")
    print("ASSERTIONS:")
    passed = 0
    failed_list = []
    for label, check_fn in assertions:
        try:
            result_val = check_fn(full_response)
            if result_val is False:
                fail(f"{label}")
                failed_list.append(label)
            else:
                ok(f"{label}")
                passed += 1
        except Exception as e:
            fail(f"{label} — EXCEPTION: {e}")
            failed_list.append(label)

    total = passed + len(failed_list)
    print(f"\n  Passed: {passed}/{total}")
    if failed_list:
        print(f"  Failed: {len(failed_list)}/{total}")
        for f_label in failed_list:
            print(f"    - {f_label}")
    return len(failed_list) == 0


async def main():
    failures = []

    # ── Scenario 1: Diana Park ────────────────────────────────────────────────
    s1_pass = await run_scenario(
        scenario_name="Scenario 1 — Diana Park (sulforaphane + HRD+ ovarian cancer prevention)",
        question="What is the evidence for sulforaphane in BRCA2 heterozygous ovarian cancer prevention?",
        context={
            "disease": "ovarian_cancer_hgs",
            "treatment_line": "prevention",
            "biomarkers": {"BRCA2": "HET", "HRD": "POSITIVE"},
        },
        persona="patient",
        research_plan=PLAN_DIANA,
        compound="sulforaphane",
        assertions=[
            # MOAT — not stub
            ("moat_analysis is present",
             lambda r: bool(r.get("moat_analysis"))),
            ("moat_analysis.pathways is non-empty list (not stub)",
             lambda r: isinstance(r["moat_analysis"].get("pathways"), list)
                       and len(r["moat_analysis"]["pathways"]) > 0),
            ("moat_analysis contains oxidative_stress or dna_repair pathway (NRF2 maps to oxidative_stress)",
             lambda r: "oxidative_stress" in r["moat_analysis"].get("pathways", [])
                       or "dna_repair" in r["moat_analysis"].get("pathways", [])),
            ("moat_analysis.treatment_line_analysis has score",
             lambda r: r["moat_analysis"].get("treatment_line_analysis", {}).get("score") is not None),
            ("moat_analysis.biomarker_analysis.total_matches >= 1",
             lambda r: r["moat_analysis"].get("biomarker_analysis", {}).get("total_matches", 0) >= 1),
            # Confidence — deterministic, not hardcoded 0.85
            ("overall_confidence is a float",
             lambda r: isinstance(r.get("overall_confidence"), float)),
            ("overall_confidence != 0.85 (not LLM-hallucinated)",
             lambda r: r.get("overall_confidence") != 0.85),
            ("overall_confidence != 1.0 (clinical-phase ceiling applied)",
             lambda r: r.get("overall_confidence") != 1.0),
            ("overall_confidence in calibrated range [0.35, 0.55] (supplement MODERATE)",
             lambda r: 0.35 <= r.get("overall_confidence", -1) <= 0.55),
            ("evidence_tier is MODERATE (not STRONG for supplement)",
             lambda r: r.get("evidence_tier") == "MODERATE"),
            ("clinical_phase_ceiling is present and <= 0.60 (pilot RCT territory)",
             lambda r: r.get("clinical_phase_ceiling") is not None
                       and r.get("clinical_phase_ceiling") <= 0.60),
            ("confidence_breakdown is present (not None)",
             lambda r: r.get("confidence_breakdown") is not None),
            ("confidence_breakdown has rct_count",
             lambda r: "rct_count" in (r.get("confidence_breakdown") or {})),
            ("confidence_breakdown has biomarker_match",
             lambda r: "biomarker_match" in (r.get("confidence_breakdown") or {})),
            ("confidence_breakdown has formula string",
             lambda r: isinstance((r.get("confidence_breakdown") or {}).get("formula"), str)
                       and len((r.get("confidence_breakdown") or {}).get("formula", "")) > 10),
            # Mechanisms — full dicts with new fields
            ("synthesized_findings.mechanisms is non-empty",
             lambda r: len(r.get("synthesized_findings", {}).get("mechanisms", [])) > 0),
            ("first mechanism has study_design field",
             lambda r: "study_design" in r["synthesized_findings"]["mechanisms"][0]),
            ("first mechanism has biomarker_relevance field",
             lambda r: "biomarker_relevance" in r["synthesized_findings"]["mechanisms"][0]),
            ("NRF2 activation is first mechanism (LLM leads, not generic)",
             lambda r: r["synthesized_findings"]["mechanisms"][0].get("mechanism") == "NRF2 activation"),
            # Value synthesis
            ("value_synthesis is present",
             lambda r: r.get("value_synthesis") is not None),
            ("value_synthesis.will_this_help is non-empty string (patient persona)",
             lambda r: bool(r.get("value_synthesis", {}).get("will_this_help"))),
            ("value_synthesis.confidence is a float",
             lambda r: isinstance(r.get("value_synthesis", {}).get("confidence"), float)),
            # query_id
            ("query_id is a valid UUID",
             lambda r: bool(r.get("query_id")) and len(r["query_id"]) == 36),
        ],
    )
    if not s1_pass:
        failures.append("Scenario 1")

    # ── Scenario 2: Robert Chen ───────────────────────────────────────────────
    s2_pass = await run_scenario(
        scenario_name="Scenario 2 — Robert Chen (berberine + T2D biological age)",
        question="What is the evidence for berberine reducing biological age acceleration in type 2 diabetes?",
        context={
            "disease": "type_2_diabetes",
            "treatment_line": "L1",
            "biomarkers": {"HbA1c": 8.2, "fasting_glucose": 165},
        },
        persona="doctor",
        research_plan=PLAN_ROBERT,
        compound="berberine",
        assertions=[
            # MOAT
            ("moat_analysis is present",
             lambda r: bool(r.get("moat_analysis"))),
            ("moat_analysis.pathways is non-empty",
             lambda r: len(r["moat_analysis"].get("pathways", [])) > 0),
            ("moat_analysis contains metabolism pathway",
             lambda r: "metabolism" in r["moat_analysis"].get("pathways", [])),
            ("moat_analysis.treatment_line_analysis has score",
             lambda r: r["moat_analysis"].get("treatment_line_analysis", {}).get("score") is not None),
            # Confidence
            ("overall_confidence is a float",
             lambda r: isinstance(r.get("overall_confidence"), float)),
            ("overall_confidence != 0.85 (not LLM-hallucinated)",
             lambda r: r.get("overall_confidence") != 0.85),
            ("overall_confidence != 1.0 (clinical-phase ceiling applied)",
             lambda r: r.get("overall_confidence") != 1.0),
            ("overall_confidence in calibrated range [0.40, 0.65] (supplement MODERATE)",
             lambda r: 0.40 <= r.get("overall_confidence", -1) <= 0.65),
            ("evidence_tier is MODERATE (not STRONG for supplement)",
             lambda r: r.get("evidence_tier") == "MODERATE"),
            ("clinical_phase_ceiling is present and <= 0.75",
             lambda r: r.get("clinical_phase_ceiling") is not None
                       and r.get("clinical_phase_ceiling") <= 0.75),
            ("confidence_breakdown present",
             lambda r: r.get("confidence_breakdown") is not None),
            ("confidence_breakdown has rct_count",
             lambda r: "rct_count" in (r.get("confidence_breakdown") or {})),
            ("rct_count >= 1 (berberine has RCT evidence)",
             lambda r: (r.get("confidence_breakdown") or {}).get("rct_count", 0) >= 1),
            ("biomarker_match is True (HbA1c=8.2 > 6.5 threshold — numeric parser fixed)",
             lambda r: (r.get("confidence_breakdown") or {}).get("biomarker_match") == True),
            ("biomarker_score > 0 (numeric biomarker bonus applied)",
             lambda r: (r.get("confidence_breakdown") or {}).get("biomarker_score", 0) > 0),
            # Mechanisms
            ("synthesized_findings.mechanisms is non-empty",
             lambda r: len(r.get("synthesized_findings", {}).get("mechanisms", [])) > 0),
            ("AMPK activation is first mechanism",
             lambda r: r["synthesized_findings"]["mechanisms"][0].get("mechanism") == "AMPK activation"),
            ("first mechanism has study_design RCT",
             lambda r: r["synthesized_findings"]["mechanisms"][0].get("study_design") == "RCT"),
            # Value synthesis — doctor persona
            ("value_synthesis is present",
             lambda r: r.get("value_synthesis") is not None),
            ("value_synthesis.clinical_recommendation is non-empty (doctor persona)",
             lambda r: bool(r.get("value_synthesis", {}).get("clinical_recommendation"))),
            # query_id
            ("query_id is a valid UUID",
             lambda r: bool(r.get("query_id")) and len(r["query_id"]) == 36),
        ],
    )
    if not s2_pass:
        failures.append("Scenario 2")

    # ── Final summary ─────────────────────────────────────────────────────────
    hdr("=" * 60)
    hdr("FINAL SUMMARY")
    if not failures:
        print(f"\n{GREEN}{BOLD}✅ ALL SCENARIOS PASSED{RESET}\n")
        return 0
    else:
        print(f"\n{RED}{BOLD}❌ FAILED SCENARIOS: {', '.join(failures)}{RESET}\n")
        return 1


if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    exit_code = asyncio.get_event_loop().run_until_complete(main())
    sys.exit(exit_code)
