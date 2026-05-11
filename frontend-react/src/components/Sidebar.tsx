import { useRef } from "react";
import type { ChatMessage, IndexedDoc, StatsResponse } from "../types";
import { buildExportMarkdown, downloadMarkdown } from "../utils/export";

interface SidebarProps {
  stats: StatsResponse | null;
  documents: IndexedDoc[];
  uploading: boolean;
  uploadStatus: string | null;
  messages: ChatMessage[];

  // PDF viewer
  onViewDoc: (filename: string) => void;

  // Comparison mode
  compareMode: boolean;
  setCompareMode: (v: boolean) => void;
  compareDocA: string | null;
  setCompareDocA: (v: string | null) => void;
  compareDocB: string | null;
  setCompareDocB: (v: string | null) => void;

  onUpload: (file: File) => void;
  onClearIndex: () => void;
  onClearChat: () => void;
}

export function Sidebar({
  stats,
  documents,
  uploading,
  uploadStatus,
  messages,
  onViewDoc,
  compareMode,
  setCompareMode,
  compareDocA,
  setCompareDocA,
  compareDocB,
  setCompareDocB,
  onUpload,
  onClearIndex,
  onClearChat,
}: SidebarProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleExport = () => {
    const md = buildExportMarkdown(messages);
    const stamp = new Date()
      .toISOString()
      .replace(/[-:T]/g, "")
      .slice(0, 14);
    downloadMarkdown(md, `rag-qa-export-${stamp}.md`);
  };

  const docStems = [...new Set(documents.map((d) => d.stem))].sort();
  const docBOptions = docStems.filter((s) => s !== compareDocA);

  return (
    <aside className="w-80 bg-white border-r border-gray-200 h-screen flex flex-col overflow-y-auto">
      {/* Title */}
      <div className="p-5 border-b border-gray-200">
        <h2 className="text-xl font-bold flex items-center gap-2">
          Documents
        </h2>
      </div>

      {/* Upload */}
      <div className="p-5 border-b border-gray-200">
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          className="hidden"
          id="pdf-upload"
        />
        <label
          htmlFor="pdf-upload"
          className={`block w-full text-center py-2.5 px-4 rounded-lg border-2 border-dashed cursor-pointer transition-colors ${
            uploading
              ? "border-gray-300 bg-gray-50 text-gray-400 cursor-not-allowed"
              : "border-blue-300 bg-blue-50 hover:bg-blue-100 text-blue-700"
          }`}
        >
          {uploading ? "⏳ Indexing..." : "📤 Upload PDF"}
        </label>
        {uploadStatus && (
          <div className="mt-2 text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded p-2">
            {uploadStatus}
          </div>
        )}
      </div>

      {/* Index stats + clickable documents */}
      <div className="p-5 border-b border-gray-200">
        <h3 className="font-semibold text-gray-700 mb-3">Index</h3>
        <div className="bg-gray-50 rounded-lg p-3 mb-3">
          <div className="text-2xl font-bold text-gray-900">
            {stats?.total_chunks ?? 0}
          </div>
          <div className="text-xs text-gray-500 uppercase tracking-wide">
            Total chunks
          </div>
        </div>

        {documents.length > 0 ? (
          <div>
            <div className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">
              Click 👁️ to view
            </div>
            <ul className="space-y-1">
              {documents.map((d) => (
                <li
                  key={d.filename}
                  className="flex items-center gap-2 text-sm group"
                >
                  <span className="flex-1 truncate text-gray-700" title={d.stem}>
                    📄 {d.stem}
                  </span>
                  <button
                    onClick={() => onViewDoc(d.filename)}
                    className="opacity-50 group-hover:opacity-100 hover:bg-blue-100 rounded p-1 transition-all"
                    title={`View ${d.filename}`}
                  >
                    👁️
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <p className="text-xs text-gray-500">
            No documents indexed yet. Upload a PDF above to start.
          </p>
        )}
      </div>

      {/* Comparison mode */}
      <div className="p-5 border-b border-gray-200">
        <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
          🔀 Comparison mode
        </h3>
        <label className="flex items-center gap-2 cursor-pointer mb-3">
          <input
            type="checkbox"
            checked={compareMode}
            onChange={(e) => setCompareMode(e.target.checked)}
            className="w-4 h-4 accent-fuchsia-500"
          />
          <span className="text-sm text-gray-700">
            Compare two documents
          </span>
        </label>

        {compareMode && (
          <>
            {docStems.length < 2 ? (
              <div className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-2">
                ⚠️ Need at least 2 indexed documents.
              </div>
            ) : (
              <div className="space-y-2">
                <div>
                  <label className="text-xs text-gray-500 block mb-1">
                    Document A
                  </label>
                  <select
                    value={compareDocA || ""}
                    onChange={(e) => setCompareDocA(e.target.value || null)}
                    className="w-full text-sm border border-gray-300 rounded px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-fuchsia-300"
                  >
                    <option value="">Select...</option>
                    {docStems.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">
                    Document B
                  </label>
                  <select
                    value={compareDocB || ""}
                    onChange={(e) => setCompareDocB(e.target.value || null)}
                    disabled={!compareDocA}
                    className="w-full text-sm border border-gray-300 rounded px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-fuchsia-300 disabled:bg-gray-50"
                  >
                    <option value="">Select...</option>
                    {docBOptions.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Conversation export */}
      <div className="p-5 border-b border-gray-200">
        <h3 className="font-semibold text-gray-700 mb-3">Conversation</h3>
        <button
          onClick={handleExport}
          disabled={messages.length === 0}
          className="w-full px-3 py-2 text-sm bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 rounded disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed"
        >
          📥 Export conversation (.md)
        </button>
        {messages.length === 0 && (
          <p className="text-xs text-gray-500 mt-2">
            Ask something to enable export.
          </p>
        )}
      </div>

      {/* Advanced */}
      <div className="p-5 mt-auto">
        <details className="text-sm">
          <summary className="cursor-pointer font-medium text-gray-700 hover:text-gray-900">
            ⚙️ Advanced
          </summary>
          <div className="mt-3 space-y-2">
            <button
              onClick={onClearIndex}
              className="w-full px-3 py-2 text-sm text-red-700 bg-red-50 hover:bg-red-100 border border-red-200 rounded"
            >
              Clear index
            </button>
            <button
              onClick={onClearChat}
              className="w-full px-3 py-2 text-sm text-gray-700 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded"
            >
              Clear chat
            </button>
          </div>
        </details>
      </div>
    </aside>
  );
}