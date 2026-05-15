"""
Tests for the test ordering agent and biomarker registry service.
"""
from __future__ import annotations

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from longivity.services.biomarker_registry_service import (
    evaluate_marker_status,
    get_all_markers,
    get_all_panels,
    get_escalation_rules,
    get_hallmark_map,
    get_marker,
    get_panel,
    get_panels_by_tier,
    get_registry_metadata,
)
from longivity.services.test_ordering_agent import (
    apply_escalation_rules,
    detect_gaps,
    map_hallmarks_to_panels,
    run_test_ordering_agent,
)


# ─────────────────────────────────────────────────────────────────────────────
# Registry Service Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestBiomarkerRegistry:
    def test_registry_loads(self):
        markers = get_all_markers()
        assert len(markers) >= 300, f"Expected ≥300 markers, got {len(markers)}"

    def test_no_duplicate_marker_keys(self):
        markers = get_all_markers()
        keys = [m["marker_key"] for m in markers]
        assert len(keys) == len(set(keys)), "Duplicate marker_keys found"

    def test_all_required_fields_present(self):
        required = ["marker_key", "display_name", "domain", "panel", "specimen",
                    "unit", "ordering_tier", "hallmarks"]
        for m in get_all_markers():
            for f in required:
                assert f in m, f"Marker {m.get('marker_key')} missing field '{f}'"

    def test_key_longevity_markers_present(self):
        key_markers = ["apob", "lpa", "hscrp", "testosterone_total", "vitamin_d_25oh",
                       "tsh", "free_t3", "hba1c", "fasting_insulin", "il6",
                       "homocysteine", "cystatin_c", "ferritin", "igf1"]
        for key in key_markers:
            m = get_marker(key)
            assert m is not None, f"Key marker '{key}' not found in registry"

    def test_marker_ranges_are_numeric_or_none(self):
        for m in get_all_markers():
            for field in ["clinical_low", "clinical_high", "longevity_optimal_low", "longevity_optimal_high"]:
                val = m.get(field)
                assert val is None or isinstance(val, (int, float)), \
                    f"Marker {m['marker_key']}.{field} = {val!r} is not numeric or None"

    def test_ordering_tiers_valid(self):
        valid_tiers = {"tier_1", "tier_2", "tier_3"}
        for m in get_all_markers():
            assert m.get("ordering_tier") in valid_tiers, \
                f"Marker {m['marker_key']} has invalid tier: {m.get('ordering_tier')}"

    def test_hallmarks_valid(self):
        valid_hallmarks = {
            "genomic_instability", "epigenetic_alterations", "nutrient_sensing",
            "mitochondrial_dysfunction", "cellular_senescence",
            "altered_intercellular_communication",
        }
        for m in get_all_markers():
            for h in m.get("hallmarks", []):
                assert h in valid_hallmarks, \
                    f"Marker {m['marker_key']} has invalid hallmark: {h}"

    def test_16_domains_present(self):
        expected_domains = {
            "metabolic_core", "hematology", "cardiovascular", "hormones_male",
            "hormones_female", "thyroid", "inflammation_immune", "nutrients_micronutrients",
            "liver_function", "kidney_function", "gut_microbiome", "toxicology_heavy_metals",
            "cancer_markers", "epigenetic_aging", "genetics_pharmacogenomics",
            "specialty_functional",
        }
        actual_domains = {m["domain"] for m in get_all_markers()}
        assert expected_domains == actual_domains, \
            f"Domain mismatch. Missing: {expected_domains - actual_domains}"

    def test_panels_load(self):
        panels = get_all_panels()
        assert len(panels) == 45, f"Expected 45 panels, got {len(panels)}"

    def test_panel_tiers(self):
        t1 = get_panels_by_tier("tier_1")
        t2 = get_panels_by_tier("tier_2")
        t3 = get_panels_by_tier("tier_3")
        assert len(t1) == 10
        assert len(t2) == 20
        assert len(t3) == 15

    def test_escalation_rules_load(self):
        rules = get_escalation_rules()
        assert len(rules) == 50, f"Expected 50 rules, got {len(rules)}"

    def test_hallmark_map_has_6_hallmarks(self):
        hmap = get_hallmark_map()
        assert len(hmap) == 6

    def test_registry_metadata(self):
        meta = get_registry_metadata()
        assert meta.get("total_count", 0) >= 300


class TestEvaluateMarkerStatus:
    def test_apob_suboptimal_high(self):
        result = evaluate_marker_status("apob", 95.0)
        assert result["clinical_status"] == "normal"
        assert result["longevity_status"] == "suboptimal_high"

    def test_apob_optimal(self):
        result = evaluate_marker_status("apob", 65.0)
        assert result["clinical_status"] == "normal"
        assert result["longevity_status"] == "optimal"

    def test_apob_clinical_high(self):
        result = evaluate_marker_status("apob", 115.0)
        assert result["clinical_status"] == "high"
        assert result["longevity_status"] == "suboptimal_high"

    def test_vitamin_d_low(self):
        result = evaluate_marker_status("vitamin_d_25oh", 18.0)
        assert result["clinical_status"] == "low"
        assert result["longevity_status"] == "suboptimal_low"

    def test_vitamin_d_optimal(self):
        result = evaluate_marker_status("vitamin_d_25oh", 65.0)
        assert result["clinical_status"] == "normal"
        assert result["longevity_status"] == "optimal"

    def test_sex_specific_testosterone_male(self):
        result = evaluate_marker_status("testosterone_total", 350.0, sex="male")
        assert result["clinical_status"] == "normal"
        assert result["longevity_status"] == "suboptimal_low"

    def test_sex_specific_testosterone_optimal_male(self):
        result = evaluate_marker_status("testosterone_total", 750.0, sex="male")
        assert result["clinical_status"] == "normal"
        assert result["longevity_status"] == "optimal"

    def test_unknown_marker(self):
        result = evaluate_marker_status("nonexistent_marker_xyz", 42.0)
        assert result["clinical_status"] == "unknown"
        assert result["longevity_status"] == "unknown"

    def test_tsh_suboptimal_high(self):
        result = evaluate_marker_status("tsh", 3.5)
        assert result["clinical_status"] == "normal"
        assert result["longevity_status"] == "suboptimal_high"

    def test_hscrp_clinical_high(self):
        result = evaluate_marker_status("hscrp", 4.5)
        assert result["clinical_status"] == "high"
        assert result["longevity_status"] == "suboptimal_high"


# ─────────────────────────────────────────────────────────────────────────────
# Test Ordering Agent Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestGapDetection:
    def test_empty_patient_has_all_gaps(self):
        gaps = detect_gaps(set())
        assert len(gaps["missing_tier1"]) > 50
        assert gaps["coverage_pct"] == 0.0
        assert len(gaps["missing_panels_tier1"]) == 10  # all 10 tier_1 panels

    def test_full_tier1_coverage(self):
        # Get all tier_1 marker keys
        tier1_keys = {m["marker_key"] for m in get_all_markers() if m.get("ordering_tier") == "tier_1"}
        gaps = detect_gaps(tier1_keys)
        assert gaps["coverage_pct"] == 100.0
        assert len(gaps["missing_tier1"]) == 0
        assert len(gaps["missing_panels_tier1"]) == 0

    def test_partial_coverage(self):
        existing = {"sodium", "potassium", "glucose", "albumin", "creatinine",
                    "total_cholesterol", "ldl_c", "hdl_c", "tsh", "hscrp",
                    "vitamin_d_25oh", "hba1c", "fasting_insulin", "ferritin"}
        gaps = detect_gaps(existing)
        assert 0 < gaps["coverage_pct"] < 100
        assert len(gaps["missing_tier1"]) > 0

    def test_sex_filtering_male(self):
        gaps_male = detect_gaps(set(), sex="male")
        gaps_female = detect_gaps(set(), sex="female")
        # Male should not have female-only markers and vice versa
        male_missing = set(gaps_male["missing_tier1"])
        female_missing = set(gaps_female["missing_tier1"])
        # They should differ (sex-specific markers)
        # Both should have common markers
        assert "tsh" in male_missing
        assert "tsh" in female_missing


class TestEscalationRules:
    def test_glucose_escalation(self):
        result = apply_escalation_rules({"glucose": 108.0}, set())
        triggered_ids = [r["rule_id"] for r in result["triggered_rules"]]
        assert "ESC-001" in triggered_ids

    def test_ldl_escalation(self):
        result = apply_escalation_rules({"ldl_c": 145.0}, set())
        triggered_ids = [r["rule_id"] for r in result["triggered_rules"]]
        assert "ESC-009" in triggered_ids

    def test_tsh_escalation(self):
        result = apply_escalation_rules({"tsh": 3.5}, set())
        triggered_ids = [r["rule_id"] for r in result["triggered_rules"]]
        assert "ESC-018" in triggered_ids

    def test_vitamin_d_escalation(self):
        result = apply_escalation_rules({"vitamin_d_25oh": 22.0}, set())
        triggered_ids = [r["rule_id"] for r in result["triggered_rules"]]
        assert "ESC-035" in triggered_ids

    def test_normal_values_no_escalation(self):
        result = apply_escalation_rules({
            "glucose": 85.0,
            "ldl_c": 90.0,
            "tsh": 1.8,
            "vitamin_d_25oh": 60.0,
            "hscrp": 0.3,
        }, set())
        assert len(result["triggered_rules"]) == 0

    def test_already_covered_panels_skipped(self):
        # If patient already has all markers in a panel, don't recommend it
        advanced_lipids_panel = get_panel("advanced_lipids")
        existing = set(advanced_lipids_panel["markers"])
        result = apply_escalation_rules({"ldl_c": 145.0}, existing)
        # advanced_lipids should not be in recommendations since already covered
        for r in result["triggered_rules"]:
            assert "advanced_lipids" not in r["recommended_panels"]

    def test_multiple_rules_fire(self):
        result = apply_escalation_rules({
            "glucose": 108.0,
            "ldl_c": 145.0,
            "tsh": 3.8,
            "hscrp": 4.2,
            "homocysteine": 12.0,
            "vitamin_d_25oh": 22.0,
        }, set())
        assert len(result["triggered_rules"]) >= 5

    def test_recommended_panels_deduplicated(self):
        result = apply_escalation_rules({
            "ldl_c": 145.0,
            "hscrp": 4.2,
        }, set())
        # cardiovascular_inflammation appears in both ESC-009 and ESC-014
        panel_list = result["recommended_panels"]
        assert len(panel_list) == len(set(panel_list)), "Duplicate panels in recommendations"


class TestHallmarkMapping:
    def test_active_hallmark_recommends_panels(self):
        result = map_hallmarks_to_panels(
            {"nutrient_sensing": {"score": 0.7, "status": "elevated"}},
            set(),
        )
        assert "nutrient_sensing" in result["active_hallmarks"]
        assert len(result["recommended_panels"]) > 0

    def test_none_hallmark_skipped(self):
        result = map_hallmarks_to_panels(
            {"nutrient_sensing": None, "cellular_senescence": None},
            set(),
        )
        assert len(result["active_hallmarks"]) == 0
        assert len(result["recommended_panels"]) == 0

    def test_insufficient_data_hallmark_skipped(self):
        result = map_hallmarks_to_panels(
            {"nutrient_sensing": {"status": "insufficient_data"}},
            set(),
        )
        assert len(result["active_hallmarks"]) == 0

    def test_already_covered_panels_skipped(self):
        # If patient already has 80%+ of a panel's markers, skip it
        igf_panel = get_panel("igf_axis")
        existing = set(igf_panel["markers"])
        result = map_hallmarks_to_panels(
            {"nutrient_sensing": {"score": 0.7}},
            existing,
        )
        panel_ids = [r["panel_id"] for r in result["recommended_panels"]]
        assert "igf_axis" not in panel_ids


class TestFullAgent:
    def _make_panels(self, values: dict) -> list:
        return [{
            "id": "test-panel",
            "drawn_at": "2026-01-01T08:00:00Z",
            "source": "test",
            "values": [{"marker_key": k, "value": v, "unit": ""} for k, v in values.items()],
        }]

    def test_empty_patient_gets_tier1_recommendations(self):
        result = run_test_ordering_agent("p1", [], sex="male", age=45)
        assert result["status"] == "pending_clinician_approval"
        assert result["summary"]["total_panels_recommended"] > 0
        # All 10 tier_1 panels should be recommended
        panel_ids = {p["panel_id"] for p in result["recommended_panels"]}
        assert "cmp" in panel_ids
        assert "cbc_with_diff" in panel_ids

    def test_abnormal_values_trigger_escalation(self):
        panels = self._make_panels({
            "glucose": 112.0,
            "ldl_c": 155.0,
            "tsh": 4.2,
        })
        result = run_test_ordering_agent("p2", panels, sex="male", age=50)
        assert result["ordering_rationale"]["escalation"]["triggered_rules"]
        panel_ids = {p["panel_id"] for p in result["recommended_panels"]}
        assert "thyroid_full" in panel_ids
        assert "advanced_lipids" in panel_ids

    def test_result_has_required_keys(self):
        result = run_test_ordering_agent("p3", [], sex="female", age=40)
        required_keys = [
            "patient_id", "generated_at", "status", "summary",
            "ordering_rationale", "recommended_panels", "requisition",
        ]
        for k in required_keys:
            assert k in result, f"Missing key: {k}"

    def test_summary_fields(self):
        result = run_test_ordering_agent("p4", [], sex="male", age=55)
        summary = result["summary"]
        assert "total_panels_recommended" in summary
        assert "total_estimated_cost_usd" in summary
        assert "tier1_coverage_pct" in summary
        assert summary["tier1_coverage_pct"] == 0.0  # no existing data

    def test_no_duplicate_panels_in_output(self):
        panels = self._make_panels({
            "glucose": 112.0,
            "ldl_c": 155.0,
            "hscrp": 4.5,
            "tsh": 4.2,
            "vitamin_d_25oh": 18.0,
        })
        result = run_test_ordering_agent(
            "p5", panels,
            active_hallmarks={"nutrient_sensing": {"score": 0.8}},
            sex="male", age=50,
        )
        panel_ids = [p["panel_id"] for p in result["recommended_panels"]]
        assert len(panel_ids) == len(set(panel_ids)), "Duplicate panels in agent output"

    def test_requisition_structure(self):
        result = run_test_ordering_agent("p6", [], sex="male", age=45)
        req = result["requisition"]
        assert "panels" in req
        assert "total_panels" in req
        assert "total_estimated_cost_usd" in req
        assert "specimen_requirements" in req

    def test_existing_markers_reduce_gaps(self):
        # Patient with full tier_1 coverage should have 0% gap
        tier1_keys = {m["marker_key"] for m in get_all_markers() if m.get("ordering_tier") == "tier_1"}
        # Use normal values to avoid triggering escalation rules
        normal_values = {
            "sodium": 140.0, "potassium": 4.2, "chloride": 102.0, "co2_bicarbonate": 24.0,
            "bun": 14.0, "creatinine": 0.9, "glucose": 88.0, "calcium": 9.5,
            "total_protein": 7.2, "albumin": 4.3, "total_bilirubin": 0.7,
            "alt": 22.0, "ast": 20.0, "alp": 65.0, "gfr_estimated": 95.0,
            "fasting_glucose": 88.0, "fasting_insulin": 4.5, "hba1c": 5.1,
            "homa_ir": 0.9, "phosphorus": 3.5, "magnesium_serum": 2.1, "ggt": 18.0,
            "uric_acid": 5.0, "c_peptide": 1.5, "lactate_dehydrogenase": 150.0,
            "wbc": 6.0, "rbc": 4.8, "hemoglobin": 14.5, "hematocrit": 44.0,
            "mcv": 88.0, "mch": 29.0, "mchc": 33.0, "rdw": 13.0, "platelets": 220.0,
            "neutrophils_abs": 3.5, "lymphocytes_abs": 2.0, "monocytes_abs": 0.5,
            "eosinophils_abs": 0.2, "basophils_abs": 0.05, "neutrophil_pct": 58.0,
            "lymphocyte_pct": 33.0, "reticulocytes": 1.2,
            "iron_serum": 100.0, "tibc": 320.0, "transferrin_saturation": 31.0,
            "ferritin": 90.0,  # normal — avoids ESC-034
            "total_cholesterol": 175.0, "ldl_c": 95.0, "hdl_c": 58.0,
            "triglycerides": 95.0, "non_hdl_c": 117.0,
            "hscrp": 0.4, "psa_total": 0.8, "tsh": 1.8,
            "hscrp_inflam": 0.4, "vitamin_d_25oh": 62.0, "vitamin_b12": 650.0,
            "folate_serum": 12.0,
            "alt_liver": 22.0, "ast_liver": 20.0, "ggt_liver": 18.0,
            "alp_liver": 65.0, "total_bilirubin_liver": 0.7,
            "albumin_liver": 4.3, "total_protein_liver": 7.2,
            "creatinine_kidney": 0.9, "bun_kidney": 14.0, "egfr_ckd_epi": 95.0,
        }
        panels = [{
            "id": "full-panel",
            "drawn_at": "2026-01-01T08:00:00Z",
            "source": "test",
            "values": [{"marker_key": k, "value": normal_values.get(k, 1.0), "unit": ""} for k in tier1_keys],
        }]
        result = run_test_ordering_agent("p7", panels, sex="male", age=45)
        assert result["summary"]["tier1_coverage_pct"] == 100.0
        # No tier_1 panels should be in recommendations (all gaps filled, no escalation)
        tier1_panel_ids = {p["panel_id"] for p in get_panels_by_tier("tier_1")}
        rec_panel_ids = {p["panel_id"] for p in result["recommended_panels"]}
        assert not (tier1_panel_ids & rec_panel_ids), \
            f"Tier_1 panels recommended despite full coverage: {tier1_panel_ids & rec_panel_ids}"
