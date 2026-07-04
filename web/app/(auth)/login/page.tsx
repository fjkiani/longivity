"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api";
import { saveAuth } from "@/lib/auth";
import Logo from "@/components/ui/logo";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [clinicName, setClinicName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      let res;
      if (mode === "login") {
        res = await authApi.login(email, password);
      } else {
        res = await authApi.register(email, password, fullName, clinicName || "My Clinic");
      }
      saveAuth(res.access_token, {
        id: res.user_id,
        email: res.email,
        full_name: res.full_name,
        clinic_id: res.clinic_id,
      });
      if (mode === "register") {
        // Trigger onboarding: seed demo patients, then redirect to wizard
        try {
          const { onboardingApi } = await import("@/lib/api");
          const ob = await onboardingApi.start("trial", true);
          router.push(`/onboarding?id=${ob.onboarding_id}`);
        } catch {
          // Onboarding start failed — still go to dashboard
          router.push("/dashboard");
        }
      } else {
        router.push("/dashboard");
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Something went wrong";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      {/* Logo (mobile only — desktop shows in layout header) */}
      <div className="mb-8 lg:hidden">
        <Logo />
      </div>

      <div className="mb-8">
        <h1 className="text-2xl font-black text-gray-900 mb-1">
          {mode === "login" ? "Welcome back" : "Create your account"}
        </h1>
        <p className="text-sm text-gray-500 font-medium">
          {mode === "login"
            ? "Sign in to your Longevity clinic dashboard."
            : "Start your longevity practice intelligence layer."}
        </p>
      </div>

      {/* Tabs */}
      <div className="flex rounded-xl bg-gray-100 p-1 mb-8">
        <button
          onClick={() => setMode("login")}
          className={`flex-1 py-2 text-sm font-bold rounded-lg transition-all ${
            mode === "login"
              ? "bg-white shadow-sm text-gray-900 ring-1 ring-gray-200"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          Sign In
        </button>
        <button
          onClick={() => setMode("register")}
          className={`flex-1 py-2 text-sm font-bold rounded-lg transition-all ${
            mode === "register"
              ? "bg-white shadow-sm text-gray-900 ring-1 ring-gray-200"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          Create Account
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {mode === "register" && (
          <>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white shadow-sm w-full"
                placeholder="Dr. Jane Smith"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">Clinic Name</label>
              <input
                type="text"
                value={clinicName}
                onChange={(e) => setClinicName(e.target.value)}
                className="border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white shadow-sm w-full"
                placeholder="Longevity Medical Center"
              />
            </div>
          </>
        )}

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1.5">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white shadow-sm w-full"
            placeholder="doctor@clinic.com"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1.5">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            className="border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white shadow-sm w-full"
            placeholder="••••••••"
          />
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700 font-medium">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-gray-900 hover:bg-black disabled:opacity-50 text-white font-bold py-3 rounded-xl text-sm transition-all shadow-sm hover:-translate-y-0.5"
        >
          {loading ? "Loading..." : mode === "login" ? "Sign In" : "Create Account"}
        </button>
      </form>

      <p className="text-xs text-center text-gray-400 mt-8">
        Research Use Only (RUO). Not for clinical diagnosis.
      </p>
    </div>
  );
}
