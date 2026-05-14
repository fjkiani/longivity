"""
longivity.agents — LangGraph multi-agent longevity assessment pipeline.

Public API:
    get_longevity_graph()  → compiled LangGraph StateGraph
    PatientState           → TypedDict for patient state
    VisitRecord            → TypedDict for visit history entries
"""
from .state import PatientState, VisitRecord
from .graph import get_longevity_graph, build_longevity_graph

__all__ = [
    "PatientState",
    "VisitRecord",
    "get_longevity_graph",
    "build_longevity_graph",
]
