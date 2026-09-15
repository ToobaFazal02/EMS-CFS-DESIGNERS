import { useEffect } from "react";
import { createPortal } from "react-dom";

type Props = {
  open: boolean;
  title?: string;
  blobUrl: string | null;
  onClose: () => void;
};

/** In-app PDF viewer — works in Tauri WebView2 where window.open(blob) is unreliable. */
export function PdfPreviewModal({ open, title = "PDF", blobUrl, onClose }: Props) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open || !blobUrl) return null;

  return createPortal(
    <div className="pdf-preview-backdrop" role="dialog" aria-modal="true" aria-label={title} onClick={onClose}>
      <div className="pdf-preview-panel card" onClick={(e) => e.stopPropagation()}>
        <div className="pdf-preview-toolbar">
          <strong>{title}</strong>
          <div className="pdf-preview-actions">
            <a className="secondary" href={blobUrl} target="_blank" rel="noopener noreferrer">
              Open tab
            </a>
            <button type="button" className="secondary" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
        <iframe title={title} src={blobUrl} className="pdf-preview-frame" />
      </div>
    </div>,
    document.body
  );
}
