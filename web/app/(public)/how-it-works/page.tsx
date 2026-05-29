import Link from "next/link";
import NormalizerDemo from "@/components/how-it-works/NormalizerDemo";
import PhenoAgeCalculator from "@/components/how-it-works/PhenoAgeCalculator";
import HallmarkMap from "@/components/how-it-works/HallmarkMap";
import GapDetector from "@/components/how-it-works/GapDetector";
import StateMachineWalkthrough from "@/components/how-it-works/StateMachineWalkthrough";
import ActionScorer from "@/components/how-it-works/ActionScorer";
import BenchmarkPanel from "@/components/demo/BenchmarkPanel";

export const metadata = {
  title: "How It Works — Longevity",
  description: "Six interactive demos showing exactly how Longevity converts biomarker inputs into ranked clinical actions.",
};

function StepBadge({ n, color }: { n: number; color: string }) {
  return (
    <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 font-black text-lg ${color}`}>
      {n}
    </div>
  );
}

export default function HowItWorksPage() {
  return (
    <div className="bg-white text-gray-900">

      {/* ── Hero ─────────────────────────────────────────────────────────────── */}
      <section className="pt-36 pb-20 px-6 text-center">
        <div className="max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-gray-100 border border-gray-200 text-gray-600 text-sm font-bold mb-8">
            Interactive · Source-Verified · No Mocked Data
          </div>
          <h1 className="text-4xl md:text-6xl font-black text-gray-900 leading-tight mb-6 tracking-tight">
            See the Machine Run
          </h1>
          <p className="text-xl text-gray-500 font-medium leading-relaxed mb-10">
            Six transformations turn raw biomarker values into one ranked clinical action.
            Every demo below is live — drag the sliders, click the states, watch the output change.
          </p>
          {/* Pipeline overview */}
          <div className="flex items-center justify-center gap-1 flex-wrap text-sm font-bold">
            {[
              { n: 1, label: "Normalize", color: "bg-emerald-100 text-emerald-700" },
              { n: 2, label: "Score", color: "bg-blue-100 text-blue-700" },
              { n: 3, label: "Map", color: "bg-violet-100 text-violet-700" },
              { n: 4, label: "Detect", color: "bg-sky-100 text-sky-700" },
              { n: 5, label: "Route", color: "bg-orange-100 text-orange-700" },
              { n: 6, label: "Recommend", color: "bg-rose-100 text-rose-700" },
            ].map((s, i, arr) => (
              <span key={s.n} className="flex items-center gap-1">
                <span className={`px-3 py-1.5 rounded-full ${s.color}`}>{s.n}. {s.label}</span>
                {i < arr.length - 1 && <span className="text-gray-300">→</span>}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── Step 1: Normalize ────────────────────────────────────────────────── */}
      <section className="py-16 px-6 bg-gray-50 border-y border-gray-100">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-start gap-4 mb-6">
            <StepBadge n={1} color="bg-emerald-100 text-emerald-700" />
            <div>
              <h2 className="text-2xl font-black text-gray-900 tracking-tight">Normalize</h2>
              <p className="text-gray-500 font-medium mt-1">
                Your lab reports g/dL. The model needs g/L. Drag the slider — watch the conversion happen in real time.
                20+ aliases per marker are resolved automatically before any math runs.
              </p>
            </div>
          </div>
          <NormalizerDemo />
          <p className="text-xs text-gray-400 mt-3 font-mono">
            Source: extract_phenoage_marker_values() · longevity_phenoage_level0.py · Out-of-range values flagged but never silently rejected
          </p>
        </div>
      </section>

      {/* ── Step 2: Score ────────────────────────────────────────────────────── */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-start gap-4 mb-6">
            <StepBadge n={2} color="bg-blue-100 text-blue-700" />
            <div>
              <h2 className="text-2xl font-black text-gray-900 tracking-tight">Score — PhenoAge</h2>
              <p className="text-gray-500 font-medium mt-1">
                Levine 2018 Gompertz proportional hazards model (PMID 29676998). Validated in NHANES III (n=11,432).
                Pick a preset or tune each marker — the bar chart shows which biomarkers are aging you fastest.
              </p>
            </div>
          </div>
          <PhenoAgeCalculator />
          <p className="text-xs text-gray-400 mt-3 font-mono">
            HR=1.08 per year of acceleration (95% CI 1.06–1.10) · Failure mode: &lt;9 markers → phenoage_estimate: null
          </p>
        </div>
      </section>

      {/* ── Step 3: Map ──────────────────────────────────────────────────────── */}
      <section className="py-16 px-6 bg-gray-50 border-y border-gray-100">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-start gap-4 mb-6">
            <StepBadge n={3} color="bg-violet-100 text-violet-700" />
            <div>
              <h2 className="text-2xl font-black text-gray-900 tracking-tight">Map — Hallmarks of Aging</h2>
              <p className="text-gray-500 font-medium mt-1">
                Biomarker deviations are mapped to 6 of the 9 hallmarks (López-Otín 2023, PMID 36599349).
                Click any hallmark to see which markers drive it and how the signal is computed.
                Gray = not yet implemented — no conflation.
              </p>
            </div>
          </div>
          <HallmarkMap />
        </div>
      </section>

      {/* ── Step 4: Detect ───────────────────────────────────────────────────── */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-start gap-4 mb-6">
            <StepBadge n={4} color="bg-sky-100 text-sky-700" />
            <div>
              <h2 className="text-2xl font-black text-gray-900 tracking-tight">Detect — Gap Analysis</h2>
              <p className="text-gray-500 font-medium mt-1">
                315-marker registry. Toggle which markers are present in a patient record — watch coverage, missing panels,
                and inferred state update instantly. Sex-specific markers are filtered automatically.
              </p>
            </div>
          </div>
          <GapDetector />
          <p className="text-xs text-gray-400 mt-3 font-mono">
            Tier 1 = PhenoAge-required + high-clinical-significance markers · coverage_pct drives state machine routing
          </p>
        </div>
      </section>

      {/* ── Step 5: Route ────────────────────────────────────────────────────── */}
      <section className="py-16 px-6 bg-gray-50 border-y border-gray-100">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-start gap-4 mb-6">
            <StepBadge n={5} color="bg-orange-100 text-orange-700" />
            <div>
              <h2 className="text-2xl font-black text-gray-900 tracking-tight">Route — State Machine</h2>
              <p className="text-gray-500 font-medium mt-1">
                No LLM. No randomness. The same inputs always produce the same state.
                Walk through a real patient journey — Marcus Webb, 52M — from first visit to active monitoring.
              </p>
            </div>
          </div>
          <StateMachineWalkthrough />
          <p className="text-xs text-gray-400 mt-3 font-mono">
            6 states · all transitions unit-tested · deterministic · same inputs → same state every time
          </p>
        </div>
      </section>

      {/* ── Step 6: Recommend ────────────────────────────────────────────────── */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-start gap-4 mb-6">
            <StepBadge n={6} color="bg-rose-100 text-rose-700" />
            <div>
              <h2 className="text-2xl font-black text-gray-900 tracking-tight">Recommend — Action Scorer</h2>
              <p className="text-gray-500 font-medium mt-1">
                Five weighted components produce one urgency score. The state machine gates which actions are valid —
                a patient in MONITORING cannot score "order baseline panel". Tune the weights and watch the top action change.
              </p>
            </div>
          </div>
          <ActionScorer />
          <p className="text-xs text-gray-400 mt-3 font-mono">
            7 action types · all components clipped to [0.0, 1.0] · always returns at least one action
          </p>
        </div>
      </section>

      {/* ── Benchmark ────────────────────────────────────────────────────────── */}
      <section className="py-16 px-6 bg-gray-900">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-black text-white mb-3 tracking-tight">What&apos;s Validated vs. Scaffolded</h2>
          <p className="text-gray-400 font-medium mb-10">
            Honest accounting. What is pinned by tests. What is implemented but not cohort-validated. What is scaffolded. No conflation.
          </p>
          <BenchmarkPanel />
        </div>
      </section>

      {/* ── Sources ──────────────────────────────────────────────────────────── */}
      <section className="py-16 px-6 bg-white border-t border-gray-100">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-black text-gray-900 mb-8 tracking-tight">Every Number Has a Source</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {[
              { label: "PhenoAge Gompertz Model", source: "Levine et al. 2018", ref: "PMID 29676998", detail: "Coefficients from Supplementary Table S1. HR=1.08/yr acceleration." },
              { label: "Hallmark Framework", source: "López-Otín et al. 2023", ref: "PMID 36599349", detail: "9 hallmarks. 6 implemented. Biomarker associations curated from literature." },
              { label: "ASCVD Pooled Cohort Equations", source: "Goff et al. 2014", ref: "PMID 24222018", detail: "4 sex/race strata. ACC/AHA guideline formula." },
              { label: "APOE Diplotype", source: "Corder et al. 1993", ref: "PMID 8346443", detail: "rs429358 + rs7412 → e2/e2 through e4/e4. e4/e4 = 8–12× AD risk." },
              { label: "MTHFR Enzyme Activity", source: "Frosst et al. 1995", ref: "PMID 8554066", detail: "C677T: CC=100%, CT=65%, TT=30% activity." },
              { label: "MR Evidence — omega_3", source: "Fabian 2025", ref: "DOI 10.1186/s40246-025-00756-3", detail: "Oily fish → PhenoAge acceleration IVW p=0.0086." },
              { label: "MR Evidence — vitamin_d3", source: "Hagenbeek 2022", ref: "PMID 36055464", detail: "Genetically predicted 25-OHD → lower GrimAge. IVW p=0.04." },
              { label: "BRCA Risk Estimates", source: "Kuchenbaecker et al. 2017", ref: "PMID 28632866", detail: "BRCA1: 50–80% lifetime breast. BRCA2: 40–70% breast." },
            ].map((s) => (
              <div key={s.label} className="flex items-start gap-3 p-4 rounded-xl border border-gray-100 bg-gray-50">
                <div className="flex-1">
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-sm font-bold text-gray-900">{s.label}</span>
                    <span className="text-[10px] font-mono text-gray-400 shrink-0">{s.ref}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">{s.source}</div>
                  <div className="text-xs text-gray-500 mt-1 leading-relaxed">{s.detail}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Hard Limits ──────────────────────────────────────────────────────── */}
      <section className="py-16 px-6 bg-gray-50 border-y border-gray-100">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-black text-gray-900 mb-2 tracking-tight">Hard Limits</h2>
          <p className="text-gray-500 font-medium mb-8">Current boundaries. Not roadmap items.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {[
              { title: "No methylation array analysis", detail: "Epigenetic clocks accept pre-computed values only. Requires external service (e.g. TruDiagnostic)." },
              { title: "No telomere assay", detail: "Telomere attrition is not in the shippable scorer. LTL accepted as supplementary but not scored numerically." },
              { title: "No body composition", detail: "DEXA / body composition endpoint has no scoring logic in current release." },
              { title: "No LangGraph without install", detail: "Multi-agent pipeline returns HTTP 503 if langgraph≥0.2.0 is not installed." },
              { title: "No persistent run registry", detail: "Pipeline status uses in-memory TTL registry (1 hour). Not persistent across restarts." },
              { title: "Research Use Only", detail: "Not a medical device. PhenoAge labels are UX thresholds, not clinical classifications." },
            ].map((item) => (
              <div key={item.title} className="flex items-start gap-3 bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                <div className="w-5 h-5 rounded-full bg-gray-200 flex items-center justify-center shrink-0 mt-0.5">
                  <svg className="w-3 h-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 text-sm mb-0.5">{item.title}</h3>
                  <p className="text-xs text-gray-500 leading-relaxed">{item.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────────────────── */}
      <section className="py-20 px-6 bg-white">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-black text-gray-900 mb-4 tracking-tight">Run It on Real Patient Data</h2>
          <p className="text-gray-500 font-medium mb-8">
            Five pre-loaded scenarios. Real API calls. Each one stress-tests a different capability.
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
