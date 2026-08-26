# Execution gate

| Key | Value |
|---|---|
| EXECUTION_APPROVED | **yes** |
| Current phase | **Pilot-ready — development complete** |
| Code allowed | Phases 1–5 + hardening + audit fixes |
| Approved by | User 24 Aug 2026 |

## Done

- Workforce: agent, live, day, PDF/Excel, sleep hours fix, OT, Work/Browser/Other
- Projects Design Queue + 50/50 payment gates + manager override UI
- Payments CRUD + delayed days + Excel
- Auto-seed admin + SAMPLE clients/projects/invoices on API start
- Screenshot audit only on day lightbox (`audit=1`)
- Re-enroll revokes old device tokens
- Functional audit: `AUDIT.bat` → **20/20 pass**

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
