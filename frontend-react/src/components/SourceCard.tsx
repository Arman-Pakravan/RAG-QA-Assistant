import type { Source } from "../types";

export function SourceCard({ index, source }: { index: number; source: Source }) {
  return (
    <div className="bg-gray-50 border-l-4 border-blue-500 px-3.5 py-2.5 rounded-md my-1.5 text-sm">
      <div className="font-semibold">
        [{index}] {source.document_name || "Unknown"}
      </div>
      <div className="text-gray-700">
        Section: <em>{source.section_title || "Unknown"}</em>
      </div>
      <div className="text-gray-600 text-xs mt-0.5">
        Type: {source.content_type || "unknown"} • Score: {source.score.toFixed(3)}
      </div>
    </div>
  );
}