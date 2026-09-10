# Execution gate

| Key | Value |
|---|---|
| EXECUTION_APPROVED | **yes** |
| Current phase | **Production ready (code)** — see `docs/46-production-audit-2026-09-09.md` |
| Code allowed | Phases 1–5 + hardening + doc 45 + 404/403 |
| Approved by | User 24 Aug 2026 (product); **9 Sep 2026** production audit DONE |

## Done

- Workforce: agent, live, day, PDF/Excel, sleep hours fix, OT, Work/Browser/Other
- Projects Design Queue + 50/50 payment gates + manager override UI
- Payments CRUD + delayed days + Excel
- Auto-seed admin + SAMPLE clients/projects/invoices on API start
- Screenshot audit only on day lightbox (`audit=1`)
- Re-enroll revokes old device tokens
- Screenshot files auto-delete after **60 days**
- Phone-responsive manager web (hamburger, screenshot fill, staff cards)
- Dashboard as home; gear menu; gold scrollbars; day hours as **8.1 h**
- Dashboard: real API data only (no fake invoice rows / no hour-preview flash); 2560 fills like 1440 (`docs/44-dashboard-predeploy.md`)
- Account **Dark / Light** + first-5-visit Skip/Next guide cards (`docs/14-ui-theme.md`)

## Latest client voice (3 Sep 2026) — implementing

See `docs/45-client-voice-2026-09-03-plan.md`. Q1–Q5 locked 7 Sep.

1. **P0** Invoice PDF exact match (COST $, drop COMMENTS, spacing, maroon) — **code done**
2. **P1** Faisal / Asad share: paid invoices − expenses → ÷ 2 (admin/partner only) — **code done**

## Ops still open (30–31 Aug)

See `docs/42-client-voice-2026-08-30-plan.md`.

## In Progress (11 Sep 2026)

**Phase 1: Desktop App (Tauri)** — Manager software with Windows installer, native feel like VSCode — `docs/47-cross-device-roadmap.md`, `docs/48-phase1-tauri-desktop.md`

## Next (ops — not code blockers)

1. Add staff + enroll Agent PCs + short install video
2. Screenshots + net hours in daily use

## Shipped since pilot docs

See `docs/41-post-pilot-backlog.md`.

1. Hubstaff-style **Dashboard** as home — **done**
2. Header **gear** → Account + Logout — **done**
3. Thin **theme** scrollbars — **done**
4. Hours as **8.1 h** on day web — **done** (PDF still `2h 32m`)
5. Distinct **HR** login + office **expenses** + receipts — **done**
6. Demo role isolation — **done**
7. Site-wide maroon (replace bright red) — **done** on web; PDF leftover in P0

## Explicitly deferred (need you / later machine)

| Item | What I need from you |
|---|---|
| Inno `.exe` installer | Optional — install Inno Setup later; pilot uses `INSTALL-AGENT.bat` |
| Google Sheet sync | **Not recommended** — app replaces Excel; export already exists |
| Postgres | **Not yet** — SQLite fine for pilot (&lt;50 users) |
| Office LAN IP | Only when other PCs connect — put in agent `api_base` |

## Roles (client req — done)

- Admin/CEO: full web including Payments $
- Employee web: My Day + My Projects only (no $)
- Agent: Sign In/Out on Windows PC

Test: `docs/37-client-handover-ur-en.md` + images in `docs/visuals/`
