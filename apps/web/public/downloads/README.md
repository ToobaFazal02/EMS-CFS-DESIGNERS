# Public download binaries

| File | Size (approx) | Notes |
|------|----------------|-------|
| `CFS-Designers-Manager-Setup.exe` | ~58 MB | Tauri NSIS — upload after `REBUILD-MANAGER-ICON.bat` |
| `CFS-Designers-Manager.msi` | ~59 MB | Tauri MSI — optional |
| `CFS-Agent-Install.zip` | ~50 MB | **gitignored** — build with `apps/agent/BUILD-EXE.bat`, upload to VPS |

## Agent version (auto-update banner)

API (no auth): `GET https://ems.cfsdesigners.com/api/v1/agent/version`

```json
{"agent_version":"1.1.0","download_url":"https://ems.cfsdesigners.com/downloads"}
```

Agents **v1.1.0+** compare this to their local `AGENT_VERSION`. If newer → banner + Download button.
**First deploy of v1.1.0 still requires manual install** on each PC (old Agents do not have the checker).

When releasing a new Agent:

1. Bump `AGENT_VERSION` in `apps/agent/ems_agent/__main__.py`
2. Bump `LATEST_AGENT_VERSION` in `apps/api/app/routers/agent.py`
3. Rebuild zip → upload here → restart `ems-api`

Full deploy: `docs/51-deploy-sep13-idle-reenroll-update.md`

## VPS check (Web Console)

```bash
mkdir -p /var/www/ems/downloads
ls -lah /var/www/ems/downloads
# Agent zip MUST be ~50M. If ~1K, nginx is serving website HTML — file missing.
curl -s https://ems.cfsdesigners.com/api/v1/agent/version
```

## Upload Agent (from your PC)

If SSH port 22 times out, use GitHub Release + `wget` on VPS (same as before), or Hostinger file tools.

```powershell
scp "$env:USERPROFILE\Desktop\CFS-Agent-Install.zip" root@YOUR_VPS_IP:/var/www/ems/downloads/CFS-Agent-Install.zip
```
