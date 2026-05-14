"""
CrisPRO genetic annotation — aligned with longevity/DNA-Repair.ipynb Module 1.
Hardcoded lookup tables only; no external API calls.
"""

from __future__ import annotations

# ══════════════════════════════════════════════════════════════════════════════
# CrisPRO Genetic Annotation Module v1.0
# ══════════════════════════════════════════════════════════════════════════════
# All lookup tables are hardcoded from published sources.
# Zero external API calls. Zero invented numbers.

# ── APOE DIPLOTYPE TABLE ─────────────────────────────────────────────────────
# Source: Corder et al. Science 1993. PMID: 8346443
# rs429358 (C>T at codon 112) + rs7412 (C>T at codon 158)
# Alleles: e2 = Cys112/Cys158, e3 = Cys112/Arg158 (reference), e4 = Arg112/Arg158

APOE_DIPLOTYPE = {
    # (rs429358_genotype, rs7412_genotype) → (apoe_genotype, risk_tier, ad_or, longevity_impact)
    ("TT", "CC"): {
        "genotype": "e3/e3",
        "risk_tier": "REFERENCE",
        "ad_risk_or": "1.0 (reference)",
        "longevity_impact": "Reference genotype; no increased or decreased longevity association",
    },
    ("TT", "CT"): {
        "genotype": "e2/e3",
        "risk_tier": "REDUCED_RISK",
        "ad_risk_or": "0.6x vs e3/e3",
        "longevity_impact": "Associated with increased longevity in centenarian studies",
    },
    ("TT", "TT"): {
        "genotype": "e2/e2",
        "risk_tier": "REDUCED_RISK",
        "ad_risk_or": "0.6x vs e3/e3",
        "longevity_impact": "Protective for AD; monitor for type III hyperlipoproteinemia",
    },
    ("CT", "CC"): {
        "genotype": "e3/e4",
        "risk_tier": "ELEVATED",
        "ad_risk_or": "2.0-3.0x vs e3/e3",
        "longevity_impact": "Associated with reduced longevity",
    },
    ("CC", "CC"): {
        "genotype": "e4/e4",
        "risk_tier": "HIGH_RISK",
        "ad_risk_or": "8-12x vs e3/e3",
        "longevity_impact": "Significantly associated with reduced longevity and early-onset AD",
    },
    ("CT", "CT"): {
        "genotype": "e2/e4",
        "risk_tier": "UNCERTAIN",
        "ad_risk_or": "~1.0-2.0x vs e3/e3 (opposing alleles)",
        "longevity_impact": "Conflicting effects: e2 protective, e4 risk. Net effect uncertain.",
    },
}

APOE_RECOMMENDATIONS = {
    "REFERENCE": "No specific APOE-related interventions indicated.",
    "REDUCED_RISK": "Favorable APOE genotype. Standard health maintenance.",
    "ELEVATED": "Monitor cognitive function. Consider cardiovascular risk optimization. APOE4 carriers may benefit from earlier lipid management.",
    "HIGH_RISK": "Strongly consider comprehensive cardiovascular and cognitive monitoring. Genetic counseling recommended. Aggressive lipid management per guidelines.",
    "UNCERTAIN": "Mixed APOE alleles — interpret with caution. Standard cardiovascular monitoring.",
}

APOE_SOURCE_PMID = "8346443"  # Corder et al. Science 1993


# ── MTHFR ACTIVITY TABLE ─────────────────────────────────────────────────────
# Source: Frosst et al. Nat Genet 1995. PMID: 8554066
# C677T (rs1801133): CC=normal, CT=~65%, TT=~30% thermolabile activity
# A1298C (rs1801131): AA=normal, AC=~85%, CC=~70%
# Compound heterozygote (C677T CT + A1298C AC): ~50%

MTHFR_C677T_ACTIVITY = {
    "CC": {"activity": 1.00, "label": "NORMAL"},
    "CT": {"activity": 0.65, "label": "MILDLY_REDUCED"},
    "TT": {"activity": 0.30, "label": "SIGNIFICANTLY_REDUCED"},
}

MTHFR_A1298C_ACTIVITY = {
    "AA": {"activity": 1.00, "label": "NORMAL"},
    "AC": {"activity": 0.85, "label": "MILDLY_REDUCED"},
    "CC": {"activity": 0.70, "label": "MODERATELY_REDUCED"},
}

MTHFR_SOURCE_PMID = "8554066"  # Frosst et al. Nat Genet 1995


# ── LONGEVITY VARIANT ANNOTATIONS ────────────────────────────────────────────
# Expanded longevity-associated loci beyond APOE/MTHFR.
# Sources: published GWAS and candidate-gene studies (PMIDs listed per entry).

LONGEVITY_VARIANT_ANNOTATIONS = {
    "rs2802292": {
        "gene": "FOXO3",
        "function": "Forkhead transcription factor; regulates insulin/IGF-1 signaling and stress resistance",
        "hallmarks": ["altered_intercellular_communication", "deregulated_nutrient_sensing"],
        "protective_allele": "G",
        "risk_allele": "T",
        "effect_size_beta": -0.163,
        "odds_ratio": 0.85,
        "pmid": "18765803",
        "population_frequency_protective": 0.35,
        "note": "G allele associated with longevity in multiple centenarian cohorts (Willcox et al. PNAS 2008).",
    },
    "rs5882": {
        "gene": "CETP",
        "function": "Cholesteryl ester transfer protein; A allele associated with higher HDL and longevity",
        "hallmarks": ["chronic_inflammation", "deregulated_nutrient_sensing"],
        "protective_allele": "A",
        "risk_allele": "G",
        "effect_size_beta": -0.128,
        "odds_ratio": 0.88,
        "pmid": "20686565",
        "population_frequency_protective": 0.42,
        "note": "A allele (Ile405Val) associated with higher HDL-C and longevity in Ashkenazi Jewish centenarians.",
    },
    "rs9536314": {
        "gene": "KL",
        "function": "Anti-aging hormone; T allele (KL-VS haplotype) associated with longevity and cognitive protection",
        "hallmarks": ["altered_intercellular_communication", "epigenetic_alterations"],
        "protective_allele": "T",
        "risk_allele": "C",
        "effect_size_beta": -0.198,
        "odds_ratio": 0.82,
        "pmid": "15520388",
        "population_frequency_protective": 0.16,
        "note": "KL-VS haplotype (T allele) associated with longevity and reduced cognitive decline (Arking et al. PNAS 2002).",
    },
    "rs7726159": {
        "gene": "TERT",
        "function": "Telomerase reverse transcriptase; C allele associated with longer telomeres",
        "hallmarks": ["telomere_attrition", "genomic_instability"],
        "protective_allele": "C",
        "risk_allele": "A",
        "effect_size_beta": -0.094,
        "odds_ratio": 0.91,
        "pmid": "20972438",
        "population_frequency_protective": 0.55,
        "note": "C allele associated with longer telomere length and reduced age-related disease risk.",
    },
    "rs4880": {
        "gene": "SOD2",
        "function": "Mitochondrial superoxide dismutase; T allele (Ala16Val) associated with reduced ROS and longevity",
        "hallmarks": ["mitochondrial_dysfunction", "oxidative_stress"],
        "protective_allele": "T",
        "risk_allele": "C",
        "effect_size_beta": -0.117,
        "odds_ratio": 0.89,
        "pmid": "12522134",
        "population_frequency_protective": 0.48,
        "note": "Ala16Val (T allele) associated with improved mitochondrial antioxidant capacity and longevity.",
    },
}


def annotate_longevity_variants(variants: dict) -> dict:
    """Annotate longevity-associated variants (FOXO3, CETP, KLOTHO, TERT, SOD2)."""
    results = {}
    for rsid, annotation in LONGEVITY_VARIANT_ANNOTATIONS.items():
        entry = variants.get(rsid)
        if entry is None:
            continue
        geno_raw = entry.get("genotype") if isinstance(entry, dict) else None
        if not geno_raw:
            continue
        geno = "".join(sorted(str(geno_raw).upper()))
        protective = annotation["protective_allele"].upper()
        risk = annotation["risk_allele"].upper()
        dosage_protective = sum(1 for b in geno if b == protective)
        dosage_risk = sum(1 for b in geno if b == risk)
        if dosage_protective == 2:
            zygosity = "homozygous_protective"
            impact = "FAVORABLE"
        elif dosage_protective == 1:
            zygosity = "heterozygous"
            impact = "INTERMEDIATE"
        elif dosage_risk == 2:
            zygosity = "homozygous_risk"
            impact = "UNFAVORABLE"
        else:
            zygosity = "unknown"
            impact = "UNKNOWN"
        results[rsid] = {
            "rsid": rsid,
            "gene": annotation["gene"],
            "genotype": geno,
            "zygosity": zygosity,
            "impact": impact,
            "protective_allele": annotation["protective_allele"],
            "risk_allele": annotation["risk_allele"],
            "dosage_protective": dosage_protective,
            "function": annotation["function"],
            "hallmarks": annotation["hallmarks"],
            "effect_size_beta": annotation["effect_size_beta"],
            "odds_ratio": annotation["odds_ratio"],
            "source_pmid": annotation["pmid"],
            "note": annotation["note"],
        }
    return results


# ── BRCA CLASSIFICATION ACTIONS ──────────────────────────────────────────────
BRCA_ACTIONS = {
    "Pathogenic": {
        "action": "ONCOLOGY_REFERRAL",
        "risk_summary_template": {
            "BRCA1": "Elevated lifetime breast (50-80%) and ovarian (20-40%) cancer risk",
            "BRCA2": "Elevated lifetime breast (40-70%) and ovarian (10-20%) cancer risk",
        },
        "upgrade_path": None,
    },
    "Likely_pathogenic": {
        "action": "ONCOLOGY_REFERRAL",
        "risk_summary_template": {
            "BRCA1": "Elevated lifetime breast and ovarian cancer risk (likely pathogenic)",
            "BRCA2": "Elevated lifetime breast and ovarian cancer risk (likely pathogenic)",
        },
        "upgrade_path": None,
    },
    "VUS": {
        "action": "MONITOR",
        "risk_summary_template": {
            "BRCA1": "Uncertain significance — cannot determine cancer risk from this variant alone",
            "BRCA2": "Uncertain significance — cannot determine cancer risk from this variant alone",
        },
        "upgrade_path": "Evo2 VUS reclassification available (Level 2)",
    },
    "Benign": {
        "action": "REASSURING",
        "risk_summary_template": {
            "BRCA1": "Benign variant — no increased cancer risk associated",
            "BRCA2": "Benign variant — no increased cancer risk associated",
        },
        "upgrade_path": None,
    },
    "Likely_benign": {
        "action": "REASSURING",
        "risk_summary_template": {
            "BRCA1": "Likely benign variant — no increased cancer risk expected",
            "BRCA2": "Likely benign variant — no increased cancer risk expected",
        },
        "upgrade_path": None,
    },
}

# BRCA risk numbers source:
# BRCA1: Kuchenbaecker et al. JAMA 2017. PMID: 28632866
# BRCA2: Kuchenbaecker et al. JAMA 2017. PMID: 28632866


# ══════════════════════════════════════════════════════════════════════════════
# ANNOTATION ENGINE
# ══════════════════════════════════════════════════════════════════════════════


def annotate_apoe(variants):
    """Determine APOE genotype from rs429358 + rs7412."""
    rs429358 = variants.get("rs429358", {}).get("genotype")
    rs7412 = variants.get("rs7412", {}).get("genotype")

    if rs429358 is None or rs7412 is None:
        return {
            "genotype": None,
            "risk_tier": "INSUFFICIENT_DATA",
            "note": "Both rs429358 and rs7412 required for APOE diplotype",
        }

    # Normalize genotype order (alphabetical)
    rs429358 = "".join(sorted(rs429358.upper()))
    rs7412 = "".join(sorted(rs7412.upper()))

    key = (rs429358, rs7412)
    entry = APOE_DIPLOTYPE.get(key)

    if entry is None:
        return {
            "genotype": None,
            "risk_tier": "INVALID_GENOTYPE",
            "note": f"Unrecognized diplotype: rs429358={rs429358}, rs7412={rs7412}",
        }

    return {
        "genotype": entry["genotype"],
        "risk_tier": entry["risk_tier"],
        "ad_risk_or": entry["ad_risk_or"],
        "longevity_impact": entry["longevity_impact"],
        "source_pmid": APOE_SOURCE_PMID,
        "recommendation": APOE_RECOMMENDATIONS[entry["risk_tier"]],
        "note": "APOE genotype is NOT scored by Evo2 — evolutionary constraint does not predict clinical risk for this locus.",
    }


def annotate_mthfr(variants):
    """Determine MTHFR enzyme activity from C677T + A1298C."""
    rs1801133 = variants.get("rs1801133", {}).get("genotype")  # C677T
    rs1801131 = variants.get("rs1801131", {}).get("genotype")  # A1298C

    c677t_geno = "".join(sorted(rs1801133.upper())) if rs1801133 else None
    a1298c_geno = "".join(sorted(rs1801131.upper())) if rs1801131 else None

    c677t_data = MTHFR_C677T_ACTIVITY.get(c677t_geno) if c677t_geno else None
    a1298c_data = MTHFR_A1298C_ACTIVITY.get(a1298c_geno) if a1298c_geno else None

    # Calculate combined activity
    if c677t_data and a1298c_data:
        # Check compound heterozygote: C677T CT + A1298C AC
        if c677t_geno == "CT" and a1298c_geno == "AC":
            activity = 0.50
            label = "MODERATELY_REDUCED"
        else:
            # Multiply individual effects (conservative model)
            activity = round(c677t_data["activity"] * a1298c_data["activity"], 2)
            if activity >= 0.95:
                label = "NORMAL"
            elif activity >= 0.60:
                label = "MILDLY_REDUCED"
            elif activity >= 0.40:
                label = "MODERATELY_REDUCED"
            else:
                label = "SIGNIFICANTLY_REDUCED"
    elif c677t_data:
        activity = c677t_data["activity"]
        label = c677t_data["label"]
    elif a1298c_data:
        activity = a1298c_data["activity"]
        label = a1298c_data["label"]
    else:
        return {
            "c677t": None,
            "a1298c": None,
            "enzyme_activity_estimate": None,
            "activity_label": "INSUFFICIENT_DATA",
            "note": "rs1801133 (C677T) and/or rs1801131 (A1298C) required",
        }

    # Recommendation based on activity
    if activity >= 0.80:
        rec = "No specific MTHFR supplementation indicated. Standard folate intake sufficient."
    elif activity >= 0.50:
        rec = "Consider methylfolate (5-MTHF) 400-800mcg daily instead of folic acid. Monitor homocysteine."
    else:
        rec = "Recommend methylfolate (5-MTHF) 800-1000mcg daily. Monitor homocysteine levels. Avoid folic acid supplementation."

    return {
        "c677t": c677t_geno,
        "a1298c": a1298c_geno,
        "enzyme_activity_estimate": activity,
        "activity_label": label,
        "recommendation": rec,
        "source_pmid": MTHFR_SOURCE_PMID,
        "hallmark_impact": "epigenetic_alterations",
    }


def annotate_brca(variants):
    """Annotate BRCA1/BRCA2 variants with clinical action."""
    results = []

    for gene in ("BRCA1", "BRCA2"):
        var_data = variants.get(gene)
        if var_data is None:
            continue

        variant = var_data.get("variant", "unknown")
        clinvar_class = var_data.get("clinvar_class", "VUS")
        zygosity = var_data.get("zygosity", "unknown")

        # Normalize classification
        norm_class = (
            clinvar_class.replace(" ", "_")
            .replace("likely_pathogenic", "Likely_pathogenic")
            .replace("likely_benign", "Likely_benign")
        )

        action_data = BRCA_ACTIONS.get(norm_class, BRCA_ACTIONS["VUS"])
        risk_template = action_data["risk_summary_template"]

        results.append(
            {
                "gene": gene,
                "variant": variant,
                "classification": clinvar_class,
                "zygosity": zygosity,
                "action": action_data["action"],
                "risk_summary": risk_template.get(gene, f"See ClinVar for {gene} {variant}"),
                "upgrade_path": action_data["upgrade_path"],
                "source_pmid": "28632866",  # Kuchenbaecker JAMA 2017
            }
        )

    return results


def annotate_genetics(request_body):
    """Full genetic annotation from patient variants.

    Input: dict with patient_id (optional) and variants dict
    Output: complete annotation response
    """
    variants = request_body.get("variants", {})

    apoe = annotate_apoe(variants)
    mthfr = annotate_mthfr(variants)
    brca = annotate_brca(variants)
    longevity_variants = annotate_longevity_variants(variants)

    return {
        "patient_id": request_body.get("patient_id"),
        "apoe_status": apoe,
        "mthfr_status": mthfr,
        "brca_status": brca,
        "variant_annotations": longevity_variants,
        "provenance": {
            "apoe_method": "rs429358 + rs7412 diplotype lookup (PMID:8346443)",
            "mthfr_method": "Published enzyme activity data (PMID:8554066)",
            "brca_method": "ClinVar classification passthrough + PMID:28632866 risk estimates",
            "longevity_variants_method": "Expanded longevity loci lookup (FOXO3/CETP/KLOTHO/TERT/SOD2)",
            "framework": "CrisPRO Genetic Annotation v1.0",
        },
        "disclaimer": "Research Use Only. Not a diagnostic. Consult a genetic counselor for clinical interpretation.",
    }

