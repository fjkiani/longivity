import DemoRunner from "@/components/demo/DemoRunner";
import { SCENARIOS } from "@/components/demo/scenarios";

export const metadata = {
  title: "Demo — Longevity",
  description: "Five patient scenarios. Real API output. One ranked action per patient. See how Longevity works for longevity clinicians.",
};

export default function DemoPage() {
  return (
    <div className="bg-white text-gray-900">

      {/* Hero */}
      <section className="pt-36 pb-12 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-8 mb-12">
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm font-bold mb-6">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                Live Output · Real API · No Mocked Data
              </div>
              <h1 className="text-4xl md:text-5xl font-black text-gray-900 leading-tight tracking-tight mb-4">
                Five Patients.<br />
                One Ranked Action Each.
              </h1>
              <p className="text-lg text-gray-700 font-medium leading-relaxed">
                Each scenario is a real patient archetype designed to stress-test a different capability.
                Select a patient, read the clinical story, then see the full pipeline output —
                biological age, active hallmarks, genetic risk, and the single most important action to take next.
              </p>
            </div>

            <div className="shrink-0 bg-gray-50 border border-gray-200 rounded-2xl p-5 space-y-3 min-w-[220px]">
              <div className="text-xs font-black text-gray-400 uppercase tracking-wider mb-2">Pipeline Stats</div>
              {[
                ["API endpoint", "assessment_level0"],
                ["Auth required", "None"],
                ["Transformations", "6"],
                ["Tests passing", "218 / 218"],
              ].map(([label, val]) => (
                <div key={label} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 font-medium">{label}</span>
                  <span className={`text-sm font-bold ${val === "None" || val === "218 / 218" ? "text-emerald-700" : "text-gray-900"} font-mono`}>{val}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Demo runner */}
          <DemoRunner scenarios={SCENARIOS} />
        </div>
      </section>

      {/* Footer */}
      <section className="py-12 px-6 border-t border-gray-100 bg-gray-50">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div>
            <p className="text-sm font-black text-gray-800 mb-1">What you're seeing</p>
            <p className="text-sm text-gray-600 max-w-xl leading-relaxed">
              The output is the raw API response from{" "}
              <code className="font-mono bg-gray-200 text-gray-800 px-1.5 py-0.5 rounded text-xs">POST /api/v1/longevity/assessment_level0</code>.
              No post-processing. No UI-layer fabrication. The structured view parses the same JSON you see in the raw toggle.
            </p>
          </div>
          <div className="flex gap-3 shrink-0">
            <a href="/how-it-works" className="text-sm font-bold text-gray-700 hover:text-gray-900 border border-gray-300 rounded-xl px-4 py-2.5 transition-colors hover:bg-white">
              How It Works →
            </a>
            <a href="/demo-login" className="text-sm font-bold text-white bg-gray-900 hover:bg-black rounded-xl px-4 py-2.5 transition-colors">
              Try Live System →
            </a>
          </div>
        </div>
        <div className="max-w-6xl mx-auto mt-6">
          <p className="text-xs text-gray-500">
            Research Use Only (RUO). Longevity is not a medical device. PhenoAge acceleration labels are CrisPRO UX thresholds, not PhenoAge classifications. Do not use for clinical decisions without a qualified clinician.
          </p>
        </div>
      </section>

    </div>
  );
}
