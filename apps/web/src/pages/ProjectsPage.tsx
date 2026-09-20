import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  createClient,
  deleteProject,
  fetchClients,
  fetchEmployees,
  fetchProjectPhases,
  fetchProjectProgress,
  fetchProjects,
  postProjectProgress,
  saveProject,
  type ClientRow,
  type Employee,
  type ProjectProgressRow,
  type ProjectRow,
} from "../api";
import { useToast } from "../components/ToastProvider";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { CurrencySelect } from "../components/CurrencySelect";
import { RefreshButton } from "../components/RefreshButton";
import { formatMoney, guessCurrencyFromLocation, normalizeCurrencyCode } from "../components/currencies";

const PHASES: { id: string; label: string; short: string }[] = [
  { id: "intake", label: "Intake", short: "Intake" },
  { id: "preliminary_design", label: "Preliminary Design", short: "Prelim Design" },
  { id: "preliminary_engineering", label: "Preliminary Engineering", short: "Prelim Eng." },
  { id: "final_engineering", label: "Final Engineering", short: "Final Eng." },
  { id: "stamped_drawings", label: "Stamped Drawings", short: "Stamped" },
  { id: "field_files", label: "Field Files", short: "Field Files" },
  { id: "run_files", label: "Run Files", short: "Run Files" },
];

const DEFAULT_SCOPES: { id: string; label: string }[] = [
  { id: "estimation", label: "Estimation" },
  { id: "detailing", label: "Detailing" },
  { id: "detailing_engineering", label: "Detailing + Engineering" },
];

const INVOICE_STATUSES: { id: string; label: string }[] = [
  { id: "none", label: "None" },
  { id: "preparing", label: "Preparing" },
  { id: "prepared", label: "Prepared" },
  { id: "sent", label: "Sent" },
  { id: "paid", label: "Paid" },
];

function isoDate(v: string | null | undefined): string {
  if (!v) return "";
  return v.slice(0, 10);
}

function duePill(iso: string | null): { cls: string; label: string } | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  const label = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  const days = (d.getTime() - Date.now()) / 86400000;
  if (days < 0) return { cls: "due-pill due-pill-overdue", label };
  if (days <= 3) return { cls: "due-pill due-pill-soon", label };
  return { cls: "due-pill due-pill-ok", label };
}

function depositNeeded(p: ProjectRow): number {
  const value = Number(p.contract_value || 0);
  const pct = Number(p.deposit_pct ?? 50);
  return Math.round(value * (pct / 100) * 100) / 100;
}

function scopeLabel(id: string, scopes: { id: string; label: string }[]): string {
  return scopes.find((s) => s.id === id)?.label || id || "—";
}

function clientOptionLabel(c: ClientRow, showFullName: boolean): string {
  const ini = (c.initial || "").trim();
  const loc = (c.location || "").trim();
  // Staff / HR: initials (+ location) only — never real firm names (client privacy)
  if (!showFullName) {
    if (ini && loc) return `[${ini}] · ${loc}`;
    if (ini) return `[${ini}]`;
    return loc || "Client";
  }
  return `${ini ? `[${ini}] ` : ""}${c.name}${loc ? ` (${loc})` : ""}`;
}

/** Map API / client validation messages → field keys for red highlights. */
function mapProjectFieldErrors(msg: string): Record<string, string> {
  const m = msg.toLowerCase();
  const out: Record<string, string> = {};
  if (/project name|job title|include letters|at least 4/.test(m)) out.name = msg;
  if (/client/.test(m)) out.client_id = msg;
  if (/work scope|scope must/.test(m)) out.work_scope = msg;
  if (/deposit %/.test(m)) out.deposit_pct = msg;
  if (/contract value/.test(m)) out.contract_value = msg;
  if (/currency/.test(m)) out.currency = msg;
  if (/area/.test(m)) out.area_sqft = msg;
  if (/storey/.test(m)) out.storeys = msg;
  if (/assignee|detailer/.test(m)) out.detailer_id = msg;
  if (/engineer/.test(m)) out.engineer_id = msg;
  if (/advance|deposit|intake|final payment|payment gate|stamped|field files|run files/.test(m)) {
    out.phase = msg;
  }
  if (/code/.test(m) && !out.phase) out.code = msg;
  return out;
}

function isPaymentGateMessage(msg: string): boolean {
  return /Advance not recorded|Final payment not recorded|cannot leave Intake|Ask Admin or Manager to clear the advance|Payment gate/i.test(
    msg
  );
}

/** Trello-style label colours per phase (CFS gold for Intake). */
const PHASE_COLOR: Record<string, string> = {
  intake: "#c9a227",
  preliminary_design: "#3b82f6",
  preliminary_engineering: "#06b6d4",
  final_engineering: "#a855f7",
  stamped_drawings: "#22c55e",
  field_files: "#f97316",
  run_files: "#14b8a6",
};

const emptyForm = {
  name: "",
  code: "",
  client_id: "",
  work_scope: "estimation",
  assignee_id: "",
  detailer_id: "",
  engineer_id: "",
  area_sqft: "",
  storeys: "",
  phase: "intake",
  work_state: "working",
  comments: "",
  due_at: "",
  target_at: "",
  contract_value: "",
  currency: "USD",
  deposit_pct: "50",
};

export function ProjectsPage() {
  const toast = useToast();
  const nav = useNavigate();
  const role = localStorage.getItem("ems_role") || "";
  const myId = localStorage.getItem("ems_employee_id") || "";
  const office = role === "admin" || role === "manager" || role === "hr" || role === "demo";
  const finance = role === "admin" || role === "manager";
  const manager = office; // board/list ops (HR included)
  const canCreate = office || role === "employee";
  const [projects, setProjects] = useState<ProjectRow[]>([]);
  const [clients, setClients] = useState<ClientRow[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [scopes, setScopes] = useState(DEFAULT_SCOPES);
  const [busy, setBusy] = useState(false);
  const [view, setView] = useState<"board" | "list">("board");
  const [editing, setEditing] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [clientName, setClientName] = useState("");
  const [clientLoc, setClientLoc] = useState("");
  const [clientInitial, setClientInitial] = useState("");
  const [clientInvoiceStatus, setClientInvoiceStatus] = useState("none");
  const [q, setQ] = useState("");
  const [overrideReason, setOverrideReason] = useState("");
  const [pendingMove, setPendingMove] = useState<{ p: ProjectRow; phase: string } | null>(null);
  const [pendingDelete, setPendingDelete] = useState<ProjectRow | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [progressPct, setProgressPct] = useState("");
  const [progressNote, setProgressNote] = useState("");
  const [progressHistory, setProgressHistory] = useState<ProjectProgressRow[]>([]);
  const [savingProgress, setSavingProgress] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [payGateHint, setPayGateHint] = useState<{ message: string; projectId: string | null } | null>(null);
  const isStaff = role === "employee";

  function progressDelta(rows: ProjectProgressRow[], index: number): string | null {
    const cur = rows[index];
    if (!cur) return null;
    const prev = rows.slice(index + 1).find((r) => r.employee_id === cur.employee_id);
    if (!prev) return null;
    const d = Number(cur.percent) - Number(prev.percent);
    if (!Number.isFinite(d) || d === 0) return null;
    return d > 0 ? `+${d}% vs prior` : `${d}% vs prior`;
  }

  function clearFieldError(key: string) {
    setFieldErrors((prev) => {
      if (!prev[key]) return prev;
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }

  async function load() {
    setBusy(true);
    try {
      const phasesP = fetchProjectPhases().catch(() => null);
      if (canCreate) {
        const [p, c, e, phases] = await Promise.all([
          fetchProjects(),
          fetchClients(),
          fetchEmployees(),
          phasesP,
        ]);
        setProjects(p);
        setClients(c);
        setEmployees(e.filter((x) => x.role === "employee"));
        if (phases?.scopes?.length && phases.scope_labels) {
          setScopes(
            phases.scopes.map((id) => ({
              id,
              label: phases.scope_labels[id] || id,
            }))
          );
        }
      } else {
        setProjects(await fetchProjects());
        setClients([]);
        setEmployees([]);
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Load failed");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    load().catch((e) => toast.error(String(e)));
  }, []);

  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    if (!s) return projects;
    return projects.filter(
      (p) =>
        p.name.toLowerCase().includes(s) ||
        (p.code || "").toLowerCase().includes(s) ||
        p.client_name.toLowerCase().includes(s) ||
        (p.client_initial || "").toLowerCase().includes(s) ||
        p.assignee_name.toLowerCase().includes(s) ||
        (p.detailer_name || "").toLowerCase().includes(s) ||
        (p.engineer_name || "").toLowerCase().includes(s) ||
        p.phase.toLowerCase().includes(s)
    );
  }, [projects, q]);

  function startEdit(p?: ProjectRow, phaseForNew?: string) {
    if (!canCreate) return;
    setOverrideReason("");
    setPendingMove(null);
    setFieldErrors({});
    setPayGateHint(null);
    setProgressPct("");
    setProgressNote("");
    setProgressHistory([]);
    if (!p) {
      setEditing("new");
      const selfId = role === "employee" && myId ? myId : "";
      setForm({
        ...emptyForm,
        phase: phaseForNew || "intake",
        work_scope: scopes[0]?.id || "estimation",
        detailer_id: selfId,
        engineer_id: "",
        assignee_id: selfId,
      });
      return;
    }
    setEditing(p.id);
    const detailerId =
      p.detailer_id ||
      p.assignees?.find((a) => a.role === "detailer")?.employee_id ||
      p.assignee_id ||
      "";
    const engineerId =
      p.engineer_id ||
      p.assignees?.find((a) => a.role === "engineer")?.employee_id ||
      (p.assignees && p.assignees.length > 1 ? p.assignees[1].employee_id : "") ||
      "";
    setForm({
      name: p.name,
      code: p.code || "",
      client_id: p.client_id || "",
      work_scope: p.work_scope || scopes[0]?.id || "estimation",
      assignee_id: detailerId || p.assignee_id || "",
      detailer_id: detailerId,
      engineer_id: engineerId,
      area_sqft: p.area_sqft != null ? String(p.area_sqft) : "",
      storeys: p.storeys != null ? String(p.storeys) : "",
      phase: p.phase,
      work_state: p.work_state,
      comments: p.comments || "",
      due_at: isoDate(p.due_at),
      target_at: isoDate(p.target_at),
      contract_value: p.contract_value != null ? String(p.contract_value) : "",
      currency: p.currency || "USD",
      deposit_pct: String(p.deposit_pct ?? 50),
    });
    if (p.latest_progress_pct != null) setProgressPct(String(p.latest_progress_pct));
    fetchProjectProgress(p.id)
      .then(setProgressHistory)
      .catch(() => setProgressHistory([]));
  }

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    setFieldErrors({});
    setPayGateHint(null);
    const name = form.name.trim().replace(/\s+/g, " ");
    const localErrors: Record<string, string> = {};
    if (name.length < 4) {
      localErrors.name = "Project name must be at least 4 characters.";
    } else {
      const letters = (name.match(/[A-Za-z]/g) || []).length;
      if (letters < 2) localErrors.name = "Project name must include letters.";
      else if (!/[ \-\d]/.test(name) && name.length < 10) {
        localErrors.name = "Use a clear job title (e.g. LOT 12 Main St or Warehouse Shed).";
      }
    }
    if (!form.client_id) localErrors.client_id = "Select a client (required). Add one above if needed.";
    if (!form.work_scope) localErrors.work_scope = "Select a work scope.";
    if (!form.detailer_id) localErrors.detailer_id = "Select a Detailer.";
    if (!form.engineer_id) localErrors.engineer_id = "Select an Engineer.";
    let deposit = 50;
    let contract = 0;
    let currency = "USD";
    if (finance) {
      deposit = Number(form.deposit_pct);
      if (Number.isNaN(deposit) || deposit < 0 || deposit > 100) {
        localErrors.deposit_pct = "Deposit % must be between 0 and 100.";
      }
      contract = form.contract_value === "" ? 0 : Number(form.contract_value);
      if (Number.isNaN(contract) || contract <= 0) {
        localErrors.contract_value = "Contract value must be greater than 0.";
      }
      currency = normalizeCurrencyCode(form.currency);
    }
    if (form.area_sqft !== "") {
      const area = Number(form.area_sqft);
      if (Number.isNaN(area) || area < 0) localErrors.area_sqft = "Area (sq.ft) cannot be negative.";
      else if (area > 5_000_000) localErrors.area_sqft = "Area (sq.ft) looks too large — check the number.";
    }
    if (form.storeys !== "") {
      const storeys = Number(form.storeys);
      if (Number.isNaN(storeys) || storeys < 0) localErrors.storeys = "Storeys cannot be negative.";
      else if (storeys > 200) localErrors.storeys = "Storeys must be 200 or fewer.";
    }
    if (Object.keys(localErrors).length) {
      setFieldErrors(localErrors);
      toast.error(Object.values(localErrors)[0] || "Fix the highlighted fields.");
      return;
    }
    try {
      const body = {
        name,
        code: finance || office ? form.code.trim() : "",
        client_id: form.client_id || null,
        work_scope: form.work_scope.trim(),
        detailer_id: form.detailer_id || null,
        engineer_id: form.engineer_id || null,
        assignee_id: form.detailer_id || null,
        assignee_ids: [form.detailer_id, form.engineer_id].filter(Boolean),
        area_sqft: form.area_sqft !== "" ? Number(form.area_sqft) : null,
        storeys: form.storeys !== "" ? Number(form.storeys) : null,
        phase: form.phase,
        work_state: form.work_state,
        comments: form.comments.trim(),
        due_at: form.due_at ? `${form.due_at}T12:00:00` : null,
        target_at: form.target_at ? `${form.target_at}T12:00:00` : null,
        contract_value: contract,
        deposit_pct: deposit,
        currency,
      };
      await saveProject(body, editing && editing !== "new" ? editing : undefined);
      setEditing(null);
      setOverrideReason("");
      setFieldErrors({});
      setPayGateHint(null);
      toast.success(editing === "new" ? "Project saved." : "Project updated.");
      await load();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Save failed";
      const mapped = mapProjectFieldErrors(msg);
      setFieldErrors(mapped);
      toast.error(msg);
      if (finance && isPaymentGateMessage(msg)) {
        setPayGateHint({
          message: msg,
          projectId: editing && editing !== "new" ? editing : null,
        });
      }
    }
  }

  async function onSaveProgress() {
    if (!editing || editing === "new") return;
    const pct = Number(progressPct);
    if (Number.isNaN(pct) || pct < 0 || pct > 100) {
      toast.error("Progress % must be between 0 and 100.");
      return;
    }
    setSavingProgress(true);
    try {
      await postProjectProgress(editing, { percent: pct, note: progressNote.trim() });
      toast.success(isStaff ? "Your progress saved — Admin can see it on this project." : "Progress logged.");
      const hist = await fetchProjectProgress(editing);
      setProgressHistory(hist);
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Progress failed");
    } finally {
      setSavingProgress(false);
    }
  }

  async function onAddClient(e: React.FormEvent) {
    e.preventDefault();
    const name = clientName.trim();
    const location = clientLoc.trim();
    const initial = clientInitial.trim();
    if (name.length < 2) {
      toast.error("Client name is required.");
      return;
    }
    if (!location) {
      toast.error("Client location is required (e.g. USA, AUS).");
      return;
    }
    if (!initial) {
      toast.error("Client initial is required (e.g. W for Willie).");
      return;
    }
    try {
      await createClient({
        name,
        location,
        initial,
        invoice_status: clientInvoiceStatus || "none",
      });
      setClientName("");
      setClientLoc("");
      setClientInitial("");
      setClientInvoiceStatus("none");
      toast.success("Client added.");
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Client failed");
    }
  }

  async function movePhase(p: ProjectRow, phase: string, force = false) {
    if (!canCreate) return;
    try {
      const detailerId =
        p.detailer_id ||
        p.assignees?.find((a) => a.role === "detailer")?.employee_id ||
        p.assignee_id ||
        "";
      const engineerId =
        p.engineer_id ||
        p.assignees?.find((a) => a.role === "engineer")?.employee_id ||
        detailerId;
      await saveProject(
        {
          name: p.name,
          code: p.code || "",
          client_id: p.client_id,
          work_scope: p.work_scope,
          detailer_id: detailerId || null,
          engineer_id: engineerId || null,
          assignee_id: detailerId || null,
          assignee_ids: [detailerId, engineerId].filter(Boolean),
          area_sqft: p.area_sqft,
          storeys: p.storeys,
          phase,
          work_state: p.work_state,
          comments: p.comments,
          due_at: p.due_at,
          target_at: p.target_at,
          contract_value: p.contract_value || 0,
          deposit_pct: p.deposit_pct || 50,
          currency: p.currency || "USD",
          override_gate: force,
          override_reason: force ? overrideReason || "Manager override from Design Queue" : "",
        },
        p.id
      );
      setPendingMove(null);
      setOverrideReason("");
      toast.success("Project moved.");
      await load();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Move failed";
      toast.error(msg);
      // Override UI is finance-only — never nudge HR toward Payments
      if (!force && finance && /Stamped|Field Files|Run Files|Final payment|need_final|Advance not recorded/i.test(msg)) {
        setPendingMove({ p, phase });
      }
    }
  }

  async function onDelete(p: ProjectRow) {
    if (!manager) return;
    setPendingDelete(p);
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    setDeleting(true);
    try {
      await deleteProject(pendingDelete.id);
      if (editing === pendingDelete.id) setEditing(null);
      setPendingDelete(null);
      toast.success("Project deleted.");
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div>
      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title="Delete project?"
        message={
          pendingDelete
            ? `Delete “${pendingDelete.name}”? Linked invoices stay in Payments (unlinked from this project).`
            : ""
        }
        confirmLabel="Delete"
        busy={deleting}
        onCancel={() => !deleting && setPendingDelete(null)}
        onConfirm={confirmDelete}
      />
      <div className="toolbar">
        <h2 style={{ margin: 0, flex: 1 }}>{manager ? "Design Queue" : "My Projects"}</h2>
        <input
          style={{ maxWidth: 280 }}
          placeholder="Search projects…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <button type="button" className="secondary" onClick={() => setView(view === "board" ? "list" : "board")}>
          {view === "board" ? "List view" : "Board view"}
        </button>
        {canCreate ? (
          <button type="button" onClick={() => startEdit()}>
            New project
          </button>
        ) : null}
        <RefreshButton busy={busy} onClick={() => load()} />
      </div>
      {pendingMove && finance ? (
        <div className="card pay-gate-card">
          <p style={{ marginTop: 0, marginBottom: 12 }}>
            <strong>{pendingMove.p.name}</strong> — advance not marked Paid yet (
            {formatMoney(depositNeeded(pendingMove.p), pendingMove.p.currency || "USD")} needed).
          </p>
          <div className="toolbar" style={{ marginBottom: 0 }}>
            <button
              type="button"
              onClick={() =>
                nav(`/payments?project=${encodeURIComponent(pendingMove.p.id)}&kind=deposit`)
              }
            >
              Open Payments → record deposit
            </button>
            <div className="field" style={{ flex: 1 }}>
              <label>Override reason</label>
              <input
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
                placeholder="Owner approved"
              />
            </div>
            <button
              type="button"
              className="secondary"
              disabled={!overrideReason.trim()}
              onClick={() => movePhase(pendingMove.p, pendingMove.phase, true)}
            >
              Override & move
            </button>
            <button type="button" className="secondary" onClick={() => setPendingMove(null)}>
              Cancel
            </button>
          </div>
        </div>
      ) : null}
      {payGateHint && finance ? (
        <div className="card pay-gate-card">
          <p style={{ marginTop: 0, marginBottom: 12 }}>{payGateHint.message}</p>
          <div className="toolbar" style={{ marginBottom: 0 }}>
            <button
              type="button"
              onClick={() =>
                nav(
                  payGateHint.projectId
                    ? `/payments?project=${encodeURIComponent(payGateHint.projectId)}&kind=deposit`
                    : "/payments?kind=deposit"
                )
              }
            >
              Go to Payments
            </button>
            <button type="button" className="secondary" onClick={() => setPayGateHint(null)}>
              Dismiss
            </button>
          </div>
        </div>
      ) : null}

      {manager ? (
      <form className="toolbar client-add-bar" onSubmit={onAddClient}>
        <div className="field">
          <label>
            New client <span className="req">*</span>
          </label>
          <input
            value={clientName}
            onChange={(e) => setClientName(e.target.value)}
            placeholder="WILLIE / firm name"
            required
            minLength={2}
          />
        </div>
        <div className="field">
          <label>
            Initial <span className="req">*</span>
          </label>
          <input
            value={clientInitial}
            onChange={(e) => setClientInitial(e.target.value.toUpperCase().slice(0, 4))}
            placeholder="W"
            required
            maxLength={4}
            style={{ maxWidth: 72 }}
          />
        </div>
        <div className="field">
          <label>
            Location <span className="req">*</span>
          </label>
          <input
            value={clientLoc}
            onChange={(e) => setClientLoc(e.target.value)}
            placeholder="USA / AUS"
            required
          />
        </div>
        <div className="field">
          <label>Invoice status</label>
          <select value={clientInvoiceStatus} onChange={(e) => setClientInvoiceStatus(e.target.value)}>
            {INVOICE_STATUSES.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
        <button type="submit" className="secondary">
          Add client
        </button>
      </form>
      ) : null}
      {manager ? (
        <p className="muted" style={{ marginTop: -8, marginBottom: 12, fontSize: 13 }}>
          Staff only see <strong>[Initial] · location</strong> — use a unique Initial (e.g. DE / DM) when two firms share a letter.
        </p>
      ) : null}

      {editing ? (
        <form className="card project-form" style={{ marginBottom: 16 }} onSubmit={onSave} noValidate>
          <h3 style={{ marginTop: 0 }}>{editing === "new" ? "New project" : "Edit project"}</h3>
          <div className="form-grid">
            <div className={`field field-span-2${fieldErrors.name ? " is-invalid" : ""}`}>
              <label>
                Project name <span className="req">*</span>
              </label>
              <input
                value={form.name}
                onChange={(e) => {
                  clearFieldError("name");
                  setForm({ ...form, name: e.target.value });
                }}
                required
                minLength={4}
                placeholder="e.g. LOT 12 Horning Street"
                aria-invalid={Boolean(fieldErrors.name)}
              />
              {fieldErrors.name ? (
                <p className="field-error" role="alert">
                  {fieldErrors.name}
                </p>
              ) : null}
            </div>
            {role === "employee" ? (
              editing && editing !== "new" && form.code ? (
                <div className="field">
                  <label>Code</label>
                  <p className="code-readonly" title="Assigned automatically">
                    {form.code}
                  </p>
                </div>
              ) : (
                <div className="field">
                  <label>Code</label>
                  <p className="muted" style={{ margin: "10px 0 0", fontSize: 13 }}>
                    Assigned automatically after save
                  </p>
                </div>
              )
            ) : (
              <div className={`field${fieldErrors.code ? " is-invalid" : ""}`}>
                <label>Code</label>
                <input
                  value={form.code}
                  onChange={(e) => {
                    clearFieldError("code");
                    setForm({ ...form, code: e.target.value.toUpperCase() });
                  }}
                  placeholder="Leave blank to auto-fill"
                  maxLength={32}
                  aria-invalid={Boolean(fieldErrors.code)}
                />
                {fieldErrors.code ? (
                  <p className="field-error" role="alert">
                    {fieldErrors.code}
                  </p>
                ) : (
                  <span className="field-hint">Optional override</span>
                )}
              </div>
            )}
            <div className={`field${fieldErrors.client_id ? " is-invalid" : ""}`}>
              <label>
                Client <span className="req">*</span>
              </label>
              <select
                required
                value={form.client_id}
                onChange={(e) => {
                  clearFieldError("client_id");
                  const clientId = e.target.value;
                  const client = clients.find((c) => c.id === clientId);
                  const next = { ...form, client_id: clientId };
                  if (client && (editing === "new" || !form.currency || form.currency === "USD")) {
                    next.currency = guessCurrencyFromLocation(client.location);
                  }
                  setForm(next);
                }}
                aria-invalid={Boolean(fieldErrors.client_id)}
              >
                <option value="">Select client…</option>
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>
                    {clientOptionLabel(c, finance || role === "hr")}
                  </option>
                ))}
              </select>
              {fieldErrors.client_id ? (
                <p className="field-error" role="alert">
                  {fieldErrors.client_id}
                </p>
              ) : null}
            </div>
            <div className={`field${fieldErrors.work_scope ? " is-invalid" : ""}`}>
              <label>
                Scope <span className="req">*</span>
              </label>
              <select
                required
                value={form.work_scope}
                onChange={(e) => {
                  clearFieldError("work_scope");
                  setForm({ ...form, work_scope: e.target.value });
                }}
                aria-invalid={Boolean(fieldErrors.work_scope)}
              >
                {scopes.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
              {fieldErrors.work_scope ? (
                <p className="field-error" role="alert">
                  {fieldErrors.work_scope}
                </p>
              ) : null}
            </div>
            <div className={`field${fieldErrors.detailer_id ? " is-invalid" : ""}`}>
              <label>
                Detailer <span className="req">*</span>
              </label>
              <select
                required
                value={form.detailer_id}
                onChange={(e) => {
                  clearFieldError("detailer_id");
                  const detailer_id = e.target.value;
                  setForm({ ...form, detailer_id, assignee_id: detailer_id });
                }}
                aria-invalid={Boolean(fieldErrors.detailer_id)}
              >
                <option value="">Select detailer…</option>
                {employees.map((emp) => (
                  <option key={emp.id} value={emp.id}>
                    {emp.full_name} #{emp.code}
                  </option>
                ))}
              </select>
              {fieldErrors.detailer_id ? (
                <p className="field-error" role="alert">
                  {fieldErrors.detailer_id}
                </p>
              ) : null}
            </div>
            <div className={`field${fieldErrors.engineer_id ? " is-invalid" : ""}`}>
              <label>
                Engineer <span className="req">*</span>
              </label>
              <select
                required
                value={form.engineer_id}
                onChange={(e) => {
                  clearFieldError("engineer_id");
                  setForm({ ...form, engineer_id: e.target.value });
                }}
                aria-invalid={Boolean(fieldErrors.engineer_id)}
              >
                <option value="">Select engineer…</option>
                {employees.map((emp) => (
                  <option key={emp.id} value={emp.id}>
                    {emp.full_name} #{emp.code}
                  </option>
                ))}
              </select>
              {fieldErrors.engineer_id ? (
                <p className="field-error" role="alert">
                  {fieldErrors.engineer_id}
                </p>
              ) : (
                <span className="field-hint">Same person may be both</span>
              )}
            </div>
            <div className={`field${fieldErrors.area_sqft ? " is-invalid" : ""}`}>
              <label>Area (sq.ft)</label>
              <input
                type="number"
                min={0}
                value={form.area_sqft}
                onChange={(e) => {
                  clearFieldError("area_sqft");
                  setForm({ ...form, area_sqft: e.target.value });
                }}
                aria-invalid={Boolean(fieldErrors.area_sqft)}
              />
              {fieldErrors.area_sqft ? (
                <p className="field-error" role="alert">
                  {fieldErrors.area_sqft}
                </p>
              ) : null}
            </div>
            <div className={`field${fieldErrors.storeys ? " is-invalid" : ""}`}>
              <label>Storey</label>
              <input
                type="number"
                min={0}
                max={200}
                value={form.storeys}
                onChange={(e) => {
                  clearFieldError("storeys");
                  setForm({ ...form, storeys: e.target.value });
                }}
                aria-invalid={Boolean(fieldErrors.storeys)}
              />
              {fieldErrors.storeys ? (
                <p className="field-error" role="alert">
                  {fieldErrors.storeys}
                </p>
              ) : null}
            </div>
            <div className={`field${fieldErrors.phase ? " is-invalid" : ""}`}>
              <label>Phase</label>
              <select
                value={form.phase}
                onChange={(e) => {
                  clearFieldError("phase");
                  setForm({ ...form, phase: e.target.value });
                }}
                aria-invalid={Boolean(fieldErrors.phase)}
              >
                {PHASES.map((ph) => (
                  <option key={ph.id} value={ph.id}>
                    {ph.label}
                  </option>
                ))}
              </select>
              {fieldErrors.phase ? (
                <p className="field-error" role="alert">
                  {fieldErrors.phase}
                </p>
              ) : null}
            </div>
            <div className="field">
              <label>Status</label>
              <select value={form.work_state} onChange={(e) => setForm({ ...form, work_state: e.target.value })}>
                <option value="working">Working</option>
                <option value="waiting">Waiting</option>
                <option value="on_hold">On hold</option>
                <option value="done">Done</option>
              </select>
            </div>
            <div className="field">
              <label>Next due</label>
              <input type="date" value={form.due_at} onChange={(e) => setForm({ ...form, due_at: e.target.value })} />
            </div>
            <div className="field">
              <label>Target</label>
              <input type="date" value={form.target_at} onChange={(e) => setForm({ ...form, target_at: e.target.value })} />
            </div>
            {finance ? (
              <>
                <div className={`field field-span-2${fieldErrors.contract_value || fieldErrors.currency ? " is-invalid" : ""}`}>
                  <label>
                    Contract value <span className="req">*</span>
                  </label>
                  <div className="money-field">
                    <input
                      className="money-amount"
                      type="number"
                      min={0}
                      step="0.01"
                      required
                      value={form.contract_value}
                      onChange={(e) => {
                        clearFieldError("contract_value");
                        setForm({ ...form, contract_value: e.target.value });
                      }}
                      aria-invalid={Boolean(fieldErrors.contract_value)}
                    />
                    <div className="money-currency">
                      <CurrencySelect
                        value={form.currency}
                        onChange={(currency) => {
                          clearFieldError("currency");
                          setForm({ ...form, currency });
                        }}
                        required
                      />
                    </div>
                  </div>
                  {fieldErrors.contract_value || fieldErrors.currency ? (
                    <p className="field-error" role="alert">
                      {fieldErrors.contract_value || fieldErrors.currency}
                    </p>
                  ) : null}
                </div>
                <div className={`field${fieldErrors.deposit_pct ? " is-invalid" : ""}`}>
                  <label>
                    Deposit % <span className="req">*</span>
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    required
                    value={form.deposit_pct}
                    onChange={(e) => {
                      clearFieldError("deposit_pct");
                      setForm({ ...form, deposit_pct: e.target.value });
                    }}
                    aria-invalid={Boolean(fieldErrors.deposit_pct)}
                  />
                  {fieldErrors.deposit_pct ? (
                    <p className="field-error" role="alert">
                      {fieldErrors.deposit_pct}
                    </p>
                  ) : (
                    <span className="field-hint">Soft warn on board — hard lock only Stamped / Field / Run</span>
                  )}
                </div>
              </>
            ) : null}
            <div className="field field-span-3">
              <label>Comments</label>
              <input value={form.comments} onChange={(e) => setForm({ ...form, comments: e.target.value })} />
            </div>
          </div>
          <div className="toolbar" style={{ marginTop: 16, marginBottom: 0 }}>
            <button type="submit">Save</button>
            <button type="button" className="secondary" onClick={() => setEditing(null)}>
              Cancel
            </button>
          </div>
          {editing && editing !== "new" ? (
            <div className="progress-block" style={{ marginTop: 20, paddingTop: 16, borderTop: "1px solid var(--border, #333)" }}>
              {isStaff ? (
                <>
                  <h4 style={{ marginTop: 0, marginBottom: 6 }}>End-of-day progress (you)</h4>
                  <p className="muted" style={{ margin: "0 0 12px", fontSize: 13, lineHeight: 1.4 }}>
                     At end of day set how complete this job is (e.g. 60%). Saved to the project — Admin sees the same history and can ask about jumps (40% → 50% = 10% today).
                  </p>
                  <div className="toolbar" style={{ marginBottom: 8, flexWrap: "wrap" }}>
                    <div className="field" style={{ minWidth: 100 }}>
                      <label>My % today</label>
                      <input
                        type="number"
                        min={0}
                        max={100}
                        step="1"
                        value={progressPct}
                        onChange={(e) => setProgressPct(e.target.value)}
                        placeholder="0–100"
                      />
                    </div>
                    <div className="field" style={{ flex: 1, minWidth: 160 }}>
                      <label>Note</label>
                      <input
                        value={progressNote}
                        onChange={(e) => setProgressNote(e.target.value)}
                        placeholder="Optional note"
                      />
                    </div>
                    <button type="button" className="secondary" disabled={savingProgress} onClick={() => onSaveProgress()}>
                      {savingProgress ? "Saving…" : "Save my progress"}
                    </button>
                  </div>
                  <h5 style={{ margin: "12px 0 6px", fontSize: 13, color: "var(--gold, #c9a227)" }}>What you logged</h5>
                  {progressHistory.filter((r) => r.employee_id === myId).length ? (
                    <ul className="muted" style={{ margin: 0, paddingLeft: 18, fontSize: 13 }}>
                      {progressHistory
                        .filter((r) => r.employee_id === myId)
                        .slice(0, 8)
                        .map((r, i, arr) => {
                          const delta = progressDelta(arr, i);
                          return (
                            <li key={r.id}>
                              {r.work_date}: <strong>{r.percent}%</strong>
                              {delta ? ` (${delta})` : ""}
                              {r.note ? ` — ${r.note}` : ""}
                            </li>
                          );
                        })}
                    </ul>
                  ) : (
                    <p className="muted" style={{ margin: 0, fontSize: 13 }}>
                      You have not logged progress on this job yet.
                    </p>
                  )}
                </>
              ) : (
                <>
                  <h4 style={{ marginTop: 0, marginBottom: 6 }}>Team progress audit</h4>
                  <p className="muted" style={{ margin: "0 0 12px", fontSize: 13, lineHeight: 1.4 }}>
                    Staff enter end-of-day % on their login. You review history here (question 40% → 50%). Optional: log a % yourself only if correcting or covering.
                  </p>
                  {progressHistory.length ? (
                    <ul className="muted" style={{ margin: "0 0 14px", paddingLeft: 18, fontSize: 13 }}>
                      {progressHistory.slice(0, 12).map((r, i) => {
                        const delta = progressDelta(progressHistory, i);
                        return (
                          <li key={r.id}>
                            {r.work_date}: <strong>{r.percent}%</strong> — {r.employee_name || "—"}
                            {delta ? ` · ${delta}` : ""}
                            {r.note ? ` (${r.note})` : ""}
                          </li>
                        );
                      })}
                    </ul>
                  ) : (
                    <p className="muted" style={{ margin: "0 0 14px", fontSize: 13 }}>
                      No staff progress logged yet.
                    </p>
                  )}
                  <details className="progress-admin-log">
                    <summary style={{ cursor: "pointer", fontSize: 13, color: "var(--text-muted, #aaa)" }}>
                      Optional: log / correct a % (office)
                    </summary>
                    <div className="toolbar" style={{ marginTop: 10, marginBottom: 0, flexWrap: "wrap" }}>
                      <div className="field" style={{ minWidth: 100 }}>
                        <label>Percent</label>
                        <input
                          type="number"
                          min={0}
                          max={100}
                          step="1"
                          value={progressPct}
                          onChange={(e) => setProgressPct(e.target.value)}
                          placeholder="0–100"
                        />
                      </div>
                      <div className="field" style={{ flex: 1, minWidth: 160 }}>
                        <label>Note</label>
                        <input
                          value={progressNote}
                          onChange={(e) => setProgressNote(e.target.value)}
                          placeholder="Optional note"
                        />
                      </div>
                      <button type="button" className="secondary" disabled={savingProgress} onClick={() => onSaveProgress()}>
                        {savingProgress ? "Saving…" : "Save as me"}
                      </button>
                    </div>
                  </details>
                </>
              )}
            </div>
          ) : null}
        </form>
      ) : null}

      {view === "board" ? (
        <div className="kanban-board">
          <div className="kanban">
            {PHASES.map((ph) => {
              const col = filtered.filter((p) => p.phase === ph.id);
              const colColor = PHASE_COLOR[ph.id] || "var(--accent)";
              return (
                <section className="kanban-col" key={ph.id} style={{ borderTopColor: colColor }}>
                  <header>
                    <span className="kanban-col-title" title={ph.label}>{ph.short}</span>
                    <span className="kanban-count" style={{ background: `${colColor}33`, color: colColor }}>
                      {col.length}
                    </span>
                  </header>
                  <div className="kanban-col-body">
                    {col.map((p) => {
                      const blocked = p.gate === "need_deposit" || p.gate === "need_final";
                      const pill = duePill(p.due_at);
                      const paid = Number(p.paid_amount || 0);
                      const contract = Number(p.contract_value || 0);
                      const need = depositNeeded(p);
                      const cur = p.currency || "USD";
                      const advanceOk = contract <= 0 || need <= 0 || paid + 0.009 >= need;
                      const fullyPaid = contract > 0 && paid + 0.009 >= contract;
                      const phaseColor = PHASE_COLOR[p.phase] || "var(--accent)";
                      return (
                        <article
                          className={`kanban-card${blocked ? " is-blocked" : ""}`}
                          key={p.id}
                        >
                          <div className="kanban-labels">
                            <span className="kanban-label" style={{ background: phaseColor }} title={ph.label} />
                            {blocked ? (
                              <span className="kanban-label" style={{ background: "#7a1f2e" }} title="Payment due" />
                            ) : null}
                            {fullyPaid ? (
                              <span className="kanban-label" style={{ background: "#22c55e" }} title="Fully paid" />
                            ) : advanceOk && contract > 0 ? (
                              <span className="kanban-label" style={{ background: "#4ade80" }} title="Advance OK" />
                            ) : null}
                          </div>
                          {p.code ? (
                            <p className="kanban-code" style={{ margin: "0 0 2px", fontSize: 12, fontWeight: 700, letterSpacing: "0.04em", color: "var(--accent, #c9a227)" }}>
                              {p.code}
                            </p>
                          ) : null}
                          <button type="button" className="kanban-title" onClick={() => startEdit(p)}>
                            {p.name}
                          </button>
                          <p className="kanban-client">{p.client_name || "No client"}</p>
                          <p className="muted" style={{ margin: "0 0 4px", fontSize: 12 }}>
                            {scopeLabel(p.work_scope, scopes)}
                          </p>
                          {p.latest_progress_pct != null ? (
                            <p
                              className="kanban-progress"
                              style={{
                                margin: "0 0 6px",
                                fontSize: 13,
                                fontWeight: 700,
                                color: "var(--accent, #c9a227)",
                              }}
                              title="Latest end-of-day progress logged by staff"
                            >
                              Progress {p.latest_progress_pct}%
                            </p>
                          ) : (
                            <p className="muted" style={{ margin: "0 0 6px", fontSize: 12 }}>
                              No progress logged
                            </p>
                          )}
                          {(p.detailer_name || p.engineer_name || p.assignee_name) ? (
                            <p className="kanban-roles" style={{ margin: "0 0 6px", fontSize: 12, color: "var(--text-muted, #aaa)" }}>
                              {p.detailer_name || p.assignee_name ? (
                                <span title="Detailer">D: {p.detailer_name || p.assignee_name}</span>
                              ) : null}
                              {(p.detailer_name || p.assignee_name) && p.engineer_name ? " · " : null}
                              {p.engineer_name ? <span title="Engineer">E: {p.engineer_name}</span> : null}
                            </p>
                          ) : null}
                          {finance && contract > 0 ? (
                            <p className="kanban-pay">
                              {formatMoney(paid, cur)} / {formatMoney(contract, cur)}
                            </p>
                          ) : null}
                          <div className="kanban-badges">
                            {pill ? <span className={pill.cls}>{pill.label}</span> : null}
                            {finance && contract <= 0 ? (
                              <span className="pill pill-blocked">No contract $</span>
                            ) : null}
                            {finance && contract > 0 && blocked ? (
                              <span className="pill pill-blocked">
                                {p.gate === "need_deposit" ? "Deposit due" : "Final pay"}
                              </span>
                            ) : null}
                            {!finance && (p.gate === "need_deposit" || p.gate === "need_final") ? (
                              <span className="pill pill-blocked" title="Office has not cleared payment yet — you can still work design phases">
                                {p.gate === "need_final" ? "Balance pending" : "Advance pending"}
                              </span>
                            ) : null}
                            {finance && contract > 0 && !blocked && fullyPaid ? (
                              <span className="pill pill-ok">Paid</span>
                            ) : null}
                            {p.assignee_name ? (
                              <span className="kanban-avatar" title={p.assignee_name}>
                                {p.assignee_name
                                  .split(/\s+/)
                                  .map((w) => w[0])
                                  .join("")
                                  .slice(0, 2)
                                  .toUpperCase()}
                              </span>
                            ) : null}
                          </div>
                          {finance && blocked ? (
                            <button
                              type="button"
                              className="kanban-pay-link"
                              onClick={() =>
                                nav(`/payments?project=${encodeURIComponent(p.id)}&kind=deposit`)
                              }
                            >
                              Payments →
                            </button>
                          ) : null}
                          {canCreate ? (
                            <div className="kanban-card-actions">
                              <select
                                aria-label={`Move ${p.name}`}
                                value={p.phase}
                                onChange={(e) => movePhase(p, e.target.value)}
                              >
                                {PHASES.map((x) => (
                                  <option key={x.id} value={x.id}>
                                    {x.label}
                                  </option>
                                ))}
                              </select>
                              {finance ? (
                                <button
                                  type="button"
                                  className="btn-danger kanban-del"
                                  title="Delete project"
                                  aria-label={`Delete ${p.name}`}
                                  onClick={() => onDelete(p)}
                                >
                                  Delete
                                </button>
                              ) : null}
                            </div>
                          ) : null}
                        </article>
                      );
                    })}
                  </div>
                  {canCreate ? (
                    <button
                      type="button"
                      className="kanban-add"
                      onClick={() => startEdit(undefined, ph.id)}
                    >
                      + Add a card
                    </button>
                  ) : null}
                </section>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="card" style={{ overflowX: "auto" }}>
          <table className="table-center">
            <thead>
              <tr>
                <th>Code</th>
                <th>Project</th>
                <th>Client</th>
                <th>Scope</th>
                <th>Location</th>
                <th>Detailer</th>
                <th>Engineer</th>
                <th>%</th>
                <th>Area</th>
                <th>Storey</th>
                <th>Phase</th>
                <th>Status</th>
                <th>Comments</th>
                {manager ? <th>Actions</th> : null}
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => {
                const blocked = p.gate === "need_deposit" || p.gate === "need_final";
                return (
                <tr key={p.id} className={blocked ? "is-pay-blocked" : undefined}>
                  <td>
                    <strong style={{ color: "var(--accent, #c9a227)" }}>{p.code || "—"}</strong>
                  </td>
                  <td>
                    <button type="button" className="linkish" onClick={() => startEdit(p)}>
                      {p.name}
                    </button>
                  </td>
                  <td>{p.client_name || "—"}</td>
                  <td>{scopeLabel(p.work_scope, scopes)}</td>
                  <td>{p.client_location || "—"}</td>
                  <td>{p.detailer_name || p.assignee_name || "—"}</td>
                  <td>{p.engineer_name || "—"}</td>
                  <td>{p.latest_progress_pct != null ? `${p.latest_progress_pct}%` : "—"}</td>
                  <td>{p.area_sqft ?? "—"}</td>
                  <td>{p.storeys ?? "—"}</td>
                  <td>
                    <span
                      className="pill phase-pill"
                      style={{
                        background: `${PHASE_COLOR[p.phase] || "var(--accent)"}22`,
                        color: PHASE_COLOR[p.phase] || "var(--accent)",
                        border: `1px solid ${PHASE_COLOR[p.phase] || "var(--accent)"}55`,
                      }}
                    >
                      {PHASES.find((x) => x.id === p.phase)?.label || p.phase}
                    </span>
                  </td>
                  <td>
                    <span
                      className={`pill ${
                        p.work_state === "working"
                          ? "pill-working"
                          : p.work_state === "waiting"
                            ? "pill-waiting"
                            : "pill-muted"
                      }`}
                    >
                      {p.work_state === "working"
                        ? "In progress"
                        : p.work_state === "waiting"
                          ? "Waiting"
                          : p.work_state === "done"
                            ? "Submitted"
                            : p.work_state}
                    </span>
                  </td>
                  <td>{p.comments || "—"}</td>
                  {manager ? (
                    <td>
                      {finance ? (
                        <button type="button" className="btn-danger btn-row-del" onClick={() => onDelete(p)}>
                          Delete
                        </button>
                      ) : (
                        <span className="muted">—</span>
                      )}
                    </td>
                  ) : null}
                </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
