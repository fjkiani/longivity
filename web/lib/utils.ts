import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

export function formatAge(dob: string | null | undefined): string {
  if (!dob) return "—";
  try {
    const d = new Date(dob);
    const today = new Date();
    const age =
      today.getFullYear() -
      d.getFullYear() -
      (today.getMonth() < d.getMonth() ||
      (today.getMonth() === d.getMonth() && today.getDate() < d.getDate())
        ? 1
        : 0);
    return `${age} yrs`;
  } catch {
    return "—";
  }
}

export function tierColor(tier: string): string {
  switch (tier?.toLowerCase()) {
    case "healthy":
    case "optimal":
      return "text-green-600 bg-green-50";
    case "borderline":
    case "moderate":
      return "text-yellow-600 bg-yellow-50";
    case "accelerated":
    case "high":
      return "text-red-600 bg-red-50";
    default:
      return "text-gray-600 bg-gray-50";
  }
}

export function evidenceTierColor(tier: string): string {
  switch (tier?.toUpperCase()) {
    case "MR_VALIDATED":
      return "text-purple-700 bg-purple-50 border-purple-200";
    case "RCT":
      return "text-blue-700 bg-blue-50 border-blue-200";
    case "OBSERVATIONAL":
      return "text-gray-600 bg-gray-50 border-gray-200";
    default:
      return "text-gray-500 bg-gray-50 border-gray-200";
  }
}

export function markerStatus(value: number, refLow: number | null, refHigh: number | null): "low" | "normal" | "high" | "unknown" {
  if (refLow === null && refHigh === null) return "unknown";
  if (refLow !== null && value < refLow) return "low";
  if (refHigh !== null && value > refHigh) return "high";
  return "normal";
}
