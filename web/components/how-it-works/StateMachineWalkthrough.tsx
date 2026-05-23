"use client";
import { useState } from "react";

const STATES = [
  {
    id: "NEW",
    label: "New Patient",
    color: "bg-gray-100 border-gray-300 text-gray-700",
    activeColor: "bg-gray-800 text-white border-gray-800",
    description: "Patient just created. No panels, no assessment, no orders.",
    action: "Order baseline panel",
    actionColor: "text-gray-600",
    conditions: ["No panels exist"],
    scenario: {
      patient: "Dr. Chen just added Marcus Webb, 52M.",
      panels: 0,
      assessment: false,
      orders: 0,
      urgency: 0.3,
    },
  },
  {
    id: "DATA_INCOMPLETE",
    label: "Data Incomplete",
    color: "bg-amber-100 border-amber-300 text-amber-800",
    activeColor: "bg-amber-600 text-white border-amber-600",
    description: "Has panels but Tier 1 coverage < 60%. Missing critical markers.",
    action: "Order gap-filling panel",
    actionColor: "text-amber-600",
    conditions: ["Has ≥1 panel", "Tier 1 coverage < 60%"],
    scenario: {
      patient: "Marcus has a CMP from last month. Missing CRP, lymphocyte %, RDW.",
      panels: 1,
      assessment: false,
      orders: 0,
      urgency: 0.55,
      coverage: "31%",
      missing: ["CRP", "Lymphocyte %", "RDW", "Alk Phos"],
    },
  },
  {
    id: "ASSESSMENT_PENDING",
    label: "Assessment Pending",
    color: "bg-blue-100 border-blue-300 text-blue-800",
    activeColor: "bg-blue-600 text-white border-blue-600",
    description: "Has sufficient data but no assessment has been run yet.",
    action: "Run assessment",
    actionColor: "text-blue-600",
    conditions: ["Has ≥1 panel", "Coverage ≥ 60%", "No assessment run"],
    scenario: {
      patient: "Marcus now has full CBC + CMP + CRP. 9/9 PhenoAge markers present.",
      panels: 2,
      assessment: false,
      orders: 0,
      urgency: 0.6,
      coverage: "78%",
    },
  },
  {
    id: "ORDER_PENDING",
    label: "Order Pending",
    color: "bg-violet-100 border-violet-300 text-violet-800",
    activeColor: "bg-violet-600 text-white border-violet-600",
    description: "Assessment run. Escalation rules fired. Test order recommended.",
    action: "Review & approve test order",
    actionColor: "text-violet-600",
    conditions: ["Assessment exists", "Escalation rules triggered", "No approved order"],
    scenario: {
      patient: "PhenoAge = 64.2yr (chron 52). +12yr acceleration. Glucose 7.1 → escalation rule fires.",
      panels: 2,
      assessment: true,
      orders: 0,
      urgency: 0.82,
      phenoAge: 64.2,
      delta: "+12.2yr",
      escalation: "Glucose > 6.1 → order HbA1c + fasting insulin",
    },
  },
  {
    id: "COMPOUND_CANDIDATE",
    label: "Compound Candidate",
    color: "bg-emerald-100 border-emerald-300 text-emerald-800",
    activeColor: "bg-emerald-600 text-white border-emerald-600",
    description: "Order approved. Active hallmarks identified. Compound recommendations ready.",
    action: "Review compound recommendations",
    actionColor: "text-emerald-600",
    conditions: ["Order approved", "Active hallmarks ≥ 1", "No compound protocol started"],
    scenario: {
      patient: "HbA1c = 6.4%. Active hallmarks: Nutrient Sensing, Cellular Senescence.",
      panels: 3,
      assessment: true,
      orders: 1,
      urgency: 0.71,
      hallmarks: ["Nutrient Sensing", "Cellular Senescence"],
      topCompound: "Berberine (RCT · relevance 0.87)",
    },
  },
  {
    id: "MONITORING",
    label: "Monitoring",
    color: "bg-teal-100 border-teal-300 text-teal-800",
    activeColor: "bg-teal-600 text-white border-teal-600",
    description: "Protocol active. Scheduled for follow-up panel in 90 days.",
    action: "Schedule follow-up panel",
    actionColor: "text-teal-600",
    conditions: ["Compound protocol active", "Follow-up panel not yet due"],
    scenario: {
      patient: "Marcus started berberine + metformin. Next panel due in 87 days.",
      panels: 3,
      assessment: true,
      orders: 1,
      urgency: 0.35,
      nextPanel: "87 days",
      protocol: "Berberine 500mg BID + Metformin 500mg QD",
    },
  },
];

export default function StateMachineWalkthrough() {
  const [active, setActive] = useState(0);
  const s = STATES[active];

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      {/* State pills */}
      <div className="p-4 border-b border-gray-100 bg-gray-50">
        <div className="flex items-center gap-1.5 flex-wrap">
          {STATES.map((st, i) => (
            <button
              key={st.id}
              onClick={() => setActive(i)}
              className={`px-3 py-1.5 rounded-full text-xs font-bold border transition-all ${
                active === i ? st.activeColor : st.color
              }`}
            >
              {st.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-0 divide-y md:divide-y-0 md:divide-x divide-gray-100">
        {/* Left: state info */}
        <div className="p-5">
          <div className="mb-4">
            <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">State</div>
            <div className="font-black text-gray-900 text-lg">{s.label}</div>
            <p className="text-sm text-gray-600 mt-1 leading-relaxed">{s.description}</p>
          </div>

          <div className="mb-4">
            <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">Entry Conditions</div>
            <div className="space-y-1">
              {s.conditions.map((c) => (
                <div key={c} className="flex items-center gap-2 text-xs text-gray-700">
                  <svg className="w-3.5 h-3.5 text-emerald-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                  {c}
                </div>
              ))}
            </div>
          </div>

          <div className="bg-gray-50 rounded-xl p-3 border border-gray-100">
            <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Next Action</div>
            <div className={`text-sm font-bold ${s.actionColor}`}>{s.action}</div>
          </div>
        </div>

        {/* Right: scenario */}
        <div className="p-5">
          <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-3">Live Scenario</div>

          <div className="bg-gray-50 rounded-xl p-3 border border-gray-100 mb-3">
            <p className="text-xs text-gray-700 leading-relaxed italic">"{s.scenario.patient}"</p>
          </div>

          {/* Mini stats */}
          <div className="grid grid-cols-3 gap-2 mb-3">
            <div className="bg-white rounded-lg border border-gray-200 p-2 text-center">
              <div className="text-lg font-black text-gray-900">{s.scenario.panels}</div>
              <div className="text-[10px] text-gray-500 font-medium">Panels</div>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-2 text-center">
              <div className="text-lg font-black text-gray-900">{s.scenario.orders}</div>
              <div className="text-[10px] text-gray-500 font-medium">Orders</div>
            </div>
            <div className={`rounded-lg border p-2 text-center ${
              s.scenario.urgency > 0.7 ? "bg-red-50 border-red-200" :
              s.scenario.urgency > 0.5 ? "bg-amber-50 border-amber-200" : "bg-emerald-50 border-emerald-200"
            }`}>
              <div className={`text-lg font-black ${
                s.scenario.urgency > 0.7 ? "text-red-700" :
                s.scenario.urgency > 0.5 ? "text-amber-700" : "text-emerald-700"
              }`}>{s.scenario.urgency}</div>
              <div className="text-[10px] text-gray-500 font-medium">Urgency</div>
            </div>
          </div>

          {/* Extra scenario details */}
          <div className="space-y-1.5">
            {"coverage" in s.scenario && (
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Tier 1 coverage</span>
                <span className="font-bold text-amber-600">{(s.scenario as any).coverage}</span>
              </div>
            )}
            {"missing" in s.scenario && (
              <div className="text-xs">
                <span className="text-gray-500">Missing: </span>
                {((s.scenario as any).missing as string[]).map((m: string) => (
                  <span key={m} className="inline-block bg-red-50 text-red-700 border border-red-200 rounded px-1.5 py-0.5 text-[10px] font-mono mr-1">{m}</span>
                ))}
              </div>
            )}
            {"phenoAge" in s.scenario && (
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">PhenoAge</span>
                <span className="font-bold text-red-600">{(s.scenario as any).phenoAge}yr ({(s.scenario as any).delta})</span>
              </div>
            )}
            {"escalation" in s.scenario && (
              <div className="text-xs bg-red-50 border border-red-200 rounded-lg px-2 py-1.5 text-red-700">
                Escalation: {(s.scenario as any).escalation}
              </div>
            )}
            {"hallmarks" in s.scenario && (
              <div className="flex flex-wrap gap-1">
                {((s.scenario as any).hallmarks as string[]).map((h: string) => (
                  <span key={h} className="text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-200 rounded px-1.5 py-0.5 font-medium">{h}</span>
                ))}
              </div>
            )}
            {"topCompound" in s.scenario && (
              <div className="text-xs bg-emerald-50 border border-emerald-200 rounded-lg px-2 py-1.5 text-emerald-700 font-medium">
                Top: {(s.scenario as any).topCompound}
              </div>
            )}
            {"nextPanel" in s.scenario && (
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Next panel</span>
                <span className="font-bold text-teal-600">in {(s.scenario as any).nextPanel}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="px-5 pb-4 pt-2 border-t border-gray-100">
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-gray-400 font-medium">Patient journey</span>
          <div className="flex-1 flex gap-1">
            {STATES.map((_, i) => (
              <div
                key={i}
                className={`h-1.5 flex-1 rounded-full transition-all ${i <= active ? "bg-gray-800" : "bg-gray-200"}`}
              />
            ))}
          </div>
          <span className="text-[10px] text-gray-400 font-medium">{active + 1}/{STATES.length}</span>
        </div>
      </div>
    </div>
  );
}
