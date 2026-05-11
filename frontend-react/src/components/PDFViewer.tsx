import { pdfUrl } from "../api/client";

interface PDFViewerProps {
  filename: string;
  onClose: () => void;
}

export function PDFViewer({ filename, onClose }: PDFViewerProps) {
  const url = pdfUrl(filename);

  return (
    <div className="w-2/5 border-l border-gray-200 bg-white flex flex-col h-screen">
      <div className="flex items-center justify-between px-5 py-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xl">📄</span>
          <span className="font-semibold truncate" title={filename}>
            {filename}
          </span>
        </div>
        <button
          onClick={onClose}
          className="ml-3 w-8 h-8 rounded-full flex items-center justify-center text-gray-500 hover:bg-red-50 hover:text-red-600 transition-colors"
          title="Close viewer"
        >
          ✖
        </button>
      </div>

      <div className="flex-1 p-3">
        <iframe
          src={url}
          title={filename}
          className="w-full h-full border border-gray-200 rounded"
        />
      </div>

      <div className="px-5 py-2 text-xs text-gray-500 border-t border-gray-100">
        💡 Can't see the PDF?{" "}
        <a
          href={url}
          target="_blank"
          rel="noreferrer"
          className="text-blue-600 hover:underline"
        >
          Open in new tab
        </a>
      </div>
    </div>
  );
}