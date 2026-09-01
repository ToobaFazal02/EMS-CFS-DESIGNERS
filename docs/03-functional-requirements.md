# Functional requirements — CFS Designers platform

Status: **v2 scope** (workforce + projects + payments **built**; employee **rollout now**; HR expenses **later**).  
Product UI name: **CFS Designers** (client 21 Aug 2026). Live: https://ems.cfsdesigners.com

---

## 0. Roles

| Role | Can |
|---|---|
| Employee | Agent Sign In/Out/Break (enroll once — no daily app login); own day; own assigned projects (no $) |
| Manager / HR | Live board, all attendance, reports, assign projects, board moves. **Not client invoices.** Later: office expenses sheet (30 Aug voice) |
| Finance / Admin | Clients + payments sheet fields, follow-ups, mark paid |
| Admin | Users, devices, retention, payment-gate overrides with reason |

---

## 1. Workforce (MUST — implemented)

### Attendance
- Punches: Sign In, Break In, Break Out, Sign Out
- Server UTC; UI Asia/Karachi
- Net hours = sessions − breaks; open sessions capped by last activity
- Multiple sessions per day; incomplete day flagged
- Sleep / long idle → auto Sign Out (agent)

### Activity
- Mouse click count; key **press count** (never characters)
- Foreground window title samples
- 30-min click histogram on daily PDF (Timesheet-style, dynamic PKT window, default 9–5)
- Idle ~3 min; screenshots skip while idle

### Screenshots
- Interval while signed in & not break; JPEG compress; device upload
- Manager: live thumb + day gallery; employee sees LIVE badge (no stealth)

### Live board
- Status, last window, click/key deltas, last screenshot
- WebSocket + poll fallback

### Reports
- Daily PDF / monthly PDF; attendance Excel/CSV (no broken Excel charts)
- Human hours on reports today (`2h 32m`); **client 31 Aug asked decimal hours `8.1` / `8.2`** (breaks in hours too) — switch after employees are live
- Wide-screen responsive manager UI; red danger banners for errors

### Offline
- Agent SQLite outbox; sync when API up; server time authoritative

---

## 2. Branding (MUST — client)

- All user-facing strings: **CFS Designers** (not “EMS CFS”)
- Agent title, tray, PDF/Excel headers, web `<title>`, login

---

## 3. Projects module (built — use after employee week)

### Data (from CFS PROJECTS sheet)
- Project name, work scope, assignee, area (sq.ft), storey, status, comments
- Link to client (name + location)

### Board (from Design Queue)
- Columns: Intake → Preliminary Design → Preliminary Engineering → Final Engineering → Stamped Drawings → Field Files → Run Files
- Card: Working / Waiting, PM/assignee, next due (red when near), target date
- List view = sheet columns; board view = Kanban
- Employee sees only assigned projects

### Payment gates (when Payments live)
- Cannot leave Intake without advance recorded (configurable %)
- Cannot deliver final files columns while balance unpaid (Admin override + audit)

---

## 4. Payments module (built — admin only; use after employee week)

### Data (from Payments Tracking sheet)
- Client name, location, invoice ref, value, invoice date, follow-up date
- Delayed days = **computed**
- Status + client comments
- Finance-only amounts

### Behaviour
- Follow-up due list; overdue badges
- Export Excel matching their headers
- Recommended policy (confirm with client): **50% before start, 50% before final files**; trusted clients **30%** exception

### Must NOT
- Store card numbers / scrape WhatsApp / public unauthenticated money screens
- Show invoice $ to employees or to **HR** (30 Aug: HR sees expenses, not invoices)

---

## 5. Office expenses (SHOULD — after employee rollout)

Source: client voice 30 Aug 2026 (`docs/42-client-voice-2026-08-30-plan.md`).

- Simple sheet for **HR**: tea/water, electricity, gas, solar, bills, parties, other office spend
- Month-end view: **money in** (invoices, admin) vs **money out** (expenses, HR)
- Not a full accounts / payroll / bank-feed product

---

## 6. Explicit out of scope (until new contract)

Payroll, leave GPS, mobile clock-in, keylogging text, stealth agent, live video, full GL accounting, client self-serve portal, Mac agent, white-label marketplace.
