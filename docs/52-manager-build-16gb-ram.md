# Manager Setup build — 16GB RAM reality (14 Sep 2026)

## Why local build keeps dying

Tauri **release** compile of `app` can peak near **~16 GB RSS**. On a 16 GB laptop, Chrome/Cursor + rustc = OOM / hang / corrupt rlib. Disk free helps; **RAM** is the real limit.

Local workarounds (`CARGO_BUILD_JOBS=1`, `opt-level=1`, no LTO, TEMP on D:) help sometimes but are **not reliable**.

## Final recommended path

**Build Setup.exe on GitHub Actions** (Windows runner), download artifact, put on VPS `/var/www/ems/downloads/`.

1. Push code (workflow: `.github/workflows/build-manager-setup.yml`)
2. GitHub → **Actions** → **Build Manager Setup** → **Run workflow**
3. Wait ~20–40 min → download artifact `CFS-Designers-Manager-Setup`
4. Upload Setup.exe to production downloads (Release + wget, same as Agent)

Do **not** keep burning local nights on `npx tauri build`.

## What is web vs Agent (sync)

| Change | Where it lives | Employees get it how? |
|--------|----------------|------------------------|
| Screenshot thumbs / PDF URLs (`resolveUrl`) | **Web** (browser + Manager shell) | VPS `npm run build` + deploy `dist` — **already on live JS** |
| API `/agent/version` | **API** | `systemctl restart ems-api` — **live `1.1.0`** |
| Idle 30s, dual monitors, Re-enroll button, update banner, Agent UI | **Agent exe only** | New `CFS-Agent-Install.zip` install — **not** automatic from web |
| Manager desktop icon / Setup | **Tauri binary** | New Setup.exe (Actions build) |

**Not the same app:** Web/Manager UI ≠ Agent. Agent features are **not** “synced” into the website; website features are **not** inside the Agent exe except that Agent talks to the same API.

## Production today (safe)

- Agent zip live → staff reinstall once  
- Admin/HR use **browser** `https://ems.cfsdesigners.com` until Setup.exe from Actions is uploaded  
