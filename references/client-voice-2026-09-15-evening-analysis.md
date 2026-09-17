# Client voice — 15 Sep 2026 evening (~6:59–7:13 PM) — ISSUES (interpreted)

**Source:** WhatsApp PTTs + photos (Agent LIVE / Day empty / Admin lightbox dual-monitor).  
**Whisper `base` Urdu transcript is noisy** — interpretation combines audio + your written notes + screenshots.  
**Status:** Analysis only (no code changes yet). Planning = next prompt.

---

## What you locked (product order)

1. **First:** Web + Agent **stable** → 100% client confidence to use again.  
2. **Then:** Desktop Manager = **exact replica** of website (UI/UX, responsive, security) — no differences.  
3. Stop rushing features that break trust.

---

## Interpreted client issues (from voices)

| # | Time | Client ask / complaint (interpreted EN) |
|---|---|---|
| 1 | 6:59 | Projects / assignees / HR-related things **not showing**; cannot add/assign projects properly while they work. |
| 2 | 7:03 | After **Agent Sign In / session on**, app **closes / session ends** after some seconds — unstable. |
| 3 | 7:05 | Idle should trip after **~10s** no mouse/keyboard (was 30s); when idle, **all screens** should still be reflected in screenshots. |
| 4 | 7:06:30 | **Clicks/keys + day stats** (net work, break, idle) **not updating live** while working; Live/Day feels stuck; older PDF day showed clicks but live day does not. |
| 5 | 7:06:56 | On screenshot: play a **sound** so staff know a shot was taken; **no delete** for staff (OK / wanted). |
| 6 | 7:08 | Agent **LIVE for 5–7+ minutes** but **no new screenshots**; wants **random interval, max ~5 min** between shots. |
| 7 | 7:13 | **PDF** flow broken / not usable for them (View/download frustration after reinstall). |
| 8 | *(you + photos)* | **Admin** sees screenshots; **employee login** (web + desktop) shows **“No screenshots”** + 0.0h / 0 clicks for same evening. |
| 9 | *(photo 4)* | Dual-monitor capture **works** (both screens in one JPEG) when admin views lightbox. |

---

## Root-cause analysis (codebase — likely)

### A) Employee login: no screenshots (CRITICAL trust issue)

**Facts in code:**
- API allows self: `_assert_self_or_manager` → employee **can** list/view **own** shots.
- Day page loads `fetchDay` + `fetchShots` for URL `:id` (staff land on `/day/{ownId}`).
- Admin lightbox on same evening **has** shots → server **did** store captures.

**Most likely causes (ordered):**
1. **Identity mismatch:** Agent enrolled as employee A; person logged into web as employee B (or test account). Admin opens A from Live → sees shots; B’s “My Day” is empty.  
2. **Stale Day page:** Day page **does not auto-refresh**; employee opened Day before uploads landed and never refreshed (Admin later sees them).  
3. Less likely: date/TZ bug (both sides use Asia/Karachi day bounds — same API).

**Not a “hide screenshots from employees” feature** — code does not block staff from own shots.

### B) Agent session dies / “band” after seconds

**Likely:**
- Idle → `idle` state quickly (default **30s**); client perceives as “session closed”.  
- Sleep/gap auto Sign Out (`sleep_gap_seconds` / power hooks).  
- Or reinstall/enroll instability after rushed deploy (invalid token → re-enroll prompts).

### C) Shots missing for 5–7 min while LIVE

**Code:** screenshot timer ~**180s ±20%**; **skipped while `idle`**.  
So: if mouse quiet → idle → **no shots** even if UI still says LIVE-ish / working recently.  
Client wants **≤5 min random** and clearer feedback.

### D) Clicks / hours “not live”

**Day detail:** one-shot fetch — **no polling**. Watching Day while clicking will show **0** until refresh.  
**Live board:** polls/WS every ~5s but shows **deltas/status**, not full Day net-hours cards.  
Activity only posts after **server Sign In** (`_server_signed_in`). If Sign In flaky → clicks stay 0.

### E) Idle 10s + all-screens on idle

Config: `idle_seconds` default **30** (client asks **10**).  
Capture already multi-monitor; idle **skips** shots today — opposite of “idle pe bhi screenshots”.

### F) Screenshot sound / no delete

Sound = **missing feature**.  
Staff delete = already not offered (good).

### G) PDF broken for them

View PDF uses `fetchAuthedBlob` + modal (works in new Manager **if** rebuilt).  
Rush install of tiny/old Setup + Tauri URL bugs earlier → “PDF not working”.  
Staff: View OK, Download PDF **admin/manager only** (by design).

### H) Projects / assignees missing

Phase C workflow **not done**; existing Projects may be role-gated / incomplete vs client expectation.

### I) Dual monitors

**Working** when capture succeeds — keep; not the primary failure.

---

## What I understood clearly

- Client lost trust after rushed Agent + Manager reinstall testing.  
- Stabilize **capture → Sign In → activity → Day/Live visibility** before more product.  
- Desktop must later match web 1:1; **not** the priority until web+agent solid.  
- Admin-visible shots prove pipeline can work; employee empty Day is **visibility/identity/refresh** problem, not “screenshots never upload”.

## What is still fuzzy (need confirm in next prompt / ops)

- Exact **employee login** used in empty Day screenshots (name/code) vs **enrolled Agent** employee.  
- Whether they sat on **Day** without Refresh while Agent LIVE.  
- Exact Agent version on that PC (1.1.1 vs 1.1.2).  
- Whisper transcripts are **approximate** — if any voice meant something else, correct me before planning.

---

## Recommended fix themes (for NEXT prompt planning only — do not implement yet)

1. P0: Prove enroll ID = login ID; Day auto-refresh / “live updating” while signed in.  
2. P0: Agent session stability + clearer LIVE vs Idle vs Signed out.  
3. P0: Screenshot cadence (random ≤5 min) + optional sound; idle policy decision with client.  
4. P1: Live vs Day metrics honesty (what updates where).  
5. P1: PDF path smoke on web + Manager after known-good Setup.  
6. Later: Desktop = pixel/UX clone of web; Phase C projects.

**Fork chat:** OK for this analysis. For **planning + coding**, prefer a **fresh chat** with this file attached:  
`references/client-voice-2026-09-15-evening-issues.txt` + this analysis.
