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

### Data safety

- [ ] Enroll / punches do not wipe employees
- [ ] Existing employee still appears after Agent enroll test
- [ ] No `.env` / secrets committed

## Deploy order (when tests pass)

1. Push code to GitHub
2. On VPS: `git pull` → API restart if needed → `npm run build` → copy `dist` to `/var/www/ems`
3. Upload **new** `CFS-Agent-Install.zip` and Manager Setup/MSI to `/var/www/ems/downloads/` (scp; large files)
4. Spot-check production Downloads + one enroll on a test PC
