# After MVP handover — saved list

Do **not** start items 1–3 until Agents are on office PCs. Client 30–31 Aug: **employees first**. Source: `docs/42-client-voice-2026-08-30-plan.md`.

## 0. This week (ops — not new product)

- Add employees + professional EMS emails + unique passwords
- Enroll PCs; four punch buttons; branded Agent already in zip
- Record a **short screen video** of install → enroll → Sign In (client asked)

---

## 1. Hubstaff-style dashboard (first screen)

- Opening after login must **not** land on Live first. Home = **Dashboard**. Live is its own tab (screenshots). **No duplicate Live/Employees/Projects buttons on the dashboard.**
- Visual pass: Lovable layout shipped (KPI + donut + week hours + pipeline + admin invoices + roster). Data from `GET /api/v1/dashboard` (PKT hours, live status, real invoices).
- Money (unpaid invoices) **admin only**.

## 2. Settings gear (replace Account tab) — **done 31 Aug 2026**

- Header: **gear icon** (not a full Account tab).
- Click → dropdown: Account, Logout (and later theme/help if needed).
- Same pattern as professional SaaS sidebars.

## 3. Themed thin scrollbars — **done 31 Aug 2026**

- Every scroll surface: thin bars in **black / gold / white** — not default grey/white OS bars.

## 4. Agent as a real desktop app

- Company **CFS logo** on desktop, Start Menu, taskbar, window, tray — **done** in `CFS-Agent-Install.zip`
- Install once → stays enrolled (client: no daily login/logout of the app)
- Window **X** → Quit (red) / Cancel

## 5. Decimal hours (client 31 Aug) — **web day view 8.1 h (done)**

- Reports: prefer **8.1 / 8.2** (and breaks in hours), not minutes-first `2h 32m` only

## 6. Distinct HR role

- Login that sees attendance + projects + later expenses
- **Cannot** see client invoices / $

## 7. Office expenses sheet (HR)

- Chai/water, electricity, gas, solar, bills, parties, other
- Month-end: money in vs money out — **not** a full accounting system

---

When starting a later sprint after employees are live, remaining: **HR role → expenses**. PDF reports still use `2h 32m` until a follow-up.
