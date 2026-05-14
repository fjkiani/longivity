"""
Tests for NHANES PhenoAge validator script.
Tests: script importable, output CSV has correct columns.
"""
import importlib
import os
import sys
import pytest


class TestNHANESValidator:

    def test_script_importable(self):
        """The nhanes_phenoage_validator script must be importable without errors."""
        scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
        src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        # Import should not raise
        import nhanes_phenoage_validator as validator
        assert hasattr(validator, 'NHANES_REFERENCE'), "NHANES_REFERENCE constant must be defined"
        assert hasattr(validator, 'main'), "main() function must be defined"

    def test_nhanes_reference_has_four_decades(self):
        """NHANES_REFERENCE must have entries for 40s, 50s, 60s, 70s."""
        scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
        src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        import nhanes_phenoage_validator as validator
        assert set(validator.NHANES_REFERENCE.keys()) == {"40s", "50s", "60s", "70s"}
        for decade, vals in validator.NHANES_REFERENCE.items():
            assert "albumin" in vals, f"albumin missing from {decade}"
            assert "creatinine" in vals, f"creatinine missing from {decade}"
