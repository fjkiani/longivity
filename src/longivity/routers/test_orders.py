"""
Test Orders Router — agent-driven lab test ordering endpoints.

Endpoints:
  GET  /patients/{patient_id}/test-order          — run agent, return recommendations
  POST /patients/{patient_id}/test-order          — approve & save order to DB
  GET  /patients/{patient_id}/test-order/{order_id} — retrieve saved order
  GET  /patients/{patient_id}/test-order/{order_id}/requisition — download requisition
  GET  /patients/{patient_id}/biomarker-gaps      — gap detection only (Step A)
  GET  /markers/{marker_key}                      — marker detail
  GET  /panels                                    — list all panels
  GET  /panels/{panel_id}                         — panel detail
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select

from ..core.deps import CurrentUser, DB
from ..db.models import BiomarkerPanel, Patient, PanelValue, TestOrder, TestOrderResult
from ..services.biomarker_registry_service import (
    evaluate_marker_status,
    get_all_markers,
    get_all_panels,
    get_marker,
    get_panel,
    get_panels_by_tier,
    get_registry_metadata,
)
from ..services.test_ordering_agent import (
    apply_escalation_rules,
    detect_gaps,
    run_test_ordering_agent,
)
from ..services.patient_event_service import record_test_order_generated, record_test_order_approved

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["test-orders"])


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _get_patient_or_404(patient_id: str, user: Any, db: Any) -> Patient:
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == user.clinic_id,
            Patient.is_active == True,
        )
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


async def _load_patient_panels(patient_id: str, db: Any) -> List[Dict]:
    """Load all biomarker panels + values for a patient as plain dicts."""
    result = await db.execute(
        select(BiomarkerPanel).where(BiomarkerPanel.patient_id == patient_id)
    )
    panels = result.scalars().all()

    panel_dicts = []
    for panel in panels:
        vals_result = await db.execute(
            select(PanelValue).where(PanelValue.panel_id == panel.id)
        )
        values = vals_result.scalars().all()
        panel_dicts.append({
            "id": panel.id,
            "drawn_at": panel.drawn_at.isoformat() if panel.drawn_at else None,
            "source": panel.source,
            "values": [
                {
                    "marker_key": v.marker_key,
                    "value": v.value,
                    "unit": v.unit,
                    "flag": v.flag,
                }
                for v in values
            ],
        })
    return panel_dicts


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────────────────────────────────────

class ApproveOrderRequest(BaseModel):
    notes: Optional[str] = None
    # Optionally override which panels to include (subset of recommended)
    panel_ids_to_include: Optional[List[str]] = None


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints: Test Orders
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/patients/{patient_id}/test-order")
async def generate_test_order(
    patient_id: str,
    user: CurrentUser,
    db: DB,
    include_hallmarks: bool = Query(True, description="Run hallmark-driven panel mapping"),
):
    """
    Run the 3-step test ordering agent for a patient and return recommendations.
    Does NOT save to the database — use POST to approve and save.

    Steps:
    1. Gap Detection — which baseline markers are missing
    2. Hallmark-Driven Mapping — which panels cover active aging hallmarks
    3. Rule-Based Escalation — which panels are triggered by abnormal values
    """
    patient = await _get_patient_or_404(patient_id, user, db)
    panels = await _load_patient_panels(patient_id, db)

    # Optionally run hallmark scorer on existing data
    active_hallmarks: Dict = {}
    if include_hallmarks and panels:
        try:
            from ..services.longevity_hallmark_scorer import LongevityHallmarkScorer
            scorer = LongevityHallmarkScorer()
            # Build flat biomarker dict for scorer
            bm_values: Dict[str, Any] = {}
            for panel in panels:
                for v in panel.get("values", []):
                    bm_values[v["marker_key"]] = v["value"]
            active_hallmarks = scorer.score_hallmark_vulnerabilities(bm_values)
        except Exception as e:
            logger.warning(f"Hallmark scoring failed (non-fatal): {e}")

    # Compute patient age
    age: Optional[int] = None
    if patient.date_of_birth:
        try:
            from datetime import date
            dob = date.fromisoformat(patient.date_of_birth)
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except Exception:
            pass

    result = run_test_ordering_agent(
        patient_id=patient_id,
        existing_panels=panels,
        active_hallmarks=active_hallmarks,
        sex=patient.sex,
        age=age,
    )

    # Record clinical event
    try:
        summary = result.get("summary", {})
        await record_test_order_generated(
            db=db,
            patient_id=patient_id,
            clinic_id=user.clinic_id,
            order_id=result.get("patient_id", patient_id) + "_draft",  # draft — no DB ID yet
            panels_recommended=summary.get("total_panels_recommended", 0),
            total_cost=summary.get("total_estimated_cost_usd", 0.0),
            actor_id=user.id,
        )
        await db.commit()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to record test_order_generated event: {e}")

    return result


@router.post("/patients/{patient_id}/test-order", status_code=status.HTTP_201_CREATED)
async def approve_test_order(
    patient_id: str,
    body: ApproveOrderRequest,
    user: CurrentUser,
    db: DB,
):
    """
    Approve and save a test order to the database.
    Runs the agent fresh, then saves the result with status='approved'.
    """
    patient = await _get_patient_or_404(patient_id, user, db)
    panels = await _load_patient_panels(patient_id, db)

    active_hallmarks: Dict = {}
    try:
        from ..services.longevity_hallmark_scorer import LongevityHallmarkScorer
        scorer = LongevityHallmarkScorer()
        bm_values: Dict[str, Any] = {}
        for panel in panels:
            for v in panel.get("values", []):
                bm_values[v["marker_key"]] = v["value"]
        active_hallmarks = scorer.score_hallmark_vulnerabilities(bm_values)
    except Exception as e:
        logger.warning(f"Hallmark scoring failed (non-fatal): {e}")

    age: Optional[int] = None
    if patient.date_of_birth:
        try:
            from datetime import date
            dob = date.fromisoformat(patient.date_of_birth)
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except Exception:
            pass

    agent_result = run_test_ordering_agent(
        patient_id=patient_id,
        existing_panels=panels,
        active_hallmarks=active_hallmarks,
        sex=patient.sex,
        age=age,
    )

    # Filter panels if clinician specified a subset
    recommended = agent_result.get("recommended_panels", [])
    if body.panel_ids_to_include:
        recommended = [p for p in recommended if p["panel_id"] in body.panel_ids_to_include]

    order = TestOrder(
        patient_id=patient_id,
        status="approved",
        ordering_rationale=agent_result.get("ordering_rationale"),
        recommended_panels=recommended,
        requisition=agent_result.get("requisition"),
        summary=agent_result.get("summary"),
        approved_by=user.id,
        approved_at=datetime.now(timezone.utc),
        notes=body.notes,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    # Record clinical event
    try:
        await record_test_order_approved(
            db=db,
            patient_id=patient_id,
            clinic_id=user.clinic_id,
            order_id=order.id,
            panels_approved=len(recommended),
            actor_id=user.id,
        )
        await db.commit()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to record test_order_approved event: {e}")

    return {
        "order_id": order.id,
        "patient_id": patient_id,
        "status": order.status,
        "approved_at": order.approved_at.isoformat() if order.approved_at else None,
        "approved_by": user.full_name or user.email,
        "summary": order.summary,
        "recommended_panels_count": len(recommended),
        "notes": order.notes,
    }


@router.get("/patients/{patient_id}/test-order/{order_id}")
async def get_test_order(
    patient_id: str,
    order_id: str,
    user: CurrentUser,
    db: DB,
):
    """Retrieve a saved test order by ID."""
    await _get_patient_or_404(patient_id, user, db)

    result = await db.execute(
        select(TestOrder).where(
            TestOrder.id == order_id,
            TestOrder.patient_id == patient_id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Test order not found")

    return {
        "order_id": order.id,
        "patient_id": order.patient_id,
        "status": order.status,
        "generated_at": order.generated_at.isoformat() if order.generated_at else None,
        "approved_at": order.approved_at.isoformat() if order.approved_at else None,
        "notes": order.notes,
        "summary": order.summary,
        "ordering_rationale": order.ordering_rationale,
        "recommended_panels": order.recommended_panels,
        "requisition": order.requisition,
    }


@router.get("/patients/{patient_id}/test-order/{order_id}/requisition")
async def get_requisition(
    patient_id: str,
    order_id: str,
    user: CurrentUser,
    db: DB,
):
    """Download the structured requisition for a saved test order."""
    await _get_patient_or_404(patient_id, user, db)

    result = await db.execute(
        select(TestOrder).where(
            TestOrder.id == order_id,
            TestOrder.patient_id == patient_id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Test order not found")

    return {
        "order_id": order.id,
        "patient_id": order.patient_id,
        "status": order.status,
        "generated_at": order.generated_at.isoformat() if order.generated_at else None,
        "requisition": order.requisition,
    }


@router.get("/patients/{patient_id}/test-orders")
async def list_test_orders(
    patient_id: str,
    user: CurrentUser,
    db: DB,
    status_filter: Optional[str] = Query(None, alias="status"),
):
    """List all test orders for a patient."""
    await _get_patient_or_404(patient_id, user, db)

    query = select(TestOrder).where(TestOrder.patient_id == patient_id)
    if status_filter:
        query = query.where(TestOrder.status == status_filter)
    query = query.order_by(TestOrder.generated_at.desc())

    result = await db.execute(query)
    orders = result.scalars().all()

    return [
        {
            "order_id": o.id,
            "status": o.status,
            "generated_at": o.generated_at.isoformat() if o.generated_at else None,
            "approved_at": o.approved_at.isoformat() if o.approved_at else None,
            "summary": o.summary,
            "notes": o.notes,
        }
        for o in orders
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints: Biomarker Gaps
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/patients/{patient_id}/biomarker-gaps")
async def get_biomarker_gaps(
    patient_id: str,
    user: CurrentUser,
    db: DB,
):
    """
    Step A only — identify which markers are missing from this patient's record.
    Returns missing markers by tier and baseline coverage percentage.
    """
    patient = await _get_patient_or_404(patient_id, user, db)
    panels = await _load_patient_panels(patient_id, db)

    existing_keys = set()
    for panel in panels:
        for v in panel.get("values", []):
            existing_keys.add(v["marker_key"])

    gaps = detect_gaps(existing_keys, sex=patient.sex)

    # Enrich missing markers with display names
    def enrich(keys: List[str]) -> List[Dict]:
        result = []
        for k in keys:
            m = get_marker(k)
            result.append({
                "marker_key": k,
                "display_name": m.get("display_name", k) if m else k,
                "domain": m.get("domain") if m else None,
                "panel": m.get("panel") if m else None,
                "clinical_significance": m.get("clinical_significance") if m else None,
            })
        return result

    return {
        "patient_id": patient_id,
        "tier1_coverage_pct": gaps["coverage_pct"],
        "missing_tier1": enrich(gaps["missing_tier1"]),
        "missing_tier2": enrich(gaps["missing_tier2"]),
        "missing_tier3": enrich(gaps["missing_tier3"]),
        "missing_panels_tier1": gaps["missing_panels_tier1"],
        "existing_marker_count": len(existing_keys),
        "total_tier1_markers": len(get_markers_by_tier_count("tier_1")),
    }


def get_markers_by_tier_count(tier: str) -> List:
    from ..services.biomarker_registry_service import get_markers_by_tier
    return get_markers_by_tier(tier)


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints: Marker Lookup
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/markers")
async def list_markers(
    domain: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
):
    """
    List all markers in the registry.
    Supports filtering by domain, ordering_tier, and text search.
    """
    markers = get_all_markers()

    if domain:
        markers = [m for m in markers if m.get("domain") == domain]
    if tier:
        markers = [m for m in markers if m.get("ordering_tier") == tier]
    if search:
        q = search.lower()
        markers = [
            m for m in markers
            if q in m.get("marker_key", "").lower()
            or q in m.get("display_name", "").lower()
            or any(q in a.lower() for a in m.get("aliases", []))
        ]

    total = len(markers)
    markers = markers[offset : offset + limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "markers": markers,
    }


@router.get("/markers/{marker_key}")
async def get_marker_detail(marker_key: str):
    """
    Get full detail for a single marker including clinical ranges,
    longevity-optimal ranges, escalation triggers, and hallmark associations.
    """
    marker = get_marker(marker_key)
    if not marker:
        raise HTTPException(status_code=404, detail=f"Marker '{marker_key}' not found")
    return marker


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints: Panel Catalog
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/panels")
async def list_panels(
    tier: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """
    List all orderable test panels.
    Supports filtering by ordering_tier and domain.
    """
    panels = get_all_panels()

    if tier:
        panels = [p for p in panels if p.get("ordering_tier") == tier]
    if domain:
        panels = [p for p in panels if p.get("domain") == domain]
    if search:
        q = search.lower()
        panels = [
            p for p in panels
            if q in p.get("panel_id", "").lower()
            or q in p.get("display_name", "").lower()
            or q in p.get("description", "").lower()
        ]

    return {
        "total": len(panels),
        "panels": panels,
    }


@router.get("/panels/{panel_id}")
async def get_panel_detail(panel_id: str):
    """
    Get full detail for a single test panel including all markers,
    specimen requirements, cost, and Quest/LabCorp codes.
    """
    panel = get_panel(panel_id)
    if not panel:
        raise HTTPException(status_code=404, detail=f"Panel '{panel_id}' not found")

    # Enrich with marker details
    marker_details = []
    for mk in panel.get("markers", []):
        m = get_marker(mk)
        if m:
            marker_details.append({
                "marker_key": mk,
                "display_name": m.get("display_name", mk),
                "unit": m.get("unit"),
                "clinical_low": m.get("clinical_low"),
                "clinical_high": m.get("clinical_high"),
                "longevity_optimal_low": m.get("longevity_optimal_low"),
                "longevity_optimal_high": m.get("longevity_optimal_high"),
                "clinical_significance": m.get("clinical_significance"),
            })
        else:
            marker_details.append({"marker_key": mk, "display_name": mk})

    return {**panel, "marker_details": marker_details}


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints: Registry Metadata
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/registry/metadata")
async def get_registry_info():
    """Return metadata about the biomarker registry and panel catalog."""
    reg_meta = get_registry_metadata()
    return {
        "registry": reg_meta,
        "total_markers": reg_meta.get("total_count", 0),
        "total_panels": len(get_all_panels()),
        "domains": reg_meta.get("domains", []),
        "ordering_tiers": reg_meta.get("ordering_tiers", {}),
        "hallmarks": reg_meta.get("hallmarks", []),
    }
