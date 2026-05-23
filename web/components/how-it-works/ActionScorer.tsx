"use client";
import { useState, useMemo } from "react";

const WEIGHTS = {
  data_urgency:        0.30,
  phenoage_urgency:    0.25,
  escalation_severity: 0.25,
  time_decay:          0.10,
  hallmark_signal:     0.10,
};

const ACTIONS = [
  { id: "order_baseline_panel",    label: "Order Baseline Panel",    states: ["NEW", "DATA_INCOMPLETE"] },
  { id: "run_assessment",          label: "Run Assessment",          states: ["ASSESSMENT_PENDING"] },
  { id: "review_test_order",       label: "Review Test Order",       states: ["ORDER_PENDING"] },
  { id: "review_compounds",        label: "Review Compounds",        states: ["COMPOUND_CANDIDATE"] },
  { id: "schedule_followup",       label: "Schedule Follow-up",      states: ["MONITORING"] },
  { id: "review_longitudinal",     label: "Review Longitudinal",     states: ["MONITORING", "COMPOUND_CANDIDATE"] },
  { id: "update_protocol",         label: "Update Protocol",         states: ["MONITORING"] },
];

const PRESETS = [
  {
    label: "New patient, no data",
    state: "NEW",
    vals: { data_urgency: 0.9, phenoage_urgency: 0.0, escalation_severity: 0.0, time_decay: 0.2, hallmark_signal: 0.0 },
  },
  {
    label: "Accelerated aging, escalation",
    state: "ORDER_PENDING",
    vals: { data_urgency: 0.3, phenoage_urgency: 0.95, escalation_severity: 0.85, time_decay: 0.6, hallmark_signal: 0.8 },
  },
  {
    label: "Monitoring, stable",
    state: "MONITORING",
    vals: { data_urgency: 0.1, phenoage_urgency: 0.3, escalation_severity: 0.0, time_decay: 0.4, hallmark_signal: 0.3 },
  },
];

export default function ActionScorer() {
  const [state, setState] = useState("ORDER_PENDING");
  const [vals, setVals] = useState({ data_urgency: 0.3, phenoage_urgency: 0.95, escalation_severity: 0.85, time_decay: 0.6, hallmark_signal: 0.8 });
  const [activePreset, setActivePreset] = useState(1);

  const score = useMemo(() => {
    return Object.entries(WEIGHTS).reduce((sum, [k, w]) => sum + w * (vals[k as keyof typeof vals] ?? 0), 0);
  }, [vals]);

  const validActions = ACTIONS.filter((a) => a.states.includes(state));
  const topAction = validActions[0];

  function applyPreset(i: number) {
    setActivePreset(i);
    setState(PRESETS[i].state);
    setVals({ ...PRESETS[i].vals });
  }

  const scoreColor = score > 0.7 ? "text-red-600" : score > 0.4 ? "text-amber-600" : "text-emerald-600";
  const scoreBg = score > 0.7 ? "bg-red-50 border-red-200" : score > 0.4 ? "bg-amber-50 border-amber-200" : "bg-emerald-50 border-emerald-200";

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Presets */}
      <div className="flex border-b border-gray-100 bg-gray-50">
        {PRESETS.map((p, i) => (
          <button
            key={p.label}
            onClick={() => applyPreset(i)}
            className={`flex-1 py-2.5 text-xs font-bold transition-all ${
              activePreset === i ? "bg-white text-gray-900 border-b-2 border-gray-900" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-0 divide-y md:divide-y-0 md:divide-x divide-gray-100">
        {/* Left: sliders */}
        <div className="p-5">
          <div className="mb-4">
            <label className="text-xs font-bold text-gray-500 uppercase tracking-wider block mb-2">Patient State</label>
            <div className="flex flex-wrap gap-1.5">
              {["NEW","DATA_INCOMPLETE","ASSESSMENT_PENDING","ORDER_PENDING","COMPOUND_CANDIDATE","MONITORING"].map((s) => (
                <button
                  key={s}
                  onClick={() => { setState(s); setActivePreset(-1); }}
                  className={`px-2 py-1 rounded-lg text-[10px] font-bold border transition-all ${
                    state === s ? "bg-gray-900 text-white border-gray-900" : "bg-gray-50 text-gray-600 border-gray-200 hover:border-gray-400"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            {Object.entries(WEIGHTS).map(([k, w]) => (
              <div key={k}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-gray-600">{k.replace(/_/g, " ")}</span>
                  <span className="text-[10px] font-mono text-gray-400">weight {w}</span>
                </div>
                <div className="flex items-center gap-3">
                  <input
                    type="range" min={0} max={1} step={0.01}
                    value={vals[k as keyof typeof vals]}
                    onChange={(e) => {
                      setActivePreset(-1);
                      setVals((v) => ({ ...v, [k]: parseFloat(e.target.value) }));
                    }}
                    className="flex-1 accent-gray-700 h-1.5"
                  />
                  <span className="font-mono text-xs text-gray-700 w-8 text-right tabular-nums">
                    {vals[k as keyof typeof vals].toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: result */}
        <div className="p-5 flex flex-col gap-4">
          {/* Score */}
          <div className={`rounded-xl border p-4 ${scoreBg}`}>
            <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1">Urgency Score</div>
            <div className={`text-5xl font-black tabular-nums ${scoreColor}`}>
              {score.toFixed(3)}
            </div>
            <div className="mt-2 text-xs text-gray-500">
              = {Object.entries(WEIGHTS).map(([k, w]) =>
                `${w}×${vals[k as keyof typeof vals].toFixed(2)}`
              ).join(" + ")}
            </div>
          </div>

          {/* Formula */}
          <div className="bg-gray-50 rounded-xl p-3 border border-gray-100 font-mono text-xs space-y-0.5">
            {Object.entries(WEIGHTS).map(([k, w]) => (
              <div key={k} className="flex items-center gap-2">
                <span className="text-gray-400 w-4">{k === Object.keys(WEIGHTS)[0] ? "=" : "+"}</span>
                <span className="text-rose-600 font-bold">{w}</span>
                <span className="text-gray-400">×</span>
                <span className="text-gray-700">{k.replace(/_/g, "_")}</span>
                <span className="text-gray-400 ml-auto">= {(w * vals[k as keyof typeof vals]).toFixed(3)}</span>
              </div>
            ))}
          </div>

          {/* Valid actions */}
          <div>
            <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">
              Valid Actions in {state}
            </div>
            <div className="space-y-1.5">
              {validActions.map((a, i) => (
                <div key={a.id} className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium ${
                  i === 0 ? "bg-gray-900 text-white" : "bg-gray-50 border border-gray-200 text-gray-600"
                }`}>
                  {i === 0 && <span className="text-[10px] font-bold bg-white text-gray-900 px-1.5 py-0.5 rounded">TOP</span>}
                  {a.label}
                </div>
              ))}
              {validActions.length === 0 && (
                <div className="text-xs text-gray-400 italic">No valid actions for this state</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
