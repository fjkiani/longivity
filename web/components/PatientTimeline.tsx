"use client";

import React, { useEffect, useState } from "react";
import { PatientTimeline as PatientTimelineType, intelligenceApi } from "@/lib/api";

const EVENT_ICONS: Record<string, string> = {
  panel_uploaded: "📋",
  panel_created_manual: "✏️",
  assessment_run: "📊",
  test_order_generated: "🧪",
  test_order_approved: "✅",
  test_order_sent: "📬",
  test_order_resulted: "📥",
  compound_started: "💊",
  compound_stopped: "🛑",
  intelligence_computed: "🤖",
  clinician_note: "📝",
};

const EVENT_COLORS: Record<string, string> = {
  panel_uploaded: "border-blue-300 bg-blue-50",
  panel_created_manual: "border-blue-300 bg-blue-50",
  assessment_run: "border-purple-300 bg-purple-50",
  test_order_generated: "border-yellow-300 bg-yellow-50",
  test_order_approved: "border-green-300 bg-green-50",
  intelligence_computed: "border-gray-200 bg-gray-50",
  compound_started: "border-pink-300 bg-pink-50",
};

interface Props {
  patientId: string;
}

export default function PatientTimeline({ patientId }: Props) {
  const [timeline, setTimeline] = useState<PatientTimelineType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    intelligenceApi
      .getPatientTimeline(patientId)
      .then(setTimeline)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [patientId]);

  if (loading) {
    return (
      <div className="text-sm text-gray-400 py-6 text-center">
        Loading timeline…
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-sm text-red-500 py-4">
        Could not load timeline: {error}
      </div>
    );
  }

  if (!timeline || timeline.events.length === 0) {
    return (
      <div className="text-sm text-gray-400 py-6 text-center">
        No clinical events recorded yet.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {timeline.events.map((event) => {
        const icon = EVENT_ICONS[event.event_type] || "•";
        const colorClass =
          EVENT_COLORS[event.event_type] || "border-gray-200 bg-white";
        return (
          <div
            key={event.id}
            className={`rounded-lg border p-3 ${colorClass}`}
          >
            <div className="flex items-start gap-3">
              <span className="text-lg shrink-0">{icon}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <span className="text-sm font-medium text-gray-800">
                    {event.summary}
                  </span>
                  <span className="text-xs text-gray-400 shrink-0">
                    {new Date(event.event_at).toLocaleString()}
                  </span>
                </div>
                {event.actor_name && (
                  <div className="text-xs text-gray-500 mt-0.5">
                    by {event.actor_name}
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
