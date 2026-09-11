/**
 * Public downloads hub — Manager desktop app + Employee Agent.
 * Enroll code still required (security); staff install themselves.
 */
export function DownloadsPage() {
  const managerSetupUrl = "/downloads/CFS-Designers-Manager-Setup.exe";
  const managerMsiUrl = "/downloads/CFS-Designers-Manager.msi";
  const agentUrl = "/downloads/CFS-Agent-Install.zip";

  return (
    <div className="downloads-page">
      <div className="toolbar">
        <div>
          <h2 style={{ margin: 0 }}>Downloads</h2>
          <p className="muted page-sub">Install CFS Designers software on your devices</p>
        </div>
      </div>

      <div className="downloads-grid">
        <article className="card downloads-card">
          <p className="downloads-kicker">Admin · HR · Partners</p>
          <h3>Manager Desktop App</h3>
          <p className="muted">
            Windows software — Dashboard, Employees, Payments, Expenses. Opens like VS Code (no browser
            bar). Same login as the website.
          </p>
          <ol className="downloads-steps">
            <li>Download and run the installer</li>
            <li>Open <strong>CFS Designers</strong> from Start Menu</li>
            <li>Sign in with your office email</li>
          </ol>
          <div className="downloads-btn-row">
            <a className="downloads-btn" href={managerSetupUrl} download>
              Download Setup (.exe)
            </a>
            <a className="downloads-btn downloads-btn-secondary" href={managerMsiUrl} download>
              Download MSI
            </a>
          </div>
          <p className="muted downloads-hint">Windows 10 / 11 · Prefer Setup.exe · Requires internet</p>
        </article>

        <article className="card downloads-card">
          <p className="downloads-kicker">Employees · Office PCs</p>
          <h3>Employee Agent</h3>
          <p className="muted">
            Tracking app for CAD PCs — Sign In / Out and screenshots. Install yourself; ask Admin for an
            enroll code (do not share codes publicly).
          </p>
          <ol className="downloads-steps">
            <li>Download the Agent zip on your work PC</li>
            <li>Extract → run <code>INSTALL-AGENT.bat</code> (or follow README inside)</li>
            <li>Admin → Employees → Enroll PC → paste the code in Agent</li>
            <li>Sign In when you start work</li>
          </ol>
          <a className="downloads-btn downloads-btn-secondary" href={agentUrl} download>
            Download Agent (.zip)
          </a>
          <p className="muted downloads-hint">One enroll code per employee PC · Admin only generates codes</p>
        </article>
      </div>

      <article className="card downloads-security">
        <h3>Security (why enroll codes)</h3>
        <p className="muted" style={{ marginBottom: 0 }}>
          Anyone can download Agent, but it cannot send attendance or screenshots until Admin creates an
          enroll code for that person. Codes are one-time and tied to one PC. Never put passwords in
          URLs or chat screenshots.
        </p>
      </article>
    </div>
  );
}
