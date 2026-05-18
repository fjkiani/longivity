"""
High-Grade Serous Ovarian Cancer (HGSOC) Treatment Line Panel — EXTENDED
Treatment-Line-Integration Module

Evidence-based resistance cascade data for HGSOC.
Extends the existing ovarian cancer panel with:
- Full Lines 1-3 resistance cascade
- Patient tissue confirmation data
- ABCB1-PARP inhibitor cross-resistance (the critical blind spot)
- BRCA reversion mutation cascade
- Bevacizumab invasion escape

All resistance mechanisms sourced from published peer-reviewed literature.
Patient tissue confirmation noted where available.

References embedded inline with DOI.
"""

HGSOC_TREATMENT_LINES = {
    "cancer_type": "High-Grade Serous Ovarian Cancer (HGSOC)",
    "icd10": "C56",
    "staging_note": "Lines 1-3 apply to Stage III-IV disease. ~70-90% of patients will relapse after first-line treatment.",
    "molecular_subtypes": {
        "BRCA1_mutant": "~15% of HGSOC; highest PARPi benefit",
        "BRCA2_mutant": "~10% of HGSOC; highest PARPi benefit",
        "HRD_positive_BRCA_WT": "~25% of HGSOC; PARPi benefit (niraparib, rucaparib)",
        "HRD_negative": "~50% of HGSOC; limited PARPi benefit"
    },

    "lines": [
        {
            "line": 1,
            "name": "Carboplatin + Paclitaxel ± Bevacizumab",
            "regimens": [
                {
                    "name": "Carboplatin + Paclitaxel",
                    "drugs": ["Carboplatin (AUC 5-6)", "Paclitaxel (175 mg/m²)"],
                    "schedule": "Q3W x 6 cycles",
                    "standard": True
                },
                {
                    "name": "Carboplatin + Paclitaxel + Bevacizumab",
                    "drugs": ["Carboplatin (AUC 5-6)", "Paclitaxel (175 mg/m²)", "Bevacizumab (15 mg/kg)"],
                    "schedule": "Q3W x 6 cycles, then bevacizumab maintenance x 16 cycles",
                    "trial": "GOG-0218 (Burger 2011, NEJM)",
                    "pfs_benefit": "~4 months PFS benefit",
                    "os_benefit": "No significant OS benefit"
                },
                {
                    "name": "Dose-Dense Paclitaxel + Carboplatin",
                    "drugs": ["Carboplatin (AUC 6 Q3W)", "Paclitaxel (80 mg/m² weekly)"],
                    "schedule": "Q3W carboplatin + weekly paclitaxel x 6 cycles"
                }
            ],
            "biomarkers_required": [
                {
                    "marker": "BRCA1/2 germline testing",
                    "purpose": "Informs maintenance PARPi eligibility after response",
                    "tested": True,
                    "timing": "Usually tested during or after Line 1, not before"
                },
                {
                    "marker": "HRD (homologous recombination deficiency) testing",
                    "purpose": "Informs niraparib/rucaparib maintenance eligibility",
                    "tested": "Sometimes",
                    "timing": "Usually tested after Line 1 response"
                }
            ],
            "biomarkers_ignored": [
                {
                    "marker": "ABCB1 (P-glycoprotein / MDR1) baseline expression",
                    "why_matters": "Paclitaxel upregulates ABCB1. ABCB1 is an efflux pump for paclitaxel, olaparib, rucaparib, and doxorubicin. Baseline ABCB1 predicts both paclitaxel resistance AND subsequent PARPi resistance. Not measured before Line 1.",
                    "evidence": "Vaidyanathan A et al. British Journal of Cancer 2016. DOI: 10.1038/bjc.2016.203; Christie E et al. Nature Communications 2019. DOI: 10.1038/s41467-019-09312-9",
                    "evidence_type": "Cell line + PATIENT TISSUE (Christie 2019)"
                },
                {
                    "marker": "EMT status",
                    "why_matters": "Carboplatin and paclitaxel both induce EMT. EMT-high tumors have enhanced invasion/migration and are more likely to develop peritoneal metastases. EMT markers (TGFβ1, ITGAV) confirmed upregulated in relapsed vs newly diagnosed patient tumors.",
                    "evidence": "Leung D et al. Journal of Translational Medicine 2022. DOI: 10.1186/s12967-022-03776-y",
                    "evidence_type": "PATIENT TISSUE — relapsed vs newly diagnosed HGSOC"
                }
            ],
            "resistance_mechanisms_induced": [
                {
                    "mechanism": "ABCB1 transcriptional fusions — chemotherapy preconditions PARPi resistance",
                    "pathway": "Paclitaxel exposure → ABCB1 gene fusions with strong promoters → MDR1 overexpression → efflux of paclitaxel, olaparib, rucaparib, doxorubicin",
                    "consequence": "Prior paclitaxel directly preconditions resistance to PARP inhibitors (Line 2). Fusion positivity strongly associated with number of lines of MDR1-substrate chemotherapy.",
                    "cross_resistance_to": ["Olaparib (Line 2)", "Rucaparib (Line 2)", "Niraparib (Line 2 — partial)", "Liposomal doxorubicin (Line 3)"],
                    "evidence": "Christie E et al. Nature Communications 2019. DOI: 10.1038/s41467-019-09312-9",
                    "patient_tissue_confirmed": True,
                    "critical": True
                },
                {
                    "mechanism": "ABCB1 upregulation with cross-resistance to olaparib and rucaparib",
                    "pathway": "Paclitaxel → ABCB1 overexpression → active efflux of paclitaxel, olaparib, doxorubicin, rucaparib",
                    "consequence": "Paclitaxel-resistant cells are cross-resistant to olaparib, doxorubicin, and rucaparib. Routine first-line paclitaxel may significantly limit subsequent chemotherapy options.",
                    "cross_resistance_to": ["Olaparib", "Rucaparib", "Doxorubicin", "Liposomal doxorubicin"],
                    "evidence": "Vaidyanathan A et al. British Journal of Cancer 2016. DOI: 10.1038/bjc.2016.203",
                    "patient_tissue_confirmed": False,
                    "critical": True
                },
                {
                    "mechanism": "EMT induction with MMP2/MMP9 upregulation",
                    "pathway": "Taxane resistance → miR-200b/c downregulation → ZEB1 upregulation → EMT → MMP2/MMP9 upregulation",
                    "consequence": "Mesenchymal phenotype, enhanced invasion, peritoneal dissemination",
                    "cross_resistance_to": ["Immunotherapy (immune-excluded phenotype)"],
                    "evidence": "Duran G et al. British Journal of Cancer 2017. DOI: 10.1038/bjc.2017.102",
                    "patient_tissue_confirmed": False
                },
                {
                    "mechanism": "Carboplatin-induced EMT confirmed in patient relapsed tumors",
                    "pathway": "Carboplatin → TGFβ1/ITGAV/AKR1B1/G6PD upregulation → EMT + metabolic reprogramming",
                    "consequence": "Enhanced migration, reduced proliferation (dormancy), immune evasion",
                    "cross_resistance_to": ["Continued platinum", "Immunotherapy"],
                    "evidence": "Leung D et al. Journal of Translational Medicine 2022. DOI: 10.1186/s12967-022-03776-y",
                    "patient_tissue_confirmed": True
                },
                {
                    "mechanism": "BRCA reversion mutation selection under platinum pressure",
                    "pathway": "Carboplatin → DNA damage → MMEJ activation → BRCA1/2 reversion mutations → HR restoration",
                    "consequence": "Restored homologous recombination → resistance to both platinum and PARP inhibitors",
                    "cross_resistance_to": ["PARP inhibitors (Line 2)", "Continued platinum"],
                    "evidence": "Tobalina L et al. Annals of Oncology 2020. DOI: 10.1016/j.annonc.2020.10.470; Lin K et al. Cancer Discovery 2018. DOI: 10.1158/2159-8290.cd-18-0715",
                    "patient_tissue_confirmed": True
                },
                {
                    "mechanism": "Cancer stem cell enrichment via ABCB1/G2M arrest",
                    "pathway": "Carboplatin → ABCB1 overexpression → G2/M-arrested stem-like cells with high stemness markers",
                    "consequence": "Treatment-resistant CSC subpopulation survives, drives relapse",
                    "cross_resistance_to": ["All subsequent cytotoxic agents"],
                    "evidence": "Lee D et al. Cell Death Discovery 2025. DOI: 10.1038/s41420-025-02435-7",
                    "patient_tissue_confirmed": False
                },
                {
                    "mechanism": "Bevacizumab-driven invasion escape (when bevacizumab added)",
                    "pathway": "Bevacizumab → VEGF blockade → tumor hypoxia → HIF-1α → MMP-2/9/12 → invasion",
                    "consequence": "GOG-0218: 4-month PFS benefit, NO OS benefit. Tumor learns to invade.",
                    "cross_resistance_to": ["Continued bevacizumab"],
                    "evidence": "Burger R et al. NEJM 2011. DOI: 10.1056/nejmoa1104390",
                    "patient_tissue_confirmed": True
                }
            ]
        },
        {
            "line": 2,
            "name": "PARP Inhibitor Maintenance ± Bevacizumab",
            "regimens": [
                {
                    "name": "Olaparib",
                    "drugs": ["Olaparib (300 mg BID)"],
                    "schedule": "Continuous until progression",
                    "indication": "BRCA1/2 mutant (germline or somatic)",
                    "trial": "SOLO-1 (first-line maintenance), SOLO-2 (recurrent)",
                    "abcb1_substrate": True
                },
                {
                    "name": "Niraparib",
                    "drugs": ["Niraparib (200-300 mg daily)"],
                    "schedule": "Continuous until progression",
                    "indication": "All patients regardless of BRCA/HRD status (FDA approved)",
                    "abcb1_substrate": "Partial"
                },
                {
                    "name": "Rucaparib",
                    "drugs": ["Rucaparib (600 mg BID)"],
                    "schedule": "Continuous until progression",
                    "indication": "BRCA mutant or HRD positive",
                    "abcb1_substrate": True
                },
                {
                    "name": "Olaparib + Bevacizumab",
                    "drugs": ["Olaparib (300 mg BID)", "Bevacizumab (15 mg/kg Q3W)"],
                    "schedule": "Continuous olaparib + bevacizumab Q3W",
                    "indication": "HRD positive (BRCA mutant or HRD positive)",
                    "trial": "PAOLA-1"
                }
            ],
            "biomarkers_required": [
                {
                    "marker": "BRCA1/2 mutation status",
                    "purpose": "Olaparib/rucaparib require BRCA mutation",
                    "tested": True
                },
                {
                    "marker": "HRD status",
                    "purpose": "Niraparib/rucaparib benefit in HRD-positive tumors",
                    "tested": "Sometimes"
                }
            ],
            "biomarkers_ignored": [
                {
                    "marker": "ABCB1 expression (from Line 1 paclitaxel)",
                    "why_matters": "Olaparib and rucaparib are ABCB1 substrates. If ABCB1 was upregulated by Line 1 paclitaxel (confirmed in patient tissue via transcriptional fusions), the PARP inhibitor will be effluxed out of the tumor cell before it can reach its target. ABCB1 is not measured before prescribing PARPi.",
                    "evidence": "Christie E et al. Nature Communications 2019. DOI: 10.1038/s41467-019-09312-9; Vaidyanathan A et al. British Journal of Cancer 2016. DOI: 10.1038/bjc.2016.203",
                    "evidence_type": "PATIENT TISSUE (Christie 2019)"
                },
                {
                    "marker": "BRCA reversion mutation status (ctDNA)",
                    "why_matters": "BRCA reversion mutations are present in 13-18% of platinum-resistant patients BEFORE starting PARPi. These patients will not respond to PARPi. ctDNA testing can detect these mutations but is not standard before PARPi initiation.",
                    "evidence": "Lin K et al. Cancer Discovery 2018. DOI: 10.1158/2159-8290.cd-18-0715",
                    "evidence_type": "PATIENT TISSUE — circulating tumor DNA"
                }
            ],
            "resistance_mechanisms_induced": [
                {
                    "mechanism": "BRCA reversion mutations",
                    "pathway": "PARPi pressure → MMEJ activation → BRCA1/2 reversion mutations → HR restoration",
                    "consequence": "43% of ovarian cancer patients on olaparib develop BRCA reversion mutations at progression. Multiple clonal events.",
                    "cross_resistance_to": ["Continued PARPi", "Platinum re-challenge"],
                    "evidence": "Lukashchuk N et al. JCO 2022. DOI: 10.1200/jco.2022.40.16_suppl.5559",
                    "patient_tissue_confirmed": True,
                    "critical": True
                },
                {
                    "mechanism": "Replication fork stabilization (RAD51 upregulation)",
                    "pathway": "PARPi → replication stress → RAD51 upregulation → fork protection → HR restoration",
                    "consequence": "34% of PARPi-resistant patients show replication fork stability as resistance mechanism",
                    "cross_resistance_to": ["Continued PARPi", "Platinum"],
                    "evidence": "Kim Y et al. Clinical Cancer Research 2023. DOI: 10.1158/1078-0432.ccr-22-3715",
                    "patient_tissue_confirmed": True
                },
                {
                    "mechanism": "Upregulated survival pathways (PI3K/AKT, RAS/MAPK)",
                    "pathway": "PARPi → selection for PI3K/AKT and RAS/MAPK activation",
                    "consequence": "41% of PARPi-resistant patients show upregulated survival pathways",
                    "cross_resistance_to": ["Continued PARPi"],
                    "evidence": "Kim Y et al. Clinical Cancer Research 2023. DOI: 10.1158/1078-0432.ccr-22-3715",
                    "patient_tissue_confirmed": True
                },
                {
                    "mechanism": "Increased mutational heterogeneity",
                    "pathway": "PARPi → genomic instability → clonal evolution",
                    "consequence": "89.7% of patients show at least one new post-progression mutation. Multiple resistance mechanisms co-exist.",
                    "cross_resistance_to": ["All subsequent therapies"],
                    "evidence": "Kim Y et al. Clinical Cancer Research 2023. DOI: 10.1158/1078-0432.ccr-22-3715",
                    "patient_tissue_confirmed": True
                }
            ]
        },
        {
            "line": 3,
            "name": "Single-Agent Chemotherapy",
            "regimens": [
                {
                    "name": "Liposomal Doxorubicin (Doxil/Caelyx)",
                    "drugs": ["Pegylated liposomal doxorubicin (40-50 mg/m²)"],
                    "schedule": "Q4W",
                    "abcb1_substrate": True,
                    "note": "ABCB1 substrate — cross-resistant with paclitaxel-selected ABCB1 overexpression"
                },
                {
                    "name": "Gemcitabine",
                    "drugs": ["Gemcitabine (1000 mg/m² D1,8)"],
                    "schedule": "Q3W",
                    "abcb1_substrate": False,
                    "note": "Not an ABCB1 substrate, but faces restored HR from BRCA reversion"
                },
                {
                    "name": "Topotecan",
                    "drugs": ["Topotecan (1.25-1.5 mg/m² D1-5)"],
                    "schedule": "Q3W",
                    "abcb1_substrate": True,
                    "note": "ABCB1 substrate — cross-resistant with paclitaxel-selected ABCB1 overexpression"
                },
                {
                    "name": "Paclitaxel (weekly)",
                    "drugs": ["Paclitaxel (80 mg/m² weekly)"],
                    "schedule": "Weekly",
                    "note": "Re-challenge with paclitaxel — faces ABCB1 overexpression from Line 1 paclitaxel"
                }
            ],
            "biomarkers_required": [],
            "biomarkers_ignored": [
                {
                    "marker": "ABCB1 expression",
                    "why_matters": "Liposomal doxorubicin and topotecan are ABCB1 substrates. The tumor has been expressing ABCB1 since Line 1 paclitaxel. These drugs will be effluxed by the same pump.",
                    "evidence": "Vaidyanathan A et al. British Journal of Cancer 2016. DOI: 10.1038/bjc.2016.203",
                    "evidence_type": "Cell line"
                },
                {
                    "marker": "BRCA reversion status",
                    "why_matters": "Patients with BRCA reversion mutations have restored HR. Gemcitabine-induced DNA damage will be repaired more efficiently. Platinum re-challenge will fail.",
                    "evidence": "Kim Y et al. Clinical Cancer Research 2023. DOI: 10.1158/1078-0432.ccr-22-3715",
                    "evidence_type": "PATIENT TISSUE — ctDNA"
                }
            ],
            "clinical_reality": {
                "response_rate_liposomal_dox": "~10-15% in platinum-resistant disease",
                "response_rate_gemcitabine": "~15-20% in platinum-resistant disease",
                "response_rate_topotecan": "~15-20% in platinum-resistant disease",
                "comment": "These are the drugs given to patients after two lines of treatment have systematically upregulated ABCB1 (effluxes doxorubicin and topotecan), restored HR (reduces gemcitabine efficacy), and enriched cancer stem cells. No biomarker testing is performed."
            }
        }
    ],

    "cross_resistance_map": [
        {
            "from_drug": "Paclitaxel (Line 1)",
            "mechanism": "ABCB1 transcriptional fusions",
            "blind_to": "Olaparib (Line 2)",
            "evidence": "Christie E et al. Nature Communications 2019. DOI: 10.1038/s41467-019-09312-9",
            "severity": "CRITICAL — confirmed in patient tumor tissue. Prior chemo preconditions PARPi resistance.",
            "patient_tissue": True
        },
        {
            "from_drug": "Paclitaxel (Line 1)",
            "mechanism": "ABCB1 upregulation",
            "blind_to": "Rucaparib (Line 2)",
            "evidence": "Vaidyanathan A et al. British Journal of Cancer 2016. DOI: 10.1038/bjc.2016.203",
            "severity": "HIGH — active efflux confirmed",
            "patient_tissue": False
        },
        {
            "from_drug": "Paclitaxel (Line 1)",
            "mechanism": "ABCB1 upregulation",
            "blind_to": "Liposomal doxorubicin (Line 3)",
            "evidence": "Vaidyanathan A et al. British Journal of Cancer 2016. DOI: 10.1038/bjc.2016.203",
            "severity": "HIGH — active efflux confirmed",
            "patient_tissue": False
        },
        {
            "from_drug": "Carboplatin (Line 1)",
            "mechanism": "BRCA reversion mutation selection via MMEJ",
            "blind_to": "PARP inhibitors (Line 2)",
            "evidence": "Tobalina L et al. Annals of Oncology 2020. DOI: 10.1016/j.annonc.2020.10.470",
            "severity": "CRITICAL — platinum creates the resistance mechanism to PARPi",
            "patient_tissue": True
        },
        {
            "from_drug": "PARP inhibitors (Line 2)",
            "mechanism": "BRCA reversion mutations (43% at progression)",
            "blind_to": "Platinum re-challenge",
            "evidence": "Lukashchuk N et al. JCO 2022. DOI: 10.1200/jco.2022.40.16_suppl.5559",
            "severity": "CRITICAL — 43% of patients on olaparib develop reversion mutations",
            "patient_tissue": True
        },
        {
            "from_drug": "Bevacizumab (Lines 1-2)",
            "mechanism": "Invasion escape (no OS benefit)",
            "blind_to": "Continued bevacizumab",
            "evidence": "Burger R et al. NEJM 2011. DOI: 10.1056/nejmoa1104390",
            "severity": "HIGH — GOG-0218: 4-month PFS benefit, no OS benefit",
            "patient_tissue": True
        }
    ],

    "the_abcb1_parp_scandal": """
    THE ABCB1-PARP INHIBITOR SCANDAL IN OVARIAN CANCER
    ===================================================
    
    Standard Line 1: Carboplatin + Paclitaxel
    Standard Line 2: PARP inhibitor (olaparib, rucaparib)
    
    THE PROBLEM:
    1. Paclitaxel (Line 1) upregulates ABCB1/P-glycoprotein
    2. Olaparib and rucaparib (Line 2) are ABCB1 substrates
    3. The PARP inhibitor is effluxed out of the tumor cell by the pump that paclitaxel trained
    4. The drug never reaches its target (PARP1 in the nucleus)
    
    THE EVIDENCE:
    - Vaidyanathan 2016 (Br J Cancer): Paclitaxel-resistant cells cross-resistant to olaparib, 
      rucaparib, and doxorubicin via ABCB1. "Routine prescription of first-line paclitaxel may 
      significantly limit subsequent chemotherapy options in ovarian cancer patients."
    
    - Christie 2019 (Nature Communications): ABCB1 transcriptional fusions confirmed in 
      chemotherapy-treated patient tumor tissue. "Fusion positivity was strongly associated with 
      the number of lines of MDR1-substrate chemotherapy given." "Prior chemotherapy may 
      precondition resistance to PARPi."
    
    THE SCANDAL:
    ABCB1 is not measured before prescribing PARP inhibitors.
    The oncologist does not know whether the drug will reach its target.
    The patient pays $15,000/month for a drug that may be effluxed before it acts.
    """,

    "key_insight": """
    HGSOC RESISTANCE CASCADE SUMMARY
    ==================================
    
    LINE 1 (Carboplatin + Paclitaxel):
    - Upregulates: ABCB1 (effluxes PARPi), BRCA reversion mutations (restores HR), EMT (invasion), CSC enrichment
    - Ignored biomarkers: ABCB1 baseline, EMT status
    
    LINE 1→2 TRANSITION (The Blind Spot):
    - Olaparib and rucaparib are ABCB1 substrates — paclitaxel already trained the tumor to efflux them
    - BRCA reversion mutations present in 13-18% of platinum-resistant patients BEFORE PARPi starts
    - Neither ABCB1 nor BRCA reversion status is measured before PARPi initiation
    
    LINE 2 (PARP Inhibitors):
    - Upregulates: BRCA reversion mutations (43% at progression), RAD51/fork stabilization, PI3K/AKT
    - Ignored biomarkers: ABCB1 from Line 1, BRCA reversion status
    
    LINE 2→3 TRANSITION (The Blind Spot):
    - Liposomal doxorubicin and topotecan are ABCB1 substrates — same pump from Line 1
    - BRCA reversion = restored HR = gemcitabine DNA damage repaired more efficiently
    - No biomarker testing before Line 3
    
    LINE 3 (Gemcitabine/Liposomal Dox/Topotecan):
    - Response rates: 10-20%
    - No biomarker testing. No molecular stratification.
    - The end of the road.
    """,

    "data_sources": [
        "Vaidyanathan A et al. British Journal of Cancer 2016. DOI: 10.1038/bjc.2016.203",
        "Christie E et al. Nature Communications 2019. DOI: 10.1038/s41467-019-09312-9",
        "Duran G et al. British Journal of Cancer 2017. DOI: 10.1038/bjc.2017.102",
        "Leung D et al. Journal of Translational Medicine 2022. DOI: 10.1186/s12967-022-03776-y",
        "Lee D et al. Cell Death Discovery 2025. DOI: 10.1038/s41420-025-02435-7",
        "Lin K et al. Cancer Discovery 2018. DOI: 10.1158/2159-8290.cd-18-0715",
        "Lukashchuk N et al. JCO 2022. DOI: 10.1200/jco.2022.40.16_suppl.5559",
        "Tobalina L et al. Annals of Oncology 2020. DOI: 10.1016/j.annonc.2020.10.470",
        "Kim Y et al. Clinical Cancer Research 2023. DOI: 10.1158/1078-0432.ccr-22-3715",
        "Burger R et al. NEJM 2011. DOI: 10.1056/nejmoa1104390",
        "McCorkle JR et al. PLoS ONE 2021. DOI: 10.1371/journal.pone.0254205",
        "Tighe A et al. Cell Reports Medicine 2025. DOI: 10.1016/j.xcrm.2025.102160"
    ]
}


def get_critical_cross_resistance_entries() -> list:
    """Return only CRITICAL severity cross-resistance entries."""
    return [
        entry for entry in HGSOC_TREATMENT_LINES["cross_resistance_map"]
        if "CRITICAL" in entry["severity"]
    ]


def get_patient_tissue_confirmed_mechanisms() -> list:
    """Return only resistance mechanisms confirmed in patient tissue."""
    confirmed = []
    for line in HGSOC_TREATMENT_LINES["lines"]:
        for mechanism in line.get("resistance_mechanisms_induced", []):
            if mechanism.get("patient_tissue_confirmed", False):
                confirmed.append({
                    "line": line["line"],
                    "mechanism": mechanism["mechanism"],
                    "evidence": mechanism["evidence"]
                })
    return confirmed


def get_abcb1_parp_scandal() -> str:
    """Return the ABCB1-PARP inhibitor scandal narrative."""
    return HGSOC_TREATMENT_LINES["the_abcb1_parp_scandal"]
