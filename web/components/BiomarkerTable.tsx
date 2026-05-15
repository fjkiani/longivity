"use client";
import { PanelValue } from "@/lib/api";
import { cn, markerStatus } from "@/lib/utils";

interface Props {
  values: PanelValue[];
}

const MARKER_LABELS: Record<string, string> = {
  albumin: "Albumin",
  creatinine: "Creatinine",
  glucose: "Glucose",
  alkaline_phosphatase: "Alkaline Phosphatase",
  wbc: "WBC",
  lymphocyte_percent: "Lymphocytes %",
  mcv: "MCV",
  rdw: "RDW",
  crp: "hsCRP",
  ldl: "LDL Cholesterol",
  hdl: "HDL Cholesterol",
  triglycerides: "Triglycerides",
  total_cholesterol: "Total Cholesterol",
  hba1c: "HbA1c",
  testosterone: "Testosterone",
  tsh: "TSH",
  ferritin: "Ferritin",
  vitamin_d: "Vitamin D",
  homocysteine: "Homocysteine",
  egfr: "eGFR",
  bun: "BUN",
  ast: "AST",
  alt: "ALT",
  hemoglobin: "Hemoglobin",
  hematocrit: "Hematocrit",
  platelets: "Platelets",
  sodium: "Sodium",
  potassium: "Potassium",
  igf1: "IGF-1",
  dhea_s: "DHEA-S",
  insulin: "Insulin",
};

// PhenoAge critical markers
const PHENOAGE_MARKERS = new Set([
  "albumin", "creatinine", "glucose", "alkaline_phosphatase",
  "wbc", "lymphocyte_percent", "mcv", "rdw", "crp",
]);

export default function BiomarkerTable({ values }: Props) {
  const sorted = [...values].sort((a, b) => {
    const aPA = PHENOAGE_MARKERS.has(a.marker_key) ? 0 : 1;
    const bPA = PHENOAGE_MARKERS.has(b.marker_key) ? 0 : 1;
    if (aPA !== bPA) return aPA - bPA;
    return (MARKER_LABELS[a.marker_key] || a.marker_key).localeCompare(
      MARKER_LABELS[b.marker_key] || b.marker_key
    );
  });

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-100">
            <th className="text-left py-2 px-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Marker</th>
            <th className="text-right py-2 px-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Value</th>
            <th className="text-right py-2 px-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Range</th>
            <th className="text-center py-2 px-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Status</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((v) => {
            const status = markerStatus(v.value, v.ref_low, v.ref_high);
            const label = MARKER_LABELS[v.marker_key] || v.marker_display || v.marker_key;
            const isPhenoAge = PHENOAGE_MARKERS.has(v.marker_key);

            return (
              <tr key={v.marker_key} className="border-b border-gray-50 hover:bg-gray-50/50">
                <td className="py-2.5 px-3">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">{label}</span>
                    {isPhenoAge && (
                      <span className="text-xs bg-purple-50 text-purple-600 px-1.5 py-0.5 rounded font-medium">
                        PhenoAge
                      </span>
                    )}
                  </div>
                </td>
                <td className="py-2.5 px-3 text-right font-mono font-medium text-gray-900">
                  {v.value} {v.unit && <span className="text-gray-400 font-normal text-xs">{v.unit}</span>}
                </td>
                <td className="py-2.5 px-3 text-right text-xs text-gray-400">
                  {v.ref_low != null && v.ref_high != null
                    ? `${v.ref_low}–${v.ref_high}`
                    : v.ref_low != null
                    ? `>${v.ref_low}`
                    : v.ref_high != null
                    ? `<${v.ref_high}`
                    : "—"}
                </td>
                <td className="py-2.5 px-3 text-center">
                  <span
                    className={cn(
                      "inline-block px-2 py-0.5 rounded-full text-xs font-medium",
                      status === "normal" && "bg-green-50 text-green-700",
                      status === "high" && "bg-red-50 text-red-700",
                      status === "low" && "bg-yellow-50 text-yellow-700",
                      status === "unknown" && "bg-gray-50 text-gray-400"
                    )}
                  >
                    {status === "normal" ? "Normal" : status === "high" ? "High" : status === "low" ? "Low" : "—"}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
