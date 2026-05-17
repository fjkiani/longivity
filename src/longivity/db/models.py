"""SQLAlchemy ORM models for the Longivity patient platform."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


# ─────────────────────────────────────────────────────────────────────────────
# Clinic / Auth
# ─────────────────────────────────────────────────────────────────────────────

class Clinic(Base):
    __tablename__ = "clinics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    users: Mapped[list["ClinicUser"]] = relationship("ClinicUser", back_populates="clinic")
    patients: Mapped[list["Patient"]] = relationship("Patient", back_populates="clinic")


class ClinicUser(Base):
    __tablename__ = "clinic_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    clinic_id: Mapped[str] = mapped_column(String(36), ForeignKey("clinics.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="clinician")  # admin | clinician
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    clinic: Mapped["Clinic"] = relationship("Clinic", back_populates="users")


# ─────────────────────────────────────────────────────────────────────────────
# Patients
# ─────────────────────────────────────────────────────────────────────────────

class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    clinic_id: Mapped[str] = mapped_column(String(36), ForeignKey("clinics.id"), nullable=False)
    mrn: Mapped[str | None] = mapped_column(String(100), nullable=True)  # medical record number
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[str | None] = mapped_column(String(20), nullable=True)  # ISO date string
    sex: Mapped[str | None] = mapped_column(String(10), nullable=True)  # male | female | other
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    # Intelligence cache (written by PatientIntelligenceService)
    intelligence_cache: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    intelligence_computed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_state: Mapped[str | None] = mapped_column(String(50), nullable=True)  # PatientState enum value
    urgency_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0–1.0

    clinic: Mapped["Clinic"] = relationship("Clinic", back_populates="patients")
    panels: Mapped[list["BiomarkerPanel"]] = relationship(
        "BiomarkerPanel", back_populates="patient", order_by="BiomarkerPanel.drawn_at"
    )
    test_orders: Mapped[list["TestOrder"]] = relationship(
        "TestOrder", back_populates="patient", order_by="TestOrder.generated_at"
    )
    events: Mapped[list["PatientEvent"]] = relationship(
        "PatientEvent", back_populates="patient", order_by="PatientEvent.event_at"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Biomarker Panels (one per blood draw)
# ─────────────────────────────────────────────────────────────────────────────

class BiomarkerPanel(Base):
    __tablename__ = "biomarker_panels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), nullable=False)
    drawn_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(100), default="manual")  # manual | quest | labcorp | pdf_upload
    lab_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # original parsed PDF data
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="panels")
    values: Mapped[list["PanelValue"]] = relationship(
        "PanelValue", back_populates="panel", cascade="all, delete-orphan"
    )


class PanelValue(Base):
    __tablename__ = "panel_values"
    __table_args__ = (UniqueConstraint("panel_id", "marker_key", name="uq_panel_marker"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    panel_id: Mapped[str] = mapped_column(String(36), ForeignKey("biomarker_panels.id"), nullable=False)
    marker_key: Mapped[str] = mapped_column(String(100), nullable=False)  # canonical key e.g. "albumin"
    marker_display: Mapped[str | None] = mapped_column(String(255), nullable=True)  # "Albumin, Serum"
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ref_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    ref_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    flag: Mapped[str | None] = mapped_column(String(20), nullable=True)  # H | L | HH | LL | None

    panel: Mapped["BiomarkerPanel"] = relationship("BiomarkerPanel", back_populates="values")


# ─────────────────────────────────────────────────────────────────────────────
# Test Orders (agent-generated lab requisitions)
# ─────────────────────────────────────────────────────────────────────────────

class TestOrder(Base):
    """
    A clinician-approved (or pending) lab test order generated by the
    test ordering agent. Stores the full agent output as JSON.
    """
    __tablename__ = "test_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    # Status lifecycle: pending → approved → sent → resulted → cancelled
    status: Mapped[str] = mapped_column(String(50), default="pending")

    # Full agent output stored as JSON
    ordering_rationale: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recommended_panels: Mapped[list | None] = mapped_column(JSON, nullable=True)
    requisition: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Approval metadata
    approved_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("clinic_users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="test_orders")
    approver: Mapped["ClinicUser | None"] = relationship("ClinicUser", foreign_keys=[approved_by])
    results: Mapped[list["TestOrderResult"]] = relationship(
        "TestOrderResult", back_populates="order", cascade="all, delete-orphan"
    )


class TestOrderResult(Base):
    """
    Links a resulted BiomarkerPanel back to the TestOrder that requested it.
    Created when lab results come back and are entered into the system.
    """
    __tablename__ = "test_order_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("test_orders.id"), nullable=False)
    panel_id: Mapped[str] = mapped_column(String(100), nullable=False)  # panel_id from test_panels.json
    resulted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    result_panel_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("biomarker_panels.id"), nullable=True
    )  # FK to the BiomarkerPanel that contains the actual values

    order: Mapped["TestOrder"] = relationship("TestOrder", back_populates="results")
    result_panel: Mapped["BiomarkerPanel | None"] = relationship("BiomarkerPanel")


class PatientEvent(Base):
    """
    Immutable audit log of every significant clinical event for a patient.
    The PatientIntelligenceService reads this timeline to reason about
    what has already happened and what the next action should be.
    """
    __tablename__ = "patient_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), nullable=False)
    clinic_id: Mapped[str] = mapped_column(String(36), ForeignKey("clinics.id"), nullable=False)

    # Event classification
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # Valid types: panel_uploaded | panel_created_manual | assessment_run |
    #   test_order_generated | test_order_approved | test_order_sent |
    #   test_order_resulted | compound_started | compound_stopped |
    #   intelligence_computed | clinician_note

    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="system", nullable=False)
    # 'clinician' | 'system' | 'agent'

    actor_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("clinic_users.id"), nullable=True
    )  # who triggered it (null = system/agent)

    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Event-specific data — see plan for per-type payload keys

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="events")
    actor: Mapped["ClinicUser | None"] = relationship("ClinicUser", foreign_keys=[actor_id])
