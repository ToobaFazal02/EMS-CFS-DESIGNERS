# Phase 1: Tauri Desktop App — Implementation Plan

**Start:** 11 Sep 2026  
**Goal:** Windows `.exe` installer — manager software (Dashboard, Payments, Employees) in branded desktop app.

---

## Day 1 — Setup Tauri + folder structure

### Install Tauri CLI

```bash
cargo install tauri-cli --version "^2.0"
rustc --version  # confirm Rust installed
```

(Windows: install [Rust](https://rustup.rs/) first if missing.)

### Create `apps/manager-desktop/` folder

```
apps/
  manager-desktop/          ← NEW
    src-tauri/              ← Rust backend
      Cargo.toml
      tauri.conf.json
      src/
        main.rs
    public/                 ← React build output (copy from web/dist)
    package.json
    README.md
  web/                      ← existing React (no changes)
  api/                      ← existing FastAPI (no changes)
  agent/                    ← existing PySide (no changes)
```

### Initialize Tauri

```bash
cd apps/manager-desktop
npm init -y
npm install --save-dev @tauri-apps/cli @tauri-apps/api
npx tauri init
```

Answers:
- App name: **CFS Designers**
- Window title: **CFS Designers — Manager**
- Web assets: `../web/dist`
- Dev server: `http://localhost:5173`
- Before dev: leave blank (web already runs)
- Before build: `cd ../web && npm run build`

### Edit `tauri.conf.json`

```json
{
  "build": {
    "beforeBuildCommand": "cd ../web && npm run build",
    "beforeDevCommand": "",
    "devUrl": "http://localhost:5173",
    "frontendDist": "../web/dist"
  },
  "productName": "CFS Designers",
  "version": "1.0.0",
  "identifier": "com.cfsdesigners.ems",
  "app": {
    "windows": [
      {
        "title": "CFS Designers — Manager",
        "width": 1400,
        "height": 900,
        "resizable": true,
        "fullscreen": false,
        "decorations": true
      }
    ],
    "security": {
      "csp": null
    }
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ],
    "windows": {
      "wix": {
        "language": "en-US"
      }
    }
  }
}
```

---

## Day 2 — Icons + branding

### Generate icons

Use existing CFS logo (black/gold) — create:
- `icons/32x32.png`
- `icons/128x128.png`
- `icons/icon.ico` (Windows)
- `icons/icon.icns` (Mac)

Tools: [tauri-icon](https://github.com/tauri-apps/tauri-icon) or ImageMagick.

```bash
npm install @tauri-apps/cli
npx tauri icon path/to/cfs-logo-512.png
```

Puts icons in `src-tauri/icons/`.

### Custom window frame (optional — branded black/gold titlebar)

Edit `tauri.conf.json`:

```json
"windows": [
  {
    "decorations": false,  // remove default titlebar
    "transparent": true
  }
]
```

Then add custom drag region in React (CSS: `-webkit-app-region: drag`).

**Skip for MVP** — default Windows frame is fine; polish later.

---

## Day 3 — Build + installer

### Dev run (test)

```bash
cd apps/manager-desktop
npx tauri dev
```

Opens window with web UI (if `apps/web` running on :5173).

### Production build

```bash
npx tauri build
```

Output:
- Windows: `src-tauri/target/release/bundle/msi/CFS-Designers_1.0.0_x64_en-US.msi`
- Installer size: ~5–8 MB (webview2, no Chromium bundled)

**Test:** install on clean Windows VM / second PC.

---

## Day 4 — Auto-update (optional for v1.1)

Tauri supports built-in updater:

1. Host releases on GitHub Releases / own server
2. `tauri.conf.json`:

```json
"updater": {
  "active": true,
  "endpoints": ["https://ems.cfsdesigners.com/updates/{{target}}/{{current_version}}"],
  "dialog": true,
  "pubkey": "..."
}
```

3. Sign builds with keypair (`tauri signer generate`)

**MVP:** skip auto-update — manual reinstall for now.

---

## Day 5 — System tray + polish

### Add tray icon

`src-tauri/src/main.rs`:

```rust
use tauri::Manager;

fn main() {
  tauri::Builder::default()
    .setup(|app| {
      let tray = tauri::SystemTray::new();
      app.handle().tray_handle().set_icon(tauri::Icon::Raw(include_bytes!("../icons/icon.ico").to_vec()))?;
      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
```

**Minimize to tray** on close:

```rust
.on_window_event(|event| {
  if let tauri::WindowEvent::CloseRequested { api, .. } = event.event() {
    event.window().hide().unwrap();
    api.prevent_close();
  }
})
```

Tray menu: **Show / Quit**.

---

## Day 6–7 — QA + client demo

### Test checklist

- [ ] Install on fresh Windows 10/11
- [ ] Icon in Start Menu
- [ ] Window branded (black + gold theme visible)
- [ ] Dashboard loads from `ems.cfsdesigners.com`
- [ ] Login works
- [ ] Payments, Employees, Projects — all pages functional
- [ ] Close → tray (if implemented)
- [ ] Uninstall clean (no leftover files)

### Demo to client

- Screen record: Start Menu → CFS Designers icon → opens → Dashboard
- Compare: "no browser address bar, feels like VSCode"
- Show: minimize to tray, reopen

### Deliver `.msi` + install instructions

**`INSTALL-MANAGER.txt`:**

```
CFS Designers Manager (Desktop Software)

1. Double-click CFS-Designers_1.0.0_x64_en-US.msi
2. Follow installer prompts (default options OK)
3. Opens Start Menu → CFS Designers
4. Login with admin/manager account

Network: requires internet — connects to ems.cfsdesigners.com
```

---

## Technical notes

**Hosting:** Desktop app talks to **existing VPS API** — no extra server.  
**Size:** ~5–8 MB installer (uses system webview2, not Electron's 150 MB).  
**Feel:** Native window, taskbar icon, Start Menu — exactly like VSCode/Cursor.  
**Updates:** Manual reinstall MVP; auto-update in v1.1 (Tauri built-in).  
**Offline:** App shell loads, but needs API — same as web (login = cloud auth).  

**Mac:** same Tauri project builds `.dmg` — change target in `tauri.conf.json`.

---

## Risks / fallback

| Risk | Mitigation |
|------|-----------|
| Rust/Tauri new to team | Tauri docs clear; worst case → Electron (heavier but easier) |
| Webview2 missing on old Windows | Installer auto-downloads (10 MB) — rare issue |
| Client wants "more native" look | Phase 1.1: custom titlebar, themes — outside MVP |

MVP = working `.exe`, branded icon, production-ready. Polish = later sprints.

---

## After Phase 1 → Phase 2

Desktop done → move to PWA (mobile/tablet) — separate sprint, no code conflict.

**Parallel work safe:** Tauri wraps web `dist`; PWA adds manifest to same `dist`. Both coexist.
