# Responsive layout (all screens)

## Rule

UI must work and look intentional on:

- Agent: typical 1366×768 → 1920×1080 → 2560×1440 / ultrawide
- Manager web: laptop, desktop, large monitor, tablet

## Large screens — DO NOT

- Tiny centered column with huge empty side gutters (looks abandoned)
- Fixed 600px content forever

## Large screens — DO

- Use **max fluid width** with sensible max (e.g. dashboard content up to ~1600–1800px) then **expand useful panels** (more columns on live board, wider tables)
- Ultrawide: split live board into more employee cards per row, keep margins modest (24–48px), not 40% empty
- Tables: full useful width, sticky header
- Agent window: scalable layout, not postage-stamp on 4K

## Small screens

- Stack panels; touch-friendly targets on tablet for manager web
- Agent remains desktop-first (Windows PCs)

## Checklist

- [ ] 1366 width usable
- [ ] 1920 balanced
- [ ] 2560+ uses space (more columns / wider charts), not tiny island
- [ ] No horizontal scroll on primary dashboards at 1280+
