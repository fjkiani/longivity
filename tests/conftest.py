"""
Shared pytest fixtures for longivity test suite.

Variants format for full_assessment:
  {rsid: {"genotype": "XX"}}  ← nested dict (what genetic_annotator.annotate_apoe expects)
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from longivity.app import app

BASE = "/api/v1/longevity"


@pytest.fixture(scope="session")
def client():
    """FastAPI test client (session-scoped for speed)."""
    return TestClient(app)


@pytest.fixture(scope="session")
def base():
    """API base path."""
    return BASE


# ─────────────────────────────────────────────────────────────────────────────
# Canonical biomarker payloads
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def healthy_biomarkers():
    """Full 9-biomarker healthy panel — PhenoAge should be ~34 for age 45."""
    return {
        "albumin": 4.8,
        "creatinine": 0.85,
        "glucose_mg_dl": 88.0,
        "crp_mg_l": 0.4,
        "lymphocyte_percent": 32.0,
        "mcv": 88.0,
        "rdw": 12.5,
        "alkaline_phosphatase": 55.0,
        "wbc": 5.2,
    }


@pytest.fixture
def accelerated_biomarkers():
    """Full 9-biomarker accelerated-aging panel — PhenoAge ~77 for age 58."""
    return {
        "albumin": 3.5,
        "creatinine": 1.4,
        "glucose_mg_dl": 118.0,
        "crp_mg_l": 4.8,
        "lymphocyte_percent": 18.0,
        "mcv": 96.0,
        "rdw": 15.2,
        "alkaline_phosphatase": 110.0,
        "wbc": 9.8,
    }


@pytest.fixture
def partial_biomarkers():
    """Partial panel (5/9) — returns component linear terms but not full PhenoAge estimate."""
    return {
        "albumin": 4.5,
        "creatinine": 0.9,
        "glucose_mg_dl": 92.0,
        "crp_mg_l": 0.8,
        "wbc": 5.8,
    }


@pytest.fixture
def lipid_biomarkers():
    """Lipid panel for cardiovascular risk testing."""
    return {
        "total_cholesterol": 210.0,
        "hdl_cholesterol": 45.0,
        "ldl_cholesterol": 130.0,
        "triglycerides": 175.0,
        "systolic_bp": 130.0,
    }


@pytest.fixture
def full_assessment_payload(healthy_biomarkers, lipid_biomarkers):
    """Full assessment payload combining biomarkers + lipids + age."""
    return {
        "age": 45,
        "sex": "male",
        "biomarkers": {**healthy_biomarkers, **lipid_biomarkers},
    }


@pytest.fixture
def apoe_variants():
    """
    APOE e3/e4 variant set in nested format expected by genetic_annotator.
    Format: {rsid: {"genotype": "XX"}}
    rs429358=CT + rs7412=CC → e3/e4
    """
    return {
        "rs429358": {"genotype": "CT"},
        "rs7412": {"genotype": "CC"},
    }


@pytest.fixture
def mthfr_variants():
    """
    MTHFR compound heterozygous variant set in nested format.
    Format: {rsid: {"genotype": "XX"}}
    rs1801133=CT (C677T het) + rs1801131=AC (A1298C het) → compound het
    """
    return {
        "rs1801133": {"genotype": "CT"},
        "rs1801131": {"genotype": "AC"},
    }
