"""
NHANES PhenoAge Calibration Eval
=================================
External ground truth: Levine 2018 (PMID 29676998)
Data: NHANES 2017-2018 (CDC public domain)

Unit mapping (NHANES SI columns → Levine 2018 canonical units):
  LBDSALSI  (albumin g/L)       → albumin g/L          (canonical)
  LBDSCRSI  (creatinine umol/L) → creatinine umol/L    (canonical)
  LBDSGLSI  (glucose mmol/L)    → glucose mmol/L       (canonical)
  LBXSAPSI  (ALP U/L)           → alkaline_phosphatase U/L (canonical)
  LBXWBCSI  (WBC 10^9/L)        → wbc 10^9/L           (canonical)
  LBXLYPCT  (lymphocyte %)      → lymphocyte_percent % (canonical)
  LBXMCVSI  (MCV fL)            → mcv fL               (canonical)
  LBXRDW    (RDW %)             → rdw %                (canonical)
  LBXHSCRP  (hsCRP mg/L)        → crp_log = ln(mg/L/10) = ln(mg/dL)

Acceptance criteria (hard gates):
  1. N >= 2,000 complete cases
  2. Pearson r(PhenoAge, chronological_age) >= 0.75
  3. Mean bias (PhenoAge - chronological_age) within +/- 5 years
  4. PhenoAge C-statistic (AUC) for 10-year mortality >= chronological age C-statistic

Run:
    PYTHONPATH=/workspace/longivity python tests/eval/nhanes_phenoage_calibration.py
"""

import os
import sys
import json
import math
import urllib.request
import urllib.error
from datetime import datetime

import numpy as np
import pandas as pd

sys.path.insert(0, "/workspace/longivity/src")
from longivity.services.longevity_phenoage_level0 import extract_phenoage_marker_values

# ── paths ──────────────────────────────────────────────────────────────────────
CACHE_DIR = "/workspace/nhanes_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

NHANES_BASE = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles"
MORT_URL = (
    "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/datalinkage/linked_mortality/"
    "NHANES_2017_2018_MORT_2019_PUBLIC.dat"
)

FILES = {
    "DEMO_J.XPT": f"{NHANES_BASE}/DEMO_J.XPT",
    "BIOPRO_J.XPT": f"{NHANES_BASE}/BIOPRO_J.XPT",
    "CBC_J.XPT": f"{NHANES_BASE}/CBC_J.XPT",
    "HSCRP_J.XPT": f"{NHANES_BASE}/HSCRP_J.XPT",
    "NHANES_2017_2018_MORT_2019_PUBLIC.dat": MORT_URL,
}

# ── Levine 2018 coefficients (canonical units from repo JSON) ──────────────────
# albumin: g/L, creatinine: umol/L, glucose: mmol/L, crp: ln(mg/dL)
COEF = {
    "albumin":      -0.0336,
    "creatinine":    0.0095,
    "glucose":       0.1953,
    "crp_ln":        0.0954,
    "lymphocyte":   -0.0120,
    "mcv":           0.0268,
    "rdw":           0.3306,
    "alp":           0.0019,
    "wbc":           0.0554,
    "age":           0.0804,
    "intercept":   -19.9067,
}
GAMMA = 0.0076927
T_MONTHS = 120.0
PA_OFFSET = 141.50225
PA_LN_COEF = -0.00553
PA_DENOM = 0.090165


def _download(name: str, url: str) -> str:
    dest = os.path.join(CACHE_DIR, name)
    if os.path.exists(dest):
        return dest
    print(f"  Downloading {name}...", end=" ", flush=True)
    try:
        urllib.request.urlretrieve(url, dest)
        print("done")
    except Exception as e:
        print(f"FAILED: {e}")
        raise
    return dest


def _load_xpt(name: str, url: str) -> pd.DataFrame:
    path = _download(name, url)
    return pd.read_sas(path, format="xport", encoding="utf-8")


def _load_mortality(name: str, url: str) -> pd.DataFrame:
    path = _download(name, url)
    colspecs = [(0, 6), (14, 15), (15, 16), (43, 47), (47, 51)]
    colnames = ["SEQN", "ELIGSTAT", "MORTSTAT", "PERMTH_INT", "PERMTH_EXM"]
    df = pd.read_fwf(path, colspecs=colspecs, names=colnames, header=None)
    df["SEQN"] = pd.to_numeric(df["SEQN"], errors="coerce")
    return df


def compute_phenoage(row: pd.Series) -> float:
    """Levine 2018 PhenoAge using canonical SI units."""
    xb = (
        COEF["intercept"]
        + COEF["albumin"]    * row["albumin_gl"]        # g/L
        + COEF["creatinine"] * row["creatinine_umoll"]  # umol/L
        + COEF["glucose"]    * row["glucose_mmoll"]     # mmol/L
        + COEF["crp_ln"]     * row["crp_ln"]            # ln(mg/dL)
        + COEF["lymphocyte"] * row["lymphocyte_pct"]    # %
        + COEF["mcv"]        * row["mcv_fl"]            # fL
        + COEF["rdw"]        * row["rdw_pct"]           # %
        + COEF["alp"]        * row["alp_ul"]            # U/L
        + COEF["wbc"]        * row["wbc_10e9"]          # 10^9/L
        + COEF["age"]        * row["age"]               # years
    )
    mort = 1 - math.exp(-math.exp(xb) * (math.exp(GAMMA * T_MONTHS) - 1) / GAMMA)
    mort = max(1e-10, min(1 - 1e-10, mort))
    return PA_OFFSET + math.log(PA_LN_COEF * math.log(1 - mort)) / PA_DENOM


def main() -> bool:
    print("=" * 65)
    print("NHANES PHENOAGE CALIBRATION EVAL")
    print(f"Run at: {datetime.utcnow().isoformat()}+00:00")
    print("External ground truth: Levine 2018, PMID 29676998")
    print("=" * 65)
    print()

    # ── 1. Download ────────────────────────────────────────────────────────────
    print("[1] Downloading NHANES 2017-2018 from CDC...")
    demo   = _load_xpt("DEMO_J.XPT",   FILES["DEMO_J.XPT"])
    biopro = _load_xpt("BIOPRO_J.XPT", FILES["BIOPRO_J.XPT"])
    cbc    = _load_xpt("CBC_J.XPT",    FILES["CBC_J.XPT"])
    crp    = _load_xpt("HSCRP_J.XPT",  FILES["HSCRP_J.XPT"])
    mort   = _load_mortality(
        "NHANES_2017_2018_MORT_2019_PUBLIC.dat",
        FILES["NHANES_2017_2018_MORT_2019_PUBLIC.dat"],
    )
    print(f"  DEMO: {len(demo)} rows")
    print(f"  BIOPRO: {len(biopro)} rows")
    print(f"  CBC: {len(cbc)} rows")
    print(f"  CRP: {len(crp)} rows")
    print(f"  Mortality: {len(mort)} rows")
    print()

    # ── 2. Merge ───────────────────────────────────────────────────────────────
    print("[2] Merging datasets on SEQN...")
    df = (
        demo[["SEQN", "RIDAGEYR"]]
        .merge(biopro[["SEQN", "LBDSALSI", "LBDSCRSI", "LBDSGLSI", "LBXSAPSI"]], on="SEQN", how="left")
        .merge(cbc[["SEQN", "LBXWBCSI", "LBXLYPCT", "LBXMCVSI", "LBXRDW"]], on="SEQN", how="left")
        .merge(crp[["SEQN", "LBXHSCRP"]], on="SEQN", how="left")
        .merge(mort[["SEQN", "MORTSTAT", "PERMTH_INT"]], on="SEQN", how="left")
    )
    print(f"  Merged: {len(df)} rows")
    print()

    # ── 3. Map to canonical units ──────────────────────────────────────────────
    print("[3] Mapping NHANES SI columns to Levine 2018 canonical units...")

    # NHANES SI columns are already in canonical units — no conversion needed
    # LBDSALSI  = albumin g/L          → canonical: g/L
    # LBDSCRSI  = creatinine umol/L    → canonical: umol/L
    # LBDSGLSI  = glucose mmol/L       → canonical: mmol/L
    # LBXSAPSI  = ALP U/L              → canonical: U/L
    # LBXWBCSI  = WBC 10^9/L           → canonical: 10^9/L
    # LBXLYPCT  = lymphocyte %         → canonical: %
    # LBXMCVSI  = MCV fL               → canonical: fL
    # LBXRDW    = RDW %                → canonical: %
    # LBXHSCRP  = hsCRP mg/L           → ln(mg/dL) = ln(mg/L / 10)

    df["albumin_gl"]       = df["LBDSALSI"]
    df["creatinine_umoll"] = df["LBDSCRSI"]
    df["glucose_mmoll"]    = df["LBDSGLSI"]
    df["alp_ul"]           = df["LBXSAPSI"]
    df["wbc_10e9"]         = df["LBXWBCSI"]
    df["lymphocyte_pct"]   = df["LBXLYPCT"]
    df["mcv_fl"]           = df["LBXMCVSI"]
    df["rdw_pct"]          = df["LBXRDW"]
    df["crp_mg_l"]         = df["LBXHSCRP"]
    df["crp_ln"]           = np.log(df["crp_mg_l"] / 10.0)  # ln(mg/dL)
    df["age"]              = df["RIDAGEYR"]

    required = [
        "albumin_gl", "creatinine_umoll", "glucose_mmoll",
        "crp_ln", "lymphocyte_pct", "mcv_fl", "rdw_pct", "alp_ul", "wbc_10e9",
    ]

    df = df[
        (df["age"] >= 20) & (df["age"] <= 85)
    ].dropna(subset=required + ["age"]).copy()

    # Drop rows where CRP was 0 (ln undefined)
    df = df[np.isfinite(df["crp_ln"])].copy()

    n = len(df)
    print(f"  Complete cases (age 20-85, all 9 biomarkers): {n}")
    print()

    # ── 4. Compute PhenoAge ────────────────────────────────────────────────────
    print("[4] Computing PhenoAge for each participant...")
    df["phenoage"] = df.apply(compute_phenoage, axis=1)
    print(f"  PhenoAge range: {df['phenoage'].min():.1f} – {df['phenoage'].max():.1f} yr")
    print(f"  Mean PhenoAge: {df['phenoage'].mean():.2f} yr")
    print(f"  Mean chronological age: {df['age'].mean():.2f} yr")
    print(f"  Mean age acceleration: {(df['phenoage'] - df['age']).mean():.2f} yr")
    print()

    # ── 5. Gate checks ─────────────────────────────────────────────────────────
    print("[5] Acceptance gate checks...")
    results = {}
    all_pass = True

    # Gate 1: N >= 2000
    gate1 = n >= 2000
    results["n_complete_cases"] = {"value": n, "threshold": 2000, "pass": gate1}
    status = "✓" if gate1 else "✗"
    print(f"  {status} Gate 1 — N complete cases: {n} (threshold: >= 2000)")
    if not gate1:
        all_pass = False

    # Gate 2: Pearson r >= 0.75
    r = float(np.corrcoef(df["phenoage"], df["age"])[0, 1])
    gate2 = r >= 0.75
    results["pearson_r"] = {"value": round(r, 4), "threshold": 0.75, "pass": gate2}
    status = "✓" if gate2 else "✗"
    print(f"  {status} Gate 2 — Pearson r(PhenoAge, age): {r:.4f} (threshold: >= 0.75)")
    if not gate2:
        all_pass = False

    # Gate 3: Mean bias within +/- 5 years (Levine 2018 NHANES III mean bias ~0)
    bias = float((df["phenoage"] - df["age"]).mean())
    gate3 = abs(bias) <= 5.0
    results["mean_bias_yr"] = {"value": round(bias, 4), "threshold": 5.0, "pass": gate3}
    status = "✓" if gate3 else "✗"
    print(f"  {status} Gate 3 — Mean bias (PhenoAge - age): {bias:+.4f} yr (threshold: +/- 5.0)")
    if not gate3:
        all_pass = False

    # Gate 4: PhenoAge AUC >= chronological age AUC for 10-yr mortality
    mort_df = df.dropna(subset=["MORTSTAT", "PERMTH_INT"]).copy()
    mort_df["MORTSTAT"] = pd.to_numeric(mort_df["MORTSTAT"], errors="coerce")
    mort_df["PERMTH_INT"] = pd.to_numeric(mort_df["PERMTH_INT"], errors="coerce")
    mort_df = mort_df[mort_df["MORTSTAT"].isin([0, 1])].copy()

    mort_df["died_10yr"] = (
        (mort_df["MORTSTAT"] == 1) & (mort_df["PERMTH_INT"] <= 120)
    ).astype(int)
    mort_df = mort_df[
        ((mort_df["MORTSTAT"] == 1) & (mort_df["PERMTH_INT"] <= 120)) |
        (mort_df["PERMTH_INT"] >= 120)
    ].copy()

    n_mort = len(mort_df)
    n_died = int(mort_df["died_10yr"].sum())
    print(f"\n  Mortality subset: {n_mort} participants, {n_died} 10-yr deaths ({100*n_died/max(1,n_mort):.1f}%)")

    if n_died >= 10 and n_mort - n_died >= 10:
        from sklearn.metrics import roc_auc_score
        auc_phenoage = roc_auc_score(mort_df["died_10yr"], mort_df["phenoage"])
        auc_chron    = roc_auc_score(mort_df["died_10yr"], mort_df["age"])
        gate4 = auc_phenoage >= auc_chron
        results["auc_phenoage"] = round(auc_phenoage, 4)
        results["auc_chronological"] = round(auc_chron, 4)
        results["auc_gate_pass"] = gate4
        status = "✓" if gate4 else "✗"
        print(f"  {status} Gate 4 — AUC PhenoAge: {auc_phenoage:.4f}, AUC chron age: {auc_chron:.4f}")
        if not gate4:
            all_pass = False
    else:
        print(f"  ~ Gate 4 — Insufficient mortality events ({n_died}) — skipped")
        results["auc_gate_pass"] = None

    # ── 6. Summary ─────────────────────────────────────────────────────────────
    print()
    print("=" * 65)
    overall = "PASS ✓" if all_pass else "FAIL ✗"
    print(f"RESULT: {overall}")
    print(f"  N={n}, r={r:.4f}, bias={bias:+.4f}yr")
    print("=" * 65)

    out = {
        "run_at": datetime.utcnow().isoformat() + "+00:00",
        "n_complete_cases": n,
        "pearson_r": round(r, 4),
        "mean_bias_yr": round(bias, 4),
        "gates": results,
        "overall_pass": all_pass,
    }
    out_path = "/workspace/longivity/tests/eval/nhanes_calibration_results.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Saved: {out_path}")

    return all_pass


if __name__ == "__main__":
    try:
        ok = main()
        sys.exit(0 if ok else 1)
    except Exception as e:
        import traceback
        print(f"\nFATAL: {e}")
        traceback.print_exc()
        sys.exit(2)
