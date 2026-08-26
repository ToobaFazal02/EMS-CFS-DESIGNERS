# Current state

## Google Sheet (legacy attendance)

Workbook: [Employee Attendance – 2026](https://docs.google.com/spreadsheets/d/19-WlqNXDQ9lb5QJs_Cz7xJi-NpdDeoCrvnRTWxtjpSE/edit?usp=sharing)

| Fact | Detail |
|---|---|
| Brand | CFS Designers |
| Employee tabs | `101 - Waheed`, `102 - Rohail`, `103 - Waseem`, `104 - Waleed`, `Summary` |
| Intended columns | Date, Sign In, Break In, Break Out, Sign Out, Total Working Hours, Total Break Hours, Net Working Hours |
| What is actually filled | Sign In (morning, typically 9:24–10:46) and a later timestamp that is **Sign Out** (afternoon/evening). Break hours stored as **0.00**. Net hours ≈ elapsed clock time |
| Weekends / off days | Blank rows (e.g. 1–2, 9, 12, 21 Aug 2026) |
| Trust model | **None.** It is a shared editable grid. Paste yesterday’s 9:00 into today and the sheet still “looks fine” |
| Live view | None |
| Proof of work | None (no app, no clicks, no screenshot) |
| Headcount in this file | 4 named staff (codes 101–104). Company is 10–12 — other people may be untracked or on another sheet |

Example (Waheed, 3 Aug 2026): signed 9:30:02 AM, left 6:09:09 PM, **8.65 h**, **0.00 break**. Same pattern most weekdays. 4 Aug and 11 Aug look like short days (~6 h).

**Implication:** EMS attendance UI should *look like this sheet* (same columns) so managers do not retrain, but punches must be **events with server time**, not typed cells.

## TimesheetV2 (legacy activity)

- One-file PyInstaller Windows EXE (~83 MB).
- Tkinter: Start Recording / Export Timesheet / End Program.
- Libraries: pynput, pygetwindow, pywin32, sqlite, matplotlib, fpdf.
- Sample PDF `click_timesheet_20241206_180617.pdf`: user Faisal, 9:07–18:06, ~13k clicks, 34 pages, 61 window titles. ~84% of clicks on `Design - Applegin Court Mooloolaba` (Scottsdale/ScotSteel), plus AutoCAD, roof/wall property dialogs, file explorer.
- Graph exists as image; table is minute × window title × click quantity.
- **No screenshots** in that PDF. Screenshots are a **new** requirement from voice, not a feature we observed.

## Voice (19 Aug 2026) — intent

1. Spreadsheet cheating (copy time from another day).
2. Software preferred for **offline**; still open to website if software is not clearly better.
3. Random screenshots, mouse clicks, keyboard clicks.
4. PDF 30-min graph + *where* the click was; EMS naming; see employees; track projects.

## Gap

Sheet = attendance without proof. TimesheetV2 = proof without multi-user, live, breaks, or anti-edit. EMS must close both gaps.
