"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api";
import { saveAuth } from "@/lib/auth";

const DEMO_EMAIL = "demo@longivity.ai";
const DEMO_PASSWORD = "DemoPass2026!";

// Disease-domain patient cards — matches seed_demo.py exactly
const DEMO_PATIENTS = [
  {
    mrn: "DEMO-001",
    name: "Robert Chen",
    age: 58,
    sex: "M",
    condition: "Pre-diabetes → Type 2 Diabetes",
    headline: "Glucose 118 · HbA1c 6.2% · CRP 4.8",
    phenoage: "+14.8yr",
    accelColor: "text-red-600",
    bgColor: "bg-red-50",
    borderColor: "border-red-200",
    badgeColor: "bg-red-100 text-red-700",
    icon: "🩸",
    state: "Ready for Protocol",
    stateColor: "bg-emerald-100 text-emerald-700",
  },
  {
    mrn: "DEMO-002",
    name: "Elena Vasquez",
    age: 52,
    sex: "F",
    condition: "Alzheimer's Risk — Silent",
    headline: "APOE e4/e4 · MTHFR compound het · Perfect labs",
    phenoage: "−18.9yr",
    accelColor: "text-emerald-600",
    bgColor: "bg-purple-50",
    borderColor: "border-purple-200",
    badgeColor: "bg-purple-100 text-purple-700",
    icon: "🧬",
    state: "Ready for Protocol",
    stateColor: "bg-emerald-100 text-emerald-700",
  },
  {
    mrn: "DEMO-003",
    name: "Marcus Webb",
    age: 47,
    sex: "M",
    condition: "Cardiovascular — Early Subclinical",
    headline: "CRP 3.8 · LDL 168 · ApoB 115 · Annual physical missed it",
    phenoage: "+4.9yr",
    accelColor: "text-orange-600",
    bgColor: "bg-orange-50",
    borderColor: "border-orange-200",
    badgeColor: "bg-orange-100 text-orange-700",
    icon: "❤️",
    state: "Ready to Assess",
    stateColor: "bg-blue-100 text-blue-700",
  },
  {
    mrn: "DEMO-004",
    name: "Diana Park",
    age: 54,
    sex: "F",
    condition: "Cancer Risk Pattern",
    headline: "BRCA2 het · Ferritin 320 · IL-6 7.8 · CEA 4.2",
    phenoage: "+12.8yr",
    accelColor: "text-red-600",
    bgColor: "bg-rose-50",
    borderColor: "border-rose-200",
    badgeColor: "bg-rose-100 text-rose-700",
    icon: "🔬",
    state: "Order Recommended",
    stateColor: "bg-amber-100 text-amber-700",
  },
  {
    mrn: "DEMO-005",
    name: "Thomas Rivera",
    age: 72,
    sex: "M",
    condition: "Sarcopenia + Multi-System Aging",
    headline: "Albumin 3.4 · Testosterone 245 · Grip 22kg",
    phenoage: "+20.4yr",
    accelColor: "text-red-700",
    bgColor: "bg-gray-50",
    borderColor: "border-gray-300",
    badgeColor: "bg-gray-200 text-gray-700",
    icon: "💪",
    state: "Order Recommended",
    stateColor: "bg-amber-100 text-amber-700",
  },
  {
    mrn: "DEMO-006",
    name: "James Okafor",
    age: 68,
    sex: "M",
    condition: "Exceptional Aging — Centenarian Pattern",
    headline: "FOXO3 G/G · CETP A/A · KLOTHO T/T · All optimal",
    phenoage: "−19.8yr",
    accelColor: "text-emerald-600",
    bgColor: "bg-emerald-50",
    borderColor: "border-emerald-200",
    badgeColor: "bg-emerald-100 text-emerald-700",
    icon: "⭐",
    state: "Active Monitoring",
    stateColor: "bg-emerald-100 text-emerald-700",
  },
];

export default function DemoLoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [seededCount, setSeededCount] = useState<number | null>(null);

  // Fetch demo status on mount
  useEffect(() => {
    const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${BASE}/api/v1/demo/status`)
      .then((r) => r.json())
      .then((d) => {
        if (d.seeded) setSeededCount(d.patient_count);
      })
      .catch(() => {});
  }, []);

  async function handleEnterDemo() {
    setLoading(true);
    setError("");
    try {
      const res = await authApi.login(DEMO_EMAIL, DEMO_PASSWORD);
      saveAuth(res.access_token, {
        id: res.user_id,
        email: res.email,
        full_name: res.full_name,
        clinic_id: res.clinic_id,
        is_demo: true,
      });
      router.push("/dashboard");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Login failed";
      if (msg.includes("401") || msg.includes("Unauthorized")) {
        setError(
          "Demo environment not yet seeded. Run: python scripts/seed_demo.py on the backend."
        );
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Demo banner */}
      <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 text-center">
        <span className="text-sm text-amber-800 font-medium">
          Research Use Only — Synthetic data derived from published reference distributions (NHANES, LonGenity, MESA, InCHIANTI, BLSA)
        </span>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm font-bold mb-6">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Live System · Real Engine · {seededCount !== null ? `${seededCount} Patients Seeded` : "Loading..."}
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-gray-900 leading-tight tracking-tight mb-4">
            Six Patients.<br />
            Six Disease Domains.<br />
            One Platform.
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto leading-relaxed">
            Each patient is a real clinical archetype grounded in published datasets.
            The engine runs the actual PhenoAge algorithm — not a mockup.
          </p>
        </div>

        {/* Patient cards grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-12">
          {DEMO_PATIENTS.map((p) => (
            <div
              key={p.mrn}
              className={`rounded-2xl border ${p.borderColor} ${p.bgColor} p-5 flex flex-col gap-3`}
            >
              {/* Top row */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{p.icon}</span>
                  <div>
                    <div className="font-bold text-gray-900 text-sm">{p.name}</div>
                    <div className="text-xs text-gray-500">{p.age}{p.sex} · {p.mrn}</div>
                  </div>
                </div>
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${p.stateColor}`}>
                  {p.state}
                </span>
              </div>

              {/* Condition */}
              <div>
                <div className="text-sm font-semibold text-gray-800">{p.condition}</div>
                <div className="text-xs text-gray-500 mt-0.5 leading-relaxed">{p.headline}</div>
              </div>

              {/* PhenoAge delta */}
              <div className="flex items-center justify-between pt-2 border-t border-white/60">
                <span className="text-xs text-gray-500 font-medium">Biological Age</span>
                <span className={`text-sm font-black ${p.accelColor}`}>
                  {p.phenoage} vs chronological
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* CTA */}
        <div className="flex flex-col items-center gap-4">
          <button
            onClick={handleEnterDemo}
            disabled={loading}
            className="bg-gray-900 hover:bg-gray-800 disabled:opacity-60 text-white font-bold text-lg px-10 py-4 rounded-2xl transition-all shadow-lg hover:shadow-xl"
          >
            {loading ? "Signing in..." : "Enter Live Demo →"}
          </button>

          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2 max-w-md text-center">
              {error}
            </div>
          )}

          <div className="text-xs text-gray-400 text-center max-w-sm">
            Logs in as <code className="bg-gray-100 px-1 rounded">demo@longivity.ai</code> · Read-only demo account ·
            Data resets periodically
          </div>
        </div>

        {/* Data provenance */}
        <div className="mt-16 border-t border-gray-100 pt-8">
          <div className="text-xs text-gray-400 text-center font-medium uppercase tracking-wider mb-4">
            Data Provenance
          </div>
          <div className="flex flex-wrap justify-center gap-3">
            {[
              "NHANES III/IV (Levine 2018)",
              "LonGenity centenarian cohort",
              "MESA cardiovascular study",
              "InCHIANTI aging cohort",
              "BLSA longitudinal aging",
              "DNA repair gene panel",
            ].map((src) => (
              <span
                key={src}
                className="text-xs bg-gray-50 border border-gray-200 text-gray-600 px-3 py-1 rounded-full"
              >
                {src}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
