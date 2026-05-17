import Link from "next/link";
import BenchmarkPanel from "@/components/demo/BenchmarkPanel";

export const metadata = {
  title: "How It Works — Longivity",
  description: "The six transformations that convert fragmented biomarker inputs into one ranked clinical action. Training sources, benchmark accuracy, and honest limitations.",
};

export default function HowItWorksPage() {
  return (
    <div className="bg-white text-gray-900">

      {/* Hero */}
      <section className="pt-36 pb-16 px-6 text-center">
        <div className="max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-gray-100 border border-gray-200 text-gray-600 text-sm font-bold mb-8">
            Technical Reference · Source-Verified
          </div>
          <h1 className="text-4xl md:text-6xl font-black text-gray-900 leading-tight mb-6 tracking-tight">
            How Longivity Works
          </h1>
          <p className="text-xl text-gray-600 font-medium leading-relaxed">
            Three inputs. Six transformations. One ranked action. Every step is deterministic, auditable, and grounded in published science. This page decodes the actual machine.
          </p>
        </div>
      </section>

      {/* Section 1: The Three Inputs */}
      <section className="py-16 px-6 bg-gray-50 border-y border-gray-100">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-black text-gray-900 mb-3 tracking-tight">The Three Inputs</h2>
          <p className="text-gray-500 font-medium mb-10">What you send to the API. What each field actually does.</p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

            {/* Biomarkers */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center mb-4">
                <svg className="w-5 h-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
              </div>
              <h3 className="font-black text-gray-900 mb-2">biomarkers: {"{}"}</h3>
              <p className="text-sm text-gray-600 leading-relaxed mb-4">
                Key-value pairs. Any unit format. 20+ aliases per marker handled automatically.
              </p>
              <div className="space-y-2">
                <div>
                  <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">9 PhenoAge-Required</p>
                  <div className="flex flex-wrap gap-1">
                    {["albumin", "creatinine", "glucose", "CRP", "lymphocyte%", "MCV", "RDW", "alk phos", "WBC"].map((m) => (
                      <span key={m} className="text-[10px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200 px-1.5 py-0.5 rounded">{m}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Supplementary (scored separately)</p>
                  <div className="flex flex-wrap gap-1">
                    {["IL-6", "DHEA-S", "vitamin D", "HbA1c", "fasting insulin", "Lp(a)", "cystatin C", "homocysteine", "ferritin"].map((m) => (
                      <span key={m} className="text-[10px] font-mono bg-gray-50 text-gray-600 border border-gray-200 px-1.5 py-0.5 rounded">{m}</span>
                    ))}
                  </div>
                </div>
              </div>
              <div className="mt-4 bg-gray-50 rounded-xl p-3 font-mono text-xs border border-gray-100">
                <div className="text-gray-400">// Unit aliases handled:</div>
                <div className="text-gray-700">albumin: 4.5 <span className="text-gray-400">// g/dL → g/L ×10</span></div>
                <div className="text-gray-700">glucose_mg_dl: 95 <span className="text-gray-400">// ÷18.018</span></div>
                <div className="text-gray-700">crp_mg_l: 1.2 <span className="text-gray-400">// → ln(mg/dL)</span></div>
              </div>
            </div>

            {/* Variants */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <div className="w-10 h-10 rounded-xl bg-violet-50 flex items-center justify-center mb-4">
                <svg className="w-5 h-5 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />
                </svg>
              </div>
              <h3 className="font-black text-gray-900 mb-2">variants: {"{}"}</h3>
              <p className="text-sm text-gray-600 leading-relaxed mb-4">
                SNP genotypes by rsID. Hardcoded lookup tables only — no external API calls.
              </p>
              <div className="space-y-2 text-xs">
                <div className="flex items-start gap-2">
                  <span className="text-violet-500 font-bold shrink-0">·</span>
                  <span><strong>APOE</strong> — rs429358 + rs7412 → diplotype (e2/e2 through e4/e4). Source: PMID 8346443</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-violet-500 font-bold shrink-0">·</span>
                  <span><strong>MTHFR</strong> — rs1801133 (C677T) + rs1801131 (A1298C) → enzyme activity. Source: PMID 8554066</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-violet-500 font-bold shrink-0">·</span>
                  <span><strong>Longevity loci</strong> — FOXO3, CETP, KLOTHO, TERT, SOD2 (5 rsIDs)</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-violet-500 font-bold shrink-0">·</span>
                  <span><strong>BRCA1/BRCA2</strong> — ClinVar classification passthrough. Source: PMID 28632866</span>
                </div>
              </div>
              <div className="mt-4 bg-gray-50 rounded-xl p-3 font-mono text-xs border border-gray-100">
                <div className="text-gray-700">rs429358: {"{"} genotype: <span className="text-violet-600">&quot;CC&quot;</span> {"}"}</div>
                <div className="text-gray-700">rs7412: {"{"} genotype: <span className="text-violet-600">&quot;CC&quot;</span> {"}"}</div>
                <div className="text-gray-400 mt-1">// → APOE e4/e4 · HIGH_RISK</div>
              </div>
            </div>

            {/* Compound queries */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <div className="w-10 h-10 rounded-xl bg-sky-50 flex items-center justify-center mb-4">
                <svg className="w-5 h-5 text-sky-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <h3 className="font-black text-gray-900 mb-2">compound_queries: []</h3>
              <p className="text-sm text-gray-600 leading-relaxed mb-4">
                Optional list of compound IDs to evaluate. If omitted, all compounds in the registry are scored against active hallmarks.
              </p>
              <div className="space-y-2 text-xs">
                <div className="flex items-start gap-2">
                  <span className="text-emerald-500 font-bold shrink-0">MR</span>
                  <span><strong>MR_VALIDATED</strong> — omega_3, vitamin_d3, folate, metformin. Causal evidence for aging clock endpoint.</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-blue-500 font-bold shrink-0">RCT</span>
                  <span><strong>RCT</strong> — berberine, NMN, NR, NAC, quercetin, urolithin_a, zinc, vitamin_k2, and others.</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-gray-400 font-bold shrink-0">OBS</span>
                  <span><strong>OBSERVATIONAL</strong> — rapamycin, resveratrol, spermidine, and others.</span>
                </div>
              </div>
              <div className="mt-4 bg-gray-50 rounded-xl p-3 font-mono text-xs border border-gray-100">
                <div className="text-gray-700">[<span className="text-sky-600">&quot;omega_3&quot;</span>, <span className="text-sky-600">&quot;berberine&quot;</span>]</div>
                <div className="text-gray-400 mt-1">// or omit → score all</div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* Section 2: Six Transformations */}
      <section id="transformations" className="py-16 px-6 bg-white">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-black text-gray-900 mb-3 tracking-tight">Six Transformations</h2>
          <p className="text-gray-500 font-medium mb-10">Sequential operations. Each one deterministic. Each one auditable. The actual formula is shown.</p>

          <div className="space-y-4">

            {/* 1 */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <div className="flex items-start gap-5">
                <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center shrink-0 font-black text-gray-600">1</div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-black text-gray-900">Normalize</h3>
                    <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Input → Canonical Units</span>
                  </div>
                  <p className="text-sm text-gray-600 leading-relaxed mb-3">
                    <code className="text-xs bg-gray-100 px-1.5 py-0.5 rounded font-mono">extract_phenoage_marker_values()</code> in <code className="text-xs bg-gray-100 px-1.5 py-0.5 rounded font-mono">longevity_phenoage_level0.py</code>. Resolves 20+ key aliases per marker. Converts units with explicit notes logged in the response. Out-of-range values are flagged but still used — never silently rejected.
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono">
                    <div className="bg-gray-50 rounded-xl p-3 border border-gray-100">
                      <div className="text-gray-400 mb-1">albumin g/dL → g/L</div>
                      <div className="text-gray-700">4.5 × 10 = <span className="text-emerald-600 font-bold">45.0</span></div>
                    </div>
                    <div className="bg-gray-50 rounded-xl p-3 border border-gray-100">
                      <div className="text-gray-400 mb-1">glucose mg/dL → mmol/L</div>
                      <div className="text-gray-700">95 ÷ 18.018 = <span className="text-emerald-600 font-bold">5.27</span></div>
                    </div>
                    <div className="bg-gray-50 rounded-xl p-3 border border-gray-100">
                      <div className="text-gray-400 mb-1">CRP mg/L → ln(mg/dL)</div>
                      <div className="text-gray-700">1.2 → 0.12 → <span className="text-emerald-600 font-bold">ln(0.12)</span></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* 2 */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <div className="flex items-start gap-5">
                <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center shrink-0 font-black text-emerald-600">2</div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-black text-gray-900">Score</h3>
                    <span className="text-xs font-bold text-emerald-600 uppercase tracking-wider">PhenoAge Gompertz Model · PMID 29676998</span>
                  </div>
                  <p className="text-sm text-gray-600 leading-relaxed mb-3">
                    Levine 2018 Gompertz proportional hazards model. Validated in NHANES III (n=11,432) and NHANES IV (n=6,209). Predicts all-cause mortality HR=1.08 per year of acceleration (95% CI 1.06–1.10).
                  </p>
                  <div className="bg-emerald-50 rounded-xl p-4 border border-emerald-100 font-mono text-xs space-y-1">
                    <div className="text-gray-500">xb = intercept + Σ(weight_i × value_i) + age_weight × age</div>
                    <div className="text-gray-500">mortality_score = 1 − exp(−exp(xb) × (exp(γ×t) − 1) / γ)</div>
                    <div className="text-gray-500">PhenoAge = offset + ln(−ln(1−m) × denominator) / ln_numerator_coefficient</div>
                    <div className="text-emerald-700 font-bold mt-2">Healthy 45yo → ~34yr · Accelerated 58yo → 77.02yr</div>
                    <div className="text-gray-400">Failure: &lt;9 biomarkers → component linear terms only; phenoage_estimate: null</div>
                  </div>
                </div>
              </div>
            </div>

            {/* 3 */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <div className="flex items-start gap-5">
                <div className="w-10 h-10 rounded-xl bg-violet-50 flex items-center justify-center shrink-0 font-black text-violet-600">3</div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-black text-gray-900">Map</h3>
                    <span className="text-xs font-bold text-violet-600 uppercase tracking-wider">Hallmark Scoring · PMID 36599349</span>
                  </div>
                  <p className="text-sm text-gray-600 leading-relaxed mb-3">
                    Maps biomarker deviations to 6 of the 9 hallmarks of aging (López-Otín 2023). PhenoAge signal = sum of |β×x| for accelerating components per hallmark. Supplementary signal = sum of threshold tier_scores (0/0.5/1). <strong>Never blended.</strong> Always labeled separately.
                  </p>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                    {[
                      { name: "Genomic Instability", status: "shippable" },
                      { name: "Epigenetic Alterations", status: "shippable" },
                      { name: "Nutrient Sensing", status: "shippable" },
                      { name: "Mitochondrial Dysfunction", status: "shippable" },
                      { name: "Cellular Senescence", status: "shippable" },
                      { name: "Intercellular Communication", status: "shippable" },
                      { name: "Telomere Attrition", status: "not-implemented" },
                      { name: "Loss of Proteostasis", status: "not-implemented" },
                      { name: "Disabled Macroautophagy", status: "not-implemented" },
                    ].map((h) => (
                      <div key={h.name} className={`px-2 py-1.5 rounded-lg text-center font-medium ${
                        h.status === "shippable"
                          ? "bg-violet-50 text-violet-700 border border-violet-200"
                          : "bg-gray-50 text-gray-400 border border-gray-200 line-through"
                      }`}>
                        {h.name}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* 4 */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <div className="flex items-start gap-5">
                <div className="w-10 h-10 rounded-xl bg-sky-50 flex items-center justify-center shrink-0 font-black text-sky-600">4</div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-black text-gray-900">Detect</h3>
                    <span className="text-xs font-bold text-sky-600 uppercase tracking-wider">Gap Detection · 315-Marker Registry</span>
                  </div>
                  <p className="text-sm text-gray-600 leading-relaxed mb-3">
                    Compares existing biomarker keys against the 315-marker registry. Returns <code className="text-xs bg-gray-100 px-1 rounded font-mono">missing_tier1</code>, <code className="text-xs bg-gray-100 px-1 rounded font-mono">coverage_pct</code>, and which panels would fill the gaps. Sex-specific markers filtered automatically.
                  </p>
                  <div className="bg-sky-50 rounded-xl p-4 border border-sky-100 font-mono text-xs">
                    <div className="text-gray-500">CMP + CBC only (5/9 PhenoAge markers) →</div>
                    <div className="text-sky-700 font-bold mt-1">coverage_pct: 31%</div>
                    <div className="text-rose-600">missing_tier1: crp_log, lymphocyte_percent, rdw, alkaline_phosphatase</div>
                    <div className="text-gray-400 mt-1">Failure: zero panels → coverage_pct: 0.0; still returns valid gap report</div>
                  </div>
                </div>
              </div>
            </div>

            {/* 5 */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <div className="flex items-start gap-5">
                <div className="w-10 h-10 rounded-xl bg-orange-50 flex items-center justify-center shrink-0 font-black text-orange-600">5</div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-black text-gray-900">Route</h3>
                    <span className="text-xs font-bold text-orange-600 uppercase tracking-wider">Deterministic State Machine</span>
                  </div>
                  <p className="text-sm text-gray-600 leading-relaxed mb-3">
                    Reads the patient&apos;s full clinical event timeline and determines which of 6 states they are in. No LLM. No randomness. Same inputs always produce the same state.
                  </p>
                  <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
                    {["NEW", "DATA_INCOMPLETE", "ASSESSMENT_PENDING", "ORDER_PENDING", "COMPOUND_CANDIDATE", "MONITORING"].map((s, i, arr) => (
                      <span key={s} className="flex items-center gap-2">
                        <span className="bg-orange-50 border border-orange-200 text-orange-700 px-2 py-1 rounded-lg font-bold">{s}</span>
                        {i < arr.length - 1 && <span className="text-gray-400">→</span>}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* 6 */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <div className="flex items-start gap-5">
                <div className="w-10 h-10 rounded-xl bg-rose-50 flex items-center justify-center shrink-0 font-black text-rose-600">6</div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-black text-gray-900">Recommend</h3>
                    <span className="text-xs font-bold text-rose-600 uppercase tracking-wider">Action Scorer · Weighted Formula</span>
                  </div>
                  <p className="text-sm text-gray-600 leading-relaxed mb-3">
                    Scores all valid actions using a weighted formula. State machine gates which actions are valid — a patient in MONITORING cannot score <code className="text-xs bg-gray-100 px-1 rounded font-mono">order_baseline_panel</code>. Always returns at least one action.
                  </p>
                  <div className="bg-rose-50 rounded-xl p-4 border border-rose-100 font-mono text-xs">
                    <div className="text-gray-600">score = <span className="text-rose-700 font-bold">0.30</span>×data_urgency</div>
                    <div className="text-gray-600">     + <span className="text-rose-700 font-bold">0.25</span>×phenoage_urgency</div>
                    <div className="text-gray-600">     + <span className="text-rose-700 font-bold">0.25</span>×escalation_severity</div>
                    <div className="text-gray-600">     + <span className="text-rose-700 font-bold">0.10</span>×time_decay</div>
                    <div className="text-gray-600">     + <span className="text-rose-700 font-bold">0.10</span>×hallmark_signal</div>
                    <div className="text-gray-400 mt-2">7 action types · all components clipped to [0.0, 1.0]</div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* Section 3: Training Sources */}
      <section className="py-16 px-6 bg-gray-900">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-black text-white mb-3 tracking-tight">Training Sources</h2>
          <p className="text-gray-400 font-medium mb-10">Every formula, lookup table, and evidence tier is anchored to a published source. No invented numbers.</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              {
                label: "PhenoAge Gompertz Model",
                source: "Levine et al. 2018",
                pmid: "29676998",
                detail: "Gompertz PH coefficients from Supplementary Table S1. Validated in NHANES III (n=11,432) and NHANES IV (n=6,209). HR=1.08/yr acceleration.",
                color: "border-emerald-800/50 bg-emerald-950/30",
              },
              {
                label: "ASCVD Pooled Cohort Equations",
                source: "Goff et al. 2014",
                pmid: "24222018",
                detail: "4 sex/race strata (white male, white female, AA male, AA female). 10-year ASCVD risk. ACC/AHA guideline formula.",
                color: "border-blue-800/50 bg-blue-950/30",
              },
              {
                label: "Hallmark Framework",
                source: "López-Otín et al. 2023",
                pmid: "36599349",
                detail: "9 hallmarks of aging. 6 implemented in shippable scorer. Biomarker-to-hallmark associations curated from published literature.",
                color: "border-violet-800/50 bg-violet-950/30",
              },
              {
                label: "APOE Diplotype",
                source: "Corder et al. 1993",
                pmid: "8346443",
                detail: "rs429358 + rs7412 → e2/e2 through e4/e4. e4/e4 = 8–12× AD risk vs e3/e3. Hardcoded lookup table.",
                color: "border-orange-800/50 bg-orange-950/30",
              },
              {
                label: "MTHFR Enzyme Activity",
                source: "Frosst et al. 1995",
                pmid: "8554066",
                detail: "C677T: CC=100%, CT=65%, TT=30% activity. A1298C: AA=100%, AC=85%, CC=70%. Compound het CT+AC=50%.",
                color: "border-yellow-800/50 bg-yellow-950/30",
              },
              {
                label: "MR Evidence — omega_3",
                source: "Fabian 2025",
                doi: "10.1186/s40246-025-00756-3",
                detail: "Oily fish → PhenoAge acceleration IVW p=0.0086. Fish oil → GrimAge IVW p=0.037. Strongest MR anchor in registry.",
                color: "border-teal-800/50 bg-teal-950/30",
              },
              {
                label: "MR Evidence — vitamin_d3",
                source: "Hagenbeek 2022",
                pmid: "36055464",
                detail: "Genetically predicted 25-OHD → lower GrimAge. IVW p=0.04. Twin Research and Human Genetics.",
                color: "border-sky-800/50 bg-sky-950/30",
              },
              {
                label: "BRCA Risk Estimates",
                source: "Kuchenbaecker et al. 2017",
                pmid: "28632866",
                detail: "BRCA1: 50–80% lifetime breast, 20–40% ovarian. BRCA2: 40–70% breast, 10–20% ovarian. JAMA 2017.",
                color: "border-rose-800/50 bg-rose-950/30",
              },
            ].map((s) => (
              <div key={s.label} className={`rounded-2xl border p-5 ${s.color}`}>
                <div className="flex items-start justify-between gap-3 mb-2">
                  <h3 className="font-bold text-white text-sm">{s.label}</h3>
                  <span className="text-xs font-mono text-gray-400 shrink-0">
                    {s.pmid ? `PMID ${s.pmid}` : s.doi ? `DOI ${s.doi}` : ""}
                  </span>
                </div>
                <p className="text-xs text-gray-400 font-medium mb-1">{s.source}</p>
                <p className="text-xs text-gray-500 leading-relaxed">{s.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Section 4: Benchmark */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-black text-gray-900 mb-3 tracking-tight">Benchmark Accuracy</h2>
          <p className="text-gray-500 font-medium mb-10">What is pinned by tests. What is implemented but not cohort-validated. What is scaffolded. No conflation.</p>
          <BenchmarkPanel />
        </div>
      </section>

      {/* Section 5: What We Don't Do */}
      <section className="py-16 px-6 bg-gray-50 border-y border-gray-100">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-black text-gray-900 mb-3 tracking-tight">What We Don&apos;t Do</h2>
          <p className="text-gray-500 font-medium mb-8">Honest limitations. Not roadmap items — current hard boundaries.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { title: "No methylation array analysis", detail: "Epigenetic clocks (GrimAge, DunedinPACE, Horvath, Hannum) accept pre-computed values only. You need an external service (e.g. TruDiagnostic) to generate the clock values." },
              { title: "No telomere assay", detail: "Telomere attrition is one of the 9 hallmarks of aging. It is NOT in the shippable scorer. Leukocyte telomere length is accepted as a supplementary biomarker but not scored numerically." },
              { title: "No body composition", detail: "DEXA / body composition endpoint is not yet in the repo. The agentic pipeline has a body_composition field in its state but no scoring logic." },
              { title: "No LangGraph in production without install", detail: "The multi-agent pipeline returns HTTP 503 if langgraph≥0.2.0 is not installed. The 6-transformation pipeline (assessment_level0) does not require LangGraph." },
              { title: "No persistent run registry", detail: "The pipeline status endpoint uses an in-memory TTL registry (1 hour). It is not persistent across restarts." },
              { title: "No clinical diagnosis", detail: "Research Use Only. Longivity is not a medical device. PhenoAge acceleration labels are CrisPRO UX thresholds, not PhenoAge classifications. Do not use for clinical decisions without a qualified clinician." },
            ].map((item) => (
              <div key={item.title} className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
                <div className="flex items-start gap-3">
                  <div className="w-5 h-5 rounded-full bg-gray-200 flex items-center justify-center shrink-0 mt-0.5">
                    <svg className="w-3 h-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-900 text-sm mb-1">{item.title}</h3>
                    <p className="text-xs text-gray-500 leading-relaxed">{item.detail}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Section 6: CTA */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-black text-gray-900 mb-4 tracking-tight">See It Run on Real Data</h2>
          <p className="text-gray-500 font-medium mb-8">
            Five pre-loaded patient scenarios. Real API calls. No mocked data. Each scenario is designed to stress-test a different capability.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/demo"
              className="px-8 py-4 rounded-xl bg-gray-900 hover:bg-black text-white text-lg font-black transition-all shadow-xl hover:-translate-y-1"
            >
              Open Demo →
            </Link>
            <Link
              href="/login"
              className="px-8 py-4 rounded-xl bg-white border-2 border-gray-200 hover:border-gray-300 text-gray-800 text-lg font-bold transition-all hover:bg-gray-50"
            >
              Enter Clinic Dashboard
            </Link>
          </div>
          <p className="text-xs text-gray-400 mt-6">Research Use Only (RUO). Not for clinical diagnosis.</p>
        </div>
      </section>

    </div>
  );
}
