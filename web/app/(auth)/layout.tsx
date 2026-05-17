import Logo from "@/components/ui/logo";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <header className="absolute z-30 w-full">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="flex h-16 items-center md:h-20">
            <Logo />
          </div>
        </div>
      </header>

      <main className="relative flex grow min-h-screen">
        {/* Background glow */}
        <div className="pointer-events-none absolute bottom-0 left-0 -translate-x-1/3" aria-hidden="true">
          <div className="h-80 w-80 rounded-full bg-gradient-to-tr from-emerald-500 opacity-40 blur-[160px]"></div>
        </div>

        {/* Left: Auth form */}
        <div className="w-full lg:w-auto lg:flex-1">
          <div className="flex h-full flex-col justify-center before:min-h-[4rem] before:flex-1 after:flex-1 md:before:min-h-[5rem]">
            <div className="px-4 sm:px-6">
              <div className="mx-auto w-full max-w-sm">
                <div className="py-16 md:py-20">{children}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Longivity branded panel */}
        <div className="relative my-6 mr-6 hidden w-[540px] shrink-0 overflow-hidden rounded-2xl lg:block bg-gray-900">
          <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-gray-900 to-emerald-950" />
          <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-600/10 blur-3xl rounded-full" />
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-violet-600/10 blur-3xl rounded-full" />

          <div className="relative z-10 flex flex-col h-full p-12 justify-between">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold mb-8 tracking-widest uppercase">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                218 Tests Passing · Production Ready
              </div>

              <h2 className="text-3xl font-black text-white mb-3 tracking-tight leading-tight">
                The Intelligence Layer<br />
                <span className="text-emerald-400">Your Patients Deserve.</span>
              </h2>
              <p className="text-gray-400 font-medium mb-10 leading-relaxed">
                Longivity turns 315 biomarkers into one ranked clinical action. PhenoAge acceleration. Hallmark scoring. Deterministic state machine. No guessing.
              </p>

              <div className="grid grid-cols-2 gap-4 mb-10">
                <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Biomarkers</span>
                  </div>
                  <div className="text-3xl font-black text-white mb-1"><span className="text-emerald-400">315</span></div>
                  <div className="text-xs text-gray-500 font-medium">Tracked in registry</div>
                </div>
                <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <svg className="w-4 h-4 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Hallmarks</span>
                  </div>
                  <div className="text-3xl font-black text-white mb-1"><span className="text-violet-400">6</span></div>
                  <div className="text-xs text-gray-500 font-medium">Aging hallmarks scored</div>
                </div>
                <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <svg className="w-4 h-4 text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">States</span>
                  </div>
                  <div className="text-3xl font-black text-white mb-1"><span className="text-sky-400">6</span></div>
                  <div className="text-xs text-gray-500 font-medium">Patient state machine</div>
                </div>
                <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <svg className="w-4 h-4 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Actions</span>
                  </div>
                  <div className="text-3xl font-black text-white mb-1"><span className="text-rose-400">7</span></div>
                  <div className="text-xs text-gray-500 font-medium">Ranked action types</div>
                </div>
              </div>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
              <div className="flex gap-1 mb-4">
                {[...Array(5)].map((_, i) => (
                  <svg key={i} className="w-4 h-4 text-yellow-400 fill-yellow-400" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                ))}
              </div>
              <p className="text-gray-300 font-medium leading-relaxed mb-4 text-sm">
                &ldquo;Before Longivity, I was spending 20 minutes per patient cross-referencing PhenoAge calculators, hallmark literature, and escalation rules. Now I open the dashboard and the next action is already ranked. The science is the same — the time is not.&rdquo;
              </p>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white font-black text-sm">JP</div>
                <div>
                  <div className="text-white font-bold text-sm">Dr. James Park</div>
                  <div className="text-gray-500 text-xs font-medium">Longevity Medicine · San Francisco · 340 patients</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
