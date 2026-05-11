import type { ChatMessage } from "../types";

export function buildExportMarkdown(messages: ChatMessage[]): string {
  const now = new Date();
  const stamp = now.toISOString().replace("T", " ").slice(0, 19);

  const lines: string[] = [
    "# RAG QA Assistant — Conversation Export",
    `_Exported: ${stamp}_`,
    "",
  ];

  if (messages.length === 0) {
    lines.push("_(No messages yet)_");
    return lines.join("\n");
  }

  let qNum = 0;
  for (const msg of messages) {
    if (msg.role === "user") {
      qNum++;
      lines.push(`## Q${qNum}: ${msg.content}`);
      lines.push("");
    } else {
      const meta: string[] = [];
      if (msg.query_type) meta.push(`**Type:** ${msg.query_type}`);
      if (msg.confidence) meta.push(`**Confidence:** ${msg.confidence}`);
      if (msg.isCompare) meta.push(`**Mode:** Comparison`);
      if (meta.length > 0) {
        lines.push(meta.join(" • "));
        lines.push("");
      }
      lines.push(msg.content);
      lines.push("");
      if (msg.sources && msg.sources.length > 0) {
        lines.push("**Sources:**");
        msg.sources.forEach((s, i) => {
          lines.push(
            `- [${i + 1}] \`${s.document_name || "Unknown"}\` — ` +
              `section *${s.section_title || "Unknown"}* ` +
              `(score ${s.score.toFixed(3)})`,
          );
        });
        lines.push("");
      }
      lines.push("---");
      lines.push("");
    }
  }
  return lines.join("\n");
}

export function downloadMarkdown(content: string, filename: string) {
  const blob = new Blob([content], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}