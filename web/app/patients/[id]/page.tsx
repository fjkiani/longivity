"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { patientsApi, panelsApi, assessmentApi, Patient, Panel, Assessment } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import Sidebar from "@/components/Sidebar";
import BiomarkerTable from "@/components/BiomarkerTable";
import BiomarkerTrendChart from "@/components/BiomarkerTrendChart";
import PhenoAgeGauge from "@/components/PhenoAgeGauge";
import CompoundRecsTable from "@/components/CompoundRecsTable";
import { formatDate, formatAge, tierColor } from "@/lib/utils";

type Tab = "overview" | "biomarkers" | "assessment" | "trends" | "nof1";

export default function PatientPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [patient, setPatient] = useState<Patient | null>(null);
  const [panels, setPanels] = useState<Panel[]>([]);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [longitudinal, setLongitudinal] = useState<any>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [loading, setLoading] = useState(true);
  const [assessLoading, setAssessLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated()) { router.replace("/login"); return; }
    Promise.all([
      patientsApi.get(id),
      panelsApi.list(id),
    ])
      .then(([p, pnls]) => {
        setPatient(p);
        setPanels(pnls);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id, router]);

  async function loadAssessment() {
    if (assessment) return;
    setAssessLoading(true);
    try {
      const a = await assessmentApi.getAssessment(id);
      setAssessment(a);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setAssessLoading(false);
    }
  }

  async function loadLongitudinal() {
    if (longitudinal) return;
    try {
      const l = await assessmentApi.getLongitudinal(id);
      setLongitudinal(l);
    } catch (e: any) {
      setError(e.message);
    }
  }

  function handleTabChange(t: Tab) {
    setTab(t);
    if (t === "assessment") loadAssessment();
    if (t === "trends") loadLongitudinal();
  }

  const latestPanel = panels[0] || null;
  const phenoResult = assessment?.phenoage_result;
  const age = patient?.age || 45;

  // Build trend data for key markers
  const trendMarkers = ["albumin", "creatinine", "glucose", "crp", "ldl", "hdl"];
  const trendData: Record<string, { date: string; value: number }[]> = {};
  [...panels].reverse().forEach((panel) => {
    panel.values.forEach((v) => {
      if (!trendData[v.marker_key]) trendData[v.marker_key] = [];
      trendData[v.marker_key].push({ date: panel.drawn_at, value: v.value });
    });
  });

  if (loading) {
    return (
      <div className="flex h-screen bg-gray-50">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-sm text-gray-400">Loading patient...</div>
        </main>
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="flex h-screen bg-gray-50">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-sm text-red-500">{error || "Patient not found"}</div>
        </main>
      </div>
    );
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: "overview", label: "Overview" },
    { key: "biomarkers", label: "Biomarkers" },
    { key: "assessment", label: "Assessment" },
    { key: "trends", label: "Trends" },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <div className="max-w-5xl mx-auto px-6 py-8">
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 mb-6 text-sm">
            <Link href="/dashboard" className="text-gray-400 hover:text-gray-600">Dashboard</Link>
            <span className="text-gray-300">/</span>
            <span className="text-gray-700">{patient.first_name} {patient.last_name}</span>
          </div>

          {/* Patient header */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                  <span className="text-green-700 font-semibold text-lg">
                    {patient.first_name[0]}{patient.last_name[0]}
                  </span>
                </div>
                <div>
                  <h1 className="text-xl font-semibold text-gray-900">
                    {patient.first_name} {patient.last_name}
                  </h1>
                  <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
                    {patient.age && <span>{patient.age} yrs</span>}
                    {patient.sex && <span className="capitalize">{patient.sex}</span>}
                    {patient.mrn && <span className="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded">MRN: {patient.mrn}</span>}
                    {patient.email && <span>{patient.email}</span>}
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                <Link
                  href={`/patients/${id}/upload`}
                  className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
                >
                  Upload Labs
                </Link>
              </div>
            </div>

            {/* Quick stats */}
            <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-100">
              <div>
                <div className="text-xs text-gray-400 mb-0.5">Lab Panels</div>
                <div className="text-lg font-semibold text-gray-900">{panels.length}</div>
              </div>
              <div>
                <div className="text-xs text-gray-400 mb-0.5">Latest Draw</div>
                <div className="text-sm font-medium text-gray-700">{formatDate(latestPanel?.drawn_at)}</div>
              </div>
              <div>
                <div className="text-xs text-gray-400 mb-0.5">Lab Source</div>
                <div className="text-sm font-medium text-gray-700 capitalize">
                  {latestPanel?.lab_name || latestPanel?.source || "—"}
                </div>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 mb-6 bg-white rounded-xl border border-gray-200 p-1">
            {tabs.map((t) => (
              <button
                key={t.key}
                onClick={() => handleTabChange(t.key)}
                className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${
                  tab === t.key
                    ? "bg-green-600 text-white"
                    : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                }`}
              >
                {t.label}
              </button>
            ))}
            <Link
              href={`/patients/${id}/test-orders`}
              className="flex-1 py-2 text-sm font-medium rounded-lg transition-all text-center text-gray-500 hover:text-gray-700 hover:bg-gray-50 border border-dashed border-gray-300"
            >
              Test Orders
            </Link>
          </div>

          {/* Tab content */}
          {tab === "overview" && (
            <div className="space-y-4">
              {panels.length === 0 ? (
                <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
                  <p className="text-gray-400 text-sm mb-3">No lab panels yet.</p>
                  <Link
                    href={`/patients/${id}/upload`}
                    className="text-sm text-green-600 hover:text-green-700 font-medium"
                  >
                    Upload first lab report →
                  </Link>
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    {/* Latest panel summary */}
                    <div className="bg-white rounded-xl border border-gray-200 p-4">
                      <h3 className="text-sm font-semibold text-gray-700 mb-3">Latest Panel</h3>
                      <div className="text-xs text-gray-400 mb-2">{formatDate(latestPanel?.drawn_at)}</div>
                      <div className="space-y-1.5">
                        {latestPanel?.values.slice(0, 6).map((v) => (
                          <div key={v.marker_key} className="flex justify-between text-sm">
                            <span className="text-gray-600">{v.marker_display || v.marker_key}</span>
                            <span className={`font-medium ${
                              v.flag === "H" || v.flag === "HH" ? "text-red-600" :
                              v.flag === "L" || v.flag === "LL" ? "text-yellow-600" :
                              "text-gray-900"
                            }`}>
                              {v.value} {v.unit}
                            </span>
                          </div>
                        ))}
                        {(latestPanel?.values.length || 0) > 6 && (
                          <button
                            onClick={() => handleTabChange("biomarkers")}
                            className="text-xs text-green-600 hover:text-green-700 mt-1"
                          >
                            +{(latestPanel?.values.length || 0) - 6} more →
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Panel history */}
                    <div className="bg-white rounded-xl border border-gray-200 p-4">
                      <h3 className="text-sm font-semibold text-gray-700 mb-3">Panel History</h3>
                      <div className="space-y-2">
                        {panels.map((panel) => (
                          <div key={panel.id} className="flex items-center justify-between text-sm">
                            <div>
                              <div className="font-medium text-gray-900">{formatDate(panel.drawn_at)}</div>
                              <div className="text-xs text-gray-400 capitalize">
                                {panel.lab_name || panel.source} · {panel.values.length} markers
                              </div>
                            </div>
                            <button
                              onClick={() => handleTabChange("biomarkers")}
                              className="text-xs text-green-600 hover:text-green-700"
                            >
                              View
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-xl border border-gray-200 p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-sm font-semibold text-gray-700">Quick Assessment</h3>
                      <button
                        onClick={() => handleTabChange("assessment")}
                        className="text-xs text-green-600 hover:text-green-700 font-medium"
                      >
                        Full Assessment →
                      </button>
                    </div>
                    <p className="text-sm text-gray-500">
                      Click "Assessment" tab to run PhenoAge analysis, hallmark scoring, and compound recommendations.
                    </p>
                  </div>
                </>
              )}
            </div>
          )}

          {tab === "biomarkers" && (
            <div className="bg-white rounded-xl border border-gray-200">
              {panels.length === 0 ? (
                <div className="p-8 text-center text-sm text-gray-400">No panels yet.</div>
              ) : (
                <>
                  {/* Panel selector */}
                  <div className="px-4 py-3 border-b border-gray-100 flex gap-2 overflow-x-auto">
                    {panels.map((panel, i) => (
                      <div key={panel.id} className={`flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium border ${
                        i === 0 ? "bg-green-50 text-green-700 border-green-200" : "bg-gray-50 text-gray-500 border-gray-200"
                      }`}>
                        {formatDate(panel.drawn_at)}
                        <span className="ml-1 text-gray-400">({panel.values.length})</span>
                      </div>
                    ))}
                  </div>
                  <BiomarkerTable values={latestPanel?.values || []} />
                </>
              )}
            </div>
          )}

          {tab === "assessment" && (
            <div className="space-y-4">
              {!latestPanel ? (
                <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-sm text-gray-400">
                  Upload a lab panel first.
                </div>
              ) : assessLoading ? (
                <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-sm text-gray-400">
                  Running assessment...
                </div>
              ) : !assessment ? (
                <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
                  <button
                    onClick={loadAssessment}
                    className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-5 py-2 rounded-lg"
                  >
                    Run Assessment
                  </button>
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <PhenoAgeGauge
                      chronologicalAge={age}
                      phenoAge={phenoResult?.phenoage_estimate ?? null}
                      tier={phenoResult?.accel_tier || ""}
                    />
                    <div className="bg-white rounded-xl border border-gray-200 p-4">
                      <h3 className="text-sm font-semibold text-gray-700 mb-3">PhenoAge Details</h3>
                      {phenoResult ? (
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-500">Biological Age</span>
                            <span className="font-semibold text-gray-900">
                              {phenoResult.phenoage_estimate?.toFixed(1) ?? "—"} yrs
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Acceleration</span>
                            <span className={`font-semibold ${
                              (phenoResult.phenoage_acceleration || 0) > 0 ? "text-red-600" : "text-green-600"
                            }`}>
                              {phenoResult.phenoage_acceleration != null
                                ? `${phenoResult.phenoage_acceleration > 0 ? "+" : ""}${phenoResult.phenoage_acceleration.toFixed(1)} yrs`
                                : "—"}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Tier</span>
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${tierColor(phenoResult.accel_tier)}`}>
                              {phenoResult.accel_tier_label}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Components</span>
                            <span className="text-gray-700">{phenoResult.components_used}/9</span>
                          </div>
                          {phenoResult.missing_components?.length > 0 && (
                            <div className="text-xs text-gray-400 mt-1">
                              Missing: {phenoResult.missing_components.join(", ")}
                            </div>
                          )}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-400">Insufficient biomarker data for PhenoAge.</p>
                      )}
                    </div>
                  </div>

                  {/* Hallmarks */}
                  {assessment.hallmark_result && (
                    <div className="bg-white rounded-xl border border-gray-200 p-4">
                      <h3 className="text-sm font-semibold text-gray-700 mb-3">Hallmarks of Aging</h3>
                      {assessment.hallmark_result.narrative && (
                        <p className="text-sm text-gray-600 mb-3 leading-relaxed">
                          {assessment.hallmark_result.narrative}
                        </p>
                      )}
                      <div className="flex flex-wrap gap-2">
                        {assessment.hallmark_result.hallmarks_activated?.map((h) => (
                          <span key={h} className="px-2.5 py-1 bg-orange-50 text-orange-700 text-xs font-medium rounded-full border border-orange-100">
                            {h.replace(/_/g, " ")}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Compound recs */}
                  <div className="bg-white rounded-xl border border-gray-200 p-4">
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">
                      Compound Recommendations
                      <span className="ml-2 text-xs font-normal text-gray-400">(RUO — not prescriptive)</span>
                    </h3>
                    <CompoundRecsTable recs={assessment.compound_recommendations || []} />
                  </div>
                </>
              )}
            </div>
          )}

          {tab === "trends" && (
            <div className="space-y-4">
              {panels.length < 2 ? (
                <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-sm text-gray-400">
                  At least 2 panels needed for trend analysis. Upload more lab reports.
                </div>
              ) : (
                <>
                  {/* PhenoAge trajectory */}
                  {longitudinal?.phenoage_trajectory && (
                    <div className="bg-white rounded-xl border border-gray-200 p-4">
                      <h3 className="text-sm font-semibold text-gray-700 mb-3">PhenoAge Trajectory</h3>
                      <BiomarkerTrendChart
                        data={longitudinal.phenoage_trajectory
                          .filter((p: any) => p.phenoage_estimate != null)
                          .map((p: any) => ({ date: p.drawn_at, value: p.phenoage_estimate }))}
                        markerKey="phenoage"
                        markerDisplay="Biological Age (PhenoAge)"
                        unit="yrs"
                        refLow={age - 2}
                        refHigh={age + 2}
                        color="#8b5cf6"
                      />
                    </div>
                  )}

                  {/* Per-marker trends */}
                  <div className="grid grid-cols-2 gap-4">
                    {trendMarkers
                      .filter((mk) => (trendData[mk]?.length || 0) >= 2)
                      .map((mk) => {
                        const vals = trendData[mk];
                        const refVals = latestPanel?.values.find((v) => v.marker_key === mk);
                        return (
                          <BiomarkerTrendChart
                            key={mk}
                            data={vals}
                            markerKey={mk}
                            markerDisplay={refVals?.marker_display || mk}
                            unit={refVals?.unit || undefined}
                            refLow={refVals?.ref_low}
                            refHigh={refVals?.ref_high}
                          />
                        );
                      })}
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
