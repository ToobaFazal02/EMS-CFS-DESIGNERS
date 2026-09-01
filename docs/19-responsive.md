# Responsive layout (all screens)

## Rule

UI must work and look intentional on:

- Agent: typical 1366×768 → 1920×1080 → 2560×1440 / ultrawide
- Manager web: laptop, desktop, large monitor, tablet

## Large screens — DO NOT

- Tiny centered column with huge empty side gutters (looks abandoned)
- Fixed 600px content forever

## Large screens — DO

- Use the **full manager shell width** (same as the top nav). Do not pin the dashboard to a ~1800px island — on 2560px that looks zoomed-out.
- Scale **type and chart chrome** up at 1920 / 2560 so KPI cards and donuts keep 1440-like density, instead of tiny text on a stretched slab
- Ultrawide: more live-board cards per row, keep side padding modest (≈40px), not 40% empty
- Tables: full useful width, sticky header
- Agent window: scalable layout, not postage-stamp on 4K

## Small screens / phones (locked 31 Aug 2026)

Client opened `https://ems.cfsdesigners.com` on a phone. The manager web **must** work there, not desktop-only.

- Hamburger nav (do not wrap 7 links onto two cramped rows)
- Header / navbar stays **sticky** on scroll (blur bar, same as Lovable mock)
- Settings **gear** for Account + Logout
- Screenshots: full-width, `object-fit: contain` (no tiny image in a huge 16:9 hole)
- Lightbox prev/next stack under the image on narrow viewports
- Employees add-form stacks; staff table becomes labeled cards
- Grids: `minmax(min(100%, 280px), 1fr)` so 360px phones do not overflow
- Thin **black/gold** scrollbars

Agent remains desktop-first (Windows PCs).

## Checklist

- [x] 1366 width usable
- [x] 1920 balanced (18px base, dashboard full shell width)
- [x] 2560+ same fill as 1440 (no centered island); 19px base + larger sparks/donut/hours chart
- [x] Phone / tablet manager web (31 Aug 2026)

Dashboard details: `docs/44-dashboard-predeploy.md`.
