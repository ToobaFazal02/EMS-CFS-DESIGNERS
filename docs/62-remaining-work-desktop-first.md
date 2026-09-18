# Remaining work — Desktop-first (LOCKED 18 Sep 2026)

**Status:** Plan + execution order updated. **Next coding = Desktop Manager + Agent ship / parity**, not more Chrome-only feature work.  
**Supersedes for “what next”:** older “next = more web Phase C polish” notes in `STATUS.md` (pre-18 Sep).  
**Does not delete:** docs 53 / 57 / 58–61 — those stay historical + test matrices.

---

## Honest answer: were we on the wrong flow?

**Partly yes for client delivery — not for architecture.**

| Truth | Detail |
|---|---|
| Client priority | **Desktop Manager (Setup.exe)** + **Employee Agent** feel like “the product” |
| What we actually coded lately | Shared **React Manager** (browser) + API — Projects, payments soft-gate, Live day totals, Dashboard EOD % |
| Gap | **Wave 4 never shipped** — office Desktop Setup still may be an **older** build, so client does not *see* the new features in Desktop |
| Architecture | Desktop Manager = **same React inside Tauri**. Features are not “web-only” — they land on Desktop **only after Setup rebuild + install** |

So: coding in React was correct (one UI). **Shipping / QA priority drifted to browser.** From now: **Desktop-first** = fix Tauri gaps → smoke every feature in Manager Setup → rebuild/upload → then remaining web polish.

```
WRONG (feel):  endless Chrome features → Desktop “later”
RIGHT (now):   Desktop parity QA + Setup ship → then remaining web/ops
```

---

## Waves / phases — complete or not? (audit 18 Sep)

### Doc 57 waves (trust + Phase C)

| Wave | Focus | Code in tree? | Client / office received? | Verdict |
|---|---|---|---|---|
| **0** Identity (Day name/code, enroll = login) | Yes | Matrix `58` | Ops retest may still be needed | **Code done** |
| **1** Agent trust (idle 10s, idle shots, ≤5 min, sound) | Yes (`Agent 1.1.5` in source) | New zip may not be on every PC | **Code done** — **ship pending** |
| **2** Day auto-refresh + Live hint | Yes | Matrix `59` | Needs Desktop/Web with current build | **Code done** |
| **3** Phase C (C1–C5) + D/E roles + soft gate + dash progress + Live day clicks/keys | Yes | Matrix `60` + `61` | **Not on Desktop until Wave 4 Setup** | **Code mostly done** — verify `61`, then ship |
| **4** Manager Setup rebuild + office install | **No / overdue** | — | Client Desktop lagging web | **NEXT — DO THIS** |
| **5** Desktop polish if gaps after 4 | Not started | — | Only if Setup still differs | **After Wave 4 smoke** |

### Doc 53 phases (A → E → D)

| Phase | Goal | Status |
|---|---|---|
| **A** Desktop+Web parity helpers (`resolveUrl`, PDF modal, Reports/Payments blobs) | **Mostly in code** — must **re-verify inside Tauri**, not only Chrome |
| **B** Agent Sign In / shots reliability | Audited leave-as-is + Wave 1 improvements; zip ship pending |
| **C** Projects codes / % / assignees | **In code** (Wave 3); Desktop gets it via Wave 4 |
| **E** Click → background update MVP | In code (Agent + Manager); production binaries / office install still ops |
| **D** Admin-only mobile PWA | **Last — do not start** until Desktop ship + remaining web below are stable |

**Bottom line:** Waves **0–3 code ≈ complete**. Wave **4 Desktop ship = incomplete** (this is the client-visible miss). Remaining product polish (notify, etc.) comes **after** Desktop parity.

---

## Locked order from today

```
STEP 1  Desktop Manager parity checklist (Tauri)     ← NOW
STEP 2  Employee Agent zip rebuild + 1-PC test
STEP 3  Wave 4 ship (Setup.exe + Agent zip + VPS)
STEP 4  Remaining web / product polish
STEP 5  Phase E signed updater polish (optional)
STEP 6  Phase D admin PWA — LAST
```

**Hard rules**

1. No DB wipe (`/var/lib/ems/ems.db`).  
2. Same React for web + Desktop — fix once.  
3. No push / force-push unless you ask.  
4. Do **not** start Phase D or sales-demo ads until Steps 1–4 are green.  
5. Prefer testing in **Manager Desktop** (`tauri:dev` or installed Setup) over Chrome-only.

---

## STEP 1 — Desktop Manager: same-as-web feature plan

**Goal:** Admin/manager can run a full workday from **Setup.exe only** — Login → Dashboard → Live → Day → PDF → Projects → Payments → Reports → Downloads → Update banner — **without Chrome**.

### 1A — Version / build hygiene (before feature QA)

| # | Task | Done when |
|---|---|---|
| D0.1 | Sync versions: `version.ts` / `tauri.conf.json` / `Cargo.toml` / `LATEST_MANAGER_VERSION` all **0.1.4** (or next bump **0.1.5** if shipping after more fixes) | No mismatch |
| D0.2 | `npm run tauri:dev` against local or prod API | App opens, login works |
| D0.3 | Prefer GitHub Actions for Setup if local 16GB OOM (`docs/52`) | Healthy artifact |

### 1B — Parity matrix (must match web)

Test **inside Desktop Manager**. Check = works like Chrome.

| Area | What to verify | Known risk |
|---|---|---|
| Login / roles | Admin, HR, employee, demo | Token + CORS (`tauri://` / `https://tauri.localhost`) |
| Dashboard | Presence, hours, **End-of-day project progress**, roster | New panel must show in Desktop |
| Live | Status, **Today clicks/keys**, recent Δ, thumbs, Day detail link | WS may fall back to poll — OK if poll ≤5s |
| Day | Auto-refresh, shots gallery, net hours, View PDF | Blob / modal (not `window.open`) |
| Projects | Create, Detailer+Engineer, scope, code, daily %, soft gate badges | Same as web |
| Payments | Sheet columns, PDF view/download, XLSX | `fetchAuthedBlob` + modal |
| Reports | Daily/monthly PDF/CSV/Excel download | Relative URL bug if any path skipped `resolveUrl` |
| Expenses | Receipt view/download | Blob helpers |
| Shares | Partner shares (admin) | Role gate |
| Downloads | Absolute prod URLs for Setup + Agent zip | Must not hit `tauri://` dead paths |
| Update banner | Shows when API `manager_version` > local; Update → silent path | Phase E MVP |
| Theme / gear / nav | No clipped mid-width chrome that blocks work | Wave 5 if leftover |

### 1C — Fix-only list (if smoke fails)

Do **not** invent new product features here — only parity bugs:

1. Any remaining relative `/api/...` fetch without `resolveUrl` / `fetchAuthedBlob`.  
2. PDF/XLSX view that still uses fragile `window.open(blob)`.  
3. Live WS URL wrong host in packaged app (`resolveWsUrl`).  
4. Downloads page pointing at bundled empty paths.  
5. CORS on VPS missing Tauri origins (doc 48).  
6. Screenshot thumbs 401 / blank in Desktop only.

**Done when:** Checklist 1B all green on Desktop; Chrome still green (regression).

---

## STEP 2 — Employee Agent (desktop staff app)

Not the Manager UI — separate PySide app. Client trust depends on this.

| # | Task | Done when |
|---|---|---|
| A1 | Confirm source `AGENT_VERSION` = API `LATEST_AGENT_VERSION` (**1.1.5**) | Match |
| A2 | Rebuild `CFS-Agent-Install.zip` (`BUILD-AGENT` / packaging script) | Zip runs on clean extract |
| A3 | 1 test PC: enroll → Sign In → idle 10s → shots ≤5 min + sound → clicks/keys → Break → Sign Out | Matches Live + Day |
| A4 | Update banner path (if older agent installed) | Click update or reinstall once |
| A5 | Dual-monitor capture still OK | Full virtual desktop in shot |

**Done when:** One real staff day trustworthy on Agent + visible on Manager Desktop Day/Live.

---

## STEP 3 — Wave 4 ship (client receives Desktop)

| # | Task |
|---|---|
| S1 | Push only when you ask; VPS `git pull` + web `npm run build` + `systemctl restart ems-api` |
| S2 | Upload **Manager Setup** + **Agent zip** to `/var/www/ems/downloads/` |
| S3 | Confirm `GET /api/v1/agent/version` versions + URLs |
| S4 | Office: uninstall/reinstall Manager once; Agent extract/install once |
| S5 | Smoke: Desktop Day shots + Projects add/% + PDF View + Live today totals |
| S6 | Client line: Desktop = website in a window; same login; data safe |

---

## STEP 4 — Remaining work AFTER Desktop (web + product)

Only start when Steps 1–3 are green (or you explicitly override).

| Pri | Item | Notes |
|---|---|---|
| R1 | Doc **61** full happy/edge walk | Soft gate + D/E roles + initials privacy |
| R2 | Notify / audit bell (admin) | Deposit unpaid phase advance + useful office alerts — **not started** |
| R3 | Any leftover Projects UX from client voice | Only if Desktop smoke finds gaps vs 6:59 / 7:26 |
| R4 | Ops: enroll video / one-pager | Not code |
| R5 | Sales white-label demo | Backlog — after CFS ops stable (`docs/41`) |

*(Conversation backlog labels like “notify bell / ship” land here as R2 + Step 3.)*

---

## STEP 5–6 — Later

| Item | When |
|---|---|
| Signed `@tauri-apps/plugin-updater` | After click→background MVP proven in office |
| Phase D admin PWA | **Last** — admin glance only; never employee Sign In on phone |
| Wave 5 pixel polish | Only if Setup still feels “not like web” after Wave 4 |

---

## What we will NOT do in the Desktop-first block

- Rewrite Desktop as a second UI framework  
- Chrome-only feature sprints while Setup is stale  
- Phase D mobile  
- DB wipe / reseed production  
- Hardcoding real client names  

---

## How coding relates to “Desktop complete”

| Change type | Where you edit | How Desktop gets it |
|---|---|---|
| Manager UI/API | `apps/web` + `apps/api` | Next **Setup.exe** (and VPS web build) |
| Tauri shell / silent update | `apps/web/src-tauri` | New Setup |
| Staff tracker | `apps/agent` | New **Agent zip** |

**Rule:** After any Manager feature, mark it **unchecked on Desktop** until Step 1B passes in Tauri/Setup.

---

## Suggested next chat prompt

```
Read STATUS.md and docs/62-remaining-work-desktop-first.md.
Start STEP 1 only: Desktop Manager parity (Tauri smoke + fix gaps).
Do not start Phase D or extra web features.
No push / no DB wipe.
```

---

## Related docs

| Doc | Role |
|---|---|
| `57-client-trust-desktop-phase-c-plan.md` | Original wave order |
| `53-finalize-desktop-web-then-mobile-plan.md` | Phase A–D + E |
| `48-phase1-tauri-desktop.md` | Tauri CORS / build |
| `52-manager-build-16gb-ram.md` | Actions build if OOM |
| `54` / `55` | Update MVP + local test |
| `58`–`61` | Wave test matrices |
| `../STATUS.md` | Execution gate (points here) |
