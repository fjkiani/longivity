// Captured from production API 2026-05-17
// Source: longivity-backend.onrender.com
export const SCENARIO_OUTPUTS: Record<string, unknown> = {
  "deceptive-optimizer": {
    "status": "SUCCESS",
    "level": null,
    "phenoage_analysis": {
      "components_available": 9,
      "components_total": 9,
      "age_years": 44,
      "xb_partial_if_complete_else_absent_note": "xb (full published form) computed only when all 9 lab components and age are present.",
      "phenoage_estimate": 44.64,
      "mortality_score_10yr": 0.028698,
      "age_acceleration": 0.64,
      "completeness_mode": "FULL_9BIOMARKERS_PLUS_AGE",
      "top_accelerators": [],
      "top_by_linear_term_magnitude": [
        {
          "canonical_key": "rdw",
          "biomarker": "rdw",
          "label": "Red cell distribution width",
          "value": 13.8,
          "unit": "%",
          "coefficient": 0.3306,
          "linear_term": 4.56228,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "mitochondrial_dysfunction"
          ],
          "primary_hallmark": "mitochondrial_dysfunction",
          "biomarker_map_id": "rdw",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "mcv",
          "biomarker": "mcv",
          "label": "Mean cell volume",
          "value": 91.0,
          "unit": "fL",
          "coefficient": 0.0268,
          "linear_term": 2.4388,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "mitochondrial_dysfunction"
          ],
          "primary_hallmark": "mitochondrial_dysfunction",
          "biomarker_map_id": "mcv",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "albumin",
          "biomarker": "albumin",
          "label": "Albumin",
          "value": 41.0,
          "unit": "g/L",
          "coefficient": -0.0336,
          "linear_term": -1.3776,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "nutrient_sensing"
          ],
          "primary_hallmark": "nutrient_sensing",
          "biomarker_map_id": "serum_albumin_g_l",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "glucose_serum",
          "biomarker": "glucose_serum",
          "label": "Glucose, serum",
          "value": 5.439005,
          "unit": "mmol/L",
          "coefficient": 0.1953,
          "linear_term": 1.062238,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "nutrient_sensing"
          ],
          "primary_hallmark": "nutrient_sensing",
          "biomarker_map_id": "serum_glucose_mmol",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "creatinine",
          "biomarker": "creatinine",
          "label": "Creatinine",
          "value": 92.841,
          "unit": "umol/L",
          "coefficient": 0.0095,
          "linear_term": 0.88199,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "cellular_senescence"
          ],
          "primary_hallmark": "cellular_senescence",
          "biomarker_map_id": "serum_creatinine_umol_l",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "wbc",
          "biomarker": "wbc",
          "label": "White blood cell count",
          "value": 6.2,
          "unit": "1000 cells/uL",
          "coefficient": 0.0554,
          "linear_term": 0.34348,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "altered_intercellular_communication"
          ],
          "primary_hallmark": "altered_intercellular_communication",
          "biomarker_map_id": "wbc",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "lymphocyte_percent",
          "biomarker": "lymphocyte_percent",
          "label": "Lymphocyte percent",
          "value": 28.0,
          "unit": "%",
          "coefficient": -0.012,
          "linear_term": -0.336,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "altered_intercellular_communication",
            "cellular_senescence"
          ],
          "primary_hallmark": "altered_intercellular_communication",
          "biomarker_map_id": "lymphocyte_percent",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "crp_log",
          "biomarker": "crp_log",
          "label": "C-reactive protein (log)",
          "value": -1.714798,
          "unit": "mg/dL",
          "coefficient": 0.0954,
          "linear_term": -0.163592,
          "tier": "MODERATE",
          "acceleration_status": "NORMAL",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.5,
          "hallmarks_from_map": [
            "altered_intercellular_communication"
          ],
          "primary_hallmark": "altered_intercellular_communication",
          "biomarker_map_id": "hscrp",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "alkaline_phosphatase",
          "biomarker": "alkaline_phosphatase",
          "label": "Alkaline phosphatase",
          "value": 72.0,
          "unit": "U/L",
          "coefficient": 0.0019,
          "linear_term": 0.1368,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "mitochondrial_dysfunction"
          ],
          "primary_hallmark": "mitochondrial_dysfunction",
          "biomarker_map_id": "alkaline_phosphatase",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        }
      ],
      "all_components": [
        {
          "canonical_key": "albumin",
          "biomarker": "albumin",
          "label": "Albumin",
          "value": 41.0,
          "unit": "g/L",
          "coefficient": -0.0336,
          "linear_term": -1.3776,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "nutrient_sensing"
          ],
          "primary_hallmark": "nutrient_sensing",
          "biomarker_map_id": "serum_albumin_g_l",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "alkaline_phosphatase",
          "biomarker": "alkaline_phosphatase",
          "label": "Alkaline phosphatase",
          "value": 72.0,
          "unit": "U/L",
          "coefficient": 0.0019,
          "linear_term": 0.1368,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "mitochondrial_dysfunction"
          ],
          "primary_hallmark": "mitochondrial_dysfunction",
          "biomarker_map_id": "alkaline_phosphatase",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "creatinine",
          "biomarker": "creatinine",
          "label": "Creatinine",
          "value": 92.841,
          "unit": "umol/L",
          "coefficient": 0.0095,
          "linear_term": 0.88199,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "cellular_senescence"
          ],
          "primary_hallmark": "cellular_senescence",
          "biomarker_map_id": "serum_creatinine_umol_l",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "crp_log",
          "biomarker": "crp_log",
          "label": "C-reactive protein (log)",
          "value": -1.714798,
          "unit": "mg/dL",
          "coefficient": 0.0954,
          "linear_term": -0.163592,
          "tier": "MODERATE",
          "acceleration_status": "NORMAL",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.5,
          "hallmarks_from_map": [
            "altered_intercellular_communication"
          ],
          "primary_hallmark": "altered_intercellular_communication",
          "biomarker_map_id": "hscrp",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "glucose_serum",
          "biomarker": "glucose_serum",
          "label": "Glucose, serum",
          "value": 5.439005,
          "unit": "mmol/L",
          "coefficient": 0.1953,
          "linear_term": 1.062238,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "nutrient_sensing"
          ],
          "primary_hallmark": "nutrient_sensing",
          "biomarker_map_id": "serum_glucose_mmol",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "lymphocyte_percent",
          "biomarker": "lymphocyte_percent",
          "label": "Lymphocyte percent",
          "value": 28.0,
          "unit": "%",
          "coefficient": -0.012,
          "linear_term": -0.336,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "altered_intercellular_communication",
            "cellular_senescence"
          ],
          "primary_hallmark": "altered_intercellular_communication",
          "biomarker_map_id": "lymphocyte_percent",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "mcv",
          "biomarker": "mcv",
          "label": "Mean cell volume",
          "value": 91.0,
          "unit": "fL",
          "coefficient": 0.0268,
          "linear_term": 2.4388,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "mitochondrial_dysfunction"
          ],
          "primary_hallmark": "mitochondrial_dysfunction",
          "biomarker_map_id": "mcv",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "rdw",
          "biomarker": "rdw",
          "label": "Red cell distribution width",
          "value": 13.8,
          "unit": "%",
          "coefficient": 0.3306,
          "linear_term": 4.56228,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "mitochondrial_dysfunction"
          ],
          "primary_hallmark": "mitochondrial_dysfunction",
          "biomarker_map_id": "rdw",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "wbc",
          "biomarker": "wbc",
          "label": "White blood cell count",
          "value": 6.2,
          "unit": "1000 cells/uL",
          "coefficient": 0.0554,
          "linear_term": 0.34348,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "altered_intercellular_communication"
          ],
          "primary_hallmark": "altered_intercellular_communication",
          "biomarker_map_id": "wbc",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        }
      ],
      "conversion_notes": {
        "albumin": "converted albumin_g_dl -> g/L (*10)",
        "creatinine": "converted creatinine_mg_dl -> \u00b5mol/L (*88.42)",
        "glucose_serum": "converted glucose_mg_dl -> mmol/L (/18.018)",
        "crp_log": "hsCRP/CRP mg/L=1.8 \u2192 CRP mg/dL=0.18000000000000002 (\u00f710) \u2192 ln(mg/dL)=-1.714798; aliases: crp_mg_l, hscrp, hs_crp_mg_l, hsCRP_mg_l (case-insensitive keys)"
      },
      "source_pmid": "29676998",
      "calibration_note": "Coefficients from Gompertz PH model (Supplementary Table S1 / Table 1, PMID 29676998). PhenotypicAge and 10-year mortality require all nine biomarkers in published units plus chronological age; partial inputs yield per-component linear terms only. CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)"
    },
    "biological_age": null,
    "hallmark_narrative": {},
    "compound_recommendations": [],
    "genetic_profile": null,
    "data_completeness": {
      "phenoage_components": 9,
      "phenoage_total": 9,
      "phenoage_complete_for_full_estimate": true,
      "supplementary_biomarkers": 0,
      "hallmarks_scoreable": 0,
      "phenoage_panel_diagnosis": {
        "normalized_biomarker_keys": [
          "albumin_g_dl",
          "alkaline_phosphatase_u_l",
          "creatinine_mg_dl",
          "crp_mg_l",
          "glucose_mg_dl",
          "lymphocyte_percent",
          "mcv_fl",
          "rdw_percent",
          "white_blood_cell_count"
        ],
        "phenoage_canonical_recognized": [
          "albumin",
          "alkaline_phosphatase",
          "creatinine",
          "crp_log",
          "glucose_serum",
          "lymphocyte_percent",
          "mcv",
          "rdw",
          "wbc"
        ],
        "phenoage_canonical_missing_for_full": [],
        "chronological_age_present": true,
        "full_phenoage_eligible": true
      },
      "all_optimal": false,
      "recommendation": "Panel complete for published PhenoAge mortality step."
    },
    "disclaimer": "Research Use Only. Biological age estimation follows published PhenoAge transforms; acceleration labels are CrisPRO UX thresholds, not PhenoAge classifications. Do not use for clinical decisions without a qualified clinician."
  },
  "genetic-wildcard": {
    "status": "SUCCESS",
    "level": 0,
    "phenoage_analysis": {
      "phenoage_estimate": 34.08,
      "mortality_score_10yr": 0.011177,
      "age_acceleration": -17.92,
      "age_years": 52,
      "completeness_mode": "FULL_9BIOMARKERS_PLUS_AGE",
      "top_accelerators": []
    },
    "biological_age": {
      "phenoage_estimate": 34.08,
      "mortality_score_10yr": 0.011177,
      "age_acceleration": -17.92,
      "age_years": 52,
      "completeness_mode": "FULL_9BIOMARKERS_PLUS_AGE",
      "top_accelerators": []
    },
    "hallmark_narrative": {},
    "compound_recommendations": [],
    "genetic_profile": null,
    "data_completeness": {
      "phenoage_components": 9,
      "phenoage_total": 9,
      "phenoage_complete_for_full_estimate": true,
      "supplementary_biomarkers": 0,
      "hallmarks_scoreable": 0,
      "phenoage_panel_diagnosis": {
        "normalized_biomarker_keys": [
          "albumin_g_dl",
          "alkaline_phosphatase_u_l",
          "creatinine_mg_dl",
          "crp_mg_l",
          "glucose_mg_dl",
          "lymphocyte_percent",
          "mcv_fl",
          "rdw_percent",
          "white_blood_cell_count"
        ],
        "phenoage_canonical_recognized": [
          "albumin",
          "alkaline_phosphatase",
          "creatinine",
          "crp_log",
          "glucose_serum",
          "lymphocyte_percent",
          "mcv",
          "rdw",
          "wbc"
        ],
        "phenoage_canonical_missing_for_full": [],
        "chronological_age_present": true,
        "full_phenoage_eligible": true
      },
      "all_optimal": true,
      "recommendation": "maintain current protocol",
      "genetics_provided": false,
      "dna_repair_genotype_provided": false,
      "compound_queries_merged_from_dna_repair": 0
    },
    "disclaimer": "Research Use Only. Biological age estimation follows published PhenoAge transforms; acceleration labels are CrisPRO UX thresholds, not PhenoAge classifications. Do not use for clinical decisions without a qualified clinician. Polygenic scores for complex traits and parental lifespan typically explain only a small fraction of phenotypic variance (often on the order of R\u00b2 \u2248 0.02\u20130.08 depending on endpoint, cohort, and PRS construction). This score is for research context and must not be interpreted as deterministic individual risk."
  },
  "metabolic-storm": {
    "status": "SUCCESS",
    "level": null,
    "phenoage_analysis": {
      "components_available": 9,
      "components_total": 9,
      "age_years": 61,
      "xb_partial_if_complete_else_absent_note": "xb (full published form) computed only when all 9 lab components and age are present.",
      "phenoage_estimate": 73.4,
      "mortality_score_10yr": 0.322508,
      "age_acceleration": 12.4,
      "completeness_mode": "FULL_9BIOMARKERS_PLUS_AGE",
      "top_accelerators": [
        {
          "canonical_key": "crp_log",
          "biomarker": "crp_log",
          "label": "C-reactive protein (log)",
          "value": -0.867501,
          "unit": "mg/dL",
          "coefficient": 0.0954,
          "linear_term": -0.08276,
          "tier": "HIGH_RISK",
          "acceleration_status": "ACCELERATING",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 1.0,
          "hallmarks_from_map": [
            "altered_intercellular_communication"
          ],
          "primary_hallmark": "altered_intercellular_communication",
          "biomarker_map_id": "hscrp",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        }
      ],
      "top_by_linear_term_magnitude": [
        {
          "canonical_key": "rdw",
          "biomarker": "rdw",
          "label": "Red cell distribution width",
          "value": 14.9,
          "unit": "%",
          "coefficient": 0.3306,
          "linear_term": 4.92594,
          "tier": "MODERATE",
          "acceleration_status": "NORMAL",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.5,
          "hallmarks_from_map": [
            "mitochondrial_dysfunction"
          ],
          "primary_hallmark": "mitochondrial_dysfunction",
          "biomarker_map_id": "rdw",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "mcv",
          "biomarker": "mcv",
          "label": "Mean cell volume",
          "value": 94.0,
          "unit": "fL",
          "coefficient": 0.0268,
          "linear_term": 2.5192,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "mitochondrial_dysfunction"
          ],
          "primary_hallmark": "mitochondrial_dysfunction",
          "biomarker_map_id": "mcv",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "glucose_serum",
          "biomarker": "glucose_serum",
          "label": "Glucose, serum",
          "value": 6.549007,
          "unit": "mmol/L",
          "coefficient": 0.1953,
          "linear_term": 1.279021,
          "tier": "MODERATE",
          "acceleration_status": "NORMAL",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.5,
          "hallmarks_from_map": [
            "nutrient_sensing"
          ],
          "primary_hallmark": "nutrient_sensing",
          "biomarker_map_id": "serum_glucose_mmol",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "albumin",
          "biomarker": "albumin",
          "label": "Albumin",
          "value": 38.0,
          "unit": "g/L",
          "coefficient": -0.0336,
          "linear_term": -1.2768,
          "tier": "MODERATE",
          "acceleration_status": "NORMAL",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.5,
          "hallmarks_from_map": [
            "nutrient_sensing"
          ],
          "primary_hallmark": "nutrient_sensing",
          "biomarker_map_id": "serum_albumin_g_l",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "creatinine",
          "biomarker": "creatinine",
          "label": "Creatinine",
          "value": 104.3356,
          "unit": "umol/L",
          "coefficient": 0.0095,
          "linear_term": 0.991188,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "cellular_senescence"
          ],
          "primary_hallmark": "cellular_senescence",
          "biomarker_map_id": "serum_creatinine_umol_l",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "wbc",
          "biomarker": "wbc",
          "label": "White blood cell count",
          "value": 8.1,
          "unit": "1000 cells/uL",
          "coefficient": 0.0554,
          "linear_term": 0.44874,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "altered_intercellular_communication"
          ],
          "primary_hallmark": "altered_intercellular_communication",
          "biomarker_map_id": "wbc",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "lymphocyte_percent",
          "biomarker": "lymphocyte_percent",
          "label": "Lymphocyte percent",
          "value": 18.0,
          "unit": "%",
          "coefficient": -0.012,
          "linear_term": -0.216,
          "tier": "MODERATE",
          "acceleration_status": "NORMAL",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.5,
          "hallmarks_from_map": [
            "altered_intercellular_communication",
            "cellular_senescence"
          ],
          "primary_hallmark": "altered_intercellular_communication",
          "biomarker_map_id": "lymphocyte_percent",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "alkaline_phosphatase",
          "biomarker": "alkaline_phosphatase",
          "label": "Alkaline phosphatase",
          "value": 98.0,
          "unit": "U/L",
          "coefficient": 0.0019,
          "linear_term": 0.1862,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "mitochondrial_dysfunction"
          ],
          "primary_hallmark": "mitochondrial_dysfunction",
          "biomarker_map_id": "alkaline_phosphatase",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "crp_log",
          "biomarker": "crp_log",
          "label": "C-reactive protein (log)",
          "value": -0.867501,
          "unit": "mg/dL",
          "coefficient": 0.0954,
          "linear_term": -0.08276,
          "tier": "HIGH_RISK",
          "acceleration_status": "ACCELERATING",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 1.0,
          "hallmarks_from_map": [
            "altered_intercellular_communication"
          ],
          "primary_hallmark": "altered_intercellular_communication",
          "biomarker_map_id": "hscrp",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        }
      ],
      "all_components": [
        {
          "canonical_key": "albumin",
          "biomarker": "albumin",
          "label": "Albumin",
          "value": 38.0,
          "unit": "g/L",
          "coefficient": -0.0336,
          "linear_term": -1.2768,
          "tier": "MODERATE",
          "acceleration_status": "NORMAL",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.5,
          "hallmarks_from_map": [
            "nutrient_sensing"
          ],
          "primary_hallmark": "nutrient_sensing",
          "biomarker_map_id": "serum_albumin_g_l",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "alkaline_phosphatase",
          "biomarker": "alkaline_phosphatase",
          "label": "Alkaline phosphatase",
          "value": 98.0,
          "unit": "U/L",
          "coefficient": 0.0019,
          "linear_term": 0.1862,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "mitochondrial_dysfunction"
          ],
          "primary_hallmark": "mitochondrial_dysfunction",
          "biomarker_map_id": "alkaline_phosphatase",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "creatinine",
          "biomarker": "creatinine",
          "label": "Creatinine",
          "value": 104.3356,
          "unit": "umol/L",
          "coefficient": 0.0095,
          "linear_term": 0.991188,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "cellular_senescence"
          ],
          "primary_hallmark": "cellular_senescence",
          "biomarker_map_id": "serum_creatinine_umol_l",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "crp_log",
          "biomarker": "crp_log",
          "label": "C-reactive protein (log)",
          "value": -0.867501,
          "unit": "mg/dL",
          "coefficient": 0.0954,
          "linear_term": -0.08276,
          "tier": "HIGH_RISK",
          "acceleration_status": "ACCELERATING",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 1.0,
          "hallmarks_from_map": [
            "altered_intercellular_communication"
          ],
          "primary_hallmark": "altered_intercellular_communication",
          "biomarker_map_id": "hscrp",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "glucose_serum",
          "biomarker": "glucose_serum",
          "label": "Glucose, serum",
          "value": 6.549007,
          "unit": "mmol/L",
          "coefficient": 0.1953,
          "linear_term": 1.279021,
          "tier": "MODERATE",
          "acceleration_status": "NORMAL",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.5,
          "hallmarks_from_map": [
            "nutrient_sensing"
          ],
          "primary_hallmark": "nutrient_sensing",
          "biomarker_map_id": "serum_glucose_mmol",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "lymphocyte_percent",
          "biomarker": "lymphocyte_percent",
          "label": "Lymphocyte percent",
          "value": 18.0,
          "unit": "%",
          "coefficient": -0.012,
          "linear_term": -0.216,
          "tier": "MODERATE",
          "acceleration_status": "NORMAL",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.5,
          "hallmarks_from_map": [
            "altered_intercellular_communication",
            "cellular_senescence"
          ],
          "primary_hallmark": "altered_intercellular_communication",
          "biomarker_map_id": "lymphocyte_percent",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "mcv",
          "biomarker": "mcv",
          "label": "Mean cell volume",
          "value": 94.0,
          "unit": "fL",
          "coefficient": 0.0268,
          "linear_term": 2.5192,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "mitochondrial_dysfunction"
          ],
          "primary_hallmark": "mitochondrial_dysfunction",
          "biomarker_map_id": "mcv",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "rdw",
          "biomarker": "rdw",
          "label": "Red cell distribution width",
          "value": 14.9,
          "unit": "%",
          "coefficient": 0.3306,
          "linear_term": 4.92594,
          "tier": "MODERATE",
          "acceleration_status": "NORMAL",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.5,
          "hallmarks_from_map": [
            "mitochondrial_dysfunction"
          ],
          "primary_hallmark": "mitochondrial_dysfunction",
          "biomarker_map_id": "rdw",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "wbc",
          "biomarker": "wbc",
          "label": "White blood cell count",
          "value": 8.1,
          "unit": "1000 cells/uL",
          "coefficient": 0.0554,
          "linear_term": 0.44874,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "altered_intercellular_communication"
          ],
          "primary_hallmark": "altered_intercellular_communication",
          "biomarker_map_id": "wbc",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        }
      ],
      "conversion_notes": {
        "albumin": "converted albumin_g_dl -> g/L (*10)",
        "creatinine": "converted creatinine_mg_dl -> \u00b5mol/L (*88.42)",
        "glucose_serum": "converted glucose_mg_dl -> mmol/L (/18.018)",
        "crp_log": "hsCRP/CRP mg/L=4.2 \u2192 CRP mg/dL=0.42000000000000004 (\u00f710) \u2192 ln(mg/dL)=-0.867501; aliases: crp_mg_l, hscrp, hs_crp_mg_l, hsCRP_mg_l (case-insensitive keys)"
      },
      "source_pmid": "29676998",
      "calibration_note": "Coefficients from Gompertz PH model (Supplementary Table S1 / Table 1, PMID 29676998). PhenotypicAge and 10-year mortality require all nine biomarkers in published units plus chronological age; partial inputs yield per-component linear terms only. CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)"
    },
    "biological_age": null,
    "hallmark_narrative": {
      "altered_intercellular_communication": {
        "status": "PRIMARY_DRIVER",
        "phenoage_signal": 0.0828,
        "supplementary_signal": 0.0,
        "supplementary_signal_note": "Sum of threshold tier_scores (0/0.5/1) for this hallmark \u2014 not blended with PhenoAge.",
        "driving_biomarkers_phenoage": [
          "crp_log"
        ],
        "driving_biomarkers_supplementary": [],
        "explanation": "PhenoAge-linear-term magnitude from accelerating components mapped to this hallmark (1 analytes). Supplementary tier scores add a separate, non-mortality-calibrated signal."
      }
    },
    "compound_recommendations": [],
    "genetic_profile": null,
    "data_completeness": {
      "phenoage_components": 9,
      "phenoage_total": 9,
      "phenoage_complete_for_full_estimate": true,
      "supplementary_biomarkers": 0,
      "hallmarks_scoreable": 1,
      "phenoage_panel_diagnosis": {
        "normalized_biomarker_keys": [
          "albumin_g_dl",
          "alkaline_phosphatase_u_l",
          "creatinine_mg_dl",
          "crp_mg_l",
          "glucose_mg_dl",
          "lymphocyte_percent",
          "mcv_fl",
          "rdw_percent",
          "white_blood_cell_count"
        ],
        "phenoage_canonical_recognized": [
          "albumin",
          "alkaline_phosphatase",
          "creatinine",
          "crp_log",
          "glucose_serum",
          "lymphocyte_percent",
          "mcv",
          "rdw",
          "wbc"
        ],
        "phenoage_canonical_missing_for_full": [],
        "chronological_age_present": true,
        "full_phenoage_eligible": true
      },
      "all_optimal": false,
      "recommendation": "Panel complete for published PhenoAge mortality step."
    },
    "disclaimer": "Research Use Only. Biological age estimation follows published PhenoAge transforms; acceleration labels are CrisPRO UX thresholds, not PhenoAge classifications. Do not use for clinical decisions without a qualified clinician."
  },
  "partial-panel": {
    "status": "SUCCESS",
    "level": null,
    "phenoage_analysis": {
      "components_available": 5,
      "components_total": 9,
      "age_years": 55,
      "xb_partial_if_complete_else_absent_note": "xb (full published form) computed only when all 9 lab components and age are present.",
      "phenoage_estimate": null,
      "mortality_score_10yr": null,
      "age_acceleration": null,
      "completeness_mode": "PARTIAL",
      "top_accelerators": [],
      "top_by_linear_term_magnitude": [
        {
          "canonical_key": "albumin",
          "biomarker": "albumin",
          "label": "Albumin",
          "value": 43.0,
          "unit": "g/L",
          "coefficient": -0.0336,
          "linear_term": -1.4448,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "nutrient_sensing"
          ],
          "primary_hallmark": "nutrient_sensing",
          "biomarker_map_id": "serum_albumin_g_l",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "glucose_serum",
          "biomarker": "glucose_serum",
          "label": "Glucose, serum",
          "value": 5.050505,
          "unit": "mmol/L",
          "coefficient": 0.1953,
          "linear_term": 0.986364,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "nutrient_sensing"
          ],
          "primary_hallmark": "nutrient_sensing",
          "biomarker_map_id": "serum_glucose_mmol",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "creatinine",
          "biomarker": "creatinine",
          "label": "Creatinine",
          "value": 75.157,
          "unit": "umol/L",
          "coefficient": 0.0095,
          "linear_term": 0.713992,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "cellular_senescence"
          ],
          "primary_hallmark": "cellular_senescence",
          "biomarker_map_id": "serum_creatinine_umol_l",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "wbc",
          "biomarker": "wbc",
          "label": "White blood cell count",
          "value": 5.8,
          "unit": "1000 cells/uL",
          "coefficient": 0.0554,
          "linear_term": 0.32132,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "altered_intercellular_communication"
          ],
          "primary_hallmark": "altered_intercellular_communication",
          "biomarker_map_id": "wbc",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "crp_log",
          "biomarker": "crp_log",
          "label": "C-reactive protein (log)",
          "value": -2.407946,
          "unit": "mg/dL",
          "coefficient": 0.0954,
          "linear_term": -0.229718,
          "tier": "MODERATE",
          "acceleration_status": "NORMAL",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.5,
          "hallmarks_from_map": [
            "altered_intercellular_communication"
          ],
          "primary_hallmark": "altered_intercellular_communication",
          "biomarker_map_id": "hscrp",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        }
      ],
      "all_components": [
        {
          "canonical_key": "albumin",
          "biomarker": "albumin",
          "label": "Albumin",
          "value": 43.0,
          "unit": "g/L",
          "coefficient": -0.0336,
          "linear_term": -1.4448,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "nutrient_sensing"
          ],
          "primary_hallmark": "nutrient_sensing",
          "biomarker_map_id": "serum_albumin_g_l",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "creatinine",
          "biomarker": "creatinine",
          "label": "Creatinine",
          "value": 75.157,
          "unit": "umol/L",
          "coefficient": 0.0095,
          "linear_term": 0.713992,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "cellular_senescence"
          ],
          "primary_hallmark": "cellular_senescence",
          "biomarker_map_id": "serum_creatinine_umol_l",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "crp_log",
          "biomarker": "crp_log",
          "label": "C-reactive protein (log)",
          "value": -2.407946,
          "unit": "mg/dL",
          "coefficient": 0.0954,
          "linear_term": -0.229718,
          "tier": "MODERATE",
          "acceleration_status": "NORMAL",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.5,
          "hallmarks_from_map": [
            "altered_intercellular_communication"
          ],
          "primary_hallmark": "altered_intercellular_communication",
          "biomarker_map_id": "hscrp",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "glucose_serum",
          "biomarker": "glucose_serum",
          "label": "Glucose, serum",
          "value": 5.050505,
          "unit": "mmol/L",
          "coefficient": 0.1953,
          "linear_term": 0.986364,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "nutrient_sensing"
          ],
          "primary_hallmark": "nutrient_sensing",
          "biomarker_map_id": "serum_glucose_mmol",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        },
        {
          "canonical_key": "wbc",
          "biomarker": "wbc",
          "label": "White blood cell count",
          "value": 5.8,
          "unit": "1000 cells/uL",
          "coefficient": 0.0554,
          "linear_term": 0.32132,
          "tier": "OPTIMAL",
          "acceleration_status": "PROTECTIVE",
          "acceleration_method": "CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)",
          "tier_score": 0.0,
          "hallmarks_from_map": [
            "altered_intercellular_communication"
          ],
          "primary_hallmark": "altered_intercellular_communication",
          "biomarker_map_id": "wbc",
          "source": "PhenoAge (Levine 2018, PMID 29676998)"
        }
      ],
      "conversion_notes": {
        "albumin": "converted albumin_g_dl -> g/L (*10)",
        "creatinine": "converted creatinine_mg_dl -> \u00b5mol/L (*88.42)",
        "glucose_serum": "converted glucose_mg_dl -> mmol/L (/18.018)",
        "crp_log": "hsCRP/CRP mg/L=0.9 \u2192 CRP mg/dL=0.09000000000000001 (\u00f710) \u2192 ln(mg/dL)=-2.407946; aliases: crp_mg_l, hscrp, hs_crp_mg_l, hsCRP_mg_l (case-insensitive keys)"
      },
      "source_pmid": "29676998",
      "calibration_note": "Coefficients from Gompertz PH model (Supplementary Table S1 / Table 1, PMID 29676998). PhenotypicAge and 10-year mortality require all nine biomarkers in published units plus chronological age; partial inputs yield per-component linear terms only. CrisPRO threshold comparison (biomarker_hallmark_map.json; not PhenoAge classification)"
    },
    "biological_age": null,
    "hallmark_narrative": {},
    "compound_recommendations": [],
    "genetic_profile": null,
    "data_completeness": {
      "phenoage_components": 5,
      "phenoage_total": 9,
      "phenoage_complete_for_full_estimate": false,
      "supplementary_biomarkers": 0,
      "hallmarks_scoreable": 0,
      "phenoage_panel_diagnosis": {
        "normalized_biomarker_keys": [
          "albumin_g_dl",
          "creatinine_mg_dl",
          "crp_mg_l",
          "glucose_mg_dl",
          "white_blood_cell_count"
        ],
        "phenoage_canonical_recognized": [
          "albumin",
          "creatinine",
          "crp_log",
          "glucose_serum",
          "wbc"
        ],
        "phenoage_canonical_missing_for_full": [
          "alkaline_phosphatase",
          "lymphocyte_percent",
          "mcv",
          "rdw"
        ],
        "chronological_age_present": true,
        "full_phenoage_eligible": false
      },
      "all_optimal": false,
      "recommendation": "Provide CBC, CMP (including glucose, albumin, creatinine, alk phos), CRP (or hsCRP), and age for full PhenoAge."
    },
    "disclaimer": "Research Use Only. Biological age estimation follows published PhenoAge transforms; acceleration labels are CrisPRO UX thresholds, not PhenoAge classifications. Do not use for clinical decisions without a qualified clinician."
  },
  "longevity-outlier": {
    "status": "SUCCESS",
    "level": 0,
    "phenoage_analysis": {
      "phenoage_estimate": 48.64,
      "mortality_score_10yr": 0.040921,
      "age_acceleration": -19.36,
      "age_years": 68,
      "completeness_mode": "FULL_9BIOMARKERS_PLUS_AGE",
      "top_accelerators": []
    },
    "biological_age": {
      "phenoage_estimate": 48.64,
      "mortality_score_10yr": 0.040921,
      "age_acceleration": -19.36,
      "age_years": 68,
      "completeness_mode": "FULL_9BIOMARKERS_PLUS_AGE",
      "top_accelerators": []
    },
    "hallmark_narrative": {},
    "compound_recommendations": [],
    "genetic_profile": null,
    "data_completeness": {
      "phenoage_components": 9,
      "phenoage_total": 9,
      "phenoage_complete_for_full_estimate": true,
      "supplementary_biomarkers": 0,
      "hallmarks_scoreable": 0,
      "phenoage_panel_diagnosis": {
        "normalized_biomarker_keys": [
          "albumin_g_dl",
          "alkaline_phosphatase_u_l",
          "creatinine_mg_dl",
          "crp_mg_l",
          "glucose_mg_dl",
          "lymphocyte_percent",
          "mcv_fl",
          "rdw_percent",
          "white_blood_cell_count"
        ],
        "phenoage_canonical_recognized": [
          "albumin",
          "alkaline_phosphatase",
          "creatinine",
          "crp_log",
          "glucose_serum",
          "lymphocyte_percent",
          "mcv",
          "rdw",
          "wbc"
        ],
        "phenoage_canonical_missing_for_full": [],
        "chronological_age_present": true,
        "full_phenoage_eligible": true
      },
      "all_optimal": true,
      "recommendation": "maintain current protocol",
      "genetics_provided": false,
      "dna_repair_genotype_provided": false,
      "compound_queries_merged_from_dna_repair": 0
    },
    "disclaimer": "Research Use Only. Biological age estimation follows published PhenoAge transforms; acceleration labels are CrisPRO UX thresholds, not PhenoAge classifications. Do not use for clinical decisions without a qualified clinician. Polygenic scores for complex traits and parental lifespan typically explain only a small fraction of phenotypic variance (often on the order of R\u00b2 \u2248 0.02\u20130.08 depending on endpoint, cohort, and PRS construction). This score is for research context and must not be interpreted as deterministic individual risk."
  }
};
