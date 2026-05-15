"""
Test Ordering Agent — 3-step deterministic agent for recommending lab test panels.

Step A: Gap Detection
    Compares patient's existing biomarker values against the required marker set
    for their age/sex/risk profile. Outputs missing_tier1, missing_tier2, missing_tier3.

Step B: Hallmark-Driven Panel Mapping
    Takes the patient's active hallmarks and maps each to required test panels
    via the hallmark_to_panels.json lookup table.

Step C: Rule-Based Escalation
    Evaluates existing biomarker values against escalation trigger rules.
    Outputs additional panels triggered by abnormal values.

No LLM required — all logic is deterministic and auditable.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from .biomarker_registry_service import (
    evaluate_marker_status,
    get_all_markers,
    get_escalation_rules,
    get_marker,
    get_panel,
    get_panels_by_tier,
    get_panels_for_hallmark,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Step A: Gap Detection
# ─────────────────────────────────────────────────────────────────────────────

def detect_gaps(
    existing_marker_keys: Set[str],
    sex: Optional[str] = None,
    age: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Identify which markers are missing from the patient's record.

    Args:
        existing_marker_keys: Set of marker_key strings already in the patient's panels.
        sex: Patient sex ("male" / "female") for sex-specific panel filtering.
        age: Patient age in years (reserved for future age-stratified logic).

    Returns:
        {
            "missing_tier1": [...],  # baseline markers not yet collected
            "missing_tier2": [...],  # expanded markers not yet collected
            "missing_tier3": [...],  # specialty markers not yet collected
            "missing_panels_tier1": [...],  # panels with ≥1 missing marker
            "coverage_pct": float,  # % of tier_1 markers present
        }
    """
    all_markers = get_all_markers()

    missing_t1, missing_t2, missing_t3 = [], [], []
    t1_total = 0

    for m in all_markers:
        key = m.get("marker_key")
        tier = m.get("ordering_tier")
        if not key or not tier:
            continue

        # Skip sex-specific markers for the wrong sex
        if m.get("sex_specific") and sex:
            domain = m.get("domain", "")
            if sex.lower() == "male" and domain == "hormones_female":
                continue
            if sex.lower() == "female" and domain == "hormones_male":
                continue

        if key not in existing_marker_keys:
            if tier == "tier_1":
                missing_t1.append(key)
            elif tier == "tier_2":
                missing_t2.append(key)
            elif tier == "tier_3":
                missing_t3.append(key)

        if tier == "tier_1":
            t1_total += 1

    # Which tier_1 panels have missing markers?
    t1_panels = get_panels_by_tier("tier_1")
    missing_panels_t1 = []
    for panel in t1_panels:
        panel_markers = set(panel.get("markers", []))
        if panel_markers & set(missing_t1):
            missing_panels_t1.append(panel["panel_id"])

    coverage_pct = round(
        100.0 * (t1_total - len(missing_t1)) / t1_total if t1_total > 0 else 0.0, 1
    )

    return {
        "missing_tier1": missing_t1,
        "missing_tier2": missing_t2,
        "missing_tier3": missing_t3,
        "missing_panels_tier1": missing_panels_t1,
        "coverage_pct": coverage_pct,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Step B: Hallmark-Driven Panel Mapping
# ─────────────────────────────────────────────────────────────────────────────

def map_hallmarks_to_panels(
    active_hallmarks: Dict[str, Any],
    existing_marker_keys: Set[str],
) -> Dict[str, Any]:
    """
    Map active longevity hallmarks to recommended test panels.

    Args:
        active_hallmarks: Dict of {hallmark_name: score_or_dict} from the hallmark scorer.
            A hallmark is "active" if its score is not None and not "insufficient_data".
        existing_marker_keys: Already-collected markers (to avoid re-ordering).

    Returns:
        {
            "active_hallmarks": [...],
            "recommended_panels": [
                {"panel_id": str, "reason": str, "hallmark": str, "tier": str}
            ]
        }
    """
    active = []
    recommended: List[Dict] = []
    seen_panels: Set[str] = set()

    for hallmark, score_data in active_hallmarks.items():
        # Skip if no data
        if score_data is None:
            continue
        if isinstance(score_data, dict) and score_data.get("status") == "insufficient_data":
            continue

        active.append(hallmark)

        # Get panels for this hallmark (tier_2 and tier_3 only — tier_1 is always ordered)
        for tier in ["tier_2", "tier_3"]:
            panel_ids = get_panels_for_hallmark(hallmark, tier)
            for pid in panel_ids:
                if pid in seen_panels:
                    continue
                panel = get_panel(pid)
                if not panel:
                    continue
                # Check if panel markers are already mostly covered
                panel_markers = set(panel.get("markers", []))
                already_have = panel_markers & existing_marker_keys
                coverage = len(already_have) / len(panel_markers) if panel_markers else 0
                if coverage >= 0.8:
                    # Already have 80%+ of this panel's markers — skip
                    continue
                seen_panels.add(pid)
                recommended.append({
                    "panel_id": pid,
                    "display_name": panel.get("display_name", pid),
                    "reason": f"Hallmark '{hallmark}' active — {panel.get('longevity_relevance', '')}",
                    "hallmark": hallmark,
                    "tier": tier,
                    "approximate_cost_usd": panel.get("approximate_cost_usd"),
                    "fasting_required": panel.get("fasting_required", False),
                })

    return {
        "active_hallmarks": active,
        "recommended_panels": recommended,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Step C: Rule-Based Escalation
# ─────────────────────────────────────────────────────────────────────────────

def _evaluate_condition(
    condition: str,
    operator: str,
    threshold: float,
    value: float,
    sex: Optional[str] = None,
    sex_threshold_male: Optional[float] = None,
    sex_threshold_female: Optional[float] = None,
) -> bool:
    """Evaluate a single escalation rule condition."""
    # Use sex-specific threshold if available
    effective_threshold = threshold
    if sex and sex.lower() == "male" and sex_threshold_male is not None:
        effective_threshold = sex_threshold_male
    elif sex and sex.lower() == "female" and sex_threshold_female is not None:
        effective_threshold = sex_threshold_female

    ops = {
        "gt": value > effective_threshold,
        "gte": value >= effective_threshold,
        "lt": value < effective_threshold,
        "lte": value <= effective_threshold,
        "eq": value == effective_threshold,
    }
    return ops.get(operator, False)


def apply_escalation_rules(
    biomarker_values: Dict[str, float],
    existing_marker_keys: Set[str],
    sex: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Apply all escalation rules to the patient's current biomarker values.

    Args:
        biomarker_values: Dict of {marker_key: numeric_value}.
        existing_marker_keys: Already-collected markers.
        sex: Patient sex for sex-specific thresholds.

    Returns:
        {
            "triggered_rules": [
                {
                    "rule_id": str,
                    "trigger_marker": str,
                    "condition": str,
                    "value": float,
                    "severity": str,
                    "recommended_panels": [...],
                    "recommended_markers": [...],
                    "rationale": str,
                    "hallmark": str,
                }
            ],
            "recommended_panels": [...],  # deduplicated
            "recommended_markers": [...],  # deduplicated
        }
    """
    rules = get_escalation_rules()
    triggered = []
    all_panels: Set[str] = set()
    all_markers: Set[str] = set()

    for rule in rules:
        trigger_key = rule.get("trigger_marker")
        if trigger_key not in biomarker_values:
            continue

        value = biomarker_values[trigger_key]
        operator = rule.get("condition_operator", "gt")
        threshold = rule.get("condition_threshold")
        if threshold is None:
            continue

        fired = _evaluate_condition(
            condition=rule.get("condition", ""),
            operator=operator,
            threshold=float(threshold),
            value=value,
            sex=sex,
            sex_threshold_male=rule.get("sex_threshold_male"),
            sex_threshold_female=rule.get("sex_threshold_female"),
        )

        if not fired:
            continue

        # Filter out panels/markers already well-covered
        rec_panels = []
        for pid in rule.get("recommended_panels", []):
            panel = get_panel(pid)
            if not panel:
                continue
            panel_markers = set(panel.get("markers", []))
            already_have = panel_markers & existing_marker_keys
            coverage = len(already_have) / len(panel_markers) if panel_markers else 0
            if coverage < 0.8:
                rec_panels.append(pid)
                all_panels.add(pid)

        rec_markers = [
            mk for mk in rule.get("recommended_markers", [])
            if mk not in existing_marker_keys
        ]
        all_markers.update(rec_markers)

        triggered.append({
            "rule_id": rule.get("rule_id"),
            "trigger_marker": trigger_key,
            "trigger_value": value,
            "trigger_unit": get_marker(trigger_key) and get_marker(trigger_key).get("unit"),
            "condition": rule.get("condition"),
            "severity": rule.get("severity", "moderate"),
            "priority": rule.get("priority", "medium"),
            "recommended_panels": rec_panels,
            "recommended_markers": rec_markers,
            "rationale": rule.get("rationale", ""),
            "hallmark": rule.get("hallmark", ""),
        })

    return {
        "triggered_rules": triggered,
        "recommended_panels": list(all_panels),
        "recommended_markers": list(all_markers),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Full Agent: Combine A + B + C
# ─────────────────────────────────────────────────────────────────────────────

def run_test_ordering_agent(
    patient_id: str,
    existing_panels: List[Dict],  # list of BiomarkerPanel dicts with "values" list
    active_hallmarks: Optional[Dict[str, Any]] = None,
    sex: Optional[str] = None,
    age: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run the full 3-step test ordering agent for a patient.

    Args:
        patient_id: Patient UUID.
        existing_panels: List of panel dicts, each with a "values" list of
            {"marker_key": str, "value": float} dicts.
        active_hallmarks: Output from longevity_hallmark_scorer (optional).
        sex: Patient sex.
        age: Patient age in years.

    Returns:
        Full structured test order recommendation.
    """
    # Build flat dicts of existing data
    existing_marker_keys: Set[str] = set()
    biomarker_values: Dict[str, float] = {}

    for panel in existing_panels:
        for val in panel.get("values", []):
            key = val.get("marker_key")
            value = val.get("value")
            if key:
                existing_marker_keys.add(key)
                if value is not None:
                    biomarker_values[key] = float(value)

    # ── Step A: Gap Detection ─────────────────────────────────────────────────
    gaps = detect_gaps(existing_marker_keys, sex=sex, age=age)

    # ── Step B: Hallmark Mapping ──────────────────────────────────────────────
    hallmark_result = map_hallmarks_to_panels(
        active_hallmarks or {},
        existing_marker_keys,
    )

    # ── Step C: Escalation Rules ──────────────────────────────────────────────
    escalation_result = apply_escalation_rules(
        biomarker_values,
        existing_marker_keys,
        sex=sex,
    )

    # ── Merge & Deduplicate Recommendations ───────────────────────────────────
    all_recommended_panel_ids: Set[str] = set()

    # From gap detection: tier_1 panels with missing markers
    for pid in gaps.get("missing_panels_tier1", []):
        all_recommended_panel_ids.add(pid)

    # From hallmark mapping
    for rec in hallmark_result.get("recommended_panels", []):
        all_recommended_panel_ids.add(rec["panel_id"])

    # From escalation
    for pid in escalation_result.get("recommended_panels", []):
        all_recommended_panel_ids.add(pid)

    # Build full panel details for each recommendation
    recommended_panels_detail = []
    total_cost = 0.0
    all_specimen_types: Set[str] = set()
    fasting_required = False

    for pid in sorted(all_recommended_panel_ids):
        panel = get_panel(pid)
        if not panel:
            continue

        # Determine reason(s)
        reasons = []
        if pid in gaps.get("missing_panels_tier1", []):
            reasons.append("Baseline gap — not yet collected")
        for rec in hallmark_result.get("recommended_panels", []):
            if rec["panel_id"] == pid:
                reasons.append(rec["reason"])
        for rule in escalation_result.get("triggered_rules", []):
            if pid in rule.get("recommended_panels", []):
                reasons.append(
                    f"{rule['trigger_marker']}={rule['trigger_value']} → {rule['rationale'][:80]}"
                )

        cost = panel.get("approximate_cost_usd") or 0
        total_cost += cost
        for spec in panel.get("specimen_types", []):
            all_specimen_types.add(spec)
        if panel.get("fasting_required"):
            fasting_required = True

        # Determine priority
        priority = "routine"
        for rule in escalation_result.get("triggered_rules", []):
            if pid in rule.get("recommended_panels", []):
                if rule.get("severity") == "severe":
                    priority = "urgent"
                    break
                elif rule.get("severity") == "moderate":
                    priority = "high"

        recommended_panels_detail.append({
            "panel_id": pid,
            "display_name": panel.get("display_name", pid),
            "domain": panel.get("domain"),
            "ordering_tier": panel.get("ordering_tier"),
            "markers": panel.get("markers", []),
            "specimen_types": panel.get("specimen_types", []),
            "fasting_required": panel.get("fasting_required", False),
            "turnaround_days": panel.get("turnaround_days"),
            "approximate_cost_usd": cost,
            "quest_panel_code": panel.get("quest_panel_code"),
            "labcorp_panel_code": panel.get("labcorp_panel_code"),
            "priority": priority,
            "reasons": reasons,
        })

    # Sort by priority then tier
    priority_order = {"urgent": 0, "high": 1, "routine": 2}
    tier_order = {"tier_1": 0, "tier_2": 1, "tier_3": 2}
    recommended_panels_detail.sort(
        key=lambda p: (
            priority_order.get(p["priority"], 3),
            tier_order.get(p["ordering_tier"], 3),
        )
    )

    # Evaluate status of existing markers
    marker_statuses = {}
    for key, value in biomarker_values.items():
        marker_statuses[key] = evaluate_marker_status(key, value, sex=sex)

    return {
        "patient_id": patient_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending_clinician_approval",
        "summary": {
            "total_panels_recommended": len(recommended_panels_detail),
            "total_markers_to_collect": sum(
                len(p["markers"]) for p in recommended_panels_detail
            ),
            "total_estimated_cost_usd": round(total_cost, 2),
            "fasting_required": fasting_required,
            "specimen_types_required": sorted(all_specimen_types),
            "tier1_coverage_pct": gaps["coverage_pct"],
            "active_hallmarks": hallmark_result["active_hallmarks"],
            "escalation_rules_triggered": len(escalation_result["triggered_rules"]),
        },
        "ordering_rationale": {
            "gap_detection": {
                "missing_tier1_count": len(gaps["missing_tier1"]),
                "missing_tier2_count": len(gaps["missing_tier2"]),
                "missing_tier3_count": len(gaps["missing_tier3"]),
                "missing_tier1_markers": gaps["missing_tier1"][:20],  # cap for readability
                "missing_panels": gaps["missing_panels_tier1"],
            },
            "hallmark_driven": {
                "active_hallmarks": hallmark_result["active_hallmarks"],
                "panels_from_hallmarks": [
                    r["panel_id"] for r in hallmark_result["recommended_panels"]
                ],
            },
            "escalation": {
                "triggered_rules": escalation_result["triggered_rules"],
                "panels_from_escalation": escalation_result["recommended_panels"],
            },
        },
        "recommended_panels": recommended_panels_detail,
        "requisition": {
            "panels": [
                {
                    "panel_id": p["panel_id"],
                    "display_name": p["display_name"],
                    "quest_code": p.get("quest_panel_code"),
                    "labcorp_code": p.get("labcorp_panel_code"),
                    "fasting_required": p["fasting_required"],
                    "specimen_types": p["specimen_types"],
                }
                for p in recommended_panels_detail
            ],
            "total_panels": len(recommended_panels_detail),
            "total_estimated_cost_usd": round(total_cost, 2),
            "fasting_required": fasting_required,
            "specimen_requirements": sorted(all_specimen_types),
        },
        "existing_marker_statuses": marker_statuses,
    }
