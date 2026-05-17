import Link from "next/link";
import { Lead, Highlight } from "@/components/ui/typography";

export const metadata = {
  title: "Longivity — Clinical Intelligence for Longevity Medicine",
  description: "One ranked clinical action per patient. PhenoAge acceleration, hallmark scoring, and a deterministic state machine — built for longevity clinicians.",
};

export default function LandingPage() {
  return (
    <div className="bg-white text-gray-900">

      {/* ── Section 1: Hero ── */}
      <section className="pt-36 pb-24 px-6 text-center">
        <div className="max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm font-bold mb-8 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Clinical Intelligence Platform · PhenoAge + Hallmarks + State Machine
          </div>

          <h1 className="text-5xl md:text-7xl font-black text-gray-900 leading-tight mb-8 tracking-tight">
            One{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-600 to-teal-500">
              Decision.
            </span>
            <br />
            Per Patient.<br />
            Every Time.
          </h1>

          <Lead className="max-w-3xl mx-auto mb-12">
            Longivity normalizes your lab inputs, computes{" "}
            <Highlight color="emerald">PhenoAge acceleration</Highlight>, scores{" "}
            <Highlight color="violet">6 hallmarks of aging</Highlight>, detects missing markers, routes the patient through a deterministic state machine, and returns{" "}
            <Highlight color="sky">one ranked action</Highlight> — with a biological reason and explicit provenance.
          </Lead>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/login"
              className="px-8 py-4 rounded-xl bg-gray-900 hover:bg-black text-white text-lg font-bold transition-all shadow-xl hover:shadow-gray-400/50 hover:-translate-y-1"
            >
              Request Demo →
            </Link>
            <Link
              href="/login"
              className="px-8 py-4 rounded-xl bg-white border-2 border-gray-200 hover:border-gray-300 text-gray-800 text-lg font-bold transition-all hover:bg-gray-50 flex items-center gap-2"
            >
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              Enter Clinic Dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* ── Section 2: The Problem ── */}
      <section className="pb-16 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="bg-gray-900 rounded-3xl p-8 md:p-12 shadow-2xl border border-gray-800 flex flex-col md:flex-row items-start justify-between gap-8">
            <div className="text-left md:w-1/2">
              <h3 className="text-2xl font-bold text-white mb-3">The Intelligence Lives in the Clinician&apos;s Head</h3>
              <p className="text-gray-400 font-medium leading-relaxed">
                A single patient visit generates 80–300 biomarker values. Today, a clinician makes 4–6 API calls and mentally stitches the answer together. When the clinician leaves, the reasoning leaves with them. That is not a SaaS product — it is a collection of tools.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-6 md:w-1/2">
              <div className="flex flex-col gap-1">
                <span className="text-gray-400 text-xs font-bold uppercase tracking-wider">Registry</span>
                <span className="text-3xl font-black text-emerald-400">315</span>
                <span className="text-gray-500 text-sm font-medium">Biomarkers tracked</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-gray-400 text-xs font-bold uppercase tracking-wider">Hallmarks</span>
                <span className="text-3xl font-black text-violet-400">6</span>
                <span className="text-gray-500 text-sm font-medium">Aging systems scored</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-gray-400 text-xs font-bold uppercase tracking-wider">States</span>
                <span className="text-3xl font-black text-sky-400">6</span>
                <span className="text-gray-500 text-sm font-medium">Patient state machine</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-gray-400 text-xs font-bold uppercase tracking-wider">Rules</span>
                <span className="text-3xl font-black text-rose-400">50+</span>
                <span className="text-gray-500 text-sm font-medium">Escalation triggers</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Section 3: The Six Transformations ── */}
      <section id="platform" className="py-24 px-6 bg-gray-50 border-y border-gray-100">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-black text-gray-900 mb-6 tracking-tight">
              Six Transformations on Patient Data
            </h2>
            <Lead className="max-w-3xl mx-auto">
              Not six features. Six sequential operations that convert fragmented inputs into a structured clinical decision. Every transformation is deterministic, auditable, and grounded in published science.
            </Lead>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

            {/* 1. Normalize */}
            <div className="bg-white rounded-3xl border border-gray-200 shadow-sm p-8 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-2xl bg-gray-100 flex items-center justify-center mb-6">
                <span className="text-2xl font-black text-gray-600">1</span>
              </div>
              <h3 className="text-xl font-black text-gray-900 mb-2">Normalize</h3>
              <p className="text-sm text-gray-500 font-semibold uppercase tracking-wider mb-4">Input → Canonical Units</p>
              <p className="text-gray-600 text-sm leading-relaxed mb-4">
                Accepts biomarker inputs in any unit format. albumin in g/dL or g/L. Glucose in mg/dL or mmol/L. CRP as mg/L, mg/dL, or ln(mg/dL). 20+ aliases per marker. Every conversion is logged in the response.
              </p>
              <div className="bg-gray-50 rounded-xl p-4 font-mono text-xs text-gray-500 border border-gray-100">
                <div className="text-gray-400">Input:</div>
                <div className="text-gray-700">albumin: 4.5 <span className="text-gray-400">(g/dL)</span></div>
                <div className="text-gray-400 mt-2">Output:</div>
                <div className="text-emerald-600 font-bold">albumin: 45.0 <span className="text-gray-400">(g/L)</span></div>
                <div className="text-gray-400 text-[10px] mt-1">note: &quot;converted g/dL → g/L (×10)&quot;</div>
              </div>
              <div className="mt-4 text-xs text-gray-400">
                <span className="font-bold text-gray-500">Failure mode:</span> Out-of-range values flagged with warning note. Still used — not rejected.
              </div>
            </div>

            {/* 2. Score */}
            <div className="bg-white rounded-3xl border border-gray-200 shadow-sm p-8 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-2xl bg-emerald-50 flex items-center justify-center mb-6">
                <span className="text-2xl font-black text-emerald-600">2</span>
              </div>
              <h3 className="text-xl font-black text-gray-900 mb-2">Score</h3>
              <p className="text-sm text-emerald-600 font-semibold uppercase tracking-wider mb-4">PhenoAge Gompertz Model</p>
              <p className="text-gray-600 text-sm leading-relaxed mb-4">
                Applies the Levine 2018 Gompertz proportional hazards model (PMID 29676998) to compute biological age from 9 biomarkers + chronological age. Acceleration = PhenoAge − chronological age.
              </p>
              <div className="bg-emerald-50 rounded-xl p-4 font-mono text-xs border border-emerald-100">
                <div className="text-gray-400">9 biomarkers + age 52</div>
                <div className="text-emerald-700 font-bold mt-1">PhenoAge: 54.2 yr</div>
                <div className="text-rose-600 font-bold">Acceleration: +2.2 yr</div>
                <div className="text-gray-400 text-[10px] mt-1">Tier: MILD · PMID 29676998</div>
              </div>
              <div className="mt-4 text-xs text-gray-400">
                <span className="font-bold text-gray-500">Failure mode:</span> With &lt;9 biomarkers, returns component linear terms only. phenoage_estimate is null. completeness_mode: PARTIAL.
              </div>
            </div>

            {/* 3. Map */}
            <div className="bg-white rounded-3xl border border-gray-200 shadow-sm p-8 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-2xl bg-violet-50 flex items-center justify-center mb-6">
                <span className="text-2xl font-black text-violet-600">3</span>
              </div>
              <h3 className="text-xl font-black text-gray-900 mb-2">Map</h3>
              <p className="text-sm text-violet-600 font-semibold uppercase tracking-wider mb-4">Hallmark Scoring</p>
              <p className="text-gray-600 text-sm leading-relaxed mb-4">
                Maps biomarker deviations to 6 of the 9 hallmarks of aging (López-Otín 2023, PMID 36599349). PhenoAge-calibrated signals are kept separate from threshold-based supplementary signals. Never blended.
              </p>
              <div className="bg-violet-50 rounded-xl p-4 font-mono text-xs border border-violet-100">
                <div className="text-gray-400">CRP elevated →</div>
                <div className="text-violet-700 font-bold mt-1">altered_intercellular_communication</div>
                <div className="text-gray-400 text-[10px]">status: PRIMARY_DRIVER</div>
                <div className="text-emerald-600 font-bold mt-1">→ Omega-3 MR_VALIDATED</div>
              </div>
              <div className="mt-4 text-xs text-gray-400">
                <span className="font-bold text-gray-500">Failure mode:</span> Hallmarks with no biomarker signal are absent from hallmark_narrative. hallmarks_scoreable count shown.
              </div>
            </div>

            {/* 4. Detect */}
            <div className="bg-white rounded-3xl border border-gray-200 shadow-sm p-8 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-2xl bg-sky-50 flex items-center justify-center mb-6">
                <span className="text-2xl font-black text-sky-600">4</span>
              </div>
              <h3 className="text-xl font-black text-gray-900 mb-2">Detect</h3>
              <p className="text-sm text-sky-600 font-semibold uppercase tracking-wider mb-4">Gap Detection</p>
              <p className="text-gray-600 text-sm leading-relaxed mb-4">
                Compares existing biomarker keys against the 315-marker registry. Returns missing_tier1, missing_tier2, missing_tier3, coverage_pct, and which panels would fill the gaps. Sex-specific markers filtered automatically.
              </p>
              <div className="bg-sky-50 rounded-xl p-4 font-mono text-xs border border-sky-100">
                <div className="text-gray-400">CMP + CBC only →</div>
                <div className="text-sky-700 font-bold mt-1">coverage_pct: 31%</div>
                <div className="text-rose-600">missing_tier1: 49 markers</div>
                <div className="text-gray-400 text-[10px] mt-1">missing_panels: iron, thyroid, lipid_advanced...</div>
              </div>
              <div className="mt-4 text-xs text-gray-400">
                <span className="font-bold text-gray-500">Failure mode:</span> Zero panels → coverage_pct: 0.0, all tier_1 markers missing. Still returns valid gap report.
              </div>
            </div>

            {/* 5. Route */}
            <div className="bg-white rounded-3xl border border-gray-200 shadow-sm p-8 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-2xl bg-orange-50 flex items-center justify-center mb-6">
                <span className="text-2xl font-black text-orange-600">5</span>
              </div>
              <h3 className="text-xl font-black text-gray-900 mb-2">Route</h3>
              <p className="text-sm text-orange-600 font-semibold uppercase tracking-wider mb-4">State Machine</p>
              <p className="text-gray-600 text-sm leading-relaxed mb-4">
                Reads the patient&apos;s full clinical event timeline and determines which of 6 states they are in. Deterministic — no LLM, no randomness. The same inputs always produce the same state.
              </p>
              <div className="bg-orange-50 rounded-xl p-4 font-mono text-xs border border-orange-100">
                <div className="text-gray-400">panel_uploaded + 31% coverage →</div>
                <div className="text-orange-700 font-bold mt-1">state: DATA_INCOMPLETE</div>
                <div className="text-gray-400 text-[10px] mt-1">NEW → DATA_INCOMPLETE → ASSESSMENT_PENDING</div>
                <div className="text-gray-400 text-[10px]">→ ORDER_PENDING → COMPOUND_CANDIDATE → MONITORING</div>
              </div>
              <div className="mt-4 text-xs text-gray-400">
                <span className="font-bold text-gray-500">Failure mode:</span> No timeline → state: NEW. Always returns one of 6 states. Never throws.
              </div>
            </div>

            {/* 6. Recommend */}
            <div className="bg-white rounded-3xl border border-gray-200 shadow-sm p-8 hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-2xl bg-rose-50 flex items-center justify-center mb-6">
                <span className="text-2xl font-black text-rose-600">6</span>
              </div>
              <h3 className="text-xl font-black text-gray-900 mb-2">Recommend</h3>
              <p className="text-sm text-rose-600 font-semibold uppercase tracking-wider mb-4">Action Scorer</p>
              <p className="text-gray-600 text-sm leading-relaxed mb-4">
                Scores all valid actions using a weighted formula. Returns the top-ranked action with a reason. State machine gates which actions are valid — a patient in MONITORING cannot score order_baseline_panel.
              </p>
              <div className="bg-rose-50 rounded-xl p-4 font-mono text-xs border border-rose-100">
                <div className="text-gray-400">score = 0.30·data + 0.25·phenoage</div>
                <div className="text-gray-400">+ 0.25·escalation + 0.10·time + 0.10·hallmark</div>
                <div className="text-rose-700 font-bold mt-2">next: Order Advanced Lipid Panel</div>
                <div className="text-gray-400 text-[10px]">score: 0.74 · urgency: high</div>
              </div>
              <div className="mt-4 text-xs text-gray-400">
                <span className="font-bold text-gray-500">Failure mode:</span> No valid actions for state → returns upload_results action. Always returns at least one action.
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* ── Section 4: Provenance ── */}
      <section id="science" className="py-24 px-6 bg-gray-900">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-black text-white mb-6 tracking-tight">
              What Is Validated. What Is Not.
            </h2>
            <p className="text-xl text-gray-400 font-medium max-w-3xl mx-auto">
              We separate mortality-calibrated signals from threshold-based signals. We label every compound recommendation with its evidence tier. We tell you what is proven and what is inferred.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

            {/* Validated */}
            <div className="bg-emerald-950/50 border border-emerald-800/50 rounded-3xl p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                </div>
                <h3 className="text-lg font-bold text-emerald-400">Validated Logic</h3>
              </div>
              <ul className="space-y-3 text-sm text-gray-300">
                <li className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5 shrink-0">·</span>
                  <span><strong className="text-white">PhenoAge Gompertz formula</strong> — PMID 29676998. Golden snapshot tests pin output to ±0.5 years. Healthy 45yo → ~34yr. Accelerated 58yo → ~77yr.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5 shrink-0">·</span>
                  <span><strong className="text-white">ASCVD Pooled Cohort Equations</strong> — PMID 24222018. 4 sex/race strata. Risk category verified.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5 shrink-0">·</span>
                  <span><strong className="text-white">MR evidence tiers</strong> — omega_3, metformin, vitamin_d3, folate are MR_VALIDATED with DOI/PMID anchors. berberine, NMN → RCT. rapamycin → OBSERVATIONAL.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5 shrink-0">·</span>
                  <span><strong className="text-white">APOE diplotype</strong> — PMID 8346443. Hardcoded lookup table. e4/e4 → 8–12× AD risk vs e3/e3.</span>
                </li>
              </ul>
            </div>

            {/* Implemented, not clinically proven */}
            <div className="bg-yellow-950/30 border border-yellow-800/30 rounded-3xl p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded-full bg-yellow-500 flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                </div>
                <h3 className="text-lg font-bold text-yellow-400">Implemented, Not Cohort-Validated</h3>
              </div>
              <ul className="space-y-3 text-sm text-gray-300">
                <li className="flex items-start gap-2">
                  <span className="text-yellow-400 mt-0.5 shrink-0">·</span>
                  <span><strong className="text-white">Hallmark-to-biomarker associations</strong> — curated from published literature. Not validated against a clinical cohort.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-yellow-400 mt-0.5 shrink-0">·</span>
                  <span><strong className="text-white">Compound relevance scoring</strong> — PMID-verified links where flagged. Scoring formula not outcome-validated.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-yellow-400 mt-0.5 shrink-0">·</span>
                  <span><strong className="text-white">Wearable hallmark mapping</strong> — HRV, VO2max, sleep thresholds from published sources. Not validated against longevity outcomes.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-yellow-400 mt-0.5 shrink-0">·</span>
                  <span><strong className="text-white">27-SNP PRS</strong> — Timmers 2019 weights correctly implemented. Partial genotype approximation not externally validated.</span>
                </li>
              </ul>
            </div>

            {/* Scaffolded */}
            <div className="bg-gray-800/50 border border-gray-700/50 rounded-3xl p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
                </div>
                <h3 className="text-lg font-bold text-gray-400">Scaffolded / Environment-Dependent</h3>
              </div>
              <ul className="space-y-3 text-sm text-gray-300">
                <li className="flex items-start gap-2">
                  <span className="text-gray-500 mt-0.5 shrink-0">·</span>
                  <span><strong className="text-white">LangGraph multi-agent pipeline</strong> — returns 503 if langgraph≥0.2.0 not installed. Tests skip gracefully.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-gray-500 mt-0.5 shrink-0">·</span>
                  <span><strong className="text-white">Epigenetic clocks</strong> — accepts pre-computed values only. Does not run methylation array analysis. Requires external service (e.g. TruDiagnostic).</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-gray-500 mt-0.5 shrink-0">·</span>
                  <span><strong className="text-white">NHANES validation</strong> — script exists and is importable. Actual validation against NHANES data not yet run.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-gray-500 mt-0.5 shrink-0">·</span>
                  <span><strong className="text-white">In-memory run registry</strong> — TTL-evicted, not persistent across restarts.</span>
                </li>
              </ul>
            </div>

          </div>
        </div>
      </section>

      {/* ── Section 5: Workflow ── */}
      <section id="workflow" className="py-24 px-6 bg-white">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-black text-gray-900 mb-6 tracking-tight">
              From Blood Draw to Next Action
            </h2>
            <Lead className="max-w-2xl mx-auto">
              Four steps. Under 2 seconds for the compute. Every action writes to the patient timeline.
            </Lead>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {[
              {
                step: "01",
                color: "bg-gray-100 text-gray-600",
                title: "Upload",
                body: "PDF from Quest, LabCorp, or manual entry. 20+ unit aliases handled automatically. albumin in g/dL or g/L — both work.",
              },
              {
                step: "02",
                color: "bg-emerald-50 text-emerald-600",
                title: "Compute",
                body: "Six transformations run: normalize, PhenoAge, hallmarks, gap detection, state machine, action scoring. Under 2 seconds.",
              },
              {
                step: "03",
                color: "bg-violet-50 text-violet-600",
                title: "Review",
                body: "One ranked action with a biological reason. Full scoring breakdown visible. Every component auditable. Provenance labeled.",
              },
              {
                step: "04",
                color: "bg-sky-50 text-sky-600",
                title: "Act",
                body: "Click the CTA. Generate a test order, run an assessment, or start a compound protocol. Every action writes to the patient timeline.",
              },
            ].map((item, i) => (
              <div key={i} className="flex flex-col items-center text-center">
                <div className={`w-16 h-16 rounded-2xl ${item.color} flex items-center justify-center mb-4 font-black text-xl`}>
                  {item.step}
                </div>
                <h3 className="text-lg font-black text-gray-900 mb-2">{item.title}</h3>
                <p className="text-sm text-gray-600 leading-relaxed">{item.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Section 6: CTA ── */}
      <section className="py-24 px-6 bg-emerald-50 border-t border-emerald-100">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-rose-50 border border-rose-200 text-rose-700 text-sm font-bold mb-8 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-rose-500"></span>
            Research Use Only (RUO)
          </div>
          <h2 className="text-4xl md:text-5xl font-black text-gray-900 mb-6 tracking-tight">
            Built for Clinicians Who Want to Reason Faster, Not Harder.
          </h2>
          <Lead className="max-w-3xl mx-auto mb-12">
            Longivity does not replace clinical judgment. It eliminates the 20 minutes of manual cross-referencing before you can exercise it.
          </Lead>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/login"
              className="px-8 py-4 rounded-xl bg-gray-900 hover:bg-black text-white text-lg font-black transition-all shadow-xl hover:-translate-y-1 flex items-center gap-3"
            >
              Request Demo →
            </Link>
            <Link
              href="/login"
              className="px-8 py-4 rounded-xl bg-white border-2 border-gray-200 hover:border-gray-300 text-gray-800 text-lg font-bold transition-all hover:bg-gray-50"
            >
              Enter Clinic Dashboard
            </Link>
          </div>
        </div>
      </section>

    </div>
  );
}
