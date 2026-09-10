# Dashboard + manager web — pre-deploy audit (1 Sep 2026)

Senior frontend/design pass before shipping the Hubstaff-style **Dashboard** home.

## What the dashboard shows (real data only)

| Widget | Source | Empty studio looks like |
|---|---|---|
| Live / pause / offline KPIs | `GET /api/v1/dashboard` live staff | `0 of N` is **correct**, not a bug |
| Sparklines | This week’s team hours (PKT Mon–Sun) | Flat line when nobody punched in |
| Hours chart | This week vs last week punches (PKT Mon–Sun) | Tiny/empty bars until Sign In. **Gold = this week, grey = last week.** Dashed lines = 0–10 h scale (not sample). |
| Project pipeline | Real `projects.work_state` counts | One green bar if all jobs are In progress |
| Client invoices | Admin only. Unpaid total = **dominant currency only**. Late list = real overdue invoices | Real client names. **No fake layout rows** |
| Team roster | Same live staff list | Names and hours from the database |

**Sample overlay:** removed (9 Sep 2026). Old `localStorage.ems_dash_preview=1` caused fake KPI boxes to flash after login then vanish — Dashboard now waits for real API data only and clears that flag on load/login.

Refresh keeps the last successful payload if the API fails. Stale in-flight requests are aborted.

## Layout / type (device)

| Width | Behaviour |
|---|---|
| Phone (≤700px) | 16px base, KPI cards snap-scroll, panels stack, hamburger + **red X**, gold active nav |
| Laptop ~1366–1440 | 17px base, dashboard **full shell width** (this is the density to match) |
| 1920 | 18px base, still full width, modest 40px side padding |
| 2560+ | **Same fill as 1440** (no centered island). 19px base, taller sparklines/donut/hours chart so it does not look zoomed-out |

Invoice / roster lists **scroll inside the card** so extra clients or staff do not blow the page.

## Production env (must be set on the VPS)

Copy from `apps/api/.env.example`:

- `SECRET_KEY` — long random, **not** `dev-secret-change-me`
- `AUTO_SEED_SAMPLES=false` — otherwise SAMPLE clients/invoices can return on API restart
- `CORS_ORIGINS` — include `https://ems.cfsdesigners.com` (and www if used)
- `TIMEZONE=Asia/Karachi`

If SAMPLE names still appear in Payments, run the existing clearer (`app/clear_samples.py`) on that database **once**, after backup.

## Chrome “91 issues”

DevTools **Issues** is not the same as red **Console** errors. Chrome often lists cookies, contrast hints, and third-party noise. Before deploy, look only at **Console → Errors** (red). Accessibility contrast on gold/muted grey is an ongoing brand tradeoff, not a crash.

## You should click once (human)

1. Hard-refresh Dashboard at **phone, 1366, 1920, 2560**.
2. Confirm invoice names match **Payments** (no “Sample ·” prefix).
3. One employee **Sign In** on the agent — hours/sparks should move off zero.
4. Staff named **`t`** is real DB data; rename on Employees if that was a test account.
5. Mixed `$` / `A$` / `PKR` on late rows is **per-invoice currency**, not a layout bug.
6. Do not deploy until VPS `.env` `SECRET_KEY` and `AUTO_SEED_SAMPLES` are checked.
7. Gear → Account: Dark / Light. Open the app 5 times max to see guide cards, then they stop.

## Code checks already run

- `npx tsc -b` in `apps/web` — clean after this pass.
- Fake invoice layout rows removed from `DashboardPage`.
- Fake week-hour preview bars removed earlier (refresh flash).
