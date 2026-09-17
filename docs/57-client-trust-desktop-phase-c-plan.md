# PLAN — Client trust recovery + Desktop priority + Phase C (17 Sep 2026)

**Status:** Wave 0+1 done; **Wave 2 Day auto-refresh implemented** (17 Sep).  
**Test matrix:** `docs/58-wave0-1-test-matrix.md` · `docs/59-wave2-day-live-test-matrix.md`  
**Sources:** 15 Sep evening voices (esp. **6:59** projects, **7:13** desktop/PDF) + photos + prior Phase B/C locks.  
**Goal:** Client uses software again with confidence; Desktop Manager feels like the real product.

---

## Critical architecture truth (answers “web first or desktop first?”)

| Surface | What it is | How fixes ship |
|---|---|---|
| **Web** `ems.cfsdesigners.com` | React Manager UI | VPS `git pull` + `npm run build` |
| **Desktop Manager** | **Same React UI** inside Tauri | Same code + **new Setup.exe** install |
| **Employee Agent** | Separate PySide app | New Agent zip install |

**Recommendation (best way):**

1. **Do NOT** build two UIs. Fix **one React Manager** → web + desktop both get it.  
2. Treat **Desktop as the delivery priority** for the client (they live in Setup.exe), but **code work is shared**.  
3. **Agent** must be fixed in parallel for screenshots/clicks/session — Desktop Day is useless if Agent data is wrong.  
4. Order of **shipping to client PCs:** Agent zip → VPS web build → Manager Setup rebuild/upload → office reinstall Manager once.

So: **not “web then desktop” and not “desktop-only fork”.**  
**Shared Manager app first (Desktop-priority packaging) + Agent stability + Phase C in the same app.**

---

## What client demanded (locked interpretation)

### From 6:59 — Projects / assign (Phase C pressure)
- Why isn’t **add project / assign / the workflow he described** live yet?
- Staff should be able to work the queue (codes, assignees, etc.) — this was promised earlier; still missing vs his mental model.

### From 7:13 + your note — Desktop is priority
- Desktop Manager must work: **screenshots, PDF, projects add**, same as website.
- Later: Desktop = **exact replica** of web (no layout/gear/PDF gaps).

### From rest of evening — Trust blockers
- Agent session unstable / feels “closed”
- Screenshots timing (≤5 min random) + sound
- Idle ~10s policy
- Day/Live stats not updating while watching
- Admin sees shots; employee My Day empty
- Dual-monitor capture already OK when shots land

---

## Phased plan (do in this order)

```
WAVE 0  Ops truth          → enroll ID = login ID checklist (no code or tiny)
WAVE 1  Agent trust        → session + shots cadence + idle + sound
WAVE 2  Manager Day trust  → auto-refresh Day/shots + PDF path (shared React)
WAVE 3  Phase C projects   → codes / scopes / multi-assignee / daily % (shared React)
WAVE 4  Desktop ship       → Manager Setup rebuild + office install (= web UI)
WAVE 5  Desktop polish     → pixel/UX parity only if gaps remain after Wave 4
```

Mobile (Phase D) stays **last**. Silent auto-update polish stays **after** trust.

---

## WAVE 0 — Ops / identity (½ day, before heavy coding)

**Why:** Admin-sees-shots / employee-empty is often enroll ≠ login.

| # | Task | Done when |
|---|---|---|
| 0.1 | One-pager: Agent enroll code must be **that employee’s** code; login email must be **same person** | Client can retest without confusion |
| 0.2 | On Day header show **employee name + code** clearly | Staff know whose day they are viewing |
| 0.3 | Smoke: Admin Live → Day of enrolled staff → shots; that staff login → My Day → same shots after refresh | Identity proven |

---

## WAVE 1 — Agent stability (trust) — ~2–3 days

| # | Task | Client voice |
|---|---|---|
| 1.1 | Clear status copy: Signed in / Idle / Break / Signed out (no “session vanished” feel) | 7:03 |
| 1.2 | Idle default **10s** (config + new installs); document reinstall for old `config.json` | 7:05 |
| 1.3 | Screenshot policy: random interval **max 5 min** (tune base/jitter); decide with you: **idle pe shot skip vs capture** (client asked capture; old lock was skip-on-idle) | 7:05, 7:08 |
| 1.4 | Optional **short sound** on successful capture | 7:06:56 |
| 1.5 | Keep **no staff delete** of screenshots | 7:06:56 |
| 1.6 | Ship **Agent zip** + VPS version bump; **1 PC test** then office | — |

**Decision needed before 1.3 code:**  
Idle pe screenshots **ON** (client 7:05) vs **OFF** (current code + earlier hard-block mindset)?  
Default proposal for plan: **still require Sign In**; while signed-in, **capture even when idle** (so 5–7 min silent gaps stop); idle only changes Live status label.

---

## WAVE 2 — Manager Day / Live trust (shared React) — ~1–2 days

| # | Task | Client voice |
|---|---|---|
| 2.1 | Day page **auto-refresh** (poll 15–30s) while open: day stats + screenshots | 7:06:30, employee empty |
| 2.2 | Visible “Updated just now” / Refresh control always obvious | 7:06:30 |
| 2.3 | Confirm PDF View works for staff (own day); Download stays admin/manager | 7:13 |
| 2.4 | Live board: clarify what updates live (status/deltas) vs Day net hours | 7:06:30 |

Ships to **web immediately**; Desktop gets it on **next Setup** (Wave 4).

---

## WAVE 3 — Phase C Projects (shared React) — ~4–6 days — **6:59 answer**

Client asked why assign/add isn’t done → this wave **is** that work.

| # | Task | Notes |
|---|---|---|
| C1 | Client master: name, location, **initial**, invoice status (CRUD; **you type data**, no seed of real names) | |
| C2 | Auto code `Initial + DDMMYY` + editable override | e.g. `D110926` |
| C3 | Scope enum: Estimation / Detailing / Detailing+Engineering | CFS only |
| C4 | Staff can **create** project; **multi-assignee** | Locked earlier |
| C5 | **Daily %** progress per assignee + history | End-of-day style |
| C6 | Role-aware: staff see code/scope; full client name rules simple | |

**Existing** Projects kanban (single assignee / free-text scope) ≠ client’s 7:26 + 6:59 model — extend, don’t pretend it’s done.

**Done when:** Staff on Desktop/Web can add project with code + assignees; update %; admin audits trail.

---

## WAVE 4 — Desktop ship (client-priority delivery) — ~1 day ops + Actions build

| # | Task |
|---|---|
| 4.1 | After Waves 1–3 code on `main`: GitHub Actions **Build Manager Setup** |
| 4.2 | Artifact must be healthy; Release + VPS `wget` to `/var/www/ems/downloads/CFS-Designers-Manager-Setup.exe` |
| 4.3 | Office: uninstall/reinstall Manager once; smoke PDF, Day shots, Projects |
| 4.4 | Honest client line: Desktop = website inside a window; same login |

This is how **Desktop priority** is met without rewriting UI twice.

---

## WAVE 5 — Desktop polish (only remaining gaps) — ~1–3 days

Only if after Wave 4 something still differs (nav/gear mid-width, window chrome, update banner):

- Keep **one CSS/React** source  
- Rebuild Setup again  
- Target: **no visible difference** staff care about

---

## Explicitly NOT in this plan yet

- Phase D admin mobile  
- Full silent background install (Chrome-style)  
- Rewriting Desktop as a separate app  
- Hardcoding client names from sheets  

---

## Suggested calendar (effort bands)

| Wave | Focus | Rough time |
|---|---|---|
| 0 | Identity ops | 0.5 day |
| 1 | Agent | 2–3 days |
| 2 | Day/Live React | 1–2 days |
| 3 | Phase C | 4–6 days |
| 4 | Manager Setup ship | 1 day |
| 5 | Polish if needed | 1–3 days |

**Parallel:** Wave 1 (Agent) can overlap Wave 2 (React) if you want Desktop+data sooner; Wave 3 after Day/shots trusted enough that client doesn’t quit again.

---

## Answer to your direct question

| Question | Answer |
|---|---|
| Pehle web ya pehle desktop? | **Pehle shared Manager + Agent.** Desktop Setup is how client **receives** Manager; web deploy is the same UI. |
| Desktop priority? | **Yes for packaging & QA on Setup.exe** — but features coded once in React. |
| Phase C kab? | **Wave 3**, right after Day/Agent trust (Waves 0–2), because 6:59 is explicit “why isn’t this built?” |
| 100% client satisfaction path? | Agent reliable → employee sees own shots/hours → Projects workflow → ship Manager Setup → polish |

---

## Open decisions — LOCKED 17 Sep

1. **Idle screenshots:** YES — capture while signed-in idle (break/signed-out still skip).  
2. **Idle timeout:** **10 seconds** for new installs + policy merge.  
3. **Wave order:** 0+1 first, then Wave 2 Day poll, then Phase C.  
4. Started with **Wave 0+1** — see `docs/58-wave0-1-test-matrix.md`.

---

## Next step

After Wave 0+1 tests pass: **Wave 2** (Day auto-refresh) → Wave 3 Phase C → Wave 4 Manager Setup.  
No push / no DB wipe unless you ask.
