#!/usr/bin/env python3
"""
Download NHANES data for PhenoAge biomarker analysis.

Usage:
    pip install pyreadstat requests
    python datasets/scripts/download_nhanes.py --cycle 2017-2018

Downloads:
    - BIOPRO (biochemistry): albumin, creatinine, glucose, alkaline phosphatase
    - CBC (blood count): WBC, lymphocyte%, MCV, RDW
    - HSCRP (high-sensitivity CRP)
    - DEMO (demographics): age, sex

Output: datasets/data/nhanes/nhanes_{cycle}_phenoage_biomarkers.csv
"""
import argparse
import os
import sys
import urllib.request
from pathlib import Path

try:
    import pyreadstat
    import pandas as pd
except ImportError:
    print("ERROR: Install required packages: pip install pyreadstat pandas")
    sys.exit(1)

# NHANES file mappings by cycle
NHANES_FILES = {
    "2017-2018": {
        "BIOPRO": "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/BIOPRO_J.XPT",
        "CBC":    "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/CBC_J.XPT",
        "HSCRP": "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/HSCRP_J.XPT",
        "DEMO":  "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/DEMO_J.XPT",
    },
    "2015-2016": {
        "BIOPRO": "https://wwwn.cdc.gov/Nchs/Nhanes/2015-2016/BIOPRO_I.XPT",
        "CBC":    "https://wwwn.cdc.gov/Nchs/Nhanes/2015-2016/CBC_I.XPT",
        "HSCRP": "https://wwwn.cdc.gov/Nchs/Nhanes/2015-2016/HSCRP_I.XPT",
        "DEMO":  "https://wwwn.cdc.gov/Nchs/Nhanes/2015-2016/DEMO_I.XPT",
    },
}

# PhenoAge biomarker variable names in NHANES
PHENOAGE_VARS = {
    "LBDSALSI": "albumin_g_dl",
    "LBXSCR":   "creatinine_mg_dl",
    "LBXSGL":   "glucose_mg_dl",
    "LBXSAPSI": "alkaline_phosphatase_u_l",
    "LBXWBCSI": "wbc_1000_ul",
    "LBXLYPCT": "lymphocyte_pct",
    "LBXMCVSI": "mcv_fl",
    "LBXRDW":   "rdw_pct",
    "LBXHSCRP": "crp_mg_l",
    "RIDAGEYR":  "age_years",
    "RIAGENDR":  "sex",
}


def download_xpt(url: str, dest: Path) -> Path:
    """Download an XPT file from CDC NHANES."""
    print(f"  Downloading {url.split('/')[-1]}...")
    req = urllib.request.Request(url, headers={"User-Agent": "longivity-research/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        dest.write_bytes(resp.read())
    print(f"  Saved to {dest} ({dest.stat().st_size:,} bytes)")
    return dest


def main():
    parser = argparse.ArgumentParser(description="Download NHANES PhenoAge biomarker data")
    parser.add_argument("--cycle", default="2017-2018", choices=list(NHANES_FILES.keys()))
    parser.add_argument("--output", default="datasets/data/nhanes/")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = output_dir / "tmp"
    tmp_dir.mkdir(exist_ok=True)

    files = NHANES_FILES[args.cycle]
    dfs = {}

    for name, url in files.items():
        xpt_path = tmp_dir / f"{name}_{args.cycle.replace('-', '_')}.XPT"
        if not xpt_path.exists():
            download_xpt(url, xpt_path)
        df, meta = pyreadstat.read_xport(str(xpt_path))
        dfs[name] = df
        print(f"  {name}: {len(df)} rows, {len(df.columns)} columns")

    # Merge on SEQN (participant ID)
    merged = dfs["DEMO"][["SEQN", "RIDAGEYR", "RIAGENDR"]].copy()
    for name in ["BIOPRO", "CBC", "HSCRP"]:
        if name in dfs:
            merged = merged.merge(dfs[name], on="SEQN", how="left")

    # Select PhenoAge variables
    available_vars = [v for v in PHENOAGE_VARS.keys() if v in merged.columns]
    result = merged[["SEQN"] + available_vars].copy()
    result.rename(columns=PHENOAGE_VARS, inplace=True)
    result["sex"] = result["sex"].map({1: "male", 2: "female"})

    # Filter to adults 18+
    result = result[result["age_years"] >= 18].copy()

    output_path = output_dir / f"nhanes_{args.cycle.replace('-', '_')}_phenoage_biomarkers.csv"
    result.to_csv(output_path, index=False)
    print(f"\nSaved: {output_path} ({len(result):,} rows)")
    print(f"Columns: {list(result.columns)}")


if __name__ == "__main__":
    main()
