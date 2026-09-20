# Phase D — Admin-only mobile PWA

**Status:** Implemented on branch `desktop+agent` (20 Sep 2026).  
**Not** a Play Store / App Store download — home-screen install of the Manager website.

## Rules (client lock)

- Phone = **Admin / Manager / HR glance only**
- Employee **Sign In / Out / screenshots** = **PC Agent only**
- PWA register + install UI only after office login

## How Admin installs

1. Open **`https://ems.cfsdesigners.com`** on the phone (must be HTTPS / production).
2. Log in as Admin (or Manager / HR).
3. Tap banner **Install Admin app** → **Install**,  
   **or** Chrome ⋮ → Install app / Add to Home screen,  
   **or** iPhone Safari → Share → Add to Home Screen.
4. Open the new home icon (standalone window).

Localhost / Desktop Tauri will often **not** show the Install button — that is normal. Use production URL on a real phone.

## Feature coverage on PWA

| Feature | On phone PWA? |
|---|---|
| Dashboard / Live / Day / Projects / Payments / Reports / Downloads | Yes (same React) |
| Notify bell + mark read | Yes |
| Unpaid red cards / 7-day progress | Yes |
| View PDF | Yes |
| Employee Sign In / Break / shots | **No** (Agent only) |
| Enroll PC | No (Admin does enroll on web/Desktop; code goes to staff PC) |

## Files

| Path | Role |
|---|---|
| `apps/web/public/manifest.webmanifest` | Install metadata |
| `apps/web/public/sw.js` | Shell cache; `/api` never cached |
| `AdminPwaInstall.tsx` | Banner + dismiss |

## Related

- Test steps: `docs/66-desktop-notify-pwa-test.md`
- Overall status: `STATUS.md`
