# Client voice — 30–31 Aug 2026 (employee rollout + HR + expenses)

Sources (WhatsApp Ptt, night of 30 Aug → 31 Aug 2026):

| Audio | Transcripts |
|---|---|
| 11:31:55 PM | `references/client-voice-2026-08-30/WhatsApp Ptt 2026-08-30 at 11.31.55 PM.txt` + `.en.txt` |
| 11:36:33 PM | same folder |
| 12:16:11 AM | same folder |
| 12:30:18 AM | same folder |
| 12:35:59 AM | same folder |

Whisper note: Roman Urdu. Raw ASR is messy; meaning below is **interpreted** from Urdu + English translation passes, plus the live chat (add staff emails so they only enroll).

**Do not code new modules from this file until the employee Agent is on office PCs.** Client order is explicit: employees first.

---

## Voice note map (chronological)

| Time | Core ask (interpreted) |
|---|---|
| 11:31 PM | **Roles:** Admin ≠ HR. HR sees **projects + attendance**, **not client invoices**. HR also needs an **office expenses** sheet (chai, bills, electricity, gas, solar, parties). Goal: month-end **money in vs money out**. |
| 11:36 PM | Employees are **not added yet**, so he cannot judge the product. **Tomorrow / day-after:** employee section must be ready and **in use** (screenshots + hours). **Projects + invoicing = a few days later.** Focus employees now. |
| 12:16 AM | Make a **screen recording** of how to put the Agent on employee PCs. From tomorrow: screenshots + **net hours**. Prefer **hourly decimals** like **8.1 / 8.2**, not a minutes-first UI. Breaks in **hours**, not raw minutes. |
| 12:30 AM | Close the **employee chapter ASAP**. He will send **names** (screenshot or link). Create a **professional email per name**. Install Agent on each PC so it **stays enrolled** — they must **not** login/logout of the app every morning. Daily work = **four buttons:** Sign In, Break In, Break Out, Sign Out. Send a **short video** so they can start. |
| 12:35 AM | Software must look like **our own CFS app** (logo/shortcut), not lost among CAD/PDF tools. Open Agent → Sign In → work on the project → **screen pictures start**. Ready to use **tomorrow**. |

---

## What we understand (locked intent)

### 1. Sequence (highest priority)

```
NOW (kal / parson)          AFTER a few days of real use         LATER
─────────────────           ────────────────────────────         ─────
Add staff + emails          Projects board (already built)       Office expenses (new)
Enroll each PC              Client invoicing (already built)     Distinct HR login
Screenshots + net hours
4-button Agent in daily use
How-to video for PCs
```

Client is **not** asking to rebuild Projects/Payments this week. He is asking to **stop talking and put employees on the Agent**.

### 2. Roles (refines 21 Aug “employee never finance”)

| Role | Sees | Does not see |
|---|---|---|
| **Admin / finance** | Invoices, payments $, full system | — |
| **HR** (new hire / new login) | Attendance, projects, **office expenses** | **Client invoices / invoice $** |
| **Employee** | Own hours + own projects (web, if used) | Invoices, expenses, other people’s money |
| **Agent on PC** | Four punches only after one-time enroll | No daily email login on the Agent |

Today the live site has **Admin** and **Employee**. **HR as a separate login that sees expenses but not invoices is not built yet.** Do not fake it by giving HR the admin password.

### 3. Professional emails + passwords (ops, not a new feature)

Client: make an email **from each employee’s name**, then they can be enrolled.

EMS already supports this on **Employees → Add staff** (login email + temp password + code + name).

- Pattern: `firstname@cfsdesigners.com` (e.g. `rohail@cfsdesigners.com`).
- These are **EMS usernames**. They do **not** create Hostinger mailboxes. Do not touch MX/SPF/DNS for this.
- Agent does **not** need that email every morning. Enroll once; then Sign In / Sign Out.
- Client will send the **full name list** (screenshot or link). Sheet we already have is only **4 CAD names**. Live **#101 is Tooba Fazil** — do not reuse 101 for Waheed.

Known from attendance sheet (codes if still free):

| Suggested code | Name | Login email |
|---|---|---|
| 102 | Rohail | `rohail@cfsdesigners.com` |
| 103 | Waseem | `waseem@cfsdesigners.com` |
| 104 | Waleed | `waleed@cfsdesigners.com` |
| 105 | Waheed Ullah | `waheed@cfsdesigners.com` |

Wait for his name dump before inventing 106+. Unique temp passwords, not `Emp123!` / `Admin123!`.

### 4. Agent UX (already matches the ask)

- One install, stays on the PC, autostart, branded CFS icon (not “lost among PDF/CAD”).
- No daily login/logout of the desktop app.
- Four buttons: Sign In, Break In, Break Out, Sign Out.
- After Sign In: screenshots + tracking.
- Deliverable he asked for: **short screen recording** of employee-PC setup (install → enroll → Sign In).

### 5. Hours display

Client prefers **decimal hours** like Excel: **8.1, 8.2** (and breaks in hours, not a minutes-first readout).

Current product also uses human form `2h 32m`. Treat **8.1-style as a requested report default** — implement after employees are live, do not block enroll.

### 6. New module: office expenses (not this sprint)

Simple **expenses sheet for HR**, not a full accounts package:

- Office spend: tea/water, electricity, gas, solar, bills, parties, anything else.
- Purpose: see **cash in (invoices)** vs **cash out (expenses)** at month end.
- Admin still owns **client invoices**. HR owns **office costs** + people/projects.

Out of scope until after employee rollout: payroll, bank feeds, full general ledger.

---

## Already true on live (do not rebuild)

- Workforce Agent + Live + screenshots + reports
- Projects Design Queue + Payments (admin)
- Employee web cannot see invoice $
- Agent pack: `CFS-Agent-Install.zip` on the operator Desktop
- Live EMS: `https://ems.cfsdesigners.com`

---

## Open (wait on client)

| Item | Status |
|---|---|
| Full employee name list (10–12?) | He will send screenshot/link |
| Real Hostinger mailboxes vs EMS-only emails | Not required for Agent |
| HR person name + whether they get a login now | Role described; login type not built |
| Decimal-hours as the only report format | Requested; not switched yet |
| Expenses categories / who enters spend | After employee pilot |
