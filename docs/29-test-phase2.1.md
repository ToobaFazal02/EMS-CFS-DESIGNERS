# Test checklist — Phase 2.1 (clean reports + monthly PDF + agent install)

Prereq: only **2 windows** — API (`RUN-API.bat`) + Web (`RUN-WEB.bat`). Agent alag.

## 0) API is the NEW build

1. Browser: http://127.0.0.1:8000/api/v1/health  
2. Pass if JSON has `"report_version": "clean-v3"`  
3. Fail if only `"ok": true` without `clean-v3` → restart `RUN-API.bat`

## 1) Reports UI labels

1. Open http://127.0.0.1:5173/reports (Ctrl+Shift+R)  
2. Daily: **View table** / Download Excel / Download CSV  
3. Monthly: **View table** / **View PDF** / Download PDF / Excel / CSV  
4. Pass if labels match (no duplicate mystery “View”)

### View table vs View PDF

| Button | What happens |
|---|---|
| View table | Same page pe HTML table preview |
| View PDF | New browser tab mein PDF |
| Download … | File Downloads folder mein |

## 2) Daily Excel (no help lines + chart)

1. Pick a past date with data → Download Excel  
2. If Excel says Protected View → **Enable Editing**  
3. Pass if:  
   - No “How to read…” row  
   - Subtitle is only date + Generated  
   - Right side chart has bars (or zeros for empty employees)  
   - Column **Hours** visible  

## 3) Daily CSV

1. Download CSV → open in Excel  
2. Pass if Date column shows readable text (not `########`)

## 4) Daily PDF (employee day page)

1. Live → employee → Day detail  
2. **View PDF** then **Download PDF**  
3. Pass if: no “clock format / previous timesheet” lines; black/white + gold bars only on graph

## 5) Monthly PDF

1. Reports → month 8 / 2026 → View PDF  
2. Pass if team table opens; Download PDF works

## 6) Agent install / autostart (optional this session)

1. Run `apps\agent\INSTALL-AGENT.bat`  
2. Pass if Startup shortcut created  
3. Sign In / End Session still works with API up

## 7) Sleep / hours (regression)

1. Sign In → wait → sleep PC 3+ min → wake  
2. Pass if session ends or status becomes Inactive; hours do not keep growing for sleep time

---

Mark each Pass/Fail in Notion or on paper before telling client “ready”.
