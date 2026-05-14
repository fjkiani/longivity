"""
Tests for expanded genetic loci (FOXO3, CETP, KLOTHO, TERT, SOD2).
"""
import pytest
from fastapi.testclient import TestClient


class TestExpandedGeneticLoci:

    def test_foxo3_annotation_in_genetic_profile(self, client: TestClient, healthy_biomarkers: dict):
        """FOXO3 rs2802292 GG should appear in genetic_profile."""
        resp = client.post("/api/v1/longevity/full_assessment", json={
            "biomarkers": healthy_biomarkers,
            "age": 50,
            "variants": {"rs2802292": {"genotype": "GG"}},
        })
        assert resp.status_code == 200, resp.text
        data = resp.json()
        gp = data.get("genetic_profile") or {}
        # Should have some annotation for rs2802292
        annotations = gp.get("variant_annotations") or gp.get("annotations") or {}
        # Accept either direct key or nested
        found = (
            "rs2802292" in str(annotations) or
            "FOXO3" in str(annotations) or
            "rs2802292" in str(gp)
        )
        assert found, f"FOXO3 rs2802292 annotation not found in genetic_profile: {gp}"

    def test_prs_score_present_with_new_loci(self, client: TestClient, healthy_biomarkers: dict):
        """PRS score should be present as top-level longevity_prs when new loci variants are provided.

        Note: PRS data lives at the top-level response key ``longevity_prs``, not inside
        ``genetic_profile``.  The new loci (FOXO3/SOD2/KLOTHO) are included in
        longevity_prs_variants.json so they contribute to the scored loci count.
        """
        resp = client.post("/api/v1/longevity/full_assessment", json={
            "biomarkers": healthy_biomarkers,
            "age": 50,
            "variants": {
                "rs2802292": {"genotype": "GG"},  # FOXO3
                "rs4880": {"genotype": "TT"},      # SOD2
                "rs9536314": {"genotype": "TC"},   # KLOTHO
            },
        })
        assert resp.status_code == 200, resp.text
        data = resp.json()
        # PRS lives at the top-level key, not inside genetic_profile
        prs = data.get("longevity_prs") or {}
        prs_str = str(prs)
        has_prs = (
            "prs" in prs_str.lower()
            or "score" in prs_str.lower()
            or "parental" in prs_str.lower()
            or "loci_scored" in prs_str.lower()
        )
        assert has_prs, (
            f"No PRS-related key found in longevity_prs response. "
            f"longevity_prs keys: {list(prs.keys())}"
        )

    def test_sod2_annotation_present(self, client: TestClient, healthy_biomarkers: dict):
        """SOD2 rs4880 should be annotated in genetic_profile."""
        resp = client.post("/api/v1/longevity/full_assessment", json={
            "biomarkers": healthy_biomarkers,
            "age": 50,
            "variants": {"rs4880": {"genotype": "TT"}},
        })
        assert resp.status_code == 200, resp.text
        data = resp.json()
        gp = data.get("genetic_profile") or {}
        found = "rs4880" in str(gp) or "SOD2" in str(gp)
        assert found, f"SOD2 rs4880 annotation not found in genetic_profile: {gp}"
