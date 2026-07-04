"use client";
/**
 * OnboardingChecklist — persistent sidebar widget shown on dashboard
 * for clinics where onboarding_completed_at is null.
 * Fetches GET /api/v1/onboarding/checklist and shows 4 steps.
 * Disappears when all 4 steps are complete.
 */
import { useEffect, useState } from "react";
import { onboardingApi, ChecklistStep } from "@/lib/api";

export function OnboardingChecklist() {
  const [steps, setSteps] = useState<ChecklistStep[]>([]);
  const [loading, setLoading] = useState(true);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    onboardingApi
      .getChecklist()
      .then((data) => {
        setSteps(data.steps);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Hide if all complete or dismissed
  const allComplete = steps.length > 0 && steps.every((s) => s.completed);
  if (loading || allComplete || dismissed) return null;

  const completedCount = steps.filter((s) => s.completed).length;
  const pct = steps.length > 0 ? Math.round((completedCount / steps.length) * 100) : 0;

  return (
    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 mb-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-black text-emerald-900">Get started</h3>
          <p className="text-xs text-emerald-700">{completedCount}/{steps.length} steps complete</p>
        </div>
        <button
          onClick={() => setDismissed(true)}
          className="text-emerald-400 hover:text-emerald-600 text-lg leading-none"
          aria-label="Dismiss"
        >
          ×
        </button>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-emerald-200 rounded-full mb-4 overflow-hidden">
        <div
          className="h-full bg-emerald-500 rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Steps */}
      <div className="space-y-2">
        {steps.map((step) => (
          <div key={step.id} className="flex items-start gap-2.5">
            <div className={`mt-0.5 w-4 h-4 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold ${
              step.completed
                ? "bg-emerald-500 text-white"
                : "bg-white border-2 border-emerald-300 text-emerald-400"
            }`}>
              {step.completed ? "✓" : ""}
            </div>
            <div className="flex-1 min-w-0">
              <p className={`text-xs font-semibold leading-tight ${
                step.completed ? "text-emerald-700 line-through opacity-60" : "text-gray-800"
              }`}>
                {step.label}
              </p>
              {!step.completed && (
                <p className="text-xs text-gray-500 mt-0.5 leading-tight">{step.description}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default OnboardingChecklist;
