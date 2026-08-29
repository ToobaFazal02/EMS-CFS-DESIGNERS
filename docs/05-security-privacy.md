# Security, privacy, legal

## Threats this product exists to stop

- Employee edits Google Sheet times.
- Employee edits local TimesheetV2/SQLite after the fact.
- Employee sets PC clock backward.

**Control:** punches become signed events; **server time** is authoritative; local DB is outbox; no UI to rewrite synced punches.

## Threats we must not create

| Threat | Control |
|---|---|
| Keylogger / password theft | Count key-downs only. Never `GetAsyncKeyState` string buffers into storage |
| Hidden surveillance | Always-visible tray + “Recording” state |
| CAD drawing leak to internet | Default on-prem disk; no third-party screenshot CDN |
| Screenshot of banking/WhatsApp | Interval capture of full desktop is still sensitive — optional blur + employee-visible gallery later; v1 at least notify |
| Manager account shared | Named logins, audit who viewed screenshots |
| Stolen laptop full of shots | Disk encryption recommended; agent encrypts outbox at rest if feasible (v1.1) |

## AuthN/Z

- Manager/admin: email+password, hashed (argon2), session or JWT.
- Agent: device enrollment (one-time code) → device token, rotatable.
- RBAC: employee / manager / admin.

## Data classes

| Class | Examples | Rule |
|---|---|---|
| Restricted | Screenshots | Manager/admin; access log |
| Internal | Window titles, click counts | Managers |
| Attendance | Punches, hours | Managers; employee own day |

## Pakistan / workplace

- Written notice in offer/handbook that PCs are monitored during work hours.
- Do not monitor after Sign Out.
- Do not capture when on Break (configurable; default **no screenshots on break**).

## Compliance-ish (pragmatic)

- Retention job (API startup + daily) deletes screenshot files and DB rows past **60 days** (`SCREENSHOT_RETENTION_DAYS`).
- Export/delete employee data on written request (admin procedure, not a public portal in v1).
