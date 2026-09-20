import { useCallback, useEffect, useState } from "react";

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
};

const DISMISS_KEY = "ems_pwa_install_dismissed";

function isOfficeRole(): boolean {
  const r = localStorage.getItem("ems_role") || "";
  return r === "admin" || r === "manager" || r === "hr";
}

function isStandalone(): boolean {
  try {
    if (window.matchMedia("(display-mode: standalone)").matches) return true;
    const nav = window.navigator as Navigator & { standalone?: boolean };
    return Boolean(nav.standalone);
  } catch {
    return false;
  }
}

function isMobileUa(): boolean {
  return /Android|iPhone|iPad|iPod/i.test(navigator.userAgent || "");
}

/**
 * Phase D — Admin-only PWA install (MDN beforeinstallprompt).
 * Not a Play Store / App Store app — install from Chrome/Safari after Admin login.
 */
export function AdminPwaInstall() {
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null);
  const [installed, setInstalled] = useState(isStandalone());
  const [iosTip, setIosTip] = useState(false);
  const [dismissed, setDismissed] = useState(() => {
    try {
      return localStorage.getItem(DISMISS_KEY) === "1";
    } catch {
      return false;
    }
  });

  useEffect(() => {
    if (!isOfficeRole() || isStandalone()) return;
    function onBip(e: Event) {
      e.preventDefault();
      setDeferred(e as BeforeInstallPromptEvent);
    }
    function onInstalled() {
      setInstalled(true);
      setDeferred(null);
    }
    window.addEventListener("beforeinstallprompt", onBip);
    window.addEventListener("appinstalled", onInstalled);
    const ua = navigator.userAgent || "";
    if (/iPhone|iPad|iPod/i.test(ua)) setIosTip(true);
    return () => {
      window.removeEventListener("beforeinstallprompt", onBip);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  const install = useCallback(async () => {
    if (!deferred) return;
    await deferred.prompt();
    await deferred.userChoice;
    setDeferred(null);
  }, [deferred]);

  function dismiss() {
    try {
      localStorage.setItem(DISMISS_KEY, "1");
    } catch {
      /* ignore */
    }
    setDismissed(true);
  }

  if (!isOfficeRole() || installed || dismissed) return null;
  // Show on mobile always (tip), or when browser offers Install
  if (!deferred && !iosTip && !isMobileUa()) return null;

  return (
    <div className="pwa-install-bar" role="status">
      <div className="pwa-install-text">
        <strong>Install Admin app (phone)</strong>
        <span>
          {deferred
            ? "Add CFS EMS to your home screen — Live, Day, Projects, Payments (office glance). Not for employee Sign In."
            : iosTip
              ? "iPhone Safari: Share → Add to Home Screen. Use production HTTPS URL while logged in as Admin."
              : "Android Chrome: menu (⋮) → Install app / Add to Home screen. Open https://ems.cfsdesigners.com as Admin."}
        </span>
      </div>
      <div className="pwa-install-actions">
        {deferred ? (
          <button type="button" className="pwa-install-btn" onClick={() => void install()}>
            Install
          </button>
        ) : null}
        <button type="button" className="pwa-dismiss-btn" onClick={dismiss} aria-label="Dismiss">
          Not now
        </button>
      </div>
    </div>
  );
}

/** Register SW only for office roles after login (admin PWA). */
export function registerAdminServiceWorker(): void {
  if (typeof window === "undefined" || !("serviceWorker" in navigator)) return;
  if (!isOfficeRole()) return;
  window.setTimeout(() => {
    navigator.serviceWorker.register("/sw.js").catch(() => undefined);
  }, 2000);
}
