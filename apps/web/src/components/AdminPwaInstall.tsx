import { useCallback, useEffect, useState } from "react";

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
};

const DISMISS_KEY = "ems_pwa_install_dismissed";

/** Install banner + SW — Admin and HR only (never manager, employee, demo). */
function isAdminOrHr(): boolean {
  const r = localStorage.getItem("ems_role") || "";
  return r === "admin" || r === "hr";
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
    if (!isAdminOrHr() || isStandalone()) return;
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

  if (!isAdminOrHr() || installed || dismissed) return null;
  // Show on mobile always (tip), or when browser offers Install
  if (!deferred && !iosTip && !isMobileUa()) return null;

  return (
    <div className="pwa-install-bar" role="status">
      <div className="pwa-install-text">
        <strong>Install Admin / HR app (phone)</strong>
        <span>
          {deferred
            ? "Add CFS EMS to your home screen — Live, Day, Projects (Admin/HR only). Not for employees or Sign In."
            : iosTip
              ? "iPhone Safari: Share → Add to Home Screen. Production HTTPS, logged in as Admin or HR."
              : "Android Chrome: menu (⋮) → Install app. Open https://ems.cfsdesigners.com as Admin or HR."}
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

/** Register SW only for Admin / HR after login (phone home-screen app). */
export function registerAdminServiceWorker(): void {
  if (typeof window === "undefined" || !("serviceWorker" in navigator)) return;
  if (!isAdminOrHr()) return;
  ensureManifestLink(true);
  window.setTimeout(() => {
    navigator.serviceWorker.register("/sw.js").catch(() => undefined);
  }, 2000);
}

/**
 * Staff / Manager must not get Chrome “Install app / Open in app” (phone PWA).
 * Desktop install is Setup.exe from Downloads — Agent is the punch app.
 */
export function blockStaffPwaInstall(): void {
  if (typeof window === "undefined") return;
  ensureManifestLink(false);
  if ("serviceWorker" in navigator) {
    void navigator.serviceWorker.getRegistrations().then((regs) => {
      for (const r of regs) void r.unregister();
    });
  }
}

function ensureManifestLink(allow: boolean): void {
  try {
    const existing = document.querySelector('link[rel="manifest"]');
    if (!allow) {
      existing?.remove();
      document.querySelector('meta[name="mobile-web-app-capable"]')?.remove();
      document.querySelector('meta[name="apple-mobile-web-app-capable"]')?.remove();
      document.querySelector('meta[name="apple-mobile-web-app-title"]')?.remove();
      return;
    }
    if (!existing) {
      const link = document.createElement("link");
      link.rel = "manifest";
      link.href = "/manifest.webmanifest";
      document.head.appendChild(link);
    }
    const ensureMeta = (name: string, content: string) => {
      let m = document.querySelector(`meta[name="${name}"]`);
      if (!m) {
        m = document.createElement("meta");
        m.setAttribute("name", name);
        document.head.appendChild(m);
      }
      m.setAttribute("content", content);
    };
    ensureMeta("mobile-web-app-capable", "yes");
    ensureMeta("apple-mobile-web-app-capable", "yes");
    ensureMeta("apple-mobile-web-app-title", "CFS EMS");
  } catch {
    /* ignore */
  }
}
