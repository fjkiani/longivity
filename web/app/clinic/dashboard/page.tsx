"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { IntelligenceResponse, intelligenceApi } from "@/lib/api";

// ─── Helpers ──────────────────────────────────────────────────────────────────

const STATE_COLORS: Record<string, string> = {
  NEW: "bg-gray-100 text-gray-600",
  DATA_INCOMPLETE: "bg-yellow-100 text-yellow-800",
  ASSESSMENT_PENDING: "bg-blue-100 text-blue-800",
  ORDER_PENDING: "bg-orange-100 text-orange-800",
  COMPOUND_CANDIDATE: "bg-purple-100 text-purple-800",
  MONITORING: "bg-green-100 text-green-800",
};

const ALL_STATES = [
  "NEW",
  "DATA_INCOMPLETE",
  "ASSESSMENT_PENDING",
  "ORDER_PENDING",
  "COMPOUND_CANDIDATE",
  "MONITORING",
];

function UrgencyBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 70 ? "bg-red-500" : pct >= 40 ? "bg-orange-400" : "bg-green-400";
  return (
    <div className="flex items-center gap-2 w-32">
      <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-gray-400 w-6">{pct}</span>
    </div>
  );
}

// ─── Worklist Row ─────────────────────────────────────────────────────────────

function WorklistRow({ intel }: { intel: IntelligenceResponse }) {
  const stateColor = STATE_COLORS[intel.current_state] ?? "bg-gray-100 text-gray-600";
  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
      <td className="py-3 px-4">
        <Link
          href={`/patients/${intel.patient_id}`}
          className="font-medium text-blue-600 hover:underline text-sm"
        >
          {intel.patient_id}
        </Link>
      </td>
      <td className="py-3 px-4">
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${stateColor}`}>
          {intel.current_state_label ?? intel.current_state}
        </span>
      </td>
      <td className="py-3 px-4">
        <UrgencyBar score={intel.urgency_score} />
      </td>
      <td className="py-3 px-4 text-sm text-gray-700 max-w-xs truncate">
        {intel.next_action?.label ?? "—"}
      </td>
      <td className="py-3 px-4 text-xs text-gray-400">
        {intel.biological_summary.phenoage_estimate != null
          ? `${intel.biological_summary.phenoage_estimate.toFixed(1)} yr`
          : "—"}
      </td>
      <td className="py-3 px-4 text-xs text-gray-400">
        {intel.gap_summary.tier1_coverage_pct.toFixed(0)}%
      </td>
      <td className="py-3 px-4">
        {intel.next_action?.cta_url ? (
          <Link
            href={intel.next_action.cta_url}
            className="text-xs bg-blue-600 text-white px-3 py-1 rounded-md hover:bg-blue-700"
          >
            {intel.next_action.cta_label ?? "Act"}
          </Link>
        ) : (
          <Link
            href={`/patients/${intel.patient_id}`}
            className="text-xs text-blue-600 hover:underline"
          >
            View
          </Link>
        )}
      </td>
    </tr>
  );
}

// ─── Grid Card ────────────────────────────────────────────────────────────────

function GridCard({ intel }: { intel: IntelligenceResponse }) {
  const stateColor = STATE_COLORS[intel.current_state] ?? "bg-gray-100 text-gray-600";
  const urgencyPct = Math.round(intel.urgency_score * 100);
  const urgencyColor =
    urgencyPct >= 70
      ? "text-red-600"
      : urgencyPct >= 40
      ? "text-orange-500"
      : "text-green-600";

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <Link
          href={`/patients/${intel.patient_id}`}
          className="font-semibold text-blue-600 hover:underline text-sm"
        >
          {intel.patient_id}
        </Link>
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${stateColor}`}>
          {intel.current_state_label ?? intel.current_state}
        </span>
      </div>

      {/* PhenoAge gauge */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-xs text-gray-400">PhenoAge</div>
          <div className="text-lg font-bold text-gray-900">
            {intel.biological_summary.phenoage_estimate != null
              ? `${intel.biological_summary.phenoage_estimate.toFixed(1)}`
              : "—"}
            <span className="text-xs font-normal text-gray-400 ml-1">yr</span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-400">Urgency</div>
          <div className={`text-lg font-bold ${urgencyColor}`}>{urgencyPct}</div>
        </div>
      </div>

      {/* Hallmarks */}
      {intel.biological_summary.hallmarks_activated.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {intel.biological_summary.hallmarks_activated.slice(0, 3).map((h) => (
            <span
              key={h}
              className="px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 text-xs"
            >
              {h.replace(/_/g, " ")}
            </span>
          ))}
        </div>
      )}

      {/* Next action */}
      {intel.next_action && (
        <div className="border-t border-gray-100 pt-3 mt-3">
          <div className="text-xs text-gray-500 mb-1">Next action</div>
          <div className="text-xs font-medium text-gray-800 truncate">
            {intel.next_action.label}
          </div>
          {intel.next_action.cta_url && (
            <Link
              href={intel.next_action.cta_url}
              className="mt-2 block text-center text-xs bg-blue-600 text-white px-3 py-1.5 rounded-md hover:bg-blue-700"
            >
              {intel.next_action.cta_label ?? "Act"}
            </Link>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

type ViewMode = "worklist" | "grid";

export default function ClinicDashboardPage() {
  const [patients, setPatients] = useState<IntelligenceResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<ViewMode>("worklist");
  const [stateFilter, setStateFilter] = useState<string>("");
  const [minUrgency, setMinUrgency] = useState<number>(0);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await intelligenceApi.getClinicIntelligence({
        state: stateFilter || undefined,
        min_urgency: minUrgency > 0 ? minUrgency : undefined,
        limit: 100,
      });
      setPatients(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [stateFilter, minUrgency]);

  useEffect(() => {
    load();
  }, [load]);

  // Persist view preference
  useEffect(() => {
    const saved = localStorage.getItem("clinic_dashboard_view") as ViewMode | null;
    if (saved) setView(saved);
  }, []);

  const setViewAndSave = (v: ViewMode) => {
    setView(v);
    localStorage.setItem("clinic_dashboard_view", v);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Clinic Dashboard</h1>
            <p className="text-sm text-gray-500 mt-1">
              {patients.length} patient{patients.length !== 1 ? "s" : ""} · sorted by urgency
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setViewAndSave("worklist")}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                view === "worklist"
                  ? "bg-blue-600 text-white"
                  : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
              }`}
            >
              ☰ Worklist
            </button>
            <button
              onClick={() => setViewAndSave("grid")}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                view === "grid"
                  ? "bg-blue-600 text-white"
                  : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
              }`}
            >
              ⊞ Grid
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 mb-6 flex-wrap">
          <select
            value={stateFilter}
            onChange={(e) => setStateFilter(e.target.value)}
            className="text-sm border border-gray-300 rounded-md px-3 py-1.5 bg-white text-gray-700"
          >
            <option value="">All states</option>
            {ALL_STATES.map((s) => (
              <option key={s} value={s}>
                {s.replace(/_/g, " ")}
              </option>
            ))}
          </select>
          <select
            value={minUrgency}
            onChange={(e) => setMinUrgency(Number(e.target.value))}
            className="text-sm border border-gray-300 rounded-md px-3 py-1.5 bg-white text-gray-700"
          >
            <option value={0}>All urgency</option>
            <option value={0.3}>≥ 30 urgency</option>
            <option value={0.5}>≥ 50 urgency</option>
            <option value={0.7}>≥ 70 urgency (high)</option>
          </select>
          <button
            onClick={load}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            ↻ Refresh
          </button>
        </div>

        {/* Content */}
        {loading ? (
          <div className="text-center py-16 text-gray-400 text-sm">
            Loading clinic intelligence…
          </div>
        ) : error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        ) : patients.length === 0 ? (
          <div className="text-center py-16 text-gray-400 text-sm">
            No patients match the current filters.
          </div>
        ) : view === "worklist" ? (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  {[
                    "Patient",
                    "State",
                    "Urgency",
                    "Next Action",
                    "PhenoAge",
                    "Coverage",
                    "",
                  ].map((h) => (
                    <th
                      key={h}
                      className="py-3 px-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {patients.map((p) => (
                  <WorklistRow key={p.patient_id} intel={p} />
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {patients.map((p) => (
              <GridCard key={p.patient_id} intel={p} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
