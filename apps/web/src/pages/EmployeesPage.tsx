import { useEffect, useState } from "react";
import {
  createEmployee,
  deleteEmployee,
  fetchEmployees,
  setEmployeeCredentials,
  startEnroll,
  type Employee,
} from "../api";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { EnrollCodeDialog } from "../components/EnrollCodeDialog";
import { PasswordField } from "../components/PasswordField";
import { useToast } from "../components/ToastProvider";

export function EmployeesPage() {
  const toast = useToast();
  const [rows, setRows] = useState<Employee[]>([]);
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [credId, setCredId] = useState<string | null>(null);
  const [credEmail, setCredEmail] = useState("");
  const [credPass, setCredPass] = useState("");
  const [busy, setBusy] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Employee | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [enrollModal, setEnrollModal] = useState<{
    employee: Employee;
    code: string;
    reenroll: boolean;
  } | null>(null);

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

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      await createEmployee({
        code,
        full_name: name,
        email,
        password,
        role: "employee",
      });
      toast.success("Staff added.");
      setCode("");
      setName("");
      setEmail("");
      setPassword("");
      await load(true);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not add employee.");
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

  async function onSetCreds(e: React.FormEvent) {
    e.preventDefault();
    if (!credId) return;
    try {
      await setEmployeeCredentials(credId, credEmail, credPass);
      toast.success("Login reset.");
      setCredId(null);
      setCredEmail("");
      setCredPass("");
      await load(true);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not set login.");
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    setDeleting(true);
    try {
      await deleteEmployee(pendingDelete.id);
      if (credId === pendingDelete.id) setCredId(null);
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

      <form className="card" style={{ marginBottom: 16 }} onSubmit={onCreate}>
        <h3 style={{ marginTop: 0 }}>Add staff (web login + Agent)</h3>
        <div className="toolbar">
          <div className="field">
            <label>Code</label>
            <input value={code} onChange={(e) => setCode(e.target.value)} required placeholder="105" />
          </div>
          <div className="field">
            <label>Full name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Name" />
          </div>
          <div className="field">
            <label>Login email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="name@cfsdesigners.com"
            />
          </div>
          <PasswordField
            label="Temp password"
            value={password}
            onChange={setPassword}
            autoComplete="new-password"
            required
            minLength={8}
          />
          <button type="submit">Add employee</button>
        </div>
      </form>

      {credId ? (
        <form className="card" style={{ marginBottom: 16 }} onSubmit={onSetCreds}>
          <h3 style={{ marginTop: 0 }}>Set / reset web login</h3>
          <div className="toolbar">
            <div className="field">
              <label>Email</label>
              <input type="email" value={credEmail} onChange={(e) => setCredEmail(e.target.value)} required />
            </div>
            <PasswordField
              label="New password"
              value={credPass}
              onChange={setCredPass}
              autoComplete="new-password"
              required
              minLength={8}
            />
            <button type="submit">Save login</button>
            <button type="button" className="secondary" onClick={() => setCredId(null)}>
              Cancel
            </button>
          </div>
        </form>
      ) : null}

      <div className="card" style={{ overflowX: "auto" }}>
        <table className="table-center">
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
                  <td>{r.code}</td>
                  <td>{r.full_name}</td>
                  <td>{r.email || "—"}</td>
                  <td>{r.role}</td>
                  <td>
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
                  <td>
                    {r.role === "employee" ? (
                      <div className="row-actions">
                        <button type="button" className="secondary" onClick={() => onEnroll(r, enrolled)}>
                          {enrolled ? "Re-enroll" : "Enroll PC"}
                        </button>
                        <button
                          type="button"
                          className="secondary"
                          onClick={() => {
                            setCredId(r.id);
                            setCredEmail(r.email || "");
                            setCredPass("");
                          }}
                        >
                          Set login
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
