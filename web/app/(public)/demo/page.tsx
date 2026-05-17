import DemoRunner from "@/components/demo/DemoRunner";
import { SCENARIOS } from "@/components/demo/scenarios";

export const metadata = {
  title: "Demo — Longivity",
  description: "Five pre-loaded patient scenarios. Real API calls. No mocked data. Each scenario stress-tests a different capability of the Longivity intelligence pipeline.",
};

export default function DemoPage() {
  return (
    <div className="bg-white text-gray-900">

      {/* Hero */}
      <section className="pt-36 pb-12 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6 mb-10">
            <div>
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm font-bold mb-6">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                Live Demo · Real API · No Mocked Data
              </div>
              <h1 className="text-4xl md:text-5xl font-black text-gray-900 leading-tight tracking-tight mb-4">
                Five Scenarios.<br />
                Five Stress Tests.
              </h1>
              <p className="text-lg text-gray-600 font-medium max-w-2xl leading-relaxed">
                Each scenario is a real patient archetype designed to probe a different capability. Select one, read the clinical story, then run it against the live API. The output is the actual system response — not a mockup.
              </p>
            </div>
            <div className="shrink-0 bg-gray-50 border border-gray-200 rounded-2xl p-5 text-sm space-y-2 min-w-[220px]">
              <div className="flex items-center justify-between">
                <span className="text-gray-500 font-medium">API endpoint</span>
                <span className="font-mono text-xs text-gray-700">assessment_level0</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-500 font-medium">Auth required</span>
                <span className="text-emerald-600 font-bold text-xs">None</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-500 font-medium">Transformations</span>
                <span className="font-bold text-gray-900 text-xs">6</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-500 font-medium">Tests passing</span>
                <span className="font-bold text-emerald-600 text-xs">218 / 218</span>
              </div>
            </div>
          </div>

          {/* Scenario legend */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-10">
            {SCENARIOS.map((s) => (
              <div key={s.id} className="bg-gray-50 border border-gray-200 rounded-xl p-3 text-center">
                <div className="text-xs font-black text-gray-400 mb-1">#{s.number}</div>
                <div className="text-xs font-bold text-gray-700 leading-tight">{s.title}</div>
                <div className={`text-[10px] font-bold mt-1 px-2 py-0.5 rounded-full inline-block ${s.badgeColor}`}>{s.subtitle}</div>
              </div>
            ))}
          </div>

          {/* Demo runner */}
          <DemoRunner scenarios={SCENARIOS} />
        </div>
      </section>

      {/* Footer note */}
      <section className="py-10 px-6 border-t border-gray-100">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <p className="text-sm font-bold text-gray-700 mb-1">What you&apos;re seeing</p>
            <p className="text-xs text-gray-500 max-w-xl leading-relaxed">
              The output is the raw API response from <code className="font-mono bg-gray-100 px-1 rounded">POST /api/v1/longevity/assessment_level0</code> or <code className="font-mono bg-gray-100 px-1 rounded">full_assessment</code>. No post-processing. No UI-layer fabrication. The structured view parses the same JSON you see in the raw toggle.
            </p>
          </div>
          <div className="flex gap-3 shrink-0">
            <a href="/how-it-works" className="text-sm font-bold text-gray-600 hover:text-gray-900 border border-gray-200 rounded-xl px-4 py-2 transition-colors">
              How It Works →
            </a>
            <a href="/login" className="text-sm font-bold text-white bg-gray-900 hover:bg-black rounded-xl px-4 py-2 transition-colors">
              Enter Dashboard →
            </a>
          </div>
        </div>
        <div className="max-w-6xl mx-auto mt-6">
          <p className="text-xs text-gray-400">
            Research Use Only (RUO). Longivity is not a medical device. PhenoAge acceleration labels are CrisPRO UX thresholds, not PhenoAge classifications. Do not use for clinical decisions without a qualified clinician.
          </p>
        </div>
      </section>

    </div>
  );
}
