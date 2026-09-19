import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  fetchAuthedBlob,
  fetchDay,
  fetchMyAttendance,
  fetchProjectProgress,
  fetchProjects,
  postProjectProgress,
  triggerBlobDownload,
  type DaySummary,
  type MeAttendance,
  type MeAttendanceDay,
  type ProjectProgressRow,
  type ProjectRow,
} from "../api";
import { Sparkline, StaffHoursBars } from "../components/DashCharts";
import { PdfPreviewModal } from "../components/PdfPreviewModal";
import { RefreshButton } from "../components/RefreshButton";
import { useToast } from "../components/ToastProvider";

const DAY_TARGET_H = 8;

function todayPktISO(): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Karachi",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
}

function pktYearMonth(): { year: number; month: number } {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Karachi",
    year: "numeric",
    month: "numeric",
  }).formatToParts(new Date());
  return {
    year: Number(parts.find((p) => p.type === "year")?.value),
    month: Number(parts.find((p) => p.type === "month")?.value),
  };
}

function isFutureMonth(year: number, month: number): boolean {
  const now = pktYearMonth();
  return year > now.year || (year === now.year && month > now.month);
}

function formatHm(hours: number): string {
  const n = Math.max(0, Number(hours) || 0);
  const h = Math.floor(n);
  const m = Math.round((n - h) * 60);
  if (h === 0 && m === 0) return "0h";
  if (m === 0) return `${h}h`;
  if (h === 0) return `${m}m`;
  return `${h}h ${String(m).padStart(2, "0")}m`;
}

function weekdayCount(year: number, month: number): number {
  const last = new Date(year, month, 0).getDate();
  let n = 0;
  for (let d = 1; d <= last; d++) {
    const wd = new Date(year, month - 1, d).getDay();
    if (wd !== 0 && wd !== 6) n += 1;
  }
  return n;
}

function dayStatus(row: MeAttendanceDay): { key: string; label: string } {
  try {
    const d = new Date(`${row.date}T12:00:00`);
    const wd = d.getDay();
    if (wd === 0 || wd === 6) {
      if (row.present && row.net_hours > 0.01) return { key: "present", label: "Present" };
      return { key: "weekend", label: "Weekend" };
    }
  } catch {
    /* ignore */
  }
  if (!row.present || row.net_hours < 0.01) return { key: "off", label: "Off" };
  if (row.net_hours < 4) return { key: "half", label: "Half day" };
  return { key: "present", label: "Present" };
}

function niceDate(iso: string): string {
  try {
    return new Date(`${iso}T12:00:00`).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

type ProjDelta = { prev: number | null; latest: number; delta: number | null; when: string };

const HIDDEN_PROJECTS_KEY = "ems_staff_hidden_projects";

function readHiddenProjectIds(): Set<string> {
  try {
    const raw = localStorage.getItem(HIDDEN_PROJECTS_KEY);
    const arr = raw ? (JSON.parse(raw) as unknown) : [];
    return new Set(Array.isArray(arr) ? arr.map(String) : []);
  } catch {
    return new Set();
  }
}

function writeHiddenProjectIds(ids: Set<string>) {
  localStorage.setItem(HIDDEN_PROJECTS_KEY, JSON.stringify([...ids]));
}

function projectIsFinished(p: ProjectRow, latestPct?: number | null): boolean {
  const ws = (p.work_state || "").toLowerCase();
  if (ws === "done" || ws === "completed" || ws === "closed") return true;
  const pct = latestPct != null ? Number(latestPct) : p.latest_progress_pct;
  return pct != null && Number(pct) >= 100;
}

/**
 * Staff home — Lovable-inspired CFS dark/gold UX (web + Desktop same React).
 */
export function StaffHomePage() {
  const toast = useToast();
  const myId = localStorage.getItem("ems_employee_id") || "";
  const myName = localStorage.getItem("ems_name") || "Staff";
  const nowYm = useMemo(() => pktYearMonth(), []);
  const [year, setYear] = useState(nowYm.year);
  const [month, setMonth] = useState(nowYm.month);
  const [day, setDay] = useState<DaySummary | null>(null);
  const [att, setAtt] = useState<MeAttendance | null>(null);
  const [projects, setProjects] = useState<ProjectRow[]>([]);
  const [hiddenIds, setHiddenIds] = useState<Set<string>>(() => readHiddenProjectIds());
  const [deltas, setDeltas] = useState<Record<string, ProjDelta>>({});
  const [busy, setBusy] = useState(false);
  const [pdfPreview, setPdfPreview] = useState<{ url: string; title: string } | null>(null);

  const [progProject, setProgProject] = useState("");
  const [progPct, setProgPct] = useState(50);
  const [progNote, setProgNote] = useState("");
  const [savingProg, setSavingProg] = useState(false);

  async function load(notify = false) {
    if (!myId) return;
    setBusy(true);
    try {
      const today = todayPktISO();
      const [d, a, projs] = await Promise.all([
        fetchDay(myId, today),
        fetchMyAttendance(year, month),
        fetchProjects(),
      ]);
      setDay(d);
      setAtt(a);
      const hidden = readHiddenProjectIds();
      setHiddenIds(hidden);
      const mine = (projs || []).filter((p) => {
        if (hidden.has(p.id)) return false;
        if (projectIsFinished(p)) return false;
        return true;
      });
      setProjects(mine);
      setProgProject((cur) => {
        if (cur && mine.some((p) => p.id === cur)) return cur;
        const id0 = mine[0]?.id || "";
        if (mine[0]?.latest_progress_pct != null) {
          setProgPct(Number(mine[0].latest_progress_pct));
        }
        return id0;
      });

      const nextDeltas: Record<string, ProjDelta> = {};
      await Promise.all(
        mine.slice(0, 12).map(async (p) => {
          try {
            const hist: ProjectProgressRow[] = await fetchProjectProgress(p.id);
            const mineRows = hist.filter((r) => r.employee_id === myId);
            const latest = mineRows[0];
            const prev = mineRows[1];
            const latestPct = latest ? Number(latest.percent) : p.latest_progress_pct ?? 0;
            const prevPct = prev ? Number(prev.percent) : null;
            nextDeltas[p.id] = {
              prev: prevPct,
              latest: latestPct,
              delta: prevPct != null ? latestPct - prevPct : null,
              when: latest?.work_date || "",
            };
          } catch {
            nextDeltas[p.id] = {
              prev: null,
              latest: p.latest_progress_pct ?? 0,
              delta: null,
              when: "",
            };
          }
        })
      );
      setDeltas(nextDeltas);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Could not load your dashboard.";
      if (notify || !att) toast.error(msg);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    load(false);
    const t = setInterval(() => load(false), 30000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [myId, year, month]);

  async function viewMonthlyPdf() {
    if (isFutureMonth(year, month)) {
      toast.error("Future months are not allowed.");
      return;
    }
    const res = await fetchAuthedBlob(
      `/api/v1/me/monthly.pdf?year=${year}&month=${month}&inline=1&v=${Date.now()}`
    );
    if ("error" in res) {
      toast.error(res.error);
      return;
    }
    if (pdfPreview?.url) URL.revokeObjectURL(pdfPreview.url);
    setPdfPreview({
      url: URL.createObjectURL(res.blob),
      title: `My monthly report — ${month}/${year}`,
    });
  }

  async function downloadMonthlyPdf() {
    if (isFutureMonth(year, month)) {
      toast.error("Future months are not allowed.");
      return;
    }
    const res = await fetchAuthedBlob(`/api/v1/me/monthly.pdf?year=${year}&month=${month}&v=${Date.now()}`);
    if ("error" in res) {
      toast.error(res.error);
      return;
    }
    const code = att?.employee_code || "me";
    triggerBlobDownload(
      res.blob,
      `CFS_Monthly_Report_${code}_${year}_${String(month).padStart(2, "0")}.pdf`
    );
  }

  async function saveProgress() {
    if (!progProject) {
      toast.error("Pick a project first.");
      return;
    }
    if (!Number.isFinite(progPct) || progPct < 0 || progPct > 100) {
      toast.error("Percent must be 0–100.");
      return;
    }
    setSavingProg(true);
    try {
      await postProjectProgress(progProject, { percent: progPct, note: progNote.trim() });
      if (progPct >= 100) {
        const next = new Set(hiddenIds);
        next.add(progProject);
        writeHiddenProjectIds(next);
        setHiddenIds(next);
        toast.success("Progress saved at 100% — removed from Assigned work.");
      } else {
        toast.success("Progress saved.");
      }
      setProgNote("");
      await load(false);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not save progress.");
    } finally {
      setSavingProg(false);
    }
  }

  function hideProjectFromDashboard(id: string) {
    const next = new Set(hiddenIds);
    next.add(id);
    writeHiddenProjectIds(next);
    setHiddenIds(next);
    setProjects((cur) => {
      const rest = cur.filter((p) => p.id !== id);
      setProgProject((sel) => {
        if (sel !== id) return sel;
        const id0 = rest[0]?.id || "";
        if (rest[0]?.latest_progress_pct != null) setProgPct(Number(rest[0].latest_progress_pct));
        return id0;
      });
      return rest;
    });
    toast.success("Hidden from Assigned work. Still on My Projects.");
  }

  function clearHiddenProjects() {
    writeHiddenProjectIds(new Set());
    setHiddenIds(new Set());
    void load(false);
    toast.success("Hidden jobs restored on this dashboard.");
  }

  const monthLabel = new Date(year, month - 1, 1).toLocaleString("en", { month: "long", year: "numeric" });
  const scheduled = weekdayCount(year, month);
  const present = att?.days_present ?? 0;
  const remaining = Math.max(0, scheduled - present);
  const todayH = day?.net_hours ?? 0;
  const todayPct = Math.min(100, Math.round((todayH / DAY_TARGET_H) * 100));
  const clicks = day?.total_clicks ?? 0;
  const keys = day?.total_keys ?? 0;
  const activityDenom = clicks + keys + Math.max(1, Math.round((day?.idle_minutes || 0) * 10));
  const activeRate = Math.min(100, Math.round(((clicks + keys) / activityDenom) * 100));

  const sparkVals = (att?.days || []).map((d) => d.net_hours);
  // Sensible trend: avg hours on recent present days vs earlier present days (capped).
  const presentHours = (att?.days || []).filter((d) => d.present && d.net_hours > 0.01).map((d) => d.net_hours);
  const recentN = Math.min(5, presentHours.length);
  const recentSlice = presentHours.slice(-recentN);
  const earlierSlice = presentHours.slice(0, Math.max(0, presentHours.length - recentN));
  const avg = (xs: number[]) => (xs.length ? xs.reduce((s, v) => s + v, 0) / xs.length : 0);
  const recentAvg = avg(recentSlice);
  const earlierAvg = avg(earlierSlice);
  let trendLabel = "Not enough days yet";
  let trendValue = "—";
  let trendUp = true;
  if (presentHours.length < 2) {
    trendLabel = presentHours.length === 1 ? "First work days this month" : "No work days yet";
    trendValue = recentAvg > 0 ? formatHm(recentAvg) : "—";
  } else if (earlierAvg < 0.15) {
    trendUp = true;
    trendValue = formatHm(recentAvg);
    trendLabel = "Avg on recent work days";
  } else {
    const raw = ((recentAvg - earlierAvg) / earlierAvg) * 100;
    const capped = Math.max(-99, Math.min(99, Math.round(raw)));
    trendUp = capped >= 0;
    trendValue = `${capped > 0 ? "+" : ""}${capped}%`;
    trendLabel = `vs earlier work days (avg ${formatHm(recentAvg)} lately)`;
  }

  const chartDays = (att?.days || []).map((d) => ({
    label: String(Number(d.date.slice(-2))),
    hours: d.net_hours,
    present: d.present,
  }));

  const recentRows = [...(att?.days || [])].reverse().filter((d) => d.present).slice(0, 12);
  const calendarRows = recentRows.length ? recentRows : [...(att?.days || [])].reverse().slice(0, 10);

  const code = att?.employee_code || "";

  return (
    <div className="staff-home">
      <header className="staff-hero">
        <div>
          <p className="staff-eyebrow">Staff workspace</p>
          <h1 className="staff-title">My dashboard</h1>
          <p className="staff-sub">
            {myName}
            {code ? ` #${code}` : ""} — attendance, performance &amp; project %
          </p>
        </div>
        <RefreshButton busy={busy} onClick={() => load(true)} />
      </header>

      <div className="staff-kpi-row">
        <article className="staff-kpi">
          <p className="staff-kpi-label">Today net hours</p>
          <p className="staff-kpi-value">{formatHm(todayH)}</p>
          <p className="staff-kpi-meta">{DAY_TARGET_H}h target</p>
          <div className="staff-meter" aria-hidden>
            <i style={{ width: `${todayPct}%` }} />
          </div>
        </article>
        <article className="staff-kpi">
          <p className="staff-kpi-label">Today clicks / keys</p>
          <p className="staff-kpi-value staff-kpi-value-sm">
            {clicks.toLocaleString()} <span className="muted">/</span> {keys.toLocaleString()}
          </p>
          <p className="staff-kpi-meta">{activeRate}% activity mix</p>
          <div className="staff-meter" aria-hidden>
            <i style={{ width: `${activeRate}%` }} />
          </div>
        </article>
        <article className="staff-kpi">
          <p className="staff-kpi-label">Month days present</p>
          <p className="staff-kpi-value">
            {present} <span className="staff-kpi-slash">/ {scheduled}</span>
          </p>
          <p className="staff-kpi-meta">
            {remaining} working day{remaining === 1 ? "" : "s"} remaining (weekdays)
          </p>
          <div className="staff-meter" aria-hidden>
            <i style={{ width: `${scheduled ? Math.min(100, Math.round((present / scheduled) * 100)) : 0}%` }} />
          </div>
        </article>
        <article className="staff-kpi">
          <p className="staff-kpi-label">Month trend</p>
          <p className={`staff-kpi-value ${trendUp ? "is-up" : "is-down"}`}>{trendValue}</p>
          <p className="staff-kpi-meta">{trendLabel}</p>
          <div className="staff-kpi-spark">
            <Sparkline
              values={presentHours.length ? presentHours : sparkVals.length ? sparkVals : [0]}
              color={trendUp ? "#4ade80" : "#fb923c"}
            />
          </div>
        </article>
      </div>
      <p className="staff-day-link">
        <Link to={`/day/${myId}`}>Open My Day (daily report) →</Link>
      </p>

      <section className="staff-split card">
        <div className="staff-split-left">
          <p className="staff-eyebrow">Daily update</p>
          <h2 className="staff-section-title">Log today’s project progress</h2>
          {projects.length ? (
            <>
              <div className="field">
                <label htmlFor="staff-prog-project">Project</label>
                <select
                  id="staff-prog-project"
                  value={progProject}
                  onChange={(e) => {
                    setProgProject(e.target.value);
                    const p = projects.find((x) => x.id === e.target.value);
                    if (p?.latest_progress_pct != null) setProgPct(Number(p.latest_progress_pct));
                  }}
                >
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {(p.code || "").trim() ? `${p.code} · ` : ""}
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <div className="staff-slider-head">
                  <label htmlFor="staff-prog-pct">My % today</label>
                  <span className="staff-pct-pill">{progPct} %</span>
                </div>
                <input
                  id="staff-prog-pct"
                  className="staff-range"
                  type="range"
                  min={0}
                  max={100}
                  step={1}
                  value={progPct}
                  style={{ ["--fill" as string]: `${progPct}%` }}
                  onChange={(e) => setProgPct(Number(e.target.value))}
                />
              </div>
              <div className="field">
                <label htmlFor="staff-prog-note">Optional note</label>
                <textarea
                  id="staff-prog-note"
                  className="staff-note"
                  rows={3}
                  value={progNote}
                  onChange={(e) => setProgNote(e.target.value)}
                  placeholder="What you finished today…"
                />
              </div>
              <button type="button" className="staff-save-btn" disabled={savingProg} onClick={saveProgress}>
                {savingProg ? "Saving…" : "Save my progress"}
              </button>
            </>
          ) : (
            <p className="muted">No open projects assigned yet. When you are Detailer or Engineer on a job, it appears here.</p>
          )}
        </div>
        <div className="staff-split-right">
          <div className="staff-split-right-head">
            <div>
              <p className="staff-eyebrow">Assigned work</p>
              <h2 className="staff-section-title">Open jobs</h2>
            </div>
            <span className="staff-active-pill">{projects.length} active</span>
          </div>
          <ul className="staff-job-list">
            {projects.map((p) => {
              const dlt = deltas[p.id];
              const pct = Math.min(100, Math.max(0, dlt?.latest ?? p.latest_progress_pct ?? 0));
              const delta = dlt?.delta;
              const barPct = pct >= 99.5 ? 100 : pct;
              return (
                <li key={p.id}>
                  <div className="staff-job-top">
                    <div>
                      <strong>{p.name}</strong>
                      <p className="muted">
                        {p.code ? `${p.code} · ` : ""}
                        {dlt?.when ? `Updated ${dlt.when}` : "No % logged yet"}
                      </p>
                    </div>
                    <div className="staff-job-actions">
                      <em>{Math.round(pct)}%</em>
                      <button
                        type="button"
                        className="staff-hide-btn"
                        title="Hide from Assigned work"
                        onClick={() => hideProjectFromDashboard(p.id)}
                      >
                        Hide
                      </button>
                    </div>
                  </div>
                  <div className="staff-proj-bar" aria-hidden>
                    <i style={{ width: `${barPct}%` }} />
                  </div>
                  <p className={`staff-delta${delta != null && delta > 0 ? " is-up" : ""}`}>
                    {delta != null && dlt?.prev != null
                      ? `${dlt.prev}% → ${Math.round(pct)}% = ${delta >= 0 ? "+" : ""}${delta}% last change`
                      : "No change in latest update"}
                  </p>
                </li>
              );
            })}
            {!projects.length ? (
              <li className="muted">No open jobs on this dashboard. Finished (100%) and hidden jobs stay on My Projects.</li>
            ) : null}
          </ul>
          {hiddenIds.size > 0 ? (
            <button type="button" className="staff-restore-btn" onClick={clearHiddenProjects}>
              Restore {hiddenIds.size} hidden job{hiddenIds.size === 1 ? "" : "s"}
            </button>
          ) : null}
          <Link className="staff-inline-link" to="/projects">
            All my projects →
          </Link>
        </div>
      </section>

      <section className="card staff-panel">
        <div className="staff-panel-head">
          <div>
            <p className="staff-eyebrow">Attendance analysis</p>
            <h2 className="staff-section-title">Hours this month</h2>
          </div>
          <div className="staff-month-pick">
            <select aria-label="Month" value={month} onChange={(e) => setMonth(Number(e.target.value))}>
              {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                <option key={m} value={m}>
                  {new Date(2000, m - 1, 1).toLocaleString("en", { month: "long" })}
                </option>
              ))}
            </select>
            <select aria-label="Year" value={year} onChange={(e) => setYear(Number(e.target.value))}>
              {[nowYm.year, nowYm.year - 1].map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </div>
        </div>
        <StaffHoursBars days={chartDays} />
        <p className="muted staff-chart-cap">
          {monthLabel}: <strong>{formatHm(att?.net_hours ?? 0)}</strong> net · Break {formatHm(att?.break_hours ?? 0)} ·{" "}
          {present} days present
        </p>
      </section>

      <section className="card staff-panel staff-report-panel">
        <div className="staff-report-head">
          <div>
            <p className="staff-eyebrow">{monthLabel}</p>
            <h2 className="staff-section-title">My monthly report</h2>
            <p className="muted">
              Personal day-by-day attendance and activity PDF for the selected month. Sessions and screenshots are on My
              Day.
            </p>
          </div>
          <div className="staff-report-actions">
            <button type="button" className="staff-btn-ghost" onClick={viewMonthlyPdf}>
              View PDF
            </button>
            <button type="button" className="staff-btn-gold" onClick={downloadMonthlyPdf}>
              Download PDF
            </button>
          </div>
        </div>
      </section>

      <section className="card staff-panel">
        <p className="staff-eyebrow">Recent records</p>
        <h2 className="staff-section-title">Attendance calendar</h2>
        <div className="staff-table-wrap">
          <table className="staff-att-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Net hours</th>
                <th>Status</th>
                <th aria-label="Open" />
              </tr>
            </thead>
            <tbody>
              {calendarRows.map((row) => {
                const st = dayStatus(row);
                return (
                  <tr key={row.date}>
                    <td>
                      <Link to={`/day/${myId}?date=${row.date}`}>{niceDate(row.date)}</Link>
                    </td>
                    <td className="num">{formatHm(row.net_hours)}</td>
                    <td>
                      <span className={`staff-badge staff-badge-${st.key}`}>{st.label}</span>
                    </td>
                    <td className="chev">
                      <Link to={`/day/${myId}?date=${row.date}`} aria-label={`Open ${row.date}`}>
                        →
                      </Link>
                    </td>
                  </tr>
                );
              })}
              {!calendarRows.length ? (
                <tr>
                  <td colSpan={4} className="muted">
                    No attendance rows this month yet.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <PdfPreviewModal
        open={Boolean(pdfPreview)}
        title={pdfPreview?.title || "PDF"}
        blobUrl={pdfPreview?.url || null}
        onClose={() => {
          if (pdfPreview?.url) URL.revokeObjectURL(pdfPreview.url);
          setPdfPreview(null);
        }}
      />
    </div>
  );
}
