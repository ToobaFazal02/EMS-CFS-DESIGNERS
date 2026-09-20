# Phase D — Admin / HR mobile PWA

**Status:** Implemented on branch `desktop+agent` (updated 20 Sep 2026).  
**Not** a Play Store / App Store download — home-screen install of the Manager website.

## Who can install

| Role | Install banner / SW |
|---|---|
| **Admin** | Yes |
| **HR** | Yes |
| Manager | **No** |
| Employee | **No** |
| Demo | **No** |

## Rules (client lock)

- Phone = **Admin / HR glance only**
- Employee **Sign In / Out / screenshots** = **PC Agent only**
- PWA register + install UI only after Admin or HR login

## How Admin / HR installs

1. Open **`https://ems.cfsdesigners.com`** on the phone (must be HTTPS / production).
2. Log in as **Admin** or **HR**.
3. Tap banner **Install Admin / HR app** → **Install**,  
   **or** Chrome ⋮ → Install app / Add to Home screen,  
   **or** iPhone Safari → Share → Add to Home Screen.
4. Open the new home icon (standalone window).

Localhost / Desktop Tauri will often **not** show the Install button — that is normal. Use production URL on a real phone.

## Feature coverage on PWA

| Feature | On phone PWA? |
|---|---|
| Dashboard / Live / Day / Projects / Reports | Yes (role-gated) |
| Payments (Admin; HR usually blocked by finance gate) | Per role API |
| Notify bell | Yes (office) |
| Unpaid red cards / 7-day progress (employee dropdowns) | Yes |
| View PDF | Yes |
| Employee Sign In / Break / shots | **No** (Agent only) |

## Files

| Path | Role |
|---|---|
| `apps/web/public/manifest.webmanifest` | Install metadata |
| `apps/web/public/sw.js` | Shell cache; `/api` never cached |
| `AdminPwaInstall.tsx` | Banner — Admin/HR only |

## Related

- Test steps: `docs/66-desktop-notify-pwa-test.md`
- PDF pack: `docs/pdfs/`
- Overall status: `STATUS.md`
