# Client voice — 20 Aug 2026, 8:23 PM (LOCKED INTENT)

Source: `WhatsApp Ptt 2026-08-20 at 8.23.35 PM.ogg` (~72s)  
Whisper EN: `references/client-voice-2026-08-20-en.txt`  
Status: **Plan finalize → then implement** (STATUS.md still not approved for code)

---

## What the client said (interpreted, no sugarcoat)

| # | Client said (sense) | Our plan response |
|---|---|---|
| 1 | **Live** — manager PC pe dekh sake kya ho raha hai; system **internet se connected** hoga | Manager web **live board** (status + last screenshot + last window). Needs network to server. Not continuous video. |
| 2 | Theme **black and yellow** (Whisper: “black and yellow”) | **Theme change from navy → Black + Yellow/Gold + White** to match his ask + CFS brand. Update `docs/14-ui-theme.md` on finalize. |
| 3 | **Sign In, Break In, Break Out, Sign Out** — full punch flow | Keep all four buttons. (Wording “break in = sign out” was garbled — we implement standard 4 punches, not merge them.) |
| 4 | Software screen ke **corner pe LIVE indicator** — **blinking red** “Live / monitoring” | Agent UI: always-visible **Recording/Live** badge (red blink when tracking). Transparency, not stealth. |
| 5 | **Administrator** — software fully equipped; background / screen capture possible | Admin/manager role on web; agent can run in tray/background with capture; employee still sees Live badge. |
| 6 | Future: agar project successful → copy/brand → **sell to other companies** | Architecture already multi-tenant-ready later; **v1 = CFS only**. White-label = Phase 2+ product decision, not v1 scope creep. |

---

## Confirmed product shape (client-aligned)

```
Employee PC (agent, black/yellow UI)
  Sign In → Live red blink ON
  optional Break In / Break Out
  screenshots + clicks + idle
  Sign Out → Live blink OFF, new tracking stops
        ↓ internet/LAN to server
Office server (DB + screenshots + reports)
        ↓
Manager / Admin website
  Live board + daily + monthly reports + history always
```

---

## Finalize checklist (before coding)

Ask client only if still fuzzy — otherwise treat as OK:

- [x] Live view for manager (not video) — YES from voice  
- [x] Black + yellow theme — YES from voice  
- [x] Sign In / Break In / Break Out / Sign Out — YES  
- [x] Red blinking Live on agent corner — YES  
- [x] Admin-capable / screen capture — YES  
- [ ] Server: office on-prem vs VPS (still recommend on-prem; voice said “internet connected” = agents reach server, not “must be public cloud”)  
- [ ] Screenshot interval 5 min random — soft OK unless he objects  
- [ ] You (Tooba) say: scope + quote OK → flip `STATUS.md` → Phase 1 build  

---

## Explicitly NOT in v1 (even if “sell later” excited)

- Selling/white-label marketplace packaging  
- Live video stream  
- Hidden agent without Live badge  
- Keylogging typed text  

---

## Implementation order (after finalize)

1. Theme tokens → black / yellow / white  
2. API + auth + punches (4 types) + multi-session + idle  
3. Agent UI with Live blink + tray  
4. Screenshots + activity sync  
5. Manager live board  
6. Daily + monthly PDF (readable templates)  
7. Pilot 2–3 PCs  

Do not start app code until user updates `STATUS.md` to `EXECUTION_APPROVED: yes`.
