import { useEffect, useMemo, useState } from "react";
import { fetchPartnerShares, type PartnerShares } from "../api";
import { RefreshButton } from "../components/RefreshButton";
import { useToast } from "../components/ToastProvider";
import { formatMoney } from "../components/currencies";

function currentYm() {
  const d = new Date();
  return { year: d.getFullYear(), month: d.getMonth() + 1 };
}

export function PartnerSharesPage() {
  const toast = useToast();
  const init = currentYm();
  const [year, setYear] = useState(init.year);
  const [month, setMonth] = useState<number | "">(init.month);
  const [busy, setBusy] = useState(false);
  const [data, setData] = useState<PartnerShares | null>(null);

  async function load(notify = false) {
    setBusy(true);
    try {
      const next = await fetchPartnerShares({
        year,
        month: month === "" ? null : Number(month),
      });
      setData(next);
      if (notify) toast.success("Partner shares refreshed.");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to load partner shares");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    load(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [year, month]);

  const periodLabel = useMemo(() => {
    if (!data) return "";
    if (data.month) return `${data.year}-${String(data.month).padStart(2, "0")}`;
    return String(data.year);
  }, [data]);

  const years = useMemo(() => {
    const y = init.year;
    return [y, y - 1, y - 2];
  }, [init.year]);

  const splitOk =
    data != null &&
    Math.abs((data.faisal_share_usd || 0) + (data.asad_share_usd || 0) - (data.net_usd || 0)) < 0.02;

  return (
    <div className="partner-shares-page">
      <div className="toolbar">
        <div>
          <h2 style={{ margin: 0 }}>Partner shares</h2>
          <p className="muted page-sub">Faisal Khan / Asad Khan · paid invoices − office costs · 50/50 in USD</p>
        </div>
        <RefreshButton busy={busy} onClick={() => load(true)} />
      </div>

      <div className="partner-filters card">
        <label>
          Year
          <select value={year} onChange={(e) => setYear(Number(e.target.value))}>
            {years.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </label>
        <label>
          Month
          <select
            value={month === "" ? "" : String(month)}
            onChange={(e) => setMonth(e.target.value === "" ? "" : Number(e.target.value))}
          >
            <option value="">Full year</option>
            {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
              <option key={m} value={m}>
                {String(m).padStart(2, "0")}
              </option>
            ))}
          </select>
        </label>
      </div>

      {data ? (
        <>
          <div className="partner-kpis">
            <article className="card dash-stat">
              <p className="dash-stat-kicker">Paid invoices ({periodLabel})</p>
              <strong className="dash-stat-num">{formatMoney(data.paid_invoices_usd, "USD")}</strong>
              <p className="dash-stat-cap">{data.paid_invoice_count} paid</p>
            </article>
            <article className="card dash-stat">
              <p className="dash-stat-kicker">Office expenses</p>
              <strong className="dash-stat-num">{formatMoney(data.expenses_usd, "USD")}</strong>
              <p className="dash-stat-cap">{data.expense_count} items (entered in PKR)</p>
            </article>
            <article className="card dash-stat dash-stat-gold">
              <p className="dash-stat-kicker">Net pool</p>
              <strong className="dash-stat-num">{formatMoney(data.net_usd, "USD")}</strong>
              <p className="dash-stat-cap">Paid − expenses</p>
            </article>
            <article className="card dash-stat dash-stat-ok">
              <p className="dash-stat-kicker">{data.partner_a_name}</p>
              <strong className="dash-stat-num">{formatMoney(data.faisal_share_usd, "USD")}</strong>
              <p className="dash-stat-cap">50%</p>
            </article>
            <article className="card dash-stat dash-stat-ok">
              <p className="dash-stat-kicker">{data.partner_b_name}</p>
              <strong className="dash-stat-num">{formatMoney(data.asad_share_usd, "USD")}</strong>
              <p className="dash-stat-cap">50%</p>
            </article>
          </div>

          {!splitOk ? (
            <p className="text-pending" role="status">
              Split check failed — refresh or contact support. Faisal + Asad must equal net.
            </p>
          ) : null}

          <article className="card" style={{ marginBottom: 16 }}>
            <div className="dash-panel-head">
              <div>
                <h3>Paid invoices</h3>
                <p className="muted page-sub">Only paid USD invoices count in the pool</p>
              </div>
            </div>
            {data.paid_rows.length ? (
              <table className="data">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Invoice</th>
                    <th>Client</th>
                    <th>Amount</th>
                    <th>In pool</th>
                  </tr>
                </thead>
                <tbody>
                  {data.paid_rows.map((r) => (
                    <tr key={r.id}>
                      <td>{r.invoice_date || "—"}</td>
                      <td>{r.number || "—"}</td>
                      <td>{r.client_name}</td>
                      <td>{formatMoney(r.amount, r.currency)}</td>
                      <td>{r.in_pool ? "Yes" : "No"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="muted">No paid invoices in this period.</p>
            )}
          </article>

          <article className="card">
            <div className="dash-panel-head">
              <div>
                <h3>Office expenses</h3>
                <p className="muted page-sub">Entered in PKR · converted to USD for the partner pool</p>
              </div>
            </div>
            {(data.expense_rows || []).length ? (
              <table className="data">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Category</th>
                    <th>Note</th>
                    <th>USD</th>
                    <th className="muted">Entered (PKR)</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.expense_rows || []).map((r) => (
                    <tr key={r.id}>
                      <td>{r.spent_on}</td>
                      <td>{r.category}</td>
                      <td>{r.vendor_note || "—"}</td>
                      <td>{formatMoney(r.amount_usd, "USD")}</td>
                      <td className="muted">
                        Rs {Number(r.amount_pkr || 0).toLocaleString("en-PK", { maximumFractionDigits: 0 })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="muted">No office expenses in this period.</p>
            )}
          </article>
        </>
      ) : (
        <p className="muted">{busy ? "Loading…" : "No data."}</p>
      )}
    </div>
  );
}
