# Lovable prompt — Dashboard tab only

Copy everything below the line into Lovable. Scope is **Dashboard only**. If the result looks right, we will rebuild the same layout in the EMS React app.

---

You are a principal product designer and front-end engineer. Design and build **only the Dashboard page** for **CFS Designers EMS** — a Hubstaff-class operations dashboard for a Cold Formed Steel / Light Gauge Steel studio (estimation, detailing, engineering). This is not a payroll app, not a generic admin template, and not a marketing site.

## Goal

A top 1% SaaS home screen: the owner understands the whole company in **one glance** — who is working, how the project pipeline looks, and (admin only) unpaid cash. Visual first: KPI cards, donut/ring, sparklines, progress bars. Tables only as a compact roster, not as the page.

Match the quality of Hubstaff Insights / Linear / Stripe Dashboards: dense but calm, not a student project.

## Hard scope (do not expand)

- Build **Dashboard only**. Do not redesign Live, Employees, Projects, Payments, Reports, Login, or the Agent.
- Do **not** duplicate the main navigation inside the page. No second row of buttons like “Open live board / Employees / Projects / Payments”. Those already exist in the top nav.
- Do **not** put a screenshot wall on Dashboard. Screenshots belong on the **Live** tab.
- Do **not** invent Hubstaff “Spent this week $1,852” unless it is clearly **unpaid client invoices** from finance data. Employees never see money.
- Do **not** add purple neon spam, glassmorphism overload, or a light theme. Dark product chrome stays CFS.

You may use extra chart colors (green, amber, blue, red, slate) **on data only**.

## Product chrome (keep)

Top bar already exists:

- Left: **CFS Designers** in gold
- Center/links: Dashboard (active) · Live · Employees · Projects · Payments · Reports
- Right: user name pill + gear → Account / Logout

If you show a sidebar in the mock, it is optional visual chrome. Prefer keeping the **existing top nav** so this page can drop into the real app.

Page title: **Dashboard**
Subtitle: `Team, projects, and cash at a glance.`
Refresh control on the right (ghost button).

## Theme (locked)

```
Background:        #0A0A0A
Cards / surface:   #141414
Raised surface:    #1F1F1F
Border:            #333333
Text:              #FFFFFF
Muted:             #A3A3A3
Gold accent:       #C9A227
Gold hover:        #E0B93A
Text on gold:      #0A0A0A
Success / signed in: #22C55E
Warning / break:     #F59E0B
Danger / offline / unpaid: #EF4444
Font: Inter or system sans (Nunito is OK). No Playfair on the dashboard — this is software, not the marketing site.
Radius: 12px cards, 8px controls, 999px pills.
```

Gold is for brand, active nav, primary actions, and axis highlights — not every button. Status uses green / amber / red.

## Layout (desktop, 1280+)

1. **KPI row** — 4 or 5 equal cards:
   - Live now (green number) — signed in
   - Break / idle (amber)
   - Offline (red)
   - Open projects — count not done, sublabel “X total”
   - Admin only: Unpaid invoices — count + currency amount

   Each KPI: small muted label, huge tabular number, one-line sublabel. Optional tiny sparkline in the card (7-day hours or 7-day presence). No clip, no overflow.

2. **Two columns**
   - Left: **Team presence** donut/ring — Signed in / Break / Offline. Center shows live count. Legend with counts.
   - Right: **Hours this week** area or bar chart (Mon–Sun). Y axis in decimal hours like **8.1 h** (never “2h 32m” as the primary label). Optional comparison vs last week as a small delta (+ / −) in green or red.

3. **Two columns**
   - Left: **Project pipeline** — horizontal bars for `working` (In progress), `waiting`, `on_hold`, `done`. Show counts. Optional stacked bar of all projects.
   - Right, **admin only**: **Cash** — unpaid vs paid invoice amounts this month, or a simple bar of unpaid totals. Label clearly “Client invoices — admin”. If role is not admin, hide this panel entirely and let pipeline go full width.

4. **Team roster** (full width, compact — not screenshot cards)
   - Rows: name, staff code (#103), status pill, last window title (ellipsis), link “Day”
   - Status pills: Signed in (green), Break / Idle (amber), Offline (red)
   - Empty: “No employees yet.”

Whitespace should feel like Hubstaff: cards with padding 20–24px, 16px gaps, not giant empty black holes and not cramped.

## Mobile (375–430)

- KPI cards wrap 2×2 (finance card full width if present)
- Charts stack vertically, full width, min chart height ~200px, never horizontal-scroll the whole page
- Roster: name + pill on first row, Day link on the right
- Touch targets 44px. No 6-column tables.

## Sample data (realistic CFS, not fake SaaS)

Staff (do not invent extra names):

| Code | Name |
|------|------|
| 101 | Tooba Fazal |
| 102 | Rohail |
| 103 | Waseem |
| 104 | Waleed |
| 105 | Waheed Ullah |

Use mixed status so the donut is not all-offline: 2 signed in, 1 break, 2 offline.

Projects: 8–12 CFS jobs (house framing, shop drawings, engineering packs). States: working / waiting / on_hold / done.

Hours: weekday ~7.5–8.4 h, Friday slightly lower. Format **8.1 h**.

Invoices (admin demo): a few unpaid USD amounts. Never show $ to a staff role.

## Interaction (keep light)

- Refresh button (can be visual only in Lovable)
- Hover on bars/donut shows tooltip
- Roster “Day” can be a dummy link
- Respect `prefers-reduced-motion`

## Quality bar

- Looks like shipped software, not a template dump
- One H1: Dashboard
- Contrast on gold/black/white that still reads
- No duplicate nav, no screenshot grid, no “Open live board” gold CTA on this page
- Loading skeletons and empty states for zero staff / zero projects

Deliver a polished Dashboard screen I can screenshot and hand to engineering to clone 1:1 into React.
