"""
Level 0 Longevity Hallmark Assessment — curated JSON only (no external APIs).
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_SHIPPABLE = frozenset(
    {
        "genomic_instability",
        "epigenetic_alterations",
        "nutrient_sensing",
        "mitochondrial_dysfunction",
        "cellular_senescence",
        "altered_intercellular_communication",
    }
)

# Biomarkers whose thresholds are qualitative notes only — skip numeric scoring.
_NOTE_ONLY_BIOMARKERS = frozenset(
    {
        "leukocyte_telomere_length",
        "dnam_epigenetic_age",
        "dhea_s",
        "free_testosterone",
    }
)

# Curated interaction flags (JSON interactions are generic; L0 adds high-yield pairs).
_COMPOUND_MED_SAFETY_FLAGS: Dict[str, List[Dict[str, str]]] = {
    "berberine": [
        {
            "if_med_substring": "metformin",
            "code": "ADDITIVE_HYPOGLYCEMIA",
            "message": "Additive hypoglycemia risk with concurrent glucose-lowering agents (e.g., metformin); monitor glucose with clinician.",
        },
        {
            "if_med_substring": "warfarin",
            "code": "ANTICOAGULANT_CYP_INTERACTION",
            "message": "Berberine may affect CYP enzymes; use extra caution with warfarin and other anticoagulants — bleeding/monitoring risk; coordinate with clinician.",
        },
        {
            "if_med_substring": "coumadin",
            "code": "ANTICOAGULANT_CYP_INTERACTION",
            "message": "Berberine may affect CYP enzymes; use extra caution with vitamin K antagonists — bleeding/monitoring risk; coordinate with clinician.",
        },
    ],
    "rapamycin": [
        {
            "if_med_substring": "tacrolimus",
            "code": "IMMUNOSUPPRESSANT_CYP3A4_HIGH",
            "message": "HIGH: mTOR/CNI stacking risk — tacrolimus + sirolimus/everolimus-class agents share CYP3A4 metabolism and immunosuppression; levels/toxicity can shift; transplant-team oversight only.",
        },
        {
            "if_med_substring": "cyclosporine",
            "code": "IMMUNOSUPPRESSANT_CYP3A4_HIGH",
            "message": "HIGH: Combined immunosuppression + CYP3A4 interaction risk with calcineurin inhibitors; requires specialist coordination.",
        },
        {
            "if_med_substring": "sirolimus",
            "code": "IMMUNOSUPPRESSANT_DUPLICATION",
            "message": "HIGH: Duplicate mTOR pathway exposure; prescription overlap — clinician review mandatory.",
        },
    ],
}

# Med token -> phrases that may appear in curated interaction strings (text mentions class, not brand).
_MED_TRIGGER_PHRASES: Dict[str, Tuple[str, ...]] = {
    "warfarin": (
        "warfarin",
        "coumadin",
        "jantoven",
        "anticoagulant",
        "blood thinner",
        "vitamin k antagonist",
        "vk antagonist",
    ),
    "coumadin": ("warfarin", "coumadin", "jantoven", "anticoagulant", "blood thinner"),
    "jantoven": ("warfarin", "coumadin", "jantoven", "anticoagulant", "blood thinner"),
}

# If interaction text warns about CYP450, these concomitant meds are high-signal to surface the line.
_CYP_ALERT_MEDS = frozenset(
    {
        "warfarin",
        "coumadin",
        "jantoven",
        "digoxin",
        "tacrolimus",
        "cyclosporine",
        "sirolimus",
        "everolimus",
    }
)


def _med_matches_interaction_text(text_l: str, med_l: str) -> bool:
    """True if patient med should surface this interaction line (substring + class + CYP bridge)."""
    ml = (med_l or "").strip().lower()
    if not ml:
        return False
    if ml in text_l:
        return True
    phrases = _MED_TRIGGER_PHRASES.get(ml)
    if phrases and any(p in text_l for p in phrases):
        return True
    if "cyp" in text_l and ml in _CYP_ALERT_MEDS:
        return True
    return False


def _resources_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "resources" / "longevity"


def _normalize_biomarker_key(key: str) -> str:
    k = (key or "").strip()
    if not k:
        return ""
    kl = k.lower().replace("-", "_")
    aliases = {
        "hscrp": "hscrp",
        "hs_crp": "hscrp",
        "crp": "hscrp",
        "vitamin_d_25oh": "25oh_vitamin_d",
        "vitamin_d": "25oh_vitamin_d",
        "25_oh_vitamin_d": "25oh_vitamin_d",
        "25ohvitamind": "25oh_vitamin_d",
        "il_6": "il6",
        "tnfalpha": "tnf_alpha",
        "tnf_a": "tnf_alpha",
        "lpa": "lp_a",
        "lp_a": "lp_a",
        "homa": "homa_ir",
        "hba1c_percent": "hba1c",
        "hba1c_pct": "hba1c",
    }
    return aliases.get(kl, kl)


@dataclass
class HallmarkScore:
    vulnerability: Optional[float]
    tier: Optional[str]
    biomarkers_used: List[str] = field(default_factory=list)
    biomarkers_missing: List[str] = field(default_factory=list)
    detail: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        if self.vulnerability is None:
            return None
        return {
            "vulnerability": round(self.vulnerability, 4),
            "tier": self.tier,
            "biomarkers_used": self.biomarkers_used,
            "biomarkers_missing": self.biomarkers_missing,
            "detail": self.detail,
        }


@dataclass
class CompoundRecommendation:
    compound: str
    display_name: str
    overall_relevance: float
    hallmark_matches: List[Dict[str, Any]]
    dose: Dict[str, Any]
    interactions: List[str]
    safety_flags: List[Dict[str, str]]
    multi_hallmark_convergence: bool = False
    relevance_cap_note: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "compound": self.compound,
            "display_name": self.display_name,
            "overall_relevance": round(self.overall_relevance, 4),
            "hallmark_matches": self.hallmark_matches,
            "dose": self.dose,
            "interactions": self.interactions,
            "safety_flags": self.safety_flags,
        }
        if self.multi_hallmark_convergence:
            out["multi_hallmark_convergence"] = True
        if self.relevance_cap_note:
            out["note"] = self.relevance_cap_note
        return out


class LongevityHallmarkScorer:
    def __init__(self) -> None:
        base = _resources_dir()
        self._biomarker_data = self._load_and_validate(base / "biomarker_hallmark_map.json")
        self._compound_data = self._load_and_validate(base / "longevity_compound_hallmark_map.json")
        self._biomarkers_by_id: Dict[str, Dict[str, Any]] = {}
        for b in self._biomarker_data.get("biomarkers", []):
            bid = b.get("biomarker_id")
            if not bid:
                raise ValueError("biomarker entry missing biomarker_id")
            self._biomarkers_by_id[bid] = b
        self._compounds_by_id: Dict[str, Dict[str, Any]] = {}
        for c in self._compound_data.get("compounds", []):
            cid = c.get("compound_id")
            if not cid:
                raise ValueError("compound entry missing compound_id")
            self._compounds_by_id[cid] = c
        self._log_excluded_scoring_links()

    def _load_and_validate(self, path: Path) -> dict:
        if not path.is_file():
            raise FileNotFoundError(f"Longevity resource missing: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError(f"Invalid root object in {path}")
        if "biomarkers" in data:
            if not isinstance(data["biomarkers"], list):
                raise ValueError("biomarker_hallmark_map: biomarkers must be a list")
            for i, b in enumerate(data["biomarkers"]):
                if not isinstance(b, dict) or not b.get("biomarker_id"):
                    raise ValueError(f"biomarkers[{i}] invalid")
        if "compounds" in data:
            if not isinstance(data["compounds"], list):
                raise ValueError("compound map: compounds must be a list")
            for i, c in enumerate(data["compounds"]):
                if not isinstance(c, dict) or not c.get("compound_id"):
                    raise ValueError(f"compounds[{i}] invalid")
        return data

    def _log_excluded_scoring_links(self) -> None:
        for c in self._compound_data.get("compounds", []):
            cid = c.get("compound_id", "")
            for link in c.get("hallmark_links") or []:
                if not link.get("include_in_scoring", True):
                    logger.info(
                        "Longevity compound %s: hallmark link %s excluded from scoring (include_in_scoring=false)",
                        cid,
                        link.get("hallmark"),
                    )

    def _parse_resolved_biomarkers(self, biomarkers: Dict[str, Any]) -> Dict[str, float]:
        """Flatten patient biomarkers to canonical id -> numeric value."""
        out: Dict[str, float] = {}
        if not biomarkers:
            return out
        for raw_k, raw_v in biomarkers.items():
            if raw_k in ("cystatin_c", "egfr"):
                continue
            nk = _normalize_biomarker_key(str(raw_k))
            if not nk:
                continue
            if nk == "cystatin_c_egfr" and isinstance(raw_v, dict):
                cc = raw_v.get("cystatin_c")
                eg = raw_v.get("egfr")
                if cc is not None and eg is not None:
                    out["cystatin_c_egfr"] = float(cc)
                    out["_egfr_for_cystatin"] = float(eg)
                continue
            try:
                out[nk] = float(raw_v)
            except (TypeError, ValueError):
                continue
        cc = biomarkers.get("cystatin_c")
        eg = biomarkers.get("egfr")
        if cc is not None and eg is not None:
            try:
                out["cystatin_c_egfr"] = float(cc)
                out["_egfr_for_cystatin"] = float(eg)
            except (TypeError, ValueError):
                pass
        return out

    def _tier_from_vulnerability(self, v: float) -> str:
        if v > 0.66:
            return "HIGH_RISK"
        if v > 0.33:
            return "MODERATE"
        return "OPTIMAL"

    def _score_numeric_biomarker(self, bdef: Dict[str, Any], value: float) -> Optional[Tuple[float, str]]:
        bid = bdef["biomarker_id"]
        if bid in _NOTE_ONLY_BIOMARKERS:
            return None
        direction = bdef.get("direction") or ""
        th = bdef.get("thresholds") or {}

        if direction == "HIGH_IS_VULNERABLE":
            o, m, h = th.get("optimal") or {}, th.get("moderate") or {}, th.get("high_risk") or {}
            mx = o.get("max")
            mn_m, mx_m = m.get("min"), m.get("max")
            mn_h = h.get("min")
            if mx is not None and value <= mx:
                return 0.0, "OPTIMAL"
            if mn_m is not None and mx_m is not None and mn_m <= value <= mx_m:
                return 0.5, "MODERATE"
            if mn_h is not None and value >= mn_h:
                return 1.0, "HIGH_RISK"
            if mx is not None and value > mx:
                return 0.5, "MODERATE"
            return 0.5, "MODERATE"

        if direction == "LOW_IS_VULNERABLE":
            o, m, h = th.get("optimal") or {}, th.get("moderate") or {}, th.get("high_risk") or {}
            o_min, o_max = o.get("min"), o.get("max")
            m_min, m_max = m.get("min"), m.get("max")
            h_max = h.get("max")
            if o_min is not None and o_max is not None and o_min <= value <= o_max:
                return 0.0, "OPTIMAL"
            if m_min is not None and m_max is not None and m_min <= value < m_max:
                return 0.5, "MODERATE"
            if h_max is not None and value < h_max:
                return 1.0, "HIGH_RISK"
            if o_max is not None and value > o_max:
                return 0.0, "OPTIMAL"
            return 0.5, "MODERATE"

        if direction == "U_SHAPED_EXTREMES_VULNERABLE":
            opt = th.get("optimal") or {}
            ml = th.get("moderate_low") or {}
            mh = th.get("moderate_high") or {}
            hr = th.get("high_risk") or {}
            lo_max = hr.get("low_band_max")
            hi_min = hr.get("high_band_min")
            n_min, n_max = opt.get("min"), opt.get("max")
            if n_min is not None and n_max is not None and n_min <= value <= n_max:
                return 0.0, "OPTIMAL"
            if lo_max is not None and value <= lo_max:
                return 1.0, "HIGH_RISK"
            if hi_min is not None and value >= hi_min:
                return 1.0, "HIGH_RISK"
            ml_min, ml_max = ml.get("min"), ml.get("max")
            mh_min, mh_max = mh.get("min"), mh.get("max")
            if ml_min is not None and ml_max is not None and ml_min <= value < ml_max:
                return 0.5, "MODERATE"
            if mh_min is not None and mh_max is not None and mh_min < value < mh_max:
                return 0.5, "MODERATE"
            return 0.5, "MODERATE"

        if direction == "HIGH_CYSTATIN_LOW_EGFR_IS_VULNERABLE":
            # Caller passes value=cystatin_c and egfr sidecar
            return None

        return None

    def _score_cystatin_egfr(self, cystatin_c: float, egfr: float) -> Tuple[float, str]:
        if cystatin_c <= 0.8 and egfr >= 90:
            return 0.0, "OPTIMAL"
        if cystatin_c >= 1.0 or egfr <= 60:
            return 1.0, "HIGH_RISK"
        return 0.5, "MODERATE"

    def _biomarker_ids_for_hallmark(self, hallmark: str) -> List[str]:
        found: List[str] = []
        for bid, bdef in self._biomarkers_by_id.items():
            for assoc in bdef.get("hallmark_associations") or []:
                if assoc.get("hallmark") == hallmark:
                    found.append(bid)
                    break
        return sorted(set(found))

    def score_hallmark_vulnerabilities(self, biomarkers: Dict[str, Any]) -> Dict[str, Optional[Dict[str, Any]]]:
        resolved = self._parse_resolved_biomarkers(biomarkers)
        egfr_side = resolved.pop("_egfr_for_cystatin", None)

        result: Dict[str, Optional[Dict[str, Any]]] = {}

        for hallmark in sorted(_SHIPPABLE):
            mapped = self._biomarker_ids_for_hallmark(hallmark)
            scores: List[float] = []
            used: List[str] = []
            detail: Dict[str, Any] = {}
            missing = [
                bid
                for bid in mapped
                if bid not in resolved and not (bid == "cystatin_c_egfr" and "cystatin_c_egfr" in resolved)
            ]

            for bid in mapped:
                if bid == "cystatin_c_egfr":
                    cc = resolved.get("cystatin_c_egfr")
                    eg = egfr_side
                    if cc is None or eg is None:
                        continue
                    sc, tier = self._score_cystatin_egfr(cc, eg)
                    scores.append(sc)
                    used.append(bid)
                    detail[bid] = {
                        "cystatin_c": cc,
                        "egfr": eg,
                        "tier": tier,
                        "score": sc,
                    }
                    continue

                if bid not in resolved:
                    continue
                val = resolved[bid]
                bdef = self._biomarkers_by_id[bid]
                if bdef.get("direction") == "HIGH_CYSTATIN_LOW_EGFR_IS_VULNERABLE":
                    continue
                parsed = self._score_numeric_biomarker(bdef, val)
                if parsed is None:
                    continue
                sc, tier = parsed
                scores.append(sc)
                used.append(bid)
                detail[bid] = {"value": val, "tier": tier, "score": sc}

            if not scores:
                hs = HallmarkScore(None, None, used, [m for m in missing if m not in used], detail)
                result[hallmark] = hs.as_dict()
                continue

            vuln = sum(scores) / len(scores)
            tier = self._tier_from_vulnerability(vuln)
            still_missing = [x for x in mapped if x not in used]
            hs = HallmarkScore(vuln, tier, used, still_missing, detail)
            result[hallmark] = hs.as_dict()

        return result

    def _verified_pmids(self, link: Dict[str, Any]) -> List[str]:
        pmids = link.get("pmids") or []
        verified = link.get("pmid_verified") or []
        out: List[str] = []
        for i, p in enumerate(pmids):
            ok = verified[i] if i < len(verified) else False
            if ok:
                out.append(str(p))
        return out

    def _link_is_scorable(self, link: Dict[str, Any]) -> bool:
        if not link.get("include_in_scoring", True):
            return False
        pmids = link.get("pmids") or []
        verified = link.get("pmid_verified") or []
        return any(i < len(verified) and verified[i] for i in range(len(pmids)))

    def _filter_interactions_for_meds(
        self,
        compound: Dict[str, Any],
        medications: List[str],
        *,
        compound_id: str = "",
    ) -> List[str]:
        texts = compound.get("interactions") or []
        if not medications:
            # No concomitant meds → do not surface drug-interaction lines (avoids false positives).
            return []
        meds_l = [m.lower().strip() for m in medications if m and str(m).strip()]
        if compound_id == "berberine":
            logger.info(
                "longevity_compound_interactions: compound_id=%s patient_medications=%s raw_interactions=%s",
                compound_id,
                medications,
                list(texts),
            )
        hits: List[str] = []
        for t in texts:
            tl = t.lower()
            matched: List[str] = []
            for m in meds_l:
                if _med_matches_interaction_text(tl, m):
                    matched.append(m)
            if matched:
                hits.append(t)
            if compound_id == "berberine":
                logger.info(
                    "longevity_compound_interactions: line=%r matched_meds=%s",
                    t,
                    matched,
                )
        if compound_id == "berberine":
            logger.info(
                "longevity_compound_interactions: compound_id=%s filtered_interactions=%s",
                compound_id,
                hits,
            )
        return hits

    def _curated_safety_flags(self, compound_id: str, medications: List[str]) -> List[Dict[str, str]]:
        flags: List[Dict[str, str]] = []
        meds_l = [m.lower() for m in medications if m]
        for rule in _COMPOUND_MED_SAFETY_FLAGS.get(compound_id, []):
            sub = (rule.get("if_med_substring") or "").lower()
            if sub and any(sub in m for m in meds_l):
                flags.append(
                    {
                        "code": rule.get("code", "CAUTION"),
                        "message": rule.get("message", ""),
                    }
                )
        return flags

    def score_compounds_for_hallmarks(
        self,
        vulnerable_hallmarks: Dict[str, Optional[Dict[str, Any]]],
        compound_queries: List[str],
        patient_medications: Optional[List[str]] = None,
    ) -> List[CompoundRecommendation]:
        patient_medications = patient_medications or []
        vuln_map: Dict[str, float] = {}
        vuln_meta: Dict[str, Dict[str, Any]] = {}
        for h, payload in vulnerable_hallmarks.items():
            if payload and payload.get("vulnerability") is not None:
                vuln_map[h] = float(payload["vulnerability"])
                vuln_meta[h] = {
                    "calibration_label": payload.get("calibration_label"),
                    "scoring_source": payload.get("scoring_source"),
                    "driven_biomarkers": list(payload.get("driven_biomarkers") or []),
                    "tier": payload.get("tier"),
                }

        recs: List[CompoundRecommendation] = []
        for q in compound_queries or []:
            qn = (q or "").strip().lower().replace(" ", "_")
            if not qn:
                continue
            c = self._compounds_by_id.get(qn)
            if not c:
                recs.append(
                    CompoundRecommendation(
                        compound=qn,
                        display_name=qn,
                        overall_relevance=0.0,
                        hallmark_matches=[],
                        dose={},
                        interactions=[],
                        safety_flags=[
                            {
                                "code": "UNKNOWN_COMPOUND",
                                "message": "Not in longevity_compound_hallmark_map.json",
                            }
                        ],
                    )
                )
                continue

            if str(c.get("status") or "").upper() == "HARMFUL_IN_CONTEXT":
                harm = c.get("harm_evidence") or {}
                finding = str(harm.get("finding") or "HARMFUL in listed context")
                trials = str(harm.get("trials") or "")
                ctx = str(harm.get("context") or "")
                msg = f"{finding}"
                if ctx:
                    msg = f"{ctx}: {msg}"
                if trials:
                    msg = f"{msg} — {trials}"
                recs.append(
                    CompoundRecommendation(
                        compound=qn,
                        display_name=str(c.get("display_name") or qn),
                        overall_relevance=0.0,
                        hallmark_matches=[],
                        dose=c.get("dose") or {},
                        interactions=list(c.get("interactions") or []),
                        safety_flags=[
                            {
                                "code": "ATBC_CARET_BLOCK",
                                "message": msg,
                            }
                        ],
                    )
                )
                continue

            matches: List[Dict[str, Any]] = []
            relevances: List[float] = []
            for link in c.get("hallmark_links") or []:
                if not self._link_is_scorable(link):
                    continue
                hm = link.get("hallmark")
                if hm not in _SHIPPABLE:
                    continue
                pv = vuln_map.get(hm)
                if pv is None:
                    continue
                w = float(link.get("weight", 0))
                rel = w * pv
                relevances.append(rel)
                pmids_out = self._verified_pmids(link)
                meta = vuln_meta.get(hm) or {}
                row: Dict[str, Any] = {
                    "hallmark": hm,
                    "compound_weight": w,
                    "patient_vulnerability": round(pv, 4),
                    "relevance": round(rel, 4),
                    "mechanism": link.get("mechanism", ""),
                    "evidence_strength": link.get("evidence_strength", ""),
                    "human_evidence": bool(link.get("human_evidence")),
                    "pmids": pmids_out,
                }
                if meta.get("calibration_label"):
                    row["calibration_label"] = meta["calibration_label"]
                if meta.get("scoring_source"):
                    row["scoring_source"] = meta["scoring_source"]
                if meta.get("driven_biomarkers"):
                    row["driven_biomarkers"] = meta["driven_biomarkers"]
                if meta.get("tier"):
                    row["vulnerability_tier"] = meta["tier"]
                src = meta.get("scoring_source")
                if src == "phenoage":
                    row["scoring_basis"] = "phenoage_mortality_calibrated"
                elif src == "supplementary":
                    row["scoring_basis"] = "supplementary_threshold_only"
                matches.append(row)

            raw_overall = sum(relevances) / len(relevances) if relevances else 0.0
            convergence = False
            cap_note: Optional[str] = None
            overall = raw_overall
            if raw_overall > 1.0:
                overall = min(raw_overall, 1.0)
                convergence = True
                cap_note = "Score exceeds 1.0 due to multiple hallmark signals"
            dose = c.get("dose") or {}
            inter = self._filter_interactions_for_meds(c, patient_medications, compound_id=qn)
            flags = self._curated_safety_flags(qn, patient_medications)

            recs.append(
                CompoundRecommendation(
                    compound=qn,
                    display_name=c.get("display_name") or qn,
                    overall_relevance=overall,
                    hallmark_matches=matches,
                    dose=dose,
                    interactions=inter,
                    safety_flags=flags,
                    multi_hallmark_convergence=convergence,
                    relevance_cap_note=cap_note,
                )
            )

        recs.sort(key=lambda r: r.overall_relevance, reverse=True)
        return recs


_scorer_singleton: Optional[LongevityHallmarkScorer] = None


def get_longevity_hallmark_scorer() -> LongevityHallmarkScorer:
    global _scorer_singleton
    if _scorer_singleton is None:
        _scorer_singleton = LongevityHallmarkScorer()
    return _scorer_singleton

