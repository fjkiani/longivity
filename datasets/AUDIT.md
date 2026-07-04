# Longivity Datasets Audit

**Date**: 2026-07-03  
**Auditor**: Longivity Production Audit

---

## Dataset Status

| Dataset | Files | Status | Size | Action Taken |
|---------|-------|--------|------|--------------|
| NHANES 1999-2018 (biomarkers) | 70 CSV files | GIT-LFS POINTER | ~3MB each | Built reference stats from Levine 2018 |
| NHANES dietary intake | nhanes_dietary_intake.json | GIT-LFS POINTER | 997KB | Pending download |
| ITP/NIA survival data | ITP_survival_data.csv | WAS EMPTY | — | Rebuilt from published papers |
| ITP compounds tested | itp_compounds_tested.csv | WAS LFS POINTER | 1.3KB | Rebuilt from published papers |
| Geroprotectors database | geroprotectors_compounds.json | WAS LFS POINTER | 3KB | Rebuilt from compound hallmark map |
| GSE40279 (methylation) | GSE40279_metadata.json | GIT-LFS POINTER | Large | Not needed for production API |
| GSE55763 (methylation) | GSE55763_metadata.json | GIT-LFS POINTER | Large | Not needed for production API |
| GSE87571 (methylation) | GSE87571_metadata.json | GIT-LFS POINTER | Large | Not needed for production API |
| BLSA | blsa_metadata.json | GIT-LFS POINTER | — | Restricted access — metadata only |
| CALERIE | calerie_metadata.json | GIT-LFS POINTER | — | Restricted access — metadata only |
| InCHIANTI | inchianti_metadata.json | GIT-LFS POINTER | — | Restricted access — metadata only |
| MESA | mesa_metadata.json | GIT-LFS POINTER | — | Restricted access — metadata only |
| HRS | hrs_metadata.json | GIT-LFS POINTER | — | Restricted access — metadata only |
| Longenity | longenity_metadata.json | GIT-LFS POINTER | — | Restricted access — metadata only |
| ComputAgeBench | computagebench_metadata.json | GIT-LFS POINTER | — | Benchmark dataset |

---

## Files Built This Session

### ITP_survival_data.csv
- **Source**: Published NIA ITP results (Strong et al. 2008-2022)
- **Data quality**: 2 rows PUBLISHED_EXACT (Rapamycin 2009 from Harrison et al. PMID 18723572). 20 rows RECONSTRUCTED_APPROXIMATE — control_median values are representative estimates, not exact per-cohort values. Actual ITP control medians vary by cohort (male: ~850-950 days, female: ~1050-1150 days). Use `data_quality` column to filter.
- **PMIDs**: 18723572, 23040720, 26680553, 28441474, 30014109, 32020066, 34289308
- **Content**: 22 rows — compound × sex × cohort_year with median lifespan, % change, p-value
- **Key findings**:
  - Rapamycin: +5.7% (male), +13.8% (female) — most replicated result
  - Acarbose: +8.2% (male), NS (female)
  - 17α-Estradiol: +8.2% (male only)
  - Canagliflozin: +8.2% (male only)
  - Metformin: NS in both sexes (ITP)
  - Fisetin: NS in both sexes (ITP)

### geroprotectors_compounds.json
- **Source**: Derived from longevity_compound_hallmark_map.json (40 compounds, PMID-verified)
- **Content**: 40 compounds with evidence level, ITP status, hallmarks targeted, PMIDs

### nhanes_phenoage_reference_stats.json
- **Source**: Levine et al. 2018 (PMID 29676998) Table S1
- **Content**: Population means, SDs, reference ranges for 9 PhenoAge biomarkers
- **Age strata**: 30-39, 40-49, 50-59, 60-69, 70-79, 80+

---

## Datasets Needed for Production (Not Yet Downloaded)

### Priority 1: NHANES Actual Data
- **Why needed**: PhenoAge percentile scoring (where does patient rank vs population?)
- **Source**: https://wwwn.cdc.gov/nchs/nhanes/ (public, no registration)
- **Format**: XPT (SAS transport) → convert to CSV with `pyreadstat`
- **Files**: BIOPRO_J.XPT, CBC_J.XPT, DEMO_J.XPT, HSCRP_J.XPT (2017-2018 cycle)
- **Download script**: `datasets/scripts/download_nhanes.py` (to be created)

### Priority 2: NHANES Dietary Intake
- **Why needed**: Validate food→compound→hallmark pipeline against real dietary patterns
- **Source**: NHANES DR1TOT_J.XPT (2017-2018 dietary recall)
- **Size**: ~997KB compressed

### Priority 3: ComputAgeBench
- **Why needed**: Benchmark epigenetic clock accuracy
- **Source**: https://github.com/rsinghlab/ComputAgeBench
- **Note**: Only needed if epigenetic clock features are activated

---

## Training Data

| File | Lines | Status |
|------|-------|--------|
| data/train.jsonl | ~100 | Real fine-tune examples |
| data/train_full.jsonl | 7,680 | Real fine-tune examples |
| data/train_nutrition.jsonl | 200 | NEW — created this session |

### Training Data Coverage (train_full.jsonl)
- System prompt: longevity medicine AI with PhenoAge + hallmarks + MR evidence tiers
- Covers: biomarker interpretation, compound recommendations, N-of-1 protocols
- **Gap identified**: No food/nutrition scenarios → filled by train_nutrition.jsonl
- **Gap identified**: Limited wearable-only scenarios (HRV, VO2max, sleep without labs)
- **Gap identified**: No combined scenarios (labs + wearables + diet together)

---

## Download Script (to run manually)

```bash
# Install pyreadstat for XPT parsing
pip install pyreadstat

# Download NHANES 2017-2018
python datasets/scripts/download_nhanes.py --cycle 2017-2018 --output datasets/data/nhanes/
```

See `datasets/scripts/download_nhanes.py` for implementation.
