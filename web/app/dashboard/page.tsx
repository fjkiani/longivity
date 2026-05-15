"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { patientsApi, Patient } from "@/lib/api";
import { isAuthenticated, getUser } from "@/lib/auth";
import Sidebar from "@/components/Sidebar";
import { formatDate, formatAge, tierColor } from "@/lib/utils";

export default function DashboardPage() {
  const router = useRouter();
  const [patients, setPatients] = useState<Patient[]>([]);
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
      .then(setPatients)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [router]);

  const filtered = patients.filter((p) => {
    const q = search.toLowerCase();
    return (
      p.first_name.toLowerCase().includes(q) ||
      p.last_name.toLowerCase().includes(q) ||
      (p.mrn || "").toLowerCase().includes(q) ||
      (p.email || "").toLowerCase().includes(q)
    );
  });

  const user = getUser();

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <div className="max-w-6xl mx-auto px-6 py-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">
                Good morning{user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}
              </h1>
              <p className="text-sm text-gray-500 mt-0.5">
                {patients.length} patient{patients.length !== 1 ? "s" : ""} in your clinic
              </p>
            </div>
            <Link
              href="/patients/new"
              className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              + Add Patient
            </Link>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mb-8">
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="text-2xl font-bold text-gray-900">{patients.length}</div>
              <div className="text-sm text-gray-500 mt-0.5">Total Patients</div>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="text-2xl font-bold text-gray-900">
                {patients.filter((p) => p.panel_count > 0).length}
              </div>
              <div className="text-sm text-gray-500 mt-0.5">With Lab Data</div>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="text-2xl font-bold text-gray-900">
                {patients.filter((p) => {
                  if (!p.latest_panel_date) return false;
                  const days = (Date.now() - new Date(p.latest_panel_date).getTime()) / 86400000;
                  return days < 30;
                }).length}
              </div>
              <div className="text-sm text-gray-500 mt-0.5">Recent Labs (30d)</div>
            </div>
          </div>

          {/* Search + Table */}
          <div className="bg-white rounded-xl border border-gray-200">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-3">
              <input
                type="text"
                placeholder="Search patients..."
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
                {!search && (
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
                    <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">MRN</th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">Panels</th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">Last Lab</th>
                    <th className="py-3 px-4"></th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((p) => (
                    <tr key={p.id} className="border-b border-gray-50 hover:bg-gray-50/50">
                      <td className="py-3 px-4">
                        <div className="font-medium text-gray-900">
                          {p.first_name} {p.last_name}
                        </div>
                        {p.email && <div className="text-xs text-gray-400">{p.email}</div>}
                      </td>
                      <td className="py-3 px-4 text-gray-600">
                        {formatAge(p.date_of_birth)}
                        {p.sex && <span className="text-gray-400"> · {p.sex}</span>}
                      </td>
                      <td className="py-3 px-4 text-gray-500 font-mono text-xs">
                        {p.mrn || "—"}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                          p.panel_count > 0 ? "bg-green-50 text-green-700" : "bg-gray-50 text-gray-400"
                        }`}>
                          {p.panel_count} panel{p.panel_count !== 1 ? "s" : ""}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-gray-500 text-xs">
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
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
