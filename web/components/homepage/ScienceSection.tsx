"use client";
import { useState, useEffect, useRef } from "react";
import { motion, useInView } from "framer-motion";

// ── Animated counter ──────────────────────────────────────────────────────────
function Counter({ target, suffix = "", duration = 1.4 }: { target: number; suffix?: string; duration?: number }) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });

  useEffect(() => {
    if (!inView) return;
    let start = 0;
    const steps = 40;
    const increment = target / steps;
    const interval = (duration * 1000) / steps;
    const timer = setInterval(() => {
      start += increment;
      if (start >= target) { setCount(target); clearInterval(timer); }
      else setCount(Math.floor(start));
    }, interval);
    return () => clearInterval(timer);
  }, [inView, target, duration]);

  return <span ref={ref}>{count}{suffix}</span>;
}

// ── Evidence tiers ────────────────────────────────────────────────────────────
const TIERS = [
  {
    id: "mr",
    label: "MR_VALIDATED",
    badge: "bg-emerald-100 text-emerald-800 border-emerald-300",
    headerBg: "bg-emerald-950/60 border-emerald-800/60",
    icon: "✦",
    iconColor: "text-emerald-400",
    headline: "Mendelian Randomization — Causal Evidence",
    description: "These compounds have causal evidence from Mendelian Randomization studies linking them to aging clock endpoints. The genetic instrument removes confounding. This is the strongest evidence tier in the registry.",
    compounds: [
      { name: "Omega-3 (EPA/DHA)", ref: "Fabian 2025", pmid: "DOI 10.1186/s40246-025-00756-3", detail: "Oily fish → PhenoAge acceleration IVW p=0.0086. Fish oil → GrimAge IVW p=0.037.", dose: "2–4g EPA+DHA daily" },
      { name: "Vitamin D3",        ref: "Hagenbeek 2022", pmid: "PMID 36055464", detail: "Genetically predicted 25-OHD → lower GrimAge. IVW p=0.04.", dose: "2000–4000 IU daily" },
      { name: "Folate (5-MTHF)",   ref: "Fenech 2012",    pmid: "PMID 22516734", detail: "Folate → PhenoAge IVW p=0.03. Critical for MTHFR compound het carriers.", dose: "400–800mcg 5-MTHF" },
      { name: "Metformin",         ref: "Kulkarni 2020",  pmid: "PMID 32483234", detail: "AMPK activation → PhenoAge reduction IVW p=0.002. Strongest metabolic anchor.", dose: "500mg QD → BID (Rx)" },
    ],
  },
  {
    id: "rct",
    label: "RCT",
    badge: "bg-blue-100 text-blue-800 border-blue-300",
    headerBg: "bg-blue-950/60 border-blue-800/60",
    icon: "◆",
    iconColor: "text-blue-400",
    headline: "Randomized Controlled Trials",
    description: "Compounds with RCT evidence for relevant endpoints (glucose, inflammation, lipids, cognitive function). Strong evidence but not causally linked to aging clock endpoints via MR.",
    compounds: [
      { name: "Berberine",    ref: "Yin 2008",    pmid: "PMID 18397984", detail: "Comparable to metformin for glucose control in RCTs. AMPK activator.", dose: "500mg TID with meals" },
      { name: "NMN",          ref: "Yoshino 2021", pmid: "PMID 33471759", detail: "NAD+ precursor. Improved muscle insulin sensitivity in postmenopausal women.", dose: "250–500mg daily" },
      { name: "Quercetin",    ref: "Kirkland 2017", pmid: "PMID 28273775", detail: "Senolytic activity in combination with dasatinib. Reduces senescent cell burden.", dose: "500–1000mg with dasatinib" },
      { name: "Urolithin A",  ref: "Andreux 2019", pmid: "PMID 31534559", detail: "Mitophagy activator. Improved muscle function in older adults.", dose: "500–1000mg daily" },
    ],
  },
  {
    id: "obs",
    label: "OBSERVATIONAL",
    badge: "bg-gray-200 text-gray-700 border-gray-300",
    headerBg: "bg-gray-800/60 border-gray-700/60",
    icon: "●",
    iconColor: "text-gray-400",
    headline: "Observational / Preclinical",
    description: "Compounds with observational or preclinical evidence. Directionally interesting but not yet proven in RCTs for aging endpoints. Labeled clearly — never conflated with higher tiers.",
    compounds: [
      { name: "Rapamycin",    ref: "Harrison 2009", pmid: "PMID 19587680", detail: "mTOR inhibitor. Extended lifespan in mice. Human longevity data limited.", dose: "Off-label — physician discretion" },
      { name: "Resveratrol",  ref: "Baur 2006",     pmid: "PMID 17086191", detail: "SIRT1 activator in preclinical models. Human RCT results mixed.", dose: "Evidence insufficient for dosing" },
      { name: "Spermidine",   ref: "Eisenberg 2016", pmid: "PMID 27841876", detail: "Autophagy inducer. Observational association with longevity in humans.", dose: "1–5mg daily (food sources preferred)" },
    ],
  },
];

const LIMITS = [
  { label: "No methylation array", detail: "Epigenetic clocks accept pre-computed values only" },
  { label: "No telomere assay",    detail: "LTL accepted as input, not scored numerically" },
  { label: "Research Use Only",    detail: "Not a medical device — RUO label applies" },
];

const STATS = [
  { value: 4,   suffix: "",  label: "MR-Validated compounds",  color: "text-emerald-400" },
  { value: 8,   suffix: "",  label: "Published source anchors", color: "text-blue-400" },
  { value: 218, suffix: "",  label: "Tests passing",            color: "text-violet-400" },
  { value: 315, suffix: "",  label: "Biomarkers in registry",   color: "text-sky-400" },
];

export default function ScienceSection() {
  const [openTier, setOpenTier] = useState("mr");

  return (
    <div className="space-y-12">
      {/* Animated stat counters */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        {STATS.map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ delay: i * 0.1, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="text-center"
          >
            <div className={`text-5xl font-black tabular-nums ${s.color}`}>
              <Counter target={s.value} suffix={s.suffix} />
            </div>
            <div className="text-sm text-gray-300 font-medium mt-1">{s.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Evidence tier accordion */}
      <div className="space-y-3">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.5 }}
          className="mb-6"
        >
          <h3 className="text-xl font-black text-white mb-1">Evidence Tiers — Every Compound Labeled</h3>
          <p className="text-gray-300 text-sm leading-relaxed">
            We don't mix MR-validated causal evidence with observational associations. Every compound recommendation carries an explicit tier. Click a tier to see the compounds and their source citations.
          </p>
        </motion.div>

        {TIERS.map((tier, ti) => {
          const isOpen = openTier === tier.id;
          return (
            <motion.div
              key={tier.id}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ delay: ti * 0.08, duration: 0.4 }}
              className={`rounded-2xl border overflow-hidden ${tier.headerBg}`}
            >
              <button
                onClick={() => setOpenTier(isOpen ? "" : tier.id)}
                className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-white/5 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className={`text-lg font-black ${tier.iconColor}`}>{tier.icon}</span>
                  <span className={`text-xs font-black px-2.5 py-1 rounded-full border ${tier.badge}`}>
                    {tier.label}
                  </span>
                  <span className="text-white font-bold text-sm hidden sm:block">{tier.headline}</span>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-xs text-gray-400 font-medium">{tier.compounds.length} compounds</span>
                  <motion.span
                    animate={{ rotate: isOpen ? 180 : 0 }}
                    transition={{ duration: 0.2 }}
                    className="text-gray-400 text-lg leading-none"
                  >
                    ↓
                  </motion.span>
                </div>
              </button>

              <AnimatePresenceWrapper isOpen={isOpen}>
                <div className="px-6 pb-5 space-y-4">
                  <p className="text-sm text-gray-300 leading-relaxed border-t border-white/10 pt-4">{tier.description}</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {tier.compounds.map((c, ci) => (
                      <motion.div
                        key={c.name}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: ci * 0.07, duration: 0.3 }}
                        className="bg-white/5 border border-white/10 rounded-xl p-4"
                      >
                        <div className="flex items-start justify-between gap-2 mb-1">
                          <span className="text-white font-black text-sm">{c.name}</span>
                          <span className="text-[10px] font-mono text-gray-400 shrink-0">{c.pmid}</span>
                        </div>
                        <p className="text-xs text-gray-300 leading-relaxed mb-2">{c.detail}</p>
                        <div className="text-xs font-bold text-gray-400">
                          <span className="text-gray-500">Dose: </span>{c.dose}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </AnimatePresenceWrapper>
            </motion.div>
          );
        })}
      </div>

      {/* Hard limits strip */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-40px" }}
        transition={{ duration: 0.4 }}
        className="flex flex-col sm:flex-row items-start sm:items-center gap-3 bg-white/5 border border-white/10 rounded-2xl px-6 py-4"
      >
        <span className="text-xs font-black text-gray-400 uppercase tracking-wider shrink-0">Hard limits</span>
        <div className="flex flex-wrap gap-2">
          {LIMITS.map((l) => (
            <div key={l.label} className="flex items-center gap-1.5 bg-gray-800 border border-gray-700 rounded-xl px-3 py-1.5">
              <span className="w-3 h-3 rounded-full bg-gray-600 flex items-center justify-center shrink-0">
                <svg className="w-2 h-2 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </span>
              <span className="text-xs font-bold text-white">{l.label}</span>
              <span className="text-xs text-gray-400 hidden sm:inline">— {l.detail}</span>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}

// Framer AnimatePresence wrapper for accordion
function AnimatePresenceWrapper({ isOpen, children }: { isOpen: boolean; children: React.ReactNode }) {
  return (
    <motion.div
      initial={false}
      animate={{ height: isOpen ? "auto" : 0, opacity: isOpen ? 1 : 0 }}
      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      style={{ overflow: "hidden" }}
    >
      {children}
    </motion.div>
  );
}
