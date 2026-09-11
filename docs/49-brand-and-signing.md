# Brand assets (CFS Designers official logo)

Source of truth: **https://cfsdesigners.com/** official assets
(`favicon-192.png`, `logo.png`, etc. — orange/silver CFS monogram).

Do **not** use the old gold serif “CFS” square SVG for tabs/icons.

| File | Use |
|------|-----|
| `public/favicon-32.png` / `favicon-48.png` / `favicon.png` | Browser tab (same as website) |
| `public/favicon-192.png` | Nav / login mark / Tauri source |
| `public/logo.png` | Full wordmark (optional) |
| `app-icon-source.png` | `npx tauri icon` → Manager desktop |
| `apps/agent/assets/cfs-logo.png` | Agent window / tray |
| `apps/agent/assets/cfs-agent.ico` | Agent `.exe` icon |

Refresh icons after replacing PNGs:

```powershell
cd D:\imp\ems-cfs-designers\apps\web
Copy-Item C:\laragon\www\cfs-designers\assets\images\favicon-192.png .\app-icon-source.png -Force
Copy-Item .\app-icon-source.png .\public\brand-mark.png -Force
npx tauri icon app-icon-source.png
npm run tauri:build
# then copy Setup.exe + MSI into public/downloads/
```

Rebuild Agent (for tray/exe icon):

```powershell
cd D:\imp\ems-cfs-designers\apps\agent
# pyinstaller cfs-agent.spec  (then re-zip CFS-Agent-Install)
```

## Code signing (“Unknown Publisher”)

Windows SmartScreen / “publisher could not be verified” happens because the Setup.exe is **not Authenticode-signed**.

- Logo + correct icon = branding only
- Removing the warning permanently needs a **code signing certificate** (e.g. Sectigo / DigiCert, ~USD 200–400/yr) + sign the NSIS/MSI after build
- Until then: tell staff “CFS Designers official installer — click More info → Run anyway” once SmartScreen appears

## Agent zip “archive damaged”

If zip is ~1–2 KB, production served the **SPA HTML** (file missing on VPS). Real zip is ~50 MB on Desktop / `apps/web/public/downloads/`.

```bash
# Web Console — size must be ~50M not 1K
ls -lah /var/www/ems/downloads/CFS-Agent-Install.zip
```

Upload from PC (mobile hotspot if SSH blocked):

```powershell
scp "$env:USERPROFILE\Desktop\CFS-Agent-Install.zip" root@187.53.129.62:/var/www/ems/downloads/CFS-Agent-Install.zip
```
