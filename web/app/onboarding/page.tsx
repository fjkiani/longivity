"use client";
/**
 * /onboarding — 4-step wizard for new clinic setup.
 * Called after POST /api/v1/auth/register + POST /api/v1/onboarding/start.
 * URL: /onboarding?id={onboarding_id}
 */
import { useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { onboardingApi, OnboardingStatus } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";

// ── Step definitions ──────────────────────────────────────────────────────────
const STEPS = [
  { id: "welcome",   label: "Welcome",           icon: "👋" },
  { id: "seeding",   label: "Setting up",        icon: "⚙️" },
  { id: "patients",  label: "Your first patient", icon: "🧬" },
  { id: "ready",     label: "You're ready",       icon: "✅" },
];

const DEMO_PATIENTS = [
  { name: "Marcus T.", condition: "T2D", phenoage: "73.6yr", accel: "+15.6yr", color: "text-red-600" },
  { name: "Robert C.", condition: "CVD", phenoage: "81.5yr", accel: "+18.5yr", color: "text-orange-600" },
  { name: "James L.",  condition: "Centenarian", phenoage: "48.2yr", accel: "−19.8yr", color: "text-emerald-600" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const onboardingId = searchParams.get("id");

  const [step, setStep] = useState(0);
  const [status, setStatus] = useState<OnboardingStatus | null>(null);
  const [error, setError] = useState("");
  const [completing, setCompleting] = useState(false);

  // Guard: must be authenticated
  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
    }
  }, [router]);

  // Poll seeding status when on step 1 (seeding)
  const pollStatus = useCallback(async () => {
    if (!onboardingId) return;
    try {
      const s = await onboardingApi.getStatus(onboardingId);
      setStatus(s);
      if (s.status === "complete") {
        setStep(2); // advance to "Your first patient"
      } else if (s.status === "failed") {
        setError(s.next_step);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Status check failed");
    }
  }, [onboardingId]);

  useEffect(() => {
    if (step !== 1) return;
    pollStatus();
    const interval = setInterval(pollStatus, 3000);
    return () => clearInterval(interval);
  }, [step, pollStatus]);

  async function handleStart(seedDemo: boolean) {
    try {
      if (!onboardingId) {
        // Already have an onboarding_id from register flow — just advance
        setStep(1);
        return;
      }
      setStep(1);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Start failed");
    }
  }

  async function handleComplete() {
    setCompleting(true);
    try {
      await onboardingApi.complete();
      setStep(3);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Complete failed");
    } finally {
      setCompleting(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-2xl">

        {/* Progress bar */}
        <div className="flex items-center justify-between mb-10">
          {STEPS.map((s, i) => (
            <div key={s.id} className="flex items-center">
              <div className={`flex items-center justify-center w-9 h-9 rounded-full text-sm font-bold border-2 transition-all ${
                i < step ? "bg-emerald-500 border-emerald-500 text-white" :
                i === step ? "bg-white border-emerald-500 text-emerald-600" :
                "bg-white border-gray-200 text-gray-400"
              }`}>
                {i < step ? "✓" : s.icon}
              </div>
              <span className={`ml-2 text-sm font-medium hidden sm:block ${
                i === step ? "text-gray-900" : "text-gray-400"
              }`}>{s.label}</span>
              {i < STEPS.length - 1 && (
                <div className={`mx-3 h-0.5 w-8 sm:w-16 transition-all ${
                  i < step ? "bg-emerald-500" : "bg-gray-200"
                }`} />
              )}
            </div>
          ))}
        </div>

        {/* Step content */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8">

          {/* Step 0: Welcome */}
          {step === 0 && (
            <div className="text-center">
              <div className="text-5xl mb-4">👋</div>
              <h1 className="text-2xl font-black text-gray-900 mb-3">Welcome to Longivity</h1>
              <p className="text-gray-600 mb-8 leading-relaxed">
                We'll seed your clinic with 3 demo patients — a T2D archetype, a CVD archetype,
                and a centenarian — so you can explore the full platform immediately.
                Takes about 30 seconds.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={() => handleStart(true)}
                  className="px-6 py-3 bg-emerald-600 text-white font-bold rounded-xl hover:bg-emerald-700 transition-colors"
                >
                  Set up with demo patients
                </button>
                <button
                  onClick={() => router.push("/dashboard")}
                  className="px-6 py-3 bg-white text-gray-600 font-medium rounded-xl border border-gray-200 hover:border-gray-400 transition-colors"
                >
                  Skip — go to dashboard
                </button>
              </div>
            </div>
          )}

          {/* Step 1: Seeding */}
          {step === 1 && (
            <div className="text-center">
              <div className="text-5xl mb-4">⚙️</div>
              <h2 className="text-xl font-black text-gray-900 mb-3">Setting up your clinic</h2>
              <p className="text-gray-500 mb-8">Creating demo patients and biomarker panels…</p>

              {/* Progress */}
              <div className="space-y-3 mb-8">
                {DEMO_PATIENTS.map((p, i) => {
                  const created = status ? status.patients_created > i : false;
                  const active = status ? status.patients_created === i : i === 0;
                  return (
                    <div key={p.name} className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${
                      created ? "border-emerald-200 bg-emerald-50" :
                      active ? "border-blue-200 bg-blue-50" :
                      "border-gray-100 bg-gray-50"
                    }`}>
                      <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                        created ? "bg-emerald-500 text-white" :
                        active ? "bg-blue-500 text-white animate-pulse" :
                        "bg-gray-200 text-gray-400"
                      }`}>
                        {created ? "✓" : active ? "…" : "○"}
                      </div>
                      <div className="flex-1 text-left">
                        <span className="text-sm font-semibold text-gray-800">{p.name}</span>
                        <span className="text-xs text-gray-500 ml-2">{p.condition}</span>
                      </div>
                      <span className={`text-xs font-mono font-bold ${p.color}`}>{p.accel}</span>
                    </div>
                  );
                })}
              </div>

              {error && (
                <div className="text-sm text-red-600 bg-red-50 rounded-lg p-3 mb-4">{error}</div>
              )}
              {status?.status === "failed" && (
                <button onClick={() => router.push("/dashboard")} className="text-sm text-gray-500 underline">
                  Skip to dashboard
                </button>
              )}
            </div>
          )}

          {/* Step 2: Your first patient */}
          {step === 2 && (
            <div>
              <div className="text-center mb-6">
                <div className="text-5xl mb-3">🧬</div>
                <h2 className="text-xl font-black text-gray-900 mb-2">Your demo patients are ready</h2>
                <p className="text-gray-500 text-sm">Click a patient to run your first assessment.</p>
              </div>

              <div className="space-y-3 mb-8">
                {DEMO_PATIENTS.map((p) => (
                  <div key={p.name} className="flex items-center justify-between p-4 rounded-xl border border-gray-200 hover:border-emerald-300 hover:bg-emerald-50 cursor-pointer transition-all group">
                    <div>
                      <p className="font-semibold text-gray-900 group-hover:text-emerald-700">{p.name}</p>
                      <p className="text-xs text-gray-500">{p.condition} · PhenoAge {p.phenoage}</p>
                    </div>
                    <div className="text-right">
                      <span className={`text-sm font-mono font-bold ${p.color}`}>{p.accel}</span>
                      <p className="text-xs text-gray-400">acceleration</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => router.push("/dashboard")}
                  className="flex-1 px-4 py-3 bg-emerald-600 text-white font-bold rounded-xl hover:bg-emerald-700 transition-colors"
                >
                  Go to dashboard →
                </button>
                <button
                  onClick={handleComplete}
                  disabled={completing}
                  className="px-4 py-3 bg-white text-gray-600 font-medium rounded-xl border border-gray-200 hover:border-gray-400 transition-colors disabled:opacity-50"
                >
                  {completing ? "Saving…" : "Mark complete"}
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Ready */}
          {step === 3 && (
            <div className="text-center">
              <div className="text-5xl mb-4">✅</div>
              <h2 className="text-xl font-black text-gray-900 mb-3">You're ready</h2>
              <p className="text-gray-600 mb-8 leading-relaxed">
                Your clinic is set up. Complete these 4 steps to get the most out of Longivity.
              </p>

              <div className="space-y-3 mb-8 text-left">
                {[
                  { label: "Add your first patient", done: true },
                  { label: "Upload a biomarker panel", done: true },
                  { label: "Run your first assessment", done: false },
                  { label: "Generate a test order", done: false },
                ].map((item) => (
                  <div key={item.label} className={`flex items-center gap-3 p-3 rounded-xl border ${
                    item.done ? "border-emerald-200 bg-emerald-50" : "border-gray-100"
                  }`}>
                    <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                      item.done ? "bg-emerald-500 text-white" : "bg-gray-200 text-gray-400"
                    }`}>
                      {item.done ? "✓" : "○"}
                    </div>
                    <span className={`text-sm font-medium ${item.done ? "text-emerald-700" : "text-gray-600"}`}>
                      {item.label}
                    </span>
                  </div>
                ))}
              </div>

              <button
                onClick={() => router.push("/dashboard")}
                className="w-full px-6 py-3 bg-emerald-600 text-white font-bold rounded-xl hover:bg-emerald-700 transition-colors"
              >
                Go to dashboard →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
