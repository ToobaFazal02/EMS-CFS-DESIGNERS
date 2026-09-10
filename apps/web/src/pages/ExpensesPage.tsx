import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  EXPENSE_CATEGORIES,
  createExpense,
  deleteExpense,
  fetchExpenseReceipt,
  fetchExpenses,
  type ExpenseMonth,
} from "../api";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { useToast } from "../components/ToastProvider";

const TZ = "Asia/Karachi";

const CAT_COLORS: Record<string, string> = {
  tea_water: "#4ade80",
  electricity: "#fb923c",
  gas: "#60a5fa",
  solar: "#c9a227",
  bills: "#38bdf8",
  parties: "#8b2e3b",
  other: "#a3a3a3",
};

const MONTH_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function todayParts() {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ,
    year: "numeric",
    month: "numeric",
    day: "2-digit",
  }).formatToParts(new Date());
  const y = Number(parts.find((p) => p.type === "year")?.value);
  const m = Number(parts.find((p) => p.type === "month")?.value);
  const d = parts.find((p) => p.type === "day")?.value || "01";
  return { y, m, todayISO: `${y}-${String(m).padStart(2, "0")}-${d}` };
}

function monthLabel(year: number, month: number) {
  return new Date(year, month - 1, 1).toLocaleString("en-GB", { month: "long", year: "numeric" });
}

function formatPkr(n: number) {
  return `Rs ${Math.round(n).toLocaleString("en-PK")}`;
}

function catLabel(id: string) {
  return EXPENSE_CATEGORIES.find((c) => c.id === id)?.label || id;
}

function formatShortDate(iso: string) {
  const [y, m, d] = iso.split("-").map(Number);
  if (!y || !m || !d) return iso;
  return new Date(y, m - 1, d).toLocaleDateString("en-GB", { day: "2-digit", month: "short" });
}

function shortFileName(name: string, max = 28) {
  const n = (name || "receipt").trim();
  if (n.length <= max) return n;
  const dot = n.lastIndexOf(".");
  const ext = dot > 0 ? n.slice(dot) : "";
  const stem = dot > 0 ? n.slice(0, dot) : n;
  const keep = Math.max(8, max - ext.length - 1);
  return `${stem.slice(0, keep)}…${ext}`;
}

function fileKind(name: string): "PDF" | "IMG" | "FILE" {
  const lower = (name || "").toLowerCase();
  if (lower.endsWith(".pdf")) return "PDF";
  if (/\.(jpe?g|png|webp|gif)$/i.test(lower)) return "IMG";
  return "FILE";
}

type ReceiptPreview = {
  url: string;
  name: string;
  blobUrl: string;
  kind: "PDF" | "IMG" | "FILE";
};

export function ExpensesPage() {
  const toast = useToast();
  const fileRef = useRef<HTMLInputElement>(null);
  const formRef = useRef<HTMLFormElement>(null);
  const now = useMemo(() => todayParts(), []);
  const [year, setYear] = useState(now.y);
  const [month, setMonth] = useState(now.m);
  const [filter, setFilter] = useState<string>("");
  const [data, setData] = useState<ExpenseMonth | null>(null);
  const [busy, setBusy] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [spentOn, setSpentOn] = useState(now.todayISO);
  const [category, setCategory] = useState("tea_water");
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const [receiptFile, setReceiptFile] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [preview, setPreview] = useState<ReceiptPreview | null>(null);
  const [previewBusy, setPreviewBusy] = useState(false);

  async function load() {
    setBusy(true);
    try {
      setData(await fetchExpenses(year, month, filter || undefined));
    } catch (e) {
      toast.error(e instanceof Error ? e.message : String(e));
      setData(null);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    load().catch(() => undefined);
  }, [year, month, filter]);

  useEffect(() => {
    return () => {
      if (preview?.blobUrl) URL.revokeObjectURL(preview.blobUrl);
    };
  }, [preview?.blobUrl]);

  function shiftMonth(delta: number) {
    let m = month + delta;
    let y = year;
    if (m < 1) {
      m = 12;
      y -= 1;
    } else if (m > 12) {
      m = 1;
      y += 1;
    }
    const cur = todayParts();
    if (y > cur.y || (y === cur.y && m > cur.m)) {
      toast.error("Future months are not allowed.");
      return;
    }
    setYear(y);
    setMonth(m);
  }

  function openForm() {
    setShowForm(true);
    toast.success("New expense form opened.");
    requestAnimationFrame(() => {
      formRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      document.getElementById("exp-amt")?.focus();
    });
  }

  function closeForm(notify = true) {
    setShowForm(false);
    if (notify) toast.success("Form closed.");
  }

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    const amt = Number(String(amount).replace(/,/g, ""));
    if (!Number.isFinite(amt) || amt <= 0) {
      toast.error("Enter a valid amount (PKR).");
      return;
    }
    setSaving(true);
    try {
      await createExpense({
        spent_on: spentOn,
        category,
        amount_pkr: amt,
        vendor_note: note.trim(),
        receipt: receiptFile,
      });
      toast.success(receiptFile ? "Expense saved with receipt." : "Expense saved.");
      closeForm(false);
      setAmount("");
      setNote("");
      setReceiptFile(null);
      if (fileRef.current) fileRef.current.value = "";
      setCategory("tea_water");
      const parts = spentOn.split("-").map(Number);
      if (parts[0] && parts[1]) {
        setYear(parts[0]);
        setMonth(parts[1]);
      }
      setSpentOn(todayParts().todayISO);
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    setDeleting(true);
    try {
      await deleteExpense(pendingDelete);
      toast.success("Expense removed.");
      setPendingDelete(null);
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : String(err));
    } finally {
      setDeleting(false);
    }
  }

  async function loadReceiptBlob(url: string) {
    return fetchExpenseReceipt(url);
  }

  async function viewReceipt(url: string, name: string) {
    setPreviewBusy(true);
    try {
      const blob = await loadReceiptBlob(url);
      const blobUrl = URL.createObjectURL(blob);
      if (preview?.blobUrl) URL.revokeObjectURL(preview.blobUrl);
      setPreview({ url, name, blobUrl, kind: fileKind(name) });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not open receipt");
    } finally {
      setPreviewBusy(false);
    }
  }

  async function downloadReceipt(url: string, name: string) {
    try {
      const blob = await loadReceiptBlob(url);
      const obj = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = obj;
      a.download = name || "receipt";
      a.click();
      setTimeout(() => URL.revokeObjectURL(obj), 30_000);
      toast.success("Download started.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not download receipt");
    }
  }

  function closePreview() {
    if (preview?.blobUrl) URL.revokeObjectURL(preview.blobUrl);
    setPreview(null);
  }

  const total = data?.total_pkr ?? 0;
  const count = data?.count ?? 0;
  const yearTotal = data?.year_total_pkr ?? 0;
  const yearCount = data?.year_count ?? 0;
  const yearMonths = data?.months || [];
  const byCat = data?.by_category || {};
  const items = data?.items || [];
  let running = 0;
  const rows = items.map((it) => {
    running += Number(it.amount_pkr) || 0;
    return { ...it, running };
  });

  return (
    <div className="exp-page">
      <div className="toolbar exp-toolbar">
        <div>
          <h2 style={{ margin: 0 }}>Office Expenses</h2>
          <p className="muted page-sub">Cash out only · studio running costs · Asia/Karachi</p>
        </div>
        <div className="exp-toolbar-actions">
          <div className="exp-month-nav" role="group" aria-label="Month">
            <button type="button" className="exp-month-btn" onClick={() => shiftMonth(-1)} aria-label="Previous month">
              ‹
            </button>
            <span className="exp-month-label">{monthLabel(year, month)}</span>
            <button type="button" className="exp-month-btn" onClick={() => shiftMonth(1)} aria-label="Next month">
              ›
            </button>
          </div>
          {showForm ? (
            <button type="button" className="btn-ghost" onClick={() => closeForm(true)}>
              Close form
            </button>
          ) : (
            <button type="button" className="exp-add-btn" onClick={openForm}>
              + Add expense
            </button>
          )}
        </div>
      </div>

      <div className="exp-summary">
        <article className="card exp-total-card">
          <p className="exp-kicker">Total spent — {monthLabel(year, month)}</p>
          <p className="exp-total-num">{formatPkr(total)}</p>
          <p className="muted">
            {count} {count === 1 ? "entry" : "entries"} this month
          </p>
        </article>
        <article className="card exp-total-card exp-year-card">
          <p className="exp-kicker">Year total — {year}</p>
          <p className="exp-total-num">{formatPkr(yearTotal)}</p>
          <p className="muted">
            {yearCount} {yearCount === 1 ? "entry" : "entries"} across all months
          </p>
        </article>
        <article className="card exp-cat-card">
          <p className="exp-kicker">By category (this month)</p>
          {count === 0 ? (
            <p className="muted">Nothing recorded for this month yet.</p>
          ) : (
            <ul className="exp-cat-list">
              {EXPENSE_CATEGORIES.map((c) => {
                const amt = Number(byCat[c.id] || 0);
                if (amt <= 0) return null;
                const pct = total > 0 ? Math.min(100, (amt / total) * 100) : 0;
                return (
                  <li key={c.id}>
                    <div className="exp-cat-row">
                      <span>
                        <i className="exp-dot" style={{ background: CAT_COLORS[c.id] }} />
                        {c.label}
                      </span>
                      <b>{formatPkr(amt)}</b>
                    </div>
                    <div className="exp-cat-bar">
                      <span style={{ width: `${pct}%`, background: CAT_COLORS[c.id] }} />
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </article>
      </div>

      <section className="card exp-year-sheet">
        <div className="exp-sheet-head">
          <h3 style={{ margin: 0 }}>{year} — month by month</h3>
          <span className="muted">Every month’s total stays saved. Jump to any month below.</span>
        </div>
        <div className="exp-year-grid">
          {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => {
            const bucket = yearMonths.find((x) => x.month === m);
            const cur = todayParts();
            const future = year > cur.y || (year === cur.y && m > cur.m);
            const active = m === month;
            return (
              <button
                key={m}
                type="button"
                className={`exp-year-cell${active ? " is-active" : ""}${bucket ? " has-data" : ""}`}
                disabled={future}
                onClick={() => {
                  if (!future) setMonth(m);
                }}
              >
                <span className="exp-year-m">{MONTH_SHORT[m - 1]}</span>
                <strong>{bucket ? formatPkr(bucket.total_pkr) : "—"}</strong>
                <small>{bucket ? `${bucket.count} ${bucket.count === 1 ? "entry" : "entries"}` : "empty"}</small>
              </button>
            );
          })}
        </div>
        <div className="exp-month-footer exp-year-footer">
          <span>{year} grand total</span>
          <strong>{formatPkr(yearTotal)}</strong>
        </div>
      </section>

      {showForm ? (
        <form ref={formRef} className="card exp-form" onSubmit={onSave} id="exp-new-form">
          <h3 style={{ marginTop: 0 }}>New expense</h3>
          <div className="exp-form-grid">
            <div className="field">
              <label htmlFor="exp-date">Date</label>
              <input
                id="exp-date"
                type="date"
                required
                max={now.todayISO}
                value={spentOn}
                onChange={(e) => setSpentOn(e.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="exp-cat">Category</label>
              <select id="exp-cat" value={category} onChange={(e) => setCategory(e.target.value)} required>
                {EXPENSE_CATEGORIES.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="exp-amt">Amount (PKR)</label>
              <input
                id="exp-amt"
                inputMode="decimal"
                required
                placeholder="12,500"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="exp-note">Vendor / note</label>
              <input
                id="exp-note"
                maxLength={300}
                placeholder="IESCO bill, office chai…"
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
            </div>
          </div>
          <div className="field">
            <label htmlFor="exp-receipt">Receipt file (optional)</label>
            <div className="exp-receipt-row">
              <input
                ref={fileRef}
                id="exp-receipt"
                type="file"
                accept=".jpg,.jpeg,.png,.webp,.pdf,image/jpeg,image/png,image/webp,application/pdf"
                onChange={(e) => {
                  const f = e.target.files?.[0] || null;
                  if (f && f.size > 5 * 1024 * 1024) {
                    toast.error("Receipt max size is 5 MB.");
                    e.target.value = "";
                    setReceiptFile(null);
                    return;
                  }
                  setReceiptFile(f);
                  if (f) toast.success(`Selected: ${shortFileName(f.name)}`);
                }}
              />
              {receiptFile ? (
                <button
                  type="button"
                  className="btn-ghost"
                  onClick={() => {
                    setReceiptFile(null);
                    if (fileRef.current) fileRef.current.value = "";
                    toast.success("Receipt cleared.");
                  }}
                >
                  Clear
                </button>
              ) : null}
            </div>
            {receiptFile ? (
              <p className="exp-file-picked muted" style={{ margin: "8px 0 0", fontSize: 13 }}>
                Selected: <strong style={{ color: "var(--accent)" }}>{shortFileName(receiptFile.name, 48)}</strong>
                {" · "}
                {(receiptFile.size / 1024).toFixed(0)} KB
              </p>
            ) : (
              <p className="muted" style={{ margin: "6px 0 0", fontSize: 13 }}>
                Choose a photo or PDF (max 5 MB). Stored with this expense.
              </p>
            )}
          </div>
          <div className="exp-form-actions">
            <button type="button" className="btn-ghost" onClick={() => closeForm(true)} disabled={saving}>
              Cancel
            </button>
            <button type="submit" className="exp-add-btn" disabled={saving}>
              {saving ? "Saving…" : "Save expense"}
            </button>
          </div>
        </form>
      ) : null}

      <section className="card exp-sheet">
        <div className="exp-sheet-head">
          <h3 style={{ margin: 0 }}>Month sheet — {monthLabel(year, month)}</h3>
          {busy ? <span className="muted">Loading…</span> : null}
        </div>
        <div className="exp-filters" role="tablist" aria-label="Filter by category">
          <button
            type="button"
            className={`exp-chip${!filter ? " is-active" : ""}`}
            onClick={() => setFilter("")}
          >
            This month
          </button>
          {EXPENSE_CATEGORIES.map((c) => (
            <button
              key={c.id}
              type="button"
              className={`exp-chip${filter === c.id ? " is-active" : ""}`}
              onClick={() => setFilter(c.id)}
            >
              {c.label}
            </button>
          ))}
        </div>

        {rows.length === 0 ? (
          <div className="exp-empty">
            <p>
              {filter
                ? `No “${catLabel(filter)}” expenses in ${monthLabel(year, month)}. Try “This month” or another month above.`
                : `No expenses recorded for ${monthLabel(year, month)} yet. Older months stay saved — use ‹ › or the year grid.`}
            </p>
          </div>
        ) : (
          <div className="exp-table-wrap">
            <table className="exp-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Category</th>
                  <th>Note / receipt</th>
                  <th>Amount</th>
                  <th>Running</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id}>
                    <td data-label="Date">{formatShortDate(r.spent_on)}</td>
                    <td data-label="Category">
                      <span className="exp-cat-cell">
                        <i className="exp-dot" style={{ background: CAT_COLORS[r.category] || "#a3a3a3" }} />
                        {catLabel(r.category)}
                      </span>
                    </td>
                    <td data-label="Note / receipt">
                      <span className="exp-note-cell">
                        {r.vendor_note || "—"}
                        {r.receipt_url ? (
                          <button
                            type="button"
                            className="exp-file-link"
                            disabled={previewBusy}
                            title={r.receipt_name || "Open receipt"}
                            onClick={() => viewReceipt(r.receipt_url!, r.receipt_name || "receipt")}
                          >
                            {shortFileName(r.receipt_name || "Receipt", 40)}
                          </button>
                        ) : r.receipt_name ? (
                          <small className="exp-receipt">{r.receipt_name}</small>
                        ) : null}
                      </span>
                    </td>
                    <td data-label="Amount">{formatPkr(r.amount_pkr)}</td>
                    <td data-label="Running">{formatPkr(r.running)}</td>
                    <td data-label="">
                      <button
                        type="button"
                        className="btn-danger btn-row-del"
                        onClick={() => setPendingDelete(r.id)}
                        aria-label="Delete expense"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="exp-month-footer">
              <span>Month total</span>
              <strong>{formatPkr(total)}</strong>
            </div>
          </div>
        )}
      </section>

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title="Remove expense?"
        message="This removes the row from the month sheet. You cannot undo."
        confirmLabel="Remove"
        busy={deleting}
        onCancel={() => setPendingDelete(null)}
        onConfirm={confirmDelete}
      />

      {preview
        ? createPortal(
            <div
              className="exp-receipt-modal"
              role="dialog"
              aria-modal="true"
              aria-label="Receipt preview"
              onClick={closePreview}
            >
              <div className="exp-receipt-dialog" onClick={(e) => e.stopPropagation()}>
                <div className="exp-receipt-dialog-head">
                  <h3 title={preview.name}>{shortFileName(preview.name, 48)}</h3>
                  <button type="button" className="btn-ghost" onClick={closePreview}>
                    Close
                  </button>
                </div>
                <div className="exp-receipt-dialog-body">
                  {preview.kind === "IMG" ? (
                    <img src={preview.blobUrl} alt={preview.name} />
                  ) : preview.kind === "PDF" ? (
                    <iframe title={preview.name} src={preview.blobUrl} />
                  ) : (
                    <p className="muted">Preview not available for this file type. Use Download.</p>
                  )}
                </div>
                <div className="exp-receipt-dialog-foot">
                  <button
                    type="button"
                    className="exp-rcpt-dl"
                    onClick={() => downloadReceipt(preview.url, preview.name)}
                  >
                    Download
                  </button>
                  <button type="button" className="exp-add-btn" onClick={closePreview}>
                    Done
                  </button>
                </div>
              </div>
            </div>,
            document.body
          )
        : null}
    </div>
  );
}
