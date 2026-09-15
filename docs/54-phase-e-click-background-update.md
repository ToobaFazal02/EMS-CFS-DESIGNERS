# Phase E — Click → background update (MVP) — 15 Sep 2026

**Status:** Implemented in code (Agent **1.1.2**, Manager **0.1.2**).  
**Client ask (14 Sep 11:41 PM):** “Update available” pe click → software background mein update.  
**Research:** Tauri official updater needs signed `latest.json` + CI keys (proper long-term). Today’s MVP = same UX without signing infra: download package → silent apply → restart.  
**Data safety:** Does **not** touch `/var/lib/ems/ems.db`, employees, punches, or screenshots. Only replaces local app binaries. Agent keeps `config.json` (enroll) + `agent_data/`.

---

## What ships in this MVP

| App | On “Update available” click | Keeps |
|---|---|---|
| **Employee Agent** | Download `CFS-Agent-Install.zip` → extract → PowerShell `robocopy` (skip `config.json`) → restart exe | Enroll token, offline queue |
| **Manager Desktop** | Download `CFS-Designers-Manager-Setup.exe` → NSIS `/S` (currentUser) → relaunch | Server-side everything |

Web browser Manager does **not** auto-update (no installable binary). Banner is Tauri-only.

---

## Phase B audit (read-only, 15 Sep) — no code change

| Check | Result |
|---|---|
| Agent shots only when local state `working` | OK for normal use |
| Activity API requires open Sign In | Hard-block OK |
| Screenshot API requires open Sign In | **Not enforced** (optional later) |
| Decision | **Do not touch** Phase B code now |

---

## Version bump checklist (every release)

1. Bump `AGENT_VERSION` in `apps/agent/ems_agent/__main__.py`
2. Bump `LATEST_AGENT_VERSION` + URLs in `apps/api/app/routers/agent.py`
3. Bump Manager: `package.json`, `tauri.conf.json`, `Cargo.toml`, `apps/web/src/version.ts`, `LATEST_MANAGER_VERSION`
4. Build Agent zip (`BUILD-EXE.bat`) → upload `/var/www/ems/downloads/CFS-Agent-Install.zip`
5. Build Manager Setup (GitHub Actions) → upload `CFS-Designers-Manager-Setup.exe`
6. VPS: `git pull` → web build → `systemctl restart ems-api`
7. Confirm: `curl -s https://ems.cfsdesigners.com/api/v1/agent/version`

**Order matters:** upload binaries **before** (or with) API version bump, otherwise clients download an old package.

---

## First-time vs next updates (honest)

| Situation | What happens |
|---|---|
| PC still on Agent **≤1.1.1** | Banner may show; click still opens Downloads (old code). **One manual install of 1.1.2** at office reinstall. |
| PC on Agent **≥1.1.2** | Click → background download + restart |
| Manager still on **≤0.1.1** | Same: one Setup install for 0.1.2, then click-updates work |

---

## Deploy today (before ~16:00)

```bash
# VPS after you push
cd /opt/ems-src
git checkout -- apps/web/tsconfig.tsbuildinfo 2>/dev/null || true
git pull
cd apps/web && rm -f tsconfig.tsbuildinfo && rm -rf dist && npm run build
cp -r dist/* /var/www/ems/
systemctl restart ems-api
curl -s https://ems.cfsdesigners.com/api/v1/agent/version
```

Local / Actions:

```powershell
cd D:\imp\ems-cfs-designers\apps\agent
.\BUILD-EXE.bat
# Zip dist\CFS-Designers-Agent → CFS-Agent-Install.zip → upload downloads/

# Manager: GitHub → Actions → Build Manager Setup → upload Setup.exe
```

**Do not** delete or reseed SQLite. `systemctl restart ems-api` only.

---

## Smoke test

- [ ] `/api/v1/agent/version` has `agent_version`, `agent_package_url`, `manager_version`, `manager_download_url`
- [ ] Package URLs return real zip/exe (not HTML)
- [ ] Install Agent 1.1.2 once → set API to a higher test version → click Update → Agent restarts → enroll still present
- [ ] Manager 0.1.2 → click Update with newer Setup on server → app exits → returns on new build
- [ ] Day / Live / punches still work after update

---

## Later (not today)

- Official `@tauri-apps/plugin-updater` + signed artifacts (Chrome-grade verify)
- Optional: API hard-block screenshots without Sign In (Phase B polish)
- Phase C projects workflow
- Phase D admin PWA
