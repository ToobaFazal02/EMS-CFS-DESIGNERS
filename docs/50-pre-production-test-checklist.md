# Pre-production test checklist (EMS)

Do **not** skip local checks and go straight to production.

## Brand / icons (this round)

1. Uninstall is not enough if you reinstall an **old** Setup.exe — that Setup still embeds the old Manager icon.
2. After a good install: Desktop + Start Menu + taskbar should show the **orange/silver monogram** (same as cfsdesigners.com), not gold serif "CFS".
3. If taskbar still looks old: **unpin** both CFS icons → open from Start Menu → **pin** again (Windows caches pinned icons).
4. Agent and Manager are **two apps** — both must show the monogram.

## Smoke test before deploy (15–20 min)

### Web (browser + Manager desktop)

- [ ] Login (admin / HR / employee roles you use)
- [ ] Dashboard loads
- [ ] Employees list + open one profile
- [ ] Live page loads (if used)
- [ ] Projects / Payments / Shares / Expenses open without blank errors
- [ ] Downloads: Setup + Agent zip start; progress **auto-scrolls** into view; cancel works
- [ ] Light + dark theme: cards/text readable

### Manager desktop app

- [ ] Opens from Start Menu with **official logo**
- [ ] Login works against **production API** (`https://ems.cfsdesigners.com`)
- [ ] Same pages as web above

### Employee Agent

- [ ] Extract zip (do **not** run bat inside WinRAR)
- [ ] Run `INSTALL-AGENT.bat` — no broken `ΓÇö` text
- [ ] Wrong enroll code → immediate **Wrong enroll code** (not only timeout)
- [ ] While checking: button shows **Connecting...**
- [ ] Valid enroll code → enrolled, then Sign In / Break / Sign Out
- [ ] Tray / taskbar shows monogram
- [ ] Idle: no mouse/keyboard ~**30s** → status Idle (Live / Agent)
- [ ] One monitor + dual monitors: screenshots cover all displays
- [ ] **Re-enroll this PC** works after admin Re-enroll + new code
- [ ] Invalid token on Sign In → dialog offers Re-enroll (not endless “Could not save”)
- [ ] After v1.1.0+: if API version higher → update banner + Download button

### Data safety

- [ ] Enroll / punches do not wipe employees
- [ ] Existing employee still appears after Agent enroll test
- [ ] No `.env` / secrets committed

## Deploy order (when tests pass)

See **`51-deploy-sep13-idle-reenroll-update.md`** for full steps.

1. Push code to GitHub (keep repo **private** if possible + VPS deploy key)
2. On VPS: `git pull` → `npm run build` → copy `dist` to `/var/www/ems` → `systemctl restart ems-api`
3. Confirm `GET /api/v1/agent/version` → `1.1.0`
4. Upload **new** `CFS-Agent-Install.zip` and Manager Setup to `/var/www/ems/downloads/`
5. Spot-check production Downloads + one enroll on a test PC
6. Tell client: **first** Agent/Manager install of this build is required; later releases use the in-app update banner
