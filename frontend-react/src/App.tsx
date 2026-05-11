import { useCallback, useEffect, useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { ChatPane } from "./components/ChatPane";
import { PDFViewer } from "./components/PDFViewer";
import * as api from "./api/client";
import type { ChatMessage, IndexedDoc, StatsResponse } from "./types";

function makeId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [documents, setDocuments] = useState<IndexedDoc[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // PDF viewer state
  const [viewingDoc, setViewingDoc] = useState<string | null>(null);

  // Comparison mode state
  const [compareMode, setCompareMode] = useState(false);
  const [compareDocA, setCompareDocA] = useState<string | null>(null);
  const [compareDocB, setCompareDocB] = useState<string | null>(null);

  const refreshSidebar = useCallback(async () => {
    try {
      const [s, d] = await Promise.all([api.getStats(), api.listDocuments()]);
      setStats(s);
      setDocuments(d.documents);
    } catch (err) {
      console.error("Failed to refresh sidebar:", err);
    }
  }, []);

  useEffect(() => {
    refreshSidebar();
  }, [refreshSidebar]);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setUploadStatus(null);
    try {
      const res = await api.uploadPdf(file);
      setUploadStatus(
        `✅ Indexed "${res.document_name}" (${res.pages} pages, ${res.chunks_indexed} chunks)`,
      );
      await refreshSidebar();
    } catch (err) {
      setUploadStatus(`❌ Upload failed: ${(err as Error).message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleSend = async (text: string) => {
    const userMsg: ChatMessage = { id: makeId(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      let assistantMsg: ChatMessage;

      if (compareMode) {
        if (!compareDocA || !compareDocB) {
          throw new Error("Please select two documents in the sidebar.");
        }
        const res = await api.compare(text, compareDocA, compareDocB);
        assistantMsg = {
          id: makeId(),
          role: "assistant",
          content: res.answer,
          query_type: "explanation",
          sources: res.sources,
          isCompare: true,
        };
      } else {
        const res = await api.ask(text);
        assistantMsg = {
          id: makeId(),
          role: "assistant",
          content: res.answer,
          query_type: res.query_type,
          confidence: res.confidence,
          sources: res.sources,
        };
      }

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: makeId(),
          role: "assistant",
          content: `Error: ${(err as Error).message}`,
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearIndex = async () => {
    if (
      !confirm(
        "Clear the entire index? All uploaded PDFs will be removed from search.",
      )
    )
      return;
    try {
      await api.resetIndex();
      setMessages([]);
      setUploadStatus(null);
      setViewingDoc(null);
      await refreshSidebar();
    } catch (err) {
      alert(`Failed to clear index: ${(err as Error).message}`);
    }
  };

  const handleClearChat = () => {
    if (messages.length === 0) return;
    setMessages([]);
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        stats={stats}
        documents={documents}
        uploading={uploading}
        uploadStatus={uploadStatus}
        messages={messages}
        onViewDoc={setViewingDoc}
        compareMode={compareMode}
        setCompareMode={setCompareMode}
        compareDocA={compareDocA}
        setCompareDocA={(v) => {
          setCompareDocA(v);
          // reset B if it equals new A
          if (v && v === compareDocB) setCompareDocB(null);
        }}
        compareDocB={compareDocB}
        setCompareDocB={setCompareDocB}
        onUpload={handleUpload}
        onClearIndex={handleClearIndex}
        onClearChat={handleClearChat}
      />

      <ChatPane
        messages={messages}
        loading={loading}
        onSend={handleSend}
        compareMode={compareMode}
        compareDocA={compareDocA}
        compareDocB={compareDocB}
      />

      {viewingDoc && (
        <PDFViewer
          filename={viewingDoc}
          onClose={() => setViewingDoc(null)}
        />
      )}
    </div>
  );
}

export default App;