"use client";
import { useState } from "react";

// ── Types ─────────────────────────────────────────────────────────────────────

interface Accelerator {
  canonical_key: string;
  label: string;
  value: number;
  unit: string;
  tier: string;
  acceleration_status: string;
  primary_hallmark: string | null;
  linear_term?: number;
}

interface HallmarkEntry {
  status: string;
  phenoage_signal: number;
  supplementary_signal: number;
  driving_biomarkers_phenoage: string[];
  driving_biomarkers_supplementary: string[];
  narrative?: string;
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
  apoe_status?: { genotype: string; risk_tier: string; ad_risk_or: string; longevity_impact: string } | null;
  mthfr_status?: { c677t: string; a1298c: string; enzyme_activity_estimate: number; activity_label: string; recommendation: string } | null;
  variant_annotations?: Record<string, { gene: string; zygosity: string; impact: string; note: string }>;
}

interface OneRankedAction {
  action: string;
  urgency: string;
  urgency_score: number;
  rationale: string;
  evidence_tier: string;
  next_panel_days: number;
}

interface ApiResponse {
  status: string;
  phenoage_analysis?: {
    phenoage_estimate: number | null;
    age_acceleration: number | null;
    mortality_score_10yr: number | null;
    completeness_mode: string;
    components_available: number | null;
    components_total: number | null;
    age_years: number;
    top_accelerators: Accelerator[];
    top_by_linear_term_magnitude: Accelerator[];
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
  one_ranked_action?: OneRankedAction;
}

// ── Constants ─────────────────────────────────────────────────────────────────

const HALLMARK_LABELS: Record<string, string> = {
  genomic_instability: "Genomic Instability",
  epigenetic_alterations: "Epigenetic Alterations",
  nutrient_sensing: "Nutrient Sensing",
  mitochondrial_dysfunction: "Mitochondrial Dysfunction",
  cellular_senescence: "Cellular Senescence",
  altered_intercellular_communication: "Intercellular Communication",
};

const TIER_COLORS: Record<string, string> = {
  MR_VALIDATED: "bg-emerald-100 text-emerald-800 border-emerald-300",
  RCT:          "bg-blue-100 text-blue-800 border-blue-300",
  OBSERVATIONAL:"bg-gray-100 text-gray-700 border-gray-300",
  PROTOCOL:     "bg-violet-100 text-violet-800 border-violet-300",
};

const URGENCY_STYLES: Record<string, { bar: string; badge: string; text: string; bg: string }> = {
  HIGH:    { bar: "bg-red-500",    badge: "bg-red-100 text-red-800 border-red-300",    text: "text-red-700",    bg: "bg-red-50 border-red-200" },
  MEDIUM:  { bar: "bg-amber-500",  badge: "bg-amber-100 text-amber-800 border-amber-300", text: "text-amber-700", bg: "bg-amber-50 border-amber-200" },
  ROUTINE: { bar: "bg-emerald-500",badge: "bg-emerald-100 text-emerald-800 border-emerald-300", text: "text-emerald-700", bg: "bg-emerald-50 border-emerald-200" },
};

const IMPACT_STYLES: Record<string, string> = {
  FAVORABLE:    "bg-emerald-50 border-emerald-200 text-emerald-800",
  INTERMEDIATE: "bg-amber-50 border-amber-200 text-amber-800",
  UNFAVORABLE:  "bg-rose-50 border-rose-200 text-rose-800",
  UNKNOWN:      "bg-gray-50 border-gray-200 text-gray-700",
};

const RISK_STYLES: Record<string, string> = {
  HIGH_RISK:    "bg-rose-50 border-rose-300 text-rose-900",
  ELEVATED:     "bg-orange-50 border-orange-300 text-orange-900",
  REFERENCE:    "bg-gray-50 border-gray-200 text-gray-800",
  REDUCED_RISK: "bg-emerald-50 border-emerald-200 text-emerald-900",
};

// ── Sub-components ────────────────────────────────────────────────────────────

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="text-xs font-black text-gray-400 uppercase tracking-wider mb-3">{children}</div>
  );
}

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-white rounded-2xl border border-gray-200 p-5 shadow-sm ${className}`}>
      {children}
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

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
  const action = data.one_ranked_action;

  const hallmarkEntries = Object.entries(hallmarks).sort((a, b) => {
    const sa = (a[1].phenoage_signal || 0) + (a[1].supplementary_signal || 0);
    const sb = (b[1].phenoage_signal || 0) + (b[1].supplementary_signal || 0);
    return sb - sa;
  });

  const accel = pa?.age_acceleration ?? null;
  const isAccel = accel !== null && accel > 2;
  const isDecel = accel !== null && accel < -2;
  const ageColor = isAccel ? "text-red-600" : isDecel ? "text-emerald-600" : "text-amber-600";
  const ageBg = isAccel ? "bg-red-50 border-red-200" : isDecel ? "bg-emerald-50 border-emerald-200" : "bg-amber-50 border-amber-200";

  const urgencyStyle = action ? (URGENCY_STYLES[action.urgency] || URGENCY_STYLES.ROUTINE) : URGENCY_STYLES.ROUTINE;

  return (
    <div className="space-y-5">
      {/* Raw toggle */}
      <div className="flex justify-end">
        <button
          onClick={onToggleRaw}
          className="text-sm font-bold text-gray-500 hover:text-gray-800 border border-gray-200 rounded-xl px-4 py-2 transition-colors hover:bg-gray-50"
        >
          {showRaw ? "← Structured View" : "View Raw JSON →"}
        </button>
      </div>

      {showRaw ? (
        <pre className="bg-gray-950 text-emerald-400 rounded-2xl p-6 text-xs overflow-auto max-h-[700px] font-mono leading-relaxed">
          {rawJson}
        </pre>
      ) : (
        <>
          {/* ── 1. ONE RANKED ACTION ─────────────────────────────────────── */}
          {action && (
            <div className={`rounded-2xl border-2 p-5 ${urgencyStyle.bg}`}>
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-black text-gray-500 uppercase tracking-wider">One Ranked Action</span>
                  <span className={`text-xs font-black px-2.5 py-1 rounded-full border ${urgencyStyle.badge}`}>
                    {action.urgency}
                  </span>
                </div>
                <div className="text-right shrink-0">
                  <div className={`text-2xl font-black tabular-nums ${urgencyStyle.text}`}>
                    {Math.round(action.urgency_score * 100)}
                  </div>
                  <div className="text-[10px] text-gray-400 font-medium">urgency score</div>
                </div>
              </div>

              {/* The action itself — big and clear */}
              <div className={`text-lg font-black text-gray-900 leading-snug mb-3`}>
                {action.action}
              </div>

              {/* Rationale */}
              <p className="text-sm text-gray-700 leading-relaxed mb-3">
                {action.rationale}
              </p>

              <div className="flex items-center gap-3 flex-wrap">
                <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${TIER_COLORS[action.evidence_tier] || TIER_COLORS.PROTOCOL}`}>
                  {action.evidence_tier}
                </span>
                <span className="text-xs text-gray-500 font-medium">
                  Next panel in <strong className="text-gray-800">{action.next_panel_days} days</strong>
                </span>
              </div>

              {/* Urgency bar */}
              <div className="mt-4 h-2 bg-white/60 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${urgencyStyle.bar}`}
                  style={{ width: `${Math.round(action.urgency_score * 100)}%` }}
                />
              </div>
            </div>
          )}

          {/* ── 2. BIOLOGICAL AGE ────────────────────────────────────────── */}
          {pa && (
            <Card>
              <SectionLabel>Biological Age — Levine 2018 Gompertz Model</SectionLabel>

              {pa.phenoage_estimate !== null ? (
                <div className="space-y-4">
                  <div className={`rounded-xl border p-4 ${ageBg}`}>
                    <div className="flex items-end gap-6 flex-wrap">
                      <div>
                        <div className={`text-6xl font-black tabular-nums ${ageColor}`}>
                          {pa.phenoage_estimate.toFixed(1)}
                          <span className="text-2xl font-bold ml-1 text-gray-500">yr</span>
                        </div>
                        <div className="text-sm text-gray-600 font-semibold mt-1">Biological Age</div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-500 font-medium">Chronological:</span>
                          <span className="text-lg font-black text-gray-800">{pa.age_years} yr</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-500 font-medium">Acceleration:</span>
                          <span className={`text-lg font-black ${ageColor}`}>
                            {accel !== null ? (accel > 0 ? `+${accel.toFixed(1)}` : accel.toFixed(1)) : "—"} yr
                          </span>
                        </div>
                        {pa.mortality_score_10yr !== null && (
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-500 font-medium">10yr mortality score:</span>
                            <span className={`text-sm font-black ${(pa.mortality_score_10yr || 0) > 0.15 ? "text-red-600" : "text-gray-700"}`}>
                              {((pa.mortality_score_10yr || 0) * 100).toFixed(1)}%
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* What this means for the doctor */}
                  <div className="bg-gray-50 rounded-xl p-4 border border-gray-100">
                    <div className="text-xs font-black text-gray-400 uppercase tracking-wider mb-2">What This Means</div>
                    <p className="text-sm text-gray-700 leading-relaxed">
                      {isAccel && accel !== null && accel > 10
                        ? `This patient's biology is running ${accel.toFixed(1)} years ahead of their calendar age. The 10-year mortality score of ${((pa.mortality_score_10yr || 0) * 100).toFixed(1)}% is significantly elevated. Immediate intervention is indicated.`
                        : isAccel && accel !== null
                        ? `Mild biological age acceleration of ${accel.toFixed(1)} years. No single marker is flagged as abnormal, but the multi-marker pattern is real. This is the "deceptive optimizer" phenotype — looks healthy, isn't.`
                        : isDecel && accel !== null
                        ? `Exceptional biological age deceleration of ${Math.abs(accel).toFixed(1)} years. This patient's biology is running significantly younger than their calendar age. Maintain current protocol.`
                        : "Biological age is near chronological age. No significant acceleration or deceleration detected."
                      }
                    </p>
                  </div>

                  {/* Top accelerators */}
                  {pa.top_accelerators && pa.top_accelerators.length > 0 && (
                    <div>
                      <div className="text-xs font-black text-gray-400 uppercase tracking-wider mb-2">Driving Accelerators</div>
                      <div className="space-y-2">
                        {pa.top_accelerators.map((comp) => (
                          <div key={comp.canonical_key} className="flex items-center gap-3 bg-red-50 border border-red-100 rounded-xl px-3 py-2">
                            <span className="w-2.5 h-2.5 rounded-full bg-red-500 shrink-0" />
                            <span className="text-sm font-bold text-gray-800 flex-1">{comp.label}</span>
                            <span className="text-sm font-mono text-gray-600">{comp.value} {comp.unit}</span>
                            {comp.primary_hallmark && (
                              <span className="text-xs text-gray-400 hidden md:block">→ {HALLMARK_LABELS[comp.primary_hallmark] || comp.primary_hallmark}</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-5">
                  <div className="text-base font-black text-amber-900 mb-2">Partial Panel — Full Estimate Not Available</div>
                  <p className="text-sm text-amber-800 leading-relaxed mb-3">
                    {pa.components_available}/{pa.components_total} biomarkers provided. Full PhenoAge estimate requires all 9 markers + chronological age.
                    The 5 markers present all look favorable — but we can't compute a biological age without the full panel.
                  </p>
                  {completeness?.phenoage_panel_diagnosis?.phenoage_canonical_missing_for_full && (
                    <div>
                      <div className="text-xs font-black text-amber-700 uppercase tracking-wider mb-2">Missing Markers</div>
                      <div className="flex flex-wrap gap-2">
                        {completeness.phenoage_panel_diagnosis.phenoage_canonical_missing_for_full.map((m) => (
                          <span key={m} className="text-sm font-mono font-bold bg-amber-100 text-amber-900 border border-amber-300 px-2.5 py-1 rounded-lg">{m}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </Card>
          )}

          {/* ── 3. HALLMARK NARRATIVE ────────────────────────────────────── */}
          {hallmarkEntries.length > 0 && (
            <Card>
              <SectionLabel>Hallmarks of Aging — Active Drivers</SectionLabel>
              <div className="space-y-4">
                {hallmarkEntries.map(([hm, entry]) => {
                  const totalSignal = (entry.phenoage_signal || 0) + (entry.supplementary_signal || 0);
                  const maxSignal = 0.3;
                  const pct = Math.min(100, Math.round((totalSignal / maxSignal) * 100));
                  const isPrimary = entry.status === "PRIMARY_DRIVER";
                  const isSecondary = entry.status === "SECONDARY_DRIVER";
                  const isOptimal = entry.status === "OPTIMAL";

                  return (
                    <div key={hm} className={`rounded-xl border p-4 ${
                      isPrimary ? "bg-red-50 border-red-200" :
                      isSecondary ? "bg-orange-50 border-orange-200" :
                      "bg-emerald-50 border-emerald-200"
                    }`}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className={`text-xs font-black px-2.5 py-1 rounded-full ${
                            isPrimary ? "bg-red-100 text-red-800 border border-red-300" :
                            isSecondary ? "bg-orange-100 text-orange-800 border border-orange-300" :
                            "bg-emerald-100 text-emerald-800 border border-emerald-300"
                          }`}>
                            {entry.status.replace(/_/g, " ")}
                          </span>
                          <span className="text-sm font-black text-gray-900">{HALLMARK_LABELS[hm] || hm}</span>
                        </div>
                        <span className="text-xs font-mono text-gray-500">signal {totalSignal.toFixed(3)}</span>
                      </div>

                      {/* Signal bar */}
                      {!isOptimal && (
                        <div className="h-2 bg-white/60 rounded-full overflow-hidden mb-3">
                          <div
                            className={`h-full rounded-full ${isPrimary ? "bg-red-500" : "bg-orange-400"}`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      )}

                      {/* Narrative */}
                      {entry.narrative && (
                        <p className="text-sm text-gray-700 leading-relaxed mb-2">{entry.narrative}</p>
                      )}

                      {/* Driving biomarkers */}
                      {([...entry.driving_biomarkers_phenoage, ...entry.driving_biomarkers_supplementary]).length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                          {[...entry.driving_biomarkers_phenoage, ...entry.driving_biomarkers_supplementary].map((b) => (
                            <span key={b} className="text-xs font-mono font-bold bg-white border border-gray-200 text-gray-600 px-2 py-0.5 rounded-lg">{b}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </Card>
          )}

          {/* ── 4. GENETIC PROFILE ──────────────────────────────────────── */}
          {genetic && (genetic.apoe_status || genetic.mthfr_status || (genetic.variant_annotations && Object.keys(genetic.variant_annotations).length > 0)) && (
            <Card>
              <SectionLabel>Genetic Profile</SectionLabel>
              <div className="space-y-3">
                {genetic.apoe_status && (
                  <div className={`rounded-xl border p-4 ${RISK_STYLES[genetic.apoe_status.risk_tier] || "bg-gray-50 border-gray-200"}`}>
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div>
                        <span className="text-base font-black text-gray-900">APOE {genetic.apoe_status.genotype}</span>
                        <span className="ml-2 text-sm font-bold text-rose-700">{genetic.apoe_status.ad_risk_or} AD risk vs e3/e3</span>
                      </div>
                      <span className="text-xs font-black px-2.5 py-1 rounded-full bg-rose-100 text-rose-800 border border-rose-300 shrink-0">
                        {genetic.apoe_status.risk_tier}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 leading-relaxed">{genetic.apoe_status.longevity_impact}</p>
                  </div>
                )}

                {genetic.mthfr_status && (
                  <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <span className="text-base font-black text-gray-900">MTHFR {genetic.mthfr_status.c677t}/{genetic.mthfr_status.a1298c}</span>
                      <span className="text-xs font-black px-2.5 py-1 rounded-full bg-amber-100 text-amber-800 border border-amber-300 shrink-0">
                        {genetic.mthfr_status.activity_label}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-1">
                      Enzyme activity: <strong className="text-gray-900">{Math.round((genetic.mthfr_status.enzyme_activity_estimate || 0) * 100)}%</strong>
                    </p>
                    <p className="text-sm text-gray-700 leading-relaxed">{genetic.mthfr_status.recommendation}</p>
                  </div>
                )}

                {genetic.variant_annotations && Object.entries(genetic.variant_annotations).map(([rsid, ann]) => (
                  <div key={rsid} className={`rounded-xl border p-4 ${IMPACT_STYLES[ann.impact] || "bg-gray-50 border-gray-200"}`}>
                    <div className="flex items-start gap-3">
                      <div className="shrink-0">
                        <div className="text-base font-black text-gray-900">{ann.gene}</div>
                        <div className="text-xs font-mono text-gray-500">{rsid}</div>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-bold text-gray-700">{ann.zygosity.replace(/_/g, " ")}</span>
                          <span className={`text-xs font-black px-2 py-0.5 rounded-full ${
                            ann.impact === "FAVORABLE" ? "bg-emerald-200 text-emerald-900" : "bg-gray-200 text-gray-700"
                          }`}>{ann.impact}</span>
                        </div>
                        <p className="text-sm text-gray-700 leading-relaxed">{ann.note}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* ── 5. COMPOUND RECOMMENDATIONS ─────────────────────────────── */}
          {compounds.length > 0 && (
            <Card>
              <SectionLabel>Compound Recommendations — Ranked by Relevance</SectionLabel>
              <div className="space-y-3">
                {compounds.map((c, i) => (
                  <div key={c.compound} className={`rounded-xl border p-4 ${i === 0 ? "bg-gray-900 border-gray-700" : "bg-gray-50 border-gray-200"}`}>
                    <div className="flex items-start gap-3">
                      <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 font-black text-sm ${
                        i === 0 ? "bg-white text-gray-900" : "bg-gray-200 text-gray-600"
                      }`}>
                        {i + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap mb-1">
                          <span className={`text-base font-black ${i === 0 ? "text-white" : "text-gray-900"}`}>
                            {c.display_name || c.compound}
                          </span>
                          <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${TIER_COLORS[c.evidence_tier] || "bg-gray-100 text-gray-600 border-gray-200"}`}>
                            {c.evidence_tier}
                          </span>
                        </div>
                        {c.primary_match && (
                          <p className={`text-sm font-medium mb-1 ${i === 0 ? "text-gray-300" : "text-gray-600"}`}>
                            Targets: {HALLMARK_LABELS[c.primary_match] || c.primary_match}
                          </p>
                        )}
                        {c.mr_anchor && (
                          <p className={`text-xs mb-1 ${i === 0 ? "text-gray-400" : "text-gray-500"}`}>
                            MR anchor: {c.mr_anchor.citation} · p={c.mr_anchor.p_value} · {c.mr_anchor.clock}
                          </p>
                        )}
                        {c.dose && (
                          <p className={`text-sm font-semibold ${i === 0 ? "text-emerald-400" : "text-gray-700"}`}>
                            {c.dose}
                          </p>
                        )}
                      </div>
                      <div className="shrink-0 text-right">
                        <div className={`text-2xl font-black tabular-nums ${i === 0 ? "text-white" : "text-gray-900"}`}>
                          {Math.round((c.overall_relevance || 0) * 100)}
                        </div>
                        <div className={`text-[10px] font-medium ${i === 0 ? "text-gray-400" : "text-gray-400"}`}>relevance</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* ── 6. DATA COMPLETENESS ─────────────────────────────────────── */}
          {completeness && (
            <div className="bg-gray-50 border border-gray-200 rounded-2xl p-5">
              <SectionLabel>Data Completeness</SectionLabel>
              <p className="text-sm text-gray-700 leading-relaxed mb-3">{completeness.recommendation}</p>
              <div className="flex gap-6 text-sm text-gray-600">
                <span>Hallmarks scored: <strong className="text-gray-900">{completeness.hallmarks_scoreable}</strong></span>
                <span>PhenoAge complete: <strong className={completeness.phenoage_complete_for_full_estimate ? "text-emerald-700" : "text-amber-700"}>
                  {completeness.phenoage_complete_for_full_estimate ? "Yes" : "No"}
                </strong></span>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
