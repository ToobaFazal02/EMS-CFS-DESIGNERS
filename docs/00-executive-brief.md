# Executive brief

**Client:** CFS Designers (LGS / CFS detailing; FrameCAD / Scottsdale / AutoCAD).  
**Product name they asked for:** **CFS Designers** (not “EMS CFS”). Internal repo may still say `ems-cfs-designers`.  
**Live:** https://ems.cfsdesigners.com  
**Problem:** Hours are typed into Google Sheets and can be faked. Managers cannot see whether the employee was in ScotSteel or on YouTube.

## Three inputs we already have

1. **Google Sheet** “Employee Attendance – 2026” — current official attendance. Tabs per employee (101 Waheed, 102 Rohail, 103 Waseem, 104 Waleed) + Summary. Columns: Date, Sign In, Break In, Break Out, Sign Out, Total Working Hours, Total Break Hours, Net Working Hours. In practice **breaks are unused (0.00)**; only morning sign-in and evening sign-out. Anyone with edit access can type `9:30 AM` after arriving at 11:00. That is the cheating the owner described.

2. **TimesheetV2.exe** — old Python/Tkinter desktop tool. Start/stop recording, click counts, window titles, 30-min graph, multi-page PDF. Local, offline, no manager live view, no screenshots in the sample PDF, no break punches, no server clock.

3. **Voice notes (19 Aug 2026)** — they want: tamper-proof sign-in/break/sign-out; prefer software because **offline**; random screenshots every few minutes; mouse + keyboard counts; PDF with 30-min click graph; **where** clicks happened (YouTube vs Scottsdale vs work); manager can **see** employees; project tracking; name it EMS.

## Confirmed (user, 20 Aug 2026)

- Headcount now **10–12**, will grow.
- Manager needs **live** and **end of day**.
- **Screenshots required** (said in voice).

## What we will build (after approval)

Not “a website”. Not “only TimesheetV2 again”. Not a browser extension.

**One EMS = Windows agent + API + manager web.** Same shape as Hubstaff/DeskTime/Time Doctor: desktop tracker + live dashboard + screenshots while clocked in. Spreadsheet becomes a *report export*, not the system of record.

Professional defaults (screenshots every ~5 min random, on-prem server, no video, breaks optional, stop after sign-out, employee can view own shots) are locked in `docs/11-questions-explained-and-market-defaults.md` unless client changes them.

## 30–31 Aug 2026 (five voice notes)

**Employees first.** Add named emails, enroll PCs, screenshots + hours from tomorrow. Projects/invoicing already built — use after a few days. **HR ≠ Admin:** HR sees attendance + projects + office expenses, **not invoices**. Hours as **8.1 / 8.2**. Branded Agent, four buttons, no daily app login. Full interpretation: `docs/42-client-voice-2026-08-30-plan.md`.

## What we will not build in v1

Payroll, GPS, mobile clock, hidden stealth agent, keylogging text, live video stream, full HRIS, Chrome-extension-only tracker. **Office expenses** is a later sheet for HR — not a full accounts package.

## How we build

`docs/12-engineering-quality.md` — latest official docs, one module at a time, test until pass before next feature. No sugarcoating status.
