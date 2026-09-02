# Execution gate

| Key | Value |
|---|---|
| EXECUTION_APPROVED | **yes** |
| Current phase | **Employee Agent rollout (client 30–31 Aug 2026)** |
| Code allowed | Phases 1–5 + hardening + audit fixes |
| Approved by | User 24 Aug 2026 |

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

## This week (client 30–31 Aug 2026)

See `docs/42-client-voice-2026-08-30-plan.md`. **Employees first.** HR role + expenses still later.

1. Add staff (named `@cfsdesigners.com` logins + unique temp passwords)
2. Enroll each PC — Agent stays enrolled; four punch buttons only
3. Screenshots + net hours from **kal / parson**
4. Short **screen recording** of employee PC install
5. Projects + invoicing: already built — client will use **after a few days**

## After employees are live (locked)

See `docs/41-post-pilot-backlog.md`.

1. Hubstaff-style **Dashboard** as home — **done**
2. Header **gear** → Account + Logout — **done**
3. Thin **theme** scrollbars — **done**
4. Hours as **8.1 h** on day web — **done** (PDF still `2h 32m`)
5. Distinct **HR** login (attendance + projects + expenses; **no invoices**)
6. Office **expenses** sheet (chai, bills, electricity, gas, solar, parties)

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
