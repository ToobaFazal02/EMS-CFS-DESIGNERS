# Public download binaries

| File | Size (approx) | Notes |
|------|----------------|-------|
| `CFS-Designers-Manager-Setup.exe` | ~58 MB | Tauri NSIS — in git (large) |
| `CFS-Designers-Manager.msi` | ~59 MB | Tauri MSI — in git (large) |
| `CFS-Agent-Install.zip` | ~50 MB | **gitignored** — must upload to VPS manually |

## VPS check (Web Console)

```bash
mkdir -p /var/www/ems/downloads
ls -lah /var/www/ems/downloads
# Agent zip MUST be ~50M. If ~1K, nginx is serving the website HTML — file missing.
```

## Upload Agent (from your PC PowerShell + mobile hotspot)

```powershell
scp "$env:USERPROFILE\Desktop\CFS-Agent-Install.zip" root@187.53.129.62:/var/www/ems/downloads/CFS-Agent-Install.zip
```

Or copy local build folder file:

```powershell
scp "D:\imp\ems-cfs-designers\apps\web\public\downloads\CFS-Agent-Install.zip" root@187.53.129.62:/var/www/ems/downloads/
```
