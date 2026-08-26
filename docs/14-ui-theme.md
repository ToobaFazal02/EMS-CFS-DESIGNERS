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

## Agent LIVE badge (client requirement)

- Corner of agent window (and tray tooltip): **LIVE** when signed in and tracking  
- **Red blinking** while recording  
- Break: show **BREAK** (amber), not LIVE blink  
- Sign Out: badge off / grey Idle offline  

## Do not

- Purple gradients, neon glow spam  
- Hide the Live badge (client wants visible monitoring)  
- Navy as primary (superseded by client black/yellow)
