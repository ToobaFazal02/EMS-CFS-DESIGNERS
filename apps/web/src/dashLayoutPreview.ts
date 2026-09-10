/** @deprecated Layout-only fake KPIs — disabled. Kept so old imports do not break. */

export function isLocalDashPreview(): boolean {
  return false;
}

export const PREVIEW_HOURS_THIS = [0, 0, 0, 0, 0, 0, 0];
export const PREVIEW_HOURS_LAST = [0, 0, 0, 0, 0, 0, 0];

const DAY = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function previewHourDays(hours: number[]) {
  return DAY.map((label, i) => ({ date: "", label, hours: hours[i] || 0 }));
}

export const PREVIEW_SPARK = {
  live: [0],
  brk: [0],
  off: [0],
  jobs: [0],
  cash: [0],
};
