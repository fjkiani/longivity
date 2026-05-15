"use client";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { formatDate } from "@/lib/utils";

interface DataPoint {
  date: string;
  value: number;
}

interface Props {
  data: DataPoint[];
  markerKey: string;
  markerDisplay?: string;
  unit?: string;
  refLow?: number | null;
  refHigh?: number | null;
  color?: string;
}

export default function BiomarkerTrendChart({
  data,
  markerKey,
  markerDisplay,
  unit,
  refLow,
  refHigh,
  color = "#16a34a",
}: Props) {
  const label = markerDisplay || markerKey;

  const formatted = data.map((d) => ({
    ...d,
    dateLabel: formatDate(d.date),
  }));

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-900">{label}</h3>
        {unit && <span className="text-xs text-gray-400">{unit}</span>}
      </div>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={formatted} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="dateLabel"
            tick={{ fontSize: 10, fill: "#9ca3af" }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={{ fontSize: 10, fill: "#9ca3af" }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            contentStyle={{
              fontSize: 12,
              border: "1px solid #e5e7eb",
              borderRadius: 8,
              boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
            }}
            formatter={(val) => [`${String(val ?? "")} ${unit || ""}`, label]}
            labelFormatter={(l) => l}
          />
          {refLow != null && (
            <ReferenceLine
              y={refLow}
              stroke="#fbbf24"
              strokeDasharray="4 2"
              label={{ value: "Low", fontSize: 9, fill: "#fbbf24" }}
            />
          )}
          {refHigh != null && (
            <ReferenceLine
              y={refHigh}
              stroke="#f87171"
              strokeDasharray="4 2"
              label={{ value: "High", fontSize: 9, fill: "#f87171" }}
            />
          )}
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            dot={{ r: 4, fill: color, strokeWidth: 0 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
