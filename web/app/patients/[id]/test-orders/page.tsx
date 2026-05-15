"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { testOrdersApi, registryApi, TestOrder, SavedOrderSummary, BiomarkerGaps } from "@/lib/api";
import { GapSummaryCard } from "@/components/GapSummaryCard";
import { TestOrderReview } from "@/components/TestOrderReview";
import { OrderHistory } from "@/components/OrderHistory";

type View = "overview" | "generate" | "review" | "history" | "view-order";

export default function TestOrdersPage() {
  const params = useParams();
  const router = useRouter();
  const patientId = params.id as string;

  const [view, setView] = useState<View>("overview");
  const [gaps, setGaps] = useState<BiomarkerGaps | null>(null);
  const [generatedOrder, setGeneratedOrder] = useState<TestOrder | null>(null);
  const [savedOrders, setSavedOrders] = useState<SavedOrderSummary[]>([]);
  const [viewingOrder, setViewingOrder] = useState<TestOrder | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load gaps and order history on mount
  useEffect(() => {
    loadData();
  }, [patientId]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [gapsData, ordersData] = await Promise.all([
        testOrdersApi.getGaps(patientId),
        testOrdersApi.list(patientId),
      ]);
      setGaps(gapsData);
      setSavedOrders(ordersData);
    } catch (e: any) {
      setError(e.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const order = await testOrdersApi.generate(patientId);
      setGeneratedOrder(order);
      setView("review");
    } catch (e: any) {
      setError(e.message || "Failed to generate order");
    } finally {
      setGenerating(false);
    }
  };

  const handleApproved = async (orderId: string) => {
    await loadData();
    setView("history");
    setGeneratedOrder(null);
  };

  const handleViewOrder = async (orderId: string) => {
    setLoading(true);
    try {
      const order = await testOrdersApi.get(patientId, orderId);
      setViewingOrder(order as any);
      setView("view-order");
    } catch (e: any) {
      setError(e.message || "Failed to load order");
    } finally {
      setLoading(false);
    }
  };

  if (loading && !gaps) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400 text-sm">Loading...</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
      {/* Back to patient */}
      <button
        onClick={() => router.push(`/patients/${patientId}`)}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
      >
        ← Back to Patient
      </button>

      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Test Orders</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Agent-driven lab test ordering — gap detection, hallmark mapping, escalation rules
          </p>
        </div>
        {view !== "review" && (
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {generating ? (
              <>
                <span className="animate-spin">⟳</span>
                Analyzing...
              </>
            ) : (
              <>
                <span>+</span>
                Generate Order
              </>
            )}
          </button>
        )}
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Tab nav */}
      {view !== "review" && view !== "view-order" && (
        <div className="flex gap-1 border-b border-gray-200">
          {(["overview", "history"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setView(tab)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                view === tab
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab === "overview" ? "Overview" : `Order History (${savedOrders.length})`}
            </button>
          ))}
        </div>
      )}

      {/* Overview tab */}
      {view === "overview" && (
        <div className="space-y-6">
          {gaps && <GapSummaryCard gaps={gaps} />}

          {/* Quick stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              label="Total Markers"
              value="315"
              sub="in registry"
              color="blue"
            />
            <StatCard
              label="Test Panels"
              value="45"
              sub="orderable"
              color="green"
            />
            <StatCard
              label="Escalation Rules"
              value="50"
              sub="deterministic"
              color="orange"
            />
            <StatCard
              label="Hallmarks Covered"
              value="6"
              sub="aging hallmarks"
              color="purple"
            />
          </div>

          {/* How it works */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">How the Agent Works</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <StepCard
                step="1"
                title="Gap Detection"
                description="Compares existing biomarker values against the required set for this patient's age and sex. Identifies missing baseline, expanded, and specialty markers."
                color="blue"
              />
              <StepCard
                step="2"
                title="Hallmark Mapping"
                description="Maps active longevity hallmarks (nutrient sensing, inflammaging, etc.) to the test panels that assess them. Prioritizes panels covering multiple hallmarks."
                color="green"
              />
              <StepCard
                step="3"
                title="Escalation Rules"
                description="Applies 50 deterministic rules to existing values. Example: LDL > 130 → order ApoB, Lp(a), NMR LipoProfile. No LLM required."
                color="orange"
              />
            </div>
          </div>

          {savedOrders.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Recent Orders</h3>
              <OrderHistory
                orders={savedOrders.slice(0, 3)}
                onViewOrder={handleViewOrder}
              />
              {savedOrders.length > 3 && (
                <button
                  onClick={() => setView("history")}
                  className="mt-2 text-xs text-blue-600 hover:underline"
                >
                  View all {savedOrders.length} orders →
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {/* History tab */}
      {view === "history" && (
        <OrderHistory orders={savedOrders} onViewOrder={handleViewOrder} />
      )}

      {/* Review generated order */}
      {view === "review" && generatedOrder && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setView("overview")}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              ← Back
            </button>
            <h2 className="text-base font-semibold text-gray-900">Review & Approve Order</h2>
          </div>
          <TestOrderReview
            patientId={patientId}
            order={generatedOrder}
            onApproved={handleApproved}
            onCancel={() => setView("overview")}
          />
        </div>
      )}

      {/* View saved order */}
      {view === "view-order" && viewingOrder && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setView("history")}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              ← Back to History
            </button>
            <h2 className="text-base font-semibold text-gray-900">Order Details</h2>
            <span className="text-xs text-gray-400">
              {new Date(viewingOrder.generated_at).toLocaleDateString()}
            </span>
          </div>
          <TestOrderReview
            patientId={patientId}
            order={viewingOrder}
            onApproved={handleApproved}
            onCancel={() => setView("history")}
          />
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  sub,
  color,
}: {
  label: string;
  value: string;
  sub: string;
  color: "blue" | "green" | "orange" | "purple";
}) {
  const colors = {
    blue: "bg-blue-50 border-blue-200",
    green: "bg-green-50 border-green-200",
    orange: "bg-orange-50 border-orange-200",
    purple: "bg-purple-50 border-purple-200",
  };
  const textColors = {
    blue: "text-blue-700",
    green: "text-green-700",
    orange: "text-orange-700",
    purple: "text-purple-700",
  };

  return (
    <div className={`rounded-xl border p-4 text-center ${colors[color]}`}>
      <div className={`text-2xl font-bold ${textColors[color]}`}>{value}</div>
      <div className="text-xs font-medium text-gray-700 mt-0.5">{label}</div>
      <div className="text-xs text-gray-400">{sub}</div>
    </div>
  );
}

function StepCard({
  step,
  title,
  description,
  color,
}: {
  step: string;
  title: string;
  description: string;
  color: "blue" | "green" | "orange";
}) {
  const colors = {
    blue: "bg-blue-600",
    green: "bg-green-600",
    orange: "bg-orange-600",
  };

  return (
    <div className="flex gap-3">
      <div
        className={`shrink-0 w-7 h-7 rounded-full ${colors[color]} text-white text-xs font-bold flex items-center justify-center`}
      >
        {step}
      </div>
      <div>
        <div className="text-sm font-semibold text-gray-900">{title}</div>
        <p className="text-xs text-gray-500 mt-1 leading-relaxed">{description}</p>
      </div>
    </div>
  );
}
