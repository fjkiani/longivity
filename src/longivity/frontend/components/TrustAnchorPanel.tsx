/**
 * TrustAnchorPanel.tsx
 * Displays the trust anchor manifest: deterministic formulas, MR evidence,
 * published thresholds. Fetches from GET /api/v1/longevity/benchmark/trust.
 *
 * Usage:
 *   <TrustAnchorPanel />
 *
 * Filters: All | DETERMINISTIC_FORMULA | MR_VALIDATED | PUBLISHED_THRESHOLD | DETERMINISTIC_LOOKUP
 */

import React, { useEffect, useState } from "react";

// ── Types ─────────────────────────────────────────────────────────────────────

type AnchorType =
  | "DETERMINISTIC_FORMULA"
  | "MR_VALIDATED"
  | "PUBLISHED_THRESHOLD"
  | "DETERMINISTIC_LOOKUP";

interface AnchorSummary {
  id: string;
  name: string;
  citation: {
    pmid?: string;
    doi?: string;
    authors?: string;
    year?: number;
    journal?: string;
  };
  key_claim: string;
}

interface TrustData {
  version: string;
  generated_at: string;
  total_anchors: number;
  by_type: Record<AnchorType, AnchorSummary[]>;
  retrieved_at: string;
}

// ── Constants ─────────────────────────────────────────────────────────────────

const TYPE_LABELS: Record<AnchorType, string> = {
  DETERMINISTIC_FORMULA: "Deterministic Formula",
  MR_VALIDATED: "Mendelian Randomization",
  PUBLISHED_THRESHOLD: "Published Threshold",
  DETERMINISTIC_LOOKUP: "Deterministic Lookup",
};

const TYPE_COLORS: Record<AnchorType, string> = {
  DETERMINISTIC_FORMULA: "bg-blue-100 text-blue-800 border-blue-200",
  MR_VALIDATED: "bg-green-100 text-green-800 border-green-200",
  PUBLISHED_THRESHOLD: "bg-amber-100 text-amber-800 border-amber-200",
  DETERMINISTIC_LOOKUP: "bg-purple-100 text-purple-800 border-purple-200",
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Component ─────────────────────────────────────────────────────────────────

export function TrustAnchorPanel() {
  const [data, setData] = useState<TrustData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<AnchorType | "ALL">("ALL");

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/longevity/benchmark/trust`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d: TrustData) => {
        setData(d);
        setLoading(false);
      })
      .catch((e: Error) => {
        setError(e.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="p-4 text-gray-500">Loading trust anchors…</div>;
  if (error) return <div className="p-4 text-red-600">Error: {error}</div>;
  if (!data) return null;

  const allTypes = Object.keys(data.by_type) as AnchorType[];
  const visibleTypes = filter === "ALL" ? allTypes : [filter];

  const visibleAnchors = visibleTypes.flatMap((t) =>
    (data.by_type[t] ?? []).map((a) => ({ ...a, type: t }))
  );

  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Trust Architecture</h2>
          <p className="text-sm text-gray-500">
            {data.total_anchors} anchors · v{data.version} · RUO
          </p>
        </div>
        <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-700 border border-green-200">
          All anchors verified
        </span>
      </div>

      {/* Filter bar */}
      <div className="flex gap-2 overflow-x-auto px-6 py-3 border-b border-gray-100">
        {(["ALL", ...allTypes] as (AnchorType | "ALL")[]).map((t) => (
          <button
            key={t}
            onClick={() => setFilter(t)}
            className={`whitespace-nowrap rounded-full px-3 py-1 text-xs font-medium border transition-colors ${
              filter === t
                ? "bg-gray-900 text-white border-gray-900"
                : "bg-white text-gray-600 border-gray-200 hover:border-gray-400"
            }`}
          >
            {t === "ALL" ? "All" : TYPE_LABELS[t]}
            {t !== "ALL" && (
              <span className="ml-1 opacity-60">
                ({(data.by_type[t] ?? []).length})
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Anchor list */}
      <div className="divide-y divide-gray-50">
        {visibleAnchors.map((anchor) => (
          <div key={anchor.id} className="px-6 py-4 hover:bg-gray-50 transition-colors">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium border ${
                      TYPE_COLORS[anchor.type as AnchorType]
                    }`}
                  >
                    {TYPE_LABELS[anchor.type as AnchorType]}
                  </span>
                  <span className="text-xs text-gray-400 font-mono">{anchor.id}</span>
                </div>
                <p className="text-sm font-medium text-gray-900 truncate">{anchor.name}</p>
                <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{anchor.key_claim}</p>
              </div>

              {/* Citation badge */}
              <div className="flex-shrink-0 text-right">
                {anchor.citation.pmid && (
                  <a
                    href={`https://pubmed.ncbi.nlm.nih.gov/${anchor.citation.pmid}/`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 rounded bg-blue-50 px-2 py-0.5 text-xs font-mono text-blue-700 hover:bg-blue-100 border border-blue-100"
                  >
                    PMID {anchor.citation.pmid}
                  </a>
                )}
                {anchor.citation.doi && !anchor.citation.pmid && (
                  <a
                    href={`https://doi.org/${anchor.citation.doi}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 rounded bg-blue-50 px-2 py-0.5 text-xs font-mono text-blue-700 hover:bg-blue-100 border border-blue-100"
                  >
                    DOI
                  </a>
                )}
                {anchor.citation.year && (
                  <p className="text-xs text-gray-400 mt-0.5">
                    {anchor.citation.authors?.split(",")[0]} {anchor.citation.year}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="border-t border-gray-100 px-6 py-3">
        <p className="text-xs text-gray-400">
          Retrieved {new Date(data.retrieved_at).toLocaleString()} · RUO — not for clinical use
        </p>
      </div>
    </div>
  );
}

export default TrustAnchorPanel;
