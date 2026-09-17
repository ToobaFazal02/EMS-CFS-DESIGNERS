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
  assignee_ids: [] as string[],
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
        p.phase.toLowerCase().includes(s)
    );
  }, [projects, q]);

  function startEdit(p?: ProjectRow, phaseForNew?: string) {
    if (!canCreate) return;
    setOverrideReason("");
    setPendingMove(null);
    setProgressPct("");
    setProgressNote("");
    setProgressHistory([]);
    if (!p) {
      setEditing("new");
      const selfIds = role === "employee" && myId ? [myId] : [];
      setForm({
        ...emptyForm,
        phase: phaseForNew || "intake",
        work_scope: scopes[0]?.id || "estimation",
        assignee_ids: selfIds,
        assignee_id: selfIds[0] || "",
      });
      return;
    }
    setEditing(p.id);
    const ids =
      p.assignees && p.assignees.length
        ? p.assignees.map((a) => a.employee_id)
        : p.assignee_id
          ? [p.assignee_id]
          : [];
    setForm({
      name: p.name,
      code: p.code || "",
      client_id: p.client_id || "",
      work_scope: p.work_scope || scopes[0]?.id || "estimation",
      assignee_id: ids[0] || p.assignee_id || "",
      assignee_ids: ids,
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

  function toggleAssignee(id: string) {
    setForm((prev) => {
      const has = prev.assignee_ids.includes(id);
      const assignee_ids = has ? prev.assignee_ids.filter((x) => x !== id) : [...prev.assignee_ids, id];
      return { ...prev, assignee_ids, assignee_id: assignee_ids[0] || "" };
    });
  }

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    const name = form.name.trim().replace(/\s+/g, " ");
    if (name.length < 4) {
      toast.error("Project name must be at least 4 characters.");
      return;
    }
    const letters = (name.match(/[A-Za-z]/g) || []).length;
    if (letters < 2) {
      toast.error("Project name must include letters.");
      return;
    }
    if (!/[ \-\d]/.test(name) && name.length < 10) {
      toast.error("Use a clear job title (e.g. LOT 12 Main St or Warehouse Shed).");
      return;
    }
    if (!form.client_id) {
      toast.error("Select a client (required). Add one above if needed.");
      return;
    }
    if (!form.work_scope) {
      toast.error("Select a work scope.");
      return;
    }
    let deposit = 50;
    let contract = 0;
    let currency = "USD";
    if (finance) {
      deposit = Number(form.deposit_pct);
      if (Number.isNaN(deposit) || deposit < 0 || deposit > 100) {
        toast.error("Deposit % must be between 0 and 100.");
        return;
      }
      contract = form.contract_value === "" ? 0 : Number(form.contract_value);
      if (Number.isNaN(contract) || contract <= 0) {
        toast.error("Contract value must be greater than 0.");
        return;
      }
      currency = normalizeCurrencyCode(form.currency);
    }
    try {
      const body = {
        name,
        code: form.code.trim(),
        client_id: form.client_id || null,
        work_scope: form.work_scope.trim(),
        assignee_id: form.assignee_ids[0] || form.assignee_id || null,
        assignee_ids: form.assignee_ids,
        area_sqft: form.area_sqft ? Number(form.area_sqft) : null,
        storeys: form.storeys ? Number(form.storeys) : null,
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
      toast.success(editing === "new" ? "Project saved." : "Project updated.");
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Save failed");
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
      toast.success("Progress saved.");
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
    if (!manager) return;
    try {
      const ids =
        p.assignees && p.assignees.length
          ? p.assignees.map((a) => a.employee_id)
          : p.assignee_id
            ? [p.assignee_id]
            : [];
      await saveProject(
        {
          name: p.name,
          code: p.code || "",
          client_id: p.client_id,
          work_scope: p.work_scope,
          assignee_id: ids[0] || p.assignee_id,
          assignee_ids: ids,
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
      if (!force && finance && /Advance|Final payment|Payment gate|need_deposit|need_final|cannot leave Intake|cannot move to/i.test(msg)) {
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
            <button type="button" onClick={() => nav("/payments")}>
              Open Payments
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

      {editing ? (
        <form className="card project-form" style={{ marginBottom: 16 }} onSubmit={onSave} noValidate>
          <h3 style={{ marginTop: 0 }}>{editing === "new" ? "New project" : "Edit project"}</h3>
          <div className="form-grid">
            <div className="field field-span-2">
              <label>
                Project name <span className="req">*</span>
              </label>
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
                minLength={4}
                placeholder="e.g. LOT 12 Horning Street"
              />
            </div>
            <div className="field">
              <label>Code</label>
              <input
                value={form.code}
                onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })}
                placeholder="Auto from initial+date"
                maxLength={32}
              />
            </div>
            <div className="field">
              <label>
                Client <span className="req">*</span>
              </label>
              <select
                required
                value={form.client_id}
                onChange={(e) => {
                  const clientId = e.target.value;
                  const client = clients.find((c) => c.id === clientId);
                  const next = { ...form, client_id: clientId };
                  if (client && (editing === "new" || !form.currency || form.currency === "USD")) {
                    next.currency = guessCurrencyFromLocation(client.location);
                  }
                  setForm(next);
                }}
              >
                <option value="">Select client…</option>
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.initial ? `[${c.initial}] ` : ""}
                    {c.name}
                    {c.location ? ` (${c.location})` : ""}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>
                Scope <span className="req">*</span>
              </label>
              <select
                required
                value={form.work_scope}
                onChange={(e) => setForm({ ...form, work_scope: e.target.value })}
              >
                {scopes.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="field field-span-2">
              <label>Assignees</label>
              <div className="assignee-checks" style={{ display: "flex", flexWrap: "wrap", gap: "8px 14px" }}>
                {employees.length === 0 ? (
                  <span className="muted">No staff roster loaded</span>
                ) : (
                  employees.map((emp) => (
                    <label key={emp.id} style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                      <input
                        type="checkbox"
                        checked={form.assignee_ids.includes(emp.id)}
                        onChange={() => toggleAssignee(emp.id)}
                      />
                      {emp.full_name} #{emp.code}
                    </label>
                  ))
                )}
              </div>
            </div>
            <div className="field">
              <label>Area (sq.ft)</label>
              <input type="number" min={0} value={form.area_sqft} onChange={(e) => setForm({ ...form, area_sqft: e.target.value })} />
            </div>
            <div className="field">
              <label>Storey</label>
              <input type="number" min={0} value={form.storeys} onChange={(e) => setForm({ ...form, storeys: e.target.value })} />
            </div>
            <div className="field">
              <label>Phase</label>
              <select value={form.phase} onChange={(e) => setForm({ ...form, phase: e.target.value })}>
                {PHASES.map((ph) => (
                  <option key={ph.id} value={ph.id}>
                    {ph.label}
                  </option>
                ))}
              </select>
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
                <div className="field field-span-2">
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
                      onChange={(e) => setForm({ ...form, contract_value: e.target.value })}
                    />
                    <div className="money-currency">
                      <CurrencySelect value={form.currency} onChange={(currency) => setForm({ ...form, currency })} required />
                    </div>
                  </div>
                </div>
                <div className="field">
                  <label>
                    Deposit % <span className="req">*</span>
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    required
                    value={form.deposit_pct}
                    onChange={(e) => setForm({ ...form, deposit_pct: e.target.value })}
                  />
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
              <h4 style={{ marginTop: 0, marginBottom: 10 }}>Daily progress %</h4>
              <div className="toolbar" style={{ marginBottom: 8, flexWrap: "wrap" }}>
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
                  {savingProgress ? "Saving…" : "Save progress"}
                </button>
              </div>
              {progressHistory.length ? (
                <ul className="muted" style={{ margin: 0, paddingLeft: 18, fontSize: 13 }}>
                  {progressHistory.slice(0, 5).map((r) => (
                    <li key={r.id}>
                      {r.work_date}: {r.percent}% — {r.employee_name || "—"}
                      {r.note ? ` (${r.note})` : ""}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="muted" style={{ margin: 0, fontSize: 13 }}>
                  No progress logged yet.
                </p>
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
                            {p.latest_progress_pct != null ? ` · ${p.latest_progress_pct}%` : ""}
                          </p>
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
                            <button type="button" className="kanban-pay-link" onClick={() => nav("/payments")}>
                              Payments →
                            </button>
                          ) : null}
                          {manager ? (
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
                <th>Assignee</th>
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
              {filtered.map((p) => (
                <tr key={p.id}>
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
                  <td>{p.assignee_name || "—"}</td>
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
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
