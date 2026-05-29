import Link from "next/link";
import { Lead, Highlight } from "@/components/ui/typography";
import FadeIn from "@/components/ui/FadeIn";
import PlatformSteps from "@/components/homepage/PlatformSteps";
import ScienceSection from "@/components/homepage/ScienceSection";

export const metadata = {
  title: "Longevity — Clinical Intelligence for Longevity Medicine",
  description: "One ranked clinical action per patient. PhenoAge acceleration, hallmark scoring, and a deterministic state machine — built for longevity clinicians.",
};

export default function LandingPage() {
  return (
    <div className="bg-white text-gray-900">

      {/* ── Hero ─────────────────────────────────────────────────────────────── */}
      <section className="pt-36 pb-24 px-6 text-center">
        <div className="max-w-4xl mx-auto">
          <FadeIn delay={0}>
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm font-bold mb-8 shadow-sm">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Clinical Intelligence Platform · PhenoAge + Hallmarks + State Machine
            </div>
          </FadeIn>

          <FadeIn delay={0.08}>
            <h1 className="text-5xl md:text-7xl font-black text-gray-900 leading-tight mb-8 tracking-tight">
              One{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-600 to-teal-500">
                Decision.
              </span>
              <br />
              Per Patient.<br />
              Every Time.
            </h1>
          </FadeIn>

          <FadeIn delay={0.16}>
            <Lead className="max-w-3xl mx-auto mb-12">
              Longevity normalizes your lab inputs, computes{" "}
              <Highlight color="emerald">PhenoAge acceleration</Highlight>, scores{" "}
              <Highlight color="violet">6 hallmarks of aging</Highlight>, detects missing markers,
              routes the patient through a deterministic state machine, and returns{" "}
              <Highlight color="sky">one ranked action</Highlight> — with a biological reason and explicit provenance.
            </Lead>
          </FadeIn>

          <FadeIn delay={0.22}>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/demo"
                className="px-8 py-4 rounded-xl bg-gray-900 hover:bg-black text-white text-lg font-bold transition-all shadow-xl hover:shadow-gray-400/50 hover:-translate-y-1"
              >
                See It Run →
              </Link>
              <Link
                href="/login"
                className="px-8 py-4 rounded-xl bg-white border-2 border-gray-200 hover:border-gray-300 text-gray-800 text-lg font-bold transition-all hover:bg-gray-50 flex items-center gap-2"
              >
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                Enter Clinic Dashboard
              </Link>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ── Problem / Stats bar ──────────────────────────────────────────────── */}
      <section className="pb-16 px-6">
        <div className="max-w-6xl mx-auto">
          <FadeIn>
            <div className="bg-gray-900 rounded-3xl p-8 md:p-12 shadow-2xl border border-gray-800 flex flex-col md:flex-row items-start justify-between gap-8">
              <div className="text-left md:w-1/2">
                <h3 className="text-2xl font-black text-white mb-3">The Intelligence Lives in the Clinician's Head</h3>
                <p className="text-gray-300 font-medium leading-relaxed">
                  A single patient visit generates 80–300 biomarker values. Today, a clinician makes 4–6 API calls and mentally stitches the answer together. When the clinician leaves, the reasoning leaves with them. That is not a SaaS product — it is a collection of tools.
                </p>
              </div>
              <div className="grid grid-cols-2 gap-6 md:w-1/2">
                {[
                  { label: "Registry",  value: "315", sub: "Biomarkers tracked",      color: "text-emerald-400" },
                  { label: "Hallmarks", value: "6",   sub: "Aging systems scored",    color: "text-violet-400" },
                  { label: "States",    value: "6",   sub: "Patient state machine",   color: "text-sky-400" },
                  { label: "Rules",     value: "50+", sub: "Escalation triggers",     color: "text-rose-400" },
                ].map((s) => (
                  <div key={s.label} className="flex flex-col gap-1">
                    <span className="text-gray-400 text-xs font-bold uppercase tracking-wider">{s.label}</span>
                    <span className={`text-3xl font-black ${s.color}`}>{s.value}</span>
                    <span className="text-gray-400 text-sm font-medium">{s.sub}</span>
                  </div>
                ))}
              </div>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ── Platform: Six Transformations ───────────────────────────────────── */}
      <section id="platform" className="py-24 px-6 bg-gray-50 border-y border-gray-100">
        <div className="max-w-6xl mx-auto">
          <FadeIn className="text-center mb-14">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gray-200 text-gray-600 text-xs font-bold uppercase tracking-wider mb-4">
              Platform
            </div>
            <h2 className="text-4xl md:text-5xl font-black text-gray-900 mb-5 tracking-tight">
              Six Transformations on Patient Data
            </h2>
            <p className="text-lg text-gray-700 font-medium max-w-3xl mx-auto leading-relaxed">
              Not six features. Six sequential operations that convert fragmented lab inputs into a structured clinical decision.
              Click any step — or watch the auto-advance — to see exactly what happens and why it matters for your patients.
            </p>
          </FadeIn>

          <FadeIn delay={0.1}>
            <PlatformSteps />
          </FadeIn>
        </div>
      </section>

      {/* ── Science: Provenance ──────────────────────────────────────────────── */}
      <section id="science" className="py-24 px-6 bg-gray-900">
        <div className="max-w-6xl mx-auto">
          <FadeIn className="text-center mb-14">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-gray-300 text-xs font-bold uppercase tracking-wider mb-4">
              Science
            </div>
            <h2 className="text-4xl md:text-5xl font-black text-white mb-5 tracking-tight">
              What Is Validated. What Is Not.
            </h2>
            <p className="text-lg text-gray-200 font-medium max-w-3xl mx-auto leading-relaxed">
              We separate mortality-calibrated signals from threshold-based signals. Every compound recommendation carries an explicit evidence tier. We tell you what is proven and what is inferred — and we never conflate the two.
            </p>
          </FadeIn>

          <ScienceSection />
        </div>
      </section>

      {/* ── Workflow ─────────────────────────────────────────────────────────── */}
      <section id="workflow" className="py-24 px-6 bg-white">
        <div className="max-w-5xl mx-auto">
          <FadeIn className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-black text-gray-900 mb-5 tracking-tight">
              From Blood Draw to Next Action
            </h2>
            <p className="text-lg text-gray-700 font-medium max-w-2xl mx-auto leading-relaxed">
              Four steps. Under 2 seconds for the compute. Every action writes to the patient timeline.
            </p>
          </FadeIn>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {[
              { step: "01", color: "bg-gray-100 text-gray-700",    title: "Upload",  body: "PDF from Quest, LabCorp, or manual entry. 20+ unit aliases handled automatically. albumin in g/dL or g/L — both work." },
              { step: "02", color: "bg-emerald-50 text-emerald-700", title: "Compute", body: "Six transformations run: normalize, PhenoAge, hallmarks, gap detection, state machine, action scoring. Under 2 seconds." },
              { step: "03", color: "bg-violet-50 text-violet-700",  title: "Review",  body: "One ranked action with a biological reason. Full scoring breakdown visible. Every component auditable. Provenance labeled." },
              { step: "04", color: "bg-sky-50 text-sky-700",        title: "Act",     body: "Click the CTA. Generate a test order, run an assessment, or start a compound protocol. Every action writes to the patient timeline." },
            ].map((item, i) => (
              <FadeIn key={i} delay={i * 0.1}>
                <div className="flex flex-col items-center text-center">
                  <div className={`w-16 h-16 rounded-2xl ${item.color} flex items-center justify-center mb-4 font-black text-xl`}>
                    {item.step}
                  </div>
                  <h3 className="text-lg font-black text-gray-900 mb-2">{item.title}</h3>
                  <p className="text-sm text-gray-700 leading-relaxed">{item.body}</p>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────────────────── */}
      <section className="py-24 px-6 bg-emerald-50 border-t border-emerald-100">
        <div className="max-w-4xl mx-auto text-center">
          <FadeIn>
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-rose-50 border border-rose-200 text-rose-700 text-sm font-bold mb-8 shadow-sm">
              <span className="w-2 h-2 rounded-full bg-rose-500" />
              Research Use Only (RUO)
            </div>
            <h2 className="text-4xl md:text-5xl font-black text-gray-900 mb-6 tracking-tight">
              Built for Clinicians Who Want to Reason Faster, Not Harder.
            </h2>
            <p className="text-lg text-gray-700 font-medium max-w-3xl mx-auto mb-12 leading-relaxed">
              Longevity does not replace clinical judgment. It eliminates the 20 minutes of manual cross-referencing before you can exercise it.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/demo"
                className="px-8 py-4 rounded-xl bg-gray-900 hover:bg-black text-white text-lg font-black transition-all shadow-xl hover:-translate-y-1 flex items-center gap-3"
              >
                See the Demo →
              </Link>
              <Link
                href="/login"
                className="px-8 py-4 rounded-xl bg-white border-2 border-gray-200 hover:border-gray-300 text-gray-800 text-lg font-bold transition-all hover:bg-gray-50"
              >
                Enter Clinic Dashboard
              </Link>
            </div>
          </FadeIn>
        </div>
      </section>

    </div>
  );
}
