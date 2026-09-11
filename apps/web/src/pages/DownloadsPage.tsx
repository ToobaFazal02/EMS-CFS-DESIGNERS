import { useRef, useState } from "react";
import { useToast } from "../components/ToastProvider";

const MANAGER_SETUP = "/downloads/CFS-Designers-Manager-Setup.exe";
const MANAGER_MSI = "/downloads/CFS-Designers-Manager.msi";
const AGENT_ZIP = "/downloads/CFS-Agent-Install.zip";

type ProgressState = { label: string; pct: number } | null;

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

function fileNameFromUrl(url: string) {
  try {
    return decodeURIComponent(url.split("/").pop() || "download");
  } catch {
    return "download";
  }
}

/**
 * Downloads hub — login required (office + staff).
 * Enroll code still required for Agent (security).
 */
export function DownloadsPage() {
  const toast = useToast();
  const [progress, setProgress] = useState<ProgressState>(null);
  const busyRef = useRef(false);

  async function startDownload(url: string, label: string) {
    if (busyRef.current) return;
    busyRef.current = true;
    setProgress({ label, pct: 0 });
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) {
        toast.error(`${label} is not available yet. Ask admin to upload the file.`);
        setProgress(null);
        return;
      }
      const total = Number(res.headers.get("Content-Length") || 0);
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
          const pct = total > 0 ? Math.min(100, Math.round((received / total) * 100)) : Math.min(99, Math.round(received / 1024 / 50));
          setProgress({ label, pct });
        }
      }
      setProgress({ label, pct: 100 });
      const blob = new Blob(chunks as BlobPart[]);
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = objectUrl;
      a.download = fileNameFromUrl(url);
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(objectUrl);
      toast.success(`${label} downloaded (${Math.round(received / 1024 / 1024) || 1} MB).`);
      window.setTimeout(() => setProgress(null), 1200);
    } catch {
      toast.error(`Could not download ${label}. Check your connection.`);
      setProgress(null);
    } finally {
      busyRef.current = false;
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
        <div className="dl-progress card" role="status" aria-live="polite">
          <div className="dl-progress-top">
            <strong>{progress.label}</strong>
            <span>{progress.pct}%</span>
          </div>
          <div className="dl-progress-track" aria-hidden>
            <i className="dl-progress-bar" style={{ width: `${progress.pct}%` }} />
          </div>
          <p className="muted dl-progress-cap">
            {progress.pct < 100 ? "Downloading… please wait" : "Saving file…"}
          </p>
        </div>
      ) : null}

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
            <button
              type="button"
              className="downloads-btn downloads-btn-secondary"
              disabled={downloading}
              onClick={() => startDownload(MANAGER_MSI, "Manager MSI")}
            >
              <DownloadIcon /> Download MSI
            </button>
          </div>
          <p className="muted downloads-hint">
            Setup.exe = easy double-click installer. MSI = IT / Group Policy install. Same app.
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
              <span>Download the zip.</span>
            </li>
            <li>
              <span className="dl-step-num">2</span>
              <span>
                Extract and run <code>INSTALL-AGENT.bat</code>.
              </span>
            </li>
            <li>
              <span className="dl-step-num">3</span>
              <span>Admin enrolls the PC and sends a code.</span>
            </li>
            <li>
              <span className="dl-step-num">4</span>
              <span>Paste the code, then Sign In at work.</span>
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
