"""
NutritionService — maps dietary inputs to longevity hallmark coverage.

Architecture:
  FoodNutrientMapper   : food name → active longevity compounds
  CompoundHallmarkMapper: compound → hallmark links (from longevity_compound_hallmark_map.json)
  NutritionHallmarkScorer: aggregate hallmark coverage scores [0-1] per hallmark
  DietaryGapAnalyzer   : identify hallmarks with low dietary coverage → recommend supplements

Usage:
    svc = NutritionService()
    result = svc.analyze_diet(foods=["blueberries", "salmon", "broccoli"], age=45, sex="male")
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Resource paths ─────────────────────────────────────────────────────────────
_RESOURCES_DIR = Path(__file__).parent.parent / "resources" / "longevity"
_FOOD_COMPOUND_MAP_PATH = _RESOURCES_DIR / "food_compound_map.json"
_COMPOUND_HALLMARK_MAP_PATH = _RESOURCES_DIR / "longevity_compound_hallmark_map.json"

# ── Hallmark display names ─────────────────────────────────────────────────────
HALLMARK_DISPLAY = {
    "genomic_instability":              "Genomic Instability",
    "telomere_attrition":               "Telomere Attrition",
    "epigenetic_alterations":           "Epigenetic Alterations",
    "loss_of_proteostasis":             "Loss of Proteostasis",
    "nutrient_sensing":                 "Deregulated Nutrient Sensing",
    "mitochondrial_dysfunction":        "Mitochondrial Dysfunction",
    "cellular_senescence":              "Cellular Senescence",
    "stem_cell_exhaustion":             "Stem Cell Exhaustion",
    "altered_intercellular_communication": "Altered Intercellular Communication",
    "disabled_macroautophagy":          "Disabled Macroautophagy",
    "chronic_inflammation":             "Chronic Inflammation (Inflammaging)",
    "dysbiosis":                        "Gut Dysbiosis",
}

# Coverage tier thresholds
COVERAGE_TIERS = {
    "STRONG":       (0.60, 1.00),
    "MODERATE":     (0.35, 0.60),
    "WEAK":         (0.15, 0.35),
    "INSUFFICIENT": (0.00, 0.15),
}


def _load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


class FoodNutrientMapper:
    """Maps food names to active longevity compound IDs."""

    def __init__(self):
        data = _load_json(_FOOD_COMPOUND_MAP_PATH)
        # Build flat lookup: normalized_name → {compounds, display_name, notes, ...}
        self._map: dict[str, dict] = {}
        for category, foods in data.get("categories", {}).items():
            for food_key, food_data in foods.items():
                # Index by food_key (e.g. "blueberries") and display_name (e.g. "Blueberries")
                self._map[food_key.lower()] = {**food_data, "category": category, "food_key": food_key}
                self._map[food_data["display_name"].lower()] = {**food_data, "category": category, "food_key": food_key}

    def lookup(self, food_name: str) -> dict | None:
        """Return food data for a given food name (case-insensitive, fuzzy)."""
        key = food_name.lower().strip()
        if key in self._map:
            return self._map[key]
        # Partial match
        for k, v in self._map.items():
            if key in k or k in key:
                return v
        return None

    def get_compounds(self, food_name: str) -> list[str]:
        """Return list of compound_ids for a food, or [] if not found."""
        data = self.lookup(food_name)
        return data["compounds"] if data else []

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """Search foods by name fragment."""
        q = query.lower().strip()
        seen_keys = set()
        results = []
        for k, v in self._map.items():
            if q in k and v["food_key"] not in seen_keys:
                seen_keys.add(v["food_key"])
                results.append({
                    "food_key": v["food_key"],
                    "display_name": v["display_name"],
                    "category": v["category"],
                    "compounds": v["compounds"],
                    "serving_unit": v.get("serving_unit", ""),
                    "notes": v.get("notes", ""),
                })
                if len(results) >= limit:
                    break
        return results

    def list_all(self) -> list[dict]:
        """Return all unique foods."""
        seen = set()
        results = []
        for v in self._map.values():
            if v["food_key"] not in seen:
                seen.add(v["food_key"])
                results.append({
                    "food_key": v["food_key"],
                    "display_name": v["display_name"],
                    "category": v["category"],
                    "compounds": v["compounds"],
                    "serving_unit": v.get("serving_unit", ""),
                })
        return sorted(results, key=lambda x: (x["category"], x["display_name"]))


class CompoundHallmarkMapper:
    """Maps compound_ids to hallmark links with weights."""

    def __init__(self):
        data = _load_json(_COMPOUND_HALLMARK_MAP_PATH)
        self._compounds: dict[str, dict] = {}
        for c in data.get("compounds", []):
            self._compounds[c["compound_id"]] = c

    def get_hallmarks(self, compound_id: str) -> list[dict]:
        """Return hallmark_links for a compound."""
        c = self._compounds.get(compound_id)
        return c["hallmark_links"] if c else []

    def get_compound(self, compound_id: str) -> dict | None:
        return self._compounds.get(compound_id)

    @property
    def all_hallmarks(self) -> set[str]:
        hallmarks = set()
        for c in self._compounds.values():
            for link in c.get("hallmark_links", []):
                hallmarks.add(link["hallmark"])
        return hallmarks

    def max_possible_weight(self, hallmark: str) -> float:
        """Sum of all compound weights for a given hallmark (denominator for coverage)."""
        total = 0.0
        for c in self._compounds.values():
            for link in c.get("hallmark_links", []):
                if link["hallmark"] == hallmark:
                    total += link.get("weight", 0.5)
        return total


class NutritionHallmarkScorer:
    """Scores hallmark coverage from a set of active dietary compounds."""

    def __init__(self, compound_mapper: CompoundHallmarkMapper):
        self._mapper = compound_mapper

    def score(self, active_compounds: set[str]) -> dict[str, dict]:
        """
        Score hallmark coverage for a set of active compounds.

        Returns:
            {hallmark: {"score": float, "tier": str, "covered_compounds": list, "max_weight": float}}
        """
        hallmarks = self._mapper.all_hallmarks
        scores = {}

        for hallmark in hallmarks:
            max_weight = self._mapper.max_possible_weight(hallmark)
            if max_weight == 0:
                continue

            covered = []
            achieved_weight = 0.0
            for compound_id in active_compounds:
                for link in self._mapper.get_hallmarks(compound_id):
                    if link["hallmark"] == hallmark:
                        achieved_weight += link.get("weight", 0.5)
                        covered.append({
                            "compound_id": compound_id,
                            "weight": link.get("weight", 0.5),
                            "mechanism": link.get("mechanism", ""),
                        })

            coverage = min(achieved_weight / max_weight, 1.0)
            tier = "INSUFFICIENT"
            for t, (lo, hi) in COVERAGE_TIERS.items():
                if lo <= coverage <= hi:
                    tier = t
                    break

            scores[hallmark] = {
                "score": round(coverage, 3),
                "tier": tier,
                "display_name": HALLMARK_DISPLAY.get(hallmark, hallmark),
                "covered_compounds": covered,
                "achieved_weight": round(achieved_weight, 3),
                "max_weight": round(max_weight, 3),
            }

        return scores


class DietaryGapAnalyzer:
    """Identifies hallmark gaps and recommends supplements to fill them."""

    def __init__(self, compound_mapper: CompoundHallmarkMapper):
        self._mapper = compound_mapper

    def analyze_gaps(
        self,
        hallmark_scores: dict[str, dict],
        active_compounds: set[str],
        age: int | None = None,
        sex: str | None = None,
    ) -> dict:
        """
        Identify hallmarks with WEAK or INSUFFICIENT dietary coverage.
        Recommend the highest-impact compounds not yet in the diet.

        Returns:
            {
                "gaps": [{"hallmark": str, "tier": str, "score": float, "top_recommendations": list}],
                "priority_supplements": [{"compound_id": str, "display_name": str, "addresses_hallmarks": list, "priority_score": float}],
                "dietary_strengths": [{"hallmark": str, "tier": str, "score": float}],
                "overall_dietary_score": float,
            }
        """
        gaps = []
        strengths = []

        for hallmark, data in hallmark_scores.items():
            if data["tier"] in ("WEAK", "INSUFFICIENT"):
                # Find top compounds for this hallmark not already in diet
                candidates = []
                for c in self._mapper._compounds.values():
                    if c["compound_id"] in active_compounds:
                        continue
                    for link in c.get("hallmark_links", []):
                        if link["hallmark"] == hallmark:
                            candidates.append({
                                "compound_id": c["compound_id"],
                                "display_name": c.get("display_name", c["compound_id"]),
                                "weight": link.get("weight", 0.5),
                                "mechanism": link.get("mechanism", ""),
                            })
                candidates.sort(key=lambda x: x["weight"], reverse=True)
                gaps.append({
                    "hallmark": hallmark,
                    "display_name": data["display_name"],
                    "tier": data["tier"],
                    "score": data["score"],
                    "top_recommendations": candidates[:3],
                })
            else:
                strengths.append({
                    "hallmark": hallmark,
                    "display_name": data["display_name"],
                    "tier": data["tier"],
                    "score": data["score"],
                })

        # Rank supplements by how many gaps they address × weight
        supplement_impact: dict[str, dict] = {}
        for gap in gaps:
            for rec in gap["top_recommendations"]:
                cid = rec["compound_id"]
                if cid not in supplement_impact:
                    supplement_impact[cid] = {
                        "compound_id": cid,
                        "display_name": rec["display_name"],
                        "addresses_hallmarks": [],
                        "priority_score": 0.0,
                    }
                supplement_impact[cid]["addresses_hallmarks"].append(gap["hallmark"])
                supplement_impact[cid]["priority_score"] += rec["weight"] * (1.0 - gap["score"])

        priority_supplements = sorted(
            supplement_impact.values(),
            key=lambda x: x["priority_score"],
            reverse=True,
        )[:5]

        # Overall dietary score = mean of all hallmark scores
        all_scores = [v["score"] for v in hallmark_scores.values()]
        overall = round(sum(all_scores) / len(all_scores), 3) if all_scores else 0.0

        return {
            "gaps": sorted(gaps, key=lambda x: x["score"]),
            "priority_supplements": priority_supplements,
            "dietary_strengths": sorted(strengths, key=lambda x: x["score"], reverse=True),
            "overall_dietary_score": overall,
            "overall_tier": _score_to_tier(overall),
        }


def _score_to_tier(score: float) -> str:
    for t, (lo, hi) in COVERAGE_TIERS.items():
        if lo <= score <= hi:
            return t
    return "INSUFFICIENT"


class NutritionService:
    """
    Main entry point for dietary analysis.
    Instantiate once and reuse (singleton pattern).
    """

    def __init__(self):
        self._food_mapper = FoodNutrientMapper()
        self._compound_mapper = CompoundHallmarkMapper()
        self._scorer = NutritionHallmarkScorer(self._compound_mapper)
        self._gap_analyzer = DietaryGapAnalyzer(self._compound_mapper)

    def analyze_diet(
        self,
        foods: list[str],
        age: int | None = None,
        sex: str | None = None,
        include_gap_analysis: bool = True,
    ) -> dict:
        """
        Full dietary analysis: foods → compounds → hallmark coverage → gaps.

        Args:
            foods: list of food names (e.g. ["blueberries", "salmon", "broccoli"])
            age: patient age (optional, for age-specific recommendations)
            sex: "male" | "female" | None
            include_gap_analysis: whether to run gap analysis (default True)

        Returns:
            {
                "foods_recognized": list,
                "foods_unrecognized": list,
                "active_compounds": list,
                "hallmark_scores": dict,
                "gap_analysis": dict,
                "overall_dietary_score": float,
                "overall_tier": str,
                "disclaimer": str,
            }
        """
        recognized = []
        unrecognized = []
        active_compounds: set[str] = set()
        food_details = []

        for food in foods:
            data = self._food_mapper.lookup(food)
            if data:
                recognized.append(food)
                active_compounds.update(data["compounds"])
                food_details.append({
                    "input": food,
                    "matched": data["display_name"],
                    "category": data["category"],
                    "compounds": data["compounds"],
                    "notes": data.get("notes", ""),
                })
            else:
                unrecognized.append(food)

        hallmark_scores = self._scorer.score(active_compounds)

        result: dict[str, Any] = {
            "foods_recognized": recognized,
            "foods_unrecognized": unrecognized,
            "food_details": food_details,
            "active_compounds": sorted(active_compounds),
            "compound_count": len(active_compounds),
            "hallmark_scores": hallmark_scores,
            "overall_dietary_score": round(
                sum(v["score"] for v in hallmark_scores.values()) / max(len(hallmark_scores), 1), 3
            ),
            "overall_tier": _score_to_tier(
                sum(v["score"] for v in hallmark_scores.values()) / max(len(hallmark_scores), 1)
            ),
            "disclaimer": (
                "Dietary analysis is research-use only (RUO). "
                "Compound bioavailability varies by preparation method, gut microbiome, and individual genetics. "
                "This is not medical advice."
            ),
        }

        if include_gap_analysis:
            result["gap_analysis"] = self._gap_analyzer.analyze_gaps(
                hallmark_scores, active_compounds, age=age, sex=sex
            )

        return result

    def search_foods(self, query: str, limit: int = 10) -> list[dict]:
        """Search foods by name fragment."""
        return self._food_mapper.search(query, limit=limit)

    def get_compound_detail(self, compound_id: str) -> dict | None:
        """Get compound detail with hallmark links."""
        return self._compound_mapper.get_compound(compound_id)

    def list_all_foods(self) -> list[dict]:
        """Return all foods in the database."""
        return self._food_mapper.list_all()


# ── Singleton ──────────────────────────────────────────────────────────────────
_nutrition_service: NutritionService | None = None


def get_nutrition_service() -> NutritionService:
    global _nutrition_service
    if _nutrition_service is None:
        _nutrition_service = NutritionService()
    return _nutrition_service
