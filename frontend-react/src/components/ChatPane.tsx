import { useEffect, useRef, useState } from "react";
import type { ChatMessage } from "../types";
import { MessageBubble } from "./MessageBubble";

interface ChatPaneProps {
  messages: ChatMessage[];
  loading: boolean;
  onSend: (text: string) => void;
  compareMode: boolean;
  compareDocA: string | null;
  compareDocB: string | null;
}

export function ChatPane({
  messages,
  loading,
  onSend,
  compareMode,
  compareDocA,
  compareDocB,
}: ChatPaneProps) {
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    onSend(text);
    setInput("");
  };

  return (
    <div className="flex-1 flex flex-col h-screen min-w-0">
      <header className="px-8 py-5 border-b border-gray-200 bg-white">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          📄 RAG QA Assistant
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Ask questions grounded in your uploaded PDFs. Answers cite their sources.
        </p>
      </header>

      {/* Comparison banner */}
      {compareMode && (
        <div className="mx-8 mt-4 px-4 py-3 rounded-lg bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 text-sm">
          <span className="font-semibold">🔀 Comparison mode:</span>{" "}
          questions will compare{" "}
          <em className="text-purple-700">{compareDocA || "—"}</em> vs{" "}
          <em className="text-purple-700">{compareDocB || "—"}</em>.
        </div>
      )}

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-8 py-6">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-center">
            <div>
              <div className="text-6xl mb-3">💬</div>
              <p className="text-gray-500 font-medium">No messages yet</p>
              <p className="text-sm text-gray-400 mt-1">
                Upload a PDF and ask a question to get started.
              </p>
            </div>
          </div>
        ) : (
          messages.map((m) => <MessageBubble key={m.id} message={m} />)
        )}
        {loading && (
          <div className="flex gap-3 mb-5">
            <div className="w-9 h-9 rounded-full bg-gray-200 flex items-center justify-center">
              🤖
            </div>
            <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 text-gray-500">
              <span className="inline-flex gap-1">
                <span className="animate-bounce">●</span>
                <span
                  className="animate-bounce"
                  style={{ animationDelay: "0.15s" }}
                >
                  ●
                </span>
                <span
                  className="animate-bounce"
                  style={{ animationDelay: "0.3s" }}
                >
                  ●
                </span>
              </span>
              <span className="ml-2 text-sm">Thinking...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="px-8 py-4 border-t border-gray-200 bg-white"
      >
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              compareMode
                ? "Ask one question — both docs will be compared..."
                : "Ask a question about your documents..."
            }
            disabled={loading}
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 disabled:bg-gray-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-5 py-2.5 bg-blue-500 hover:bg-blue-600 text-white rounded-full font-medium disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}