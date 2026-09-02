import { useId } from "react";

type SparklineProps = {
  values: number[];
  color: string;
};

export function Sparkline({ values, color }: SparklineProps) {
  const gid = `spark-${useId().replace(/:/g, "")}`;
  const pts = values.length ? values : [0];
  const idle = pts.every((v) => v < 0.05);
  const max = Math.max(...pts, 0.01);
  const min = idle ? 0 : Math.min(...pts, 0);
  const span = Math.max(max - min, 0.01);
  const w = 240;
  const h = 56;
  const coords = pts.map((v, i) => {
    const x = pts.length === 1 ? w / 2 : (i / (pts.length - 1)) * (w - 8) + 4;
    const y = idle ? h * 0.58 : h - 4 - ((v - min) / span) * (h - 14);
    return { x, y };
  });
  const line = coords.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
  const first = coords[0];
  const last = coords[coords.length - 1];
  const area = `${line} L${last.x.toFixed(1)},${h} L${first.x.toFixed(1)},${h} Z`;
  return (
    <svg className="dash-spark" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" aria-hidden>
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.5" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gid})`} />
      <path d={line} fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

type PresenceProps = {
  working: number;
  brk: number;
  offline: number;
};

export function PresenceDonut({ working, brk, offline }: PresenceProps) {
  const total = Math.max(working + brk + offline, 0);
  const r = 54;
  const c = 2 * Math.PI * r;
  const segs = [
    { n: working, color: "#4ade80" },
    { n: brk, color: "#fb923c" },
    { n: offline, color: "#f87171" },
  ];
  let offset = 0;
  const pct = (n: number) => (total ? Math.round((n / total) * 100) : 0);
  return (
    <div className="dash-presence">
      <div className="dash-donut-wrap">
        <svg viewBox="0 0 140 140" className="dash-donut" aria-hidden>
          <circle cx="70" cy="70" r={r} fill="none" stroke="var(--donut-track)" strokeWidth="16" />
          {total
            ? segs.map((s) => {
                const len = (s.n / total) * c;
                const el = (
                  <circle
                    key={s.color}
                    cx="70"
                    cy="70"
                    r={r}
                    fill="none"
                    stroke={s.color}
                    strokeWidth="16"
                    strokeDasharray={`${len} ${c - len}`}
                    strokeDashoffset={-offset}
                    strokeLinecap="butt"
                    transform="rotate(-90 70 70)"
                  />
                );
                offset += len;
                return el;
              })
            : null}
        </svg>
        <div className="dash-donut-center">
          <strong>{working}</strong>
          <span>Live now</span>
        </div>
      </div>
      <ul className="dash-legend">
        <li>
          <i style={{ background: "#4ade80" }} />
          <span>Signed in</span>
          <b>
            {working} <em>{pct(working)}%</em>
          </b>
        </li>
        <li>
          <i style={{ background: "#fb923c" }} />
          <span>Break / idle</span>
          <b>
            {brk} <em>{pct(brk)}%</em>
          </b>
        </li>
        <li>
          <i style={{ background: "#f87171" }} />
          <span>Offline</span>
          <b>
            {offline} <em>{pct(offline)}%</em>
          </b>
        </li>
      </ul>
    </div>
  );
}

type HoursChartProps = {
  thisWeek: { label: string; hours: number }[];
  lastWeek: { label: string; hours: number }[];
};

export function HoursWeekChart({ thisWeek, lastWeek }: HoursChartProps) {
  const fallback = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const labels = thisWeek.length ? thisWeek.map((d) => d.label) : fallback;
  const a = labels.map((_, i) => thisWeek[i]?.hours || 0);
  const b = labels.map((_, i) => lastWeek[i]?.hours || 0);
  const peak = Math.max(10, ...a, ...b, 0);
  const maxY = Math.ceil(peak / 2.5) * 2.5 || 10;
  const W = 420;
  const H = 228;
  const left = 48;
  const right = 12;
  const top = 10;
  const bottom = 28;
  const innerW = W - left - right;
  const innerH = H - top - bottom;
  const n = Math.max(labels.length, 1);
  const group = innerW / n;
  const barW = Math.min(18, group * 0.32);
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((t) => t * maxY);

  function y(v: number) {
    return top + innerH - (v / maxY) * innerH;
  }

  return (
    <svg className="dash-hours-svg" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Team hours each day this week versus last week. All employees combined.">
      {ticks.map((t) => (
        <g key={t}>
          <line
            x1={left}
            x2={W - right}
            y1={y(t)}
            y2={y(t)}
            stroke="var(--chart-grid)"
            strokeWidth="1"
            strokeDasharray="5 6"
          />
          <text x={left - 8} y={y(t) + 4} textAnchor="end" fill="currentColor" fontSize="14">
            {t.toFixed(1)}h
          </text>
        </g>
      ))}
      {labels.map((lab, i) => {
        const cx = left + i * group + group / 2;
        const hThis = a[i] || 0;
        const hLast = b[i] || 0;
        const xLast = cx - barW - 2;
        const xThis = cx + 2;
        return (
          <g key={lab}>
            <rect x={xLast} y={y(hLast)} width={barW} height={Math.max(0, y(0) - y(hLast))} fill="var(--chart-last)" rx="2" />
            <rect x={xThis} y={y(hThis)} width={barW} height={Math.max(0, y(0) - y(hThis))} fill="var(--gold)" rx="2" />
            <text x={cx} y={H - 8} textAnchor="middle" fill="currentColor" fontSize="14">
              {lab}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

type PipelineRow = { key: string; label: string; n: number; color: string };

export function PipelineBars({ rows, total }: { rows: PipelineRow[]; total: number }) {
  const denom = Math.max(total, 1);
  return (
    <div className="dash-bars">
      {rows.map((row) => {
        const pct = total ? Math.round((row.n / denom) * 100) : 0;
        return (
          <div className="dash-bar-row" key={row.key}>
            <div className="dash-bar-meta">
              <span>
                <i className="dash-bar-dot" style={{ background: row.color }} /> {row.label}
              </span>
              <b>
                {row.n} <em>{pct}%</em>
              </b>
            </div>
            <div className="dash-bar-track" aria-hidden>
              <span style={{ width: `${row.n ? Math.max(pct, 6) : 0}%`, background: row.color }} />
            </div>
          </div>
        );
      })}
      {total ? (
        <div className="dash-composite" aria-hidden>
          <span className="muted dash-composite-label">All projects</span>
          <div className="dash-composite-track">
            {rows.map((row) =>
              row.n ? (
                <span key={row.key} style={{ width: `${(row.n / denom) * 100}%`, background: row.color }} />
              ) : null
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function niceMoneyMax(n: number): number {
  const v = Math.max(n, 1);
  if (v < 1000) {
    const step = v <= 20 ? 5 : v <= 50 ? 10 : v <= 200 ? 50 : 100;
    return Math.max(step, Math.ceil(v / step) * step);
  }
  const k = v / 1000;
  const tops = [4, 5, 8, 10, 12, 15, 16, 20, 24, 25, 30, 40, 50, 60, 75, 80, 100, 120, 150, 200, 250, 300, 400, 500, 750, 1000];
  const top = tops.find((c) => c >= k) ?? Math.ceil(k / 100) * 100;
  return top * 1000;
}

function axisMoney(v: number, currency: string): string {
  const sym = currency === "AUD" ? "A$" : currency === "PKR" ? "Rs" : currency === "USD" || currency === "CAD" ? "$" : `${currency} `;
  if (v >= 1000) {
    const k = v / 1000;
    const num = k >= 10 || Number.isInteger(k) ? String(Math.round(k)) : k.toFixed(1);
    return `${sym}${num}k`;
  }
  return `${sym}${Math.round(v)}`;
}

type MoneyBarsProps = {
  unpaid: number;
  paid: number;
  currency: string;
};

export function MoneyBars({ unpaid, paid, currency }: MoneyBarsProps) {
  const max = niceMoneyMax(Math.max(unpaid, paid, 1));
  function fmt(n: number) {
    try {
      return new Intl.NumberFormat("en-US", { style: "currency", currency, maximumFractionDigits: 0 }).format(n);
    } catch {
      return `${currency} ${Math.round(n)}`;
    }
  }
  const ticks = 4;
  return (
    <div className="dash-money">
      <div className="dash-money-plot">
        <div className="dash-money-guides" aria-hidden />
        <div className="dash-money-row">
          <span>Unpaid</span>
          <div className="dash-bar-track dash-money-track">
            <span style={{ width: `${Math.max((unpaid / max) * 100, unpaid ? 4 : 0)}%`, background: "#ef4444" }} />
          </div>
          <b className="text-pending">{fmt(unpaid)}</b>
        </div>
        <div className="dash-money-row">
          <span>Paid</span>
          <div className="dash-bar-track dash-money-track">
            <span style={{ width: `${Math.max((paid / max) * 100, paid ? 4 : 0)}%`, background: "#22c55e" }} />
          </div>
          <b className="text-paid">{fmt(paid)}</b>
        </div>
        <div className="dash-money-axis" aria-hidden>
          {Array.from({ length: ticks + 1 }, (_, i) => (
            <span key={i}>{axisMoney((max / ticks) * i, currency)}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
