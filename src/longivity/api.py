from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from .services.longevity_phenoage_level0 import run_longevity_assessment_level0
from .services.longevity_report_builder import run_longevity_full_assessment

router = APIRouter(prefix="/api/v1/longevity", tags=["longevity"])


class LongevityAssessmentLevel0Request(BaseModel):
    """Level 0: PhenoAge Gompertz (PMID 29676998) + hallmark narrative + optional compound ranking (RUO)."""

    biomarkers: Dict[str, Any] = Field(default_factory=dict)
    age: Optional[int] = None
    chronological_age: Optional[int] = None
    compound_queries: Optional[List[str]] = Field(default=None)
    patient_medications: Optional[List[str]] = Field(default=None)
    medications: Optional[List[str]] = Field(
        default=None,
        description="Alias for patient_medications (same semantics).",
    )

    @model_validator(mode="after")
    def merge_medication_aliases(self):
        if self.medications:
            if not self.patient_medications:
                self.patient_medications = list(self.medications)
            else:
                seen: set = set()
                merged: List[str] = []
                for x in list(self.patient_medications) + list(self.medications):
                    if x and str(x) not in seen:
                        seen.add(str(x))
                        merged.append(str(x))
                self.patient_medications = merged
        return self


class LongevityFullAssessmentRequest(LongevityAssessmentLevel0Request):
    """Level 0 plus optional Module 1 (variants) and Module 2 (patient_genotype for DNA repair)."""

    patient_id: Optional[str] = Field(default=None)
    variants: Optional[Dict[str, Any]] = Field(default=None)
    patient_genotype: Optional[Dict[str, Any]] = Field(default=None)


@router.post("/assessment_level0")
async def longevity_assessment_level0(body: LongevityAssessmentLevel0Request) -> Dict[str, Any]:
    payload = body.model_dump(exclude_none=True)
    return run_longevity_assessment_level0(payload)


@router.post("/full_assessment")
async def longevity_full_assessment(body: LongevityFullAssessmentRequest) -> Dict[str, Any]:
    payload = body.model_dump(exclude_none=True)
    result = run_longevity_full_assessment(payload)
    if result.get("status") == "ERROR":
        raise HTTPException(
            status_code=422,
            detail=result.get("error", "No usable input for longevity assessment."),
        )
    return result

