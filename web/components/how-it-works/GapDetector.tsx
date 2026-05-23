"use client";
import { useState, useMemo } from "react";

const TIER1_MARKERS = [
  { key: "albumin",          label: "Albumin",          domain: "Metabolic",    panel: "CMP" },
  { key: "creatinine",       label: "Creatinine",       domain: "Metabolic",    panel: "CMP" },
  { key: "glucose",          label: "Glucose",          domain: "Metabolic",    panel: "CMP" },
  { key: "crp",              label: "CRP",              domain: "Inflammation", panel: "CRP Panel" },
  { key: "lymphocyte",       label: "Lymphocyte %",     domain: "Hematology",   panel: "CBC" },
  { key: "mcv",              label: "MCV",              domain: "Hematology",   panel: "CBC" },
  { key: "rdw",              label: "RDW",              domain: "Hematology",   panel: "CBC" },
  { key: "alk_phos",         label: "Alk Phos",         domain: "Metabolic",    panel: "CMP" },
  { key: "wbc",              label: "WBC",              domain: "Hematology",   panel: "CBC" },
  { key: "hba1c",            label: "HbA1c",            domain: "Metabolic",    panel: "HbA1c" },
  { key: "vitamin_d",        label: "Vitamin D",        domain: "Hormonal",     panel: "Vitamin D Panel" },
  { key: "tsh",              label: "TSH",              domain: "Hormonal",     panel: "Thyroid Panel" },
  { key: "testosterone",     label: "Testosterone",     domain: "Hormonal",     panel: "Hormone Panel" },
  { key: "igf1",             label: "IGF-1",            domain: "Hormonal",     panel: "IGF-1" },
  { key: "il6",              label: "IL-6",             domain: "Inflammation", panel: "Cytokine Panel" },
];

const PANEL_PRESETS = [
  { label: "CMP only",         keys: ["albumin","creatinine","glucose","alk_phos"] },
  { label: "CMP + CBC",        keys: ["albumin","creatinine","glucose","alk_phos","lymphocyte","mcv","rdw","wbc"] },
  { label: "Full baseline",    keys: ["albumin","creatinine","glucose","alk_phos","lymphocyte","mcv","rdw","wbc","crp","hba1c","vitamin_d","tsh"] },
  { label: "Complete panel",   keys: TIER1_MARKERS.map((m) => m.key) },
];

const DOMAIN_COLORS: Record<string, string> = {
  Metabolic:    "bg-blue-50 border-blue-200 text-blue-700",
  Inflammation: "bg-red-50 border-red-200 text-red-700",
  Hematology:   "bg-violet-50 border-violet-200 text-violet-700",
  Hormonal:     "bg-amber-50 border-amber-200 text-amber-700",
};

export default function GapDetector() {
  const [present, setPresent] = useState<Set<string>>(new Set(PANEL_PRESETS[1].keys));
  const [activePreset, setActivePreset] = useState(1);

  function applyPreset(i: number) {
    setActivePreset(i);
    setPresent(new Set(PANEL_PRESETS[i].keys));
  }

  function toggle(key: string) {
    setActivePreset(-1);
    setPresent((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  const coverage = useMemo(() => Math.round((present.size / TIER1_MARKERS.length) * 100), [present]);
  const missing = useMemo(() => TIER1_MARKERS.filter((m) => !present.has(m.key)), [present]);
  const phenoageReady = useMemo(() => {
    const required = ["albumin","creatinine","glucose","crp","lymphocyte","mcv","rdw","alk_phos","wbc"];
    return required.filter((k) => present.has(k)).length;
  }, [present]);

  const coverageColor = coverage >= 80 ? "text-emerald-600" : coverage >= 50 ? "text-amber-600" : "text-red-600";
  const coverageBg = coverage >= 80 ? "bg-emerald-50 border-emerald-200" : coverage >= 50 ? "bg-amber-50 border-amber-200" : "bg-red-50 border-red-200";

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Presets */}
      <div className="flex border-b border-gray-100 bg-gray-50">
        {PANEL_PRESETS.map((p, i) => (
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
        {/* Left: marker toggles */}
        <div className="p-5">
          <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-3">
            Toggle markers present in patient record
          </div>
          <div className="flex flex-wrap gap-2">
            {TIER1_MARKERS.map((m) => (
              <button
                key={m.key}
                onClick={() => toggle(m.key)}
                className={`px-2.5 py-1.5 rounded-lg text-xs font-bold border transition-all ${
                  present.has(m.key)
                    ? "bg-gray-900 text-white border-gray-900"
                    : "bg-gray-50 text-gray-500 border-gray-200 hover:border-gray-400"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>

        {/* Right: gap report */}
        <div className="p-5 flex flex-col gap-4">
          {/* Coverage */}
          <div className={`rounded-xl border p-4 ${coverageBg}`}>
            <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1">Tier 1 Coverage</div>
            <div className={`text-5xl font-black tabular-nums ${coverageColor}`}>
              {coverage}%
            </div>
            <div className="mt-2 flex items-center gap-3 text-xs text-gray-600">
              <span>{present.size} / {TIER1_MARKERS.length} markers</span>
              <span className="font-bold">PhenoAge: {phenoageReady}/9 ready</span>
            </div>
            {/* Coverage bar */}
            <div className="mt-3 h-2 bg-white/60 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  coverage >= 80 ? "bg-emerald-500" : coverage >= 50 ? "bg-amber-500" : "bg-red-500"
                }`}
                style={{ width: `${coverage}%` }}
              />
            </div>
          </div>

          {/* Missing markers */}
          {missing.length > 0 ? (
            <div>
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">
                Missing ({missing.length})
              </div>
              <div className="flex flex-wrap gap-1.5">
                {missing.map((m) => (
                  <span key={m.key} className={`text-[11px] font-medium px-2 py-1 rounded-lg border ${DOMAIN_COLORS[m.domain]}`}>
                    {m.label}
                    <span className="ml-1 opacity-60 text-[9px]">{m.panel}</span>
                  </span>
                ))}
              </div>
            </div>
          ) : (
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 text-xs text-emerald-700 font-bold text-center">
              All Tier 1 markers present
            </div>
          )}

          {/* State inference */}
          <div className="bg-gray-50 rounded-xl p-3 border border-gray-100 text-xs">
            <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Inferred State</div>
            <div className="font-bold text-gray-900">
              {present.size === 0 ? "NEW" :
               coverage < 60 ? "DATA_INCOMPLETE" :
               "ASSESSMENT_PENDING"}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
