"use client";

import { useState, useCallback } from "react";
import type { Scenario } from "./ScenarioCard";
import PipelineOutput from "./PipelineOutput";
import SCENARIO_OUTPUTS from "./scenario_outputs.json";

interface DemoRunnerProps {
  scenarios: Scenario[];
}

const ACCENT: Record<string, { pill: string; num: string; border: string; bg: string }> = {
  rose:    { pill: "bg-rose-100 text-rose-700 border-rose-200",    num: "bg-rose-500 text-white",    border: "border-rose-400",    bg: "bg-rose-50" },
  violet:  { pill: "bg-violet-100 text-violet-700 border-violet-200", num: "bg-violet-500 text-white", border: "border-violet-400", bg: "bg-violet-50" },
  orange:  { pill: "bg-orange-100 text-orange-700 border-orange-200", num: "bg-orange-500 text-white", border: "border-orange-400", bg: "bg-orange-50" },
  sky:     { pill: "bg-sky-100 text-sky-700 border-sky-200",       num: "bg-sky-500 text-white",     border: "border-sky-400",     bg: "bg-sky-50" },
  emerald: { pill: "bg-emerald-100 text-emerald-700 border-emerald-200", num: "bg-emerald-500 text-white", border: "border-emerald-400", bg: "bg-emerald-50" },
};

// API base — reads from env at build time, falls back to Render deployment
const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ??
  "https://longevity-backend.onrender.com";

export default function DemoRunner({ scenarios }: DemoRunnerProps) {
  const [selected, setSelected] = useState<Scenario>(scenarios[0]);
  const [showRaw, setShowRaw] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(
    // Pre-populate with static output so the demo is never blank on first load
    ((SCENARIO_OUTPUTS as Record<string, unknown>)[scenarios[0].id] ?? null) as Record<string, unknown> | null
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLive, setIsLive] = useState(false);
  const [lastRunAt, setLastRunAt] = useState<string | null>(null);

  const runScenario = useCallback(async (scenario: Scenario) => {
    setLoading(true);
    setError(null);
    setIsLive(false);

    try {
      const response = await fetch(`${API_BASE}/api/v1/patients/demo/assessment`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Demo-Mode": "true",
        },
        body: JSON.stringify(scenario.payload),
        signal: AbortSignal.timeout(30_000), // 30s timeout
      });

      if (!response.ok) {
        throw new Error(`API returned ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
      setIsLive(true);
      setLastRunAt(new Date().toISOString());
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      console.warn("Live API call failed, falling back to static output:", msg);
      setError(`Live API unavailable — showing cached output. (${msg})`);
      // Graceful fallback to static JSON
      const staticOutput = (SCENARIO_OUTPUTS as Record<string, unknown>)[scenario.id] ?? null;
      setResult(staticOutput as Record<string, unknown> | null);
      setIsLive(false);
      setLastRunAt(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSelectScenario = (s: Scenario) => {
    setSelected(s);
    setShowRaw(false);
    // Load static output immediately, then kick off live fetch
    const staticOutput = (SCENARIO_OUTPUTS as Record<string, unknown>)[s.id] ?? null;
    setResult(staticOutput as Record<string, unknown> | null);
    setIsLive(false);
    setError(null);
    runScenario(s);
  };

  const ac = ACCENT[selected.accentColor] || ACCENT.rose;

  return (
    <div className="space-y-8">
      {/* Scenario selector — horizontal cards */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
        {scenarios.map((s) => {
          const a = ACCENT[s.accentColor] || ACCENT.rose;
          const isActive = selected.id === s.id;
          return (
            <button
              key={s.id}
              onClick={() => handleSelectScenario(s)}
              className={`rounded-2xl border-2 p-4 text-left transition-all hover:shadow-md ${
                isActive ? `${a.border} ${a.bg} shadow-md` : "border-gray-200 bg-white hover:border-gray-300"
              }`}
            >
              <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-black text-sm mb-2 ${
                isActive ? a.num : "bg-gray-100 text-gray-500"
              }`}>
                {s.number}
              </div>
              <div className="font-black text-gray-900 text-sm leading-tight mb-1">{s.title}</div>
              <div className={`text-[11px] font-bold px-2 py-0.5 rounded-full inline-block border ${a.pill}`}>
                {s.subtitle}
              </div>
            </button>
          );
        })}
      </div>

      {/* Main panel */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left: clinical brief */}
        <div className="lg:col-span-2 space-y-4">
          {/* Patient card */}
          <div className={`rounded-2xl border-2 ${ac.border} ${ac.bg} p-5`}>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-black text-gray-500 uppercase tracking-wider">Patient Brief</span>
              <span className="text-xs font-mono text-gray-500">Age {selected.age} · {selected.sex}</span>
            </div>
            <h2 className="text-xl font-black text-gray-900 mb-1">{selected.title}</h2>
            <p className="text-sm font-bold text-gray-600 mb-3">{selected.subtitle}</p>
            <p className="text-sm text-gray-700 leading-relaxed">{selected.clinicalStory}</p>
          </div>

          {/* Stress test */}
          <div className="rounded-2xl border border-gray-200 bg-white p-5">
            <div className="text-xs font-black text-gray-400 uppercase tracking-wider mb-2">What We're Testing</div>
            <p className="text-sm font-semibold text-gray-800 leading-relaxed">{selected.stressTest}</p>
          </div>

          {/* Expected findings */}
          <div className="rounded-2xl border border-gray-200 bg-white p-5">
            <div className="text-xs font-black text-gray-400 uppercase tracking-wider mb-3">Expected Findings</div>
            <ul className="space-y-2">
              {selected.expectedFindings.map((f, i) => (
                <li key={i} className="flex items-start gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center shrink-0 mt-0.5">
                    <svg className="w-3 h-3 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                  </span>
                  <span className="text-sm text-gray-700 leading-snug">{f}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* API payload */}
          <details className="rounded-2xl border border-gray-200 bg-white overflow-hidden">
            <summary className="px-5 py-3 text-sm font-bold text-gray-600 cursor-pointer hover:text-gray-900 hover:bg-gray-50 transition-colors">
              View API payload →
            </summary>
            <pre className="bg-gray-950 text-emerald-400 px-5 py-4 text-xs overflow-auto max-h-48 font-mono leading-relaxed">
              {JSON.stringify(selected.payload, null, 2)}
            </pre>
          </details>

          {/* Status bar */}
          <div className="flex items-center gap-2 text-xs text-gray-400 px-1">
            {loading ? (
              <>
                <span className="w-2 h-2 rounded-full bg-yellow-400 shrink-0 animate-pulse" />
                <span>Calling live API...</span>
              </>
            ) : isLive ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
                <span>
                  Live output from{" "}
                  <span className="font-mono text-gray-500">longevity-backend.onrender.com</span>
                  {lastRunAt && (
                    <> · {new Date(lastRunAt).toLocaleString()}</>
                  )}
                </span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-gray-400 shrink-0" />
                <span>Cached output · <button onClick={() => runScenario(selected)} className="underline hover:text-gray-600">Run live</button></span>
              </>
            )}
          </div>

          {/* Error banner */}
          {error && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-700">
              {error}
            </div>
          )}
        </div>

        {/* Right: pipeline output */}
        <div className="lg:col-span-3">
          {loading && (
            <div className="rounded-2xl border border-gray-200 bg-gray-50 p-12 text-center">
              <div className="inline-block w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-sm text-gray-500 font-medium">Running live assessment...</p>
            </div>
          )}
          {!loading && result ? (
            <PipelineOutput
              data={result as unknown as Parameters<typeof PipelineOutput>[0]["data"]}
              rawJson={JSON.stringify(result, null, 2)}
              showRaw={showRaw}
              onToggleRaw={() => setShowRaw((v) => !v)}
            />
          ) : !loading && (
            <div className="rounded-2xl border border-gray-200 bg-gray-50 p-12 text-center text-gray-400">
              No output captured for this scenario.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
