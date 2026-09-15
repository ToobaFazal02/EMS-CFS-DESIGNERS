# Finalize Desktop + Web, then Admin Mobile — PLAN (LOCKED SEQUENCE)

**Status:** Implementation in progress (local). **You push + deploy** — agent does not push unless asked.  
**Deadline note (15 Sep):** Client reinstalls office-wide ~**16:00** — ship **P0 today pack** first (below).  
**Git:** Do not push unless you ask. You review + test locally, then **you** push.  
**Date:** 14–15 Sep 2026  

**Decisions locked 14 Sep (you):**

| # | Decision | Locked answer |
|---|---|---|
| 1 | Screenshots without Sign In | **Hard-block** — no screenshots until server Sign In / attendance open. Proof after proper punch only. |
| 2 | Phase C timing | **After** attendance stable (after Phase B) |
| 3 | Mobile | **PWA only** first (admin-only); no store apps yet |

---

## Production vs local (15 Sep morning — honest)

| Layer | On production now? | Notes |
|---|---|---|
| Hours fallback when Sign In missing + dashboard offline caption | **Likely yes** (pushed earlier: `3c5ef2a`, `7ed0550`) | Only if VPS still has that `git pull` |
| Agent zip **1.1.1** on `/downloads` | **Likely yes** if you uploaded Sep 14 | Re-enroll, idle 30s, **Update available banner** (download page — not silent install) |
| Phase A web/desktop: PDF modal, Tauri Reports/Payments URLs, payments sheet columns, Actions dropdown, `invoice_prep` | **NO — local only, not on GitHub `origin/main`** | Must commit → push → VPS build **before** 4pm if client should see them |
| Phase B Sign In gate for screenshots | **Not done** | |
| Phase C project codes / daily % | **Not done** | |
| Silent one-click background install | **Not done** (never was) | Banner + Download only on Agent 1.1.0+ |

**Bottom line for 4pm:** Jo local Phase A changes hain woh **production pe nahi** jab tak tum push + VPS deploy na karo. Agent reinstall ke liye **zip pehle se 1.1.1** hona chahiye; future “Update available” uske baad kaam karega.

---

## TODAY pack — priority for client reinstall (~16:00)

Client voice **14 Sep 11:41 PM**: software pe **“new update available”** → click → update (woh background install chahta hai).

### P0 — must before / with reinstall (do these first)

| Order | Item | Why |
|---|---|---|
| 1 | Confirm VPS Agent zip = **1.1.1** + API `LATEST_AGENT_VERSION=1.1.1` | Reinstall day; banner works next time |
| 2 | Push + deploy **Phase A local web/API** (PDF, Payments columns, desktop URLs, Actions menu) | Managers see fixed UI today |
| 3 | Staff reinstall **Agent** from Downloads (every PC) | Old Agents have no update checker |
| 4 | Manager PCs: new **Manager Setup** if desktop app used | Optional if they only use browser |
| 5 | Tell client honestly: update = **banner → Download → install**; silent background install = later phase |

### P1 — same week after reinstall stable

| Item | Phase |
|---|---|
| Hard-block screenshots until Sign In | **B** |
| Projects codes + multi-assignee + daily % | **C** (after attendance stable) |

### P2 — later

| Item | Phase |
|---|---|
| Admin-only mobile PWA | **D** |
| True one-click / background auto-install (Agent + Manager) | **E** (new — client 14 Sep) |

---

## Phase E — Professional auto-update (client 14 Sep 11:41 PM)

**Source:** `WhatsApp Ptt 2026-09-14 at 11.41.43 PM.ogg` → `references/client-voice-2026-09-14-1141-*.txt`

**Ask:** App use karte waqt **“New update available”** dikhe; click pe update **background** mein install ho jaye.

| Step | Reality today | Target Phase E |
|---|---|---|
| Detect newer version | Agent 1.1.0+ ✅ | Keep |
| Show “Update available” | Agent banner ✅ | Same + Manager desktop |
| Click → download | Opens Downloads page ✅ | In-app download |
| Click → silent install in background | ❌ Not built | Agent installer + Tauri updater |
| Very old Agent | No banner ❌ | One-time manual reinstall (today) |

**Do not promise Phase E for 4pm.** Promise: reinstall 1.1.1 now + banner for **next** releases.

---

**Sources:**

| Voice | Files |
|---|---|
| 11 Sep 2026, 7:26 PM | Projects / codes / % progress |
| 11 Sep 2026, 8:55 PM | Admin-only mobile |
| 14 Sep 2026, 11:41 PM | Update available + click to update |
| Your order | Desktop+web first → phone last; no push without you |

---

## Product surfaces (do not confuse)

| Surface | Who | Stack | Job |
|---|---|---|---|
| **Web** `ems.cfsdesigners.com` | Admin / HR / partners / staff (role-gated) | React | Full EMS in browser |
| **Manager Desktop** | Admin / HR / managers | Same React inside **Tauri** | Same UI, Start Menu icon, no Chrome bar |
| **Employee Agent** | CAD staff PCs only | PySide6 exe | Sign In / Break / Sign Out + screenshots + activity |
| **Phone (later)** | **Admin only** | PWA (preferred) | Manager glance — **not** employee Sign In/Out |

Client (8:55 PM): mobile app **sirf admin** ke paas — warna employees mobile se Sign In/Out misuse kar sakte hain. Staff = **desktop Agent only**.

---

## What the client said (interpreted, 11 Sep)

### A) Projects workflow (7:26 PM) — big ops design

Keep it **simple**. CFS work has **three scopes**:

1. Estimation  
2. Detailing  
3. Detailing + Engineering  

**Who creates the project on the website (interpreted):**

- Admin / manager **hands work** to staff (scope + client initial / code hint).  
- Staff (**boys**) **enter / upload the project in the app themselves** — admin does not have to type every job into the website.  
- Staff fill: project code (initial + date), location, deadline, scope, assignee (who is doing it: Waheed, Rohail, …).  
- Full client name stays off the staff day-to-day view — **initial letter** is enough when talking (`D110926`, `N110926`).  
- End of day: staff set **% progress**; history saved so owner can audit (40% → 50% = 10% today).  

Client will also send a **~22 client list** with initials (ops input for Phase C).

Attendance chapter (Sign In / Break / Sign Out + screenshots) he treats as **already clear** — install + daily use. **Our rule (your lock):** screenshots only **after** Sign In.

### B) Mobile (8:55 PM)

- Build a **mobile** experience  
- **Admin-only**  
- Employees stay on the **PC Agent** (no mobile punch surface)

### C) Your hardening order (14 Sep)

1. Web + Manager desktop must be **feature-complete and reliable** (PDF View/Download, Reports, Payments, Live, Day, screenshots).  
2. Employee Agent must be trustworthy (Sign In → clicks/keys/idle + shots).  
3. **Only then** admin phone app.  
4. No reckless DB / seed / wipe while shipping.

---

## Honest gap analysis (today)

### Already strong

- Live API + SQLite production data intact (shots/punches/employees present)  
- Web Day / Dashboard / roles / downloads page  
- Agent enroll, punches, screenshots, activity (activity requires Sign In — by design)  
- Manager Setup.exe + Agent zip shipping path  
- Day page Tauri fix for screenshot/PDF URLs (`resolveUrl` / `AuthedImg`)  
- Estimated hours when Sign In missing (display only — not fake punches)

### Broken / incomplete on **Manager Desktop** (same React, Tauri webview)

| Area | Problem |
|---|---|
| **Reports** PDF/CSV/Excel | Relative `/api/...` fetch → fails in Tauri (`tauri://localhost`) |
| **Payments** invoice PDF/XLSX | Same relative fetch bug |
| **Day View PDF** | Fetch often OK; `window.open(blob)` weak in WebView2 |
| **Live WebSocket** | Uses webview host; falls back to polling |
| **Downloads links** | May hit bundled paths instead of production `/downloads` |
| Tray / silent auto-update / frameless polish | Claimed in doc 47; **not** really in Rust shell |

### Product gaps vs 7:26 voice (Projects)

Existing Projects board ≠ full client coding scheme (`D110926`), initial-only privacy, daily % progress memory, and simplest assign flow. Treat as **Phase C** after desktop/web parity — not before Agent reliability.

### Ops / behaviour gaps (not “data wipe”)

- Screenshots can exist **without** server Sign In → Estimated hours, clicks 0  
- Dashboard “offline” was live-status, not “never clocked in today” (caption fixed)  
- Staff must press **Sign In** for clicks/keys/idle + official sessions  

---

## Client payments sheet columns (locked from screenshot — no seeded names)

Match **CFS Designers Payments Tracking Sheet → CLIENT DETAILS**:

| Sheet column | EMS field |
|---|---|
| S/No. | row index |
| CLIENT NAME | client.name |
| LOCATION | client.location / bill_to_location |
| INVOICE | `invoice_prep`: prepared / preparing / unprepared |
| INVOICE VALUE | amount + currency |
| INVOICE DATE | invoice_date |
| FOLLOW UP DATE | follow_up_at |
| INVOICE DELAYED (DAYS) | delayed_days (computed) |
| INVOICE STATUS | status (sent → “SENT TO CLIENT”, etc.) |
| Comments From Clients | client_comments |

Extra EMS columns kept: Project, Actions (View/PDF). **No real client rows hardcoded.**

---

## Delivery phases (approved sequence)

```
Phase A  →  Manager Desktop + Web parity (no phone yet)
Phase B  →  Employee Agent reliability + attendance honesty
Phase C  →  Projects workflow (client codes + % progress) — web+desktop together
Phase D  →  Admin-only mobile (PWA) — AFTER A–C stable in production
```

**Hard rule:** Do not start Phase D until A–C smoke-tested on production with real staff.

---

### Phase A — Manager Desktop + Web “complete” (FIRST)

**Goal:** Anything that works in Chrome also works in Manager Setup.exe.

| # | Work | Notes |
|---|---|---|
| A1 | Shared `resolveUrl` / blob download helper | Use everywhere: Reports, Payments, Day, Expenses |
| A2 | Fix Reports exports in Tauri | PDF / CSV / Excel |
| A3 | Fix Payments invoice PDF/XLSX in Tauri | Inline view + download |
| A4 | Reliable PDF **view** in desktop | Prefer in-app viewer / Tauri shell open — not fragile `window.open` |
| A5 | Live WS base URL in Tauri | Point to `ems.cfsdesigners.com` |
| A6 | Downloads page absolute production URLs | Manager Setup + Agent zip |
| A7 | Desktop smoke checklist | Day shots, View/Download PDF, Reports, Payments, Live, Dashboard |
| A8 | Ship new Manager Setup via Actions | Upload to VPS `/downloads/` |

**Out of scope for A:** phone, new project-code system, silent auto-update.

**Done when:** Admin can run a full day from **desktop app only** without opening Chrome.

---

### Phase B — Employee Agent reliability

**Goal:** Daily attendance is trustworthy; no “shots without Sign In” confusion in normal use.

| # | Work | Notes |
|---|---|---|
| B1 | **Hard-block screenshots until server Sign In** | Agent + API: no shot upload without open Sign In (aligned with activity). Clear UI: “Sign In to start tracking / screenshots.” |
| B2 | Clear Agent status: Signed in / Offline punch queued / Re-enroll | |
| B3 | Ensure activity + idle post only after successful Sign In | Already mostly true — tighten + test |
| B4 | Staff install video + one-pager | Ops |
| B5 | Production Agent zip = current build | Idle 30s, ~3 min shots, Re-enroll |

**Done when:** Real employee day shows Sign In session + clicks/keys (when working) + shots + PDF matches.

---

### Phase C — Projects workflow (7:26 voice)

**Goal:** Simple CFS queue matching client language.

| # | Work | Notes |
|---|---|---|
| C1 | Client master (name, location, invoice status, **initial**) | UI CRUD — **you enter data**; no real names in repo/seed |
| C2 | Auto project code `Initial + DDMMYY` | Editable override |
| C3 | Scope enum: Estimation / Detailing / Detailing+Engineering | |
| C4 | Location, deadline, **multi-assignee** | Staff create project + select assignees |
| C5 | **Daily % progress** log per assignee | One meaningful update per day (history for audit) |
| C6 | Staff see code + scope; full client name rules | Role-aware; keep simple |

**Done when:** Admin creates `N110926`, assigns boy, boy updates %, owner sees trail.

---

### Phase D — Admin-only mobile (LAST)

**Goal:** Owner glances Live / Day / projects on phone — **no employee punch UI**.

| # | Work | Notes |
|---|---|---|
| D1 | PWA manifest + icons + install prompt | Same React, admin routes |
| D2 | Mobile polish for Dashboard / Live / Day | Already partly responsive |
| D3 | Explicitly hide / block Agent-like punch actions on mobile | Security: client 8:55 |
| D4 | Optional: “Admin mobile only” install doc | |

**Not in v1 mobile:** employee Sign In/Out, screenshot capture from phone.

**Done when:** Admin installs to home screen; staff cannot use phone as fake Agent.

---

## Non-negotiables (every phase)

1. **No DB wipe / reseed / delete production `/var/lib/ems/ems.db`.**  
2. Prefer display fixes over inventing punches.  
3. Same React code for web + desktop; fix helpers once.  
4. Phone never becomes employee tracker.  
5. CFS scopes only — no civil/roads pivot.  
6. Commit locally as needed for your review; **never push / never force-push** unless you explicitly ask. You test + push.

---

## Suggested calendar (effort, not promises)

| Phase | Focus days (1 dev) | Depends on |
|---|---|---|
| A | 2–4 | Your “start Phase A” |
| B | 2–3 | A mostly done + staff PCs |
| C | 4–6 | Client client-list + your OK |
| D | 3–4 | A–C stable live |

---

## Open decisions — LOCKED (14 Sep)

1. **Screenshots without Sign In:** ~~proof-only~~ → **HARD-BLOCK until Sign In**  
2. **Phase C:** ~~now~~ → **after attendance stable (after B)**  
3. **Mobile:** **PWA only**, admin-only  

### Still useful from client before Phase C (not blocking A/B)

~~Full ~22 client list~~ — structure seen (name, location, invoice status). **Do not hardcode / seed any real client names from screenshots.** You enter clients yourself in admin/UI for testing.

| # | Topic | Locked (14 Sep night) |
|---|---|---|
| C-who | Who can create projects? | **Every employee** can create |
| C-assignees | One vs many | **Multiple** assignees; staff select themselves / each other |
| C-progress | % updates | **Daily** update (end-of-day style), as client asked |
| C-data | Client list / seed | **No hardcoded clients** in code or auto-seed from screenshots. Empty/demo-safe; you type test data |

Optional later (only if you choose to send a fuller crop): invoice/status columns beyond PREPARED / PREPARING / UNPREPARED — not required to start Phase A/B.  

---

## Next action

When ready: reply **`start Phase A`** — desktop/web parity only. No GitHub push from the agent unless you ask.
