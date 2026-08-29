import { useState } from "react";
import { changeMyDisplayName, changeMyEmail, changeMyPassword } from "../api";
import { PasswordField } from "../components/PasswordField";
import { useToast } from "../components/ToastProvider";

function isManagerRole(): boolean {
  const r = localStorage.getItem("ems_role") || "";
  return r === "admin" || r === "manager";
}

export function AccountPage() {
  const toast = useToast();
  const [cur, setCur] = useState("");
  const [next, setNext] = useState("");
  const [next2, setNext2] = useState("");
  const [email, setEmail] = useState("");
  const [emailPass, setEmailPass] = useState("");
  const [displayName, setDisplayName] = useState(() => localStorage.getItem("ems_name") || "");
  const manager = isManagerRole();
  const displayRole = localStorage.getItem("ems_role") || "";

  async function onDisplayName(e: React.FormEvent) {
    e.preventDefault();
    try {
      const r = await changeMyDisplayName(displayName);
      localStorage.setItem("ems_name", r.full_name);
      setDisplayName(r.full_name);
      window.dispatchEvent(new Event("ems-profile"));
      toast.success("Display name updated.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not update name");
    }
  }

  async function onPassword(e: React.FormEvent) {
    e.preventDefault();
    if (next !== next2) {
      toast.error("New passwords do not match");
      return;
    }
    try {
      await changeMyPassword(cur, next);
      setCur("");
      setNext("");
      setNext2("");
      toast.success("Password updated.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Password change failed");
    }
  }

  async function onEmail(e: React.FormEvent) {
    e.preventDefault();
    try {
      const r = await changeMyEmail(email, emailPass);
      setEmail("");
      setEmailPass("");
      toast.success(`Email updated to ${r.email}.`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Email change failed");
    }
  }

  return (
    <div className="page-account">
      <header className="page-header">
        <div>
          <h2>Account</h2>
          <p className="muted page-sub">
            {localStorage.getItem("ems_name") || "User"}
            {displayRole && !manager ? ` · ${displayRole}` : ""}
          </p>
        </div>
      </header>

      <div className="account-layout">
        <div className="account-col">
          {manager ? (
            <form className="card account-panel" onSubmit={onDisplayName}>
              <h3>Display name</h3>
              <p className="account-hint muted">Shown in the top bar after you sign in.</p>
              <div className="account-fields">
                <div className="field">
                  <label htmlFor="display-name">Your name</label>
                  <input
                    id="display-name"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    required
                    minLength={2}
                    maxLength={120}
                    autoComplete="name"
                    placeholder="e.g. Ali Khan"
                  />
                </div>
              </div>
              <div className="account-actions">
                <button type="submit">Save name</button>
              </div>
            </form>
          ) : null}

          {manager ? (
            <form className="card account-panel" onSubmit={onEmail}>
              <h3>Change login email</h3>
              <div className="account-fields">
                <div className="field">
                  <label>New email</label>
                  <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
                </div>
                <PasswordField
                  label="Confirm with current password"
                  value={emailPass}
                  onChange={setEmailPass}
                  autoComplete="current-password"
                  required
                />
              </div>
              <div className="account-actions">
                <button type="submit">Update email</button>
              </div>
            </form>
          ) : (
            <div className="card account-panel">
              <h3>Login email</h3>
              <div className="field">
                <label>Your email</label>
                <input
                  type="email"
                  value={localStorage.getItem("ems_login_hint") || "—"}
                  readOnly
                  disabled
                  className="input-readonly"
                />
              </div>
            </div>
          )}
        </div>

        <div className="account-col">
          <form className="card account-panel" onSubmit={onPassword}>
            <h3>Change password</h3>
            <div className="account-fields">
              <PasswordField label="Current password" value={cur} onChange={setCur} autoComplete="current-password" required />
              <PasswordField
                label="New password"
                value={next}
                onChange={setNext}
                autoComplete="new-password"
                required
                minLength={8}
              />
              <PasswordField
                label="Confirm new password"
                value={next2}
                onChange={setNext2}
                autoComplete="new-password"
                required
                minLength={8}
              />
            </div>
            <div className="account-actions">
              <button type="submit">Update password</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
