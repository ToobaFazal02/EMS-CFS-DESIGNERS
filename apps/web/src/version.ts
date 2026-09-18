/** Bump with every Manager Setup.exe release (keep in sync with tauri.conf.json + API). */
export const MANAGER_APP_VERSION = "0.1.5";

/** Shown in web + desktop footer (same React shell). */
export const WEB_APP_VERSION = MANAGER_APP_VERSION;

export function isTauriDesktop(): boolean {
  try {
    return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
  } catch {
    return false;
  }
}

/** Semver-ish compare: true if a > b */
export function versionGt(a: string, b: string): boolean {
  const pa = a
    .trim()
    .split(".")
    .map((x) => parseInt(x.replace(/\D/g, ""), 10) || 0);
  const pb = b
    .trim()
    .split(".")
    .map((x) => parseInt(x.replace(/\D/g, ""), 10) || 0);
  const n = Math.max(pa.length, pb.length);
  for (let i = 0; i < n; i++) {
    const x = pa[i] ?? 0;
    const y = pb[i] ?? 0;
    if (x > y) return true;
    if (x < y) return false;
  }
  return false;
}
