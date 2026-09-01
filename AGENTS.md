# CFS Designers

Workplace **Employee Management System** for CFS Designers (Cold Formed Steel / LGS detailing). Not a website clone. Not a TimesheetV2 pixel-clone only.

## What this is

Two surfaces, one system:

1. **Windows agent** on each employee PC — sign in / break / sign out, mouse+keyboard *counts*, active window title, periodic screenshots, offline queue, end-of-day PDF.
2. **Admin web** for managers — live presence + activity, day timeline, screenshot gallery, attendance that employees cannot rewrite.

Google Sheet attendance is the **legacy process to replace**, not the architecture.

## Hard rules

- Read `STATUS.md` first. If `EXECUTION_APPROVED` is `no`, do not implement application code.
- Read `docs/08-open-questions-client.md` before inventing product behavior.
- Always follow `.cursor/rules/07-engineering-standards.mdc` and `docs/23-engineering-playbook.md`: modular clean code, one tested slice at a time, security, performance, docs, mentor-style test steps for the user.
- Keystroke **count only**. Never capture, store, or transmit typed characters (no password/keylogger).
- Monitoring is **disclosed workplace tooling**, not hidden spyware. Agent UI must show recording state.
- CAD screenshots are **client IP**. Default: office/on-prem storage, not random public cloud.
- Do not pivot this product into general HR/payroll/ERP unless asked.

## Canonical docs (read on demand, do not dump all into every turn)

| File | When |
|---|---|
| `docs/00-executive-brief.md` | Any new chat / orientation |
| `docs/01-current-state.md` | Sheet, TimesheetV2, voice notes |
| `docs/03-functional-requirements.md` | Features |
| `docs/04-non-functional-requirements.md` | Scale, safety, ops |
| `docs/05-security-privacy.md` | Auth, data, legal |
| `docs/06-tech-stack.md` | Languages and why |
| `docs/07-architecture.md` | Components and data flow |
| `docs/08-open-questions-client.md` | Client confirms / adjusts defaults |
| `docs/09-phases-estimate.md` | Delivery slices |
| `docs/11-questions-explained-and-market-defaults.md` | What each question means + market practice |
| `docs/12-engineering-quality.md` | Test-before-next, latest docs, no shortcuts |
| `docs/13-data-storage.md` | Where data lives (DB, screenshots, backups) |
| `docs/14-ui-theme.md` | Black / navy / white tokens |
| `docs/15-frontend-quality.md` | Buttons, type, a11y, consistency |
| `docs/16-signout-vs-manager.md` | Tracking stop ≠ manager loses data |
| `docs/17-vpn-plain.md` | What VPN means |
| `docs/18-reports-daily-monthly.md` | Daily + monthly reports |
| `docs/19-responsive.md` | All screen sizes, no tiny island on 4K |
| `docs/44-dashboard-predeploy.md` | Dashboard real data + ultra-wide fonts + pre-VPS clicks |
| `docs/20-idle-sessions-pdf.md` | Idle detection, multi-session day, PDF template |
| `docs/21-client-voice-2026-08-20-plan.md` | Latest client voice — finalize before code |
| `docs/22-phase1-runbook.md` | How to run Phase 1 locally |
| `docs/23-engineering-playbook.md` | Agile chunks, roles, DoD, mentor testing |
| `docs/24-manual-test-checklist.md` | Step-by-step feature tests (mentor) |
| `docs/25-client-handover.md` | How to hand over to client |
| `docs/26-delivery-budget-tools.md` | Docker, client costs, XLSX vs CSV, PM tools |

## Stack (proposed — locked only after user approval)

- Agent: Python 3.11, PySide6, local SQLite outbox
- API: FastAPI, PostgreSQL, WebSockets
- Web: React + TypeScript + Vite
- PHP-only or website-only is **rejected** for the recorder (browsers cannot hook clicks/windows/screenshots)

## Scale assumption

Now **10–12** employees, design for **50** without rewrite. Live dashboard + end-of-day reports both required.
