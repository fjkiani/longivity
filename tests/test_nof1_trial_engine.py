"""Tests for N-of-1 Trial Engine."""

import pytest
from datetime import date
from longivity.services.nof1_trial_engine import (
    generate_nof1_protocol,
    COMPOUND_BIOMARKER_EFFECTS,
    MONITORING_SCHEDULE,
)


BASELINE_BIOMARKERS = {
    "albumin": 3.8,
    "creatinine": 1.3,
    "glucose_serum": 130.0,
    "crp_mg_l": 3.5,
    "lymphocyte_pct": 22.0,
    "mcv_fl": 95.0,
    "rdw_pct": 15.5,
    "alkaline_phosphatase_u_l": 110.0,
    "wbc_1000_ul": 9.5,
}


class TestProtocolGeneration:
    def test_generates_protocol_for_omega3(self):
        protocol = generate_nof1_protocol(
            patient_id="TEST-001",
            age=65,
            baseline_biomarkers=BASELINE_BIOMARKERS,
            compound_id="omega_3",
            start_date=date(2025, 1, 1),
        )
        assert protocol is not None
        assert "trial_id" in protocol
        assert protocol["trial_id"].startswith("NOF1-")

    def test_omega3_is_mr_validated_tier(self):
        protocol = generate_nof1_protocol(
            patient_id="TEST-001",
            age=65,
            baseline_biomarkers=BASELINE_BIOMARKERS,
            compound_id="omega_3",
            start_date=date(2025, 1, 1),
        )
        assert protocol["evidence_tier"] == "MR_VALIDATED"
        assert protocol["mr_anchor"] is not None
        assert protocol["mr_anchor"]["p_value"] == 0.0086
        assert "Fabian 2025" in protocol["mr_anchor"]["citation"]

    def test_berberine_is_rct_tier(self):
        protocol = generate_nof1_protocol(
            patient_id="TEST-002",
            age=55,
            baseline_biomarkers=BASELINE_BIOMARKERS,
            compound_id="berberine",
            start_date=date(2025, 1, 1),
        )
        assert protocol["evidence_tier"] == "RCT"
        assert protocol["mr_anchor"] is None

    def test_rapamycin_is_observational_tier(self):
        protocol = generate_nof1_protocol(
            patient_id="TEST-003",
            age=60,
            baseline_biomarkers=BASELINE_BIOMARKERS,
            compound_id="rapamycin",
            start_date=date(2025, 1, 1),
        )
        assert protocol["evidence_tier"] == "OBSERVATIONAL"


class TestPhaseStructure:
    def setup_method(self):
        self.protocol = generate_nof1_protocol(
            patient_id="TEST-001",
            age=65,
            baseline_biomarkers=BASELINE_BIOMARKERS,
            compound_id="omega_3",
            start_date=date(2025, 1, 1),
        )

    def test_has_four_phases(self):
        phases = self.protocol["design"]["phases"]
        assert len(phases) == 4

    def test_phase_labels_are_abcd(self):
        phases = self.protocol["design"]["phases"]
        labels = [p["phase"] for p in phases]
        assert labels == ["A", "B", "C", "D"]

    def test_phase_a_is_baseline(self):
        phase_a = self.protocol["design"]["phases"][0]
        assert phase_a["intervention"] is None
        assert phase_a["duration_weeks"] == 4

    def test_phase_b_is_treatment(self):
        phase_b = self.protocol["design"]["phases"][1]
        assert phase_b["intervention"] == "omega_3"
        assert phase_b["duration_weeks"] == 8

    def test_phase_c_is_washout(self):
        phase_c = self.protocol["design"]["phases"][2]
        assert phase_c["intervention"] is None
        assert phase_c["duration_weeks"] == 4

    def test_total_duration_is_20_weeks_without_crossover(self):
        assert self.protocol["design"]["total_duration_weeks"] == 20

    def test_primary_endpoint_is_phenoage(self):
        assert self.protocol["design"]["primary_endpoint"] == "phenoage_estimate"

    def test_primary_endpoint_timepoints(self):
        timepoints = self.protocol["design"]["primary_endpoint_timepoints_weeks"]
        assert 0 in timepoints
        assert 8 in timepoints


class TestCrossoverDesign:
    def test_crossover_adds_second_compound_in_phase_d(self):
        protocol = generate_nof1_protocol(
            patient_id="TEST-001",
            age=65,
            baseline_biomarkers=BASELINE_BIOMARKERS,
            compound_id="omega_3",
            crossover_compound_id="berberine",
            start_date=date(2025, 1, 1),
        )
        phase_d = protocol["design"]["phases"][3]
        assert phase_d["intervention"] == "berberine"
        assert protocol["crossover_compound_id"] == "berberine"
        assert protocol["crossover_evidence_tier"] == "RCT"

    def test_crossover_total_duration_is_24_weeks(self):
        protocol = generate_nof1_protocol(
            patient_id="TEST-001",
            age=65,
            baseline_biomarkers=BASELINE_BIOMARKERS,
            compound_id="omega_3",
            crossover_compound_id="berberine",
            start_date=date(2025, 1, 1),
        )
        assert protocol["design"]["total_duration_weeks"] == 24


class TestExpectedDeltas:
    def test_omega3_has_crp_delta(self):
        protocol = generate_nof1_protocol(
            patient_id="TEST-001",
            age=65,
            baseline_biomarkers=BASELINE_BIOMARKERS,
            compound_id="omega_3",
            start_date=date(2025, 1, 1),
        )
        deltas = protocol["expected_deltas"]
        crp_row = next((d for d in deltas if d["biomarker"] == "crp_mg_l"), None)
        assert crp_row is not None
        assert crp_row["expected_delta_mean"] == -0.5
        assert crp_row["direction"] == "decrease"
        assert crp_row["baseline_value"] == 3.5
        assert crp_row["expected_post_value"] == pytest.approx(3.0, abs=0.01)

    def test_berberine_has_glucose_delta(self):
        protocol = generate_nof1_protocol(
            patient_id="TEST-002",
            age=55,
            baseline_biomarkers=BASELINE_BIOMARKERS,
            compound_id="berberine",
            start_date=date(2025, 1, 1),
        )
        deltas = protocol["expected_deltas"]
        glucose_row = next((d for d in deltas if d["biomarker"] == "glucose_serum"), None)
        assert glucose_row is not None
        assert glucose_row["expected_delta_mean"] == -15.0
        assert glucose_row["expected_post_value"] == pytest.approx(115.0, abs=0.01)

    def test_unknown_biomarkers_included_with_no_delta(self):
        protocol = generate_nof1_protocol(
            patient_id="TEST-001",
            age=65,
            baseline_biomarkers=BASELINE_BIOMARKERS,
            compound_id="omega_3",
            start_date=date(2025, 1, 1),
        )
        deltas = protocol["expected_deltas"]
        # albumin is in baseline but not in omega_3 effects
        albumin_row = next((d for d in deltas if d["biomarker"] == "albumin"), None)
        assert albumin_row is not None
        assert albumin_row["expected_delta_mean"] is None
        assert albumin_row["direction"] == "unknown"


class TestMonitoringSchedule:
    def setup_method(self):
        self.protocol = generate_nof1_protocol(
            patient_id="TEST-001",
            age=65,
            baseline_biomarkers=BASELINE_BIOMARKERS,
            compound_id="omega_3",
            start_date=date(2025, 1, 1),
        )

    def test_monitoring_schedule_present(self):
        assert "monitoring_schedule" in self.protocol

    def test_wearable_tracking_present(self):
        ms = self.protocol["monitoring_schedule"]
        assert "wearable_tracking" in ms
        assert ms["wearable_tracking"]["frequency"] == "continuous"

    def test_lab_draws_present(self):
        ms = self.protocol["monitoring_schedule"]
        assert "lab_draws" in ms
        assert len(ms["lab_draws"]) > 0

    def test_primary_endpoint_draws_at_correct_weeks(self):
        ms = self.protocol["monitoring_schedule"]
        weeks = [d["week"] for d in ms["primary_endpoint_draws"]]
        assert 0 in weeks
        assert 8 in weeks


class TestPowerNote:
    def test_mr_validated_power_note_mentions_mr(self):
        protocol = generate_nof1_protocol(
            patient_id="TEST-001",
            age=65,
            baseline_biomarkers=BASELINE_BIOMARKERS,
            compound_id="omega_3",
            start_date=date(2025, 1, 1),
        )
        assert "MR_VALIDATED" in protocol["power_note"]
        assert "Mendelian Randomization" in protocol["power_note"]

    def test_observational_power_note_is_exploratory(self):
        protocol = generate_nof1_protocol(
            patient_id="TEST-003",
            age=60,
            baseline_biomarkers=BASELINE_BIOMARKERS,
            compound_id="rapamycin",
            start_date=date(2025, 1, 1),
        )
        assert "exploratory" in protocol["power_note"].lower()


class TestRUODisclaimer:
    def test_ruo_disclaimer_present(self):
        protocol = generate_nof1_protocol(
            patient_id="TEST-001",
            age=65,
            baseline_biomarkers=BASELINE_BIOMARKERS,
            compound_id="omega_3",
            start_date=date(2025, 1, 1),
        )
        assert "Research Use Only" in protocol["ruo_disclaimer"]

    def test_methodology_references_present(self):
        protocol = generate_nof1_protocol(
            patient_id="TEST-001",
            age=65,
            baseline_biomarkers=BASELINE_BIOMARKERS,
            compound_id="omega_3",
            start_date=date(2025, 1, 1),
        )
        refs = protocol["methodology_references"]
        assert len(refs) >= 2
        pmids = [r["pmid"] for r in refs]
        assert "21406327" in pmids  # Lillie 2011
        assert "23839752" in pmids  # Duan 2013
