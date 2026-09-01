import { useEffect, useRef, useState } from "react";
import {
  createEmployee,
  deleteEmployee,
  fetchEmployees,
  startEnroll,
  updateEmployee,
  type Employee,
} from "../api";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { EnrollCodeDialog } from "../components/EnrollCodeDialog";
import { PasswordField } from "../components/PasswordField";
import { useToast } from "../components/ToastProvider";

function emptyForm() {
  return { code: "", name: "", email: "", password: "" };
}

export function EmployeesPage() {
  const toast = useToast();
  const formRef = useRef<HTMLFormElement>(null);
  const [rows, setRows] = useState<Employee[]>([]);
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [editing, setEditing] = useState<Employee | null>(null);
  const [busy, setBusy] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Employee | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [enrollModal, setEnrollModal] = useState<{
    employee: Employee;
    code: string;
    reenroll: boolean;
  } | null>(null);

  function resetForm() {
    const blank = emptyForm();
    setCode(blank.code);
    setName(blank.name);
    setEmail(blank.email);
    setPassword(blank.password);
    setEditing(null);
  }

  function startEdit(emp: Employee) {
    setEditing(emp);
    setCode(emp.code);
    setName(emp.full_name);
    setEmail(emp.email || "");
    setPassword("");
    window.requestAnimationFrame(() => {
      formRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  async function load(silent = false) {
    setBusy(true);
    try {
      setRows(await fetchEmployees());
    } catch (e) {
      if (!silent) toast.error(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    load(true).catch(() => undefined);
    const t = setInterval(() => {
      load(true).catch(() => undefined);
    }, 4000);
    return () => clearInterval(t);
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      if (editing) {
        await updateEmployee(editing.id, {
          code,
          full_name: name,
          email,
          ...(password.trim() ? { password: password.trim() } : {}),
        });
        toast.success("Employee updated.");
        resetForm();
      } else {
        await createEmployee({
          code,
          full_name: name,
          email,
          password,
          role: "employee",
        });
        toast.success("Staff added.");
        resetForm();
      }
      await load(true);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : editing ? "Could not update employee." : "Could not add employee.");
    }
  }

  async function onEnroll(emp: Employee, reenroll: boolean) {
    try {
      const data = await startEnroll(emp.id);
      setEnrollModal({ employee: emp, code: data.enroll_code, reenroll });
      await load(true);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Enroll failed.");
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    setDeleting(true);
    try {
      await deleteEmployee(pendingDelete.id);
      if (editing?.id === pendingDelete.id) resetForm();
      setPendingDelete(null);
      toast.success("Staff removed.");
      await load(true);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Remove failed.");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div>
      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title="Remove staff?"
        message={
          pendingDelete
            ? `Remove “${pendingDelete.full_name}” (#${pendingDelete.code})? Login and PC enroll stop. Past hours/screenshots stay in reports.`
            : ""
        }
        confirmLabel="Remove"
        busy={deleting}
        onCancel={() => !deleting && setPendingDelete(null)}
        onConfirm={confirmDelete}
      />
      <EnrollCodeDialog
        open={Boolean(enrollModal)}
        employeeName={enrollModal?.employee.full_name || ""}
        employeeCode={enrollModal?.employee.code || ""}
        enrollCode={enrollModal?.code || ""}
        reenroll={enrollModal?.reenroll}
        onClose={() => setEnrollModal(null)}
      />

      <div className="toolbar">
        <h2 style={{ margin: 0, flex: 1 }}>Employees</h2>
        <button type="button" className="secondary" onClick={() => load()} disabled={busy}>
          {busy ? "Refreshing…" : "↻ Refresh"}
        </button>
      </div>

      <form className="card staff-add-form" onSubmit={onSubmit} ref={formRef}>
        <h3 style={{ marginTop: 0 }}>{editing ? `Edit ${editing.full_name}` : "Add staff (web login + Agent)"}</h3>
        <div className="staff-add-grid">
          <div className="field">
            <label htmlFor="staff-code">Code</label>
            <input
              id="staff-code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
              placeholder="105"
            />
          </div>
          <div className="field">
            <label htmlFor="staff-name">Full name</label>
            <input
              id="staff-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              placeholder="Name"
            />
          </div>
          <div className="field">
            <label htmlFor="staff-email">Login email</label>
            <input
              id="staff-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="name@cfsdesigners.com"
            />
          </div>
          <PasswordField
            id="staff-password"
            label={editing ? "New password (optional)" : "Temp password"}
            value={password}
            onChange={setPassword}
            autoComplete="new-password"
            required={!editing}
            minLength={8}
          />
          <div className="staff-add-actions">
            <button type="submit">{editing ? "Save changes" : "Add employee"}</button>
            {editing ? (
              <button type="button" className="secondary" onClick={resetForm}>
                Cancel
              </button>
            ) : null}
          </div>
        </div>
      </form>

      <div className="card" style={{ overflowX: "auto" }}>
        <table className="table-center staff-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Device</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const enrolled = Boolean(r.enrolled || r.enrolled_at || r.enrolled_hostname);
              return (
                <tr key={r.id}>
                  <td data-label="Code">{r.code}</td>
                  <td data-label="Name">{r.full_name}</td>
                  <td data-label="Email">{r.email || "—"}</td>
                  <td data-label="Role">{r.role}</td>
                  <td data-label="Device">
                    {r.role !== "employee" ? (
                      "—"
                    ) : enrolled ? (
                      <span title={r.enrolled_hostname || ""}>
                        Enrolled{r.enrolled_hostname ? ` · ${r.enrolled_hostname}` : ""}
                      </span>
                    ) : (
                      "Not enrolled"
                    )}
                  </td>
                  <td data-label="Actions">
                    {r.role === "employee" ? (
                      <div className="row-actions">
                        <button type="button" className="secondary" onClick={() => startEdit(r)}>
                          Edit
                        </button>
                        <button type="button" className="secondary" onClick={() => onEnroll(r, enrolled)}>
                          {enrolled ? "Re-enroll" : "Enroll PC"}
                        </button>
                        <button type="button" className="btn-danger btn-row-del" onClick={() => setPendingDelete(r)}>
                          Remove
                        </button>
                      </div>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
