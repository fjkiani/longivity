"""
Colorectal Cancer (mCRC) Treatment Line Panel
Treatment-Line-Integration Module

Evidence-based resistance cascade data for Metastatic Colorectal Cancer.
All resistance mechanisms sourced from published peer-reviewed literature.
Patient tissue confirmation noted where available — this is the gold standard.

References embedded inline with DOI.
"""

MCRC_TREATMENT_LINES = {
    "cancer_type": "Metastatic Colorectal Cancer (mCRC)",
    "icd10": "C18-C20",
    "staging_note": "Lines 1-3 apply to Stage IV (metastatic) disease. Adjuvant FOLFOX is also used in Stage III.",
    "molecular_subtypes": {
        "RAS_WT_BRAF_WT": "Eligible for EGFR inhibitors (cetuximab/panitumumab)",
        "RAS_mutant": "NOT eligible for EGFR inhibitors (~45% of mCRC)",
        "BRAF_V600E": "Encorafenib + cetuximab preferred in Line 2+",
        "MSI_H": "Pembrolizumab first-line preferred",
        "HER2_amplified": "Trastuzumab + pertuzumab or tucatinib options"
    },

    "lines": [
        {
            "line": 1,
            "name": "FOLFOX ± Targeted Agent",
            "regimens": [
                {
                    "name": "FOLFOX + Bevacizumab",
                    "drugs": ["Oxaliplatin (85 mg/m²)", "Leucovorin (400 mg/m²)", "5-FU bolus (400 mg/m²)", "5-FU infusion (2400 mg/m² over 46h)", "Bevacizumab (5 mg/kg)"],
                    "schedule": "Q2W",
                    "indication": "RAS mutant or RAS WT left-sided (bevacizumab preferred over cetuximab for right-sided)"
                },
                {
                    "name": "FOLFOX + Cetuximab",
                    "drugs": ["Oxaliplatin (85 mg/m²)", "Leucovorin (400 mg/m²)", "5-FU bolus (400 mg/m²)", "5-FU infusion (2400 mg/m² over 46h)", "Cetuximab (400 mg/m² loading, then 250 mg/m²)"],
                    "schedule": "Q2W",
                    "indication": "RAS WT / BRAF WT left-sided tumors",
                    "biomarker_required": "RAS/BRAF wild-type"
                },
                {
                    "name": "FOLFOXIRI + Bevacizumab",
                    "drugs": ["Oxaliplatin (85 mg/m²)", "Irinotecan (165 mg/m²)", "Leucovorin (200 mg/m²)", "5-FU infusion (3200 mg/m² over 48h)", "Bevacizumab (5 mg/kg)"],
                    "schedule": "Q2W",
                    "indication": "Fit patients, high tumor burden, BRAF V600E"
                }
            ],
            "biomarkers_required": [
                {
                    "marker": "RAS (KRAS/NRAS) mutation status",
                    "purpose": "Determines eligibility for EGFR inhibitors",
                    "tested": True
                },
                {
                    "marker": "BRAF V600E mutation",
                    "purpose": "Prognostic; determines FOLFOXIRI eligibility",
                    "tested": True
                },
                {
                    "marker": "MSI/MMR status",
                    "purpose": "MSI-H → pembrolizumab first-line",
                    "tested": True
                }
            ],
            "biomarkers_ignored": [
                {
                    "marker": "ZEB2 expression",
                    "why_matters": "ZEB2 is an independent prognostic marker of reduced OS and DFS in patients receiving adjuvant FOLFOX. ZEB2-driven EMT activates ERCC1 and ERCC4, making oxaliplatin useless. ZEB2 expression retained in 96% of liver metastases.",
                    "evidence": "Sreekumar R et al. Molecular Oncology 2021. DOI: 10.1002/1878-0261.12965",
                    "evidence_type": "PATIENT TISSUE — primary tumors and matched liver metastases"
                },
                {
                    "marker": "ERCC1 expression",
                    "why_matters": "ERCC1 overexpression predicts oxaliplatin resistance. ERCC1 protein levels are significantly higher in FOLFOX-treated patients vs untreated patients (confirmed in patient tumor tissue). ERCC1 is an independent predictor of FOLFOX/XELOX resistance.",
                    "evidence": "Baba H et al. British Journal of Cancer 2012. DOI: 10.1038/bjc.2012.502; Bogomolova IA et al. 2023",
                    "evidence_type": "PATIENT TISSUE — hepatic resection specimens"
                },
                {
                    "marker": "DPD (DPYD) expression",
                    "why_matters": "DPD degrades 5-FU. DPD protein levels are significantly higher in FOLFOX-treated patients vs untreated. FOLFIRI (Line 2) still contains 5-FU — the same drug DPD already learned to destroy.",
                    "evidence": "Baba H et al. British Journal of Cancer 2012. DOI: 10.1038/bjc.2012.502",
                    "evidence_type": "PATIENT TISSUE — hepatic resection specimens"
                }
            ],
            "resistance_mechanisms_induced": [
                {
                    "mechanism": "ZEB2-ERCC1 axis activation",
                    "pathway": "Oxaliplatin pressure → ZEB2 selection → ERCC1/ERCC4 upregulation → NER pathway activation",
                    "consequence": "Tumor repairs oxaliplatin-induced DNA damage; oxaliplatin becomes ineffective",
                    "cross_resistance_to": ["Continued oxaliplatin", "Cisplatin"],
                    "evidence": "Sreekumar R et al. Molecular Oncology 2021. DOI: 10.1002/1878-0261.12965",
                    "patient_tissue_confirmed": True
                },
                {
                    "mechanism": "Slug/AKT/GSK3β-ERCC1 axis",
                    "pathway": "Oxaliplatin → AKT/GSK3β activation → Slug overexpression → ERCC1 upregulation + EMT",
                    "consequence": "EMT + oxaliplatin resistance; Slug-ERCC1 co-expression confirmed in CRC patients",
                    "cross_resistance_to": ["Oxaliplatin", "Cisplatin"],
                    "evidence": "Wei W et al. Oncology Research 2020. DOI: 10.3727/096504020x15877284857868",
                    "patient_tissue_confirmed": True
                },
                {
                    "mechanism": "DPD upregulation",
                    "pathway": "5-FU exposure → DPD selection → 5-FU degradation",
                    "consequence": "5-FU is degraded before it can act; FOLFIRI (Line 2) still contains 5-FU",
                    "cross_resistance_to": ["5-FU in FOLFIRI (Line 2)", "Capecitabine", "TAS-102 (partial)"],
                    "evidence": "Baba H et al. British Journal of Cancer 2012. DOI: 10.1038/bjc.2012.502",
                    "patient_tissue_confirmed": True
                },
                {
                    "mechanism": "Thymidylate synthase (TYMS) upregulation",
                    "pathway": "5-FU exposure → TYMS overexpression → reduced 5-FU efficacy",
                    "consequence": "5-FU target enzyme is overexpressed; drug cannot inhibit it effectively",
                    "cross_resistance_to": ["5-FU in FOLFIRI (Line 2)", "Pemetrexed"],
                    "evidence": "Escalante P et al. Pharmaceutics 2021. DOI: 10.3390/pharmaceutics13010075",
                    "patient_tissue_confirmed": False
                },
                {
                    "mechanism": "PD-L1 upregulation (adaptive immune resistance)",
                    "pathway": "FOLFOX → PD-1+ CD8 T cell infiltration → IFN-γ → PD-L1 on tumor cells",
                    "consequence": "Immunosuppressive microenvironment; subsequent immunotherapy less effective",
                    "cross_resistance_to": ["Checkpoint inhibitors"],
                    "evidence": "Dosset M et al. Oncoimmunology 2018. DOI: 10.1080/2162402x.2018.1433981",
                    "patient_tissue_confirmed": True
                },
                {
                    "mechanism": "Bevacizumab-driven invasion escape",
                    "pathway": "Bevacizumab → VEGF blockade → tumor hypoxia → autocrine VEGF-A/B/C upregulation → VEGFR-1 phosphorylation → increased migration/invasion",
                    "consequence": "Bevacizumab-adapted cells are MORE migratory, MORE invasive, and MORE metastatic in vivo",
                    "cross_resistance_to": ["Continued bevacizumab", "Ramucirumab"],
                    "evidence": "Fan F et al. British Journal of Cancer 2011. DOI: 10.1038/bjc.2011.81",
                    "patient_tissue_confirmed": False
                }
            ]
        },
        {
            "line": 2,
            "name": "FOLFIRI ± Targeted Agent",
            "regimens": [
                {
                    "name": "FOLFIRI + Bevacizumab",
                    "drugs": ["Irinotecan (180 mg/m²)", "Leucovorin (400 mg/m²)", "5-FU bolus (400 mg/m²)", "5-FU infusion (2400 mg/m² over 46h)", "Bevacizumab (5 mg/kg)"],
                    "schedule": "Q2W",
                    "note": "Bevacizumab continuation beyond progression (VELOUR/ML18147 data)"
                },
                {
                    "name": "FOLFIRI + Cetuximab",
                    "drugs": ["Irinotecan (180 mg/m²)", "Leucovorin (400 mg/m²)", "5-FU bolus (400 mg/m²)", "5-FU infusion (2400 mg/m² over 46h)", "Cetuximab (400 mg/m² loading, then 250 mg/m²)"],
                    "schedule": "Q2W",
                    "biomarker_required": "RAS WT / BRAF WT"
                },
                {
                    "name": "FOLFIRI + Aflibercept",
                    "drugs": ["Irinotecan (180 mg/m²)", "Leucovorin (400 mg/m²)", "5-FU bolus (400 mg/m²)", "5-FU infusion (2400 mg/m² over 46h)", "Aflibercept (4 mg/kg)"],
                    "schedule": "Q2W"
                }
            ],
            "biomarkers_required": [
                {
                    "marker": "RAS/BRAF status",
                    "purpose": "Determines cetuximab eligibility",
                    "tested": True
                }
            ],
            "biomarkers_ignored": [
                {
                    "marker": "ABCG2 expression",
                    "why_matters": "Irinotecan resistance drives ABCG2 overexpression confirmed in patient hepatic metastases post-irinotecan. ABCG2 is not measured before starting FOLFIRI.",
                    "evidence": "Candeil L et al. International Journal of Cancer 2004. DOI: 10.1002/ijc.20032",
                    "evidence_type": "PATIENT TISSUE — hepatic metastases"
                },
                {
                    "marker": "DPD status from Line 1",
                    "why_matters": "FOLFIRI still contains 5-FU. DPD was upregulated by Line 1 FOLFOX. The tumor already learned to destroy 5-FU. FOLFIRI is giving the patient the same drug the tumor already defeated.",
                    "evidence": "Baba H et al. British Journal of Cancer 2012. DOI: 10.1038/bjc.2012.502",
                    "evidence_type": "PATIENT TISSUE"
                },
                {
                    "marker": "Twist1 / EMT status",
                    "why_matters": "Irinotecan resistance selects for Twist1-driven EMT with MMP2 upregulation. EMT-high tumors are more invasive and less responsive to subsequent targeted therapies.",
                    "evidence": "Yang Y et al. International Journal of Oncology 2017. DOI: 10.3892/ijo.2017.4044",
                    "evidence_type": "Cell line"
                }
            ],
            "resistance_mechanisms_induced": [
                {
                    "mechanism": "ABCG2 overexpression",
                    "pathway": "SN-38 (active irinotecan metabolite) exposure → ABCG2 selection → SN-38 efflux",
                    "consequence": "Irinotecan/SN-38 is effluxed; confirmed in patient hepatic metastases",
                    "cross_resistance_to": ["Continued irinotecan", "Topotecan (Line 3)", "Mitoxantrone"],
                    "evidence": "Candeil L et al. International Journal of Cancer 2004. DOI: 10.1002/ijc.20032",
                    "patient_tissue_confirmed": True
                },
                {
                    "mechanism": "Twist1-driven EMT + MMP2 upregulation",
                    "pathway": "Irinotecan → Twist1 overexpression → EMT + CD44 upregulation + MMP2 → invasion",
                    "consequence": "Cancer stem cell-like phenotype, enhanced invasion, irinotecan resistance",
                    "cross_resistance_to": ["Continued irinotecan", "Regorafenib (partial)"],
                    "evidence": "Yang Y et al. International Journal of Oncology 2017. DOI: 10.3892/ijo.2017.4044",
                    "patient_tissue_confirmed": False
                },
                {
                    "mechanism": "Topoisomerase I (TOP1) degradation",
                    "pathway": "Irinotecan → DNA-PK activation → TOP1 phosphorylation → BRCA1-BARD1 ubiquitination → TOP1 proteasomal degradation",
                    "consequence": "The drug target itself is destroyed; irinotecan has nothing to inhibit",
                    "cross_resistance_to": ["Continued irinotecan", "Topotecan"],
                    "evidence": "Ando K et al. JCO 2025. DOI: 10.1200/jco.2025.43.4_suppl.217",
                    "patient_tissue_confirmed": True
                },
                {
                    "mechanism": "Wnt signaling activation + cancer stem cell enrichment",
                    "pathway": "Irinotecan → Wnt pathway activation → MARCKSL1+ stem cell cluster maintenance",
                    "consequence": "Treatment-resistant stem cell subpopulation drives relapse",
                    "cross_resistance_to": ["All subsequent cytotoxic agents"],
                    "evidence": "Pan Y et al. Cancer Medicine 2026. DOI: 10.1002/cam4.71550",
                    "patient_tissue_confirmed": True
                },
                {
                    "mechanism": "ABCB1 + ABCG2 combined efflux (irinotecan-resistant cells)",
                    "pathway": "Chronic irinotecan exposure → upregulation of both ABCB1 and ABCG2",
                    "consequence": "Multidrug resistant phenotype; efflux of multiple Line 3 agents",
                    "cross_resistance_to": ["Liposomal doxorubicin", "Topotecan", "Mitoxantrone"],
                    "evidence": "Dilber T et al. FEBS Letters 2025. DOI: 10.1002/1873-3468.70208",
                    "patient_tissue_confirmed": False
                }
            ]
        },
        {
            "line": 3,
            "name": "Regorafenib or TAS-102",
            "regimens": [
                {
                    "name": "Regorafenib",
                    "drugs": ["Regorafenib (160 mg daily)"],
                    "schedule": "Days 1-21 of 28-day cycle",
                    "mechanism": "Multi-kinase inhibitor: VEGFR1-3, TIE2, PDGFR, FGFR, KIT, RET, RAF",
                    "response_rate": "~10% ORR (CORRECT trial)",
                    "os_benefit": "1.4 months median OS benefit over placebo"
                },
                {
                    "name": "TAS-102 (Trifluridine/Tipiracil)",
                    "drugs": ["Trifluridine 35 mg/m² + Tipiracil 8.19 mg/m²"],
                    "schedule": "BID Days 1-5 and 8-12 of 28-day cycle",
                    "mechanism": "Thymidine-based nucleoside analog; tipiracil inhibits thymidine phosphorylase",
                    "response_rate": "~2% ORR (RECOURSE trial)",
                    "os_benefit": "1.8 months median OS benefit over placebo"
                }
            ],
            "biomarkers_required": [],
            "biomarkers_ignored": [
                {
                    "marker": "Everything",
                    "why_matters": "No biomarker testing is required or recommended before Line 3 in mCRC. The tumor has been through two lines of chemotherapy that have systematically upregulated every resistance pathway. No molecular stratification is performed.",
                    "evidence": "NCCN Guidelines mCRC v2024",
                    "evidence_type": "Clinical guideline"
                }
            ],
            "resistance_mechanisms_induced": [
                {
                    "mechanism": "RAS/RAF/MEK/ERK pathway reactivation",
                    "pathway": "Regorafenib → RAF inhibition → paradoxical RAS/RAF reactivation in RAS-mutant tumors",
                    "consequence": "Regorafenib resistance in RAS-mutant mCRC (~45% of patients)",
                    "cross_resistance_to": ["Other RAF inhibitors"],
                    "evidence": "Ramzy G et al. Cancers 2022. DOI: 10.3390/cancers14194812",
                    "patient_tissue_confirmed": False
                }
            ],
            "clinical_reality": {
                "response_rate_regorafenib": "~10% ORR",
                "response_rate_tas102": "~2% ORR",
                "median_os_regorafenib": "6.4 months (CORRECT trial)",
                "median_os_tas102": "7.1 months (RECOURSE trial)",
                "comment": "These are the drugs given to patients after two lines of chemotherapy have systematically upregulated every resistance pathway. The 1-2 month OS benefit represents the end of the road for a system that never interrogated the molecular damage it was inflicting."
            }
        }
    ],

    "cross_resistance_map": [
        {
            "from_drug": "FOLFOX / Oxaliplatin (Line 1)",
            "mechanism": "ZEB2-ERCC1 axis activation",
            "blind_to": "Continued oxaliplatin",
            "evidence": "Sreekumar R et al. Molecular Oncology 2021. DOI: 10.1002/1878-0261.12965",
            "severity": "HIGH — confirmed in patient tissue",
            "patient_tissue": True
        },
        {
            "from_drug": "5-FU (Line 1 FOLFOX)",
            "mechanism": "DPD upregulation",
            "blind_to": "5-FU in FOLFIRI (Line 2)",
            "evidence": "Baba H et al. British Journal of Cancer 2012. DOI: 10.1038/bjc.2012.502",
            "severity": "HIGH — confirmed in patient tissue. FOLFIRI still contains 5-FU.",
            "patient_tissue": True
        },
        {
            "from_drug": "Irinotecan (Line 2 FOLFIRI)",
            "mechanism": "ABCG2 overexpression",
            "blind_to": "Topotecan (if used in Line 3)",
            "evidence": "Candeil L et al. International Journal of Cancer 2004. DOI: 10.1002/ijc.20032",
            "severity": "HIGH — confirmed in patient hepatic metastases",
            "patient_tissue": True
        },
        {
            "from_drug": "Bevacizumab (Lines 1-2)",
            "mechanism": "Autocrine VEGF loop upregulation → invasion",
            "blind_to": "Regorafenib (targets VEGFR but not autocrine VEGF loops)",
            "evidence": "Fan F et al. British Journal of Cancer 2011. DOI: 10.1038/bjc.2011.81",
            "severity": "MODERATE",
            "patient_tissue": False
        },
        {
            "from_drug": "FOLFOX (Line 1)",
            "mechanism": "PD-L1 upregulation",
            "blind_to": "Checkpoint inhibitors (if used in MSS tumors)",
            "evidence": "Dosset M et al. Oncoimmunology 2018. DOI: 10.1080/2162402x.2018.1433981",
            "severity": "MODERATE — relevant for MSS tumors considering immunotherapy",
            "patient_tissue": True
        }
    ],

    "the_5fu_scandal": """
    THE 5-FU SCANDAL IN mCRC
    ========================
    
    5-FU is present in BOTH FOLFOX (Line 1) AND FOLFIRI (Line 2).
    
    FOLFOX selects for:
    - DPD overexpression (degrades 5-FU) — confirmed in patient tissue (Baba 2012)
    - TYMS overexpression (5-FU target enzyme) — confirmed in cell lines
    
    FOLFIRI then gives the patient 5-FU again.
    
    The tumor has already been selected for resistance to 5-FU.
    The second line is giving the patient the same drug the tumor already defeated,
    just paired with a different partner (irinotecan instead of oxaliplatin).
    
    This is not a treatment strategy. It is a billing strategy.
    """,

    "key_insight": """
    mCRC RESISTANCE CASCADE SUMMARY
    ================================
    
    LINE 1 (FOLFOX):
    - Upregulates: ZEB2-ERCC1 (repairs oxaliplatin damage), DPD (destroys 5-FU), TYMS, PD-L1
    - Ignored biomarkers: ZEB2, ERCC1, DPD baseline
    
    LINE 1→2 TRANSITION (The Blind Spot):
    - FOLFIRI still contains 5-FU — DPD already upregulated by Line 1
    - ERCC1 upregulation is irrelevant to irinotecan (different mechanism)
    - But DPD upregulation directly undermines the 5-FU component of FOLFIRI
    
    LINE 2 (FOLFIRI):
    - Upregulates: ABCG2 (effluxes SN-38), Twist1/EMT/MMP2, TOP1 degradation, Wnt/CSC
    - Ignored biomarkers: ABCG2, DPD from Line 1, Twist1/EMT
    
    LINE 2→3 TRANSITION (The Blind Spot):
    - Regorafenib targets VEGFR/RAF/KIT — does not address ABCG2, Twist1, Wnt, or TOP1 loss
    - TAS-102 is a thymidine analog — faces DPD-mediated degradation selected for by Line 1
    
    LINE 3 (Regorafenib/TAS-102):
    - ORR: 2-10%. OS benefit: 1-2 months.
    - No biomarker testing required. No molecular stratification.
    - The end of the road for a system that never interrogated the molecular damage it caused.
    """,

    "data_sources": [
        "Sreekumar R et al. Molecular Oncology 2021. DOI: 10.1002/1878-0261.12965",
        "Baba H et al. British Journal of Cancer 2012. DOI: 10.1038/bjc.2012.502",
        "Wei W et al. Oncology Research 2020. DOI: 10.3727/096504020x15877284857868",
        "Dosset M et al. Oncoimmunology 2018. DOI: 10.1080/2162402x.2018.1433981",
        "Candeil L et al. International Journal of Cancer 2004. DOI: 10.1002/ijc.20032",
        "Yang Y et al. International Journal of Oncology 2017. DOI: 10.3892/ijo.2017.4044",
        "Napolitano S et al. Clinical Cancer Research 2023. DOI: 10.1158/1078-0432.ccr-22-3894",
        "Fan F et al. British Journal of Cancer 2011. DOI: 10.1038/bjc.2011.81",
        "Tomida C et al. International Journal of Oncology 2018. DOI: 10.3892/ijo.2018.4291",
        "Escalante P et al. Pharmaceutics 2021. DOI: 10.3390/pharmaceutics13010075",
        "Pan Y et al. Cancer Medicine 2026. DOI: 10.1002/cam4.71550",
        "Dilber T et al. FEBS Letters 2025. DOI: 10.1002/1873-3468.70208",
        "Ando K et al. JCO 2025. DOI: 10.1200/jco.2025.43.4_suppl.217"
    ]
}


def get_line_data(line_number: int) -> dict:
    """Return treatment line data for a given line number (1, 2, or 3)."""
    for line in MCRC_TREATMENT_LINES["lines"]:
        if line["line"] == line_number:
            return line
    raise ValueError(f"Line {line_number} not found in mCRC panel")


def get_patient_tissue_confirmed_mechanisms() -> list:
    """Return only resistance mechanisms confirmed in patient tissue."""
    confirmed = []
    for line in MCRC_TREATMENT_LINES["lines"]:
        for mechanism in line.get("resistance_mechanisms_induced", []):
            if mechanism.get("patient_tissue_confirmed", False):
                confirmed.append({
                    "line": line["line"],
                    "mechanism": mechanism["mechanism"],
                    "evidence": mechanism["evidence"]
                })
    return confirmed


def get_cross_resistance_summary() -> str:
    """Return a summary of all cross-resistance relationships."""
    lines = []
    for entry in MCRC_TREATMENT_LINES["cross_resistance_map"]:
        pt = " [PATIENT TISSUE CONFIRMED]" if entry.get("patient_tissue") else ""
        lines.append(f"  {entry['from_drug']} → {entry['blind_to']}: {entry['severity']}{pt}")
    return "mCRC Cross-Resistance Map:\n" + "\n".join(lines)
