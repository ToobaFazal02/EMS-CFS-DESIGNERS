/** Client 31 Aug 2026: show hours as 8.1 / 8.2, not minutes-first. */
export function formatHours(hours: number | string | null | undefined): string {
  const n = Number(hours);
  if (!Number.isFinite(n) || n === 0) return "0.0";
  return n.toFixed(1);
}

export function formatHoursLabel(hours: number | string | null | undefined): string {
  return `${formatHours(hours)} h`;
}

export function formatMinutesAsHours(minutes: number | string | null | undefined): string {
  return formatHoursLabel((Number(minutes) || 0) / 60);
}
