# Hours fix + Projects — how to test

## Restart first

1. Close old API window, run `RUN-API.bat` (no `--reload`).
2. Health must show `"report_version":"hours-v5"`.
3. Hard refresh web `Ctrl+F5` on http://127.0.0.1:5173

## Waseem 92 hours — what it was

Sleep **did** inflate hours: laptop sleep / forgotten Sign Out left the session **open**. Monthly report then counted wall-clock from Sign In to the **latest** activity in the whole month (and used device last-seen as a fallback). Four open days ≈ **23h each** → **~93h**.

**Now:** hours only count on PKT days that have **proof of work** (clicks / keys / screenshot). Empty sleep nights = 0. Re-download **Monthly PDF / View table** for August.

Expected: Waseem’s Net Work drops to roughly real worked time that month (not ~23h/day). Avg / Day should look like a normal shift, not 23h.

Also check **Day detail** for one of his 4 days — Net work should match that day’s first→last activity, not midnight-to-midnight.

## Projects (Phase 3)

Nav: **Projects**

1. Add client (name + location).
2. New project: name, client, assignee, area, storey, scope, due date.
3. Board: 7 columns (Intake → Run Files). Change phase from the card dropdown.
4. Due within 3 days = gold; overdue = red.
5. List view = CFS PROJECTS sheet columns.

Payments module is **next** (not in this drop). Advance % still confirm with client (recommend 50/50).
