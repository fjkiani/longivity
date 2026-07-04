"""
Canonical disease cohort patient archetypes for Longivity product validation.

Five real disease cohorts. Each archetype is a typed payload that runs through
the live system. All biomarker values are clinically plausible for the stated
disease context. All expected findings are verified against live system outputs.

Cohorts:
  1. Marcus  — Type 2 Diabetes / Metabolic Syndrome (58M)
  2. Robert  — Cardiovascular Disease / Atherosclerosis Risk (63M)
  3. Elena   — Alzheimer's Risk / APOE e4/e4 + MTHFR compound het (52F)
  4. Dorothy — Accelerated Aging / Sarcopenia + Frailty (71F)
  5. James   — Longevity Optimization / Centenarian Trajectory (68M)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PatientArchetype:
    id: str
    name: str
    age: int
    sex: str
    disease_context: str
    clinical_story: str
    stress_test: str
    payload: Dict[str, Any]
    expected_findings: List[str]
    # Assertions: (field_path, operator, value)
    # field_path uses dot notation: "phenoage_analysis.phenoage_estimate"
    assertions: List[Dict[str, Any]] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Cohort 1: Type 2 Diabetes / Metabolic Syndrome
# ─────────────────────────────────────────────────────────────────────────────
MARCUS = PatientArchetype(
    id="marcus_t2d",
    name="Marcus",
    age=58,
    sex="M",
    disease_context="Type 2 Diabetes / Metabolic Syndrome",
    clinical_story=(
        "58-year-old male. A1c 7.8%, fasting insulin 22 µU/mL, glucose 142 mg/dL. "
        "GP said 'watch your diet.' PhenoAge catches 15+ years of hidden biological aging. "
        "Glucose is the #1 PhenoAge accelerator by coefficient (0.1953, PMID 29676998). "
        "System must rank Metformin (MR_VALIDATED, IVW p=0.02) above Berberine (RCT)."
    ),
    stress_test=(
        "Does the system catch 15+ years of biological aging in a patient whose GP said "
        "'A1c is a bit high'? Does MR_VALIDATED rank above RCT for same hallmark?"
    ),
    payload={
        "age": 58,
        "sex": "M",
        "biomarkers": {
            "albumin": 4.0,
            "creatinine": 1.1,
            "glucose_mg_dl": 142.0,
            "crp_mg_l": 4.8,
            "lymphocyte_percent": 21.0,
            "mcv": 94.0,
            "rdw": 15.2,
            "alkaline_phosphatase": 95.0,
            "wbc": 9.2,
            "hba1c_percent": 7.8,
            "fasting_insulin": 22.0,
            "25oh_vitamin_d": 19.0,
        },
        "compound_queries": ["metformin", "berberine", "omega_3", "vitamin_d3", "nmn", "taurine"],
    },
    expected_findings=[
        "PhenoAge > 70yr (acceleration > 12yr)",
        "nutrient_sensing hallmark active (glucose coefficient 0.1953)",
        "altered_intercellular_communication hallmark active (CRP 4.8)",
        "Metformin tier=MR_VALIDATED (Dugué 2021, PMID 34385711)",
        "Berberine tier=RCT (PMID 34956436)",
        "10yr mortality > 25%",
    ],
    assertions=[
        {"path": "phenoage_analysis.phenoage_estimate", "op": "gt", "value": 70.0, "label": "PhenoAge > 70yr"},
        {"path": "phenoage_analysis.age_acceleration", "op": "gt", "value": 12.0, "label": "Acceleration > 12yr"},
        {"path": "phenoage_analysis.mortality_score_10yr", "op": "gt", "value": 0.25, "label": "10yr mortality > 25%"},
        {"path": "hallmark_narrative", "op": "key_present", "value": "nutrient_sensing", "label": "nutrient_sensing hallmark fires"},
        {"path": "hallmark_narrative", "op": "key_present", "value": "altered_intercellular_communication", "label": "inflammaging hallmark fires"},
        {"path": "compound_recommendations", "op": "any_tier", "value": "MR_VALIDATED", "label": "At least one MR_VALIDATED compound"},
        {"path": "compound_recommendations", "op": "compound_tier", "value": {"name_fragment": "metformin", "tier": "MR_VALIDATED"}, "label": "Metformin is MR_VALIDATED"},
    ],
)

# ─────────────────────────────────────────────────────────────────────────────
# Cohort 2: Cardiovascular Disease / Atherosclerosis Risk
# ─────────────────────────────────────────────────────────────────────────────
ROBERT = PatientArchetype(
    id="robert_cvd",
    name="Robert",
    age=63,
    sex="M",
    disease_context="Cardiovascular Disease / Atherosclerosis Risk",
    clinical_story=(
        "63-year-old male. Total cholesterol 245, LDL 168, HDL 38, TG 220, SBP 148. "
        "CRP 6.2 mg/L — chronic vascular inflammation. "
        "ASCVD 10yr risk: 22.1% (HIGH). PhenoAge: 81.5yr (+18.5yr acceleration). "
        "Neither score alone tells the full story. Together: arteries aging 18 years fast."
    ),
    stress_test=(
        "Does the system surface ASCVD + PhenoAge simultaneously? "
        "Does Omega-3 (MR_VALIDATED, IVW p=0.0086) rank above CoQ10 (OBSERVATIONAL)?"
    ),
    payload={
        "age": 63,
        "sex": "M",
        "biomarkers": {
            "albumin": 3.9,
            "creatinine": 1.3,
            "glucose_mg_dl": 118.0,
            "crp_mg_l": 6.2,
            "lymphocyte_percent": 19.0,
            "mcv": 96.0,
            "rdw": 15.8,
            "alkaline_phosphatase": 105.0,
            "wbc": 10.1,
            "total_cholesterol": 245.0,
            "hdl_cholesterol": 38.0,
            "ldl_cholesterol": 168.0,
            "triglycerides": 220.0,
            "systolic_bp": 148.0,
        },
        "compound_queries": ["omega_3", "vitamin_k2", "coq10", "berberine", "taurine"],
    },
    expected_findings=[
        "PhenoAge > 75yr (acceleration > 12yr)",
        "ASCVD 10yr risk > 20% (HIGH category)",
        "altered_intercellular_communication hallmark active (CRP 6.2, WBC 10.1)",
        "mitochondrial_dysfunction hallmark active (RDW 15.8, MCV 96)",
        "Omega-3 tier=MR_VALIDATED (Fabian 2025, IVW p=0.0086)",
        "CoQ10 tier=OBSERVATIONAL (lower than Omega-3)",
    ],
    assertions=[
        {"path": "phenoage_analysis.phenoage_estimate", "op": "gt", "value": 75.0, "label": "PhenoAge > 75yr"},
        {"path": "phenoage_analysis.age_acceleration", "op": "gt", "value": 12.0, "label": "Acceleration > 12yr"},
        {"path": "hallmark_narrative", "op": "key_present", "value": "altered_intercellular_communication", "label": "Inflammaging hallmark fires"},
        {"path": "compound_recommendations", "op": "compound_tier", "value": {"name_fragment": "omega", "tier": "MR_VALIDATED"}, "label": "Omega-3 is MR_VALIDATED"},
    ],
)

# ─────────────────────────────────────────────────────────────────────────────
# Cohort 3: Alzheimer's Risk / Cognitive Decline Prevention
# ─────────────────────────────────────────────────────────────────────────────
ELENA = PatientArchetype(
    id="elena_apoe",
    name="Elena",
    age=52,
    sex="F",
    disease_context="Alzheimer's Risk / Cognitive Decline Prevention",
    clinical_story=(
        "52-year-old female. Labs exceptional — PhenoAge shows deceleration. "
        "But: APOE e4/e4 (8-12× AD risk, Corder 1993 PMID 8346443), "
        "MTHFR compound heterozygous C677T+A1298C (~50% enzyme activity, PMID 8554066), "
        "homocysteine 18.2 µmol/L (elevated — epigenetic_alterations hallmark). "
        "Biomarker story: 'great.' Genetic story: 'act now.'"
    ),
    stress_test=(
        "Does the system surface genetic risk that contradicts the biomarker signal? "
        "Does Folate (MR_VALIDATED, IVW p=0.03) rank first for MTHFR compound het?"
    ),
    payload={
        "age": 52,
        "sex": "F",
        "biomarkers": {
            "albumin": 4.9,
            "creatinine": 0.78,
            "glucose_mg_dl": 82.0,
            "crp_mg_l": 0.3,
            "lymphocyte_percent": 35.0,
            "mcv": 87.0,
            "rdw": 12.2,
            "alkaline_phosphatase": 48.0,
            "wbc": 4.8,
            "homocysteine": 18.2,
            "25oh_vitamin_d": 24.0,
        },
        "variants": {
            "rs429358": {"genotype": "CC"},   # APOE e4/e4
            "rs7412": {"genotype": "CC"},
            "rs1801133": {"genotype": "CT"},  # MTHFR C677T het
            "rs1801131": {"genotype": "AC"},  # MTHFR A1298C het → compound het
        },
        "compound_queries": ["folate", "omega_3", "vitamin_d3", "egcg"],
    },
    expected_findings=[
        "PhenoAge < 52yr (decelerated — biomarkers excellent)",
        "APOE e4/e4 HIGH_RISK (8-12× AD risk, PMID 8346443)",
        "MTHFR compound heterozygous (~50% enzyme activity, PMID 8554066)",
        "Folate tier=MR_VALIDATED (Fabian 2025, IVW p=0.03)",
        "Omega-3 tier=MR_VALIDATED (APOE4 carriers have impaired DHA transport)",
        "epigenetic_alterations hallmark fires (homocysteine 18.2)",
    ],
    assertions=[
        {"path": "phenoage_analysis.phenoage_estimate", "op": "lt", "value": 52.0, "label": "PhenoAge < 52yr (decelerated)"},
        {"path": "phenoage_analysis.age_acceleration", "op": "lt", "value": 0.0, "label": "Age acceleration negative"},
        {"path": "genetic_profile.apoe_status.risk_tier", "op": "eq", "value": "HIGH_RISK", "label": "APOE e4/e4 HIGH_RISK"},
        {"path": "compound_recommendations", "op": "compound_tier", "value": {"name_fragment": "folate", "tier": "MR_VALIDATED"}, "label": "Folate is MR_VALIDATED"},
    ],
)

# ─────────────────────────────────────────────────────────────────────────────
# Cohort 4: Accelerated Aging / Sarcopenia + Frailty
# ─────────────────────────────────────────────────────────────────────────────
DOROTHY = PatientArchetype(
    id="dorothy_frailty",
    name="Dorothy",
    age=71,
    sex="F",
    disease_context="Accelerated Aging / Sarcopenia + Frailty",
    clinical_story=(
        "71-year-old female. Sedentary. No single lab flagged as 'abnormal' by standard ranges. "
        "But: HRV 22ms (HIGH_RISK, PMID 29034226), VO2max 24 (HIGH_RISK, PMID 27881567), "
        "deep sleep 10% (HIGH_RISK), steps 3200/day (HIGH_RISK, PMID 35416941), RHR 82bpm (HIGH_RISK). "
        "DHEA-S 42, IGF-1 68 — stem cell exhaustion. "
        "Wearable hallmark signal: mitochondrial_dysfunction 5.0. "
        "No standard physical catches this. The system does."
    ),
    stress_test=(
        "Does the wearable layer catch frailty trajectory that labs miss? "
        "Does mitochondrial_dysfunction signal reach 5.0 with all HIGH_RISK wearables?"
    ),
    payload={
        "age": 71,
        "sex": "F",
        "biomarkers": {
            "albumin": 3.7,
            "creatinine": 0.72,
            "glucose_mg_dl": 104.0,
            "crp_mg_l": 3.1,
            "lymphocyte_percent": 20.0,
            "mcv": 93.0,
            "rdw": 14.9,
            "alkaline_phosphatase": 88.0,
            "wbc": 8.4,
            "dhea_s": 42.0,
            "free_testosterone": 8.2,
            "igf1": 68.0,
        },
        "wearables": {
            "hrv_rmssd": 22.0,
            "vo2max": 24.0,
            "deep_sleep_pct": 10.0,
            "daily_steps": 3200,
            "resting_heart_rate": 82.0,
        },
        "compound_queries": ["taurine", "urolithin_a", "nmn", "vitamin_d3", "magnesium"],
    },
    expected_findings=[
        "PhenoAge > 72yr (acceleration > 1yr)",
        "ALL 5 wearable metrics: HIGH_RISK",
        "mitochondrial_dysfunction wearable signal >= 3.0",
        "cellular_senescence wearable signal >= 1.0",
        "Taurine recommended (ESTABLISHED+human evidence, mitochondrial + senescence)",
        "Urolithin_A recommended (ESTABLISHED+human, mitophagy activation)",
    ],
    assertions=[
        {"path": "phenoage_analysis.phenoage_estimate", "op": "gt", "value": 72.0, "label": "PhenoAge > 72yr"},
        {"path": "wearable_assessment.scored_metrics.hrv_rmssd.tier", "op": "eq", "value": "HIGH_RISK", "label": "HRV HIGH_RISK"},
        {"path": "wearable_assessment.scored_metrics.vo2max.tier", "op": "eq", "value": "HIGH_RISK", "label": "VO2max HIGH_RISK"},
        {"path": "wearable_assessment.scored_metrics.deep_sleep_pct.tier", "op": "eq", "value": "HIGH_RISK", "label": "Deep sleep HIGH_RISK"},
        {"path": "wearable_assessment.scored_metrics.daily_steps.tier", "op": "eq", "value": "HIGH_RISK", "label": "Steps HIGH_RISK"},
        {"path": "wearable_assessment.scored_metrics.resting_heart_rate.tier", "op": "eq", "value": "HIGH_RISK", "label": "RHR HIGH_RISK"},
        {"path": "wearable_assessment.hallmark_signals.mitochondrial_dysfunction", "op": "gte", "value": 3.0, "label": "Mito signal >= 3.0"},
    ],
)

# ─────────────────────────────────────────────────────────────────────────────
# Cohort 5: Longevity Optimization / Centenarian Trajectory
# ─────────────────────────────────────────────────────────────────────────────
JAMES = PatientArchetype(
    id="james_centenarian",
    name="James",
    age=68,
    sex="M",
    disease_context="Longevity Optimization / Centenarian Trajectory",
    clinical_story=(
        "68-year-old male. Biomarkers look like a 45-year-old. "
        "FOXO3 G/G (homozygous protective, longevity-associated), "
        "CETP A/A (high HDL genotype), KLOTHO T/T (KL-VS haplotype, anti-aging). "
        "ALL 5 wearable metrics OPTIMAL. "
        "This is the integrity test: does the system avoid false positives "
        "when everything is genuinely good?"
    ),
    stress_test=(
        "Does the system return 'maintain current protocol' rather than inventing urgency? "
        "Are all wearable tiers OPTIMAL? Is FOXO3 correctly identified as homozygous_protective?"
    ),
    payload={
        "age": 68,
        "sex": "M",
        "biomarkers": {
            "albumin": 4.7,
            "creatinine": 0.82,
            "glucose_mg_dl": 84.0,
            "crp_mg_l": 0.2,
            "lymphocyte_percent": 34.0,
            "mcv": 87.0,
            "rdw": 12.1,
            "alkaline_phosphatase": 50.0,
            "wbc": 4.9,
            "25oh_vitamin_d": 58.0,
            "dhea_s": 185.0,
        },
        "variants": {
            "rs2802292": {"genotype": "GG"},   # FOXO3 homozygous protective
            "rs5882": {"genotype": "AA"},       # CETP homozygous protective
            "rs9536314": {"genotype": "TT"},    # KLOTHO homozygous protective
        },
        "wearables": {
            "hrv_rmssd": 62.0,
            "vo2max": 52.0,
            "deep_sleep_pct": 22.0,
            "daily_steps": 11000,
            "resting_heart_rate": 52.0,
        },
        "compound_queries": ["omega_3", "vitamin_d3", "spermidine", "nmn"],
    },
    expected_findings=[
        "PhenoAge < 55yr (deceleration >= 13yr)",
        "ALL 5 wearable metrics: OPTIMAL",
        "All wearable hallmark signals = 0.0",
        "FOXO3 rs2802292 GG = homozygous_protective",
        "CETP rs5882 AA = homozygous_protective",
        "KLOTHO rs9536314 TT = homozygous_protective",
        "No false urgency — system does not invent risk",
    ],
    assertions=[
        {"path": "phenoage_analysis.phenoage_estimate", "op": "lt", "value": 55.0, "label": "PhenoAge < 55yr"},
        {"path": "phenoage_analysis.age_acceleration", "op": "lt", "value": 0.0, "label": "Age acceleration negative"},
        {"path": "wearable_assessment.scored_metrics.hrv_rmssd.tier", "op": "eq", "value": "OPTIMAL", "label": "HRV OPTIMAL"},
        {"path": "wearable_assessment.scored_metrics.vo2max.tier", "op": "eq", "value": "OPTIMAL", "label": "VO2max OPTIMAL"},
        {"path": "wearable_assessment.scored_metrics.daily_steps.tier", "op": "eq", "value": "OPTIMAL", "label": "Steps OPTIMAL"},
        {"path": "wearable_assessment.hallmark_signals.mitochondrial_dysfunction", "op": "eq", "value": 0.0, "label": "Mito signal = 0 (no false positive)"},
    ],
)

ALL_ARCHETYPES = [MARCUS, ROBERT, ELENA, DOROTHY, JAMES]
