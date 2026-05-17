"use client";

interface HallmarkEntry {
  status: string;
  phenoage_signal: number;
  supplementary_signal: number;
  driving_biomarkers_phenoage: string[];
  driving_biomarkers_supplementary: string[];
}

interface CompoundRec {
  compound: string;
  display_name: string;
  overall_relevance: number;
  evidence_tier: string;
  evidence_tier_label: string;
  primary_match: string | null;
  mr_anchor: { clock: string; p_value: number; direction: string; citation: string } | null;
  dose: string | null;
}

interface GeneticProfile {
  apoe_status?: { genotype: string; risk_tier: string; ad_risk_or: string; longevity_impact: string };
  mthfr_status?: { c677t: string; a1298c: string; enzyme_activity_estimate: number; activity_label: string; recommendation: string };
  variant_annotations?: Record<string, { gene: string; zygosity: string; impact: string; note: string }>;
}

interface ApiResponse {
  status: string;
  phenoage_analysis?: {
    phenoage_estimate: number | null;
    age_acceleration: number | null;
    mortality_score_10yr: number | null;
    completeness_mode: string;
    components_available: number;
    components_total: number;
    top_accelerators: Array<{ canonical_key: string; tier: string; acceleration_status: string; linear_term: number; primary_hallmark: string | null }>;
  };
  hallmark_narrative?: Record<string, HallmarkEntry>;
  compound_recommendations?: CompoundRec[];
  data_completeness?: {
    phenoage_complete_for_full_estimate: boolean;
    hallmarks_scoreable: number;
    recommendation: string;
    phenoage_panel_diagnosis?: { phenoage_canonical_missing_for_full: string[] };
  };
  genetic_profile?: GeneticProfile;
  genetic_analysis?: GeneticProfile;
  scoring_calibration?: string;
}

const HALLMARK_LABELS: Record<string, string> = {
  genomic_instability: "Genomic Instability",
  epigenetic_alterations: "Epigenetic Alterations",
  nutrient_sensing: "Nutrient Sensing",
  mitochondrial_dysfunction: "Mitochondrial Dysfunction",
  cellular_senescence: "Cellular Senescence",
  altered_intercellular_communication: "Intercellular Communication",
};

const TIER_COLORS: Record<string, string> = {
  MR_VALIDATED: "bg-emerald-100 text-emerald-800 border-emerald-200",
  RCT: "bg-blue-100 text-blue-800 border-blue-200",
  OBSERVATIONAL: "bg-gray-100 text-gray-700 border-gray-200",
};

const IMPACT_COLORS: Record<string, string> = {
  FAVORABLE: "text-emerald-600 bg-emerald-50",
  INTERMEDIATE: "text-yellow-700 bg-yellow-50",
  UNFAVORABLE: "text-rose-600 bg-rose-50",
  UNKNOWN: "text-gray-500 bg-gray-50",
};

const RISK_COLORS: Record<string, string> = {
  HIGH_RISK: "text-rose-700 bg-rose-50 border-rose-200",
  ELEVATED: "text-orange-700 bg-orange-50 border-orange-200",
  REFERENCE: "text-gray-700 bg-gray-50 border-gray-200",
  REDUCED_RISK: "text-emerald-700 bg-emerald-50 border-emerald-200",
  UNCERTAIN: "text-yellow-700 bg-yellow-50 border-yellow-200",
};

function AccelerationBadge({ accel }: { accel: number | null }) {
  if (accel === null) return null;
  const isAccel = accel > 0;
  const isDecel = accel < 0;
  return (
    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-bold ${
      isAccel ? "bg-rose-100 text-rose-700" : isDecel ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-600"
    }`}>
      {isAccel ? "▲" : isDecel ? "▼" : "="} {isAccel ? "+" : ""}{accel.toFixed(1)} yr
    </span>
  );
}

export default function PipelineOutput({ data, rawJson, showRaw, onToggleRaw }: {
  data: ApiResponse;
  rawJson: string;
  showRaw: boolean;
  onToggleRaw: () => void;
}) {
  const pa = data.phenoage_analysis;
  const hallmarks = data.hallmark_narrative || {};
  const compounds = data.compound_recommendations || [];
  const completeness = data.data_completeness;
  const genetic = data.genetic_profile || data.genetic_analysis;

  const hallmarkEntries = Object.entries(hallmarks).sort((a, b) => {
    const scoreA = (a[1].phenoage_signal || 0) + (a[1].supplementary_signal || 0);
    const scoreB = (b[1].phenoage_signal || 0) + (b[1].supplementary_signal || 0);
    return scoreB - scoreA;
  });

  return (
    <div className="space-y-6">
      {/* Toggle */}
      <div className="flex justify-end">
        <button
          onClick={onToggleRaw}
          className="text-xs font-medium text-gray-500 hover:text-gray-700 border border-gray-200 rounded-lg px-3 py-1.5 transition-colors"
        >
          {showRaw ? "Show Structured View" : "Show Raw JSON"}
        </button>
      </div>

      {showRaw ? (
        <pre className="bg-gray-950 text-emerald-400 rounded-2xl p-6 text-xs overflow-auto max-h-[600px] font-mono leading-relaxed">
          {rawJson}
        </pre>
      ) : (
        <>
          {/* PhenoAge Card */}
          {pa && (
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-black text-gray-900">PhenoAge Analysis</h3>
                <span className={`text-xs font-bold px-2 py-1 rounded-full ${
                  pa.completeness_mode === "FULL_9BIOMARKERS_PLUS_AGE"
                    ? "bg-emerald-100 text-emerald-700"
                    : "bg-yellow-100 text-yellow-700"
                }`}>
                  {pa.completeness_mode === "FULL_9BIOMARKERS_PLUS_AGE" ? "Full Panel" : `Partial ${pa.components_available}/${pa.components_total}`}
                </span>
              </div>

              {pa.phenoage_estimate !== null ? (
                <div className="flex items-end gap-6 flex-wrap">
                  <div>
                    <div className="text-5xl font-black text-gray-900">{pa.phenoage_estimate?.toFixed(1)}</div>
                    <div className="text-sm text-gray-500 font-medium mt-1">Biological Age (years)</div>
                  </div>
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-500 font-medium">Acceleration:</span>
                      <AccelerationBadge accel={pa.age_acceleration} />
                    </div>
                    {pa.mortality_score_10yr !== null && (
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-500 font-medium">10yr mortality score:</span>
                        <span className="text-sm font-bold text-gray-700">{((pa.mortality_score_10yr || 0) * 100).toFixed(2)}%</span>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
                  <p className="text-sm font-bold text-yellow-800 mb-1">Partial Panel — PhenoAge estimate not available</p>
                  <p className="text-xs text-yellow-700">
                    {pa.components_available}/{pa.components_total} biomarkers provided. Full estimate requires all 9 + chronological age.
                  </p>
                  {completeness?.phenoage_panel_diagnosis?.phenoage_canonical_missing_for_full && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {completeness.phenoage_panel_diagnosis.phenoage_canonical_missing_for_full.map((m) => (
                        <span key={m} className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded-full font-mono">{m}</span>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Top accelerators */}
              {pa.top_accelerators && pa.top_accelerators.length > 0 && (
                <div className="mt-4">
                  <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Top Accelerating Components</p>
                  <div className="space-y-1.5">
                    {pa.top_accelerators.slice(0, 4).map((comp) => (
                      <div key={comp.canonical_key} className="flex items-center gap-3 text-xs">
                        <span className={`w-2 h-2 rounded-full shrink-0 ${
                          comp.acceleration_status === "ACCELERATING" ? "bg-rose-500" :
                          comp.acceleration_status === "PROTECTIVE" ? "bg-emerald-500" : "bg-gray-300"
                        }`} />
                        <span className="font-mono text-gray-600 w-36 shrink-0">{comp.canonical_key}</span>
                        <span className={`font-bold ${
                          comp.tier === "HIGH_RISK" ? "text-rose-600" :
                          comp.tier === "OPTIMAL" ? "text-emerald-600" : "text-gray-600"
                        }`}>{comp.tier}</span>
                        {comp.primary_hallmark && (
                          <span className="text-gray-400 truncate">→ {HALLMARK_LABELS[comp.primary_hallmark] || comp.primary_hallmark}</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Hallmark Narrative */}
          {hallmarkEntries.length > 0 && (
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <h3 className="font-black text-gray-900 mb-4">Hallmark Narrative</h3>
              <div className="space-y-3">
                {hallmarkEntries.map(([hm, entry]) => {
                  const totalSignal = (entry.phenoage_signal || 0) + (entry.supplementary_signal || 0);
                  const maxSignal = 3.0;
                  const pct = Math.min(100, Math.round((totalSignal / maxSignal) * 100));
                  return (
                    <div key={hm} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <span className={`font-bold px-2 py-0.5 rounded-full text-xs ${
                            entry.status === "PRIMARY_DRIVER" ? "bg-rose-100 text-rose-700" :
                            entry.status === "SECONDARY_DRIVER" ? "bg-orange-100 text-orange-700" :
                            "bg-gray-100 text-gray-600"
                          }`}>{entry.status.replace("_", " ")}</span>
                          <span className="font-semibold text-gray-700">{HALLMARK_LABELS[hm] || hm}</span>
                        </div>
                        <div className="flex items-center gap-3 text-gray-400">
                          {entry.phenoage_signal > 0 && (
                            <span>PA: <span className="font-mono text-gray-600">{entry.phenoage_signal.toFixed(3)}</span></span>
                          )}
                          {entry.supplementary_signal > 0 && (
                            <span>Supp: <span className="font-mono text-gray-600">{entry.supplementary_signal.toFixed(3)}</span></span>
                          )}
                        </div>
                      </div>
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            entry.status === "PRIMARY_DRIVER" ? "bg-rose-500" :
                            entry.status === "SECONDARY_DRIVER" ? "bg-orange-400" : "bg-gray-400"
                          }`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      {(entry.driving_biomarkers_phenoage?.length > 0 || entry.driving_biomarkers_supplementary?.length > 0) && (
                        <div className="flex flex-wrap gap-1 pt-0.5">
                          {[...entry.driving_biomarkers_phenoage, ...entry.driving_biomarkers_supplementary].map((b) => (
                            <span key={b} className="text-[10px] font-mono bg-gray-50 border border-gray-200 text-gray-500 px-1.5 py-0.5 rounded">{b}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Genetic Profile */}
          {genetic && (
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <h3 className="font-black text-gray-900 mb-4">Genetic Profile</h3>
              <div className="space-y-4">
                {genetic.apoe_status?.genotype && (
                  <div className={`rounded-xl border p-4 ${RISK_COLORS[genetic.apoe_status.risk_tier] || "bg-gray-50 border-gray-200"}`}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-sm">APOE {genetic.apoe_status.genotype}</span>
                      <span className="text-xs font-bold">{genetic.apoe_status.risk_tier}</span>
                    </div>
                    <p className="text-xs">{genetic.apoe_status.ad_risk_or} AD risk vs e3/e3</p>
                    <p className="text-xs mt-0.5 opacity-80">{genetic.apoe_status.longevity_impact}</p>
                  </div>
                )}
                {genetic.mthfr_status?.enzyme_activity_estimate !== undefined && (
                  <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-sm text-gray-900">MTHFR {genetic.mthfr_status.c677t}/{genetic.mthfr_status.a1298c}</span>
                      <span className="text-xs font-bold text-gray-600">{genetic.mthfr_status.activity_label}</span>
                    </div>
                    <p className="text-xs text-gray-600">Enzyme activity: <span className="font-bold">{Math.round((genetic.mthfr_status.enzyme_activity_estimate || 0) * 100)}%</span></p>
                    <p className="text-xs text-gray-500 mt-1">{genetic.mthfr_status.recommendation}</p>
                  </div>
                )}
                {genetic.variant_annotations && Object.entries(genetic.variant_annotations).map(([rsid, ann]) => (
                  <div key={rsid} className={`rounded-xl p-3 flex items-start gap-3 ${IMPACT_COLORS[ann.impact] || "bg-gray-50"}`}>
                    <div className="shrink-0">
                      <div className="text-xs font-black">{ann.gene}</div>
                      <div className="text-[10px] font-mono opacity-70">{rsid}</div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold">{ann.zygosity.replace("_", " ")}</span>
                        <span className="text-xs font-bold">{ann.impact}</span>
                      </div>
                      <p className="text-[10px] mt-0.5 opacity-80 leading-relaxed line-clamp-2">{ann.note}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Compound Recommendations */}
          {compounds.length > 0 && (
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <h3 className="font-black text-gray-900 mb-4">Compound Recommendations</h3>
              <div className="space-y-3">
                {compounds.slice(0, 5).map((c) => (
                  <div key={c.compound} className="flex items-start gap-4 p-3 rounded-xl bg-gray-50 border border-gray-100">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <span className="font-bold text-sm text-gray-900">{c.display_name || c.compound}</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${TIER_COLORS[c.evidence_tier] || "bg-gray-100 text-gray-600 border-gray-200"}`}>
                          {c.evidence_tier}
                        </span>
                      </div>
                      {c.primary_match && (
                        <p className="text-xs text-gray-500">→ {HALLMARK_LABELS[c.primary_match] || c.primary_match}</p>
                      )}
                      {c.mr_anchor && (
                        <p className="text-[10px] text-gray-400 mt-0.5">
                          {c.mr_anchor.citation} · p={c.mr_anchor.p_value} · {c.mr_anchor.clock}
                        </p>
                      )}
                      {c.dose && <p className="text-[10px] text-gray-400 mt-0.5">{c.dose}</p>}
                    </div>
                    <div className="shrink-0 text-right">
                      <div className="text-lg font-black text-gray-900">{Math.round((c.overall_relevance || 0) * 100)}</div>
                      <div className="text-[10px] text-gray-400">relevance</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Data Completeness */}
          {completeness && (
            <div className="bg-gray-50 border border-gray-200 rounded-2xl p-5">
              <h3 className="font-bold text-gray-700 text-sm mb-2">Data Completeness</h3>
              <p className="text-xs text-gray-600 leading-relaxed">{completeness.recommendation}</p>
              <div className="flex gap-4 mt-3 text-xs text-gray-500">
                <span>Hallmarks scoreable: <span className="font-bold text-gray-700">{completeness.hallmarks_scoreable}</span></span>
                <span>PhenoAge complete: <span className={`font-bold ${completeness.phenoage_complete_for_full_estimate ? "text-emerald-600" : "text-yellow-600"}`}>{completeness.phenoage_complete_for_full_estimate ? "Yes" : "No"}</span></span>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
