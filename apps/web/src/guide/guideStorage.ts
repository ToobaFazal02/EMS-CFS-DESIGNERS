const OPENS_KEY = "ems_guide_opens";
const SESSION_KEY = "ems_guide_session";
const DISMISS_KEY = "ems_guide_dismissed";
const SEEN_KEY = "ems_guide_seen";
const MAX_OPENS = 5;

export function registerGuideOpen(): number {
  try {
    if (sessionStorage.getItem(SESSION_KEY)) {
      return Number(localStorage.getItem(OPENS_KEY) || 0);
    }
    sessionStorage.setItem(SESSION_KEY, "1");
    const next = Math.min(MAX_OPENS + 1, (Number(localStorage.getItem(OPENS_KEY)) || 0) + 1);
    localStorage.setItem(OPENS_KEY, String(next));
    return next;
  } catch {
    return MAX_OPENS + 1;
  }
}

export function guidesAllowedThisSession(): boolean {
  try {
    if (sessionStorage.getItem(DISMISS_KEY)) return false;
    const n = registerGuideOpen();
    return n >= 1 && n <= MAX_OPENS;
  } catch {
    return false;
  }
}

export function skipGuidesThisSession() {
  try {
    sessionStorage.setItem(DISMISS_KEY, "1");
  } catch {
    /* ignore */
  }
}

export function resetGuides() {
  try {
    localStorage.removeItem(OPENS_KEY);
    sessionStorage.removeItem(SESSION_KEY);
    sessionStorage.removeItem(DISMISS_KEY);
    sessionStorage.removeItem(SEEN_KEY);
  } catch {
    /* ignore */
  }
}

export function markGuideSeen(pathKey: string) {
  try {
    const raw = sessionStorage.getItem(SEEN_KEY);
    const seen: string[] = raw ? (JSON.parse(raw) as string[]) : [];
    if (!seen.includes(pathKey)) {
      seen.push(pathKey);
      sessionStorage.setItem(SEEN_KEY, JSON.stringify(seen));
    }
  } catch {
    /* ignore */
  }
}

export function wasGuideSeen(pathKey: string): boolean {
  try {
    const raw = sessionStorage.getItem(SEEN_KEY);
    const seen: string[] = raw ? (JSON.parse(raw) as string[]) : [];
    return seen.includes(pathKey);
  } catch {
    return false;
  }
}

export function guidePathKey(pathname: string): string {
  if (pathname.startsWith("/day/")) return "/day";
  return pathname;
}
