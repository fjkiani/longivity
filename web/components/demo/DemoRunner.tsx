"use client";

import { useState } from "react";
import ScenarioCard, { Scenario } from "./ScenarioCard";
import PipelineOutput from "./PipelineOutput";
import scenarioOutputs from "./scenario_outputs.json";

// Hardcoded outputs captured from production API 2026-05-17
const SCENARIO_OUTPUTS = scenarioOutputs as Record<string, unknown>;

interface DemoRunnerProps {
  scenarios: Scenario[];
}

export default function DemoRunner({ scenarios }: DemoRunnerProps) {
  const [selected, setSelected] = useState<Scenario>(scenarios[0]);
  const [showRaw, setShowRaw] = useState(false);

  const result = SCENARIO_OUTPUTS[selected.id] as Record<string, unknown> | null;

  function selectScenario(s: Scenario) {
    setSelected(s);
    setShowRaw(false);
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

      {/* Right: Detail + Output */}
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

          {/* Stress test */}
          <div className="bg-gray-50 rounded-xl p-4 mb-4">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Stress Test</p>
            <p className="text-xs text-gray-600 leading-relaxed">{selected.stressTest}</p>
          </div>

          {/* Expected findings */}
          <div className="bg-gray-50 rounded-xl p-4 mb-4">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Expected Findings</p>
            <ul className="space-y-1">
              {selected.expectedFindings.map((f, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-gray-600">
                  <span className="text-emerald-500 mt-0.5 shrink-0">✓</span>
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

          {/* Live capture badge */}
          <div className="flex items-center gap-2 text-xs text-gray-400 border-t border-gray-100 pt-4">
            <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0"></span>
            <span>
              Output captured live from{" "}
              <span className="font-mono text-gray-500">longivity-backend.onrender.com</span>{" "}
              · 2026-05-17
            </span>
          </div>
        </div>

        {/* Output — always shown, no button needed */}
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
