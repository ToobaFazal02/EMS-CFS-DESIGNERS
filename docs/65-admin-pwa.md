# Phase D — Admin-only mobile PWA

**Status:** Implemented on branch `desktop+agent` (20 Sep 2026).

## Rules (client lock)

- Phone = **Admin / Manager / HR glance only**
- Employee **Sign In / Out / screenshots** stay on **PC Agent** — never a phone punch surface
- PWA install prompt + service worker register **only after office login**

## What shipped

| Item | Detail |
|---|---|
| `public/manifest.webmanifest` | Installable name/icons/standalone |
| `public/sw.js` | Shell cache; **`/api` never cached** |
| `AdminPwaInstall` | `beforeinstallprompt` + iOS Add-to-Home tip |
| SW register | From Shell when role is office/demo |

## Test

1. Admin login on Android Chrome (HTTPS production)
2. Banner **Install Admin app** → Install
3. Open from home screen → Live / Day / Projects
4. Employee login → no install banner, no SW register from Shell
