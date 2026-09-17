# Wave 0 + Wave 1 — implement notes + full test matrix

**Date:** 17 Sep 2026  
**Locked decisions:** Idle screenshots **YES** (after Sign In) · Idle **10s** · Wave 0+1 before Phase C  

**Industry note:** Hubstaff / Time Doctor normally **pause** screenshots when idle/timer paused. CFS client explicitly wants the opposite while signed in — we follow the client lock, not Hubstaff default.

**Sound note:** Capture click uses Windows `winsound.Beep` (no QtMultimedia / WAV bundle). Reliable in frozen PyInstaller Agent.

---

## What shipped in code

### Wave 0 — Identity

| Change | Where |
|---|---|
| Day API returns `employee_full_name` + `employee_code` | `schemas.py`, `manager.py` |
| Day header shows **Name (#code)** + Your day / Viewing… + Updated time | `DayPage.tsx` |
| Manual **Refresh** (Wave 2 auto-poll still later) | `DayPage.tsx` |
| Enroll dialog identity warning (enroll code = login person) | `EnrollCodeDialog.tsx` |

### Wave 1 — Agent trust

| Change | Where |
|---|---|
| `idle_seconds` default **10** | `storage.py`, `config.production.json`, `config.example.json` |
| Screenshots while **working OR idle** (still skip break / signed out) | `__main__.py` `_tick_screenshot` |
| Random interval **90–300s** (never > 5 min) | `__main__.py` `_arm_screenshot_timer` |
| Short beep on successful upload | `__main__.py` `_play_capture_sound` |
| Clearer status copy (Signed in / Idle / Break / Signed out) | `__main__.py` `on_status` |
| Agent + API version **1.1.4** | Sign-in sleep false-positive fix + capture WAV |

---

## WAVE 0 — How to test (all paths)

### Happy paths

1. **Admin identity smoke**
   - Staff → pick person A → **Enroll PC** → note code `#NNNN`.
   - On A’s PC: paste enroll → Agent shows `Enrolled as Name (#NNNN)`.
   - A signs in Agent → work 1–2 min → Admin Live → open **Day** for A.
   - Header must show **A’s name (#code)** (not “Day detail”).
   - Click **Refresh** after ~2 min → screenshots appear for A.

2. **Employee My Day same person**
   - A logs into Manager with **A’s** email (same person as enroll).
   - Nav **My Day** → header = A’s name + “Your day”.
   - **Refresh** → same shots Admin saw.

3. **Manager viewing staff**
   - Manager opens Live → Day of B → header = B’s name (#code) + “Viewing this employee’s day”.

### Weeping / unhappy paths

| Case | Steps | Expect |
|---|---|---|
| Enroll ≠ login | Enroll PC as employee A; log into web as employee B; open My Day | My Day is **B’s** day — empty or B’s data only. Admin Live shows shots under **A**. Header codes prove mismatch. Fix: re-enroll / correct login. |
| Wrong Day URL | Employee A opens `/day/{B’s id}` | API **403** / toast error — not another person’s shots. |
| Future date | Pick tomorrow on Day | Toast: future dates not allowed; no data. |
| Not logged in | Open Day URL with cleared token | Redirect login. |
| Bad employee id | Manager `/day/not-a-real-id` | 404 / error toast. |
| No Refresh after new shot | Stay on Day without Refresh | Old gallery until Refresh (auto-poll = Wave 2). |

### Wave 0 pass criteria

- [ ] Header always shows name + code when day loads  
- [ ] Admin and matching employee see **same** shots after Refresh  
- [ ] Mismatched enroll/login explained by different headers / empty My Day  
- [ ] Enroll dialog shows identity warning  

---

## WAVE 1 — How to test (all paths)

**Prerequisite:** Run Agent **1.1.3** (or local source). Old installs: reinstall zip **or** delete local `config.json` policy fields so `config.production.json` merges idle=10 / max=300. Policy merge overwrites idle/screenshot keys from shipped production config without wiping `device_token`.

### Happy paths

1. **Sign In → LIVE**
   - Enrolled PC → **Sign In**.
   - Badge **LIVE**; text: “Signed in — LIVE…”.
   - Connection: Online · tracking.
   - First shot within ~2.5s; short **beep** on successful upload.

2. **Idle 10s**
   - After Sign In, don’t touch mouse/keyboard ~10s.
   - Badge → **IDLE**; text mentions screenshots continue.
   - Live board shows idle for that person within ~15–30s (activity tick).

3. **Idle pe bhi screenshots**
   - Stay idle 6+ minutes (no input).
   - Expect **≥1 screenshot** in that window (random 90–300s).
   - Beep on each successful upload.
   - Day → Refresh → new thumbs while status was idle.

4. **Cadence ≤ 5 min**
   - Note timestamps of 4–5 consecutive shots while signed in.
   - Gap between any two ≤ **300s**; typically 1.5–5 min, not fixed clock.

5. **Break pauses shots**
   - **Start break** → badge BREAK; no new shots / no beep during break.
   - **End break** → LIVE again; shots resume.

6. **Sign Out stops**
   - Sign Out → OFF; no shots; text “Signed out…”.

7. **Dual monitor** (if applicable)
   - Idle + working captures still stitch both screens (existing behavior).

### Weeping / unhappy paths

| Case | Steps | Expect |
|---|---|---|
| Signed out idle PC | Never Sign In; leave PC idle | No screenshots uploaded; no beep. |
| Offline / API down | Unplug net after Sign In | Shot may queue (“Offline — shot queued”); no success beep until upload succeeds. After reconnect, sync drains queue. |
| Invalid / revoked token | Revoke device in admin; Agent still open | Invalid token UX / re-enroll prompt; no silent fake LIVE forever. |
| Sleep / lid close | Sign In → sleep PC > sleep_gap | Auto Sign Out / session ended path (existing). |
| Long idle auto Sign Out | Idle ≥ `auto_sign_out_idle_seconds` (default 30 min) | Session ends — not just IDLE. |
| Capture sound off | Set `"capture_sound": false` in config | Shots upload, **no** beep. |
| Old Agent 1.1.2 still installed | No new zip | Still old idle skip + 30s idle — client must update to 1.1.3. |
| Staff try delete shot | Day gallery | No delete control (unchanged). |

### Wave 1 pass criteria

- [ ] Idle flips by ~10s after last input  
- [ ] Idle does **not** stop screenshots while signed in  
- [ ] Gaps never exceed 5 minutes while signed in (working/idle)  
- [ ] Beep only on successful live upload  
- [ ] Break / Sign Out stop capture  
- [ ] Status copy never feels like “session vanished” when only idle  

---

## Deploy order (after your tests)

1. Push when you ask (not before).  
2. VPS: pull → restart `ems-api` (version 1.1.3) → `npm run build` web (Day header).  
3. Build Agent zip 1.1.3 → upload `/downloads/CFS-Agent-Install.zip`.  
4. One test PC install → full matrix above → then office.  
5. Manager Setup rebuild = later Wave 4 (same React once web is built).

---

## Explicitly NOT in this wave

- Day **auto-poll** every 15–30s → Wave 2  
- Phase C projects → Wave 3  
- Manager Setup.exe rebuild → Wave 4  
