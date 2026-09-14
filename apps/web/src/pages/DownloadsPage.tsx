import { useEffect, useRef, useState } from "react";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { useToast } from "../components/ToastProvider";

const MANAGER_SETUP = "/downloads/CFS-Designers-Manager-Setup.exe";
const AGENT_ZIP = "/downloads/CFS-Agent-Install.zip";

type ProgressState = {
  label: string;
  pct: number;
  receivedMb: number;
  totalMb: number | null;
} | null;

function DownloadIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M12 4v10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M8 11l4 4 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M5 19h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function MonitorIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden>
      <rect x="3" y="4" width="18" height="12" rx="2" stroke="currentColor" strokeWidth="1.8" />
      <path d="M8 20h8M12 16v4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function ChipIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden>
      <rect x="7" y="7" width="10" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.8" />
      <path
        d="M9 3v4M12 3v4M15 3v4M9 17v4M12 17v4M15 17v4M3 9h4M3 12h4M3 15h4M17 9h4M17 12h4M17 15h4"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M12 3l7 3v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  );
}

function fileNameFromUrl(url: string) {
  try {
    return decodeURIComponent(url.split("/").pop() || "download");
  } catch {
    return "download";
  }
}

function looksLikeHtml(bytes: Uint8Array): boolean {
  const n = Math.min(64, bytes.length);
  let s = "";
  for (let i = 0; i < n; i++) s += String.fromCharCode(bytes[i]);
  const t = s.trimStart().toLowerCase();
  return t.startsWith("<!doctype") || t.startsWith("<html") || t.startsWith("<head");
}

function validateDownloadBytes(url: string, label: string, bytes: Uint8Array): string | null {
  if (bytes.length < 8) return `${label} is empty or incomplete. Try again.`;
  if (looksLikeHtml(bytes)) {
    return `${label} is missing on the server (got a web page instead of the file). Ask admin to upload the real installer to /downloads.`;
  }
  const name = fileNameFromUrl(url).toLowerCase();
  if (name.endsWith(".zip")) {
    // ZIP local file header: PK\x03\x04
    if (!(bytes[0] === 0x50 && bytes[1] === 0x4b && (bytes[2] === 0x03 || bytes[2] === 0x05 || bytes[2] === 0x07))) {
      return `${label} is not a valid zip (file is damaged or wrong). Re-upload CFS-Agent-Install.zip (~50 MB).`;
    }
    if (bytes.length < 100_000) {
      return `${label} is too small (${Math.round(bytes.length / 1024)} KB). Real Agent zip is ~50 MB — server file is wrong.`;
    }
  }
  if (name.endsWith(".exe")) {
    // PE: MZ
    if (!(bytes[0] === 0x4d && bytes[1] === 0x5a)) {
      return `${label} is not a valid Windows installer. Ask admin to re-upload the file.`;
    }
    if (bytes.length < 1_000_000) {
      return `${label} is too small to be the Manager installer. Re-upload from the build.`;
    }
  }
  if (name.endsWith(".msi")) {
    // MSI is OLE compound: D0 CF 11 E0 …
    if (!(bytes[0] === 0xd0 && bytes[1] === 0xcf && bytes[2] === 0x11 && bytes[3] === 0xe0)) {
      return `${label} is not a valid MSI. Ask admin to re-upload the file.`;
    }
    if (bytes.length < 1_000_000) {
      return `${label} is too small to be the Manager MSI. Re-upload from the build.`;
    }
  }
  return null;
}

/**
 * Downloads hub — login required (office + staff).
 * Enroll code still required for Agent (security).
 */
export function DownloadsPage() {
  const toast = useToast();
  const [progress, setProgress] = useState<ProgressState>(null);
  const [cancelOpen, setCancelOpen] = useState(false);
  const busyRef = useRef(false);
  const abortRef = useRef<AbortController | null>(null);
  const progressRef = useRef<HTMLDivElement>(null);
  const shouldScrollToProgressRef = useRef(false);

  // Auto-scroll to progress after React paints it (rAF alone races setState).
  useEffect(() => {
    if (!progress || !shouldScrollToProgressRef.current) return;
    shouldScrollToProgressRef.current = false;
    progressRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    progressRef.current?.focus({ preventScroll: true });
  }, [progress]);

  function requestCancel() {
    if (!busyRef.current || !abortRef.current) return;
    setCancelOpen(true);
  }

  function confirmCancel() {
    setCancelOpen(false);
    abortRef.current?.abort();
  }

  async function startDownload(url: string, label: string) {
    if (busyRef.current) return;
    busyRef.current = true;
    const ac = new AbortController();
    abortRef.current = ac;

    // Show top progress immediately (before network) so Agent/Setup both feel instant
    shouldScrollToProgressRef.current = true;
    setProgress({ label, pct: 0, receivedMb: 0, totalMb: null });
    toast.success(`${label} started — progress is at the top of this page.`);

    try {
      const res = await fetch(url, { cache: "no-store", signal: ac.signal });
      if (!res.ok) {
        toast.error(
          res.status === 404
            ? `${label} file is missing on the server. Ask admin to upload it to /downloads.`
            : `${label} could not start (error ${res.status}). Try again.`
        );
        setProgress(null);
        return;
      }
      const total = Number(res.headers.get("Content-Length") || 0);
      const totalMb = total > 0 ? Math.round((total / 1024 / 1024) * 10) / 10 : null;
      const reader = res.body?.getReader();
      if (!reader) {
        toast.error("Download failed. Try again.");
        setProgress(null);
        return;
      }
      const chunks: Uint8Array[] = [];
      let received = 0;
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        if (value) {
          chunks.push(value);
          received += value.length;
          const pct =
            total > 0
              ? Math.min(100, Math.round((received / total) * 100))
              : Math.min(99, Math.round(received / 1024 / 50));
          const receivedMb = Math.round((received / 1024 / 1024) * 10) / 10;
          setProgress({ label, pct, receivedMb, totalMb });
        }
      }
      setProgress({
        label,
        pct: 100,
        receivedMb: Math.round((received / 1024 / 1024) * 10) / 10,
        totalMb,
      });
      const merged = new Uint8Array(received);
      let offset = 0;
      for (const c of chunks) {
        merged.set(c, offset);
        offset += c.length;
      }
      const invalid = validateDownloadBytes(url, label, merged);
      if (invalid) {
        toast.error(invalid);
        setProgress(null);
        return;
      }
      const blob = new Blob([merged]);
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = objectUrl;
      a.download = fileNameFromUrl(url);
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(objectUrl);
      toast.success(`Success — ${label} downloaded (${Math.round(received / 1024 / 1024) || 1} MB). Check your Downloads folder.`);
      window.setTimeout(() => setProgress(null), 1200);
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        toast.success("Download cancelled.");
      } else {
        toast.error(`Could not download ${label}. Check your connection or try again.`);
      }
      setProgress(null);
    } finally {
      busyRef.current = false;
      abortRef.current = null;
      setCancelOpen(false);
    }
  }

  const downloading = Boolean(progress);

  return (
    <div className="downloads-page downloads-lovable">
      <div className="toolbar">
        <div>
          <h2 style={{ margin: 0 }}>Downloads</h2>
        </div>
      </div>

      {progress ? (
        <div className="dl-progress card" role="status" aria-live="polite" ref={progressRef} tabIndex={-1}>
          <div className="dl-progress-top">
            <strong>{progress.label}</strong>
            <div className="dl-progress-actions">
              <span className="dl-progress-pct">{progress.pct}%</span>
              <button
                type="button"
                className="dl-progress-cancel"
                onClick={requestCancel}
                aria-label="Cancel download"
                title="Cancel download"
              >
                <CloseIcon />
                Cancel
              </button>
            </div>
          </div>
          <div className="dl-progress-track" aria-hidden>
            <i className="dl-progress-bar" style={{ width: `${progress.pct}%` }} />
          </div>
          <p className="muted dl-progress-cap">
            {progress.pct < 100
              ? `Downloading… ${progress.receivedMb} MB${
                  progress.totalMb != null ? ` / ${progress.totalMb} MB` : ""
                } · Chrome download bar appears when the file finishes`
              : "Saving file to your Downloads folder…"}
          </p>
        </div>
      ) : null}

      <ConfirmDialog
        open={cancelOpen}
        title="Cancel download?"
        message="Progress will be lost. You can start the download again anytime."
        confirmLabel="Yes, cancel"
        cancelLabel="Keep downloading"
        danger
        onConfirm={confirmCancel}
        onCancel={() => setCancelOpen(false)}
      />

      <div className="downloads-grid">
        <article className="card downloads-card">
          <div className="dl-card-head">
            <span className="dl-card-icon" aria-hidden>
              <MonitorIcon />
            </span>
            <p className="downloads-kicker">Admin · HR · Partners</p>
          </div>
          <h3>Manager Desktop App</h3>
          <p className="muted">
            Windows app for Dashboard, Employees, Payments, and Expenses. Opens like a native app (no
            browser bar). Same login as the website.
          </p>
          <ol className="downloads-steps">
            <li>
              <span className="dl-step-num">1</span>
              <span>Download Setup (.exe) — recommended.</span>
            </li>
            <li>
              <span className="dl-step-num">2</span>
              <span>
                Open <strong>CFS Designers</strong> from Start Menu.
              </span>
            </li>
            <li>
              <span className="dl-step-num">3</span>
              <span>Sign in with your office email.</span>
            </li>
          </ol>
          <div className="downloads-btn-row">
            <button
              type="button"
              className="downloads-btn"
              disabled={downloading}
              onClick={() => startDownload(MANAGER_SETUP, "Manager Setup (.exe)")}
            >
              <DownloadIcon /> Download Setup (.exe)
            </button>
          </div>
          <p className="muted downloads-hint">
            Setup.exe installs the Manager desktop app. Requires Windows WebView2 (usually already installed).
          </p>
        </article>

        <article className="card downloads-card">
          <div className="dl-card-head">
            <span className="dl-card-icon" aria-hidden>
              <ChipIcon />
            </span>
            <p className="downloads-kicker downloads-kicker-muted">Employees · Office PCs</p>
          </div>
          <h3>Employee Agent</h3>
          <p className="muted">
            Tracking app for CAD PCs — Sign In / Out and screenshots. Install yourself; Admin sends a
            one-time enroll code.
          </p>
          <ol className="downloads-steps">
            <li>
              <span className="dl-step-num">1</span>
              <span>Download the zip (~50 MB).</span>
            </li>
            <li>
              <span className="dl-step-num">2</span>
              <span>
                Right-click → <strong>Extract All</strong> (do not run .bat inside WinRAR).
              </span>
            </li>
            <li>
              <span className="dl-step-num">3</span>
              <span>
                Open the folder and double-click <code>INSTALL-AGENT.bat</code>.
              </span>
            </li>
            <li>
              <span className="dl-step-num">4</span>
              <span>Admin enrolls the PC and sends a code — paste it, then Sign In.</span>
            </li>
          </ol>
          <div className="downloads-btn-row">
            <button
              type="button"
              className="downloads-btn downloads-btn-secondary"
              disabled={downloading}
              onClick={() => startDownload(AGENT_ZIP, "Employee Agent (.zip)")}
            >
              <DownloadIcon /> Download Agent (.zip)
            </button>
          </div>
          <p className="muted downloads-hint">One enroll code per PC · Admin generates codes</p>
        </article>
      </div>

      <article className="card downloads-security">
        <div className="dl-sec-head">
          <span className="dl-sec-icon" aria-hidden>
            <ShieldIcon />
          </span>
          <div>
            <h3>Security</h3>
            <span className="dl-sec-badge">Enroll codes</span>
          </div>
        </div>
        <p className="muted" style={{ marginBottom: 0 }}>
          Anyone with the zip still needs an Admin enroll code before attendance or screenshots can
          upload. Codes are one-time and tied to one PC.
        </p>
      </article>
    </div>
  );
}
