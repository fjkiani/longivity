from __future__ import annotations
from typing import Any, Dict, List, Optional, TypedDict
from datetime import datetime


class VisitRecord(TypedDict):
    visit_id: str
    timestamp: str
    biomarkers: Dict[str, Any]
    variants: Optional[Dict[str, Any]]
    patient_genotype: Optional[Dict[str, Any]]
    wearables: Optional[Dict[str, Any]]
    body_composition: Optional[Dict[str, Any]]
    medications: List[str]
    compound_queries: List[str]
    assessment_result: Optional[Dict[str, Any]]


class PatientState(TypedDict):
    # Identity
    patient_id: str
    age: Optional[int]
    sex: Optional[str]  # "M" / "F" / None

    # Current visit input
    current_input: Dict[str, Any]

    # Accumulated history (list of VisitRecord)
    visit_history: List[VisitRecord]

    # Current visit outputs (filled by agents)
    phenoage_result: Optional[Dict[str, Any]]
    hallmark_result: Optional[Dict[str, Any]]
    genetic_result: Optional[Dict[str, Any]]
    dna_repair_result: Optional[Dict[str, Any]]
    prs_result: Optional[Dict[str, Any]]
    compound_result: Optional[Dict[str, Any]]
    cardiovascular_risk: Optional[Dict[str, Any]]
    wearable_result: Optional[Dict[str, Any]]
    body_composition_result: Optional[Dict[str, Any]]

    # Gap detection output
    detected_gaps: List[Dict[str, Any]]
    gap_priority_order: List[str]

    # Longitudinal delta (if prior visit exists)
    longitudinal_delta: Optional[Dict[str, Any]]

    # Final assembled report
    final_report: Optional[Dict[str, Any]]

    # Routing / control
    errors: List[str]
    agents_run: List[str]
    run_id: str
    timestamp: str
