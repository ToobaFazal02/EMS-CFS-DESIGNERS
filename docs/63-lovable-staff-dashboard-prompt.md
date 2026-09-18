# Lovable prompt — Staff “My dashboard” tab only

Copy everything below the line into Lovable. Scope is **employee My dashboard only**. If the result looks right, we port layout/CSS into EMS React (`StaffHomePage.tsx`).

---

You are a principal product designer. Design **only the Staff My dashboard page** for **CFS Designers EMS** — Cold Formed Steel / LGS studio. Staff use this page on **web and Windows desktop (same UI)**. Not admin team dashboard. Not marketing.

## Goal

A premium, calm, eye-catching **personal performance home**: the employee instantly sees “how am I doing today / this month?”, a clear **hours graph**, **project progress bars**, a **prominent end-of-day % form** (not a hidden modal), and actions for **View / Download my monthly PDF**. Match Hubstaff Insights / Linear quality — dense but elegant.

## Hard scope

- Build **Staff My dashboard only**. Do not redesign Login, Admin Dashboard, Live, Payments, or Agent.
- Do **not** invent money / invoices / partner shares for staff.
- Do **not** show other employees’ data.
- Do **not** use purple neon, glassmorphism overload, Inter/Roboto defaults, or cream terracotta AI clichés.
- Keep **dark Black + Gold + White** CFS brand. Fonts: elegant serif for titles (Playfair-like) + clean sans for UI (Nunito-like).

## Existing top nav (do not redesign)

Left: **CFS Designers Staff** · Center: Dashboard (active) · My Day · My Projects · Downloads · Right: avatar + name + gear.

Page title: **My dashboard**  
Subtitle: `{Name} · #{code} — attendance, performance & project %`  
Refresh ghost button top-right.

## Sections (one composition, not a cluttered dashboard)

1. **KPI strip (4)** — Today net hours · Today clicks/keys · Month days present · Month trend (sparkline up/down). Gold/green accents. One link: “Open My Day (daily report) →”.

2. **Log today’s project progress** (HERO card — must feel primary, not buried)
   - Project select · My % today · Optional note · gold **Save my progress**
   - Below: list of open jobs with gold progress bars + %
   - Short helper: Admin sees the same history (40% → 50% = 10% today).

3. **Hours this month** — bar chart of days worked (gold bars). Year/month selectors. Caption with month totals.

4. **My monthly report (PDF)** — short copy: personal day-by-day PDF; daily sessions/screenshots live on My Day; team Reports are admin-only. Buttons: View PDF · Download PDF.

5. **Attendance calendar table** — Date · Net hours · Status; date links to My Day.

## Visual rules

- Dark charcoal panels, subtle gold borders, generous spacing, no fake cards on every widget.
- Progress bars = thin gold fills on muted tracks.
- Charts readable; no chart junk.
- Mobile: stack KPI → progress form → chart → PDF → table.

## Out of scope

Admin Live wall, team Reports, Payments, screenshots gallery (belongs on My Day).

## Deliverable

One polished Staff My dashboard screen (dark CFS) ready to screenshot and hand to engineering.

---

**After Lovable:** paste screenshots here; we implement in `apps/web/src/pages/StaffHomePage.tsx` on branch `desktop+agent`.
