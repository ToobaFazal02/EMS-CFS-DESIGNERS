import { useEffect, useState } from "react";
import { Link, Navigate, NavLink, Route, Routes, useNavigate } from "react-router-dom";
import { fetchLive, login, type LiveEmployee } from "./api";
import { LoginStage3D } from "./components/LoginStage3D";
import { useToast } from "./components/ToastProvider";
import { AccountPage } from "./pages/AccountPage";
import { DayPage } from "./pages/DayPage";
import { EmployeesPage } from "./pages/EmployeesPage";
import { PaymentsPage } from "./pages/PaymentsPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { ReportsPage } from "./pages/ReportsPage";

function LoginPage() {
  const nav = useNavigate();
  const toast = useToast();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const data = await login(email, password);
      localStorage.setItem("ems_token", data.access_token);
      localStorage.setItem("ems_name", data.full_name);
      localStorage.setItem("ems_role", data.role);
      localStorage.setItem("ems_employee_id", data.employee_id);
      localStorage.setItem("ems_login_hint", email.trim().toLowerCase());
      const role = String(data.role || "");
      if (role === "employee") nav(`/day/${data.employee_id}`);
      else nav("/");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-shell">
        <LoginStage3D />
        <form className="login-card login-card-3d" onSubmit={onSubmit}>
          <h1>
            <span className="login-brand">CFS Designers</span>
          </h1>
          <p className="login-sub">Sign in to continue</p>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
              required
              placeholder="name@cfsdesigners.com"
            />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <div className="password-wrap">
              <input
                id="password"
                type={showPass ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
                placeholder="••••••••"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPass((v) => !v)}
                aria-label={showPass ? "Hide password" : "Show password"}
                title={showPass ? "Hide password" : "Show password"}
              >
                {showPass ? (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
                    <path
                      d="M3 3l18 18M10.5 10.7a2.5 2.5 0 003.3 3.3M9.9 5.6A10.5 10.5 0 0112 5.5c5 0 9.3 3.1 11 7.5a12.3 12.3 0 01-4.1 4.9M6.1 6.1A12.2 12.2 0 001 13c1.7 4.4 6 7.5 11 7.5 1.4 0 2.8-.2 4.1-.7"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                ) : (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
                    <path
                      d="M1 12s4-7.5 11-7.5S23 12 23 12s-4 7.5-11 7.5S1 12 1 12z"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinejoin="round"
                    />
                    <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2" />
                  </svg>
                )}
              </button>
            </div>
          </div>
          <button type="submit" className="login-submit" disabled={busy} style={{ width: "100%", marginTop: 12 }}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

function isManagerRole(): boolean {
  const r = localStorage.getItem("ems_role") || "";
  return r === "admin" || r === "manager";
}

function roleLabel(role: string): string {
  if (role === "admin") return "Admin";
  if (role === "manager") return "Manager";
  if (role === "employee") return "Staff";
  return role;
}

function Shell({ children }: { children: React.ReactNode }) {
  const [name, setName] = useState(() => localStorage.getItem("ems_name") || "User");
  const role = localStorage.getItem("ems_role") || "";
  const myId = localStorage.getItem("ems_employee_id") || "";
  const manager = isManagerRole();
  const nav = useNavigate();

  useEffect(() => {
    const sync = () => setName(localStorage.getItem("ems_name") || "User");
    window.addEventListener("ems-profile", sync);
    return () => window.removeEventListener("ems-profile", sync);
  }, []);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span>CFS Designers</span>
          {!manager ? <small className="muted" style={{ marginLeft: 8 }}>Staff</small> : null}
        </div>
        <nav className="nav">
          {manager ? (
            <>
              <NavLink to="/" end>
                Live
              </NavLink>
              <NavLink to="/employees">Employees</NavLink>
              <NavLink to="/projects">Projects</NavLink>
              <NavLink to="/payments">Payments</NavLink>
              <NavLink to="/reports">Reports</NavLink>
              <NavLink to="/account">Account</NavLink>
            </>
          ) : (
            <>
              {myId ? <NavLink to={`/day/${myId}`}>My Day</NavLink> : null}
              <NavLink to="/projects">My Projects</NavLink>
              <NavLink to="/account">Account</NavLink>
            </>
          )}
        </nav>
        <div className="user-chip">
          <span className="user-chip-name">
            {name}
            {!manager && role ? <span className="user-chip-role"> · {roleLabel(role)}</span> : null}
          </span>
          <button
            className="secondary"
            type="button"
            onClick={() => {
              localStorage.removeItem("ems_token");
              localStorage.removeItem("ems_role");
              localStorage.removeItem("ems_employee_id");
              localStorage.removeItem("ems_name");
              nav("/login");
            }}
          >
            Logout
          </button>
        </div>
      </header>
      {children}
    </div>
  );
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  if (!localStorage.getItem("ems_token")) return <Navigate to="/login" replace />;
  return <Shell>{children}</Shell>;
}

function RequireManager({ children }: { children: React.ReactNode }) {
  if (!localStorage.getItem("ems_token")) return <Navigate to="/login" replace />;
  if (!isManagerRole()) {
    const id = localStorage.getItem("ems_employee_id");
    return <Navigate to={id ? `/day/${id}` : "/projects"} replace />;
  }
  return <Shell>{children}</Shell>;
}

function LivePage() {
  const toast = useToast();
  const [rows, setRows] = useState<LiveEmployee[]>([]);
  const [busy, setBusy] = useState(false);
  const [tick, setTick] = useState(0);
  const token = localStorage.getItem("ems_token") || "";

  async function refresh(notify = false) {
    setBusy(true);
    try {
      setRows(await fetchLive());
      setTick((n) => n + 1);
    } catch (e) {
      if (notify) toast.error(e instanceof Error ? e.message : "Error");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    refresh(false);
    const t = setInterval(() => refresh(false), 5000);
    let ws: WebSocket | null = null;
    try {
      const proto = location.protocol === "https:" ? "wss" : "ws";
      ws = new WebSocket(`${proto}://${location.host}/api/v1/ws/live?token=${encodeURIComponent(token)}`);
      ws.onmessage = () => refresh(false);
    } catch {
      /* poll only */
    }
    return () => {
      clearInterval(t);
      ws?.close();
    };
  }, [token]);

  return (
    <div>
      <div className="toolbar">
        <h2 style={{ margin: 0, flex: 1 }}>Live board</h2>
        <button type="button" className="secondary" onClick={() => refresh(true)} disabled={busy}>
          {busy ? "Refreshing…" : "↻ Refresh"}
        </button>
      </div>
      <div className="grid-live">
        {rows.map((r) => (
          <article className="card" key={r.employee_id}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "flex-start" }}>
              <h3 style={{ textAlign: "center", flex: 1 }}>
                {r.full_name} <span className="muted">#{r.code}</span>
              </h3>
              <span className="status">
                <i className={`dot ${r.status}`} /> {r.status}
              </span>
            </div>
            <p className="muted" title={r.last_window} style={{ textAlign: "center" }}>
              {r.last_window || "—"}
            </p>
            <p className="muted" style={{ textAlign: "center" }}>
              Δ clicks {r.last_clicks_delta} · keys {r.last_keys_delta}
              {r.status === "idle" ? ` · idle ${r.idle_seconds}s` : ""}
            </p>
            {r.last_screenshot_url ? (
              <AuthedImg
                key={`${r.last_screenshot_url}-${tick}-${r.last_seen_at || ""}`}
                path={`${r.last_screenshot_url}${r.last_screenshot_url.includes("?") ? "&" : "?"}v=${tick}`}
                className="thumb"
                alt={`Last screen ${r.full_name}`}
              />
            ) : (
              <div className="thumb thumb-empty" role="img" aria-label="No screenshot yet">
                <span>No screenshot yet</span>
              </div>
            )}
            <p style={{ marginTop: 10, textAlign: "center" }}>
              <Link to={`/day/${r.employee_id}`}>Day detail →</Link>
            </p>
          </article>
        ))}
        {!rows.length ? <p className="muted">No employees yet.</p> : null}
      </div>
    </div>
  );
}

export function AuthedImg({
  path,
  className,
  alt,
  audit = false,
}: {
  path: string;
  className?: string;
  alt: string;
  /** When true, server writes screenshot_view audit (day lightbox only). */
  audit?: boolean;
}) {
  const [src, setSrc] = useState("");
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let url = "";
    let cancelled = false;
    setSrc("");
    setFailed(false);
    const token = localStorage.getItem("ems_token") || "";
    const clean = path.split("?")[0];
    const fetchPath = audit ? `${clean}${clean.includes("?") ? "&" : "?"}audit=1` : clean;
    fetch(fetchPath, { headers: { Authorization: `Bearer ${token}` }, cache: "no-store" })
      .then((r) => {
        if (!r.ok) throw new Error("img");
        return r.blob();
      })
      .then((b) => {
        if (cancelled) return;
        if (!b || b.size < 32) throw new Error("empty");
        url = URL.createObjectURL(b);
        setSrc(url);
      })
      .catch(() => {
        if (!cancelled) {
          setFailed(true);
          setSrc("");
        }
      });
    return () => {
      cancelled = true;
      if (url) URL.revokeObjectURL(url);
    };
  }, [path, audit]);
  if (failed) {
    return (
      <div className={`${className || ""} thumb-empty`} role="img" aria-label="Screenshot unavailable">
        <span>Unavailable</span>
        <small>Could not load this capture</small>
      </div>
    );
  }
  if (!src) {
    return (
      <div className={`${className || ""} thumb-empty`} role="img" aria-label="Loading screenshot">
        <span>Loading…</span>
      </div>
    );
  }
  return <img className={className} src={src} alt={alt} />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <RequireManager>
            <LivePage />
          </RequireManager>
        }
      />
      <Route
        path="/employees"
        element={
          <RequireManager>
            <EmployeesPage />
          </RequireManager>
        }
      />
      <Route
        path="/day/:id"
        element={
          <RequireAuth>
            <DayPage />
          </RequireAuth>
        }
      />
      <Route
        path="/projects"
        element={
          <RequireAuth>
            <ProjectsPage />
          </RequireAuth>
        }
      />
      <Route
        path="/payments"
        element={
          <RequireManager>
            <PaymentsPage />
          </RequireManager>
        }
      />
      <Route
        path="/account"
        element={
          <RequireAuth>
            <AccountPage />
          </RequireAuth>
        }
      />
      <Route
        path="/reports"
        element={
          <RequireManager>
            <ReportsPage />
          </RequireManager>
        }
      />
    </Routes>
  );
}
