import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  fetchAuthedBlob,
  fetchDay,
  fetchMyAttendance,
  triggerBlobDownload,
  type DaySummary,
  type MeAttendance,
} from "../api";
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
 * Employee home — own performance + attendance (client: staff can track attendance
 * and view/download their monthly PDF). Same React = web + Manager Desktop.
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
  const [busy, setBusy] = useState(false);
  const [pdfPreview, setPdfPreview] = useState<{ url: string; title: string } | null>(null);

  async function load(notify = false) {
    if (!myId) return;
    setBusy(true);
    try {
      const today = todayPktISO();
      const [d, a] = await Promise.all([
        fetchDay(myId, today),
        fetchMyAttendance(year, month),
      ]);
      setDay(d);
      setAtt(a);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Could not load your dashboard.";
      if (notify) toast.error(msg);
      else toast.error(msg);
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
      title: `My monthly PDF — ${month}/${year}`,
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
    triggerBlobDownload(res.blob, `monthly_${code}_${year}_${String(month).padStart(2, "0")}.pdf`);
  }

  const weekDays = (att?.days || []).slice(-7);
  const monthLabel = new Date(year, month - 1, 1).toLocaleString("en", { month: "long", year: "numeric" });

  return (
    <div>
      <div className="toolbar">
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0 }}>My dashboard</h2>
          <p className="muted page-sub" style={{ margin: "4px 0 0" }}>
            {myName}
            {att?.employee_code ? ` · #${att.employee_code}` : ""} — your attendance & performance (PKT)
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
              Open My Day →
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
        <article className="dash-stat dash-stat-warn">
          <p className="dash-stat-kicker">This month · net</p>
          <p className="dash-stat-num">{formatHours(att?.net_hours ?? 0)} h</p>
          <p className="dash-stat-cap">Break {formatHours(att?.break_hours ?? 0)} h</p>
        </article>
      </div>

      <div className="dash-panels" style={{ marginBottom: 16 }}>
        <article className="card dash-panel">
          <div className="dash-panel-head">
            <div>
              <h3>Track attendance</h3>
              <p className="muted page-sub">Pick a month — hours per day (PKT)</p>
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <select
                aria-label="Year"
                value={year}
                onChange={(e) => setYear(Number(e.target.value))}
              >
                {[nowYm.year, nowYm.year - 1].map((y) => (
                  <option key={y} value={y}>
                    {y}
                  </option>
                ))}
              </select>
              <select
                aria-label="Month"
                value={month}
                onChange={(e) => setMonth(Number(e.target.value))}
              >
                {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                  <option key={m} value={m}>
                    {new Date(2000, m - 1, 1).toLocaleString("en", { month: "short" })}
                  </option>
                ))}
              </select>
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
          {weekDays.length ? (
            <p className="muted" style={{ marginTop: 12, marginBottom: 0, fontSize: 13 }}>
              Last days in view:{" "}
              {weekDays.map((d) => `${d.label} ${formatHours(d.net_hours)}h`).join(" · ")}
            </p>
          ) : null}
        </article>

        <article className="card dash-panel">
          <div className="dash-panel-head">
            <div>
              <h3>My monthly PDF</h3>
              <p className="muted page-sub">Your performance summary for the selected month</p>
            </div>
          </div>
          <p className="muted" style={{ marginTop: 0 }}>
            Same month as the table ({monthLabel}). View in-app or download — managers still use team
            Reports.
          </p>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button type="button" className="secondary" onClick={viewMonthlyPdf}>
              View PDF
            </button>
            <button type="button" onClick={downloadMonthlyPdf}>
              Download PDF
            </button>
            <Link to="/projects" style={{ alignSelf: "center" }}>
              My Projects →
            </Link>
          </div>
        </article>
      </div>

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
