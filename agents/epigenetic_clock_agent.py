"""
Epigenetic Clock Agent — LangGraph node for the longivity pipeline.

Runs when epigenetic clock data is present in current_input.
Calls epigenetic_clock_service.score_epigenetic_clocks() and writes
result to state["epigenetic_clock_result"].

Inserted between cardiovascular_agent and longitudinal_agent in the graph.
"""
from __future__ import annotations

from .state import PatientState


def epigenetic_clock_agent(state: PatientState) -> PatientState:
    """
    Process epigenetic clock data if present in current_input.

    Reads:  state["current_input"]["epigenetic_clocks"]
    Writes: state["epigenetic_clock_result"]
    """
    try:
        from longivity.services.epigenetic_clock_service import score_epigenetic_clocks
    except ImportError:
        return {
            **dict(state),
            "errors": list(state.get("errors") or []) + ["epigenetic_clock_service not available"],
        }

    ci = state.get("current_input") or {}
    clock_values = ci.get("epigenetic_clocks") or {}

    agents_run = list(state.get("agents_run") or [])
    agents_run.append("epigenetic_clock_agent")

    if not clock_values:
        # No clock data — return state unchanged (gap_detection will flag this)
        return {**dict(state), "agents_run": agents_run}

    chronological_age = ci.get("age") or state.get("age")

    try:
        result = score_epigenetic_clocks(clock_values, chronological_age)
    except Exception as exc:
        errors = list(state.get("errors") or [])
        errors.append(f"epigenetic_clock_agent error: {exc}")
        return {**dict(state), "agents_run": agents_run, "errors": errors}

    return {**dict(state), "epigenetic_clock_result": result, "agents_run": agents_run}
