# Phase 1: Tauri Desktop — Implementation (live)

**Official docs:** https://v2.tauri.app/start/prerequisites/ · https://v2.tauri.app/start/create-project/

## Done (11 Sep 2026)

- [x] Rust + MSVC + C++ Build Tools
- [x] `@tauri-apps/cli@latest` in `apps/web`
- [x] `src-tauri/` init — product **CFS Designers**, id `com.cfsdesigners.ems`
- [x] CFS logo icons (`npx tauri icon app-icon-source.png`)
- [x] NSIS `installerIcon` / `uninstallerIcon` → `icons/icon.ico` (Setup.exe shows CFS, not default NSIS)
- [x] Desktop production API → `https://ems.cfsdesigners.com` (Tauri non-dev)
- [x] `/downloads` page — Manager `.msi` + Agent `.zip` + enroll security note
- [x] Login link → Downloads (public, no login required for staff)

## Build installer

```powershell
cd D:\imp\ems-cfs-designers\apps\web
npm run tauri:build
```

Outputs (typical):
- `src-tauri/target/release/bundle/msi/CFS Designers_0.1.0_x64_en-US.msi`
- `src-tauri/target/release/bundle/nsis/CFS Designers_0.1.0_x64-setup.exe`

Copy Manager installer to:

```
apps/web/public/downloads/CFS-Designers-Manager.msi
```

Then rebuild web / deploy `dist` + copy Agent zip as `CFS-Agent-Install.zip`.

## VPS CORS (required for desktop app)

In production `.env`:

```
CORS_ORIGINS=https://ems.cfsdesigners.com,https://tauri.localhost,http://tauri.localhost,tauri://localhost
```

Then `systemctl restart ems-api`.

## Deploy web + downloads

```bash
cd /opt/ems-src && git pull
cd apps/web && npm ci && npm run build
cp -r dist/* /var/www/ems/
# also copy MSI + Agent zip into /var/www/ems/downloads/
```

## Security workflow (locked)

1. Staff download Agent from `/downloads` (public)
2. Admin generates enroll code on Employees
3. Staff paste code once — no CEO visit to each PC
4. Codes are one-time / device-bound — download alone cannot track
