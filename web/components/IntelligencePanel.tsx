"use client";

import React, { useState } from "react";
import {
  IntelligenceResponse,
  ScoredAction,
  intelligenceApi,
} from "@/lib/api";

// ─── Helpers ──────────────────────────────────────────────────────────────────

const STATE_COLORS: Record<string, string> = {
  NEW: "bg-gray-100 text-gray-700",
  DATA_INCOMPLETE: "bg-yellow-100 text-yellow-800",
  ASSESSMENT_PENDING: "bg-blue-100 text-blue-800",
  ORDER_PENDING: "bg-orange-100 text-orange-800",
  COMPOUND_CANDIDATE: "bg-purple-100 text-purple-800",
  MONITORING: "bg-green-100 text-green-800",
};

const URGENCY_COLORS: Record<string, string> = {
  high: "bg-red-500",
  medium: "bg-orange-400",
  low: "bg-yellow-400",
  routine: "bg-green-400",
};

const ACTION_ICONS: Record<string, string> = {
  order_baseline_panel: "🧪",
  order_escalation_panel: "⚠️",
  run_assessment: "📊",
  review_assessment: "👁️",
  start_compound: "💊",
  schedule_followup: "📅",
  upload_results: "📤",
};

function UrgencyBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 70 ? "bg-red-500" : pct >= 40 ? "bg-orange-400" : "bg-green-400";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-gray-500 w-8">{pct}%</span>
    </div>
  );
}

function ActionCard({ action, primary }: { action: ScoredAction; primary?: boolean }) {
  const icon = ACTION_ICONS[action.type] || "▶️";
  const urgencyColor = URGENCY_COLORS[action.urgency] || "bg-gray-400";
  return (
    <div
      className={`rounded-lg border p-4 ${
        primary ? "border-blue-400 bg-blue-50 shadow-sm" : "border-gray-200 bg-white"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <span className="text-2xl">{icon}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-gray-900 text-sm">{action.label}</span>
              <span
                className={`inline-block w-2 h-2 rounded-full ${urgencyColor}`}
                title={action.urgency}
              />
              <span className="text-xs text-gray-400 capitalize">{action.urgency}</span>
            </div>
            <p className="text-xs text-gray-600 mt-1 leading-relaxed">{action.reason}</p>
          </div>
        </div>
        <div className="flex flex-col items-end gap-2 shrink-0">
          <span className="text-xs font-mono text-gray-400">
            {Math.round(action.score * 100)}
          </span>
          {action.cta_url && action.cta_label && (
            <a
              href={action.cta_url}
              className="text-xs bg-blue-600 text-white px-3 py-1 rounded-md hover:bg-blue-700 whitespace-nowrap"
            >
              {action.cta_label}
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

interface Props {
  patientId: string;
  initial?: IntelligenceResponse | null;
}

export default function IntelligencePanel({ patientId, initial }: Props) {
  const [intel, setIntel] = useState<IntelligenceResponse | null>(initial ?? null);
  const [loading, setLoading] = useState(!initial);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  React.useEffect(() => {
    if (!initial) {
      intelligenceApi
        .getPatientIntelligence(patientId)
        .then(setIntel)
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }
  }, [patientId, initial]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const fresh = await intelligenceApi.getPatientIntelligence(patientId, true);
      setIntel(fresh);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Refresh failed");
    } finally {
      setRefreshing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        Computing patient intelligence…
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        {error}
      </div>
    );
  }

  if (!intel) return null;

  const { biological_summary: bio, gap_summary: gap, timeline_summary: tl } = intel;

  return (
    <div className="space-y-6">
      {/* Header row */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <span
            className={`px-3 py-1 rounded-full text-xs font-semibold ${
              STATE_COLORS[intel.current_state] ?? "bg-gray-100 text-gray-700"
            }`}
          >
            {intel.current_state_label ?? intel.current_state}
          </span>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Urgency</span>
            <UrgencyBar score={intel.urgency_score} />
          </div>
        </div>
        <div className="flex items-center gap-2">
          {intel.cache_hit && (
            <span className="text-xs text-gray-400">
              Cached · {new Date(intel.computed_at).toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="text-xs text-blue-600 hover:text-blue-800 disabled:opacity-50"
          >
            {refreshing ? "Refreshing…" : "↻ Refresh"}
          </button>
        </div>
      </div>

      {/* Next action (primary) */}
      {intel.next_action && (
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            Recommended Next Action
          </h3>
          <ActionCard action={intel.next_action} primary />
        </div>
      )}

      {/* Biological summary strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          {
            label: "PhenoAge",
            value:
              bio.phenoage_estimate != null
                ? `${bio.phenoage_estimate.toFixed(1)} yr`
                : "—",
            sub:
              bio.age_acceleration != null
                ? `${bio.age_acceleration > 0 ? "+" : ""}${bio.age_acceleration.toFixed(1)} yr`
                : null,
            subColor:
              (bio.age_acceleration ?? 0) > 2
                ? "text-red-500"
                : (bio.age_acceleration ?? 0) > 0
                ? "text-orange-500"
                : "text-green-500",
          },
          {
            label: "Tier-1 Coverage",
            value: `${gap.tier1_coverage_pct.toFixed(0)}%`,
            sub: `${gap.missing_tier1_count} missing`,
            subColor: "text-gray-400",
          },
          {
            label: "Escalation Rules",
            value: String(gap.escalation_rules_firing),
            sub: gap.escalation_rules_firing > 0 ? "firing" : "none",
            subColor:
              gap.escalation_rules_firing > 0 ? "text-orange-500" : "text-green-500",
          },
          {
            label: "Panels",
            value: String(tl.panel_count),
            sub: tl.latest_panel_date
              ? `Last: ${new Date(tl.latest_panel_date).toLocaleDateString()}`
              : "No panels",
            subColor: "text-gray-400",
          },
        ].map((stat) => (
          <div
            key={stat.label}
            className="rounded-lg border border-gray-200 bg-white p-3 text-center"
          >
            <div className="text-xs text-gray-500 mb-1">{stat.label}</div>
            <div className="text-xl font-bold text-gray-900">{stat.value}</div>
            {stat.sub && (
              <div className={`text-xs mt-0.5 ${stat.subColor}`}>{stat.sub}</div>
            )}
          </div>
        ))}
      </div>

      {/* Hallmarks */}
      {bio.hallmarks_activated.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            Active Hallmarks
          </h3>
          <div className="flex flex-wrap gap-2">
            {bio.hallmarks_activated.map((h) => (
              <span
                key={h}
                className="px-2 py-1 rounded-full bg-purple-100 text-purple-800 text-xs font-medium"
              >
                {h.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Top compound */}
      {intel.top_compound && (
        <div className="rounded-lg border border-purple-200 bg-purple-50 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-purple-600 uppercase tracking-wide mb-1">
                Top Compound Candidate
              </div>
              <div className="font-semibold text-gray-900">
                {intel.top_compound.display_name}
              </div>
              <div className="text-xs text-gray-500 mt-0.5">
                {intel.top_compound.hallmark.replace(/_/g, " ")} ·{" "}
                {intel.top_compound.evidence_tier}
              </div>
            </div>
            <div className="text-2xl font-bold text-purple-700">
              {Math.round(intel.top_compound.relevance_score * 100)}
              <span className="text-sm font-normal text-purple-400">/100</span>
            </div>
          </div>
        </div>
      )}

      {/* Available actions */}
      {intel.available_actions.length > 1 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            All Available Actions
          </h3>
          <div className="space-y-2">
            {intel.available_actions.slice(1).map((action) => (
              <ActionCard key={action.type} action={action} />
            ))}
          </div>
        </div>
      )}

      {/* Scoring breakdown (collapsed) */}
      <details className="text-xs text-gray-400">
        <summary className="cursor-pointer hover:text-gray-600">
          Scoring breakdown
        </summary>
        <div className="mt-2 grid grid-cols-2 gap-1 font-mono">
          {Object.entries(intel.scoring_breakdown)
            .filter(([k]) => k !== "weights")
            .map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <span>{k}</span>
                <span>{typeof v === "number" ? v.toFixed(3) : String(v)}</span>
              </div>
            ))}
        </div>
      </details>
    </div>
  );
}
