import { useEffect, useState } from "react";
import { resolveUrl } from "../api";
import { isTauriDesktop, MANAGER_APP_VERSION, versionGt } from "../version";

type UpdateInfo = {
  latest: string;
  url: string;
};

type Phase = "idle" | "updating" | "error";

/**
 * Manager Desktop only: "Update available" → click installs Setup.exe silently (/S).
 * Server data untouched. Requires Tauri command `start_silent_manager_update`.
 */
export function ManagerUpdateBanner() {
  const [info, setInfo] = useState<UpdateInfo | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!isTauriDesktop()) return;
    let cancelled = false;
    const t = window.setTimeout(async () => {
      try {
        const r = await fetch(resolveUrl("/api/v1/agent/version"), { cache: "no-store" });
        if (!r.ok || cancelled) return;
        const data = await r.json();
        const latest = String(data?.manager_version || "").trim();
        const url = String(
          data?.manager_download_url ||
            "https://ems.cfsdesigners.com/downloads/CFS-Designers-Manager-Setup.exe"
        ).trim();
        if (latest && versionGt(latest, MANAGER_APP_VERSION)) {
          setInfo({ latest, url });
        }
      } catch {
        /* offline — skip */
      }
    }, 4000);
    return () => {
      cancelled = true;
      window.clearTimeout(t);
    };
  }, []);

  async function onUpdateClick() {
    if (!info || phase === "updating") return;
    setPhase("updating");
    setErr("");
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("start_silent_manager_update", { url: info.url });
      // App exits on success — if we are still here, show status briefly
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e || "Update failed");
      setErr(msg);
      setPhase("error");
      // Fallback: open download via Tauri (WebView2 window.open is unreliable)
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        await invoke("open_external_url", { url: info.url });
      } catch {
        try {
          window.open(info.url, "_blank", "noopener,noreferrer");
        } catch {
          /* ignore */
        }
      }
    }
  }

  if (!info) return null;

  return (
    <div className="app-update-banner" role="status">
      <div className="app-update-banner-text">
        <strong>
          {phase === "updating" ? "Updating Manager…" : `Update available: v${info.latest}`}
        </strong>
        <span>
          {phase === "updating"
            ? "Downloading and installing in the background. App will restart. Server data stays safe."
            : phase === "error"
              ? `Could not auto-install (${err}). Opening manual download…`
              : `You have v${MANAGER_APP_VERSION}. Click Update — installs in the background.`}
        </span>
      </div>
      <button
        type="button"
        className="app-update-banner-btn"
        onClick={onUpdateClick}
        disabled={phase === "updating"}
      >
        {phase === "updating" ? "Updating…" : `Update to v${info.latest}`}
      </button>
    </div>
  );
}
