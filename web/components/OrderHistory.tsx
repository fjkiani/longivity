"use client";

import { SavedOrderSummary } from "@/lib/api";

interface Props {
  orders: SavedOrderSummary[];
  onViewOrder: (orderId: string) => void;
}

const statusConfig: Record<string, { label: string; className: string }> = {
  pending: { label: "Pending", className: "bg-yellow-100 text-yellow-800" },
  approved: { label: "Approved", className: "bg-blue-100 text-blue-800" },
  sent: { label: "Sent to Lab", className: "bg-purple-100 text-purple-800" },
  resulted: { label: "Resulted", className: "bg-green-100 text-green-800" },
  cancelled: { label: "Cancelled", className: "bg-gray-100 text-gray-600" },
};

export function OrderHistory({ orders, onViewOrder }: Props) {
  if (orders.length === 0) {
    return (
      <div className="text-center py-8 text-gray-400 text-sm">
        No test orders yet. Generate your first order above.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {orders.map((order) => {
        const status = statusConfig[order.status] || statusConfig.pending;
        const date = order.approved_at || order.generated_at;
        const formattedDate = date
          ? new Date(date).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
              year: "numeric",
            })
          : "—";

        return (
          <div
            key={order.order_id}
            className="flex items-center gap-4 p-4 bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${status.className}`}
                >
                  {status.label}
                </span>
                <span className="text-xs text-gray-400">{formattedDate}</span>
              </div>
              {order.summary && (
                <div className="mt-1 flex gap-4 text-xs text-gray-500">
                  <span>{order.summary.total_panels_recommended} panels</span>
                  <span>${order.summary.total_estimated_cost_usd?.toLocaleString()}</span>
                  <span>{order.summary.tier1_coverage_pct}% baseline coverage</span>
                  {order.summary.escalation_rules_triggered > 0 && (
                    <span className="text-orange-600">
                      {order.summary.escalation_rules_triggered} escalations
                    </span>
                  )}
                </div>
              )}
              {order.notes && (
                <p className="mt-1 text-xs text-gray-400 truncate">{order.notes}</p>
              )}
            </div>
            <button
              onClick={() => onViewOrder(order.order_id)}
              className="shrink-0 text-xs font-medium text-blue-600 hover:text-blue-800 hover:underline"
            >
              View
            </button>
          </div>
        );
      })}
    </div>
  );
}
