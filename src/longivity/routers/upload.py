"""PDF upload router — parse lab PDFs and store as biomarker panels."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..core.deps import CurrentUser, DB
from ..db.models import BiomarkerPanel, Patient, PanelValue
from ..services.lab_pdf_parser import parse_lab_pdf
from ..services.patient_event_service import record_panel_uploaded

router = APIRouter(prefix="/api/v1/patients", tags=["upload"])


async def _trigger_recompute_bg(patient_id: str, clinic_id: str) -> None:
    """Fire-and-forget: recompute patient intelligence after new panel."""
    import logging
    logger = logging.getLogger(__name__)
    try:
        from ..db.database import AsyncSessionLocal
        from ..db.models import Patient
        from sqlalchemy import select
        from ..services.patient_intelligence_service import compute_patient_intelligence
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Patient).where(Patient.id == patient_id, Patient.clinic_id == clinic_id)
            )
            patient = result.scalar_one_or_none()
            if patient:
                await compute_patient_intelligence(patient, db, force_refresh=True)
                await db.commit()
    except Exception as e:
        logger.warning(f"Background recompute failed for patient {patient_id}: {e}")

MAX_PDF_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post("/{patient_id}/upload", response_model=dict, status_code=201)
async def upload_lab_pdf(
    patient_id: str,
    current_user: CurrentUser,
    db: DB,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Lab report PDF"),
    drawn_at: str = Form(default=None, description="Draw date ISO string (defaults to now)"),
    notes: str = Form(default=None),
):
    """
    Upload a lab report PDF. Parses biomarkers automatically and stores as a panel.

    Returns the created panel with all extracted values and parse confidence score.
    """
    # Verify patient
    p_result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == current_user.clinic_id,
        )
    )
    if not p_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Patient not found")

    # Validate file type
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        # Be lenient — some browsers send wrong content type
        if not (file.filename or "").lower().endswith(".pdf"):
            raise HTTPException(status_code=422, detail="Only PDF files are accepted")

    # Read file
    pdf_bytes = await file.read()
    if len(pdf_bytes) > MAX_PDF_SIZE:
        raise HTTPException(status_code=413, detail="PDF too large (max 20 MB)")
    if len(pdf_bytes) < 100:
        raise HTTPException(status_code=422, detail="PDF appears empty or corrupt")

    # Parse
    try:
        parse_result = parse_lab_pdf(pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"PDF parsing failed: {e}")

    if not parse_result["markers"]:
        raise HTTPException(
            status_code=422,
            detail="No biomarkers could be extracted from this PDF. "
                   "Try manual entry or a different PDF format.",
        )

    # Determine draw date
    if drawn_at:
        try:
            draw_dt = datetime.fromisoformat(drawn_at.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid drawn_at: {drawn_at}")
    else:
        draw_dt = datetime.now(timezone.utc)

    # Create panel
    panel = BiomarkerPanel(
        patient_id=patient_id,
        drawn_at=draw_dt,
        source="pdf_upload",
        lab_name=parse_result.get("lab_name"),
        notes=notes,
        raw_json={
            "filename": file.filename,
            "parse_confidence": parse_result["parse_confidence"],
            "phenoage_markers_found": parse_result["phenoage_markers_found"],
            "total_markers_found": parse_result["total_markers_found"],
        },
    )
    db.add(panel)
    await db.flush()

    # Store values
    for m in parse_result["markers"]:
        pv = PanelValue(
            panel_id=panel.id,
            marker_key=m["marker_key"],
            marker_display=m.get("marker_display"),
            value=m["value"],
            unit=m.get("unit"),
            ref_low=m.get("ref_low"),
            ref_high=m.get("ref_high"),
            flag=m.get("flag"),
        )
        db.add(pv)

    await db.flush()

    # Reload with values
    result = await db.execute(
        select(BiomarkerPanel)
        .where(BiomarkerPanel.id == panel.id)
        .options(selectinload(BiomarkerPanel.values))
    )
    panel = result.scalar_one()

    # Record clinical event
    await record_panel_uploaded(
        db=db,
        patient_id=patient_id,
        clinic_id=current_user.clinic_id,
        panel_id=panel.id,
        source=panel.source,
        marker_count=len(panel.values) if hasattr(panel, 'values') else 0,
        drawn_at=panel.drawn_at.isoformat() if panel.drawn_at else "",
        actor_id=current_user.id,
    )
    await db.commit()

    # Trigger background intelligence recompute
    background_tasks.add_task(_trigger_recompute_bg, patient_id, current_user.clinic_id)

    return {
        "panel_id": panel.id,
        "patient_id": patient_id,
        "drawn_at": panel.drawn_at.isoformat(),
        "source": panel.source,
        "lab_name": panel.lab_name,
        "parse_confidence": parse_result["parse_confidence"],
        "phenoage_markers_found": parse_result["phenoage_markers_found"],
        "total_markers_found": parse_result["total_markers_found"],
        "values": [
            {
                "marker_key": v.marker_key,
                "marker_display": v.marker_display,
                "value": v.value,
                "unit": v.unit,
                "ref_low": v.ref_low,
                "ref_high": v.ref_high,
                "flag": v.flag,
            }
            for v in panel.values
        ],
    }
