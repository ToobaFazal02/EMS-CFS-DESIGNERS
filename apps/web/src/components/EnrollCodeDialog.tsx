import { useEffect, useId, useRef, useState } from "react";

type Props = {
  open: boolean;
  employeeName: string;
  employeeCode: string;
  enrollCode: string;
  reenroll?: boolean;
  onClose: () => void;
};

/** Stays open until closed — enroll codes must not vanish in a toast. */
export function EnrollCodeDialog({
  open,
  employeeName,
  employeeCode,
  enrollCode,
  reenroll = false,
  onClose,
}: Props) {
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!open) return;
    setCopied(false);
    closeRef.current?.focus();
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  async function copyCode() {
    try {
      await navigator.clipboard.writeText(enrollCode);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <div
        className="modal-dialog enroll-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="modal-icon" aria-hidden>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="4" width="18" height="14" rx="2" stroke="currentColor" strokeWidth="2" />
            <path d="M8 21h8M12 18v3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </div>
        <h3 id={titleId} className="modal-title">
          {reenroll ? "Re-enroll PC" : "Enroll PC"}
        </h3>
        <p className="modal-message">
          Give this one-time code to <strong>{employeeName}</strong> (#{employeeCode}). They enter it in the CFS
          Agent on their PC. Keep this window open until they finish — the code disappears if you close it without
          copying.
        </p>
        <p className="modal-message" style={{ marginTop: 8, fontSize: 13 }}>
          Identity check: this PC must enroll as <strong>#{employeeCode}</strong>. That person must log in to the
          Manager with the same staff account — otherwise Live shows shots under one name and My Day looks empty
          under another.
        </p>
        <div className="enroll-code-box" aria-label={`Enroll code ${enrollCode}`}>
          {enrollCode}
        </div>
        <div className="modal-actions enroll-actions">
          <button type="button" className="secondary" onClick={copyCode}>
            {copied ? "Copied" : "Copy code"}
          </button>
          <button type="button" ref={closeRef} onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
