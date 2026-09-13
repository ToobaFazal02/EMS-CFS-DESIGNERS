# Deploy guide — 13 Sep 2026 (idle 30s, dual monitors, re-enroll, update banner)

## Honest answers (read first)

### Is production deploy safe?

**Yes**, if you follow the order below. These changes do **not** wipe employees, punches, or screenshots.

| Change | Risk | Why safe |
|--------|------|----------|
| Web `resolveUrl` (screenshot thumbs in Desktop Manager) | Low | Only URL building for API media |
| Idle **30 seconds** (was 180s) | Low | Config default only; existing enrolled PCs keep old `config.json` until Agent reinstall / config reset |
| Dual / multi-monitor capture (`mss.monitors[0]`) | Low | Scales: 1 screen = that screen; 2–3+ = combined virtual desktop |
| Re-enroll UI + 401 handling | Low | Clears local token only after confirm; needs manager’s new enroll code |
| `GET /api/v1/agent/version` | Low | Public read-only JSON (version + download URL). No secrets |

**GitHub:** Prefer **private** repo (client work). If private, VPS needs a Deploy Key or HTTPS token for `git pull`.

### Will everyone auto-update without installing?

**No — not yet for people still on the old Agent.**

What we shipped is **update notification**, not silent force-install:

1. New Agent (v1.1.0+) calls `/api/v1/agent/version` after startup.
2. If server version is newer → green banner + **Download Update** → opens Downloads page.
3. Employee downloads zip / Setup and runs install (NSIS replaces old Manager; Agent zip = extract + INSTALL-AGENT.bat).

**First rollout:** every employee PC must install **this** new Agent once. After that, future bumps only need:

- Bump `AGENT_VERSION` in `apps/agent/ems_agent/__main__.py`
- Bump `LATEST_AGENT_VERSION` in `apps/api/app/routers/agent.py`
- Upload new zip / Setup to `/var/www/ems/downloads/`
- Restart API

Then enrolled Agents show “Update available”.

Admin / Manager desktop: same idea — new Setup.exe once; later versions can add Tauri updater later (not in this release).

---

## What is already in `main` (code)

- Idle default **30s** (`idle_seconds`)
- Multi-monitor screenshots (all displays in one JPEG)
- Desktop Manager screenshot/PDF URLs work in Tauri (`resolveUrl`)
- Agent: Re-enroll link + invalid-token dialog
- Agent + API: version check banner (`1.1.0`)

## What you must still build & upload (binaries)

Code alone does **not** change employee PCs. You need:

1. **Web + API on VPS** (`git pull`, build, restart)
2. **New `CFS-Agent-Install.zip`** from `BUILD-EXE.bat`
3. **New Manager Setup** from `REBUILD-MANAGER-ICON.bat` (official icon)

---

## Deploy order (do this)

### A — Local builds (PowerShell **outside** Cursor)

```powershell
# Agent (idle 30s + dual screen + re-enroll + update banner)
cd D:\imp\ems-cfs-designers\apps\agent
.\BUILD-EXE.bat

# Manager icon + installer
cd D:\imp\ems-cfs-designers\apps\web
.\REBUILD-MANAGER-ICON.bat
```

### B — VPS (Hostinger web terminal)

```bash
cd /opt/ems-src
git pull origin main
cd apps/web && npm run build && cp -r dist/* /var/www/ems/
systemctl restart ems-api
systemctl status ems-api | head -8
curl -s https://ems.cfsdesigners.com/api/v1/agent/version
# expect: {"agent_version":"1.1.0","download_url":"..."}
```

### C — Upload binaries

Put on VPS:

- `/var/www/ems/downloads/CFS-Agent-Install.zip` (~50MB, not HTML)
- Manager Setup.exe (and MSI if you ship it)

(Use GitHub Release / Hostinger file tools if SSH port 22 is blocked.)

### D — Client / employees

| Who | Action |
|-----|--------|
| Admin web | Hard refresh `Ctrl+Shift+R` on `ems.cfsdesigners.com` |
| Manager desktop | Install **new** Setup.exe once (replaces old) |
| Each employee | New Agent zip → Extract → `INSTALL-AGENT.bat` |

**Invalid device token:** Admin → Employees → **Re-enroll** → send new code → employee uses Agent **Re-enroll this PC** (or enroll form).

---

## Smoke test after deploy

- [ ] `/api/v1/agent/version` returns `1.1.0`
- [ ] Employee Sign In works on one test PC
- [ ] Wrong enroll → clear error (not freeze)
- [ ] Idle after ~30s no mouse/keyboard → Idle status
- [ ] 1 monitor + 2 monitors both capture correctly
- [ ] Day page screenshots visible (browser + Manager desktop)
- [ ] Re-enroll clears token and accepts new code
- [ ] Old Agent still works until replaced (no server break)

---

## Version bump checklist (next release — later)

You said: finish this deploy first; later you will send new version work after testing. When ready:

1. Change `AGENT_VERSION` + `LATEST_AGENT_VERSION` together
2. Rebuild Agent zip + upload downloads
3. `systemctl restart ems-api`
4. Employees with **v1.1.0+** see the update banner

Silent auto-install (Chrome-style) is **not** in this release — can be Phase 2 (Tauri updater / Agent self-update).
