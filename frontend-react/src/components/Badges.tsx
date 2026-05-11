import type { Confidence, QueryType } from "../types";

const QUERY_TYPE_STYLES: Record<QueryType, { label: string; color: string }> = {
  lookup: { label: "🔍 Lookup", color: "bg-blue-500" },
  explanation: { label: "💡 Explanation", color: "bg-purple-500" },
  how_to: { label: "🛠️ How-To", color: "bg-emerald-500" },
  policy: { label: "📋 Policy", color: "bg-amber-500" },
  data: { label: "📊 Data (redirected)", color: "bg-red-500" },
};

const CONFIDENCE_STYLES: Record<NonNullable<Confidence>, { label: string; color: string }> = {
  high: { label: "🟢 High confidence", color: "bg-emerald-500" },
  medium: { label: "🟡 Medium confidence", color: "bg-amber-500" },
  low: { label: "🔴 Low confidence", color: "bg-red-500" },
};

const baseBadge =
  "inline-block px-2.5 py-1 rounded-full text-white text-xs font-semibold mr-1.5 mb-1";

export function QueryTypeBadge({ type }: { type: QueryType }) {
  const style = QUERY_TYPE_STYLES[type] || { label: type, color: "bg-gray-500" };
  return <span className={`${baseBadge} ${style.color}`}>{style.label}</span>;
}

export function ConfidenceBadge({ confidence }: { confidence: Confidence }) {
  if (!confidence) return null;
  const style = CONFIDENCE_STYLES[confidence];
  return <span className={`${baseBadge} ${style.color}`}>{style.label}</span>;
}

export function CompareBadge() {
  return <span className={`${baseBadge} bg-fuchsia-500`}>🔀 Comparison</span>;
}