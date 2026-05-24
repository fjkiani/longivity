"use client";
import { useEffect, useState } from "react";
import { getUser } from "@/lib/auth";

/**
 * DemoBanner — thin top bar shown when logged in as the demo account.
 * Renders nothing for real users.
 */
export default function DemoBanner() {
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    const user = getUser();
    if (user?.is_demo || user?.email === "demo@longivity.ai") {
      setIsDemo(true);
    }
  }, []);

  if (!isDemo) return null;

  return (
    <div className="bg-amber-50 border-b border-amber-200 px-4 py-1.5 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
        <span className="text-xs text-amber-800 font-semibold">
          Demo Mode — Research Use Only
        </span>
        <span className="text-xs text-amber-600">
          · Synthetic data derived from NHANES, LonGenity, MESA, InCHIANTI, BLSA
        </span>
      </div>
      <a
        href="/demo-login"
        className="text-xs text-amber-700 hover:text-amber-900 font-medium underline"
      >
        About this demo
      </a>
    </div>
  );
}
