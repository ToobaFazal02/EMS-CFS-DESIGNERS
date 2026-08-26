# Automated functional audit — 24 Aug 2026

Ran: `python -m app.audit` → **20 passed, 0 failed**

| Check | Result |
|---|---|
| SAMPLE clients/projects/invoices | PASS |
| Health `phase5-complete` | PASS |
| Manager login | PASS |
| Live / Employees / Clients / Projects / Invoices | PASS |
| Harbour `need_deposit` + Intake 409 | PASS |
| Summit Stamped Drawings 409 | PASS |
| Delayed days + Payments xlsx | PASS |
| Day detail + Day PDF + Attendance CSV + Monthly PDF | PASS |
| Screenshot audit opt-in only | PASS |
| Create unpaid non-Intake blocked; Intake allowed | PASS |

Web: `tsc --noEmit` clean.

## Fixes in this pass

1. Startup seed creates admin + staff (not only SAMPLE rows)
2. Screenshot audit only when `?audit=1` (day lightbox)
3. Re-enroll revokes prior devices
4. Payment gate UX: Intake unpaid badge; create 409; override UI
5. Invoice project↔client validation; Reports date = Asia/Karachi
6. Stale VERSION.md / leftover `_patch_pdf.py` removed
7. `AUDIT.bat` for repeatable checks

## Still needs human / browser

Agent LIVE blink, sleep Sign Out, tray, enroll on real PC — use `docs/34`.
