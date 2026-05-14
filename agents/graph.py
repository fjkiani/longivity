"""
LangGraph state machine for the longivity multi-agent longevity assessment pipeline.

Graph topology:
  biomarker_agent
      ↓ (conditional)
  genetic_agent ──────────────────────────────────────────────────────────────┐
      ↓ (conditional)                                                          │
  cardiovascular_agent ←──────────────────────────────────────────────────────┘
      ↓
  longitudinal_agent
      ↓
  gap_detection_agent
      ↓
  report_assembler_agent
      ↓
  END

Conditional routing:
  - genetic_agent runs only if variants or patient_genotype present
  - cardiovascular_agent runs only if age + sex + lipid data present
    (otherwise skips directly to longitudinal_agent)
"""
from __future__ import annotations

from typing import Optional

from langgraph.graph import StateGraph, END

from .state import PatientState
from .biomarker_agent import biomarker_agent
from .genetic_agent import genetic_agent
from .cardiovascular_agent import cardiovascular_agent
from .gap_detection_agent import gap_detection_agent
from .longitudinal_agent import longitudinal_agent
from .report_assembler_agent import report_assembler_agent


# ─────────────────────────────────────────────────────────────────────────────
# Routing functions
# ─────────────────────────────────────────────────────────────────────────────

def _route_after_biomarker(state: PatientState) -> str:
    """After biomarker agent: run genetics if data present, else go to cardiovascular."""
    ci = state.get("current_input", {}) or {}
    has_variants = bool(ci.get("variants"))
    has_genotype = bool(ci.get("patient_genotype"))
    if has_variants or has_genotype:
        return "genetic_agent"
    return "cardiovascular_agent"


def _route_after_genetics(state: PatientState) -> str:
    """After genetic agent: run cardiovascular if enough data present."""
    ci = state.get("current_input", {}) or {}
    bio = {
        str(k).strip().replace("-", "_").replace("/", "_").lower(): v
        for k, v in (ci.get("biomarkers") or {}).items()
    }
    has_age = bool(ci.get("age") or ci.get("chronological_age"))
    has_sex = bool(ci.get("sex"))
    has_lipids = any(k in bio for k in (
        "total_cholesterol", "total_chol",
        "hdl_cholesterol", "hdl",
        "ldl_cholesterol", "ldl",
    ))
    has_sbp = any(k in bio for k in ("systolic_bp", "sbp"))
    if has_age and has_sex and has_lipids and has_sbp:
        return "cardiovascular_agent"
    return "longitudinal_agent"


def _route_after_biomarker_no_genetics(state: PatientState) -> str:
    """
    When genetics is skipped: check if cardiovascular data is available.
    Reuses same logic as _route_after_genetics.
    """
    return _route_after_genetics(state)


# ─────────────────────────────────────────────────────────────────────────────
# Graph builder
# ─────────────────────────────────────────────────────────────────────────────

def build_longevity_graph() -> StateGraph:
    """Build and compile the LangGraph longevity assessment state machine."""
    graph = StateGraph(PatientState)

    # ── Register all nodes ────────────────────────────────────────────────────
    graph.add_node("biomarker_agent", biomarker_agent)
    graph.add_node("genetic_agent", genetic_agent)
    graph.add_node("cardiovascular_agent", cardiovascular_agent)
    graph.add_node("longitudinal_agent", longitudinal_agent)
    graph.add_node("gap_detection_agent", gap_detection_agent)
    graph.add_node("report_assembler_agent", report_assembler_agent)

    # ── Entry point ───────────────────────────────────────────────────────────
    graph.set_entry_point("biomarker_agent")

    # ── Biomarker → conditional genetics or cardiovascular ────────────────────
    graph.add_conditional_edges(
        "biomarker_agent",
        _route_after_biomarker,
        {
            "genetic_agent": "genetic_agent",
            "cardiovascular_agent": "cardiovascular_agent",
        },
    )

    # ── Genetics → conditional cardiovascular or longitudinal ─────────────────
    graph.add_conditional_edges(
        "genetic_agent",
        _route_after_genetics,
        {
            "cardiovascular_agent": "cardiovascular_agent",
            "longitudinal_agent": "longitudinal_agent",
        },
    )

    # ── Cardiovascular → longitudinal (always) ────────────────────────────────
    graph.add_edge("cardiovascular_agent", "longitudinal_agent")

    # ── Longitudinal → gap detection ──────────────────────────────────────────
    graph.add_edge("longitudinal_agent", "gap_detection_agent")

    # ── Gap detection → report assembly ──────────────────────────────────────
    graph.add_edge("gap_detection_agent", "report_assembler_agent")

    # ── Report → END ──────────────────────────────────────────────────────────
    graph.add_edge("report_assembler_agent", END)

    return graph.compile()


# ─────────────────────────────────────────────────────────────────────────────
# Singleton compiled graph (lazy init)
# ─────────────────────────────────────────────────────────────────────────────
_GRAPH: Optional[object] = None


def get_longevity_graph():
    """Return the compiled LangGraph longevity assessment graph (singleton)."""
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_longevity_graph()
    return _GRAPH
