"""
Lab PDF parser — extracts biomarker values from Quest Diagnostics, LabCorp,
and generic lab report PDFs.

Strategy:
1. Extract all text from PDF using pdfplumber
2. Run regex patterns against each line to find marker name + value + unit + ref range
3. Map extracted names to canonical keys used by the longevity assessment engine
4. Return structured list of PanelValueInput-compatible dicts
"""
from __future__ import annotations

import io
import re
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# Canonical key mapping — maps common lab report names → our internal keys
# ─────────────────────────────────────────────────────────────────────────────

MARKER_ALIASES: dict[str, str] = {
    # Albumin
    "albumin": "albumin",
    "albumin, serum": "albumin",
    "alb": "albumin",
    # Creatinine
    "creatinine": "creatinine",
    "creatinine, serum": "creatinine",
    "creat": "creatinine",
    # Glucose
    "glucose": "glucose",
    "glucose, serum": "glucose",
    "fasting glucose": "glucose",
    "blood glucose": "glucose",
    # ALP
    "alkaline phosphatase": "alkaline_phosphatase",
    "alk phos": "alkaline_phosphatase",
    "alp": "alkaline_phosphatase",
    "alkaline phosphatase, s": "alkaline_phosphatase",
    # WBC
    "wbc": "wbc",
    "white blood cell count": "wbc",
    "white blood cells": "wbc",
    "leukocytes": "wbc",
    # Lymphocytes
    "lymphocytes": "lymphocyte_percent",
    "lymphocyte %": "lymphocyte_percent",
    "lymphs %": "lymphocyte_percent",
    "lymphocyte percent": "lymphocyte_percent",
    "lymphs": "lymphocyte_percent",
    # MCV
    "mcv": "mcv",
    "mean corpuscular volume": "mcv",
    # RDW
    "rdw": "rdw",
    "rdw-cv": "rdw",
    "red cell distribution width": "rdw",
    # CRP / hsCRP
    "crp": "crp",
    "c-reactive protein": "crp",
    "hs-crp": "crp",
    "hscrp": "crp",
    "high sensitivity crp": "crp",
    "c reactive protein, cardiac": "crp",
    "c-reactive protein, cardiac": "crp",
    # Lipids
    "ldl": "ldl",
    "ldl cholesterol": "ldl",
    "ldl-c": "ldl",
    "low density lipoprotein": "ldl",
    "hdl": "hdl",
    "hdl cholesterol": "hdl",
    "hdl-c": "hdl",
    "high density lipoprotein": "hdl",
    "triglycerides": "triglycerides",
    "trig": "triglycerides",
    "total cholesterol": "total_cholesterol",
    "cholesterol, total": "total_cholesterol",
    # HbA1c
    "hba1c": "hba1c",
    "hemoglobin a1c": "hba1c",
    "glycated hemoglobin": "hba1c",
    "a1c": "hba1c",
    # Testosterone
    "testosterone": "testosterone",
    "testosterone, total": "testosterone",
    "testosterone, serum": "testosterone",
    # TSH
    "tsh": "tsh",
    "thyroid stimulating hormone": "tsh",
    "thyrotropin": "tsh",
    # Ferritin
    "ferritin": "ferritin",
    "ferritin, serum": "ferritin",
    # Vitamin D
    "vitamin d": "vitamin_d",
    "25-oh vitamin d": "vitamin_d",
    "25-hydroxyvitamin d": "vitamin_d",
    "vitamin d, 25-hydroxy": "vitamin_d",
    "25(oh)d": "vitamin_d",
    # Homocysteine
    "homocysteine": "homocysteine",
    "homocyst(e)ine": "homocysteine",
    # Insulin
    "insulin": "insulin",
    "insulin, fasting": "insulin",
    # BUN
    "bun": "bun",
    "blood urea nitrogen": "bun",
    "urea nitrogen": "bun",
    # AST / ALT
    "ast": "ast",
    "aspartate aminotransferase": "ast",
    "sgot": "ast",
    "alt": "alt",
    "alanine aminotransferase": "alt",
    "sgpt": "alt",
    # Hemoglobin
    "hemoglobin": "hemoglobin",
    "hgb": "hemoglobin",
    "hb": "hemoglobin",
    # Hematocrit
    "hematocrit": "hematocrit",
    "hct": "hematocrit",
    # Platelets
    "platelets": "platelets",
    "platelet count": "platelets",
    "plt": "platelets",
    # Sodium / Potassium / CO2
    "sodium": "sodium",
    "potassium": "potassium",
    "co2": "co2",
    "carbon dioxide": "co2",
    "bicarbonate": "co2",
    # eGFR
    "egfr": "egfr",
    "estimated gfr": "egfr",
    "gfr": "egfr",
    # IGF-1
    "igf-1": "igf1",
    "igf1": "igf1",
    "insulin-like growth factor 1": "igf1",
    # DHEA-S
    "dhea-s": "dhea_s",
    "dhea sulfate": "dhea_s",
    "dehydroepiandrosterone sulfate": "dhea_s",
}

# ─────────────────────────────────────────────────────────────────────────────
# Reference ranges (optimal, not just lab normal) for common markers
# ─────────────────────────────────────────────────────────────────────────────

OPTIMAL_RANGES: dict[str, tuple[float | None, float | None]] = {
    "albumin": (4.0, 5.0),
    "creatinine": (0.6, 1.1),
    "glucose": (70, 90),
    "alkaline_phosphatase": (30, 70),
    "wbc": (4.0, 7.0),
    "lymphocyte_percent": (25, 40),
    "mcv": (82, 92),
    "rdw": (11.5, 13.0),
    "crp": (0.0, 0.5),
    "ldl": (None, 100),
    "hdl": (60, None),
    "triglycerides": (None, 100),
    "total_cholesterol": (None, 200),
    "hba1c": (4.5, 5.4),
    "testosterone": (500, 900),  # male reference
    "tsh": (1.0, 2.5),
    "ferritin": (50, 150),
    "vitamin_d": (50, 80),
    "homocysteine": (None, 9),
    "egfr": (90, None),
}

# ─────────────────────────────────────────────────────────────────────────────
# Regex patterns for value extraction
# ─────────────────────────────────────────────────────────────────────────────

# Matches: "Albumin   4.2   g/dL   3.5-5.0"
# or:      "Glucose   95   mg/dL   70-99   Normal"
VALUE_PATTERN = re.compile(
    r"(?P<value>[\d]+\.?[\d]*)\s*"
    r"(?P<unit>[a-zA-Z/%]+(?:/[a-zA-Z]+)?)?\s*"
    r"(?:(?P<ref_low>[\d]+\.?[\d]*)\s*[-–]\s*(?P<ref_high>[\d]+\.?[\d]*))?"
    r"\s*(?P<flag>[HhLl]{1,2})?"
)

# Detect flag markers
FLAG_PATTERN = re.compile(r"\b(H{1,2}|L{1,2}|HIGH|LOW|CRITICAL|PANIC)\b", re.IGNORECASE)


def _normalize_name(raw: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    s = raw.lower().strip()
    s = re.sub(r"[,*#@]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def _extract_flag(line: str) -> str | None:
    m = FLAG_PATTERN.search(line)
    if not m:
        return None
    f = m.group(1).upper()
    if f in ("HIGH", "CRITICAL", "PANIC"):
        return "H"
    if f == "LOW":
        return "L"
    return f


def _parse_line(line: str) -> dict | None:
    """
    Try to extract a biomarker reading from a single text line.
    Returns dict with keys: marker_key, marker_display, value, unit, ref_low, ref_high, flag
    or None if no match.
    """
    # Split on 2+ spaces or tab to separate name from values
    parts = re.split(r"\s{2,}|\t", line.strip())
    if len(parts) < 2:
        return None

    name_raw = parts[0].strip()
    rest = " ".join(parts[1:])

    # Normalize name and look up canonical key
    name_norm = _normalize_name(name_raw)
    canonical = MARKER_ALIASES.get(name_norm)
    if not canonical:
        # Try partial match — check if any alias is contained in the normalized name
        for alias, key in MARKER_ALIASES.items():
            if alias in name_norm or name_norm in alias:
                canonical = key
                break
    if not canonical:
        return None

    # Extract numeric value
    m = re.search(r"([\d]+\.?[\d]*)", rest)
    if not m:
        return None
    try:
        value = float(m.group(1))
    except ValueError:
        return None

    # Extract unit
    unit_m = re.search(r"[\d\.]+\s*([a-zA-Z/%]+(?:/[a-zA-Z]+)?)", rest)
    unit = unit_m.group(1) if unit_m else None

    # Extract reference range
    ref_m = re.search(r"([\d]+\.?[\d]*)\s*[-–]\s*([\d]+\.?[\d]*)", rest)
    ref_low = float(ref_m.group(1)) if ref_m else None
    ref_high = float(ref_m.group(2)) if ref_m else None

    # Use optimal ranges as fallback
    if ref_low is None and ref_high is None and canonical in OPTIMAL_RANGES:
        ref_low, ref_high = OPTIMAL_RANGES[canonical]

    # Flag
    flag = _extract_flag(rest) or _extract_flag(line)

    return {
        "marker_key": canonical,
        "marker_display": name_raw,
        "value": value,
        "unit": unit,
        "ref_low": ref_low,
        "ref_high": ref_high,
        "flag": flag,
    }


def parse_lab_pdf(pdf_bytes: bytes) -> dict[str, Any]:
    """
    Parse a lab report PDF and return extracted biomarkers.

    Returns:
        {
            "markers": [{"marker_key": ..., "value": ..., ...}],
            "lab_name": str | None,
            "raw_text_preview": str,
            "parse_confidence": float,  # 0-1
        }
    """
    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError("pdfplumber not installed. Run: pip install pdfplumber")

    markers: dict[str, dict] = {}  # deduplicate by canonical key
    all_text_lines: list[str] = []
    lab_name: str | None = None

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines = text.split("\n")
            all_text_lines.extend(lines)

            # Detect lab name from first page header
            if lab_name is None and lines:
                header = " ".join(lines[:5]).lower()
                if "quest" in header:
                    lab_name = "Quest Diagnostics"
                elif "labcorp" in header or "laboratory corporation" in header:
                    lab_name = "LabCorp"
                elif "mayo" in header:
                    lab_name = "Mayo Clinic Laboratories"
                elif "sonora" in header:
                    lab_name = "Sonora Quest"

            for line in lines:
                result = _parse_line(line)
                if result:
                    key = result["marker_key"]
                    # Keep first occurrence (usually most recent in Quest/LabCorp format)
                    if key not in markers:
                        markers[key] = result

    marker_list = list(markers.values())
    raw_preview = "\n".join(all_text_lines[:50])

    # Confidence: ratio of PhenoAge-critical markers found
    phenoage_keys = {"albumin", "creatinine", "glucose", "alkaline_phosphatase",
                     "wbc", "lymphocyte_percent", "mcv", "rdw", "crp"}
    found_phenoage = phenoage_keys & set(markers.keys())
    confidence = len(found_phenoage) / len(phenoage_keys)

    return {
        "markers": marker_list,
        "lab_name": lab_name,
        "raw_text_preview": raw_preview,
        "parse_confidence": round(confidence, 2),
        "phenoage_markers_found": sorted(found_phenoage),
        "total_markers_found": len(marker_list),
    }
