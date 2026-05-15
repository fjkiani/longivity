"""Tests for MR causal confidence tier registry."""

import pytest
from longivity.services.mr_evidence_registry import (
    get_evidence_tier,
    get_mr_records,
    get_best_mr_record,
    evidence_tier_label,
    annotate_compound_recommendation,
    MR_EVIDENCE,
    RCT_COMPOUNDS,
)


class TestEvidenceTierAssignment:
    def test_omega3_is_mr_validated(self):
        assert get_evidence_tier("omega_3") == "MR_VALIDATED"

    def test_metformin_is_mr_validated(self):
        assert get_evidence_tier("metformin") == "MR_VALIDATED"

    def test_vitamin_d3_is_mr_validated(self):
        assert get_evidence_tier("vitamin_d3") == "MR_VALIDATED"

    def test_folate_is_mr_validated(self):
        assert get_evidence_tier("folate") == "MR_VALIDATED"

    def test_berberine_is_rct(self):
        assert get_evidence_tier("berberine") == "RCT"

    def test_nmn_is_rct(self):
        assert get_evidence_tier("nmn") == "RCT"

    def test_urolithin_a_is_rct(self):
        assert get_evidence_tier("urolithin_a") == "RCT"

    def test_rapamycin_is_observational(self):
        assert get_evidence_tier("rapamycin") == "OBSERVATIONAL"

    def test_resveratrol_is_observational(self):
        assert get_evidence_tier("resveratrol") == "OBSERVATIONAL"

    def test_unknown_compound_is_observational(self):
        assert get_evidence_tier("unicorn_extract") == "OBSERVATIONAL"


class TestMRRecords:
    def test_omega3_has_two_mr_records(self):
        records = get_mr_records("omega_3")
        assert len(records) == 2

    def test_omega3_mr_records_have_required_fields(self):
        records = get_mr_records("omega_3")
        for r in records:
            assert "exposure" in r
            assert "outcome" in r
            assert "method" in r
            assert "p_value" in r
            assert "direction" in r
            assert "clock" in r
            assert "citation" in r

    def test_omega3_best_mr_record_is_lowest_pvalue(self):
        best = get_best_mr_record("omega_3")
        assert best is not None
        assert best["p_value"] == 0.0086  # PhenoAge record is lower than GrimAge 0.037

    def test_omega3_mr_fabian_2025_citation(self):
        best = get_best_mr_record("omega_3")
        assert "Fabian 2025" in best["citation"]
        assert best["doi"] == "10.1186/s40246-025-00756-3"

    def test_no_mr_records_for_rapamycin(self):
        assert get_mr_records("rapamycin") == []
        assert get_best_mr_record("rapamycin") is None

    def test_all_mr_compounds_have_p_value(self):
        for cid, records in MR_EVIDENCE.items():
            for r in records:
                assert r.get("p_value") is not None, f"{cid} record missing p_value"
                assert 0 < r["p_value"] < 1, f"{cid} p_value out of range"


class TestEvidenceTierLabel:
    def test_mr_validated_label(self):
        label = evidence_tier_label("MR_VALIDATED")
        assert "Mendelian Randomization" in label

    def test_rct_label(self):
        label = evidence_tier_label("RCT")
        assert "Randomized" in label

    def test_observational_label(self):
        label = evidence_tier_label("OBSERVATIONAL")
        assert "Observational" in label


class TestAnnotateCompoundRecommendation:
    def test_annotates_omega3_with_mr_tier(self):
        rec = {"compound": "omega_3", "overall_relevance": 0.8}
        annotated = annotate_compound_recommendation(rec)
        assert annotated["evidence_tier"] == "MR_VALIDATED"
        assert annotated["mr_anchor"] is not None
        assert annotated["mr_anchor"]["p_value"] == 0.0086

    def test_annotates_berberine_with_rct_tier(self):
        rec = {"compound": "berberine", "overall_relevance": 0.7}
        annotated = annotate_compound_recommendation(rec)
        assert annotated["evidence_tier"] == "RCT"
        assert annotated["mr_anchor"] is None

    def test_annotates_rapamycin_with_observational_tier(self):
        rec = {"compound": "rapamycin", "overall_relevance": 0.5}
        annotated = annotate_compound_recommendation(rec)
        assert annotated["evidence_tier"] == "OBSERVATIONAL"
        assert annotated["mr_anchor"] is None

    def test_annotation_is_in_place(self):
        rec = {"compound": "omega_3"}
        result = annotate_compound_recommendation(rec)
        assert result is rec  # same object


class TestIntegrationWithLevelZero:
    """Integration: compound recommendations from level0 service include evidence_tier."""

    def test_compound_recs_have_evidence_tier(self):
        import sys
        sys.path.insert(0, ".")
        from longivity.services.longevity_phenoage_level0 import run_longevity_assessment_level0

        result = run_longevity_assessment_level0({
            "age": 65,
            "biomarkers": {
                "albumin": 3.8, "creatinine": 1.3, "glucose_mg_dl": 130,
                "crp_mg_l": 3.5, "lymphocyte_pct": 22, "mcv_fl": 95,
                "rdw_pct": 15.5, "alkaline_phosphatase_u_l": 110, "wbc_1000_ul": 9.5,
            },
            "compound_queries": ["omega_3", "berberine", "rapamycin"],
        })
        recs = result.get("compound_recommendations", [])
        assert len(recs) > 0, "Expected compound recommendations for accelerated panel"
        for rec in recs:
            assert "evidence_tier" in rec, f"Missing evidence_tier in {rec.get('compound')}"
            assert rec["evidence_tier"] in ("MR_VALIDATED", "RCT", "OBSERVATIONAL")

    def test_omega3_rec_has_mr_anchor(self):
        import sys
        sys.path.insert(0, ".")
        from longivity.services.longevity_phenoage_level0 import run_longevity_assessment_level0

        result = run_longevity_assessment_level0({
            "age": 65,
            "biomarkers": {
                "albumin": 3.8, "creatinine": 1.3, "glucose_mg_dl": 130,
                "crp_mg_l": 3.5, "lymphocyte_pct": 22, "mcv_fl": 95,
                "rdw_pct": 15.5, "alkaline_phosphatase_u_l": 110, "wbc_1000_ul": 9.5,
            },
            "compound_queries": ["omega_3"],
        })
        recs = result.get("compound_recommendations", [])
        omega3_recs = [r for r in recs if r.get("compound") == "omega_3"]
        assert len(omega3_recs) == 1
        rec = omega3_recs[0]
        assert rec["evidence_tier"] == "MR_VALIDATED"
        assert rec["mr_anchor"] is not None
        assert rec["mr_anchor"]["p_value"] == 0.0086
