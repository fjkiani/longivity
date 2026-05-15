"use client";

import { BiomarkerGaps } from "@/lib/api";

interface Props {
  gaps: BiomarkerGaps;
}

const domainColors: Record<string, string> = {
  metabolic_core: "bg-blue-100 text-blue-800",
  hematology: "bg-red-100 text-red-800",
  cardiovascular: "bg-pink-100 text-pink-800",
  thyroid: "bg-purple-100 text-purple-800",
  hormones_male: "bg-orange-100 text-orange-800",
  hormones_female: "bg-rose-100 text-rose-800",
  inflammation_immune: "bg-yellow-100 text-yellow-800",
  nutrients_micronutrients: "bg-green-100 text-green-800",
  liver_function: "bg-amber-100 text-amber-800",
  kidney_function: "bg-cyan-100 text-cyan-800",
  gut_microbiome: "bg-lime-100 text-lime-800",
  toxicology_heavy_metals: "bg-gray-100 text-gray-800",
  cancer_markers: "bg-red-200 text-red-900",
  epigenetic_aging: "bg-violet-100 text-violet-800",
  genetics_pharmacogenomics: "bg-indigo-100 text-indigo-800",
  specialty_functional: "bg-teal-100 text-teal-800",
};

export function GapSummaryCard({ gaps }: Props) {
  const coveragePct = gaps.tier1_coverage_pct;
  const coverageColor =
    coveragePct >= 80 ? "text-green-600" :
    coveragePct >= 50 ? "text-yellow-600" :
    "text-red-600";

  const barColor =
    coveragePct >= 80 ? "bg-green-500" :
    coveragePct >= 50 ? "bg-yellow-500" :
    "bg-red-500";

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-gray-900">Biomarker Coverage</h3>
          <p className="text-sm text-gray-500 mt-0.5">
            {gaps.existing_marker_count} of {gaps.total_tier1_markers} baseline markers collected
          </p>
        </div>
        <span className={`text-2xl font-bold ${coverageColor}`}>
          {coveragePct}%
        </span>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-gray-100 rounded-full h-2.5">
        <div
          className={`h-2.5 rounded-full transition-all ${barColor}`}
          style={{ width: `${coveragePct}%` }}
        />
      </div>

      {/* Tier summary */}
      <div className="grid grid-cols-3 gap-3">
        <TierBadge
          tier="Tier 1"
          label="Baseline"
          count={gaps.missing_tier1.length}
          color="red"
        />
        <TierBadge
          tier="Tier 2"
          label="Expanded"
          count={gaps.missing_tier2.length}
          color="yellow"
        />
        <TierBadge
          tier="Tier 3"
          label="Specialty"
          count={gaps.missing_tier3.length}
          color="gray"
        />
      </div>

      {/* Missing tier_1 panels */}
      {gaps.missing_panels_tier1.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
            Missing Baseline Panels
          </p>
          <div className="flex flex-wrap gap-1.5">
            {gaps.missing_panels_tier1.map((pid) => (
              <span
                key={pid}
                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-50 text-red-700 border border-red-200"
              >
                {pid.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Missing tier_1 markers by domain */}
      {gaps.missing_tier1.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
            Missing Baseline Markers ({gaps.missing_tier1.length})
          </p>
          <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
            {gaps.missing_tier1.map((m) => (
              <span
                key={m.marker_key}
                className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                  domainColors[m.domain] || "bg-gray-100 text-gray-700"
                }`}
                title={m.domain?.replace(/_/g, " ")}
              >
                {m.display_name}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function TierBadge({
  tier,
  label,
  count,
  color,
}: {
  tier: string;
  label: string;
  count: number;
  color: "red" | "yellow" | "gray";
}) {
  const colors = {
    red: count > 0 ? "bg-red-50 border-red-200 text-red-700" : "bg-green-50 border-green-200 text-green-700",
    yellow: count > 0 ? "bg-yellow-50 border-yellow-200 text-yellow-700" : "bg-green-50 border-green-200 text-green-700",
    gray: "bg-gray-50 border-gray-200 text-gray-600",
  };

  return (
    <div className={`rounded-lg border p-3 text-center ${colors[color]}`}>
      <div className="text-lg font-bold">{count}</div>
      <div className="text-xs font-medium">{tier}</div>
      <div className="text-xs opacity-75">{label}</div>
    </div>
  );
}
