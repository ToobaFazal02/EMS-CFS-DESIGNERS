import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  fetchAuthedBlob,
  fetchDay,
  fetchMyAttendance,
  fetchProjects,
  postProjectProgress,
  triggerBlobDownload,
  type DaySummary,
  type MeAttendance,
  type ProjectRow,
} from "../api";
import { Sparkline, StaffHoursBars } from "../components/DashCharts";
import { PdfPreviewModal } from "../components/PdfPreviewModal";
import { RefreshButton } from "../components/RefreshButton";
import { useToast } from "../components/ToastProvider";
import { formatHours } from "../formatHours";

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

/**
 * Employee home — attendance graph, project % log, monthly PDF (day-by-day).
 * Same React = browser + Manager Desktop.
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
  const [busy, setBusy] = useState(false);
  const [pdfPreview, setPdfPreview] = useState<{ url: string; title: string } | null>(null);

  const [progProject, setProgProject] = useState("");
  const [progPct, setProgPct] = useState("50");
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
      const mine = (projs || []).filter((p) => (p.work_state || "") !== "done");
      setProjects(mine);
      setProgProject((cur) => {
        if (cur && mine.some((p) => p.id === cur)) return cur;
        return mine[0]?.id || "";
      });
      if (mine[0]?.latest_progress_pct != null && !progPct) {
        setProgPct(String(mine[0].latest_progress_pct));
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Could not load your dashboard.";
      toast.error(msg);
      if (!notify) {
        /* still toast once on poll errors */
      }
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
    const pct = Number(progPct);
    if (!Number.isFinite(pct) || pct < 0 || pct > 100) {
      toast.error("Percent must be 0–100.");
      return;
    }
    setSavingProg(true);
    try {
      await postProjectProgress(progProject, { percent: pct, note: progNote.trim() });
      toast.success("Progress saved — Admin can see it.");
      setProgNote("");
      await load(false);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not save progress.");
    } finally {
      setSavingProg(false);
    }
  }

  const monthLabel = new Date(year, month - 1, 1).toLocaleString("en", { month: "long", year: "numeric" });
  const chartDays = (att?.days || [])
    .filter((d) => d.present)
    .map((d) => ({ label: d.label.replace(/^\w+\s/, ""), hours: d.net_hours, present: d.present }));
  const sparkVals = (att?.days || []).map((d) => d.net_hours);
  const trendUp =
    sparkVals.length >= 2
      ? sparkVals[sparkVals.length - 1] >= sparkVals[Math.max(0, sparkVals.length - 8)]
      : true;

  const selectedProj = projects.find((p) => p.id === progProject);

  return (
    <div className="staff-home">
      <div className="toolbar">
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0 }}>My dashboard</h2>
          <p className="muted page-sub" style={{ margin: "4px 0 0" }}>
            {myName}
            {att?.employee_code ? ` · #${att.employee_code}` : ""} — attendance, performance & project %
          </p>
        </div>
        <RefreshButton busy={busy} onClick={() => load(true)} />
      </div>

      <div className="dash-stats" style={{ marginBottom: 16 }}>
        <article className="dash-stat dash-stat-gold">
          <p className="dash-stat-kicker">Today · net work</p>
          <p className="dash-stat-num">{formatHours(day?.net_hours ?? 0)} h</p>
          <p className="dash-stat-cap">
            <Link className="dash-stat-link" to={`/day/${myId}`}>
              Open My Day (daily report) →
            </Link>
          </p>
        </article>
        <article className="dash-stat dash-stat-ok">
          <p className="dash-stat-kicker">Today · clicks / keys</p>
          <p className="dash-stat-num">
            {day?.total_clicks ?? 0} / {day?.total_keys ?? 0}
          </p>
          <p className="dash-stat-cap">Activity while signed in</p>
        </article>
        <article className="dash-stat dash-stat-mute">
          <p className="dash-stat-kicker">This month · days</p>
          <p className="dash-stat-num">{att?.days_present ?? 0}</p>
          <p className="dash-stat-cap">{monthLabel}</p>
        </article>
        <article className={`dash-stat ${trendUp ? "dash-stat-ok" : "dash-stat-warn"}`}>
          <p className="dash-stat-kicker">Month trend</p>
          <p className="dash-stat-num" style={{ fontSize: 18 }}>
            {trendUp ? "Up / steady" : "Softer lately"}
          </p>
          <div style={{ marginTop: 6 }}>
            <Sparkline values={sparkVals.length ? sparkVals : [0]} color={trendUp ? "#4ade80" : "#fb923c"} />
          </div>
        </article>
      </div>

      <article className="card dash-panel staff-progress-card" style={{ marginBottom: 16 }}>
        <div className="dash-panel-head">
          <div>
            <h3>Log today’s project progress</h3>
            <p className="muted page-sub">
              End of day: set how complete the job is (e.g. 50% → 60%). Admin sees the same history.
            </p>
          </div>
          <Link to="/projects">All my projects →</Link>
        </div>
        {projects.length ? (
          <div className="staff-progress-form">
            <div className="field">
              <label htmlFor="staff-prog-project">Project</label>
              <select
                id="staff-prog-project"
                value={progProject}
                onChange={(e) => {
                  setProgProject(e.target.value);
                  const p = projects.find((x) => x.id === e.target.value);
                  if (p?.latest_progress_pct != null) setProgPct(String(p.latest_progress_pct));
                }}
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {(p.code || "").trim() ? `${p.code} · ` : ""}
                    {p.name}
                    {p.latest_progress_pct != null ? ` (${p.latest_progress_pct}%)` : ""}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="staff-prog-pct">My % today</label>
              <input
                id="staff-prog-pct"
                type="number"
                min={0}
                max={100}
                step={1}
                value={progPct}
                onChange={(e) => setProgPct(e.target.value)}
              />
            </div>
            <div className="field staff-progress-note">
              <label htmlFor="staff-prog-note">Note</label>
              <input
                id="staff-prog-note"
                value={progNote}
                onChange={(e) => setProgNote(e.target.value)}
                placeholder="Optional — what you finished today"
              />
            </div>
            <button type="button" className="staff-progress-save" disabled={savingProg} onClick={saveProgress}>
              {savingProg ? "Saving…" : "Save my progress"}
            </button>
          </div>
        ) : (
          <p className="muted" style={{ margin: 0 }}>
            No open projects assigned yet. When you are Detailer/Engineer on a job, it appears here.
          </p>
        )}
        {projects.length ? (
          <ul className="staff-proj-list">
            {projects.slice(0, 6).map((p) => {
              const pct = p.latest_progress_pct ?? 0;
              return (
                <li key={p.id}>
                  <div className="staff-proj-meta">
                    <strong>{p.code || "—"}</strong>
                    <span>{p.name}</span>
                    <em>{pct}%</em>
                  </div>
                  <div className="staff-proj-bar" aria-hidden>
                    <i style={{ width: `${Math.min(100, Math.max(0, pct))}%` }} />
                  </div>
                </li>
              );
            })}
          </ul>
        ) : null}
        {selectedProj?.latest_progress_pct != null ? (
          <p className="muted" style={{ marginBottom: 0, fontSize: 13 }}>
            Selected job last logged: <strong>{selectedProj.latest_progress_pct}%</strong>
          </p>
        ) : null}
      </article>

      <div className="dash-panels" style={{ marginBottom: 16 }}>
        <article className="card dash-panel">
          <div className="dash-panel-head">
            <div>
              <h3>Hours this month</h3>
              <p className="muted page-sub">Graph of days you worked · {monthLabel}</p>
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <select aria-label="Year" value={year} onChange={(e) => setYear(Number(e.target.value))}>
                {[nowYm.year, nowYm.year - 1].map((y) => (
                  <option key={y} value={y}>
                    {y}
                  </option>
                ))}
              </select>
              <select aria-label="Month" value={month} onChange={(e) => setMonth(Number(e.target.value))}>
                {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                  <option key={m} value={m}>
                    {new Date(2000, m - 1, 1).toLocaleString("en", { month: "short" })}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <StaffHoursBars days={chartDays.length ? chartDays : (att?.days || []).map((d) => ({ label: d.label, hours: d.net_hours }))} />
          <p className="muted" style={{ marginTop: 10, marginBottom: 0, fontSize: 13 }}>
            Month total: <strong>{formatHours(att?.net_hours ?? 0)} h</strong> · Break{" "}
            {formatHours(att?.break_hours ?? 0)} h · {att?.days_present ?? 0} days present
          </p>
        </article>

        <article className="card dash-panel">
          <div className="dash-panel-head">
            <div>
              <h3>My monthly report (PDF)</h3>
              <p className="muted page-sub">Full month: summary + every day — yours to view & download</p>
            </div>
          </div>
          <p className="muted" style={{ marginTop: 0 }}>
            <strong>You get a full monthly report:</strong> document control, your identity, period
            summary, status legend, every day’s hours, monthly totals, project % logs, and how to read
            it. <strong>Daily detail</strong> (sessions / screenshots) stays on{" "}
            <Link to={`/day/${myId}`}>My Day</Link>. Team-wide Reports remain Admin/Manager only.
          </p>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button type="button" className="secondary" onClick={viewMonthlyPdf}>
              View monthly report
            </button>
            <button type="button" onClick={downloadMonthlyPdf}>
              Download monthly report
            </button>
          </div>
        </article>
      </div>

      <article className="card dash-panel">
        <div className="dash-panel-head">
          <div>
            <h3>Attendance calendar</h3>
            <p className="muted page-sub">Click a day to open that day’s report</p>
          </div>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table className="table-center" style={{ width: "100%", fontSize: 14 }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left" }}>Date</th>
                <th style={{ textAlign: "right" }}>Net hours</th>
                <th style={{ textAlign: "left" }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {(att?.days || []).map((row) => (
                <tr key={row.date}>
                  <td>
                    <Link to={`/day/${myId}?date=${row.date}`}>{row.label}</Link>
                    <span className="muted" style={{ marginLeft: 8, fontSize: 12 }}>
                      {row.date}
                    </span>
                  </td>
                  <td style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                    {formatHours(row.net_hours)}
                  </td>
                  <td>{row.present ? "Present" : "—"}</td>
                </tr>
              ))}
              {!att?.days?.length ? (
                <tr>
                  <td colSpan={3} className="muted">
                    No days in this month yet.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </article>

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
