import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { Link, useParams } from "react-router-dom";
import { fetchDay, fetchShots } from "../api";
import { AuthedImg } from "../components/AuthedImg";
import { useToast } from "../components/ToastProvider";
import { formatHoursLabel, formatMinutesAsHours } from "../formatHours";

const TZ = "Asia/Karachi";

function todayLocalISO(): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
}

/** Parse API times that may lack Z (stored as UTC). */
function parseUtc(iso: string): Date {
  const s = iso.trim();
  if (/Z$/i.test(s) || /[+-]\d{2}:\d{2}$/.test(s)) return new Date(s);
  return new Date(s.endsWith("Z") ? s : `${s}Z`);
}

function formatLocal(iso: string | null | undefined, withDate = true): string {
  if (!iso) return "—";
  const d = parseUtc(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString("en-GB", {
    timeZone: TZ,
    ...(withDate
      ? { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: true }
      : { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: true }),
  });
}

function hoursToHm(hours: number | string | null | undefined): string {
  return formatHoursLabel(hours);
}

function minutesToHm(minutes: number | string | null | undefined): string {
  return formatMinutesAsHours(minutes);
}

function statusLabel(s: any): string {
  if (s.sign_out) return "Ended";
  if (s.status === "on_break") return "On break";
  if (s.status === "inactive") return "Inactive";
  if (s.sign_in) return "In progress";
  return "Incomplete";
}

export function DayPage() {
  const toast = useToast();
  const { id } = useParams();
  const maxDate = useMemo(() => todayLocalISO(), []);
  const [date, setDate] = useState(maxDate);
  const [day, setDay] = useState<any>(null);
  const [shots, setShots] = useState<{ id: string; captured_at: string; url: string }[]>([]);
  const [lightbox, setLightbox] = useState<number | null>(null);

  useEffect(() => {
    if (!id) return;
    if (date > maxDate) {
      toast.error(`Future dates are not allowed. Today is ${maxDate}.`);
      setDay(null);
      setShots([]);
      return;
    }
    Promise.all([fetchDay(id, date), fetchShots(id, date)])
      .then(([d, s]) => {
        setDay(d);
        setShots(s);
        setLightbox(null);
      })
      .catch((e) => toast.error(String(e)));
  }, [id, date, maxDate]);

  useEffect(() => {
    if (lightbox === null) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setLightbox(null);
      if (e.key === "ArrowRight") setLightbox((i) => (i === null ? i : Math.min(i + 1, shots.length - 1)));
      if (e.key === "ArrowLeft") setLightbox((i) => (i === null ? i : Math.max(i - 1, 0)));
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [lightbox, shots.length]);

  const token = localStorage.getItem("ems_token") || "";
  const pdfHref = `/api/v1/employees/${id}/day.pdf?date=${date}&v=${Date.now()}`;

  const manager = (() => {
    const r = localStorage.getItem("ems_role") || "";
    return r === "admin" || r === "manager";
  })();

  return (
    <div>
      <p>
        {manager ? (
          <Link to="/live">← Live</Link>
        ) : (
          <Link to="/projects">← My Projects</Link>
        )}
      </p>
      <div className="toolbar">
        <h2 style={{ margin: 0, flex: 1 }}>Day detail</h2>
        <div className="field date-field">
          <label htmlFor="day-date">Date</label>
          <div className="date-wrap">
            <input
              id="day-date"
              type="date"
              max={maxDate}
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
            <span className="date-icon" aria-hidden>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="5" width="18" height="16" rx="2" stroke="#C9A227" strokeWidth="2" />
                <path d="M3 10h18M8 3v4M16 3v4" stroke="#C9A227" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </span>
          </div>
        </div>
        <button
          type="button"
          className="secondary"
          onClick={async () => {
            if (date > maxDate) {
              toast.error(`Future dates are not allowed. Today is ${maxDate}.`);
              return;
            }
            const r = await fetch(
              `/api/v1/employees/${id}/day.pdf?date=${date}&inline=1&v=${Date.now()}`,
              { headers: { Authorization: `Bearer ${token}` } }
            );
            if (!r.ok) {
              toast.error(`PDF failed (${r.status})`);
              return;
            }
            const blob = await r.blob();
            const url = URL.createObjectURL(blob);
            window.open(url, "_blank", "noopener,noreferrer");
            setTimeout(() => URL.revokeObjectURL(url), 60_000);
          }}
        >
          View PDF
        </button>
        {manager ? (
          <button
            type="button"
            onClick={async () => {
              if (date > maxDate) {
                toast.error(`Future dates are not allowed. Today is ${maxDate}.`);
                return;
              }
              const r = await fetch(pdfHref, { headers: { Authorization: `Bearer ${token}` } });
              if (!r.ok) {
                let msg = `PDF failed (${r.status})`;
                try {
                  const j = await r.json();
                  if (typeof j?.detail === "string") msg = j.detail;
                } catch {
                  /* ignore */
                }
                toast.error(msg);
                return;
              }
              const blob = await r.blob();
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = `daily_${date}.pdf`;
              a.click();
              URL.revokeObjectURL(url);
            }}
          >
            Download PDF
          </button>
        ) : null}
      </div>
      {day ? (
        <>
          <div className="grid-live" style={{ marginBottom: 16 }}>
            <div className="card">
              <h3>Net work</h3>
              <p style={{ fontSize: 28, margin: 0 }}>{hoursToHm(day.net_hours)}</p>
            </div>
            <div className="card">
              <h3>Break time</h3>
              <p style={{ fontSize: 28, margin: 0 }}>{hoursToHm(day.break_hours)}</p>
            </div>
            <div className="card">
              <h3>Clicks / Keys</h3>
              <p style={{ fontSize: 28, margin: 0 }}>
                {day.total_clicks} / {day.total_keys}
              </p>
            </div>
            <div className="card">
              <h3>Idle time</h3>
              <p style={{ fontSize: 28, margin: 0 }}>{minutesToHm(day.idle_minutes)}</p>
            </div>
          </div>
          <div className="card" style={{ marginBottom: 16 }}>
            <h3>Sessions</h3>
            <div className="sessions-wrap">
            <table className="table-center">
              <thead>
                <tr>
                  <th>Sign In</th>
                  <th>Sign Out</th>
                  <th>Break</th>
                  <th>Net work</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {day.sessions.map((s: any) => (
                  <tr key={s.session_id}>
                    <td>{s.sign_in ? formatLocal(s.sign_in, false) : "—"}</td>
                    <td>{s.sign_out ? formatLocal(s.sign_out, false) : "—"}</td>
                    <td>{minutesToHm(s.break_minutes)}</td>
                    <td>{hoursToHm(s.net_hours)}</td>
                    <td>{statusLabel(s)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          </div>
          <div className="toolbar" style={{ alignItems: "center" }}>
            <h3 style={{ margin: 0, flex: 1 }}>Screenshots — {date}</h3>
            <span className="muted">{shots.length} capture(s)</span>
          </div>
          <div className="shots-grid">
            {shots.map((s, idx) => (
              <button type="button" className="shot-card" key={s.id} onClick={() => setLightbox(idx)}>
                <p className="shot-time">{formatLocal(s.captured_at)}</p>
                <AuthedImg path={s.url} className="thumb" alt={`Screenshot ${idx + 1}`} />
              </button>
            ))}
            {!shots.length ? <p className="muted">No screenshots this day.</p> : null}
          </div>
        </>
      ) : null}

      {lightbox !== null && shots[lightbox]
        ? createPortal(
            <div className="lightbox" role="dialog" aria-modal="true" onClick={() => setLightbox(null)}>
              <div className="lightbox-inner" onClick={(e) => e.stopPropagation()}>
                <div className="lightbox-chrome">
                  <p className="lightbox-meta">
                    <span>
                      {lightbox + 1} / {shots.length}
                    </span>
                    <span className="lightbox-meta-date">{formatLocal(shots[lightbox].captured_at)}</span>
                  </p>
                  <button type="button" className="lightbox-x" aria-label="Close" onClick={() => setLightbox(null)}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
                      <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" />
                    </svg>
                  </button>
                </div>
                <div className="lightbox-stage">
                  <button
                    type="button"
                    className="lightbox-nav lightbox-nav-prev"
                    disabled={lightbox <= 0}
                    onClick={() => setLightbox((i) => (i === null ? 0 : Math.max(0, i - 1)))}
                    aria-label="Previous"
                  >
                    ‹
                  </button>
                  <AuthedImg path={shots[lightbox].url} className="lightbox-img" alt="Screenshot large" audit />
                  <button
                    type="button"
                    className="lightbox-nav lightbox-nav-next"
                    disabled={lightbox >= shots.length - 1}
                    onClick={() => setLightbox((i) => (i === null ? 0 : Math.min(shots.length - 1, i + 1)))}
                    aria-label="Next"
                  >
                    ›
                  </button>
                </div>
              </div>
            </div>,
            document.body,
          )
        : null}
    </div>
  );
}
