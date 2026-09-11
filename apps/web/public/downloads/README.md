# Installers served at `/downloads/…`

| File | Purpose |
|------|---------|
| `CFS-Designers-Manager-Setup.exe` | Preferred Windows installer (NSIS) |
| `CFS-Designers-Manager.msi` | Alternate MSI |
| `CFS-Agent-Install.zip` | Employee Agent pack — upload from packaging / Desktop |

Rebuild Manager after code changes:

```powershell
cd apps\web
npm run tauri:build
# then copy from Tauri bundle output → these filenames
```
