"use client";
import { cn, evidenceTierColor } from "@/lib/utils";

interface CompoundRec {
  compound_id: string;
  display_name: string;
  relevance_score: number;
  evidence_tier: string;
  evidence_tier_label: string;
  mr_anchor: string | null;
  hallmarks_targeted: string[];
}

interface Props {
  recs: CompoundRec[];
}

const TIER_LABELS: Record<string, string> = {
  MR_VALIDATED: "MR Validated",
  RCT: "RCT",
  OBSERVATIONAL: "Observational",
};

export default function CompoundRecsTable({ recs }: Props) {
  if (!recs || recs.length === 0) {
    return (
      <div className="text-sm text-gray-400 py-4 text-center">
        No compound recommendations for this panel.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {recs.map((rec) => (
        <div
          key={rec.compound_id}
          className="flex items-start gap-3 p-3 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors"
        >
          {/* Score bar */}
          <div className="flex-shrink-0 w-10 text-center">
            <div className="text-lg font-bold text-gray-900">
              {Math.round(rec.relevance_score * 100)}
            </div>
            <div className="text-xs text-gray-400">score</div>
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-medium text-gray-900 text-sm">{rec.display_name}</span>
              <span
                className={cn(
                  "text-xs px-2 py-0.5 rounded-full border font-medium",
                  evidenceTierColor(rec.evidence_tier)
                )}
              >
                {TIER_LABELS[rec.evidence_tier] || rec.evidence_tier}
              </span>
            </div>
            {rec.mr_anchor && (
              <p className="text-xs text-gray-500 mt-0.5">{rec.mr_anchor}</p>
            )}
            {rec.hallmarks_targeted?.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1.5">
                {rec.hallmarks_targeted.map((h) => (
                  <span key={h} className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                    {h.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Relevance bar */}
          <div className="flex-shrink-0 w-16">
            <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 rounded-full"
                style={{ width: `${Math.round(rec.relevance_score * 100)}%` }}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
