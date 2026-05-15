"use client";

import { useState } from "react";
import { TestOrder, RecommendedPanel, testOrdersApi } from "@/lib/api";

interface Props {
  patientId: string;
  order: TestOrder;
  onApproved: (orderId: string) => void;
  onCancel: () => void;
}

const priorityConfig = {
  urgent: { label: "Urgent", className: "bg-red-100 text-red-800 border-red-200" },
  high: { label: "High", className: "bg-orange-100 text-orange-800 border-orange-200" },
  routine: { label: "Routine", className: "bg-blue-100 text-blue-800 border-blue-200" },
};

const tierConfig = {
  tier_1: { label: "Baseline", className: "bg-green-100 text-green-700" },
  tier_2: { label: "Expanded", className: "bg-blue-100 text-blue-700" },
  tier_3: { label: "Specialty", className: "bg-purple-100 text-purple-700" },
};

export function TestOrderReview({ patientId, order, onApproved, onCancel }: Props) {
  const [selectedPanels, setSelectedPanels] = useState<Set<string>>(
    new Set(order.recommended_panels.map((p) => p.panel_id))
  );
  const [notes, setNotes] = useState("");
  const [approving, setApproving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const togglePanel = (panelId: string) => {
    setSelectedPanels((prev) => {
      const next = new Set(prev);
      if (next.has(panelId)) next.delete(panelId);
      else next.add(panelId);
      return next;
    });
  };

  const selectedPanelDetails = order.recommended_panels.filter((p) =>
    selectedPanels.has(p.panel_id)
  );
  const totalCost = selectedPanelDetails.reduce(
    (sum, p) => sum + (p.approximate_cost_usd || 0),
    0
  );
  const fastingRequired = selectedPanelDetails.some((p) => p.fasting_required);
  const specimenTypes = [...new Set(selectedPanelDetails.flatMap((p) => p.specimen_types))];

  const handleApprove = async () => {
    setApproving(true);
    setError(null);
    try {
      const result = await testOrdersApi.approve(
        patientId,
        notes || undefined,
        [...selectedPanels]
      );
      onApproved(result.order_id);
    } catch (e: any) {
      setError(e.message || "Failed to approve order");
    } finally {
      setApproving(false);
    }
  };

  const { summary, ordering_rationale } = order;

  return (
    <div className="space-y-6">
      {/* Summary bar */}
      <div className="bg-gray-50 rounded-xl border border-gray-200 p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <SummaryCell
            label="Panels Selected"
            value={`${selectedPanels.size} / ${order.recommended_panels.length}`}
          />
          <SummaryCell
            label="Est. Cost"
            value={`$${totalCost.toLocaleString()}`}
          />
          <SummaryCell
            label="Tier-1 Coverage"
            value={`${summary.tier1_coverage_pct}%`}
            valueClass={
              summary.tier1_coverage_pct >= 80 ? "text-green-600" :
              summary.tier1_coverage_pct >= 50 ? "text-yellow-600" :
              "text-red-600"
            }
          />
          <SummaryCell
            label="Escalation Rules"
            value={String(summary.escalation_rules_triggered)}
            valueClass={summary.escalation_rules_triggered > 0 ? "text-orange-600" : "text-gray-700"}
          />
        </div>
        {fastingRequired && (
          <div className="mt-3 flex items-center gap-2 text-sm text-amber-700 bg-amber-50 rounded-lg px-3 py-2">
            <span>⚠</span>
            <span>Fasting required for some panels. Patient must fast 8–12 hours before blood draw.</span>
          </div>
        )}
        {specimenTypes.length > 1 && (
          <div className="mt-2 text-xs text-gray-500">
            Specimen types: {specimenTypes.join(", ")}
          </div>
        )}
      </div>

      {/* Rationale summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <RationaleCard
          title="Gap Detection"
          icon="🔍"
          items={[
            `${ordering_rationale.gap_detection.missing_tier1_count} baseline markers missing`,
            `${ordering_rationale.gap_detection.missing_panels.length} baseline panels needed`,
          ]}
        />
        <RationaleCard
          title="Hallmark-Driven"
          icon="🧬"
          items={
            ordering_rationale.hallmark_driven.active_hallmarks.length > 0
              ? ordering_rationale.hallmark_driven.active_hallmarks.map(
                  (h) => h.replace(/_/g, " ")
                )
              : ["No active hallmarks detected"]
          }
        />
        <RationaleCard
          title="Escalation Rules"
          icon="⚡"
          items={
            ordering_rationale.escalation.triggered_rules.length > 0
              ? ordering_rationale.escalation.triggered_rules.slice(0, 3).map(
                  (r) => `${r.trigger_marker} = ${r.trigger_value}`
                )
              : ["No escalation rules triggered"]
          }
        />
      </div>

      {/* Panel list */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-semibold text-gray-900">
            Recommended Panels
          </h4>
          <div className="flex gap-2">
            <button
              onClick={() =>
                setSelectedPanels(new Set(order.recommended_panels.map((p) => p.panel_id)))
              }
              className="text-xs text-blue-600 hover:underline"
            >
              Select all
            </button>
            <span className="text-gray-300">|</span>
            <button
              onClick={() => setSelectedPanels(new Set())}
              className="text-xs text-gray-500 hover:underline"
            >
              Clear all
            </button>
          </div>
        </div>

        <div className="space-y-2">
          {order.recommended_panels.map((panel) => (
            <PanelRow
              key={panel.panel_id}
              panel={panel}
              selected={selectedPanels.has(panel.panel_id)}
              onToggle={() => togglePanel(panel.panel_id)}
            />
          ))}
        </div>
      </div>

      {/* Notes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Clinician Notes (optional)
        </label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={2}
          placeholder="Add notes for this order..."
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3 justify-end">
        <button
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          onClick={handleApprove}
          disabled={approving || selectedPanels.size === 0}
          className="px-5 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {approving ? "Saving..." : `Approve & Save (${selectedPanels.size} panels)`}
        </button>
      </div>
    </div>
  );
}

function SummaryCell({
  label,
  value,
  valueClass = "text-gray-900",
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div>
      <div className={`text-xl font-bold ${valueClass}`}>{value}</div>
      <div className="text-xs text-gray-500 mt-0.5">{label}</div>
    </div>
  );
}

function RationaleCard({
  title,
  icon,
  items,
}: {
  title: string;
  icon: string;
  items: string[];
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-3">
      <div className="flex items-center gap-1.5 mb-2">
        <span>{icon}</span>
        <span className="text-xs font-semibold text-gray-700">{title}</span>
      </div>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="text-xs text-gray-600 flex items-start gap-1">
            <span className="text-gray-400 mt-0.5">•</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function PanelRow({
  panel,
  selected,
  onToggle,
}: {
  panel: RecommendedPanel;
  selected: boolean;
  onToggle: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const priority = priorityConfig[panel.priority] || priorityConfig.routine;
  const tier = tierConfig[panel.ordering_tier as keyof typeof tierConfig] || tierConfig.tier_2;

  return (
    <div
      className={`rounded-lg border transition-colors ${
        selected
          ? "border-blue-300 bg-blue-50"
          : "border-gray-200 bg-white opacity-60"
      }`}
    >
      <div className="flex items-center gap-3 p-3">
        <input
          type="checkbox"
          checked={selected}
          onChange={onToggle}
          className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-gray-900">
              {panel.display_name}
            </span>
            <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium border ${priority.className}`}>
              {priority.label}
            </span>
            <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${tier.className}`}>
              {tier.label}
            </span>
            {panel.fasting_required && (
              <span className="text-xs text-amber-600">Fasting</span>
            )}
          </div>
          {panel.reasons[0] && (
            <p className="text-xs text-gray-500 mt-0.5 truncate">
              {panel.reasons[0]}
            </p>
          )}
        </div>
        <div className="text-right shrink-0">
          <div className="text-sm font-semibold text-gray-900">
            ${panel.approximate_cost_usd}
          </div>
          <div className="text-xs text-gray-400">
            {panel.markers.length} markers
          </div>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-gray-400 hover:text-gray-600 text-xs px-1"
        >
          {expanded ? "▲" : "▼"}
        </button>
      </div>

      {expanded && (
        <div className="px-4 pb-3 border-t border-gray-100 pt-2 space-y-2">
          <div className="flex flex-wrap gap-1">
            {panel.markers.map((m) => (
              <span
                key={m}
                className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-gray-100 text-gray-600"
              >
                {m.replace(/_/g, " ")}
              </span>
            ))}
          </div>
          {panel.reasons.length > 1 && (
            <div className="space-y-1">
              {panel.reasons.slice(1).map((r, i) => (
                <p key={i} className="text-xs text-gray-500">• {r}</p>
              ))}
            </div>
          )}
          <div className="flex gap-4 text-xs text-gray-500">
            {panel.quest_panel_code && <span>Quest: {panel.quest_panel_code}</span>}
            {panel.labcorp_panel_code && <span>LabCorp: {panel.labcorp_panel_code}</span>}
            {panel.turnaround_days && <span>TAT: {panel.turnaround_days}d</span>}
            <span>Specimen: {panel.specimen_types.join(", ")}</span>
          </div>
        </div>
      )}
    </div>
  );
}
