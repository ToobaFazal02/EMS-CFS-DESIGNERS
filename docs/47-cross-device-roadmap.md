# Cross-Device Software — Roadmap & Milestones

**Client requirement:** EMS ko installed software banao — laptop, phone, tablet sab pe. Browser tab nahi, proper application icon aur feel chahiye.

**Solution:** Existing React web + FastAPI backend ko multi-device wrappers se package karo — **rewrite nahi**.

---

## Phase 1: Desktop App (Tauri) — **Priority 1**

**Goal:** Windows/Mac installed software — VSCode/Cursor jaisi feel, Start Menu icon, `.exe` installer.

**Tech:** Tauri 2 (Rust + webview) wraps existing React build.

**Deliverables:**
- ✅ Windows installer (`CFS-Designers-Manager-Setup.exe`)
- ✅ Mac `.dmg` / `.app` (optional if team uses Mac)
- ✅ Frameless/branded window (black + gold theme)
- ✅ Auto-update check
- ✅ System tray option (minimize to background)
- ✅ Clean uninstall

**Timeline:** 5–7 working days (1 focused dev)

**Cost:** Zero hosting — client install on their laptops.

**User experience:**
- Manager opens **CFS Designers** from Start Menu
- Black/gold branded window (no browser address bar)
- Same Dashboard / Payments / Employees — feels native
- Network: talks to `https://ems.cfsdesigners.com` API (same backend)

---

## Phase 2: PWA (Mobile & Tablet) — **Priority 2**

**Goal:** Phone/tablet "Add to Home Screen" → app drawer icon, full screen, offline cache.

**Tech:** Progressive Web App (web standards: manifest, service worker).

**Deliverables:**
- ✅ `manifest.json` (app name, icons, theme colors)
- ✅ Service Worker (cache static assets, offline fallback)
- ✅ Install prompt for supported browsers
- ✅ Splash screen (black + gold branding)
- ✅ iOS Safari + Android Chrome compatible

**Timeline:** 3–4 working days

**Cost:** Zero — same VPS hosting.

**User experience:**
- Manager opens Chrome on phone → "Install CFS Designers"
- Icon appears in app drawer (Android) / home screen (iOS)
- Opens full screen, no browser UI
- Works offline if service worker caches dashboard
- Same login, same data

---

## Employee Agent (Phase 0 — already done)

**Deliverable:** Windows tracking app (`CFS-Agent-Install.zip`) for office PCs.

**Status:** Exists, no changes needed. Separate from manager app.

---

## Cost breakdown

| Component | Hosting | License | Total extra |
|-----------|---------|---------|-------------|
| Desktop app (Tauri) | Client install — none | Free (MIT) | **₹0** |
| PWA (mobile) | Same VPS | Free | **₹0** |
| Backend API | Existing Hostinger VPS | Already paid | **₹0** |

**VPS capacity:** Same FastAPI handles 50+ users — no extra server.

---

## Architecture (no rebuild)

```
┌─────────────────┐
│  Desktop (Tauri) │──┐
└─────────────────┘  │
                     │    HTTPS
┌─────────────────┐  ├──► ┌──────────────────┐
│  Phone (PWA)    │──┤    │ FastAPI + SQLite │
└─────────────────┘  │    │ (VPS Hostinger)  │
                     │    └──────────────────┘
┌─────────────────┐  │
│  Tablet (PWA)   │──┘
└─────────────────┘

┌─────────────────┐
│ Employee Agent  │──► Same API (enroll, punch, upload)
└─────────────────┘
```

All clients use **same React code**, **same API**, **same data** — naya server nahi.

---

## Client delivery order

1. **Now:** VPS web `ems.cfsdesigners.com` live — browser review
2. **Week 1 (Phase 1):** Desktop installer beta — manager software feel
3. **Week 2 (Phase 2):** PWA live — mobile/tablet "install app"
4. **Parallel:** Employee Agent zip (already exists)

---

## Success criteria

- [ ] Manager opens **CFS Designers** icon (not Chrome tab)
- [ ] Window feels native (branded, no address bar, system tray)
- [ ] Phone "Add to Home Screen" → app icon works
- [ ] Same login all devices
- [ ] No extra hosting cost
- [ ] Installer clean (sign later optional — Inno Setup / real cert)

---

## Future polish (optional)

- Code signing certificate (Windows installer trust)
- Mac App Store submission (if client wants)
- Linux AppImage (if office uses Ubuntu)
- Offline-first mode (service worker caching aggressive)

Phase 1 & 2 = production-ready without these extras.
