import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Link, Navigate, NavLink, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { fetchLive, LoginError, login, resolveWsUrl, type LiveEmployee } from "./api";
import { LoginStage3D } from "./components/LoginStage3D";
import { useToast } from "./components/ToastProvider";
import { AuthedImg } from "./components/AuthedImg";
import { GuideCard } from "./components/GuideCard";
import { RefreshButton } from "./components/RefreshButton";
import { ManagerUpdateBanner } from "./components/ManagerUpdateBanner";
import { ThemeSwitch } from "./components/ThemeSwitch";
import { AccountPage } from "./pages/AccountPage";
import { DashboardPage } from "./pages/DashboardPage";
import { DayPage } from "./pages/DayPage";
import { EmployeesPage } from "./pages/EmployeesPage";
import { ExpensesPage } from "./pages/ExpensesPage";
import { PartnerSharesPage } from "./pages/PartnerSharesPage";
import { PaymentsPage } from "./pages/PaymentsPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { ReportsPage } from "./pages/ReportsPage";
import { AccessDeniedPage, NotFoundPage } from "./pages/NotFoundPage";
import { DownloadsPage } from "./pages/DownloadsPage";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type LoginFieldErrors = { email?: string; password?: string };

function validateLogin(email: string, password: string): LoginFieldErrors {
  const next: LoginFieldErrors = {};
  const trimmed = email.trim();
  if (!trimmed) next.email = "Enter your email.";
  else if (!EMAIL_RE.test(trimmed)) next.email = "Enter a valid email address.";
  if (!password) next.password = "Enter your password.";
  return next;
}

function LoginPage() {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [busy, setBusy] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<LoginFieldErrors>({});
  const [formError, setFormError] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const next = validateLogin(email, password);
    setFieldErrors(next);
    setFormError("");
    if (next.email || next.password) {
      const first = next.email ? "email" : "password";
      document.getElementById(first)?.focus();
      return;
    }
    setBusy(true);
    try {
      const data = await login(email, password);
      localStorage.setItem("ems_token", data.access_token);
      localStorage.setItem("ems_name", data.full_name);
      localStorage.setItem("ems_role", data.role);
      localStorage.setItem("ems_employee_id", data.employee_id);
      localStorage.setItem("ems_login_hint", email.trim().toLowerCase());
      // Old layout-preview leftover — caused fake KPI boxes to flash after login
      localStorage.removeItem("ems_dash_preview");
      const role = String(data.role || "");
      if (role === "employee") nav(`/day/${data.employee_id}`);
      else nav("/");
    } catch (err) {
      const status = err instanceof LoginError ? err.status : -1;
      const message = err instanceof Error ? err.message : "Could not sign in. Try again.";
      setFormError(message);
      if (status === 401) {
        setFieldErrors({ email: " ", password: " " });
      }
      document.getElementById("password")?.focus();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-shell">
        <LoginStage3D />
        <form className="login-card login-card-3d" onSubmit={onSubmit} noValidate>
          <h1 className="login-brand-row">
            <img className="login-brand-mark" src="/favicon-192.png?v=2" alt="" width={48} height={48} />
            <span className="login-brand">CFS Designers</span>
          </h1>
          <p className="login-sub">Sign in to continue</p>
          {formError ? (
            <div className="alert-danger login-alert" role="alert" aria-live="assertive">
              <span className="alert-danger-icon" aria-hidden>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M12 9v4M12 17h.01M10.3 4.7L2.2 19a2 2 0 001.7 3h16.2a2 2 0 001.7-3L13.7 4.7a2 2 0 00-3.4 0z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </span>
              <p className="alert-danger-text">{formError}</p>
            </div>
          ) : null}
          <div className={`field${fieldErrors.email ? " is-invalid" : ""}`}>
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              inputMode="email"
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck={false}
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setFieldErrors((cur) => ({ ...cur, email: undefined }));
                setFormError("");
              }}
              autoComplete="username"
              required
              placeholder="name@cfsdesigners.com"
              aria-invalid={Boolean(fieldErrors.email)}
              aria-describedby={fieldErrors.email?.trim() ? "email-error" : undefined}
            />
            {fieldErrors.email?.trim() ? (
              <p id="email-error" className="field-error" role="alert">
                {fieldErrors.email}
              </p>
            ) : null}
          </div>
          <div className={`field${fieldErrors.password ? " is-invalid" : ""}`}>
            <label htmlFor="password">Password</label>
            <div className="password-wrap">
              <input
                id="password"
                type={showPass ? "text" : "password"}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setFieldErrors((cur) => ({ ...cur, password: undefined }));
                  setFormError("");
                }}
                autoComplete="current-password"
                required
                placeholder="••••••••"
                aria-invalid={Boolean(fieldErrors.password)}
                aria-describedby={fieldErrors.password?.trim() ? "password-error" : undefined}
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
            {fieldErrors.password?.trim() ? (
              <p id="password-error" className="field-error" role="alert">
                {fieldErrors.password}
              </p>
            ) : null}
          </div>
          <button type="submit" className="login-submit" disabled={busy} style={{ width: "100%", marginTop: 12 }}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

function isFinanceRole(): boolean {
  const r = localStorage.getItem("ems_role") || "";
  return r === "admin" || r === "manager";
}

function isPartnerRole(): boolean {
  /** Faisal / Asad profit split — admin only (never HR / employee / demo / manager). */
  return (localStorage.getItem("ems_role") || "") === "admin";
}

function isOfficeRole(): boolean {
  const r = localStorage.getItem("ems_role") || "";
  return r === "admin" || r === "manager" || r === "hr";
}

function isDemoRole(): boolean {
  return (localStorage.getItem("ems_role") || "") === "demo";
}

function isOfficeOrDemoRole(): boolean {
  return isOfficeRole() || isDemoRole();
}

function roleLabel(role: string): string {
  if (role === "admin") return "Admin";
  if (role === "manager") return "Manager";
  if (role === "hr") return "HR";
  if (role === "demo") return "Demo";
  if (role === "employee") return "Staff";
  return role;
}

function MainNavLinks({
  office,
  finance,
  partner,
  demo,
  myId,
}: {
  office: boolean;
  finance: boolean;
  partner: boolean;
  demo: boolean;
  myId: string;
}) {
  if (demo) {
    return (
      <>
        <NavLink to="/" end>
          Dashboard
        </NavLink>
        <NavLink to="/live">Live</NavLink>
        <NavLink to="/employees">Team</NavLink>
        <NavLink to="/projects">Projects</NavLink>
        <NavLink to="/expenses">Expenses</NavLink>
        <NavLink to="/downloads">Downloads</NavLink>
      </>
    );
  }
  if (office) {
    return (
      <>
        <NavLink to="/" end>
          Dashboard
        </NavLink>
        <NavLink to="/live">Live</NavLink>
        <NavLink to="/employees">Employees</NavLink>
        <NavLink to="/projects">Projects</NavLink>
        {finance ? <NavLink to="/payments">Payments</NavLink> : null}
        {partner ? <NavLink to="/partner-shares">Shares</NavLink> : null}
        <NavLink to="/expenses">Expenses</NavLink>
        <NavLink to="/reports">Reports</NavLink>
        <NavLink to="/downloads">Downloads</NavLink>
      </>
    );
  }
  return (
    <>
      {myId ? <NavLink to={`/day/${myId}`}>My Day</NavLink> : null}
      <NavLink to="/projects">My Projects</NavLink>
      <NavLink to="/downloads">Downloads</NavLink>
    </>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  const [name, setName] = useState(() => localStorage.getItem("ems_name") || "User");
  const [navOpen, setNavOpen] = useState(false);
  const [gearOpen, setGearOpen] = useState(false);
  const gearRef = useRef<HTMLDivElement>(null);
  const role = localStorage.getItem("ems_role") || "";
  const myId = localStorage.getItem("ems_employee_id") || "";
  const office = isOfficeRole();
  const finance = isFinanceRole();
  const partner = isPartnerRole();
  const demo = isDemoRole();
  const nav = useNavigate();
  const loc = useLocation();

  useEffect(() => {
    const sync = () => setName(localStorage.getItem("ems_name") || "User");
    window.addEventListener("ems-profile", sync);
    return () => window.removeEventListener("ems-profile", sync);
  }, []);

  useEffect(() => {
    setNavOpen(false);
    setGearOpen(false);
  }, [loc.pathname]);

  useEffect(() => {
    if (!navOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [navOpen]);

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (gearRef.current && !gearRef.current.contains(e.target as Node)) setGearOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setGearOpen(false);
        setNavOpen(false);
      }
    }
    document.addEventListener("click", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("click", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, []);

  function logout() {
    localStorage.removeItem("ems_token");
    localStorage.removeItem("ems_role");
    localStorage.removeItem("ems_employee_id");
    localStorage.removeItem("ems_name");
    setGearOpen(false);
    nav("/login", { replace: true });
  }

  return (
    <div className="app-shell">
      <ManagerUpdateBanner />
      <header className="topbar">
        <div className="topbar-lead">
          <div className="brand">
            <img className="brand-mark" src="/favicon-192.png?v=2" alt="" width={32} height={32} />
            <span>CFS Designers</span>
            {!office && !demo ? <small className="muted"> Staff</small> : null}
            {role === "hr" ? <span className="role-pill">HR View</span> : null}
            {demo ? <span className="role-pill role-pill-demo">Demo</span> : null}
          </div>
        </div>
        <nav className="nav nav-desktop" aria-label="Main">
          <MainNavLinks office={office} finance={finance} partner={partner} demo={demo} myId={myId} />
        </nav>
        <div className="topbar-actions">
          <div className="user-chip" title={`${name}${role ? ` · ${roleLabel(role)}` : ""}`}>
            <span className="user-chip-avatar" aria-hidden>
              {(name || "U")
                .split(/\s+/)
                .filter(Boolean)
                .slice(0, 2)
                .map((w) => w[0]?.toUpperCase() || "")
                .join("") || "U"}
            </span>
            <span className="user-chip-meta">
              <span className="user-chip-name">{name}</span>
              {role ? <span className="user-chip-role">{roleLabel(role)}</span> : null}
            </span>
          </div>
          <button
            type="button"
            className="nav-toggle"
            aria-label={navOpen ? "Close menu" : "Open menu"}
            aria-expanded={navOpen}
            onClick={() => {
              setGearOpen(false);
              setNavOpen((v) => !v);
            }}
          >
            <span />
            <span />
            <span />
          </button>
          <div className="gear-wrap" ref={gearRef}>
              <button
                type="button"
                className="gear-btn"
                aria-label="Settings"
                aria-expanded={gearOpen}
                onClick={(e) => {
                  e.stopPropagation();
                  setNavOpen(false);
                  setGearOpen((v) => !v);
                }}
              >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
                <path
                  d="M12 15.5a3.5 3.5 0 100-7 3.5 3.5 0 000 7z"
                  stroke="currentColor"
                  strokeWidth="2"
                />
                <path
                  d="M19.4 13a7.7 7.7 0 00.1-2l2.1-1.6-2-3.4-2.5.8a7.6 7.6 0 00-1.7-1L15 3.1h-4l-.4 2.7a7.6 7.6 0 00-1.7 1L6.4 6l-2 3.4L6.5 11a7.7 7.7 0 000 2l-2.1 1.6 2 3.4 2.5-.8a7.6 7.6 0 001.7 1l.4 2.7h4l.4-2.7a7.6 7.6 0 001.7-1l2.5.8 2-3.4L19.4 13z"
                  stroke="currentColor"
                  strokeWidth="1.7"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
            {gearOpen ? (
              <div className="gear-menu" role="menu">
                <div className="gear-theme" onPointerDown={(e) => e.stopPropagation()} onClick={(e) => e.stopPropagation()}>
                  <ThemeSwitch variant="menu" />
                </div>
                <Link to="/account" role="menuitem" className="gear-item" onClick={() => setGearOpen(false)}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
                    <circle cx="12" cy="8" r="3.5" stroke="currentColor" strokeWidth="1.8" />
                    <path
                      d="M5 19.5c1.6-3 4-4.5 7-4.5s5.4 1.5 7 4.5"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                    />
                  </svg>
                  Account
                </Link>
                <button
                  type="button"
                  role="menuitem"
                  className="gear-item gear-logout"
                  onPointerDown={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    logout();
                  }}
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
                    <path d="M10 7V5a2 2 0 012-2h7v18h-7a2 2 0 01-2-2v-2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                    <path d="M14 12H4m0 0l3-3m-3 3l3 3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  Logout
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </header>
      {createPortal(
        <>
          <button
            type="button"
            className={`nav-backdrop${navOpen ? " is-visible" : ""}`}
            aria-label="Close menu"
            aria-hidden={!navOpen}
            tabIndex={navOpen ? 0 : -1}
            onClick={() => setNavOpen(false)}
          />
          <nav
            className={`nav nav-mobile${navOpen ? " is-open" : ""}`}
            aria-label="Main menu"
            aria-hidden={!navOpen}
            onClick={() => setNavOpen(false)}
          >
            <div className="nav-drawer-head">
              <span className="nav-drawer-title">
                <img className="brand-mark" src="/favicon-192.png?v=2" alt="" width={28} height={28} />
                CFS Designers
              </span>
              <button
                type="button"
                className="nav-close"
                aria-label="Close menu"
                onClick={(e) => {
                  e.stopPropagation();
                  setNavOpen(false);
                }}
              >
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden>
                  <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" />
                </svg>
              </button>
            </div>
            <MainNavLinks office={office} finance={finance} partner={partner} demo={demo} myId={myId} />
            <div
              className="nav-mobile-settings"
              onClick={(e) => e.stopPropagation()}
              onPointerDown={(e) => e.stopPropagation()}
            >
              <div className="nav-mobile-theme-row">
                <span className="nav-mobile-theme-label">Appearance</span>
                <ThemeSwitch />
              </div>
              <Link to="/account" className="gear-item" onClick={() => setNavOpen(false)}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
                  <circle cx="12" cy="8" r="3.5" stroke="currentColor" strokeWidth="1.8" />
                  <path
                    d="M5 19.5c1.6-3 4-4.5 7-4.5s5.4 1.5 7 4.5"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                  />
                </svg>
                Account
              </Link>
              <button
                type="button"
                className="gear-item gear-logout"
                onPointerDown={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  logout();
                }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
                  <path d="M10 7V5a2 2 0 012-2h7v18h-7a2 2 0 01-2-2v-2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                  <path d="M14 12H4m0 0l3-3m-3 3l3 3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                Logout
              </button>
            </div>
          </nav>
        </>,
        document.body,
      )}
      {children}
      <GuideCard manager={office || demo} />
    </div>
  );
}

function DownloadsRoute() {
  if (!localStorage.getItem("ems_token")) return <Navigate to="/login" replace />;
  return (
    <Shell>
      <DownloadsPage />
    </Shell>
  );
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  if (!localStorage.getItem("ems_token")) return <Navigate to="/login" replace />;
  return <Shell>{children}</Shell>;
}

function RequireOffice({ children }: { children: React.ReactNode }) {
  if (!localStorage.getItem("ems_token")) return <Navigate to="/login" replace />;
  if (!isOfficeRole()) {
    const id = localStorage.getItem("ems_employee_id");
    return <Navigate to={id ? `/day/${id}` : "/projects"} replace />;
  }
  return <Shell>{children}</Shell>;
}

function RequireOfficeOrDemo({ children }: { children: React.ReactNode }) {
  if (!localStorage.getItem("ems_token")) return <Navigate to="/login" replace />;
  if (!isOfficeOrDemoRole()) {
    const id = localStorage.getItem("ems_employee_id");
    return <Navigate to={id ? `/day/${id}` : "/projects"} replace />;
  }
  return <Shell>{children}</Shell>;
}

function RequireFinance({ children }: { children: React.ReactNode }) {
  if (!localStorage.getItem("ems_token")) return <Navigate to="/login" replace />;
  if (!isFinanceRole()) {
    return (
      <Shell>
        <AccessDeniedPage message="HR and staff cannot open Payments or client invoices. Ask an admin if you need access." />
      </Shell>
    );
  }
  return <Shell>{children}</Shell>;
}

function RequirePartner({ children }: { children: React.ReactNode }) {
  if (!localStorage.getItem("ems_token")) return <Navigate to="/login" replace />;
  if (!isPartnerRole()) {
    return (
      <Shell>
        <AccessDeniedPage message="Partner shares are only for Faisal / Asad (admin). Your role cannot open this page." />
      </Shell>
    );
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
      ws = new WebSocket(`${resolveWsUrl("/api/v1/ws/live")}?token=${encodeURIComponent(token)}`);
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
        <RefreshButton busy={busy} onClick={() => refresh(true)} />
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

function CatchAllPage() {
  if (localStorage.getItem("ems_token")) {
    return (
      <Shell>
        <NotFoundPage />
      </Shell>
    );
  }
  return <NotFoundPage />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <RequireOfficeOrDemo>
            <DashboardPage />
          </RequireOfficeOrDemo>
        }
      />
      <Route
        path="/live"
        element={
          <RequireOfficeOrDemo>
            <LivePage />
          </RequireOfficeOrDemo>
        }
      />
      <Route
        path="/employees"
        element={
          <RequireOfficeOrDemo>
            <EmployeesPage />
          </RequireOfficeOrDemo>
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
          <RequireFinance>
            <PaymentsPage />
          </RequireFinance>
        }
      />
      <Route
        path="/partner-shares"
        element={
          <RequirePartner>
            <PartnerSharesPage />
          </RequirePartner>
        }
      />
      <Route
        path="/expenses"
        element={
          <RequireOfficeOrDemo>
            <ExpensesPage />
          </RequireOfficeOrDemo>
        }
      />
      <Route path="/downloads" element={<DownloadsRoute />} />
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
          <RequireOffice>
            <ReportsPage />
          </RequireOffice>
        }
      />
      <Route path="*" element={<CatchAllPage />} />
    </Routes>
  );
}
