# Docs index — CFS Designers platform

**Product name (client):** CFS Designers  
**Internal repo folder:** `ems-cfs-designers` (ok to keep)  
**Stack:** Windows agent + FastAPI + React manager web  

Read `STATUS.md` before coding. This index is the map of every locked plan.

---

## Start here

| Doc | Purpose |
|---|---|
| `../STATUS.md` | Execution gate + current phase |
| `00-executive-brief.md` | One-page why |
| `02-product-vision.md` | What we are building |
| `03-functional-requirements.md` | **All FR** (workforce + projects + payments + later expenses) |
| `42-client-voice-2026-08-30-plan.md` | Employees first, HR, expenses |
| `45-client-voice-2026-09-03-plan.md` | **Latest client voice** — invoice PDF parity + Faisal/Asad shares |
| `46-production-audit-2026-09-09.md` | **Production audit DONE** — 404/403, security, deploy gate |
| `47-cross-device-roadmap.md` | **11 Sep 2026** Multi-device software plan — Tauri desktop + PWA mobile |
| `48-phase1-tauri-desktop.md` | **Phase 1 implementation** — Desktop app (Windows installer) step-by-step |
| `50-pre-production-test-checklist.md` | Smoke tests before live (icons, enroll UX, downloads) |
| `51-deploy-sep13-idle-reenroll-update.md` | **13 Sep 2026** Idle 30s, multi-monitor, re-enroll, update banner — deploy + honesty on auto-update |
| `52-manager-build-16gb-ram.md` | **14 Sep 2026** Why local Tauri OOM on 16GB — use GitHub Actions for Setup.exe |
| `53-finalize-desktop-web-then-mobile-plan.md` | **14–15 Sep** Desktop+Web → Agent → Projects → Admin PWA; Phase E order |
| `54-phase-e-click-background-update.md` | **15 Sep** Click → background update MVP (Agent 1.1.2 / Manager 0.1.2) |
| `57-client-trust-desktop-phase-c-plan.md` | **17 Sep** Trust recovery: Agent + Day + Phase C + Desktop ship order |
| `58-wave0-1-test-matrix.md` | **17 Sep** Wave 0+1 shipped — identity + Agent idle/shots/sound + full happy/weeping tests |
| `59-wave2-day-live-test-matrix.md` | **17 Sep** Wave 2 — Day auto-refresh + Live hint + test matrix |
| `60-wave3-phase-c-test-matrix.md` | **17 Sep** Wave 3 Phase C (C1–C5) — codes/scopes/assignees/daily % + tests |
| `61-projects-payments-flow-qa.md` | **18 Sep** Projects/payments soft gate + Detailer/Engineer QA |
| `62-remaining-work-desktop-first.md` | **18 Sep LOCKED** Desktop+Agent **100% first** on branch **`desktop+agent`** → web/mobile least priority |
| `64-signed-updater-ops.md` | P3 signed Tauri updater checklist (keys + CI) |
| `65-admin-pwa.md` | P4 Admin/**HR**-only mobile PWA (home screen; not manager/employee) |
| `66-desktop-notify-pwa-test.md` | How to run Desktop, hear notify, install Admin/HR PWA, Agent smoke |
| `pdfs/` | **Ops PDF pack v0.1.6** — QA, security, Hostinger, local, break/fix, auto-update honesty, master AI prompt |
| `63-lovable-staff-dashboard-prompt.md` | **18 Sep** Lovable prompt — Staff My dashboard aesthetic |
| `43-lovable-dashboard-prompt.md` | Copy-paste Lovable prompt — **Dashboard tab only** |
| `44-dashboard-predeploy.md` | **1 Sep 2026** Dashboard data + ultra-wide type + what to click before VPS |
| `04-non-functional-requirements.md` | **All NFR** (perf, scale, security bar) |
| `05-security-privacy.md` | Threats + controls |
| `31-projects-payments-plan-DRAFT.md` | Projects + payments + advance % plan |

---

## Client voice & WhatsApp (saved)

| Doc / folder | Content |
|---|---|
| `21-client-voice-2026-08-20-plan.md` | Live board, black/gold, 4 punches, red LIVE blink |
| `30-client-voice-2026-08-21-plan.md` | Projects + invoicing + roles + one system |
| `31-projects-payments-plan-DRAFT.md` | Sheet columns, Design Queue, 50/50 advance, gates |
| `32-client-voice-index.md` | **All audio transcripts mapped** |
| `42-client-voice-2026-08-30-plan.md` | Employee-first rollout, HR vs invoices, expenses, 8.1 hours |
| `45-client-voice-2026-09-03-plan.md` | Invoice PDF exact match + Faisal/Asad partner share |
| `../references/client-voice-2026-08-20-*.txt` | 20 Aug transcript |
| `../references/client-voice-2026-08-21/*.txt` | 21 Aug (8 notes) transcripts |
| `../references/client-voice-2026-08-30/` | 30–31 Aug (5 notes) transcripts |
| `../references/client-voice-2026-09-03/` | 3 Sep (3 notes) transcripts + interpreted EN |

---

## Phase plans

| Doc | Phase |
|---|---|
| `09-phases-estimate.md` | Original estimate bands |
| `27-phase2-plan.md` | Phase 2.1–2.2 delivery |
| `29-test-phase2.1.md` | Test checklist |
| `22-phase1-runbook.md` | How to run Phase 1 |

---

## Architecture & quality

`06-tech-stack` · `07-architecture` · `10-data-model` · `12-engineering-quality` · `13-data-storage` · `14-ui-theme` · `15-frontend-quality` · `18-reports` · `19-responsive` · `20-idle-sessions-pdf`

---

## What is done vs next

| Area | Status |
|---|---|
| Workforce (agent, live, reports, PDF graph) | **Done** (Phase 1–2) — **pilot enroll now** (30 Aug voice) |
| Waves 0–3 (trust + Phase C) | **Code in tree** — see `62` for Desktop ship gap |
| Wave 4 Manager Setup / Desktop receive | **Next** — `docs/62-remaining-work-desktop-first.md` |
| Rebrand → CFS Designers | **Done** on live `https://ems.cfsdesigners.com` |
| Projects Kanban + payment gates | **Built** — client said use **after** employees are live |
| Payments Tracking | **Built** (admin only) — same: after employee week |
| Distinct **HR** login (no invoices) | **Done** Sep 2026 |
| Office **expenses** + receipts + month/year totals | **Done** Sep 2026 |
| Demo role + `is_demo` isolation | **Done** Sep 2026 |
| Invoice PDF = client sample (COST, no COMMENTS, spacing) | **Next** — `docs/45` P0 (awaiting approval) |
| Faisal / Asad partner share ledger | **Planned** — `docs/45` P1 |
| Report hours as **8.1 / 8.2** | **Done** on web (day + dashboard). PDF may still use `2h 32m` |
| Hubstaff dashboard / gear / scrollbars | **Done** — real API data, device type scale (`docs/19`, `docs/44`) |
| Dark / Light + first-5-visit guides | **Done** — Account appearance; Skip/Next cards (`docs/14`) |
| Idle 30s + multi-monitor SS + re-enroll + update banner | **Code done** 13 Sep — ship binaries via `docs/51` |
| Silent force auto-update (no click) | **Later** — not in v1.1.0 (banner + download only) |
