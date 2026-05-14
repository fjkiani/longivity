"""
OverseerAgent — node wrapper factory for the longivity LangGraph pipeline.

Wraps every agent node with:
  - Wall-clock timing (time.perf_counter)
  - Exception capture (agent errors are logged but do NOT crash the pipeline)
  - Structured audit_log entry appended to PatientState
  - pipeline_health summary written to PatientState after each node

Usage:
    from .overseer_agent import overseer_wrap
    graph.add_node("biomarker_agent", overseer_wrap(biomarker_agent, "biomarker_agent"))
"""
import time
from typing import Any, Callable, Dict
from .state import PatientState


def overseer_wrap(node_fn: Callable, node_name: str) -> Callable:
    """
    Wrap a LangGraph node function with timing, error capture, and audit logging.

    Args:
        node_fn: The original agent node function (PatientState -> PatientState)
        node_name: Human-readable name for this node (used in audit_log)

    Returns:
        Wrapped function with identical signature.
    """
    def wrapped(state: PatientState) -> PatientState:
        t0 = time.perf_counter()
        error_msg = None
        result = state  # default: pass through unchanged on error

        try:
            result = node_fn(state)
            status = "ok"
        except Exception as exc:
            status = "error"
            error_msg = f"{type(exc).__name__}: {exc}"
            # Do NOT re-raise — pipeline continues with current state
            errors = list(result.get("errors") or [])
            errors.append(f"[{node_name}] {error_msg}")
            result = {**dict(result), "errors": errors}

        duration_ms = int((time.perf_counter() - t0) * 1000)

        entry: Dict[str, Any] = {
            "agent": node_name,
            "duration_ms": duration_ms,
            "status": status,
            "error": error_msg,
        }

        # Append to audit_log
        audit_log = list(result.get("audit_log") or [])
        audit_log.append(entry)

        # Recompute pipeline_health
        total = len(audit_log)
        errors_count = sum(1 for e in audit_log if e["status"] == "error")
        pipeline_health: Dict[str, Any] = {
            "agents_completed": total,
            "agents_errored": errors_count,
            "total_duration_ms": sum(e["duration_ms"] for e in audit_log),
            "overall_status": "degraded" if errors_count > 0 else "healthy",
        }

        return {**dict(result), "audit_log": audit_log, "pipeline_health": pipeline_health}

    wrapped.__name__ = f"overseer_{node_name}"
    wrapped.__qualname__ = f"overseer_{node_name}"
    return wrapped


def build_pipeline_health(audit_log: list) -> Dict[str, Any]:
    """Compute pipeline_health summary from a completed audit_log."""
    if not audit_log:
        return {"agents_completed": 0, "agents_errored": 0, "total_duration_ms": 0, "overall_status": "not_run"}
    errors_count = sum(1 for e in audit_log if e["status"] == "error")
    return {
        "agents_completed": len(audit_log),
        "agents_errored": errors_count,
        "total_duration_ms": sum(e["duration_ms"] for e in audit_log),
        "overall_status": "degraded" if errors_count > 0 else "healthy",
    }
