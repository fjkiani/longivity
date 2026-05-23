"use client";
import { useState } from "react";

const HALLMARKS = [
  {
    id: "genomic",
    label: "Genomic Instability",
    color: "bg-violet-100 border-violet-300 text-violet-800",
    activeColor: "bg-violet-600 text-white border-violet-600",
    dotColor: "bg-violet-500",
    implemented: true,
    markers: ["CRP", "WBC", "Lymphocyte %"],
    signal: "Elevated WBC + low lymphocyte % → immune stress → DNA damage signaling",
    source: "PMID 36599349",
  },
  {
    id: "epigenetic",
    label: "Epigenetic Alterations",
    color: "bg-blue-100 border-blue-300 text-blue-800",
    activeColor: "bg-blue-600 text-white border-blue-600",
    dotColor: "bg-blue-500",
    implemented: true,
    markers: ["PhenoAge acceleration", "GrimAge (pre-computed)", "DunedinPACE (pre-computed)"],
    signal: "PhenoAge delta > +5yr → epigenetic clock acceleration signal",
    source: "PMID 29676998",
  },
  {
    id: "nutrient",
    label: "Nutrient Sensing",
    color: "bg-amber-100 border-amber-300 text-amber-800",
    activeColor: "bg-amber-600 text-white border-amber-600",
    dotColor: "bg-amber-500",
    implemented: true,
    markers: ["Glucose", "HbA1c", "Fasting insulin", "HOMA-IR"],
    signal: "Glucose > 5.6 mmol/L or HbA1c > 5.7% → mTOR/AMPK dysregulation",
    source: "PMID 36599349",
  },
  {
    id: "mitochondrial",
    label: "Mitochondrial Dysfunction",
    color: "bg-orange-100 border-orange-300 text-orange-800",
    activeColor: "bg-orange-600 text-white border-orange-600",
    dotColor: "bg-orange-500",
    implemented: true,
    markers: ["Lactate", "VO2max (wearable)", "Ferritin", "RDW"],
    signal: "Elevated RDW + low VO2max → mitochondrial heteroplasmy proxy",
    source: "PMID 36599349",
  },
  {
    id: "senescence",
    label: "Cellular Senescence",
    color: "bg-rose-100 border-rose-300 text-rose-800",
    activeColor: "bg-rose-600 text-white border-rose-600",
    dotColor: "bg-rose-500",
    implemented: true,
    markers: ["IL-6", "CRP", "TNF-α", "p16 (if available)"],
    signal: "IL-6 > 3.5 pg/mL + CRP > 3 mg/L → SASP (senescence-associated secretory phenotype)",
    source: "PMID 36599349",
  },
  {
    id: "intercellular",
    label: "Intercellular Communication",
    color: "bg-teal-100 border-teal-300 text-teal-800",
    activeColor: "bg-teal-600 text-white border-teal-600",
    dotColor: "bg-teal-500",
    implemented: true,
    markers: ["Albumin", "Total protein", "IGF-1", "DHEA-S"],
    signal: "Low albumin + low DHEA-S → systemic signaling decline",
    source: "PMID 36599349",
  },
  {
    id: "telomere",
    label: "Telomere Attrition",
    color: "bg-gray-100 border-gray-300 text-gray-500",
    activeColor: "bg-gray-400 text-white border-gray-400",
    dotColor: "bg-gray-400",
    implemented: false,
    markers: ["Leukocyte telomere length (accepted, not scored)"],
    signal: "Not in shippable scorer. Requires external telomere assay (e.g. LifeLength).",
    source: "—",
  },
  {
    id: "proteostasis",
    label: "Loss of Proteostasis",
    color: "bg-gray-100 border-gray-300 text-gray-500",
    activeColor: "bg-gray-400 text-white border-gray-400",
    dotColor: "bg-gray-400",
    implemented: false,
    markers: ["Not yet implemented"],
    signal: "Scaffolded. No scoring logic in current release.",
    source: "—",
  },
  {
    id: "autophagy",
    label: "Disabled Macroautophagy",
    color: "bg-gray-100 border-gray-300 text-gray-500",
    activeColor: "bg-gray-400 text-white border-gray-400",
    dotColor: "bg-gray-400",
    implemented: false,
    markers: ["Not yet implemented"],
    signal: "Scaffolded. No scoring logic in current release.",
    source: "—",
  },
];

export default function HallmarkMap() {
  const [active, setActive] = useState("genomic");
  const h = HALLMARKS.find((x) => x.id === active)!;

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="p-5 border-b border-gray-100">
        <p className="text-xs text-gray-500 font-medium">
          Click a hallmark to see which biomarkers drive it and how the signal is computed.
          <span className="ml-2 inline-flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-violet-500 inline-block" /> Implemented
            <span className="w-2 h-2 rounded-full bg-gray-400 inline-block ml-2" /> Not yet
          </span>
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-0 divide-y md:divide-y-0 md:divide-x divide-gray-100">
        {/* Left: hallmark grid */}
        <div className="p-5">
          <div className="grid grid-cols-3 gap-2">
            {HALLMARKS.map((hm) => (
              <button
                key={hm.id}
                onClick={() => setActive(hm.id)}
                className={`rounded-xl border px-2 py-2.5 text-[11px] font-bold text-center transition-all leading-tight ${
                  active === hm.id ? hm.activeColor : hm.color
                } ${!hm.implemented ? "opacity-60" : ""}`}
              >
                {hm.label}
                {!hm.implemented && (
                  <span className="block text-[9px] font-normal mt-0.5 opacity-70">not implemented</span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Right: detail */}
        <div className="p-5 flex flex-col gap-4">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className={`w-3 h-3 rounded-full ${h.dotColor}`} />
              <h3 className="font-black text-gray-900 text-sm">{h.label}</h3>
              {!h.implemented && (
                <span className="text-[10px] font-bold bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
                  Not implemented
                </span>
              )}
            </div>

            <div className="mb-3">
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1.5">Driving Biomarkers</div>
              <div className="flex flex-wrap gap-1.5">
                {h.markers.map((m) => (
                  <span key={m} className="text-xs bg-gray-50 border border-gray-200 text-gray-700 px-2 py-1 rounded-lg font-medium">
                    {m}
                  </span>
                ))}
              </div>
            </div>

            <div className="bg-gray-50 rounded-xl p-3 border border-gray-100">
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Signal Logic</div>
              <p className="text-xs text-gray-700 leading-relaxed">{h.signal}</p>
            </div>

            {h.source !== "—" && (
              <div className="mt-2 text-[10px] text-gray-400 font-mono">Source: {h.source}</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
