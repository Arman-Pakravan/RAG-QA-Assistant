import { useState } from "react";
import type { ChatMessage } from "../types";
import { QueryTypeBadge, ConfidenceBadge, CompareBadge } from "./Badges";
import { SourceCard } from "./SourceCard";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 mb-5 ${isUser ? "flex-row-reverse" : ""}`}>
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center text-lg ${
          isUser ? "bg-blue-100" : "bg-gray-200"
        }`}
      >
        {isUser ? "🧑" : "🤖"}
      </div>

      {/* Bubble */}
      <div className={`flex-1 max-w-3xl ${isUser ? "text-right" : ""}`}>
        <div
          className={`inline-block text-left px-4 py-3 rounded-2xl ${
            isUser
              ? "bg-blue-500 text-white"
              : message.isError
              ? "bg-red-50 border border-red-300 text-red-800"
              : "bg-white border border-gray-200"
          }`}
        >
          {/* Badges (assistant only) */}
          {!isUser && (message.query_type || message.confidence || message.isCompare) && (
            <div className="mb-2">
              {message.query_type && <QueryTypeBadge type={message.query_type} />}
              {message.confidence && <ConfidenceBadge confidence={message.confidence} />}
              {message.isCompare && <CompareBadge />}
            </div>
          )}

          {/* Content (preserve newlines) */}
          <div className="whitespace-pre-wrap break-words">{message.content}</div>

          {/* Sources */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="mt-3">
              <button
                onClick={() => setShowSources(!showSources)}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                {showSources ? "▼" : "▶"} 📚 Sources ({message.sources.length})
              </button>
              {showSources && (
                <div className="mt-2">
                  {message.sources.map((src, i) => (
                    <SourceCard key={i} index={i + 1} source={src} />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}