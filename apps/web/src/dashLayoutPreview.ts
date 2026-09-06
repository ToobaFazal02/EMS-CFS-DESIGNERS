/** Layout-only numbers. Vite production builds compile this to always-false. */

export function isLocalDashPreview(): boolean {
  // Opt-in only — never fake KPIs for HR / demo / normal local use
  if (import.meta.env.PROD) return false;
  if (typeof window === "undefined") return false;
  return localStorage.getItem("ems_dash_preview") === "1";
}

export const PREVIEW_HOURS_THIS = [7.6, 8.1, 8.4, 7.9, 8.2, 3.1, 0];
export const PREVIEW_HOURS_LAST = [7.2, 8.0, 7.8, 8.3, 7.5, 4.0, 0.5];

const DAY = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function previewHourDays(hours: number[]) {
  return DAY.map((label, i) => ({ date: "", label, hours: hours[i] || 0 }));
}

export const PREVIEW_SPARK = {
  live: [3.2, 5.1, 4.4, 6.8, 7.2, 5.9, 8.1],
  brk: [1.2, 2.8, 4.1, 2.2, 3.6, 1.8, 2.4],
  off: [6.1, 4.2, 5.5, 3.1, 2.4, 4.8, 3.6],
  jobs: [4.0, 4.4, 5.1, 6.2, 5.8, 7.0, 6.4],
  cash: [2.1, 3.4, 4.0, 5.6, 4.8, 6.2, 5.4],
};
