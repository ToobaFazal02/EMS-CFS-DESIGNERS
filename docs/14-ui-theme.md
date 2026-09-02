# UI theme — UPDATED per client voice 20 Aug 2026

## Choice: **Black · Yellow/Gold · White**

Client asked black and yellow. Aligns with CFS brand. Replaces earlier navy proposal.

## Tokens

```css
--bg:            #0A0A0A;   /* black */
--surface:       #141414;
--surface-2:     #1F1F1F;
--border:        #333333;
--text:          #FFFFFF;
--text-muted:    #A3A3A3;
--accent:        #C9A227;   /* gold/yellow */
--accent-hover:  #E0B93A;
--accent-soft:   #3D3415;   /* dark gold tint on black UI */
--success:       #22C55E;   /* online */
--warning:       #F59E0B;   /* break / idle */
--danger:        #EF4444;   /* live blink / offline / late */
--live-blink:    #FF2020;   /* agent corner LIVE indicator */
--on-accent:     #0A0A0A;   /* text on yellow buttons */
```

Light PDF pages: white bg, black text, gold rules/headers.

## Web appearance (Account → Appearance)

Default is **dark**. Client can switch **Light** on Account (gear). Choice is `localStorage ems_theme` and `html[data-theme]`. Applied in `index.html` before paint so the first frame matches.

Light tokens (cream + gold, same brand):

```css
--bg:            #F3EFE6;
--surface:       #FFFDF8;
--text:          #1C1914;
--text-muted:    #5C564C;
--gold / accent: #C9A227;
--on-accent:     #1C1914;
```

Gold-on-cream body links use `#6B560F` so type stays readable. Buttons stay gold with dark label.

## First-five-visit guide cards

Installer-style **Skip / Next** cards (no extra npm tour library). Shown after login on each tab. Count `ems_guide_opens` once per browser session; after **5 opens** they never show again. Skip hides the rest of that visit. Not painted as permanent copy on the page.

## Agent LIVE badge (client requirement)

- Corner of agent window (and tray tooltip): **LIVE** when signed in and tracking  
- **Red blinking** while recording  
- Break: show **BREAK** (amber), not LIVE blink  
- Sign Out: badge off / grey Idle offline  

## Do not

- Purple gradients, neon glow spam  
- Hide the Live badge (client wants visible monitoring)  
- Navy as primary (superseded by client black/yellow)
