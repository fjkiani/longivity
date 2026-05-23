"use client";
import { useState, useMemo } from "react";

// Levine 2018 Gompertz PH coefficients (PMID 29676998, Supplementary Table S1)
const WEIGHTS: Record<string, number> = {
  albumin:      -0.0336,
  creatinine:    0.0095,
  glucose:       0.1953,
  crp_log:       0.0954,
  lymphocyte:   -0.0120,
  mcv:           0.0268,
  rdw:           0.3306,
  alk_phos:      0.00188,
  wbc:           0.0554,
};
const INTERCEPT = -19.9067;
const AGE_WEIGHT = 0.0804;
const GAMMA = 0.0076927;
const T = 10;
const OFFSET = 141.50225;
const DENOM_COEF = 0.00553;
const LN_NUM_COEF = 0.0076927;

const DEFAULTS: Record<string, number> = {
  albumin: 45,       // g/L
  creatinine: 0.9,   // mg/dL
  glucose: 5.27,     // mmol/L
  crp_log: -2.12,    // ln(mg/dL)
  lymphocyte: 28,    // %
  mcv: 90,           // fL
  rdw: 13.5,         // %
  alk_phos: 70,      // U/L
  wbc: 6.5,          // 10^3/µL
};

const LABELS: Record<string, { label: string; unit: string; min: number; max: number; step: number }> = {
  albumin:    { label: "Albumin",       unit: "g/L",       min: 20,   max: 60,   step: 0.5 },
  creatinine: { label: "Creatinine",    unit: "mg/dL",     min: 0.4,  max: 4,    step: 0.05 },
  glucose:    { label: "Glucose",       unit: "mmol/L",    min: 3,    max: 15,   step: 0.1 },
  crp_log:    { label: "ln(CRP)",       unit: "ln(mg/dL)", min: -4,   max: 3,    step: 0.1 },
  lymphocyte: { label: "Lymphocyte %",  unit: "%",         min: 5,    max: 60,   step: 0.5 },
  mcv:        { label: "MCV",           unit: "fL",        min: 70,   max: 110,  step: 0.5 },
  rdw:        { label: "RDW",           unit: "%",         min: 10,   max: 20,   step: 0.1 },
  alk_phos:   { label: "Alk Phos",      unit: "U/L",       min: 20,   max: 300,  step: 1 },
  wbc:        { label: "WBC",           unit: "10³/µL",    min: 2,    max: 15,   step: 0.1 },
};

function computePhenoAge(vals: Record<string, number>, age: number): number | null {
  const keys = Object.keys(WEIGHTS);
  const missing = keys.filter((k) => vals[k] == null);
  if (missing.length > 0) return null;

  const xb = INTERCEPT + AGE_WEIGHT * age + keys.reduce((sum, k) => sum + WEIGHTS[k] * vals[k], 0);
  const m = 1 - Math.exp(-Math.exp(xb) * (Math.exp(GAMMA * T) - 1) / GAMMA);
  if (m <= 0 || m >= 1) return null;
  const phenoage = OFFSET + Math.log(-Math.log(1 - m) / DENOM_COEF) / LN_NUM_COEF;
  return +phenoage.toFixed(1);
}

const PRESETS = [
  { label: "Healthy 45yo", age: 45, vals: { albumin: 47, creatinine: 0.85, glucose: 4.9, crp_log: -2.5, lymphocyte: 32, mcv: 89, rdw: 12.8, alk_phos: 55, wbc: 5.5 } },
  { label: "Accelerated 58yo", age: 58, vals: { albumin: 38, creatinine: 1.2, glucose: 6.8, crp_log: 0.4, lymphocyte: 18, mcv: 95, rdw: 15.2, alk_phos: 120, wbc: 9.2 } },
  { label: "Optimal 60yo", age: 60, vals: { albumin: 50, creatinine: 0.8, glucose: 4.7, crp_log: -3.0, lymphocyte: 38, mcv: 88, rdw: 12.2, alk_phos: 48, wbc: 4.8 } },
];

export default function PhenoAgeCalculator() {
  const [age, setAge] = useState(45);
  const [vals, setVals] = useState<Record<string, number>>({ ...DEFAULTS });
  const [activePreset, setActivePreset] = useState(0);

  const phenoAge = useMemo(() => computePhenoAge(vals, age), [vals, age]);
  const delta = phenoAge != null ? +(phenoAge - age).toFixed(1) : null;

  const isAccelerated = delta != null && delta > 2;
  const isHealthy = delta != null && delta < -2;
  const color = isAccelerated ? "text-red-600" : isHealthy ? "text-emerald-600" : "text-amber-600";
  const bgColor = isAccelerated ? "bg-red-50 border-red-200" : isHealthy ? "bg-emerald-50 border-emerald-200" : "bg-amber-50 border-amber-200";
  const label = isAccelerated ? "Accelerated Aging" : isHealthy ? "Healthy Aging" : "Near Chronological";

  function applyPreset(idx: number) {
    setActivePreset(idx);
    setAge(PRESETS[idx].age);
    setVals({ ...PRESETS[idx].vals });
  }

  // Bar chart: contribution of each marker
  const contributions = useMemo(() => {
    return Object.entries(WEIGHTS).map(([k, w]) => ({
      key: k,
      label: LABELS[k].label,
      contrib: w * (vals[k] ?? 0),
    }));
  }, [vals]);
  const maxAbs = Math.max(...contributions.map((c) => Math.abs(c.contrib)), 0.01);

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Presets */}
      <div className="flex border-b border-gray-100 bg-gray-50">
        {PRESETS.map((p, i) => (
          <button
            key={p.label}
            onClick={() => applyPreset(i)}
            className={`flex-1 py-3 text-xs font-bold transition-all ${
              activePreset === i
                ? "bg-white text-gray-900 border-b-2 border-gray-900"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-0 divide-y md:divide-y-0 md:divide-x divide-gray-100">
        {/* Left: sliders */}
        <div className="p-5 space-y-3">
          {/* Age */}
          <div className="flex items-center gap-3">
            <span className="text-xs font-bold text-gray-500 w-24 shrink-0">Age</span>
            <input
              type="range" min={20} max={90} step={1} value={age}
              onChange={(e) => setAge(parseInt(e.target.value))}
              className="flex-1 accent-gray-700 h-1.5"
            />
            <span className="font-mono font-black text-gray-900 w-10 text-right tabular-nums text-sm">{age}</span>
          </div>
          <div className="border-t border-gray-100 pt-3 space-y-2.5">
            {Object.entries(LABELS).map(([k, meta]) => (
              <div key={k} className="flex items-center gap-3">
                <span className="text-xs font-medium text-gray-500 w-24 shrink-0 truncate">{meta.label}</span>
                <input
                  type="range" min={meta.min} max={meta.max} step={meta.step}
                  value={vals[k] ?? meta.min}
                  onChange={(e) => {
                    setActivePreset(-1);
                    setVals((v) => ({ ...v, [k]: parseFloat(e.target.value) }));
                  }}
                  className="flex-1 accent-emerald-500 h-1.5"
                />
                <span className="font-mono text-xs text-gray-700 w-12 text-right tabular-nums">{vals[k]}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right: result + bar chart */}
        <div className="p-5 flex flex-col gap-4">
          {/* Big result */}
          <div className={`rounded-xl border p-4 ${bgColor}`}>
            <div className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">PhenoAge</div>
            <div className={`text-5xl font-black tabular-nums ${color}`}>
              {phenoAge ?? "—"}
              <span className="text-lg font-bold ml-1">yr</span>
            </div>
            <div className="flex items-center gap-3 mt-2">
              <span className="text-sm text-gray-500">Chronological: <strong>{age} yr</strong></span>
              {delta != null && (
                <span className={`text-sm font-bold ${color}`}>
                  {delta > 0 ? "+" : ""}{delta} yr
                </span>
              )}
            </div>
            <div className={`text-xs font-bold mt-1 ${color}`}>{label}</div>
          </div>

          {/* Contribution bars */}
          <div>
            <div className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Marker Contributions to xb</div>
            <div className="space-y-1.5">
              {contributions.map((c) => {
                const pct = Math.abs(c.contrib) / maxAbs * 100;
                const isPos = c.contrib > 0;
                return (
                  <div key={c.key} className="flex items-center gap-2">
                    <span className="text-[10px] text-gray-500 w-20 shrink-0 truncate">{c.label}</span>
                    <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-300 ${isPos ? "bg-red-400" : "bg-emerald-400"}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className={`text-[10px] font-mono w-12 text-right tabular-nums ${isPos ? "text-red-600" : "text-emerald-600"}`}>
                      {c.contrib > 0 ? "+" : ""}{c.contrib.toFixed(3)}
                    </span>
                  </div>
                );
              })}
            </div>
            <p className="text-[10px] text-gray-400 mt-2">Red = ages faster · Green = ages slower</p>
          </div>
        </div>
      </div>
    </div>
  );
}
