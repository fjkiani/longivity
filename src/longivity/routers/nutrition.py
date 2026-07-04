"""
Nutrition router — dietary analysis endpoints.

POST /api/v1/nutrition/analyze          — full dietary analysis
GET  /api/v1/nutrition/foods/search     — food search
GET  /api/v1/nutrition/foods            — list all foods
GET  /api/v1/nutrition/compounds/{id}   — compound detail
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from longivity.services.nutrition_service import get_nutrition_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/nutrition", tags=["nutrition"])


# ── Request / Response models ─────────────────────────────────────────────────

class FoodItem(BaseModel):
    name: str = Field(..., description="Food name (e.g. 'blueberries', 'salmon', 'broccoli')")
    servings: float = Field(default=1.0, ge=0.1, le=20.0, description="Number of servings")


class NutritionAnalyzeRequest(BaseModel):
    foods: list[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of food names to analyze",
        examples=[["blueberries", "salmon", "broccoli", "green_tea", "walnuts"]],
    )
    age: int | None = Field(default=None, ge=18, le=120, description="Patient age (optional)")
    sex: str | None = Field(default=None, pattern="^(male|female|other)$", description="Patient sex (optional)")
    include_gap_analysis: bool = Field(default=True, description="Include supplement gap analysis")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/analyze")
async def analyze_diet(request: NutritionAnalyzeRequest) -> dict:
    """
    Analyze a dietary pattern and return longevity hallmark coverage scores.

    Maps foods → active longevity compounds → hallmark coverage [0-1] for each
    of the 9 Lopez-Otin hallmarks of aging. Identifies dietary gaps and
    recommends supplements to fill them.

    Returns:
        - foods_recognized / foods_unrecognized
        - active_compounds: list of longevity compounds present in diet
        - hallmark_scores: coverage score + tier per hallmark
        - gap_analysis: gaps, priority supplements, dietary strengths
        - overall_dietary_score: mean hallmark coverage [0-1]
        - overall_tier: STRONG / MODERATE / WEAK / INSUFFICIENT
    """
    svc = get_nutrition_service()
    try:
        result = svc.analyze_diet(
            foods=request.foods,
            age=request.age,
            sex=request.sex,
            include_gap_analysis=request.include_gap_analysis,
        )
        return result
    except Exception as e:
        logger.error(f"Nutrition analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Nutrition analysis failed: {str(e)}",
        )


@router.get("/foods/search")
async def search_foods(
    q: str = Query(..., min_length=2, max_length=100, description="Search query"),
    limit: int = Query(default=10, ge=1, le=50),
) -> dict:
    """
    Search foods by name fragment.

    Returns matching foods with their compound mappings.
    """
    svc = get_nutrition_service()
    results = svc.search_foods(q, limit=limit)
    return {
        "query": q,
        "results": results,
        "count": len(results),
    }


@router.get("/foods")
async def list_foods(
    category: str | None = Query(default=None, description="Filter by category"),
) -> dict:
    """
    List all foods in the database with their compound mappings.

    Optional: filter by category (berries, cruciferous_vegetables, fatty_fish, etc.)
    """
    svc = get_nutrition_service()
    all_foods = svc.list_all_foods()
    if category:
        all_foods = [f for f in all_foods if f["category"] == category]
    categories = sorted(set(f["category"] for f in all_foods))
    return {
        "foods": all_foods,
        "count": len(all_foods),
        "categories": categories,
    }


@router.get("/compounds/{compound_id}")
async def get_compound(compound_id: str) -> dict:
    """
    Get compound detail with hallmark links, mechanisms, and PMIDs.
    """
    svc = get_nutrition_service()
    compound = svc.get_compound_detail(compound_id)
    if not compound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compound '{compound_id}' not found. Use GET /api/v1/nutrition/foods to discover available compounds.",
        )
    return compound
