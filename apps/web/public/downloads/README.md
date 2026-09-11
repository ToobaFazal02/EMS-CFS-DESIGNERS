# Installers served at `/downloads/…`

| File | Purpose |
|------|---------|
| `CFS-Designers-Manager-Setup.exe` | Preferred Windows installer (NSIS) |
| `CFS-Designers-Manager.msi` | Alternate MSI |
| `CFS-Agent-Install.zip` | Employee Agent (~50MB) — **not in git**; copy from Desktop pack |

## Agent zip (local)

```powershell
Copy-Item "$env:USERPROFILE\Desktop\CFS-Agent-Install.zip" `
  D:\imp\ems-cfs-designers\apps\web\public\downloads\CFS-Agent-Install.zip
```

## Agent zip (VPS)

```bash
# from your PC:
scp CFS-Agent-Install.zip root@YOUR_VPS_IP:/var/www/ems/downloads/
```
