# End-to-end testing — all phases

Health must show `"report_version":"phase5-complete"` after `RUN-API.bat`.

Login: `admin@cfsdesigners.com` / `Admin123!`  
Samples + admin auto-load on API start (or `SEED-SAMPLES.bat`).  
Automated API check: **`AUDIT.bat`** (expect 20/20).  
Sample rows: **Summit LGS (SAMPLE)** and **Harbour Frames (SAMPLE)**.

This is **office software**: Windows **Agent** on employee PCs + **manager web** in Chrome + **API** on the office server. It is **not** the public cfsdesigners.com marketing site.

---

## What each piece is

| Piece | Kind | Who |
|---|---|---|
| **Agent** | Installed Windows app (PySide) | Employee CAD PC |
| **Web** | Browser UI (`:5173`) | Manager / admin |
| **API** | Backend (`:8000`) | Always on |

**Agent** = Sign In/Out, LIVE red blink, clicks/keys, screenshots. Not a website.

---

## Sample data (after seed)

| Sample | Meaning |
|---|---|
| **Summit LGS** / Iliff St | Contract $10,000. Deposit $5,000 **Paid**. Job already in Preliminary Design. Can work. Cannot go to Stamped/Field/Run until remaining $5,000 Paid. |
| **Harbour Frames** / Warehouse | Contract $8,000. Deposit **Pending**, follow-up overdue (delayed days > 0). Stuck in **Intake**. Moving the card must show a red danger error until you mark SAMPLE-INV-2001 **Paid**. |

---

## Phase 1 — Workforce (agent + live + day)

- [ ] Agent window: CFS Designers; LIVE blink after Sign In
- [ ] Live board: status, last window, screenshot
- [ ] Day detail: hours, sessions, View/Download PDF
- [ ] PDF graph: Click Count, 30-min, 9–5 PKT, date+time labels
- [ ] Sleep PC: hours must **stop** (not 23h/day). Monthly Waseem must not be ~93h after hours-v5
- [ ] Sign Out / tray Quit; sleep auto session end

## Phase 2 — Reports + polish

- [ ] Reports: daily Excel/CSV (no rotated chart)
- [ ] Monthly PDF/Excel/CSV; hours `2h 32m` not only decimals
- [ ] Future date = red danger banner (no `alert()`)
- [ ] Ultra-wide layout fills width
- [ ] Branding **CFS Designers** (login, PDF footer, Excel title)

## Phase 3 — Projects (Design Queue)

- [ ] Nav Projects: 7 columns Intake → Run Files
- [ ] SAMPLE Iliff in Preliminary Design; Harbour in Intake
- [ ] List view: name, client, location, assignee, area, storey, phase, status, comments
- [ ] Due soon gold; overdue red
- [ ] New client + new project save

## Phase 4 — Payments sheet

- [ ] Nav Payments: columns match Excel (client, location, invoice #, value, dates, delayed days, status, comments)
- [ ] SAMPLE-INV-2001 delayed days > 0 and not paid
- [ ] SAMPLE-INV-1001 status paid
- [ ] Download Excel opens without a chart overlay
- [ ] Edit invoice: change Harbour deposit to **Paid**, save

## Phase 5 — Payment gates

- [ ] Harbour still Intake + unpaid: change phase to Preliminary Design → **red error** about 50% advance
- [ ] After marking SAMPLE-INV-2001 Paid: move to Preliminary Design **succeeds**
- [ ] Summit: try Stamped Drawings while balance invoice still pending → **blocked** until SAMPLE-INV-1002 Paid
- [ ] After 100% paid, Stamped / Field / Run Files allowed

---

## Restart order

1. `RUN-API.bat` → health `payments-v1`  
2. Seed command above (once)  
3. `RUN-WEB.bat` → Ctrl+F5  
4. `RUN-AGENT.bat` for workforce tests
