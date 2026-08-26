# Frontend UI quality (agent + manager web)

## Non-negotiable

- **One design system** — shared colors (`docs/14-ui-theme.md`), spacing scale, type scale, button variants. No one-off random sizes.
- **Consistent type:** Inter or system UI stack for ops UI (not Playfair — that is CFS marketing site). Sizes: 12 / 14 / 16 / 20 / 24 / 32 only.
- **Buttons:** every button visible contrast, clear label, hover + focus ring, disabled state greyed + not clickable, loading state if async. Primary = navy; secondary = outline; danger = red for destructive only.
- **Smooth:** no janky layout jump; transitions ≤ 200ms; respect `prefers-reduced-motion`.
- **Accessible:** keyboard tab order, visible focus, labels on inputs, contrast AA on text, real `alt` on images/screenshots thumbs, don’t rely on color alone (online = green + “Online” text).
- **Working ≠ pretty mock:** click every control in checklist before calling a screen done.
- **Subtle:** dense ops dashboard — no emoji decoration, no purple glow, no pill spam, no fake skeleton delays.

## Spacing / layout

- 4px base grid (8 / 12 / 16 / 24 / 32).
- Cards only where they group interactive content; live board = clear rows/cards with one job each.
- Mobile: manager web usable on tablet; agent is desktop Windows.

## Checklist before “UI done”

- [ ] All buttons do something or are correctly disabled
- [ ] Empty + error + loading states exist
- [ ] Focus visible with keyboard only
- [ ] Same button styles reused (no 5 different blues)
- [ ] Screenshot thumbs don’t break layout
- [ ] Checked on ~1366, 1920, and 2560 widths (no tiny island on large screens)

## Responsive

Full rules in `docs/19-responsive.md`. Large monitors expand useful panels; never leave half the screen empty with a tiny centered column.