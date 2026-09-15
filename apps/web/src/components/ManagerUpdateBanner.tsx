import { useEffect, useState } from "react";
import { resolveUrl } from "../api";
import { isTauriDesktop, MANAGER_APP_VERSION, versionGt } from "../version";

type UpdateInfo = {
  latest: string;
  url: string;
};

/**
 * Manager Desktop only: professional "Update available" bar (matches Agent banner pattern).
 * Click opens Manager Setup download — install replaces the app (data on server stays safe).
 */
export function ManagerUpdateBanner() {
  const [info, setInfo] = useState<UpdateInfo | null>(null);

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
          data?.manager_download_url || data?.download_url || "https://ems.cfsdesigners.com/downloads"
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

  if (!info) return null;

  return (
    <div className="app-update-banner" role="status">
      <div className="app-update-banner-text">
        <strong>Update available: v{info.latest}</strong>
        <span>
          You have v{MANAGER_APP_VERSION}. Download and run the new Manager Setup — your data stays on the
          server.
        </span>
      </div>
      <a className="app-update-banner-btn" href={info.url} target="_blank" rel="noopener noreferrer">
        Download v{info.latest}
      </a>
    </div>
  );
}
