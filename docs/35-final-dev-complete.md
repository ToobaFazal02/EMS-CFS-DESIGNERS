# Final development complete — how to run & test

**Live:** https://ems.cfsdesigners.com (`AUTO_SEED_SAMPLES=false`). Seed admin/staff below is **local demo only**. Production staff: Employees page + unique passwords. Current client ask: `docs/42-client-voice-2026-08-30-plan.md`.

## Why samples were missing before

Seed lived in `app.seed` but did **not** run on API start. Fixed: startup calls `ensure_samples()` which now also creates **admin + staff 101–104** and SAMPLE projects/invoices.

## Start

1. `RUN-API.bat` → `"report_version":"phase5-complete"`
2. Optional: `SEED-SAMPLES.bat` / `AUDIT.bat`
3. `RUN-WEB.bat` → Ctrl+F5 → `admin@cfsdesigners.com` / `Admin123!`
4. `RUN-AGENT.bat` for workforce tests

## Automated audit (API)

`AUDIT.bat` — must print **20 passed, 0 failed** covering login, samples, payment gates, day PDF, monthly PDF, Excel, screenshot audit opt-in.

## Manual checklist

### Workforce
- [ ] Sign In → LIVE blink; Sign Out / sleep ends session
- [ ] Live board + day screenshots (lightbox audits once)
- [ ] Day PDF: click graph + Work/Browser/Other + overtime
- [ ] Monthly PDF: OT column; no multi-day sleep inflation

### Projects
- [ ] Design Queue 7 columns; SAMPLE cards present
- [ ] Harbour unpaid: badge **blocked until deposit**; move → red error + override panel
- [ ] Summit: Stamped Drawings blocked until balance Paid

### Payments
- [ ] SAMPLE invoices; delayed days on 2001; Excel download
- [ ] Mark Harbour Paid → phase move works

### Agent
- [ ] Enroll → punch → screenshot; optional `"screenshot_blur": true` in `config.json`

## Deferred

Inno installer (see `packaging/`), Google Sheet sync, Postgres, employee web login without finance — need your call (see `STATUS.md`).
