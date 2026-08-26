# Phase 2 — started

Phase 1 MVP is in pilot. Phase 2 adds delivery hardening and report polish.

## Phase 2.1 (this sprint) — done

| Item | Status |
|---|---|
| Clean reports (no instructional filler lines) | Done |
| Excel tables only (no broken charts) | Done |
| Admin View + Download | Done |
| Monthly PDF (team) | Done |
| Agent Install + Windows Login Autostart | Done (`INSTALL-AGENT.bat`) |
| Sleep auto Sign Out + stale hours cap | Done |
| Wide-screen responsive web UI | Done |
| Red danger alerts (no native alert boxes) | Done |
| PDF graph: dynamic clicks, 9–5 PKT, date+time labels | Done (`timesheet-v4`) |

## Phase 2.2

| Item | Notes |
|---|---|
| Agent tray icon | **Done** |
| Screenshot blur option | **Done** (`screenshot_blur` in agent config) |
| Work vs Other apps on PDF | **Done** (Work / Browser / Other) |
| Overtime rules | **Done** (`OVERTIME_HOURS_PER_DAY`, monthly OT column) |
| Simple Windows installer (.exe) | Script ready: `packaging/agent-installer.iss` — compile when Inno installed |
| Google Sheet sync | Deferred — optional client ask |
| 50+ users / Postgres | Deferred |

## How to install agent (employee PC)

1. Copy `apps/agent` folder (or deliver ZIP)
2. Double-click **`INSTALL-AGENT.bat`**
3. Enroll with manager code
4. Agent will start on next Windows login

Remove autostart: **`REMOVE-AUTOSTART.bat`**
