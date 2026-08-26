# Idle, multi-session, PDF reports (locked)

## Install

Yes — **EMS Windows agent har employee PC pe install** hota hai.  
Flow: kaam se pehle **Sign In** → kaam → (optional Break) → **Sign Out**. Autostart on Windows logon = recommended so they don’t forget.

---

## Idle / away / static screen (MUST — employer can see)

If mouse + keyboard quiet for a configurable time (default **3 minutes**, Hubstaff/DeskTime style):

| What happens | Manager sees |
|---|---|
| Status → **Idle** (not “Online working”) | Live board: Idle since hh:mm |
| Optional: pause activity scoring / flag idle minutes | Day timeline: grey Idle blocks |
| Screenshots may still fire on interval **or** skip while idle (default: **skip while idle** to save disk + avoid useless static shots) | Idle reason clear in report |
| Window title still last known (e.g. YouTube tab open but no input) | “Last window” + idle duration |

So: employee 1–2 hours chala gaya, ya screen static ek site pe, clicks/keys nahi — **CEO ko pata chalega** (Idle + duration). Ye “silent cheat” band karta hai.

Idle ≠ Sign Out for short idle. Tracking session stays open while Idle **until**:

### Auto Sign Out (sleep / shutdown / long away) — MUST

| Event | Behavior |
|---|---|
| PC **sleep / hibernate / lid close** | Agent **auto Sign Out** immediately (before / on suspend). Hours stop. |
| **Shutdown / logoff** / agent quit while signed in | Auto Sign Out |
| PC **wakes** still “signed in” (missed suspend event) | Auto Sign Out + skip blank screenshots for ~90s |
| No mouse/keyboard for **`auto_sign_out_idle_seconds`** (default **30 min**) | Auto Sign Out (after Idle first) |
| Blank / solid-color capture (wake black screen) | **Discarded** — not uploaded |

Intentional **Break** is not auto-closed by idle alone (lunch OK); sleep still closes the day session.

After auto Sign Out → employee must **Sign In** again to resume tracking.

---

## Same day: Sign Out then Sign In again (MUST)

Example: 09:00–11:00 work → Sign Out → 14:00 Sign In again → 18:00 Sign Out.

| Correct behavior | Wrong |
|---|---|
| **Multiple sessions** same calendar day | Second Sign In “continues” first as if never left |
| Session 1: 09:00–11:00 (2h) | One fake continuous 09:00–18:00 |
| Session 2: 14:00–18:00 (4h) | |
| **Daily report** = one day PDF with **Session 1 + Session 2** listed, plus **Net total hours** = 6h | Two disconnected PDFs only with no day total |
| Monthly = sum of all sessions that month | |

Break In/Out = still inside one session (lunch without full Sign Out).  
Full leave mid-day → **Sign Out** (clean). Return → **new Sign In** = new session.

Punch sequence per session: Sign In → optional Breaks → Sign Out.  
Forgot Sign Out: day flagged incomplete; manager can fix with audit.

---

## PDF template quality (MUST)

Not a dump of raw tables that nobody can read.

**Daily PDF structure (professional):**

1. Cover strip: Employee name, date, timezone, net hours, sessions count  
2. Sessions table: each Sign In/Out + duration  
3. Summary: total clicks, key presses, idle minutes, break minutes  
4. 30‑min activity chart (readable labels, not overlapping)  
5. Top windows/apps (Work vs Other) — top 15, not 800 noise rows on page 1  
6. Optional appendix: detailed minute log (or link “full log in system”)  
7. Screenshot index: thumbnails grid with timestamps (not 34 pages of junk first)

Formatting: navy/black/white, margins, page numbers, “EMS CFS Designers”, generated timestamp, consistent fonts. Printable A4.

**Monthly PDF:** days present, totals, late count, idle hours trend, top apps — one clean compile per employee + team rollup.
