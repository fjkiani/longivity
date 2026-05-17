"use client";

import { useState } from "react";
import ScenarioCard, { Scenario } from "./ScenarioCard";
import PipelineOutput from "./PipelineOutput";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface DemoRunnerProps {
  scenarios: Scenario[];
}

export default function DemoRunner({ scenarios }: DemoRunnerProps) {
  const [selected, setSelected] = useState<Scenario>(scenarios[0]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showRaw, setShowRaw] = useState(false);
  const [hasRun, setHasRun] = useState(false);

  function selectScenario(s: Scenario) {
    setSelected(s);
    setResult(null);
    setError(null);
    setHasRun(false);
    setShowRaw(false);
  }

  async function runScenario() {
    setLoading(true);
    setError(null);
    setResult(null);
    setHasRun(true);
    try {
      const endpoint = selected.endpoint === "full_assessment"
        ? "/api/v1/longevity/full_assessment"
        : "/api/v1/longevity/assessment_level0";
      const resp = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(selected.payload),
      });
      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(`API error ${resp.status}: ${text.slice(0, 200)}`);
      }
      const data = await resp.json();
      setResult(data);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
      {/* Left: Scenario selector */}
      <div className="lg:col-span-2 space-y-3">
        <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-4">Select a Scenario</p>
        {scenarios.map((s) => (
          <ScenarioCard
            key={s.id}
            scenario={s}
            selected={selected.id === s.id}
            onSelect={() => selectScenario(s)}
          />
        ))}
      </div>

      {/* Right: Run + Output */}
      <div className="lg:col-span-3 space-y-6">
        {/* Scenario detail */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-start justify-between gap-4 mb-4">
            <div>
              <h3 className="font-black text-gray-900 text-lg">{selected.title}</h3>
              <p className="text-sm text-gray-500 mt-1 leading-relaxed">{selected.clinicalStory}</p>
            </div>
            <div className="shrink-0 text-right">
              <div className="text-xs text-gray-400 font-medium">Age {selected.age} · {selected.sex}</div>
              <div className="text-xs text-gray-400 font-mono mt-0.5">{selected.endpoint}</div>
            </div>
          </div>

          {/* Expected findings */}
          <div className="bg-gray-50 rounded-xl p-4 mb-4">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Expected Findings</p>
            <ul className="space-y-1">
              {selected.expectedFindings.map((f, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-gray-600">
                  <span className="text-gray-400 mt-0.5 shrink-0">·</span>
                  {f}
                </li>
              ))}
            </ul>
          </div>

          {/* Payload preview */}
          <details className="mb-4">
            <summary className="text-xs font-medium text-gray-500 cursor-pointer hover:text-gray-700">
              View API payload →
            </summary>
            <pre className="mt-2 bg-gray-950 text-emerald-400 rounded-xl p-4 text-xs overflow-auto max-h-48 font-mono">
              {JSON.stringify(selected.payload, null, 2)}
            </pre>
          </details>

          <button
            onClick={runScenario}
            disabled={loading}
            className="w-full bg-gray-900 hover:bg-black disabled:opacity-50 text-white font-black py-3 rounded-xl text-sm transition-all shadow-sm hover:-translate-y-0.5 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Running six transformations...
              </>
            ) : (
              <>
                <span>▶</span>
                Run Scenario {selected.number}
              </>
            )}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-5">
            <p className="text-sm font-bold text-red-800 mb-1">API Error</p>
            <p className="text-xs text-red-700 font-mono">{error}</p>
            <p className="text-xs text-red-500 mt-2">
              Make sure the Longivity API is running at <span className="font-mono">{API_BASE}</span>
            </p>
          </div>
        )}

        {/* Not yet run */}
        {!hasRun && !loading && (
          <div className="bg-gray-50 border border-dashed border-gray-300 rounded-2xl p-10 text-center">
            <div className="text-3xl mb-3">▶</div>
            <p className="text-sm font-bold text-gray-500">Click &ldquo;Run Scenario&rdquo; to call the real API</p>
            <p className="text-xs text-gray-400 mt-1">Six transformations · Real output · No mocked data</p>
          </div>
        )}

        {/* Output */}
        {result && (
          <PipelineOutput
            data={result as unknown as Parameters<typeof PipelineOutput>[0]["data"]}
            rawJson={JSON.stringify(result, null, 2)}
            showRaw={showRaw}
            onToggleRaw={() => setShowRaw((v) => !v)}
          />
        )}
      </div>
    </div>
  );
}
