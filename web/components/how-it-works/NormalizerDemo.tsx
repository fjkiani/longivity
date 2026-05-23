"use client";
import { useState } from "react";

const MARKERS = [
  {
    key: "albumin",
    label: "Albumin",
    inputUnit: "g/dL",
    outputUnit: "g/L",
    defaultVal: 4.5,
    convert: (v: number) => +(v * 10).toFixed(2),
    formula: "× 10",
    note: "PhenoAge Gompertz model uses g/L. Most US labs report g/dL.",
    min: 2, max: 6, step: 0.1,
    aliases: ["alb", "albumin_g_dl", "serum_albumin"],
  },
  {
    key: "glucose",
    label: "Glucose",
    inputUnit: "mg/dL",
    outputUnit: "mmol/L",
    defaultVal: 95,
    convert: (v: number) => +(v / 18.018).toFixed(3),
    formula: "÷ 18.018",
    note: "Levine 2018 uses mmol/L. US labs report mg/dL. Alias: glucose_mg_dl, fasting_glucose.",
    min: 50, max: 300, step: 1,
    aliases: ["glucose_mg_dl", "fasting_glucose", "blood_glucose"],
  },
  {
    key: "crp",
    label: "CRP",
    inputUnit: "mg/L",
    outputUnit: "ln(mg/dL)",
    defaultVal: 1.2,
    convert: (v: number) => +(Math.log(v / 10)).toFixed(4),
    formula: "÷10 → ln()",
    note: "Model uses natural log of mg/dL. Out-of-range values are flagged but still used — never silently rejected.",
    min: 0.1, max: 20, step: 0.1,
    aliases: ["crp_mg_l", "hs_crp", "hscrp", "c_reactive_protein"],
  },
  {
    key: "creatinine",
    label: "Creatinine",
    inputUnit: "mg/dL",
    outputUnit: "mg/dL",
    defaultVal: 0.9,
    convert: (v: number) => +v.toFixed(2),
    formula: "no conversion",
    note: "Already in correct units. Alias: creat, serum_creatinine, creatinine_mg_dl.",
    min: 0.4, max: 5, step: 0.05,
    aliases: ["creat", "serum_creatinine", "creatinine_mg_dl"],
  },
];

export default function NormalizerDemo() {
  const [values, setValues] = useState<Record<string, number>>(
    Object.fromEntries(MARKERS.map((m) => [m.key, m.defaultVal]))
  );
  const [active, setActive] = useState("albumin");

  const marker = MARKERS.find((m) => m.key === active)!;
  const raw = values[active];
  const converted = marker.convert(raw);

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="flex border-b border-gray-100">
        {MARKERS.map((m) => (
          <button
            key={m.key}
            onClick={() => setActive(m.key)}
            className={`flex-1 py-3 text-xs font-bold transition-all ${
              active === m.key
                ? "bg-emerald-50 text-emerald-700 border-b-2 border-emerald-500"
                : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      <div className="p-6">
        <div className="flex flex-col md:flex-row items-stretch md:items-center gap-4 mb-5">
          <div className="flex-1 bg-gray-50 rounded-xl p-4 border border-gray-100">
            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">
              You send — {marker.inputUnit}
            </label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min={marker.min}
                max={marker.max}
                step={marker.step}
                value={raw}
                onChange={(e) =>
                  setValues((v) => ({ ...v, [active]: parseFloat(e.target.value) }))
                }
                className="flex-1 accent-emerald-500 h-2"
              />
              <span className="font-mono font-black text-gray-900 text-xl w-16 text-right tabular-nums">
                {raw}
              </span>
            </div>
            <div className="mt-3 flex flex-wrap gap-1">
              {marker.aliases.map((a) => (
                <span key={a} className="text-[10px] font-mono bg-white border border-gray-200 text-gray-500 px-1.5 py-0.5 rounded">
                  {a}
                </span>
              ))}
            </div>
          </div>

          <div className="flex md:flex-col items-center justify-center gap-1 shrink-0 px-2">
            <span className="text-xs font-mono text-gray-500 bg-gray-100 px-2 py-1 rounded-lg whitespace-nowrap">
              {marker.formula}
            </span>
            <svg className="w-5 h-5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </div>

          <div className="flex-1 bg-emerald-50 rounded-xl p-4 border border-emerald-100">
            <label className="block text-xs font-bold text-emerald-600 uppercase tracking-wider mb-3">
              Model receives — {marker.outputUnit}
            </label>
            <div className="font-mono font-black text-emerald-700 text-3xl tabular-nums">
              {converted}
            </div>
          </div>
        </div>

        <p className="text-xs text-gray-500 bg-gray-50 rounded-xl px-4 py-2.5 border border-gray-100 leading-relaxed">
          <span className="font-bold text-gray-700">How it works: </span>{marker.note}
        </p>
      </div>
    </div>
  );
}
