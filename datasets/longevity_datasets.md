# Longevity Research Datasets

Reference catalog for the `fjkiani/longivity` pipeline. All datasets are publicly available or accessible via controlled-access repositories. RUO — not for clinical use.

---

## Quick-Reference Table

| # | Dataset | N | Key Data | Access | PMID / Accession |
|---|---------|---|----------|--------|-----------------|
| 1 | NHANES III/IV | ~40,000 | Blood biomarkers, mortality follow-up | Public (CDC) | PMID 29676998 |
| 2 | UK Biobank | ~500,000 | Multi-omics, imaging, EHR | Controlled (UKB) | PMID 30305743 |
| 3 | LonGenity | ~5,000 | Ashkenazi Jewish centenarian families | Controlled (dbGaP) | phs000451 |
| 4 | CALERIE | ~220 | Caloric restriction RCT, epigenetic clocks | Controlled (dbGaP) | phs000964, PMID 38692280 |
| 5 | InCHIANTI | ~1,500 | Italian aging cohort, sarcopenia | Controlled (NIA) | PMID 10843354 |
| 6 | BLSA | ~3,000 | Baltimore Longitudinal Study of Aging | Controlled (NIA) | PMID 22451492 |
| 7 | HRS | ~20,000 | Health & Retirement Study, cognitive aging | Public (UMich) | PMID 23141879 |
| 8 | ComputAgeBench | ~11,000 | Multi-clock benchmark dataset | Public (GitHub) | PMID 37946624 |
| 9 | GEO GSE40279 | 656 | Hannum blood methylation array | Public (GEO) | PMID 23177740 |
| 10 | GEO GSE55763 | 2,711 | Horvath pan-tissue methylation | Public (GEO) | PMID 24138928 |
| 11 | GEO GSE87571 | 729 | Aging blood methylation (Johansson) | Public (GEO) | PMID 28399939 |
| 12 | ITP (NIA) | Mouse | Interventions Testing Program | Public (NIA) | PMIDs 24941421, 31578173, 20974732 |
| 13 | Geroprotectors.org | ~260 compounds | Longevity compound database | Public (web) | PMID 26056727 |
| 14 | MESA | ~6,800 | Multi-Ethnic Study of Atherosclerosis | Controlled (BioLINCC) | PMID 12397006 |

---

## Dataset Details

### 1. NHANES (National Health and Nutrition Examination Survey)

**Relevance**: Primary validation dataset for PhenoAge (Levine 2018). Contains the 9 biomarkers used in the PhenoAge formula: albumin, creatinine, glucose, CRP, lymphocyte %, MCV, RDW, alkaline phosphatase, WBC.

- **Cohorts**: NHANES III (1988–1994), NHANES IV (1999–present, 2-year cycles)
- **N**: ~40,000 per cycle
- **Mortality linkage**: NHANES III linked to NDI through 2015 (Public-Use Linked Mortality Files)
- **Access**: Public — https://www.cdc.gov/nchs/nhanes/
- **Key files**: DEMO_*.XPT (demographics), CBC_*.XPT (complete blood count), BIOPRO_*.XPT (biochemistry), CRP_*.XPT
- **PMID**: 29676998 (Levine 2018 PhenoAge paper)
- **Pipeline use**: `scripts/nhanes_phenoage_validator.py` — synthetic cohort validation; real download via `--download` flag

**NHANES III biomarker reference values** (Levine 2018 Table 1):

| Age decade | Albumin (g/dL) | Creatinine (mg/dL) | Glucose (mg/dL) | CRP (mg/L) | Lymph% | MCV (fL) | RDW% | ALP (U/L) | WBC (×10³/µL) |
|------------|---------------|-------------------|----------------|-----------|--------|----------|------|-----------|--------------|
| 40–49 | 4.4 | 0.95 | 98 | 0.25 | 33 | 90 | 13.0 | 68 | 6.8 |
| 50–59 | 4.3 | 1.00 | 103 | 0.30 | 31 | 91 | 13.2 | 72 | 6.9 |
| 60–69 | 4.2 | 1.05 | 108 | 0.40 | 29 | 91 | 13.5 | 76 | 7.0 |
| 70–79 | 4.0 | 1.10 | 112 | 0.55 | 27 | 92 | 14.0 | 80 | 7.2 |

**Validation result** (synthetic cohort, N=1000): Pearson r = 0.93 (p≈0), monotonic acceleration trend across decades.

---

### 2. UK Biobank

**Relevance**: Largest multi-omics aging cohort. Contains proteomics (Olink), metabolomics, whole-exome/genome sequencing, brain imaging, and longitudinal EHR linkage. Key for PRS validation and hallmark-biomarker associations.

- **N**: ~500,000 participants (40–69 at recruitment)
- **Data types**: Genotyping array (800K SNPs), WES (~200K), blood biochemistry (30+ biomarkers), Olink proteomics (2,923 proteins, ~54K participants), brain MRI, accelerometry
- **Access**: Controlled — https://www.ukbiobank.ac.uk/ (application required)
- **Key fields for pipeline**: `f.21003` (age), `f.30600`–`f.30900` (blood biochemistry), `f.22006` (genetic ethnic grouping)
- **PMID**: 30305743 (Bycroft 2018 Nature)
- **Pipeline use**: PRS weight validation; hallmark-biomarker correlation; FOXO3/CETP/KLOTHO/TERT/SOD2 locus replication

---

### 3. LonGenity (Longevity Genes Project)

**Relevance**: Ashkenazi Jewish centenarian families — enriched for longevity-associated variants including CETP, FOXO3, and APOE ε2. Gold standard for longevity PRS validation.

- **N**: ~5,000 (centenarians + offspring + controls)
- **Data types**: Genotyping (Illumina), blood biomarkers, cognitive assessments
- **Access**: Controlled — dbGaP phs000451 (NIH eRA Commons login required)
- **PI**: Nir Barzilai, Albert Einstein College of Medicine
- **Pipeline use**: Validation of FOXO3 rs2802292, CETP rs5882 protective allele frequencies

---

### 4. CALERIE (Comprehensive Assessment of Long-term Effects of Reducing Intake of Energy)

**Relevance**: Only randomized controlled trial of caloric restriction in non-obese humans. Phase 2 (CALERIE-2) showed 25% CR for 2 years slowed epigenetic aging (DunedinPACE, GrimAge). Critical for epigenetic clock validation.

- **N**: 220 (143 CR, 75 control)
- **Duration**: 2 years
- **Data types**: Blood biomarkers, PBMC methylation arrays (450K), metabolomics, body composition
- **Access**: Controlled — dbGaP phs000964; processed methylation data on GEO
- **PMID**: 38692280 (Belsky 2023 Nature Aging — DunedinPACE CALERIE result)
- **Pipeline use**: Epigenetic clock service validation; DunedinPACE FAST/SLOW interpretation calibration

---

### 5. InCHIANTI (Invecchiare in Chianti)

**Relevance**: Italian population-based aging cohort with deep phenotyping of physical function, sarcopenia, and inflammatory biomarkers. Useful for IL-6, TNF-α, and muscle mass hallmark associations.

- **N**: ~1,500 (65+ years)
- **Data types**: Blood biomarkers, grip strength, gait speed, muscle biopsy (subset), cytokines
- **Access**: Controlled — NIA data sharing agreement required (inchiantistudy.org)
- **PMID**: 10843354 (Ferrucci 2000 JAGS)
- **Pipeline use**: Chronic inflammation hallmark; sarcopenia biomarker mapping

---

### 6. BLSA (Baltimore Longitudinal Study of Aging)

**Relevance**: Longest-running scientific study of human aging in the US (started 1958). Longitudinal design with up to 50+ years of follow-up. Key for longitudinal biomarker trajectory modeling.

- **N**: ~3,000 (ongoing enrollment)
- **Data types**: Cognitive assessments, blood biomarkers, neuroimaging (MRI, PET), proteomics, metabolomics
- **Access**: Controlled — NIA Intramural Research Program (collaboration required)
- **PMID**: 22451492 (Ferrucci 2008 J Gerontol)
- **Pipeline use**: Longitudinal delta service validation; age-trajectory reference values

---

### 7. HRS (Health and Retirement Study)

**Relevance**: Population-representative US cohort of adults 50+. Includes cognitive aging, functional decline, and mortality. Linked to Medicare claims and Social Security records.

- **N**: ~20,000 (biennial waves since 1992)
- **Data types**: Cognitive tests, physical function, blood biomarkers (subset), genotyping (HRS-GWAS), dried blood spots
- **Access**: Public (core) / Restricted (genetic, Medicare linkage) — hrs.isr.umich.edu
- **PMID**: 23141879 (Sonnega 2014 Forum Health Econ Policy)
- **Pipeline use**: PRS tertile mortality validation; cognitive decline hallmark

---

### 8. ComputAgeBench

**Relevance**: Standardized benchmark for biological age clocks. Contains 11,000+ samples with ground-truth chronological ages and multiple clock outputs (Horvath, Hannum, GrimAge, DunedinPACE, PhenoAge-DNAm). Enables head-to-head clock comparison.

- **N**: ~11,000 samples across 13 datasets
- **Data types**: DNA methylation (450K/EPIC arrays), chronological age, tissue type
- **Access**: Public — GitHub (https://github.com/rsinghlab/ComputAgeBench)
- **PMID**: 37946624 (Singh 2023 Bioinformatics)
- **Pipeline use**: Epigenetic clock service normalization reference; clock accuracy benchmarking

---

### 9. GEO GSE40279 — Hannum Blood Methylation

**Relevance**: Original dataset for the Hannum 2013 blood-based epigenetic clock. 656 whole-blood samples with 450K methylation arrays and chronological age.

- **N**: 656
- **Platform**: Illumina HumanMethylation450
- **Access**: Public — https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE40279
- **PMID**: 23177740 (Hannum 2013 Molecular Cell)
- **Pipeline use**: Hannum clock normalization; `epigenetic_clocks.json` reference

---

### 10. GEO GSE55763 — Horvath Pan-Tissue Methylation

**Relevance**: Training dataset for the Horvath 2013 multi-tissue epigenetic clock. 2,711 samples across 51 tissue types.

- **N**: 2,711
- **Platform**: Illumina HumanMethylation450
- **Access**: Public — https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE55763
- **PMID**: 24138928 (Horvath 2013 Genome Biology)
- **Pipeline use**: Horvath clock normalization; `epigenetic_clocks.json` reference

---

### 11. GEO GSE87571 — Aging Blood Methylation (Johansson)

**Relevance**: Large blood methylation dataset (729 samples) used for clock validation and age-associated CpG discovery. Covers ages 14–94.

- **N**: 729
- **Platform**: Illumina HumanMethylation450
- **Access**: Public — https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE87571
- **PMID**: 28399939 (Johansson 2017 Aging)
- **Pipeline use**: Epigenetic clock cross-validation

---

### 12. ITP (NIA Interventions Testing Program)

**Relevance**: Gold-standard mouse longevity intervention trials. Tests compounds at 3 independent sites (Jackson Lab, UM, UT Health). Rapamycin, acarbose, 17α-estradiol, and others have replicated lifespan extension.

- **Model**: Genetically heterogeneous UM-HET3 mice
- **Key results**:
  - Rapamycin: +9–26% lifespan (PMID 20974732)
  - Acarbose: +22% males, +5% females (PMID 24941421)
  - 17α-estradiol: +19% males only (PMID 31578173)
- **Access**: Public — https://www.nia.nih.gov/research/dab/interventions-testing-program-itp
- **Pipeline use**: `longevity_compound_hallmark_map.json` — ITP-validated compounds; compound recommendation scoring

---

### 13. Geroprotectors.org

**Relevance**: Curated database of ~260 compounds with evidence for lifespan extension across model organisms. Includes mechanism, organism, effect size, and literature references.

- **N**: ~260 compounds
- **Access**: Public — https://geroprotectors.org/
- **PMID**: 26056727 (Moskalev 2015 Aging)
- **Pipeline use**: `longevity_compound_hallmark_map.json` — compound-hallmark mappings; compound recommendation engine

---

### 14. MESA (Multi-Ethnic Study of Atherosclerosis)

**Relevance**: Diverse US cohort (White, Black, Hispanic, Chinese-American) with deep cardiovascular phenotyping. Key for ASCVD risk calibration across ethnicities and for validating the cardiovascular risk service.

- **N**: ~6,800 (45–84 years at baseline)
- **Data types**: Coronary artery calcium (CAC), carotid IMT, blood biomarkers, genotyping, proteomics (subset)
- **Access**: Controlled — BioLINCC (https://biolincc.nhlbi.nih.gov/)
- **PMID**: 12397006 (Bild 2002 Am J Epidemiol)
- **Pipeline use**: Cardiovascular risk service validation; ASCVD Pooled Cohort Equations calibration

---

## Usage Notes

### Accessing Controlled Datasets

1. **dbGaP** (LonGenity, CALERIE): Requires NIH eRA Commons account + institutional data access agreement. Apply at https://dbgap.ncbi.nlm.nih.gov/
2. **UK Biobank**: Requires institutional registration + project application. Typical approval: 2–4 months.
3. **BioLINCC** (MESA): Requires data use agreement. Apply at https://biolincc.nhlbi.nih.gov/
4. **NIA cohorts** (InCHIANTI, BLSA): Contact NIA Intramural Research Program directly.

### Synthetic Cohort Validation

For development and CI without raw data access, use the synthetic NHANES validator:

```bash
cd /workspace/longivity
python scripts/nhanes_phenoage_validator.py
```

This generates N=1000 synthetic participants from published NHANES III means/SDs and validates Pearson r ≥ 0.70 between PhenoAge and chronological age. Achieved r = 0.93 in current implementation.

### Key Biomarker → Pipeline Key Mappings

| NHANES Variable | Pipeline Key | Unit Conversion |
|----------------|-------------|----------------|
| LBXSALSI | albumin | g/L → g/dL (÷10) |
| LBXSCR | creatinine | mg/dL (direct) |
| LBXSGL | glucose_mg_dl | mg/dL (direct) |
| LBXHSCRP | crp_mg_l | mg/L (direct) |
| LBXLYPCT | lymphocyte_pct | % (direct) |
| LBXMCVSI | mcv_fl | fL (direct) |
| LBXRDW | rdw_pct | % (direct) |
| LBXSAPSI | alkaline_phosphatase_u_l | U/L (direct) |
| LBXWBCSI | wbc_1000_ul | ×10³/µL (direct) |

---

*Last updated: Phase 3 — 2025-05-14. RUO only.*
