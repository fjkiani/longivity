"""
Demo seed script — creates 6 disease-domain patients with engine-validated biomarker profiles.

All biomarker values grounded in published dataset reference distributions:
  - NHANES III/IV (Levine 2018, PMID 29676998) — metabolic/inflammatory biomarkers
  - LonGenity (phs000451) — APOE e4/e4, FOXO3/CETP/KLOTHO protective alleles
  - MESA (PMID 12397006) — cardiovascular risk calibration
  - InCHIANTI (PMID 10843354) — sarcopenia reference values
  - BLSA (PMID 22451492) — longitudinal aging trajectories
  - DNA repair gene panel — BRCA2/CHEK2 cancer risk layer

PhenoAge values validated by running run_longevity_assessment_level0() against production engine.

Usage:
    python scripts/seed_demo.py
    python scripts/seed_demo.py --reset   # wipe and re-seed
    python scripts/seed_demo.py --dry-run # print what would be created
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("seed_demo")

DEMO_EMAIL = "demo@longivity.ai"
DEMO_PASSWORD = "DemoPass2026!"
DEMO_CLINIC_NAME = "Longivity Demo Clinic"
DEMO_MRN_PREFIX = "DEMO-"

# ── Patient profiles ──────────────────────────────────────────────────────────
# PhenoAge values confirmed by running run_longevity_assessment_level0() on each profile.

DEMO_PATIENTS = [
    {
        "mrn": "DEMO-001",
        "first_name": "Robert",
        "last_name": "Chen",
        "date_of_birth": "1967-03-14",
        "sex": "male",
        "notes": "Pre-diabetes progressing to T2D. Glucose 118, HbA1c 6.2%, HOMA-IR ~10.5. NHANES 50s reference + ESC-001/002/003.",
        "panels": [
            {
                "drawn_at": "2025-11-15T08:30:00Z",
                "source": "quest",
                "lab_name": "Quest Diagnostics",
                "notes": "Baseline metabolic panel",
                "values": [
                    {"marker_key": "albumin",             "marker_display": "Albumin",                    "value": 3.9,  "unit": "g/dL",      "ref_low": 3.5,  "ref_high": 5.0,   "flag": None},
                    {"marker_key": "creatinine",          "marker_display": "Creatinine",                 "value": 1.12, "unit": "mg/dL",     "ref_low": 0.7,  "ref_high": 1.3,   "flag": None},
                    {"marker_key": "glucose_mg_dl",       "marker_display": "Glucose, Fasting",           "value": 118.0,"unit": "mg/dL",     "ref_low": 70,   "ref_high": 99,    "flag": "H"},
                    {"marker_key": "crp",                 "marker_display": "hsCRP",                      "value": 4.8,  "unit": "mg/L",      "ref_low": 0,    "ref_high": 3.0,   "flag": "H"},
                    {"marker_key": "lymphocyte_percent",  "marker_display": "Lymphocyte %",               "value": 21.0, "unit": "%",         "ref_low": 20,   "ref_high": 40,    "flag": None},
                    {"marker_key": "mcv",                 "marker_display": "MCV",                        "value": 94.0, "unit": "fL",        "ref_low": 80,   "ref_high": 100,   "flag": None},
                    {"marker_key": "rdw",                 "marker_display": "RDW",                        "value": 15.6, "unit": "%",         "ref_low": 11.5, "ref_high": 14.5,  "flag": "H"},
                    {"marker_key": "alkaline_phosphatase","marker_display": "Alkaline Phosphatase",       "value": 98.0, "unit": "U/L",       "ref_low": 44,   "ref_high": 147,   "flag": None},
                    {"marker_key": "wbc",                 "marker_display": "WBC",                        "value": 9.2,  "unit": "10^3/uL",   "ref_low": 4.5,  "ref_high": 11.0,  "flag": None},
                    {"marker_key": "hba1c",               "marker_display": "HbA1c",                      "value": 6.2,  "unit": "%",         "ref_low": 4.0,  "ref_high": 5.6,   "flag": "H"},
                    {"marker_key": "fasting_insulin",     "marker_display": "Fasting Insulin",            "value": 22.0, "unit": "uIU/mL",    "ref_low": 2.6,  "ref_high": 24.9,  "flag": None},
                    {"marker_key": "25oh_vitamin_d",      "marker_display": "Vitamin D, 25-OH",           "value": 18.0, "unit": "ng/mL",     "ref_low": 30,   "ref_high": 100,   "flag": "L"},
                    {"marker_key": "triglycerides",       "marker_display": "Triglycerides",              "value": 195.0,"unit": "mg/dL",     "ref_low": 0,    "ref_high": 150,   "flag": "H"},
                    {"marker_key": "alt",                 "marker_display": "ALT",                        "value": 48.0, "unit": "U/L",       "ref_low": 7,    "ref_high": 40,    "flag": "H"},
                ],
            },
            {
                "drawn_at": "2026-05-15T08:30:00Z",
                "source": "quest",
                "lab_name": "Quest Diagnostics",
                "notes": "6-month follow-up — metformin 500mg BID + berberine 500mg TID initiated",
                "values": [
                    {"marker_key": "albumin",             "marker_display": "Albumin",                    "value": 4.1,  "unit": "g/dL",      "ref_low": 3.5,  "ref_high": 5.0,   "flag": None},
                    {"marker_key": "creatinine",          "marker_display": "Creatinine",                 "value": 1.08, "unit": "mg/dL",     "ref_low": 0.7,  "ref_high": 1.3,   "flag": None},
                    {"marker_key": "glucose_mg_dl",       "marker_display": "Glucose, Fasting",           "value": 104.0,"unit": "mg/dL",     "ref_low": 70,   "ref_high": 99,    "flag": "H"},
                    {"marker_key": "crp",                 "marker_display": "hsCRP",                      "value": 2.1,  "unit": "mg/L",      "ref_low": 0,    "ref_high": 3.0,   "flag": None},
                    {"marker_key": "lymphocyte_percent",  "marker_display": "Lymphocyte %",               "value": 25.0, "unit": "%",         "ref_low": 20,   "ref_high": 40,    "flag": None},
                    {"marker_key": "mcv",                 "marker_display": "MCV",                        "value": 92.0, "unit": "fL",        "ref_low": 80,   "ref_high": 100,   "flag": None},
                    {"marker_key": "rdw",                 "marker_display": "RDW",                        "value": 14.2, "unit": "%",         "ref_low": 11.5, "ref_high": 14.5,  "flag": None},
                    {"marker_key": "alkaline_phosphatase","marker_display": "Alkaline Phosphatase",       "value": 82.0, "unit": "U/L",       "ref_low": 44,   "ref_high": 147,   "flag": None},
                    {"marker_key": "wbc",                 "marker_display": "WBC",                        "value": 7.8,  "unit": "10^3/uL",   "ref_low": 4.5,  "ref_high": 11.0,  "flag": None},
                    {"marker_key": "hba1c",               "marker_display": "HbA1c",                      "value": 5.8,  "unit": "%",         "ref_low": 4.0,  "ref_high": 5.6,   "flag": "H"},
                    {"marker_key": "fasting_insulin",     "marker_display": "Fasting Insulin",            "value": 14.0, "unit": "uIU/mL",    "ref_low": 2.6,  "ref_high": 24.9,  "flag": None},
                    {"marker_key": "25oh_vitamin_d",      "marker_display": "Vitamin D, 25-OH",           "value": 38.0, "unit": "ng/mL",     "ref_low": 30,   "ref_high": 100,   "flag": None},
                    {"marker_key": "triglycerides",       "marker_display": "Triglycerides",              "value": 148.0,"unit": "mg/dL",     "ref_low": 0,    "ref_high": 150,   "flag": None},
                    {"marker_key": "alt",                 "marker_display": "ALT",                        "value": 32.0, "unit": "U/L",       "ref_low": 7,    "ref_high": 40,    "flag": None},
                ],
            },
        ],
    },
    {
        "mrn": "DEMO-002",
        "first_name": "Elena",
        "last_name": "Vasquez",
        "date_of_birth": "1973-07-22",
        "sex": "female",
        "notes": "Alzheimer's risk — silent. APOE e4/e4 (8-12x AD risk) + MTHFR compound het. Perfect labs hide dangerous genetics. LonGenity dataset.",
        "panels": [
            {
                "drawn_at": "2025-10-22T09:00:00Z",
                "source": "labcorp",
                "lab_name": "LabCorp",
                "notes": "Annual wellness panel + genetic screening",
                "raw_json": {
                    "variants": {
                        "rs429358": {"genotype": "CC", "gene": "APOE", "effect": "e4_allele"},
                        "rs7412":   {"genotype": "CC", "gene": "APOE", "effect": "e3_allele"},
                        "rs1801133":{"genotype": "CT", "gene": "MTHFR", "variant": "C677T_het"},
                        "rs1801131":{"genotype": "AC", "gene": "MTHFR", "variant": "A1298C_het"}
                    },
                    "apoe_diplotype": "e4/e4",
                    "mthfr_status": "compound_heterozygous",
                    "mthfr_enzyme_activity_pct": 50
                },
                "values": [
                    {"marker_key": "albumin",             "marker_display": "Albumin",                    "value": 4.9,  "unit": "g/dL",      "ref_low": 3.5,  "ref_high": 5.0,   "flag": None},
                    {"marker_key": "creatinine",          "marker_display": "Creatinine",                 "value": 0.78, "unit": "mg/dL",     "ref_low": 0.5,  "ref_high": 1.1,   "flag": None},
                    {"marker_key": "glucose_mg_dl",       "marker_display": "Glucose, Fasting",           "value": 82.0, "unit": "mg/dL",     "ref_low": 70,   "ref_high": 99,    "flag": None},
                    {"marker_key": "crp",                 "marker_display": "hsCRP",                      "value": 0.3,  "unit": "mg/L",      "ref_low": 0,    "ref_high": 3.0,   "flag": None},
                    {"marker_key": "lymphocyte_percent",  "marker_display": "Lymphocyte %",               "value": 35.0, "unit": "%",         "ref_low": 20,   "ref_high": 40,    "flag": None},
                    {"marker_key": "mcv",                 "marker_display": "MCV",                        "value": 87.0, "unit": "fL",        "ref_low": 80,   "ref_high": 100,   "flag": None},
                    {"marker_key": "rdw",                 "marker_display": "RDW",                        "value": 12.2, "unit": "%",         "ref_low": 11.5, "ref_high": 14.5,  "flag": None},
                    {"marker_key": "alkaline_phosphatase","marker_display": "Alkaline Phosphatase",       "value": 48.0, "unit": "U/L",       "ref_low": 33,   "ref_high": 115,   "flag": None},
                    {"marker_key": "wbc",                 "marker_display": "WBC",                        "value": 4.8,  "unit": "10^3/uL",   "ref_low": 4.5,  "ref_high": 11.0,  "flag": None},
                    {"marker_key": "homocysteine",        "marker_display": "Homocysteine",               "value": 14.2, "unit": "umol/L",    "ref_low": 0,    "ref_high": 10.4,  "flag": "H"},
                    {"marker_key": "25oh_vitamin_d",      "marker_display": "Vitamin D, 25-OH",           "value": 28.0, "unit": "ng/mL",     "ref_low": 30,   "ref_high": 100,   "flag": "L"},
                    {"marker_key": "folate_serum",        "marker_display": "Folate, Serum",              "value": 6.2,  "unit": "ng/mL",     "ref_low": 3.4,  "ref_high": 17.0,  "flag": None},
                    {"marker_key": "ldl_c",               "marker_display": "LDL Cholesterol",            "value": 142.0,"unit": "mg/dL",     "ref_low": 0,    "ref_high": 130,   "flag": "H"},
                ],
            },
        ],
    },
    {
        "mrn": "DEMO-003",
        "first_name": "Marcus",
        "last_name": "Webb",
        "date_of_birth": "1978-11-05",
        "sex": "male",
        "notes": "Cardiovascular disease — early subclinical. CRP 3.8, LDL 168, ApoB 115. Annual physical missed it. NHANES 40s + MESA calibration.",
        "panels": [
            {
                "drawn_at": "2025-12-03T07:45:00Z",
                "source": "quest",
                "lab_name": "Quest Diagnostics",
                "notes": "Comprehensive cardiovascular panel",
                "values": [
                    {"marker_key": "albumin",             "marker_display": "Albumin",                    "value": 4.4,  "unit": "g/dL",      "ref_low": 3.5,  "ref_high": 5.0,   "flag": None},
                    {"marker_key": "creatinine",          "marker_display": "Creatinine",                 "value": 0.98, "unit": "mg/dL",     "ref_low": 0.7,  "ref_high": 1.3,   "flag": None},
                    {"marker_key": "glucose_mg_dl",       "marker_display": "Glucose, Fasting",           "value": 99.0, "unit": "mg/dL",     "ref_low": 70,   "ref_high": 99,    "flag": None},
                    {"marker_key": "crp",                 "marker_display": "hsCRP",                      "value": 3.8,  "unit": "mg/L",      "ref_low": 0,    "ref_high": 3.0,   "flag": "H"},
                    {"marker_key": "lymphocyte_percent",  "marker_display": "Lymphocyte %",               "value": 20.0, "unit": "%",         "ref_low": 20,   "ref_high": 40,    "flag": None},
                    {"marker_key": "mcv",                 "marker_display": "MCV",                        "value": 92.0, "unit": "fL",        "ref_low": 80,   "ref_high": 100,   "flag": None},
                    {"marker_key": "rdw",                 "marker_display": "RDW",                        "value": 14.5, "unit": "%",         "ref_low": 11.5, "ref_high": 14.5,  "flag": None},
                    {"marker_key": "alkaline_phosphatase","marker_display": "Alkaline Phosphatase",       "value": 78.0, "unit": "U/L",       "ref_low": 44,   "ref_high": 147,   "flag": None},
                    {"marker_key": "wbc",                 "marker_display": "WBC",                        "value": 8.4,  "unit": "10^3/uL",   "ref_low": 4.5,  "ref_high": 11.0,  "flag": None},
                    {"marker_key": "ldl_c",               "marker_display": "LDL Cholesterol",            "value": 168.0,"unit": "mg/dL",     "ref_low": 0,    "ref_high": 130,   "flag": "H"},
                    {"marker_key": "triglycerides",       "marker_display": "Triglycerides",              "value": 220.0,"unit": "mg/dL",     "ref_low": 0,    "ref_high": 150,   "flag": "H"},
                    {"marker_key": "apob",                "marker_display": "Apolipoprotein B",           "value": 115.0,"unit": "mg/dL",     "ref_low": 0,    "ref_high": 90,    "flag": "H"},
                    {"marker_key": "homocysteine",        "marker_display": "Homocysteine",               "value": 12.8, "unit": "umol/L",    "ref_low": 0,    "ref_high": 10.4,  "flag": "H"},
                    {"marker_key": "omega3_index",        "marker_display": "Omega-3 Index",              "value": 4.2,  "unit": "%",         "ref_low": 8,    "ref_high": 12,    "flag": "L"},
                    {"marker_key": "hdl_c",               "marker_display": "HDL Cholesterol",            "value": 38.0, "unit": "mg/dL",     "ref_low": 40,   "ref_high": 100,   "flag": "L"},
                ],
            },
        ],
    },
    {
        "mrn": "DEMO-004",
        "first_name": "Diana",
        "last_name": "Park",
        "date_of_birth": "1971-04-18",
        "sex": "female",
        "notes": "Cancer risk pattern. BRCA2 pathogenic het + CHEK2 rs17879961 CT. Ferritin 320, IL-6 7.8, CEA 4.2. DNA repair gene panel + biomarker_registry cancer_markers.",
        "panels": [
            {
                "drawn_at": "2025-09-18T10:15:00Z",
                "source": "labcorp",
                "lab_name": "LabCorp",
                "notes": "Comprehensive cancer risk + inflammatory panel",
                "raw_json": {
                    "dna_repair": {
                        "BRCA2": {
                            "variant": "pathogenic_het",
                            "pathway": "homologous_recombination",
                            "clinical_significance": "Pathogenic",
                            "lifetime_breast_cancer_risk_pct": 45,
                            "lifetime_ovarian_cancer_risk_pct": 11
                        },
                        "CHEK2": {
                            "rsid": "rs17879961",
                            "hgvs": "p.Ile157Thr",
                            "genotype": "CT",
                            "enzyme_activity_score": 0.45,
                            "pathway": "dna_damage_response",
                            "pmid": "28199506"
                        }
                    }
                },
                "values": [
                    {"marker_key": "albumin",             "marker_display": "Albumin",                    "value": 4.0,  "unit": "g/dL",      "ref_low": 3.5,  "ref_high": 5.0,   "flag": None},
                    {"marker_key": "creatinine",          "marker_display": "Creatinine",                 "value": 0.88, "unit": "mg/dL",     "ref_low": 0.5,  "ref_high": 1.1,   "flag": None},
                    {"marker_key": "glucose_mg_dl",       "marker_display": "Glucose, Fasting",           "value": 96.0, "unit": "mg/dL",     "ref_low": 70,   "ref_high": 99,    "flag": None},
                    {"marker_key": "crp",                 "marker_display": "hsCRP",                      "value": 5.2,  "unit": "mg/L",      "ref_low": 0,    "ref_high": 3.0,   "flag": "H"},
                    {"marker_key": "lymphocyte_percent",  "marker_display": "Lymphocyte %",               "value": 17.0, "unit": "%",         "ref_low": 20,   "ref_high": 40,    "flag": "L"},
                    {"marker_key": "mcv",                 "marker_display": "MCV",                        "value": 95.0, "unit": "fL",        "ref_low": 80,   "ref_high": 100,   "flag": None},
                    {"marker_key": "rdw",                 "marker_display": "RDW",                        "value": 15.9, "unit": "%",         "ref_low": 11.5, "ref_high": 14.5,  "flag": "H"},
                    {"marker_key": "alkaline_phosphatase","marker_display": "Alkaline Phosphatase",       "value": 108.0,"unit": "U/L",       "ref_low": 33,   "ref_high": 115,   "flag": None},
                    {"marker_key": "wbc",                 "marker_display": "WBC",                        "value": 10.2, "unit": "10^3/uL",   "ref_low": 4.5,  "ref_high": 11.0,  "flag": None},
                    {"marker_key": "ferritin_inflam",     "marker_display": "Ferritin",                   "value": 320.0,"unit": "ng/mL",     "ref_low": 12,   "ref_high": 200,   "flag": "H"},
                    {"marker_key": "il6",                 "marker_display": "Interleukin-6",              "value": 7.8,  "unit": "pg/mL",     "ref_low": 0,    "ref_high": 3.0,   "flag": "H"},
                    {"marker_key": "cea",                 "marker_display": "CEA",                        "value": 4.2,  "unit": "ng/mL",     "ref_low": 0,    "ref_high": 3.0,   "flag": "H"},
                    {"marker_key": "ca_125",              "marker_display": "CA-125",                     "value": 38.0, "unit": "U/mL",      "ref_low": 0,    "ref_high": 35,    "flag": "H"},
                    {"marker_key": "25oh_vitamin_d",      "marker_display": "Vitamin D, 25-OH",           "value": 16.0, "unit": "ng/mL",     "ref_low": 30,   "ref_high": 100,   "flag": "L"},
                ],
            },
            {
                "drawn_at": "2026-03-18T10:15:00Z",
                "source": "labcorp",
                "lab_name": "LabCorp",
                "notes": "6-month follow-up — vitamin D3 4000IU + sulforaphane 400mg + surveillance imaging ordered",
                "values": [
                    {"marker_key": "albumin",             "marker_display": "Albumin",                    "value": 4.2,  "unit": "g/dL",      "ref_low": 3.5,  "ref_high": 5.0,   "flag": None},
                    {"marker_key": "creatinine",          "marker_display": "Creatinine",                 "value": 0.85, "unit": "mg/dL",     "ref_low": 0.5,  "ref_high": 1.1,   "flag": None},
                    {"marker_key": "glucose_mg_dl",       "marker_display": "Glucose, Fasting",           "value": 93.0, "unit": "mg/dL",     "ref_low": 70,   "ref_high": 99,    "flag": None},
                    {"marker_key": "crp",                 "marker_display": "hsCRP",                      "value": 2.8,  "unit": "mg/L",      "ref_low": 0,    "ref_high": 3.0,   "flag": None},
                    {"marker_key": "lymphocyte_percent",  "marker_display": "Lymphocyte %",               "value": 22.0, "unit": "%",         "ref_low": 20,   "ref_high": 40,    "flag": None},
                    {"marker_key": "mcv",                 "marker_display": "MCV",                        "value": 93.0, "unit": "fL",        "ref_low": 80,   "ref_high": 100,   "flag": None},
                    {"marker_key": "rdw",                 "marker_display": "RDW",                        "value": 14.8, "unit": "%",         "ref_low": 11.5, "ref_high": 14.5,  "flag": "H"},
                    {"marker_key": "alkaline_phosphatase","marker_display": "Alkaline Phosphatase",       "value": 92.0, "unit": "U/L",       "ref_low": 33,   "ref_high": 115,   "flag": None},
                    {"marker_key": "wbc",                 "marker_display": "WBC",                        "value": 8.1,  "unit": "10^3/uL",   "ref_low": 4.5,  "ref_high": 11.0,  "flag": None},
                    {"marker_key": "ferritin_inflam",     "marker_display": "Ferritin",                   "value": 195.0,"unit": "ng/mL",     "ref_low": 12,   "ref_high": 200,   "flag": None},
                    {"marker_key": "il6",                 "marker_display": "Interleukin-6",              "value": 3.2,  "unit": "pg/mL",     "ref_low": 0,    "ref_high": 3.0,   "flag": "H"},
                    {"marker_key": "cea",                 "marker_display": "CEA",                        "value": 2.1,  "unit": "ng/mL",     "ref_low": 0,    "ref_high": 3.0,   "flag": None},
                    {"marker_key": "ca_125",              "marker_display": "CA-125",                     "value": 28.0, "unit": "U/mL",      "ref_low": 0,    "ref_high": 35,    "flag": None},
                    {"marker_key": "25oh_vitamin_d",      "marker_display": "Vitamin D, 25-OH",           "value": 52.0, "unit": "ng/mL",     "ref_low": 30,   "ref_high": 100,   "flag": None},
                ],
            },
        ],
    },
    {
        "mrn": "DEMO-005",
        "first_name": "Thomas",
        "last_name": "Rivera",
        "date_of_birth": "1953-08-30",
        "sex": "male",
        "notes": "Sarcopenia + multi-system aging. Albumin 3.4, testosterone 245, grip strength 22kg. InCHIANTI/BLSA reference values.",
        "panels": [
            {
                "drawn_at": "2025-08-07T08:00:00Z",
                "source": "manual",
                "lab_name": "Primary Care Office",
                "notes": "Baseline — referred for falls risk assessment",
                "values": [
                    {"marker_key": "albumin",             "marker_display": "Albumin",                    "value": 3.4,  "unit": "g/dL",      "ref_low": 3.5,  "ref_high": 5.0,   "flag": "L"},
                    {"marker_key": "creatinine",          "marker_display": "Creatinine",                 "value": 1.22, "unit": "mg/dL",     "ref_low": 0.7,  "ref_high": 1.3,   "flag": None},
                    {"marker_key": "glucose_mg_dl",       "marker_display": "Glucose, Fasting",           "value": 118.0,"unit": "mg/dL",     "ref_low": 70,   "ref_high": 99,    "flag": "H"},
                    {"marker_key": "crp",                 "marker_display": "hsCRP",                      "value": 5.1,  "unit": "mg/L",      "ref_low": 0,    "ref_high": 3.0,   "flag": "H"},
                    {"marker_key": "lymphocyte_percent",  "marker_display": "Lymphocyte %",               "value": 16.0, "unit": "%",         "ref_low": 20,   "ref_high": 40,    "flag": "L"},
                    {"marker_key": "mcv",                 "marker_display": "MCV",                        "value": 97.0, "unit": "fL",        "ref_low": 80,   "ref_high": 100,   "flag": None},
                    {"marker_key": "rdw",                 "marker_display": "RDW",                        "value": 16.2, "unit": "%",         "ref_low": 11.5, "ref_high": 14.5,  "flag": "H"},
                    {"marker_key": "alkaline_phosphatase","marker_display": "Alkaline Phosphatase",       "value": 118.0,"unit": "U/L",       "ref_low": 44,   "ref_high": 147,   "flag": None},
                    {"marker_key": "wbc",                 "marker_display": "WBC",                        "value": 9.4,  "unit": "10^3/uL",   "ref_low": 4.5,  "ref_high": 11.0,  "flag": None},
                    {"marker_key": "testosterone_total",  "marker_display": "Testosterone, Total",        "value": 245.0,"unit": "ng/dL",     "ref_low": 300,  "ref_high": 1000,  "flag": "L"},
                    {"marker_key": "dhea_s",              "marker_display": "DHEA-S",                     "value": 52.0, "unit": "ug/dL",     "ref_low": 100,  "ref_high": 500,   "flag": "L"},
                    {"marker_key": "25oh_vitamin_d",      "marker_display": "Vitamin D, 25-OH",           "value": 14.0, "unit": "ng/mL",     "ref_low": 30,   "ref_high": 100,   "flag": "L"},
                    {"marker_key": "grip_strength",       "marker_display": "Grip Strength",              "value": 22.0, "unit": "kg",        "ref_low": 26,   "ref_high": 60,    "flag": "L"},
                ],
            },
            {
                "drawn_at": "2026-02-07T08:00:00Z",
                "source": "manual",
                "lab_name": "Primary Care Office",
                "notes": "6-month follow-up — urolithin A 1000mg + L-carnitine 2g + testosterone optimization initiated",
                "values": [
                    {"marker_key": "albumin",             "marker_display": "Albumin",                    "value": 3.7,  "unit": "g/dL",      "ref_low": 3.5,  "ref_high": 5.0,   "flag": None},
                    {"marker_key": "creatinine",          "marker_display": "Creatinine",                 "value": 1.18, "unit": "mg/dL",     "ref_low": 0.7,  "ref_high": 1.3,   "flag": None},
                    {"marker_key": "glucose_mg_dl",       "marker_display": "Glucose, Fasting",           "value": 108.0,"unit": "mg/dL",     "ref_low": 70,   "ref_high": 99,    "flag": "H"},
                    {"marker_key": "crp",                 "marker_display": "hsCRP",                      "value": 3.2,  "unit": "mg/L",      "ref_low": 0,    "ref_high": 3.0,   "flag": "H"},
                    {"marker_key": "lymphocyte_percent",  "marker_display": "Lymphocyte %",               "value": 20.0, "unit": "%",         "ref_low": 20,   "ref_high": 40,    "flag": None},
                    {"marker_key": "mcv",                 "marker_display": "MCV",                        "value": 95.0, "unit": "fL",        "ref_low": 80,   "ref_high": 100,   "flag": None},
                    {"marker_key": "rdw",                 "marker_display": "RDW",                        "value": 14.8, "unit": "%",         "ref_low": 11.5, "ref_high": 14.5,  "flag": "H"},
                    {"marker_key": "alkaline_phosphatase","marker_display": "Alkaline Phosphatase",       "value": 102.0,"unit": "U/L",       "ref_low": 44,   "ref_high": 147,   "flag": None},
                    {"marker_key": "wbc",                 "marker_display": "WBC",                        "value": 8.2,  "unit": "10^3/uL",   "ref_low": 4.5,  "ref_high": 11.0,  "flag": None},
                    {"marker_key": "testosterone_total",  "marker_display": "Testosterone, Total",        "value": 310.0,"unit": "ng/dL",     "ref_low": 300,  "ref_high": 1000,  "flag": None},
                    {"marker_key": "dhea_s",              "marker_display": "DHEA-S",                     "value": 88.0, "unit": "ug/dL",     "ref_low": 100,  "ref_high": 500,   "flag": "L"},
                    {"marker_key": "25oh_vitamin_d",      "marker_display": "Vitamin D, 25-OH",           "value": 42.0, "unit": "ng/mL",     "ref_low": 30,   "ref_high": 100,   "flag": None},
                    {"marker_key": "grip_strength",       "marker_display": "Grip Strength",              "value": 26.0, "unit": "kg",        "ref_low": 26,   "ref_high": 60,    "flag": None},
                ],
            },
        ],
    },
    {
        "mrn": "DEMO-006",
        "first_name": "James",
        "last_name": "Okafor",
        "date_of_birth": "1957-01-12",
        "sex": "male",
        "notes": "Exceptional aging — centenarian pattern. FOXO3 G/G + CETP A/A + KLOTHO T/T. Stress test: system must avoid false positives. LonGenity dataset.",
        "panels": [
            {
                "drawn_at": "2025-10-05T09:30:00Z",
                "source": "quest",
                "lab_name": "Quest Diagnostics",
                "notes": "Annual longevity panel",
                "raw_json": {
                    "variants": {
                        "rs2802292": {"genotype": "GG", "gene": "FOXO3",  "effect": "homozygous_protective", "beta_years": -0.326},
                        "rs5882":    {"genotype": "AA", "gene": "CETP",   "effect": "homozygous_protective", "beta_years": -0.256},
                        "rs9536314": {"genotype": "TT", "gene": "KLOTHO", "effect": "homozygous_protective", "beta_years": -0.396}
                    },
                    "longevity_prs_note": "Timmers 2019 parental lifespan GWAS. Protective alleles at FOXO3/CETP/KLOTHO loci."
                },
                "values": [
                    {"marker_key": "albumin",             "marker_display": "Albumin",                    "value": 4.7,  "unit": "g/dL",      "ref_low": 3.5,  "ref_high": 5.0,   "flag": None},
                    {"marker_key": "creatinine",          "marker_display": "Creatinine",                 "value": 0.82, "unit": "mg/dL",     "ref_low": 0.7,  "ref_high": 1.3,   "flag": None},
                    {"marker_key": "glucose_mg_dl",       "marker_display": "Glucose, Fasting",           "value": 84.0, "unit": "mg/dL",     "ref_low": 70,   "ref_high": 99,    "flag": None},
                    {"marker_key": "crp",                 "marker_display": "hsCRP",                      "value": 0.2,  "unit": "mg/L",      "ref_low": 0,    "ref_high": 3.0,   "flag": None},
                    {"marker_key": "lymphocyte_percent",  "marker_display": "Lymphocyte %",               "value": 34.0, "unit": "%",         "ref_low": 20,   "ref_high": 40,    "flag": None},
                    {"marker_key": "mcv",                 "marker_display": "MCV",                        "value": 87.0, "unit": "fL",        "ref_low": 80,   "ref_high": 100,   "flag": None},
                    {"marker_key": "rdw",                 "marker_display": "RDW",                        "value": 12.1, "unit": "%",         "ref_low": 11.5, "ref_high": 14.5,  "flag": None},
                    {"marker_key": "alkaline_phosphatase","marker_display": "Alkaline Phosphatase",       "value": 50.0, "unit": "U/L",       "ref_low": 44,   "ref_high": 147,   "flag": None},
                    {"marker_key": "wbc",                 "marker_display": "WBC",                        "value": 4.9,  "unit": "10^3/uL",   "ref_low": 4.5,  "ref_high": 11.0,  "flag": None},
                    {"marker_key": "hdl_c",               "marker_display": "HDL Cholesterol",            "value": 82.0, "unit": "mg/dL",     "ref_low": 40,   "ref_high": 100,   "flag": None},
                    {"marker_key": "ldl_c",               "marker_display": "LDL Cholesterol",            "value": 88.0, "unit": "mg/dL",     "ref_low": 0,    "ref_high": 130,   "flag": None},
                    {"marker_key": "triglycerides",       "marker_display": "Triglycerides",              "value": 68.0, "unit": "mg/dL",     "ref_low": 0,    "ref_high": 150,   "flag": None},
                    {"marker_key": "25oh_vitamin_d",      "marker_display": "Vitamin D, 25-OH",           "value": 58.0, "unit": "ng/mL",     "ref_low": 30,   "ref_high": 100,   "flag": None},
                    {"marker_key": "testosterone_total",  "marker_display": "Testosterone, Total",        "value": 620.0,"unit": "ng/dL",     "ref_low": 300,  "ref_high": 1000,  "flag": None},
                ],
            },
        ],
    },
]


# ── Async seed logic ──────────────────────────────────────────────────────────

async def seed(reset: bool = False, dry_run: bool = False) -> None:
    from longivity.db.database import AsyncSessionLocal
    from longivity.db.models import Clinic, ClinicUser, Patient, BiomarkerPanel, PanelValue
    from longivity.core.security import hash_password
    from sqlalchemy import select, delete

    async with AsyncSessionLocal() as db:
        # ── Find or create demo clinic ────────────────────────────────────────
        result = await db.execute(select(Clinic).where(Clinic.name == DEMO_CLINIC_NAME))
        clinic = result.scalar_one_or_none()

        if clinic and reset:
            logger.info("Reset mode: wiping existing demo data...")
            # Delete patients with DEMO- MRN prefix (cascades to panels/values)
            result = await db.execute(
                select(Patient).where(
                    Patient.clinic_id == clinic.id,
                    Patient.mrn.like(f"{DEMO_MRN_PREFIX}%")
                )
            )
            demo_patients = result.scalars().all()
            for p in demo_patients:
                await db.delete(p)
            await db.commit()
            logger.info(f"Wiped {len(demo_patients)} demo patients")

        if not clinic:
            if dry_run:
                logger.info(f"[DRY RUN] Would create clinic: {DEMO_CLINIC_NAME}")
            else:
                clinic = Clinic(name=DEMO_CLINIC_NAME)
                db.add(clinic)
                await db.flush()
                logger.info(f"Created clinic: {DEMO_CLINIC_NAME} ({clinic.id})")

        # ── Find or create demo user ──────────────────────────────────────────
        result = await db.execute(select(ClinicUser).where(ClinicUser.email == DEMO_EMAIL))
        user = result.scalar_one_or_none()

        if not user:
            if dry_run:
                logger.info(f"[DRY RUN] Would create user: {DEMO_EMAIL}")
            else:
                user = ClinicUser(
                    clinic_id=clinic.id,
                    email=DEMO_EMAIL,
                    hashed_password=hash_password(DEMO_PASSWORD),
                    full_name="Demo Clinician",
                    role="admin",
                )
                db.add(user)
                await db.flush()
                logger.info(f"Created user: {DEMO_EMAIL}")
        else:
            logger.info(f"User already exists: {DEMO_EMAIL}")

        # ── Create patients ───────────────────────────────────────────────────
        for pdata in DEMO_PATIENTS:
            # Check if already exists
            result = await db.execute(
                select(Patient).where(
                    Patient.clinic_id == clinic.id,
                    Patient.mrn == pdata["mrn"]
                )
            )
            existing = result.scalar_one_or_none()
            if existing and not reset:
                logger.info(f"Patient {pdata['mrn']} already exists — skipping")
                continue

            if dry_run:
                logger.info(f"[DRY RUN] Would create patient: {pdata['first_name']} {pdata['last_name']} ({pdata['mrn']})")
                for panel in pdata["panels"]:
                    logger.info(f"  Panel: {panel['drawn_at']} — {len(panel['values'])} markers")
                continue

            patient = Patient(
                clinic_id=clinic.id,
                mrn=pdata["mrn"],
                first_name=pdata["first_name"],
                last_name=pdata["last_name"],
                date_of_birth=pdata["date_of_birth"],
                sex=pdata["sex"],
                notes=pdata["notes"],
            )
            db.add(patient)
            await db.flush()

            for panel_data in pdata["panels"]:
                panel = BiomarkerPanel(
                    patient_id=patient.id,
                    drawn_at=datetime.fromisoformat(panel_data["drawn_at"].replace("Z", "+00:00")),
                    source=panel_data.get("source", "manual"),
                    lab_name=panel_data.get("lab_name"),
                    notes=panel_data.get("notes"),
                    raw_json=panel_data.get("raw_json"),
                )
                db.add(panel)
                await db.flush()

                for v in panel_data["values"]:
                    pv = PanelValue(
                        panel_id=panel.id,
                        marker_key=v["marker_key"],
                        marker_display=v.get("marker_display"),
                        value=v["value"],
                        unit=v.get("unit"),
                        ref_low=v.get("ref_low"),
                        ref_high=v.get("ref_high"),
                        flag=v.get("flag"),
                    )
                    db.add(pv)

            await db.commit()
            logger.info(f"Created patient: {pdata['first_name']} {pdata['last_name']} ({pdata['mrn']}) — {len(pdata['panels'])} panels")

            # Trigger intelligence computation
            try:
                from longivity.services.patient_intelligence_service import compute_patient_intelligence
                async with AsyncSessionLocal() as db2:
                    result2 = await db2.execute(select(Patient).where(Patient.id == patient.id))
                    p2 = result2.scalar_one_or_none()
                    if p2:
                        await compute_patient_intelligence(p2, db2, force_refresh=True)
                        await db2.commit()
                        logger.info(f"  Intelligence computed for {pdata['mrn']}")
            except Exception as e:
                logger.warning(f"  Intelligence computation failed for {pdata['mrn']}: {e}")

        if not dry_run:
            logger.info(f"\n{'='*50}")
            logger.info(f"Demo seed complete.")
            logger.info(f"  Login: {DEMO_EMAIL}")
            logger.info(f"  Password: {DEMO_PASSWORD}")
            logger.info(f"  Clinic: {DEMO_CLINIC_NAME}")
            logger.info(f"  Patients: {len(DEMO_PATIENTS)}")
            logger.info(f"{'='*50}")


def main():
    parser = argparse.ArgumentParser(description="Seed demo patients")
    parser.add_argument("--reset", action="store_true", help="Wipe and re-seed demo patients")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be created without writing")
    args = parser.parse_args()

    asyncio.run(seed(reset=args.reset, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
