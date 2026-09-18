# Execution gate

| Key | Value |
|---|---|
| EXECUTION_APPROVED | **yes** |
| Current phase | **Desktop Manager + Agent → 100% first** — `docs/62-remaining-work-desktop-first.md` |
| Code allowed | STEP 1–3 only (Desktop parity → Agent → Wave 4 ship). No web polish / no mobile until both 100%. |
| Git branch | **`desktop+agent`** — create/use this branch; push when you ask |
| Approved by | User 18 Sep — Desktop + Agent 100% on branch `desktop+agent`, then least-priority web/mobile |

## Locked product order (18 Sep)

1. **Desktop Manager** (Setup.exe) — client reqs **100%**
2. **Employee Agent** (zip) — client reqs **100%**
3. Gate: both green → ship
4. Remaining **web** polish — **least priority**
5. **Mobile** (Phase D) — **least priority / LAST**

## Honest status (18 Sep)

- Waves **0–3** (identity, Agent trust, Day/Live, Phase C + D/E + soft gate + dash progress + Live day totals): **code mostly in tree**
- Wave **4** Manager Setup + office Desktop receive: **not done** ← client-visible gap
- Recent work felt “web-only” because we tested in Chrome; Desktop = same React **after** new Setup.exe

## Done (production / recent code)

- Workforce: agent, live, day, PDF/Excel, multi-monitor, re-enroll
- Phase A helpers: Payments Actions, Tauri URL helpers, PDF modal (re-verify in Desktop)
- Phase E partial: version API + banners; Agent/Manager click-update path
- Wave 0–2: identity, Agent idle/shots/sound, Day auto-refresh
- Wave 3: projects codes/scopes/Detailer+Engineer/daily %; soft payment gate; Dashboard EOD %; Live today clicks/keys — see `docs/61`

## Next (locked order)

1. **STEP 1** — Desktop Manager parity checklist in Tauri/Setup (`docs/62`) — **in progress on `desktop+agent`**
2. **STEP 2** — Agent zip rebuild + 1-PC test
3. **STEP 3** — Wave 4 ship (Setup + Agent + VPS downloads)
4. **STEP 4+** — Remaining web / notify / Phase D — **only after Desktop + Agent 100%** (least priority)

### Branch `desktop+agent` progress (18 Sep)

| Done in this branch | Notes |
|---|---|
| Docs lock + branch created | `STATUS` / `62` / `INDEX` |
| Manager version sync → **0.1.5** | package.json, tauri.conf, Cargo.toml, version.ts, API |
| Restore click→silent Manager update | Rust command + ACL permission + banner button |
| Lazy `apiBase()` / Downloads absolute URLs | Tauri `tauri://` 404 fix hardening |
| Agent idle copy clarity | Same 10s idle / 5‑min shot policy |
| Removed “Design phases free…” hint | Projects form (web=desktop) |
| **Staff My dashboard** | Attendance month table + own monthly PDF view/download |

**Data:** Never wipe `/var/lib/ems/ems.db`.  
**Git:** Branch **`desktop+agent`**. Push when ready.

## Auto-update honesty (client line)

- Banner: **Update available**
- Click: download + install in background + restart
- Server / hours / screenshots data: **safe**
- First install of a new build: still extract/Setup once per PC
