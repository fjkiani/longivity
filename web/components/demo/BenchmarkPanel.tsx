export default function BenchmarkPanel() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

      {/* Validated */}
      <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center">
            <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="font-black text-emerald-800 text-sm">Validated by Golden Snapshots</h3>
        </div>
        <ul className="space-y-3 text-xs text-emerald-900">
          <li className="flex items-start gap-2">
            <span className="text-emerald-500 mt-0.5 shrink-0 font-bold">·</span>
            <span><strong>PhenoAge formula</strong> — Healthy 45yo → ~34yr (pinned range 28–42yr). Accelerated 58yo → 77.02yr (pinned range 60–85yr). Deterministic to &lt;0.001yr. Source: PMID 29676998.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-emerald-500 mt-0.5 shrink-0 font-bold">·</span>
            <span><strong>ASCVD PCE</strong> — 4 sex/race strata. Risk value in [0, 100]% range verified. Source: PMID 24222018.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-emerald-500 mt-0.5 shrink-0 font-bold">·</span>
            <span><strong>APOE diplotype</strong> — rs429358 + rs7412 → e2/e2 through e4/e4. e4/e4 = 8–12× AD risk. Source: PMID 8346443.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-emerald-500 mt-0.5 shrink-0 font-bold">·</span>
            <span><strong>MR evidence tiers</strong> — omega_3 (IVW p=0.0086, PhenoAge), vitamin_d3 (IVW p=0.04, GrimAge), folate (IVW p=0.03, PhenoAge). Source: Fabian 2025, DOI 10.1186/s40246-025-00756-3.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-emerald-500 mt-0.5 shrink-0 font-bold">·</span>
            <span><strong>State machine transitions</strong> — all 6 states + transition rules unit-tested. Deterministic.</span>
          </li>
        </ul>
      </div>

      {/* Implemented, not cohort-validated */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-6 h-6 rounded-full bg-yellow-500 flex items-center justify-center">
            <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01" />
            </svg>
          </div>
          <h3 className="font-black text-yellow-800 text-sm">Implemented, Not Cohort-Validated</h3>
        </div>
        <ul className="space-y-3 text-xs text-yellow-900">
          <li className="flex items-start gap-2">
            <span className="text-yellow-500 mt-0.5 shrink-0 font-bold">·</span>
            <span><strong>Hallmark-to-biomarker associations</strong> — curated from published literature (PMID 36599349). Not validated against a clinical cohort. Associations are directionally correct but magnitudes are not outcome-calibrated.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-yellow-500 mt-0.5 shrink-0 font-bold">·</span>
            <span><strong>Compound relevance scoring</strong> — PMID-verified links where flagged. Scoring formula (weighted hallmark vulnerability) not outcome-validated.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-yellow-500 mt-0.5 shrink-0 font-bold">·</span>
            <span><strong>Wearable hallmark mapping</strong> — HRV, VO2max, sleep thresholds from published sources. Not validated against longevity outcomes.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-yellow-500 mt-0.5 shrink-0 font-bold">·</span>
            <span><strong>27-SNP PRS</strong> — Timmers 2019 weights correctly implemented. Partial genotype approximation not externally validated.</span>
          </li>
        </ul>
      </div>

      {/* Scaffolded */}
      <div className="bg-gray-50 border border-gray-200 rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-6 h-6 rounded-full bg-gray-400 flex items-center justify-center">
            <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <h3 className="font-black text-gray-600 text-sm">Scaffolded / Environment-Dependent</h3>
        </div>
        <ul className="space-y-3 text-xs text-gray-700">
          <li className="flex items-start gap-2">
            <span className="text-gray-400 mt-0.5 shrink-0 font-bold">·</span>
            <span><strong>LangGraph multi-agent pipeline</strong> — returns 503 if langgraph≥0.2.0 not installed. Tests skip gracefully.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-gray-400 mt-0.5 shrink-0 font-bold">·</span>
            <span><strong>Epigenetic clocks</strong> — accepts pre-computed values only (GrimAge, DunedinPACE, Horvath, Hannum). Does not run methylation array analysis. Requires external service.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-gray-400 mt-0.5 shrink-0 font-bold">·</span>
            <span><strong>NHANES validation</strong> — script exists and is importable. Actual validation against NHANES III/IV data not yet run.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-gray-400 mt-0.5 shrink-0 font-bold">·</span>
            <span><strong>In-memory run registry</strong> — TTL-evicted (1hr), not persistent across restarts.</span>
          </li>
        </ul>
      </div>

    </div>
  );
}
