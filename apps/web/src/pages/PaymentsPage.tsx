import { useEffect, useMemo, useState } from "react";
import {
  deleteInvoice,
  fetchClients,
  fetchInvoices,
  fetchProjects,
  saveInvoice,
  type ClientRow,
  type InvoiceRow,
  type ProjectRow,
} from "../api";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { CurrencySelect } from "../components/CurrencySelect";
import { useToast } from "../components/ToastProvider";
import { formatMoney, guessCurrencyFromLocation, normalizeCurrencyCode } from "../components/currencies";
import { invoiceStatusLabel, invoiceStatusTextClass } from "../components/invoiceStatus";

const STATUSES = ["proforma", "sent", "pending", "paid", "overdue", "info_sent", "unpaid_info"];

function isoDate(v: string | null | undefined): string {
  if (!v) return "";
  return String(v).slice(0, 10);
}

function monthKey(iso: string | null | undefined): string {
  return isoDate(iso).slice(0, 7);
}

function thisMonthKey(): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Karachi",
    year: "numeric",
    month: "2-digit",
  }).format(new Date());
}

const empty = {
  client_id: "",
  project_id: "",
  number: "",
  amount: "",
  currency: "USD",
  invoice_date: "",
  follow_up_at: "",
  status: "pending",
  kind: "deposit",
  client_comments: "",
};

export function PaymentsPage() {
  const toast = useToast();
  const [rows, setRows] = useState<InvoiceRow[]>([]);
  const [clients, setClients] = useState<ClientRow[]>([]);
  const [projects, setProjects] = useState<ProjectRow[]>([]);
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const [form, setForm] = useState(empty);
  const [q, setQ] = useState("");
  const [pendingDelete, setPendingDelete] = useState<InvoiceRow | null>(null);
  const [deleting, setDeleting] = useState(false);
  const token = localStorage.getItem("ems_token") || "";

  async function load() {
    setBusy(true);
    try {
      const [inv, c, p] = await Promise.all([fetchInvoices(), fetchClients(), fetchProjects()]);
      setRows(inv);
      setClients(c);
      setProjects(p);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Load failed");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setBusy(true);
      try {
        const [inv, c, p] = await Promise.all([fetchInvoices(), fetchClients(), fetchProjects()]);
        if (cancelled) return;
        setRows(inv);
        setClients(c);
        setProjects(p);
      } catch (e) {
        if (!cancelled) toast.error(e instanceof Error ? e.message : "Load failed");
      } finally {
        if (!cancelled) setBusy(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const sorted = useMemo(() => {
    return [...rows].sort((a, b) => {
      const byClient = a.client_name.localeCompare(b.client_name, undefined, { sensitivity: "base" });
      if (byClient !== 0) return byClient;
      const da = a.invoice_date || "";
      const db = b.invoice_date || "";
      if (da !== db) return da.localeCompare(db);
      return a.number.localeCompare(b.number, undefined, { numeric: true });
    });
  }, [rows]);

  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    if (!s) return sorted;
    return sorted.filter(
      (r) =>
        r.client_name.toLowerCase().includes(s) ||
        r.number.toLowerCase().includes(s) ||
        r.status.toLowerCase().includes(s) ||
        (r.project_name || "").toLowerCase().includes(s)
    );
  }, [sorted, q]);

  const summary = useMemo(() => {
    const ym = thisMonthKey();
    let pending = 0;
    let received = 0;
    let monthReceived = 0;
    let overdueCount = 0;
    for (const r of rows) {
      const amt = Number(r.amount) || 0;
      if (r.status === "paid") {
        received += amt;
        if (monthKey(r.invoice_date) === ym) {
          monthReceived += amt;
        }
      } else {
        pending += amt;
        if (r.delayed_days > 0) overdueCount += 1;
      }
    }
    return { pending, received, monthReceived, overdueCount, currency: "USD" };
  }, [rows]);

  function startEdit(r?: InvoiceRow) {
    if (!r) {
      setEditing("new");
      setForm(empty);
      return;
    }
    setEditing(r.id);
    setForm({
      client_id: r.client_id,
      project_id: r.project_id || "",
      number: r.number,
      amount: String(r.amount),
      currency: r.currency || "USD",
      invoice_date: isoDate(r.invoice_date),
      follow_up_at: isoDate(r.follow_up_at),
      status: r.status,
      kind: r.kind || "deposit",
      client_comments: r.client_comments || "",
    });
  }

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    try {
      await saveInvoice(
        {
          client_id: form.client_id,
          project_id: form.project_id || null,
          number: form.number,
          amount: Number(form.amount),
          currency: normalizeCurrencyCode(form.currency),
          invoice_date: form.invoice_date ? `${form.invoice_date}T12:00:00` : null,
          follow_up_at: form.follow_up_at ? `${form.follow_up_at}T12:00:00` : null,
          status: form.status,
          kind: form.kind,
          client_comments: form.client_comments,
        },
        editing && editing !== "new" ? editing : undefined
      );
      setEditing(null);
      toast.success(editing === "new" ? "Invoice saved." : "Invoice updated.");
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Save failed");
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    setDeleting(true);
    try {
      await deleteInvoice(pendingDelete.id);
      if (editing === pendingDelete.id) setEditing(null);
      setPendingDelete(null);
      toast.success("Invoice deleted.");
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setDeleting(false);
    }
  }

  async function downloadXlsx() {
    const r = await fetch("/api/v1/reports/payments.xlsx", { headers: { Authorization: `Bearer ${token}` } });
    if (!r.ok) {
      toast.error("Excel download failed");
      return;
    }
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "CFS_Payments_Tracking.xlsx";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div>
      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title="Delete invoice?"
        message={
          pendingDelete
            ? `Delete invoice “${pendingDelete.number}” for ${pendingDelete.client_name}? This cannot be undone.`
            : ""
        }
        confirmLabel="Delete"
        busy={deleting}
        onCancel={() => !deleting && setPendingDelete(null)}
        onConfirm={confirmDelete}
      />

      <div className="toolbar">
        <h2 style={{ margin: 0, flex: 1 }}>Payments tracking</h2>
        <input style={{ maxWidth: 260 }} placeholder="Search client, invoice, status…" value={q} onChange={(e) => setQ(e.target.value)} />
        <button type="button" className="secondary" onClick={downloadXlsx}>
          Download Excel
        </button>
        <button type="button" onClick={() => startEdit()}>
          New invoice
        </button>
        <button type="button" className="secondary" onClick={() => load()} disabled={busy}>
          {busy ? "Refreshing…" : "↻ Refresh"}
        </button>
      </div>

      <div className="payments-summary">
        <div className="payments-summary-card">
          <span className="payments-summary-label">Total pending</span>
          <strong className="text-pending">{formatMoney(summary.pending, summary.currency)}</strong>
        </div>
        <div className="payments-summary-card">
          <span className="payments-summary-label">Total received</span>
          <strong className="text-paid">{formatMoney(summary.received, summary.currency)}</strong>
        </div>
        <div className="payments-summary-card">
          <span className="payments-summary-label">This month received</span>
          <strong>{formatMoney(summary.monthReceived, summary.currency)}</strong>
        </div>
        <div className="payments-summary-card">
          <span className="payments-summary-label">Overdue invoices</span>
          <strong className={summary.overdueCount ? "text-pending" : ""}>{summary.overdueCount}</strong>
        </div>
      </div>

      {editing ? (
        <form className="card" style={{ marginBottom: 16 }} onSubmit={onSave}>
          <h3 style={{ marginTop: 0 }}>{editing === "new" ? "New invoice" : "Edit invoice"}</h3>
          <div className="toolbar">
            <div className="field">
              <label>Client</label>
              <select
                required
                value={form.client_id}
                onChange={(e) => {
                  const clientId = e.target.value;
                  const client = clients.find((c) => c.id === clientId);
                  const next = { ...form, client_id: clientId };
                  if (editing === "new" && client) {
                    next.currency = guessCurrencyFromLocation(client.location);
                  }
                  setForm(next);
                }}
              >
                <option value="">—</option>
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Project</label>
              <select value={form.project_id} onChange={(e) => setForm({ ...form, project_id: e.target.value })}>
                <option value="">—</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Invoice #</label>
              <input required value={form.number} onChange={(e) => setForm({ ...form, number: e.target.value })} />
            </div>
            <div className="field">
              <label>Value</label>
              <div className="money-field">
                <input
                  className="money-amount"
                  type="number"
                  min={0}
                  step="0.01"
                  required
                  value={form.amount}
                  onChange={(e) => setForm({ ...form, amount: e.target.value })}
                />
                <div className="money-currency">
                  <CurrencySelect value={form.currency} onChange={(currency) => setForm({ ...form, currency })} required />
                </div>
              </div>
            </div>
          </div>
          <div className="toolbar">
            <div className="field">
              <label>Invoice date</label>
              <input type="date" value={form.invoice_date} onChange={(e) => setForm({ ...form, invoice_date: e.target.value })} />
            </div>
            <div className="field">
              <label>Follow up date</label>
              <input type="date" value={form.follow_up_at} onChange={(e) => setForm({ ...form, follow_up_at: e.target.value })} />
            </div>
            <div className="field">
              <label>Status</label>
              <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Kind</label>
              <select value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
                <option value="deposit">Deposit</option>
                <option value="balance">Balance</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          <div className="field">
            <label>Comments from client</label>
            <input value={form.client_comments} onChange={(e) => setForm({ ...form, client_comments: e.target.value })} />
          </div>
          <div className="toolbar">
            <button type="submit">Save</button>
            <button type="button" className="secondary" onClick={() => setEditing(null)}>
              Cancel
            </button>
          </div>
        </form>
      ) : null}

      <div className="card payments-table-wrap">
        <table className="payments-table">
          <thead>
            <tr>
              <th className="col-num">S/No.</th>
              <th className="col-client">Client</th>
              <th className="col-location">Location</th>
              <th className="col-project">Project</th>
              <th className="col-invoice">Invoice</th>
              <th className="col-money">Value</th>
              <th className="col-date">Invoice date</th>
              <th className="col-date">Follow up</th>
              <th className="col-days">Delayed (days)</th>
              <th className="col-status">Status</th>
              <th className="col-comments">Comments</th>
              <th className="col-actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r, i) => (
              <tr key={r.id} className="payments-row">
                <td className="col-num" onClick={() => startEdit(r)}>
                  {i + 1}
                </td>
                <td className="col-client" onClick={() => startEdit(r)}>
                  <span className="cell-text cell-client-link">{r.client_name}</span>
                </td>
                <td className="col-location" onClick={() => startEdit(r)}>
                  <span className="cell-text">{r.location || "—"}</span>
                </td>
                <td className="col-project" onClick={() => startEdit(r)}>
                  <span className="cell-text">{r.project_name || "—"}</span>
                </td>
                <td className="col-invoice" onClick={() => startEdit(r)}>
                  <span className="cell-text">{r.number}</span>
                </td>
                <td className="col-money" onClick={() => startEdit(r)}>
                  {formatMoney(Number(r.amount), r.currency)}
                </td>
                <td onClick={() => startEdit(r)}>{isoDate(r.invoice_date) || "—"}</td>
                <td onClick={() => startEdit(r)}>{isoDate(r.follow_up_at) || "—"}</td>
                <td
                  className={`col-days${r.delayed_days > 0 && r.status !== "paid" ? " text-pending" : ""}`}
                  onClick={() => startEdit(r)}
                >
                  {r.delayed_days}
                </td>
                <td onClick={() => startEdit(r)}>
                  <span className={invoiceStatusTextClass(r.status)}>{invoiceStatusLabel(r.status)}</span>
                </td>
                <td className="col-comments" onClick={() => startEdit(r)}>
                  <span className="cell-text">{r.client_comments || "—"}</span>
                </td>
                <td className="col-actions">
                  <button
                    type="button"
                    className="btn-danger btn-row-del"
                    onClick={(e) => {
                      e.stopPropagation();
                      setPendingDelete(r);
                    }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
