import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { fetchDashboard, type DashboardSummary } from "../api";
import { HoursWeekChart, MoneyBars, PipelineBars, PresenceDonut, Sparkline } from "../components/DashCharts";
import {
  isLocalDashPreview,
  PREVIEW_HOURS_LAST,
  PREVIEW_HOURS_THIS,
  PREVIEW_SPARK,
  previewHourDays,
} from "../dashLayoutPreview";
import { useToast } from "../components/ToastProvider";
import { RefreshButton } from "../components/RefreshButton";
import { formatHours, formatHoursLabel } from "../formatHours";

function money(amount: number, currency = "USD") {
  try {
    return new Intl.NumberFormat("en-US", { style: "currency", currency, maximumFractionDigits: 0 }).format(amount);
  } catch {
    return `${currency} ${Math.round(amount)}`;
  }
}

function statusLabel(status: string) {
  if (status === "working") return "Signed in";
  if (status === "break") return "Break";
  if (status === "idle") return "Idle";
  return "Offline";
}

function pillClass(status: string) {
  if (status === "working") return "dash-pill dash-pill-working";
  if (status === "break" || status === "idle") return "dash-pill dash-pill-break";
  return "dash-pill dash-pill-offline";
}

function deltaLabel(n: number) {
  const abs = Math.abs(n).toFixed(1);
  if (n > 0.05) return `+${abs} h vs last week`;
  if (n < -0.05) return `−${abs} h vs last week`;
  return "Even with last week";
}

function isAbort(e: unknown) {
  return (e instanceof DOMException && e.name === "AbortError") || (e instanceof Error && e.name === "AbortError");
}

export function DashboardPage() {
  const toast = useToast();
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const abortRef = useRef<AbortController | null>(null);
  const dataRef = useRef<DashboardSummary | null>(null);
  dataRef.current = data;

  async function load(notify = false) {
    abortRef.current?.abort();
    const ac = new AbortController();
    abortRef.current = ac;
    setBusy(true);
    try {
      const next = await fetchDashboard(ac.signal);
      setData(next);
      setErr("");
    } catch (e) {
      if (isAbort(e) || ac.signal.aborted) return;
      const msg = e instanceof Error ? e.message : "Could not load dashboard.";
      setErr(msg);
      if (notify || !dataRef.current) toast.error(msg);
    } finally {
      if (!ac.signal.aborted) setBusy(false);
    }
  }

  useEffect(() => {
    load(false);
    const t = setInterval(() => load(false), 20000);
    return () => {
      abortRef.current?.abort();
      clearInterval(t);
    };
  }, []);

  const layoutPreview = import.meta.env.DEV && isLocalDashPreview();
  const spark = data?.sparkline?.length ? data.sparkline : [0];
  const pipeline = data?.pipeline;
  const finance = data?.finance;
  const staff = layoutPreview ? 5 : data?.staff_count || 0;
  const liveNow = layoutPreview ? 2 : data?.live_now || 0;
  const breakIdle = layoutPreview ? 1 : data?.break_idle || 0;
  const offline = layoutPreview ? 2 : data?.offline || 0;
  const pipeRows = pipeline
    ? [
        { key: "working", label: "In progress", n: pipeline.working, color: "#22c55e" },
        { key: "waiting", label: "Waiting", n: pipeline.waiting, color: "#3b82f6" },
        { key: "hold", label: "On hold", n: pipeline.on_hold, color: "#f59e0b" },
        { key: "done", label: "Done", n: pipeline.done, color: "#64748b" },
      ]
    : [];
  const weekLogged = layoutPreview
    ? PREVIEW_HOURS_THIS.reduce((s, n) => s + n, 0)
    : (data?.hours_this_week || []).reduce((s, d) => s + d.hours, 0);
  const hoursThis = layoutPreview ? previewHourDays(PREVIEW_HOURS_THIS) : data?.hours_this_week || [];
  const hoursLast = layoutPreview ? previewHourDays(PREVIEW_HOURS_LAST) : data?.hours_last_week || [];
  const weekDelta = layoutPreview ? 1.2 : data?.week_delta_hours ?? 0;
  const sparkLive = layoutPreview ? PREVIEW_SPARK.live : spark;
  const sparkBrk = layoutPreview ? PREVIEW_SPARK.brk : spark;
  const sparkOff = layoutPreview ? PREVIEW_SPARK.off : spark;
  const sparkJobs = layoutPreview ? PREVIEW_SPARK.jobs : spark;
  const sparkCash = layoutPreview ? PREVIEW_SPARK.cash : spark;
  const jobsOpen = layoutPreview ? 9 : pipeline?.open ?? 0;
  const jobsTotal = layoutPreview ? 12 : pipeline?.total ?? 0;
  const unpaidCount = layoutPreview ? 4 : finance?.unpaid_count ?? 0;
  const unpaidLabel = layoutPreview
    ? "$21,780 outstanding"
    : finance
      ? `${money(finance.unpaid_amount, finance.currency)} outstanding`
      : "Outstanding";
  const showFinanceKpi = Boolean(finance) || layoutPreview;
  const lateRows = finance?.late || [];

  return (
    <div className="dash">
      <div className="toolbar">
        <div>
          <h2 style={{ margin: 0 }}>Dashboard</h2>
          <p className="muted page-sub">
            {showFinanceKpi ? "Team, projects, and cash at a glance." : "People, presence, and project load at a glance."}
          </p>
        </div>
        <RefreshButton
          busy={busy}
          onClick={() => load(true)}
          busyLabel={busy && !data ? "Loading…" : "Refreshing…"}
        />
      </div>

      {err && !data ? <p className="muted">{err}</p> : null}
      {err && data ? (
        <p className="muted dash-refresh-err" role="status">
          Could not refresh — showing last loaded data. {err}
        </p>
      ) : null}

      <div className="dash-stats">
        <article className="card dash-stat dash-stat-ok">
          <p className="dash-stat-kicker">Live now</p>
          <strong className="dash-stat-num">{data || layoutPreview ? liveNow : "—"}</strong>
          <p className="dash-stat-cap">{data || layoutPreview ? `of ${staff} staff signed in` : "Staff signed in"}</p>
          <Sparkline values={sparkLive} color="#4ade80" />
        </article>
        <article className="card dash-stat dash-stat-warn">
          <p className="dash-stat-kicker">Break / idle</p>
          <strong className="dash-stat-num">{data || layoutPreview ? breakIdle : "—"}</strong>
          <p className="dash-stat-cap">{layoutPreview ? "paused in the last 15 min" : "Paused / idle"}</p>
          <Sparkline values={sparkBrk} color="#fb923c" />
        </article>
        <article className="card dash-stat dash-stat-bad">
          <p className="dash-stat-kicker">Offline</p>
          <strong className="dash-stat-num">{data || layoutPreview ? offline : "—"}</strong>
          <p className="dash-stat-cap">not clocked in today</p>
          <Sparkline values={sparkOff} color="#f87171" />
        </article>
        <article className="card dash-stat dash-stat-mute">
          <p className="dash-stat-kicker">Open projects</p>
          <strong className="dash-stat-num">{pipeline || layoutPreview ? jobsOpen : "—"}</strong>
          <p className="dash-stat-cap">{pipeline || layoutPreview ? `${jobsTotal} total jobs` : "Jobs"}</p>
          <Sparkline values={sparkJobs} color="#e5e7eb" />
        </article>
        {showFinanceKpi ? (
          <article className="card dash-stat dash-stat-gold">
            <p className="dash-stat-kicker">Unpaid invoices</p>
            <strong className="dash-stat-num">{unpaidCount}</strong>
            <p className="dash-stat-cap">{unpaidLabel}</p>
            <Sparkline values={sparkCash} color="#c9a227" />
          </article>
        ) : null}
      </div>

      <div className="dash-panels">
        <article className="card dash-panel dash-panel-presence">
          <div className="dash-panel-head">
            <div>
              <h3>Team presence</h3>
              <p className="muted page-sub">Live status across the studio</p>
            </div>
          </div>
          <PresenceDonut working={liveNow} brk={breakIdle} offline={offline} />
        </article>
        <article className="card dash-panel dash-panel-hours">
          <div className="dash-panel-head">
            <div>
              <h3>Team hours this week</h3>
              <p className="muted page-sub">
                All staff combined · {formatHours(weekLogged)} h this week · Mon–Sun
              </p>
            </div>
            {data || layoutPreview ? (
              <span className={`dash-delta${weekDelta < -0.05 ? " is-down" : ""}`}>{deltaLabel(weekDelta)}</span>
            ) : null}
          </div>
          <HoursWeekChart thisWeek={hoursThis} lastWeek={hoursLast} />
          <p className="dash-hours-legend">
            <i className="dash-swatch gold" /> This week (everyone)
            <i className="dash-swatch grey" /> Last week (everyone)
          </p>
        </article>
      </div>

      <div className={`dash-panels${finance ? "" : " dash-panels-one"}`}>
        <article className="card dash-panel">
          <div className="dash-panel-head">
            <div>
              <h3>Project pipeline</h3>
              <p className="muted page-sub">{pipeline ? `${pipeline.total} CFS jobs tracked` : "No jobs yet"}</p>
            </div>
          </div>
          {pipeline && pipeline.total ? (
            <PipelineBars rows={pipeRows} total={pipeline.total} />
          ) : (
            <p className="muted">No projects yet.</p>
          )}
        </article>
        {finance ? (
          <article className="card dash-panel dash-panel-invoices">
            <div className="dash-panel-head">
              <div>
                <h3>Client invoices</h3>
                <p className="muted page-sub">This month — unpaid vs collected</p>
              </div>
              <span className="dash-admin-badge">Admin</span>
            </div>
            <MoneyBars unpaid={finance.unpaid_amount} paid={finance.paid_month_amount} currency={finance.currency} />
            {lateRows.length ? (
              <>
                <ul className="dash-late">
                  {lateRows.map((inv) => (
                    <li key={inv.id}>
                      <strong title={inv.client_name}>{inv.client_name}</strong>
                      <span className="dash-late-meta">
                        <span className="muted">{inv.number || "—"}</span>
                        <span className="text-pending">{inv.delayed_days}d late</span>
                      </span>
                      <b>{money(inv.amount, inv.currency)}</b>
                    </li>
                  ))}
                </ul>
                <p className="muted dash-late-hint">{finance.late.length} overdue</p>
              </>
            ) : (
              <p className="muted dash-late-empty">No late invoices.</p>
            )}
          </article>
        ) : null}
      </div>

      <article className="card dash-panel">
        <div className="dash-panel-head">
          <div>
            <h3>Team roster</h3>
            <p className="muted page-sub">
              {staff} staff — today’s activity
              {data?.generated_at ? ` · ${data.generated_at}` : ""}
            </p>
          </div>
        </div>
        {data?.roster.length ? (
          <ul className="dash-roster">
            {data.roster.map((r) => (
              <li key={r.employee_id}>
                <span className="dash-avatar" aria-hidden>
                  #{r.code}
                </span>
                <div className="dash-roster-id">
                  <strong>{r.full_name}</strong>
                  <span className="muted">{formatHoursLabel(r.hours_today)} today</span>
                </div>
                <span className={pillClass(r.status)}>
                  <i className={`dot ${r.status}`} />
                  {statusLabel(r.status)}
                </span>
                <p className="muted dash-window" title={r.last_window || ""}>
                  {r.last_window || "No window yet"}
                </p>
                <Link to={`/day/${r.employee_id}`}>Day</Link>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No employees yet. Add staff on Employees, then enroll each PC.</p>
        )}
      </article>
    </div>
  );
}
