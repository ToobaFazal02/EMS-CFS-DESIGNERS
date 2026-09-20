import { useCallback, useEffect, useState } from "react";

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
};

function isOfficeRole(): boolean {
  const r = localStorage.getItem("ems_role") || "";
  return r === "admin" || r === "manager" || r === "hr";
}

function isStandalone(): boolean {
  try {
    if (window.matchMedia("(display-mode: standalone)").matches) return true;
    // iOS
    const nav = window.navigator as Navigator & { standalone?: boolean };
    return Boolean(nav.standalone);
  } catch {
    return false;
  }
}

/**
 * Phase D — Admin-only PWA install (MDN beforeinstallprompt pattern).
 * Hidden for employees so phone never becomes a fake Agent.
 */
export function AdminPwaInstall() {
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null);
  const [installed, setInstalled] = useState(isStandalone());
  const [iosTip, setIosTip] = useState(false);

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

  if (!isOfficeRole() || installed) return null;
  if (!deferred && !iosTip) return null;

  return (
    <div className="pwa-install-bar" role="status">
      <div className="pwa-install-text">
        <strong>Install Admin app</strong>
        <span>
          {deferred
            ? "Add CFS EMS to your home screen for Live / Day / Projects (office only)."
            : "iPhone: Share → Add to Home Screen. Employee Sign In stays on the PC Agent."}
        </span>
      </div>
      {deferred ? (
        <button type="button" className="pwa-install-btn" onClick={() => void install()}>
          Install
        </button>
      ) : null}
    </div>
  );
}

/** Register SW only for office roles after login (admin PWA). */
export function registerAdminServiceWorker(): void {
  if (typeof window === "undefined" || !("serviceWorker" in navigator)) return;
  if (!isOfficeRole()) return;
  // Defer so login paint isn't blocked
  window.setTimeout(() => {
    navigator.serviceWorker.register("/sw.js").catch(() => undefined);
  }, 2000);
}
