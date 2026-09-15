import { useEffect, useMemo, useState, type MouseEvent as ReactMouseEvent } from "react";
import { createPortal } from "react-dom";
import {
  deleteInvoice,
  fetchAuthedBlob,
  fetchClients,
  fetchInvoiceSettings,
  fetchInvoices,
  fetchProjects,
  saveInvoice,
  saveInvoiceSettings,
  triggerBlobDownload,
  type ClientRow,
  type InvoiceLineItem,
  type InvoiceRow,
  type InvoiceSettings,
  type ProjectRow,
} from "../api";
import { CellColorPicker } from "../components/CellColorPicker";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { CurrencySelect } from "../components/CurrencySelect";
import { PdfPreviewModal } from "../components/PdfPreviewModal";
import { RefreshButton } from "../components/RefreshButton";
import { useToast } from "../components/ToastProvider";
import { formatMoney, guessCurrencyFromLocation, normalizeCurrencyCode } from "../components/currencies";
import {
  INVOICE_PREP,
  invoicePrepLabel,
  invoicePrepTextClass,
  invoiceStatusLabel,
  invoiceStatusTextClass,
} from "../components/invoiceStatus";

const STATUSES = ["proforma", "sent", "pending", "paid", "overdue", "info_sent", "unpaid_info"];

type Tab = "invoices" | "template";

type FormState = {
  client_id: string;
  project_id: string;
  number: string;
  amount: string;
  currency: string;
  invoice_date: string;
  follow_up_at: string;
  status: string;
  kind: string;
  invoice_prep: string;
  client_comments: string;
  bill_to_name: string;
  bill_to_location: string;
  bill_to_phone: string;
  line_items: InvoiceLineItem[];
  invoice_notes: string;
};

const emptyLine = (): InvoiceLineItem => ({
  description: "",
  scope: "",
  qty: 1,
  unit_price: 0,
  area: "",
  rate: "",
  comments: "",
  unpaid: false,
  cell_colors: {},
});

const emptyForm: FormState = {
  client_id: "",
  project_id: "",
  number: "",
  amount: "",
  currency: "USD",
  invoice_date: "",
  follow_up_at: "",
  status: "pending",
  kind: "deposit",
  invoice_prep: "unprepared",
  client_comments: "",
  bill_to_name: "",
  bill_to_location: "",
  bill_to_phone: "",
  line_items: [emptyLine()],
  invoice_notes: "",
};

const emptySettings: InvoiceSettings = {
  issuer_name: "",
  issuer_address: "",
  issuer_phone: "",
  issuer_email: "",
  bank_title: "USD Account Details:",
  bank_intro: "",
  bank_account_name: "",
  bank_account_number: "",
  bank_account_type: "",
  bank_routing: "",
  bank_swift: "",
  bank_name_address: "",
  contact_name: "",
  contact_email: "",
  footer_thanks: "THANK YOU FOR YOUR BUSINESS!",
  header_color: "#92D050",
  highlight_color: "#A85914",
};

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

function parseNum(v: string | number | undefined | null): number | null {
  if (v === undefined || v === null || v === "") return null;
  const n = Number(String(v).replace(/[$,]/g, "").trim());
  return Number.isFinite(n) ? n : null;
}

function lineAmount(row: InvoiceLineItem): number {
  const a = parseNum(row.area ?? row.qty);
  const r = parseNum(row.rate ?? row.unit_price);
  if (a != null && r != null) return a * r;
  return Number(row.unit_price) || 0;
}

function lineTotal(items: InvoiceLineItem[]): number {
  return items.reduce((sum, row) => sum + lineAmount(row), 0);
}

function fillBillTo(client: ClientRow | undefined, prev: FormState): FormState {
  if (!client) return prev;
  return {
    ...prev,
    bill_to_name: client.name || "",
    bill_to_location: client.location || "",
    bill_to_phone: client.phone || "",
  };
}

export function PaymentsPage() {
  const toast = useToast();
  const [tab, setTab] = useState<Tab>("invoices");
  const [rows, setRows] = useState<InvoiceRow[]>([]);
  const [clients, setClients] = useState<ClientRow[]>([]);
  const [projects, setProjects] = useState<ProjectRow[]>([]);
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [settings, setSettings] = useState<InvoiceSettings>(emptySettings);
  const [settingsBusy, setSettingsBusy] = useState(false);
  const [q, setQ] = useState("");
  const [pendingDelete, setPendingDelete] = useState<InvoiceRow | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [pdfPreview, setPdfPreview] = useState<{ url: string; title: string } | null>(null);
  const [actionsMenu, setActionsMenu] = useState<{
    id: string;
    top: number;
    left: number;
  } | null>(null);

  useEffect(() => {
    if (!actionsMenu) return;
    function onDoc(e: globalThis.MouseEvent) {
      const t = e.target as HTMLElement | null;
      if (t?.closest?.(".payments-actions-menu")) return;
      if (t?.closest?.(".payments-actions-dropdown-fixed")) return;
      setActionsMenu(null);
    }
    function onScroll() {
      setActionsMenu(null);
    }
    document.addEventListener("mousedown", onDoc);
    window.addEventListener("scroll", onScroll, true);
    window.addEventListener("resize", onScroll);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      window.removeEventListener("scroll", onScroll, true);
      window.removeEventListener("resize", onScroll);
    };
  }, [actionsMenu]);

  function toggleActionsMenu(e: ReactMouseEvent<HTMLButtonElement>, id: string) {
    e.stopPropagation();
    if (actionsMenu?.id === id) {
      setActionsMenu(null);
      return;
    }
    const rect = e.currentTarget.getBoundingClientRect();
    const menuW = 156;
    const menuH = 180;
    let left = rect.right - menuW;
    if (left < 8) left = 8;
    if (left + menuW > window.innerWidth - 8) left = window.innerWidth - menuW - 8;
    let top = rect.bottom + 6;
    if (top + menuH > window.innerHeight - 8) {
      top = Math.max(8, rect.top - menuH - 6);
    }
    setActionsMenu({ id, top, left });
  }

  function closeActionsMenu() {
    setActionsMenu(null);
  }

  const computedTotal = useMemo(() => lineTotal(form.line_items), [form.line_items]);

  async function load() {
    setBusy(true);
    try {
      const [inv, c, p, tpl] = await Promise.all([
        fetchInvoices(),
        fetchClients(),
        fetchProjects(),
        fetchInvoiceSettings(),
      ]);
      setRows(inv);
      setClients(c);
      setProjects(p);
      setSettings(tpl);
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
        const [inv, c, p, tpl] = await Promise.all([
          fetchInvoices(),
          fetchClients(),
          fetchProjects(),
          fetchInvoiceSettings(),
        ]);
        if (cancelled) return;
        setRows(inv);
        setClients(c);
        setProjects(p);
        setSettings(tpl);
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
      setForm({ ...emptyForm, line_items: [emptyLine()] });
      setTab("invoices");
      return;
    }
    setEditing(r.id);
    const items =
      r.line_items && Array.isArray(r.line_items) && r.line_items.length > 0
        ? r.line_items.map((row) => ({
            description: String(row.description || ""),
            scope: String(row.scope || ""),
            qty: Number(row.qty) || 1,
            unit_price: Number(row.unit_price) || 0,
            area: String(row.area ?? (row.qty != null ? String(row.qty) : "")),
            rate: String(row.rate ?? (row.unit_price != null ? String(row.unit_price) : "")),
            comments: String(row.comments || ""),
            unpaid: Boolean(row.unpaid),
            cell_colors: { ...(row.cell_colors || {}) },
          }))
        : [{ ...emptyLine(), description: "Services", qty: 1, unit_price: Number(r.amount) || 0, area: "", rate: String(Number(r.amount) || 0) }];

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
      invoice_prep: (r.invoice_prep || "unprepared").toLowerCase(),
      client_comments: r.client_comments || "",
      bill_to_name: r.bill_to_name || r.client_name || "",
      bill_to_location: r.bill_to_location || r.location || "",
      bill_to_phone: r.bill_to_phone || "",
      line_items: items,
      invoice_notes: r.invoice_notes || "",
    });
    setTab("invoices");
  }

  function updateLineItem(index: number, patch: Partial<InvoiceLineItem>) {
    setForm((prev) => {
      const next = [...prev.line_items];
      next[index] = {
        description: String(next[index]?.description || ""),
        scope: String(next[index]?.scope || ""),
        qty: Number(next[index]?.qty) || 1,
        unit_price: Number(next[index]?.unit_price) || 0,
        area: String(next[index]?.area || ""),
        rate: String(next[index]?.rate || ""),
        comments: String(next[index]?.comments || ""),
        unpaid: Boolean(next[index]?.unpaid),
        cell_colors: { ...(next[index]?.cell_colors || {}) },
        ...patch,
      };
      return { ...prev, line_items: next };
    });
  }

  function setCellColor(
    index: number,
    key: "project" | "scope" | "area" | "rate" | "cost",
    hex: string,
  ) {
    setForm((prev) => {
      const next = [...prev.line_items];
      const row = next[index];
      if (!row) return prev;
      const colors = { ...(row.cell_colors || {}) };
      const cleaned = (hex || "").trim().toUpperCase();
      if (!cleaned) delete colors[key];
      else colors[key] = cleaned;
      next[index] = {
        ...row,
        cell_colors: colors,
        unpaid: key === "cost" && cleaned === "#7A1F2E" ? true : row.unpaid,
      };
      return { ...prev, line_items: next };
    });
  }

  function addLineItem() {
    setForm((prev) => ({ ...prev, line_items: [...prev.line_items, emptyLine()] }));
  }

  function removeLineItem(index: number) {
    setForm((prev) => {
      const next = prev.line_items.filter((_, i) => i !== index);
      return { ...prev, line_items: next.length ? next : [emptyLine()] };
    });
  }

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    
    // Frontend validation
    if (!form.client_id?.trim()) {
      toast.error("Please select a client");
      return;
    }
    if (!form.number?.trim()) {
      toast.error("Invoice number is required");
      return;
    }
    
    const validLines = form.line_items.filter((row) => {
      const desc = String(row.description || "").trim();
      return desc.length > 0;
    });
    
    if (!validLines.length) {
      toast.error("Add at least one line item with a description");
      return;
    }

    // Validate each line
    for (let i = 0; i < validLines.length; i++) {
      const row = validLines[i];
      const areaNum = parseNum(row.area);
      const rateNum = parseNum(row.rate);
      if (areaNum != null && areaNum <= 0) {
        toast.error(`Line ${i + 1}: Area must be greater than 0`);
        return;
      }
      if (rateNum != null && rateNum < 0) {
        toast.error(`Line ${i + 1}: Rate cannot be negative`);
        return;
      }
      if (areaNum == null && rateNum == null && (Number(row.unit_price) || 0) < 0) {
        toast.error(`Line ${i + 1}: COST cannot be negative`);
        return;
      }
    }

    try {
      const payload = {
        client_id: form.client_id.trim(),
        project_id: form.project_id?.trim() || null,
        number: form.number.trim(),
        amount: computedTotal || 0,
        currency: normalizeCurrencyCode(form.currency),
        invoice_date: form.invoice_date ? `${form.invoice_date}T12:00:00` : null,
        follow_up_at: form.follow_up_at ? `${form.follow_up_at}T12:00:00` : null,
        status: form.status,
        kind: form.kind,
        invoice_prep: form.invoice_prep || "unprepared",
        client_comments: form.client_comments.trim(),
        bill_to_name: form.bill_to_name.trim(),
        bill_to_location: form.bill_to_location.trim(),
        bill_to_phone: form.bill_to_phone.trim(),
        line_items: validLines.map((row) => {
          const areaNum = parseNum(row.area);
          const rateNum = parseNum(row.rate);
          const amt = lineAmount(row);
          return {
            description: String(row.description).trim(),
            scope: String(row.scope || "").trim(),
            qty: areaNum != null && areaNum > 0 ? areaNum : 1,
            unit_price: areaNum != null && rateNum != null ? rateNum : amt,
            area: String(row.area || "").trim(),
            rate: String(row.rate || "").trim(),
            comments: String(row.comments || "").trim(),
            unpaid: Boolean(row.unpaid),
            cell_colors: Object.fromEntries(
              Object.entries(row.cell_colors || {}).filter(([, v]) => Boolean(v && String(v).trim())),
            ),
          };
        }),
        invoice_notes: form.invoice_notes.trim(),
      };
      
      await saveInvoice(payload, editing && editing !== "new" ? editing : undefined);
      setEditing(null);
      toast.success(editing === "new" ? "Invoice created successfully" : "Invoice updated successfully");
      await load();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to save invoice";
      toast.error(msg);
      console.error("Invoice save error:", err);
    }
  }

  async function onSaveSettings(e: React.FormEvent) {
    e.preventDefault();
    setSettingsBusy(true);
    try {
      const saved = await saveInvoiceSettings(settings);
      setSettings(saved);
      toast.success("Invoice template saved.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSettingsBusy(false);
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
    const res = await fetchAuthedBlob("/api/v1/reports/payments.xlsx");
    if ("error" in res) {
      toast.error(res.error || "Excel download failed");
      return;
    }
    triggerBlobDownload(res.blob, "CFS_Payments_Tracking.xlsx");
  }

  async function downloadInvoicePdf(inv: InvoiceRow, inline = false) {
    const qs = inline ? "?inline=1" : "";
    const res = await fetchAuthedBlob(`/api/v1/invoices/${inv.id}/pdf${qs}`);
    if ("error" in res) {
      toast.error(res.error || "Invoice PDF failed");
      return;
    }
    if (inline) {
      if (pdfPreview?.url) URL.revokeObjectURL(pdfPreview.url);
      setPdfPreview({
        url: URL.createObjectURL(res.blob),
        title: `Invoice ${inv.number || inv.id}`,
      });
      return;
    }
    triggerBlobDownload(res.blob, `CFS_Invoice_${inv.number || inv.id}.pdf`);
  }

  async function downloadInvoiceXlsx(inv: InvoiceRow) {
    const res = await fetchAuthedBlob(`/api/v1/invoices/${inv.id}/xlsx`);
    if ("error" in res) {
      toast.error(res.error || "Invoice Excel download failed");
      return;
    }
    triggerBlobDownload(res.blob, `CFS_Invoice_${inv.number || inv.id}.xlsx`);
  }

  function closePdfPreview() {
    if (pdfPreview?.url) URL.revokeObjectURL(pdfPreview.url);
    setPdfPreview(null);
  }

  return (
    <div>
      {actionsMenu
        ? createPortal(
            <div
              className="payments-actions-dropdown-fixed"
              role="menu"
              style={{ top: actionsMenu.top, left: actionsMenu.left }}
            >
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  const inv = rows.find((x) => x.id === actionsMenu.id);
                  closeActionsMenu();
                  if (inv) downloadInvoicePdf(inv, true);
                }}
              >
                View
              </button>
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  const inv = rows.find((x) => x.id === actionsMenu.id);
                  closeActionsMenu();
                  if (inv) downloadInvoicePdf(inv, false);
                }}
              >
                PDF
              </button>
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  const inv = rows.find((x) => x.id === actionsMenu.id);
                  closeActionsMenu();
                  if (inv) downloadInvoiceXlsx(inv);
                }}
              >
                Excel
              </button>
              <button
                type="button"
                role="menuitem"
                className="is-danger"
                onClick={() => {
                  const inv = rows.find((x) => x.id === actionsMenu.id);
                  closeActionsMenu();
                  if (inv) setPendingDelete(inv);
                }}
              >
                Delete
              </button>
            </div>,
            document.body
          )
        : null}
      <PdfPreviewModal
        open={Boolean(pdfPreview)}
        title={pdfPreview?.title}
        blobUrl={pdfPreview?.url || null}
        onClose={closePdfPreview}
      />
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

      <div className="toolbar payments-toolbar">
        <h2>Payments &amp; invoices</h2>
        {tab === "invoices" ? (
          <input
            placeholder="Search client, invoice, status…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        ) : null}
        <div className="payments-tabs" role="tablist">
          <button
            type="button"
            role="tab"
            className={tab === "invoices" ? "active" : ""}
            aria-selected={tab === "invoices"}
            onClick={() => setTab("invoices")}
          >
            Invoices
          </button>
          <button
            type="button"
            role="tab"
            className={tab === "template" ? "active" : ""}
            aria-selected={tab === "template"}
            onClick={() => setTab("template")}
          >
            Template settings
          </button>
        </div>
        {tab === "invoices" ? (
          <>
            <button type="button" className="secondary" onClick={downloadXlsx}>
              Download Excel
            </button>
            <button type="button" className="secondary" onClick={() => startEdit()}>
              + New invoice
            </button>
          </>
        ) : null}
        <RefreshButton busy={busy} onClick={() => load()} />
      </div>

      {tab === "invoices" ? (
        <>

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
            <form className="card invoice-form" onSubmit={onSave}>
              <h3 style={{ marginTop: 0 }}>{editing === "new" ? "New invoice" : "Edit invoice"}</h3>

              <div className="invoice-form-grid">
                <div className="field">
                  <label>Client</label>
                  <select
                    required
                    value={form.client_id}
                    onChange={(e) => {
                      const clientId = e.target.value;
                      const client = clients.find((c) => c.id === clientId);
                      let next = { ...form, client_id: clientId };
                      if (client) {
                        if (editing === "new") {
                          next.currency = guessCurrencyFromLocation(client.location);
                        }
                        next = fillBillTo(client, next);
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
                    {projects
                      .filter((p) => !form.client_id || p.client_id === form.client_id)
                      .map((p) => (
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
                  <label>Currency</label>
                  <CurrencySelect value={form.currency} onChange={(currency) => setForm({ ...form, currency })} required />
                </div>
                <div className="field">
                  <label>Invoice date</label>
                  <input
                    type="date"
                    value={form.invoice_date}
                    onChange={(e) => setForm({ ...form, invoice_date: e.target.value })}
                  />
                </div>
                <div className="field">
                  <label>FOLLOW UP DATE</label>
                  <input
                    type="date"
                    value={form.follow_up_at}
                    onChange={(e) => setForm({ ...form, follow_up_at: e.target.value })}
                  />
                </div>
                <div className="field">
                  <label>INVOICE</label>
                  <select
                    value={form.invoice_prep}
                    onChange={(e) => setForm({ ...form, invoice_prep: e.target.value })}
                  >
                    {INVOICE_PREP.map((s) => (
                      <option key={s} value={s}>
                        {invoicePrepLabel(s)}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label>INVOICE STATUS</label>
                  <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {invoiceStatusLabel(s)}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label>Kind</label>
                  <select value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
                    <option value="deposit">Deposit</option>
                    <option value="balance">Balance</option>
                    <option value="progress">Progress</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              <fieldset className="invoice-fieldset">
                <legend>Invoice To (editable)</legend>
                <div className="invoice-form-grid">
                  <div className="field">
                    <label>Name</label>
                    <input
                      value={form.bill_to_name}
                      onChange={(e) => setForm({ ...form, bill_to_name: e.target.value })}
                      placeholder="Client name on invoice"
                    />
                  </div>
                  <div className="field">
                    <label>Location / country</label>
                    <input
                      value={form.bill_to_location}
                      onChange={(e) => setForm({ ...form, bill_to_location: e.target.value })}
                      placeholder="e.g. USA"
                    />
                  </div>
                  <div className="field">
                    <label>Phone</label>
                    <input
                      value={form.bill_to_phone}
                      onChange={(e) => setForm({ ...form, bill_to_phone: e.target.value })}
                      placeholder="+1 …"
                    />
                  </div>
                </div>
              </fieldset>

              <fieldset className="invoice-fieldset">
                <legend>Line items</legend>
                <div className="invoice-line-items-wrap">
                  <table className="invoice-line-items">
                    <thead>
                      <tr>
                        <th className="col-sno">S/No</th>
                        <th>Project Name</th>
                        <th>Scope of Work</th>
                        <th className="col-qty">Area</th>
                        <th className="col-rate">$ / sq.ft</th>
                        <th className="col-amt">COST ($)</th>
                        <th className="col-unpaid">Unpaid</th>
                        <th className="col-del" aria-label="Remove" />
                      </tr>
                    </thead>
                    <tbody>
                      {form.line_items.map((row, i) => {
                        const amt = lineAmount(row);
                        const numeric = parseNum(row.area) != null && parseNum(row.rate) != null;
                        const cc = row.cell_colors || {};
                        return (
                          <tr key={i} className={row.unpaid ? "line-unpaid" : undefined}>
                            <td className="col-sno">{i + 1}</td>
                            <td>
                              <div className="cell-with-color">
                                <input
                                  required
                                  value={row.description}
                                  onChange={(e) => updateLineItem(i, { description: e.target.value })}
                                  placeholder="Project name"
                                  style={cc.project ? { background: cc.project } : undefined}
                                />
                                <CellColorPicker
                                  label="Project"
                                  value={cc.project}
                                  onChange={(hex) => setCellColor(i, "project", hex)}
                                />
                              </div>
                            </td>
                            <td>
                              <div className="cell-with-color">
                                <input
                                  value={row.scope || ""}
                                  onChange={(e) => updateLineItem(i, { scope: e.target.value })}
                                  placeholder="Estimation / Detailing"
                                  style={cc.scope ? { background: cc.scope } : undefined}
                                />
                                <CellColorPicker
                                  label="Scope"
                                  value={cc.scope}
                                  onChange={(hex) => setCellColor(i, "scope", hex)}
                                />
                              </div>
                            </td>
                            <td>
                              <div className="cell-with-color">
                                <input
                                  value={row.area ?? ""}
                                  onChange={(e) => updateLineItem(i, { area: e.target.value })}
                                  placeholder="309 or LumpSum"
                                  style={cc.area ? { background: cc.area } : undefined}
                                />
                                <CellColorPicker
                                  label="Area"
                                  value={cc.area}
                                  onChange={(hex) => setCellColor(i, "area", hex)}
                                />
                              </div>
                            </td>
                            <td>
                              <div className="cell-with-color">
                                <input
                                  value={row.rate ?? ""}
                                  onChange={(e) => updateLineItem(i, { rate: e.target.value })}
                                  placeholder="0.4 or LumpSum"
                                  style={cc.rate ? { background: cc.rate } : undefined}
                                />
                                <CellColorPicker
                                  label="Rate"
                                  value={cc.rate}
                                  onChange={(hex) => setCellColor(i, "rate", hex)}
                                />
                              </div>
                            </td>
                            <td
                              className={`col-amt${
                                row.unpaid && !(cc.cost && cc.cost.toUpperCase() !== "#7A1F2E") ? " cell-unpaid" : ""
                              }`}
                              style={cc.cost ? { background: cc.cost, color: cc.cost.toUpperCase() === "#7A1F2E" ? "#fff" : undefined } : undefined}
                            >
                              <div className="cell-with-color">
                                {numeric ? (
                                  <span className="cell-amt-text">{formatMoney(amt, form.currency)}</span>
                                ) : (
                                  <input
                                    type="number"
                                    min={0}
                                    step="0.01"
                                    value={row.unit_price || ""}
                                    onChange={(e) => {
                                      const val = e.target.value;
                                      updateLineItem(i, { unit_price: val === "" ? 0 : Number(val) });
                                    }}
                                    placeholder="COST"
                                  />
                                )}
                                <CellColorPicker
                                  label="COST"
                                  value={cc.cost}
                                  onChange={(hex) => setCellColor(i, "cost", hex)}
                                />
                              </div>
                            </td>
                            <td className="col-unpaid">
                              <label className="unpaid-check">
                                <input
                                  type="checkbox"
                                  checked={Boolean(row.unpaid)}
                                  onChange={(e) => {
                                    const on = e.target.checked;
                                    const colors = { ...(row.cell_colors || {}) };
                                    if (on) colors.cost = "#7A1F2E";
                                    else if ((colors.cost || "").toUpperCase() === "#7A1F2E") delete colors.cost;
                                    updateLineItem(i, { unpaid: on, cell_colors: colors });
                                  }}
                                />
                                Maroon
                              </label>
                            </td>
                            <td className="col-del">
                              <button
                                type="button"
                                className="btn-danger btn-row-del"
                                onClick={() => removeLineItem(i)}
                                aria-label="Remove line"
                                disabled={form.line_items.length === 1}
                              >
                                ×
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                    <tfoot>
                      <tr>
                        <td colSpan={5} className="total-label">
                          TOTAL BUDGET
                        </td>
                        <td className="col-amt total-value">{formatMoney(computedTotal, form.currency)}</td>
                        <td colSpan={2} />
                      </tr>
                    </tfoot>
                  </table>
                </div>
                <button type="button" className="secondary" onClick={addLineItem}>
                  + Add line item
                </button>
                <p className="line-hint">
                  Paint any cell: click the small color chip on Project / Scope / Area / Rate / COST — Yellow for Detailing (like the client PDF), Maroon for unpaid COST, or any custom color. PDF matches your picks.
                </p>

              <div className="invoice-notes-block">
                <div className="field field-full-width">
                  <label>Notes (not printed on PDF)</label>
                  <textarea
                    rows={3}
                    style={{ width: "100%", display: "block", boxSizing: "border-box" }}
                    value={form.invoice_notes}
                    onChange={(e) => setForm({ ...form, invoice_notes: e.target.value })}
                    placeholder="Not printed — internal only"
                  />
                </div>
                <div className="field field-full-width">
                  <label>Internal comments (tracking only)</label>
                  <textarea
                    rows={3}
                    style={{ width: "100%", display: "block", boxSizing: "border-box" }}
                    value={form.client_comments}
                    onChange={(e) => setForm({ ...form, client_comments: e.target.value })}
                    placeholder="Not printed on PDF — internal use only"
                  />
                </div>
              </div>
              </fieldset>

              <div className="toolbar">
                <button type="submit">Save invoice</button>
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
                  <th className="col-client">
                    <span className="th-inline">CLIENT NAME</span>
                    <span className="th-stack">CLIENT<br />NAME</span>
                  </th>
                  <th className="col-location">LOCATION</th>
                  <th className="col-project">Project</th>
                  <th className="col-invoice">INVOICE</th>
                  <th className="col-money">
                    <span className="th-inline">INVOICE VALUE</span>
                    <span className="th-stack">INVOICE<br />VALUE</span>
                  </th>
                  <th className="col-date">
                    <span className="th-inline">INVOICE DATE</span>
                    <span className="th-stack">INVOICE<br />DATE</span>
                  </th>
                  <th className="col-date">
                    <span className="th-inline">FOLLOW UP DATE</span>
                    <span className="th-stack">FOLLOW UP<br />DATE</span>
                  </th>
                  <th className="col-days">
                    <span className="th-inline">INVOICE DELAYED (DAYS)</span>
                    <span className="th-stack">DELAYED<br />(DAYS)</span>
                  </th>
                  <th className="col-status">
                    <span className="th-inline">INVOICE STATUS</span>
                    <span className="th-stack">INVOICE<br />STATUS</span>
                  </th>
                  <th className="col-comments">
                    <span className="th-inline">Comments From Clients</span>
                    <span className="th-stack">Comments<br />From Clients</span>
                  </th>
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
                      <span className="cell-text">{r.bill_to_location || r.location || "—"}</span>
                    </td>
                    <td className="col-project" onClick={() => startEdit(r)}>
                      <span className="cell-text">{r.project_name || "—"}</span>
                    </td>
                    <td className="col-invoice" onClick={() => startEdit(r)}>
                      <span className={invoicePrepTextClass(r.invoice_prep || "unprepared")}>
                        {invoicePrepLabel(r.invoice_prep || "unprepared")}
                      </span>
                      <div className="muted" style={{ fontSize: 11, marginTop: 2 }}>
                        #{r.number}
                      </div>
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
                    <td className="col-actions" onClick={(e) => e.stopPropagation()}>
                      <div className="row-actions payments-actions-full">
                        <button
                          type="button"
                          className="secondary btn-row"
                          onClick={() => downloadInvoicePdf(r, true)}
                        >
                          View
                        </button>
                        <button
                          type="button"
                          className="secondary btn-row"
                          onClick={() => downloadInvoicePdf(r, false)}
                        >
                          PDF
                        </button>
                        <button
                          type="button"
                          className="secondary btn-row"
                          onClick={() => downloadInvoiceXlsx(r)}
                        >
                          Excel
                        </button>
                        <button
                          type="button"
                          className="btn-danger btn-row-del"
                          onClick={() => setPendingDelete(r)}
                        >
                          Delete
                        </button>
                      </div>
                      <div className="payments-actions-menu">
                        <button
                          type="button"
                          className="secondary btn-row payments-actions-toggle"
                          aria-expanded={actionsMenu?.id === r.id}
                          aria-haspopup="menu"
                          onClick={(e) => toggleActionsMenu(e, r.id)}
                        >
                          Actions ▾
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <form className="card invoice-settings-form" onSubmit={onSaveSettings}>
          <h3 style={{ marginTop: 0 }}>Invoice template settings</h3>
          <p className="payments-hint">
            Configure your company details, bank account info, and contact information. These details will appear on every invoice PDF you generate.
          </p>

          <fieldset className="invoice-fieldset">
            <legend>Your company (top of invoice)</legend>
            <div className="invoice-form-grid">
              <div className="field">
                <label>Name</label>
                <input
                  value={settings.issuer_name}
                  onChange={(e) => setSettings({ ...settings, issuer_name: e.target.value })}
                />
              </div>
              <div className="field">
                <label>Phone</label>
                <input
                  value={settings.issuer_phone}
                  onChange={(e) => setSettings({ ...settings, issuer_phone: e.target.value })}
                />
              </div>
              <div className="field span-2">
                <label>Address</label>
                <input
                  value={settings.issuer_address}
                  onChange={(e) => setSettings({ ...settings, issuer_address: e.target.value })}
                />
              </div>
              <div className="field">
                <label>Email</label>
                <input
                  type="email"
                  value={settings.issuer_email}
                  onChange={(e) => setSettings({ ...settings, issuer_email: e.target.value })}
                />
              </div>
            </div>
          </fieldset>

          <fieldset className="invoice-fieldset">
            <legend>Bank / payment details (bottom of invoice)</legend>
            <div className="field field-full-width">
              <label>Section title</label>
              <input
                value={settings.bank_title}
                onChange={(e) => setSettings({ ...settings, bank_title: e.target.value })}
              />
            </div>
            <div className="field field-full-width">
              <label>Transfer instructions</label>
              <textarea
                rows={3}
                value={settings.bank_intro}
                onChange={(e) => setSettings({ ...settings, bank_intro: e.target.value })}
              />
            </div>
            <div className="invoice-form-grid">
              <div className="field">
                <label>Account name</label>
                <input
                  value={settings.bank_account_name}
                  onChange={(e) => setSettings({ ...settings, bank_account_name: e.target.value })}
                />
              </div>
              <div className="field">
                <label>Account number</label>
                <input
                  value={settings.bank_account_number}
                  onChange={(e) => setSettings({ ...settings, bank_account_number: e.target.value })}
                />
              </div>
              <div className="field">
                <label>Account type</label>
                <input
                  value={settings.bank_account_type}
                  onChange={(e) => setSettings({ ...settings, bank_account_type: e.target.value })}
                />
              </div>
              <div className="field">
                <label>Routing number</label>
                <input
                  value={settings.bank_routing}
                  onChange={(e) => setSettings({ ...settings, bank_routing: e.target.value })}
                />
              </div>
              <div className="field">
                <label>Swift / BIC</label>
                <input
                  value={settings.bank_swift}
                  onChange={(e) => setSettings({ ...settings, bank_swift: e.target.value })}
                />
              </div>
              <div className="field field-full-width">
                <label>Bank name &amp; address</label>
                <textarea
                  rows={2}
                  value={settings.bank_name_address}
                  onChange={(e) => setSettings({ ...settings, bank_name_address: e.target.value })}
                />
              </div>
            </div>
          </fieldset>

          <fieldset className="invoice-fieldset">
            <legend>Contact footer</legend>
            <div className="invoice-form-grid">
              <div className="field">
                <label>Contact name</label>
                <input
                  value={settings.contact_name}
                  onChange={(e) => setSettings({ ...settings, contact_name: e.target.value })}
                />
              </div>
              <div className="field">
                <label>Contact email</label>
                <input
                  type="email"
                  value={settings.contact_email}
                  onChange={(e) => setSettings({ ...settings, contact_email: e.target.value })}
                />
              </div>
              <div className="field span-2">
                <label>Thank-you line</label>
                <input
                  value={settings.footer_thanks}
                  onChange={(e) => setSettings({ ...settings, footer_thanks: e.target.value })}
                />
              </div>
            </div>
          </fieldset>

          <fieldset className="invoice-fieldset">
            <legend>Invoice colors (PDF styling)</legend>
            <div className="invoice-form-grid">
              <div className="field">
                <label>Table header color</label>
                <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                  <input
                    type="color"
                    value={settings.header_color}
                    onChange={(e) => setSettings({ ...settings, header_color: e.target.value })}
                    style={{ width: 60, height: 40 }}
                  />
                  <input
                    type="text"
                    value={settings.header_color}
                    onChange={(e) => setSettings({ ...settings, header_color: e.target.value })}
                    placeholder="#92D050"
                    style={{ flex: 1, minWidth: 120 }}
                  />
                </div>
                <div className="color-swatches" role="group" aria-label="Header presets">
                  {[
                    ["#92D050", "Lime"],
                    ["#548235", "Green"],
                    ["#c9a227", "Gold"],
                    ["#7a1f2e", "Maroon"],
                    ["#A85914", "Copper"],
                  ].map(([hex, label]) => (
                    <button
                      key={hex}
                      type="button"
                      className={`color-swatch${settings.header_color.toLowerCase() === hex.toLowerCase() ? " is-active" : ""}`}
                      style={{ background: hex }}
                      title={label}
                      aria-label={label}
                      onClick={() => setSettings({ ...settings, header_color: hex })}
                    />
                  ))}
                </div>
              </div>
              <div className="field">
                <label>Highlight / accent color</label>
                <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                  <input
                    type="color"
                    value={settings.highlight_color}
                    onChange={(e) => setSettings({ ...settings, highlight_color: e.target.value })}
                    style={{ width: 60, height: 40 }}
                  />
                  <input
                    type="text"
                    value={settings.highlight_color}
                    onChange={(e) => setSettings({ ...settings, highlight_color: e.target.value })}
                    placeholder="#c9a227"
                    style={{ flex: 1, minWidth: 120 }}
                  />
                </div>
                <div className="color-swatches" role="group" aria-label="Highlight presets">
                  {[
                    ["#c9a227", "Gold"],
                    ["#A85914", "Copper"],
                    ["#7a1f2e", "Maroon"],
                    ["#92D050", "Lime"],
                    ["#1f3a5f", "Navy"],
                  ].map(([hex, label]) => (
                    <button
                      key={hex}
                      type="button"
                      className={`color-swatch${settings.highlight_color.toLowerCase() === hex.toLowerCase() ? " is-active" : ""}`}
                      style={{ background: hex }}
                      title={label}
                      aria-label={label}
                      onClick={() => setSettings({ ...settings, highlight_color: hex })}
                    />
                  ))}
                </div>
              </div>
            </div>
          </fieldset>

          <div className="toolbar">
            <button type="submit" disabled={settingsBusy}>
              {settingsBusy ? "Saving…" : "Save template"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
