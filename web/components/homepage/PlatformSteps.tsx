"use client";
import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

const STEPS = [
  {
    n: 1,
    label: "Normalize",
    color: "emerald",
    tagline: "Your lab sends g/dL. The model needs g/L. We handle it.",
    doctorNote: "Labs across the US report the same biomarker in different units. Albumin comes in as g/dL, g/L, or just a number. Glucose arrives as mg/dL or mmol/L. CRP as mg/L, mg/dL, or already log-transformed. Before any math runs, every value is resolved to the canonical unit the Levine 2018 model expects — and every conversion is logged in the response so you can audit it.",
    demo: {
      type: "conversion",
      rows: [
        { label: "albumin", input: "4.5 g/dL", arrow: "× 10", output: "45.0 g/L", color: "emerald" },
        { label: "glucose", input: "95 mg/dL", arrow: "÷ 18.018", output: "5.27 mmol/L", color: "emerald" },
        { label: "crp",     input: "1.2 mg/L",  arrow: "÷10 → ln()", output: "−2.12 ln(mg/dL)", color: "emerald" },
      ],
    },
    failMode: "Out-of-range values are flagged with a warning note — but still used. Never silently rejected.",
  },
  {
    n: 2,
    label: "Score",
    color: "blue",
    tagline: "9 biomarkers → one biological age number.",
    doctorNote: "The Levine 2018 Gompertz proportional hazards model (PMID 29676998) converts 9 biomarkers + chronological age into a single biological age estimate. Validated in NHANES III (n=11,432). A patient with PhenoAge 10 years ahead of their calendar age has a mortality hazard ratio of ~2.2× compared to a matched peer. This is the number that drives everything downstream.",
    demo: {
      type: "phenoage",
      rows: [
        { label: "Chronological age", value: "52 yr", color: "gray" },
        { label: "PhenoAge estimate",  value: "64.2 yr", color: "red" },
        { label: "Acceleration",       value: "+12.2 yr", color: "red" },
        { label: "10yr mortality score", value: "18.4%", color: "red" },
      ],
    },
    failMode: "Fewer than 9 biomarkers → phenoage_estimate: null. Component linear terms still returned. completeness_mode: PARTIAL.",
  },
  {
    n: 3,
    label: "Map",
    color: "violet",
    tagline: "Which aging systems are active in this patient?",
    doctorNote: "Biomarker deviations are mapped to 6 of the 9 hallmarks of aging (López-Otín 2023, PMID 36599349). Elevated CRP → Intercellular Communication. High RDW → Mitochondrial Dysfunction. Low lymphocyte % → Cellular Senescence. PhenoAge-calibrated signals are kept strictly separate from threshold-based supplementary signals — never blended, always labeled.",
    demo: {
      type: "hallmarks",
      rows: [
        { label: "Intercellular Communication", status: "PRIMARY DRIVER",   color: "red",    pct: 88 },
        { label: "Mitochondrial Dysfunction",   status: "SECONDARY DRIVER", color: "orange", pct: 55 },
        { label: "Cellular Senescence",         status: "SECONDARY DRIVER", color: "orange", pct: 38 },
        { label: "Nutrient Sensing",            status: "OPTIMAL",          color: "emerald", pct: 0 },
      ],
    },
    failMode: "Hallmarks with no biomarker signal are absent from the response. hallmarks_scoreable count always shown.",
  },
  {
    n: 4,
    label: "Detect",
    color: "sky",
    tagline: "What's missing from this panel — and what to order next.",
    doctorNote: "The 315-marker registry is compared against the patient's existing biomarker keys. The system returns missing_tier1 (PhenoAge-required + high-significance), missing_tier2, coverage_pct, and which specific panels would fill the gaps. Sex-specific markers are filtered automatically. A patient with only a CMP + CBC has 31% Tier 1 coverage — the system tells you exactly what to order.",
    demo: {
      type: "gaps",
      coverage: 31,
      present: ["albumin", "creatinine", "glucose", "MCV", "WBC"],
      missing: ["CRP", "lymphocyte %", "RDW", "alk phos", "HbA1c", "vitamin D", "TSH"],
    },
    failMode: "Zero panels → coverage_pct: 0.0. Still returns a valid gap report with all tier-1 markers listed.",
  },
  {
    n: 5,
    label: "Route",
    color: "orange",
    tagline: "Where is this patient in their clinical journey?",
    doctorNote: "A deterministic state machine reads the patient's full clinical event timeline and assigns one of 6 states. No LLM. No randomness. The same inputs always produce the same state. State gates which actions are valid — a patient in MONITORING cannot be routed to 'order baseline panel.' Every state transition is unit-tested.",
    demo: {
      type: "states",
      states: ["NEW", "DATA INCOMPLETE", "ASSESSMENT PENDING", "ORDER PENDING", "COMPOUND CANDIDATE", "MONITORING"],
      active: 3,
    },
    failMode: "No timeline → state: NEW. Always returns one of 6 states. Never throws.",
  },
  {
    n: 6,
    label: "Recommend",
    color: "rose",
    tagline: "One action. Ranked. With a biological reason.",
    doctorNote: "All valid actions for the current state are scored using a weighted formula: 30% data urgency, 25% PhenoAge urgency, 25% escalation severity, 10% time decay, 10% hallmark signal. The top-ranked action is returned with a plain-English rationale and explicit evidence tier. The state machine gates which actions are even eligible — so the recommendation is always contextually appropriate.",
    demo: {
      type: "action",
      action: "Initiate insulin resistance protocol",
      urgency: "HIGH",
      score: 94,
      rationale: "PhenoAge +12.2yr. Glucose 108 + HbA1c 5.9% + fasting insulin 18.5 = HOMA-IR ~8.8. Metformin MR-validated (p=0.002).",
      tier: "MR_VALIDATED",
    },
    failMode: "No valid actions for state → returns upload_results action. Always returns at least one action.",
  },
];

const COLOR_MAP: Record<string, { bg: string; text: string; border: string; pill: string; bar: string; num: string }> = {
  emerald: { bg: "bg-emerald-50",  text: "text-emerald-700", border: "border-emerald-200", pill: "bg-emerald-100 text-emerald-800 border-emerald-300", bar: "bg-emerald-500", num: "bg-emerald-100 text-emerald-700" },
  blue:    { bg: "bg-blue-50",     text: "text-blue-700",    border: "border-blue-200",    pill: "bg-blue-100 text-blue-800 border-blue-300",    bar: "bg-blue-500",    num: "bg-blue-100 text-blue-700" },
  violet:  { bg: "bg-violet-50",   text: "text-violet-700",  border: "border-violet-200",  pill: "bg-violet-100 text-violet-800 border-violet-300",  bar: "bg-violet-500",  num: "bg-violet-100 text-violet-700" },
  sky:     { bg: "bg-sky-50",      text: "text-sky-700",     border: "border-sky-200",     pill: "bg-sky-100 text-sky-800 border-sky-300",     bar: "bg-sky-500",     num: "bg-sky-100 text-sky-700" },
  orange:  { bg: "bg-orange-50",   text: "text-orange-700",  border: "border-orange-200",  pill: "bg-orange-100 text-orange-800 border-orange-300",  bar: "bg-orange-500",  num: "bg-orange-100 text-orange-700" },
  rose:    { bg: "bg-rose-50",     text: "text-rose-700",    border: "border-rose-200",    pill: "bg-rose-100 text-rose-800 border-rose-300",    bar: "bg-rose-500",    num: "bg-rose-100 text-rose-700" },
  gray:    { bg: "bg-gray-50",     text: "text-gray-700",    border: "border-gray-200",    pill: "bg-gray-100 text-gray-700 border-gray-300",    bar: "bg-gray-400",    num: "bg-gray-100 text-gray-600" },
  red:     { bg: "bg-red-50",      text: "text-red-700",     border: "border-red-200",     pill: "bg-red-100 text-red-800 border-red-300",     bar: "bg-red-500",     num: "bg-red-100 text-red-700" },
};

function DemoWidget({ step }: { step: typeof STEPS[0] }) {
  const c = COLOR_MAP[step.color];
  const d = step.demo;

  if (d.type === "conversion") {
    return (
      <div className="space-y-2">
        {d.rows.map((row, i) => (
          <motion.div
            key={row.label}
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1, duration: 0.35 }}
            className="flex items-center gap-2 bg-white rounded-xl border border-gray-100 px-4 py-2.5"
          >
            <span className="font-mono text-xs text-gray-500 w-20 shrink-0">{row.label}</span>
            <span className="font-mono text-sm font-bold text-gray-800">{row.input}</span>
            <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-lg font-mono mx-1">{row.arrow}</span>
            <span className={`font-mono text-sm font-black ${COLOR_MAP[row.color].text}`}>{row.output}</span>
          </motion.div>
        ))}
      </div>
    );
  }

  if (d.type === "phenoage") {
    return (
      <div className="grid grid-cols-2 gap-3">
        {d.rows.map((row, i) => (
          <motion.div
            key={row.label}
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.1, duration: 0.35 }}
            className={`rounded-xl border p-3 ${COLOR_MAP[row.color].bg} ${COLOR_MAP[row.color].border}`}
          >
            <div className={`text-xl font-black tabular-nums ${COLOR_MAP[row.color].text}`}>{row.value}</div>
            <div className="text-xs text-gray-600 font-medium mt-0.5">{row.label}</div>
          </motion.div>
        ))}
      </div>
    );
  }

  if (d.type === "hallmarks") {
    return (
      <div className="space-y-2.5">
        {d.rows.map((row, i) => (
          <motion.div
            key={row.label}
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1, duration: 0.35 }}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-bold text-gray-800">{row.label}</span>
              <span className={`text-[10px] font-black px-2 py-0.5 rounded-full border ${COLOR_MAP[row.color].pill}`}>
                {row.status}
              </span>
            </div>
            {row.pct > 0 && (
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                  className={`h-full rounded-full ${COLOR_MAP[row.color].bar}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${row.pct}%` }}
                  transition={{ delay: i * 0.1 + 0.2, duration: 0.6, ease: "easeOut" }}
                />
              </div>
            )}
          </motion.div>
        ))}
      </div>
    );
  }

  if (d.type === "gaps") {
    return (
      <div className="space-y-3">
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-sm font-bold text-gray-700">Tier 1 Coverage</span>
            <span className={`text-lg font-black ${d.coverage < 50 ? "text-red-600" : "text-emerald-600"}`}>{d.coverage}%</span>
          </div>
          <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full bg-red-500"
              initial={{ width: 0 }}
              animate={{ width: `${d.coverage}%` }}
              transition={{ delay: 0.2, duration: 0.7, ease: "easeOut" }}
            />
          </div>
        </div>
        <div>
          <div className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Present</div>
          <div className="flex flex-wrap gap-1.5">
            {d.present.map((m) => (
              <span key={m} className="text-xs font-mono bg-emerald-50 border border-emerald-200 text-emerald-700 px-2 py-0.5 rounded-lg">{m}</span>
            ))}
          </div>
        </div>
        <div>
          <div className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Missing — order these</div>
          <div className="flex flex-wrap gap-1.5">
            {d.missing.map((m, i) => (
              <motion.span
                key={m}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.06 }}
                className="text-xs font-mono bg-red-50 border border-red-200 text-red-700 px-2 py-0.5 rounded-lg"
              >
                {m}
              </motion.span>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (d.type === "states") {
    return (
      <div className="space-y-2">
        {d.states.map((s, i) => (
          <motion.div
            key={s}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.08, duration: 0.3 }}
            className={`flex items-center gap-3 px-3 py-2 rounded-xl border transition-all ${
              i === d.active
                ? "bg-orange-500 border-orange-500 text-white shadow-md"
                : i < d.active
                ? "bg-gray-100 border-gray-200 text-gray-500"
                : "bg-white border-gray-200 text-gray-400"
            }`}
          >
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-black shrink-0 ${
              i === d.active ? "bg-white text-orange-600" : i < d.active ? "bg-gray-400 text-white" : "bg-gray-200 text-gray-400"
            }`}>{i + 1}</span>
            <span className="text-sm font-bold">{s}</span>
            {i === d.active && <span className="ml-auto text-[10px] font-black bg-white/20 px-2 py-0.5 rounded-full">CURRENT</span>}
          </motion.div>
        ))}
      </div>
    );
  }

  if (d.type === "action") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="bg-gray-900 rounded-2xl p-5 space-y-3"
      >
        <div className="flex items-start justify-between gap-3">
          <span className="text-xs font-black text-gray-400 uppercase tracking-wider">One Ranked Action</span>
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-xs font-black bg-red-100 text-red-800 border border-red-300 px-2.5 py-1 rounded-full">{d.urgency}</span>
            <span className="text-2xl font-black text-white tabular-nums">{d.score}</span>
          </div>
        </div>
        <div className="text-base font-black text-white leading-snug">{d.action}</div>
        <p className="text-sm text-gray-300 leading-relaxed">{d.rationale}</p>
        <span className="inline-block text-xs font-bold bg-emerald-900 text-emerald-300 border border-emerald-700 px-2.5 py-1 rounded-full">{d.tier}</span>
      </motion.div>
    );
  }

  return null;
}

export default function PlatformSteps() {
  const [active, setActive] = useState(0);
  const [paused, setPaused] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (paused) return;
    intervalRef.current = setInterval(() => {
      setActive((a) => (a + 1) % STEPS.length);
    }, 3200);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [paused]);

  const step = STEPS[active];
  const c = COLOR_MAP[step.color];

  return (
    <div
      className="grid grid-cols-1 lg:grid-cols-5 gap-8"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      {/* Left: step list */}
      <div className="lg:col-span-2 space-y-2">
        {STEPS.map((s, i) => {
          const sc = COLOR_MAP[s.color];
          const isActive = active === i;
          return (
            <button
              key={s.n}
              onClick={() => { setActive(i); setPaused(true); }}
              className={`w-full text-left rounded-2xl border-2 px-5 py-4 transition-all duration-200 ${
                isActive
                  ? `${sc.bg} ${sc.border} shadow-md`
                  : "bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50"
              }`}
            >
              <div className="flex items-center gap-3">
                <span className={`w-9 h-9 rounded-xl flex items-center justify-center font-black text-sm shrink-0 transition-all ${
                  isActive ? `${sc.bar} text-white` : "bg-gray-100 text-gray-500"
                }`}>{s.n}</span>
                <div className="flex-1 min-w-0">
                  <div className="font-black text-gray-900 text-sm">{s.label}</div>
                  <div className={`text-xs font-medium mt-0.5 truncate ${isActive ? sc.text : "text-gray-500"}`}>
                    {s.tagline}
                  </div>
                </div>
                {isActive && (
                  <motion.div
                    layoutId="activeArrow"
                    className={`w-1.5 h-8 rounded-full shrink-0 ${sc.bar}`}
                  />
                )}
              </div>
              {/* Progress bar for auto-advance */}
              {isActive && !paused && (
                <motion.div
                  className={`mt-3 h-0.5 rounded-full ${sc.bar} opacity-40`}
                  initial={{ width: "0%" }}
                  animate={{ width: "100%" }}
                  transition={{ duration: 3.2, ease: "linear" }}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Right: detail panel */}
      <div className="lg:col-span-3">
        <AnimatePresence mode="wait">
          <motion.div
            key={active}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            className="space-y-5"
          >
            {/* Header */}
            <div className={`rounded-2xl border-2 ${c.border} ${c.bg} p-6`}>
              <div className="flex items-center gap-3 mb-3">
                <span className={`w-10 h-10 rounded-xl flex items-center justify-center font-black text-lg ${c.bar} text-white`}>
                  {step.n}
                </span>
                <div>
                  <div className="font-black text-gray-900 text-xl">{step.label}</div>
                  <div className={`text-sm font-bold ${c.text}`}>{step.tagline}</div>
                </div>
              </div>
              <p className="text-sm text-gray-700 leading-relaxed">{step.doctorNote}</p>
            </div>

            {/* Demo widget */}
            <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
              <div className="text-xs font-black text-gray-400 uppercase tracking-wider mb-4">Live Example</div>
              <DemoWidget step={step} />
            </div>

            {/* Failure mode */}
            <div className="bg-gray-50 rounded-xl border border-gray-200 px-4 py-3 flex items-start gap-2">
              <span className="text-xs font-black text-gray-400 uppercase tracking-wider shrink-0 mt-0.5">Failure mode</span>
              <span className="text-sm text-gray-700">{step.failMode}</span>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
