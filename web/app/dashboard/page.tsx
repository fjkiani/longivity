"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { patientsApi, Patient, intelligenceApi, IntelligenceResponse } from "@/lib/api";
import { isAuthenticated, getUser } from "@/lib/auth";
import Sidebar from "@/components/Sidebar";
import DemoBanner from "@/components/DemoBanner";
import { formatDate, formatAge } from "@/lib/utils";

// Human-readable state labels — no internal jargon shown to demo viewers
const STATE_LABELS: Record<string, { label: string; color: string }> = {
  NEW:                { label: "New Patient",        color: "bg-gray-100 text-gray-600" },
  DATA_INCOMPLETE:    { label: "Needs Lab Work",     color: "bg-yellow-100 text-yellow-700" },
  ASSESSMENT_PENDING: { label: "Ready to Assess",    color: "bg-blue-100 text-blue-700" },
  ORDER_PENDING:      { label: "Order Recommended",  color: "bg-amber-100 text-amber-700" },
  COMPOUND_CANDIDATE: { label: "Ready for Protocol", color: "bg-emerald-100 text-emerald-700" },
  MONITORING:         { label: "Active Monitoring",  color: "bg-teal-100 text-teal-700" },
};

function stateLabel(state: string | undefined) {
  if (!state) return { label: "—", color: "bg-gray-50 text-gray-400" };
  return STATE_LABELS[state] || { label: state, color: "bg-gray-100 text-gray-600" };
}

function accelColor(accel: number | undefined | null): string {
  if (accel == null) return "text-gray-400";
  if (accel > 10) return "text-red-600 font-bold";
  if (accel > 5) return "text-orange-600 font-semibold";
  if (accel > 0) return "text-yellow-600";
  if (accel < -5) return "text-emerald-600 font-semibold";
  return "text-emerald-500";
}

function accelLabel(accel: number | undefined | null): string {
  if (accel == null) return "—";
  const sign = accel >= 0 ? "+" : "";
  return `${sign}${accel.toFixed(1)}yr`;
}

// Extract condition headline from patient notes (first sentence)
function conditionHeadline(notes: string | null | undefined): string {
  if (!notes) return "";
  return notes.split(".")[0].trim().slice(0, 60);
}

export default function DashboardPage() {
  const router = useRouter();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [intelligence, setIntelligence] = useState<Record<string, IntelligenceResponse>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    patientsApi
      .list()
      .then(async (pts) => {
        setPatients(pts);
        // Load intelligence for all patients (for PhenoAge + state)
        const intel: Record<string, IntelligenceResponse> = {};
        await Promise.allSettled(
          pts.map(async (p) => {
            try {
              const i = await intelligenceApi.getPatientIntelligence(p.id);
              intel[p.id] = i;
            } catch {
              // Non-fatal — patient may not have intelligence yet
            }
          })
        );
        setIntelligence(intel);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [router]);

  const filtered = patients.filter((p) => {
    const q = search.toLowerCase();
    return (
      p.first_name.toLowerCase().includes(q) ||
      p.last_name.toLowerCase().includes(q) ||
      (p.mrn || "").toLowerCase().includes(q) ||
      (p.email || "").toLowerCase().includes(q) ||
      (p.notes || "").toLowerCase().includes(q)
    );
  });

  const user = getUser();
  const isDemo = user?.is_demo || user?.email === "demo@longivity.ai";

  // Stats
  const withLabs = patients.filter((p) => p.panel_count > 0).length;
  const accelerated = Object.values(intelligence).filter(
    (i) => (i.phenoage_result?.acceleration ?? 0) > 5
  ).length;
  const recentLabs = patients.filter((p) => {
    if (!p.latest_panel_date) return false;
    return (Date.now() - new Date(p.latest_panel_date).getTime()) / 86400000 < 30;
  }).length;

  return (
    <div className="flex h-screen bg-gray-50 flex-col">
      <DemoBanner />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <div className="max-w-6xl mx-auto px-6 py-8">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
              <div>
                <h1 className="text-2xl font-semibold text-gray-900">
                  {isDemo ? "Demo Clinic" : `Good morning${user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}`}
                </h1>
                <p className="text-sm text-gray-500 mt-0.5">
                  {patients.length} patient{patients.length !== 1 ? "s" : ""} in your clinic
                  {isDemo && " · Research Use Only"}
                </p>
              </div>
              {!isDemo && (
                <Link
                  href="/patients/new"
                  className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
                >
                  + Add Patient
                </Link>
              )}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-4 gap-4 mb-8">
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="text-2xl font-bold text-gray-900">{patients.length}</div>
                <div className="text-sm text-gray-500 mt-0.5">Total Patients</div>
              </div>
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="text-2xl font-bold text-gray-900">{withLabs}</div>
                <div className="text-sm text-gray-500 mt-0.5">With Lab Data</div>
              </div>
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="text-2xl font-bold text-red-600">{accelerated}</div>
                <div className="text-sm text-gray-500 mt-0.5">Accelerated Aging (&gt;5yr)</div>
              </div>
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="text-2xl font-bold text-gray-900">{recentLabs}</div>
                <div className="text-sm text-gray-500 mt-0.5">Recent Labs (30d)</div>
              </div>
            </div>

            {/* Search + Table */}
            <div className="bg-white rounded-xl border border-gray-200">
              <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-3">
                <input
                  type="text"
                  placeholder="Search patients by name, MRN, or condition..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="flex-1 text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>

              {loading ? (
                <div className="py-12 text-center text-sm text-gray-400">Loading patients...</div>
              ) : error ? (
                <div className="py-12 text-center text-sm text-red-500">{error}</div>
              ) : filtered.length === 0 ? (
                <div className="py-12 text-center">
                  <p className="text-sm text-gray-400 mb-3">
                    {search ? "No patients match your search." : "No patients yet."}
                  </p>
                  {!search && !isDemo && (
                    <Link
                      href="/patients/new"
                      className="text-sm text-green-600 hover:text-green-700 font-medium"
                    >
                      Add your first patient →
                    </Link>
                  )}
                </div>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100">
                      <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">Patient</th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">Age / Sex</th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">Condition</th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">Biological Age</th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">Status</th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">Last Lab</th>
                      <th className="py-3 px-4"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((p) => {
                      const intel = intelligence[p.id];
                      const accel = intel?.phenoage_result?.acceleration;
                      const state = intel?.state;
                      const sl = stateLabel(state);
                      const condition = conditionHeadline(p.notes);

                      return (
                        <tr key={p.id} className="border-b border-gray-50 hover:bg-gray-50/50">
                          <td className="py-3 px-4">
                            <div className="font-medium text-gray-900">
                              {p.first_name} {p.last_name}
                            </div>
                            <div className="text-xs text-gray-400 font-mono">{p.mrn || ""}</div>
                          </td>
                          <td className="py-3 px-4 text-gray-600 whitespace-nowrap">
                            {formatAge(p.date_of_birth)}
                            {p.sex && <span className="text-gray-400"> · {p.sex}</span>}
                          </td>
                          <td className="py-3 px-4 max-w-[200px]">
                            {condition ? (
                              <span className="text-xs text-gray-600 leading-relaxed">{condition}</span>
                            ) : (
                              <span className="text-xs text-gray-300">—</span>
                            )}
                          </td>
                          <td className="py-3 px-4 whitespace-nowrap">
                            {accel != null ? (
                              <span className={`text-sm ${accelColor(accel)}`}>
                                {accelLabel(accel)}
                              </span>
                            ) : (
                              <span className="text-xs text-gray-300">
                                {p.panel_count > 0 ? "Computing..." : "No labs"}
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-4">
                            <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${sl.color}`}>
                              {sl.label}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-gray-500 text-xs whitespace-nowrap">
                            {formatDate(p.latest_panel_date)}
                          </td>
                          <td className="py-3 px-4 text-right">
                            <Link
                              href={`/patients/${p.id}`}
                              className="text-xs text-green-600 hover:text-green-700 font-medium"
                            >
                              View →
                            </Link>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
