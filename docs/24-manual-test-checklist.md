# Manual test checklist — Phase 1 (mentor script)

Do these **in order**. One FAIL = stop, fix, re-test that step + previous linked steps.

## Setup (3 terminals) — YES, correct

| Terminal | Folder | Command | Expect |
|---|---|---|---|
| 1 API | `apps/api` | `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` | `Application startup complete` |
| 2 Web | `apps/web` | `npm run dev` | `http://localhost:5173` |
| 3 Agent | `apps/agent` | `python -m ems_agent` | Window with Sign In / LIVE badge |

Login: `admin@cfsdesigners.com` / `Admin123!`  
Swagger: http://127.0.0.1:8000/docs

---

## A — API health

1. Open http://127.0.0.1:8000/api/v1/health  
2. Expect: `{"ok":true,...}`

## B — Manager login (web)

1. Open http://localhost:5173  
2. Login with admin credentials  
3. Expect: Live board, name “CFS Admin”, Logout works  
4. FAIL if blank page / 401 loop

## C — Employees

1. Go to **Employees**  
2. See 101–104 + ADMIN  
3. Add employee code `105`, name `Test User` → Add  
4. Expect new row  
5. Click **Enroll PC** on 101  
6. Expect enroll code message (copy it)

## D — Agent enroll + Sign In (full loop)

1. Terminal 3: agent window open  
2. Paste enroll code → Enroll this PC  
3. Click **Sign In**  
4. Expect: red **LIVE** blink  
5. Open Notepad or browser, click/type a bit  
6. Web **Live** → Refresh within ~15s  
7. Expect: that employee **working** (or idle), window title, clicks/keys > 0  

## E — Break / Idle / Sign Out

1. Agent **Break In** → badge BREAK; live status break  
2. **Break Out** → LIVE again  
3. Leave PC idle ~3 min → status **idle** (optional long wait; can skip once)  
4. **Sign Out** → LIVE off; live board **offline**  
5. Confirm **new** screenshots stop after sign out  
6. Day detail still shows earlier session (history kept)

## F — Day detail + PDF

1. Live → **Day detail** for signed employee  
2. Pick today’s date  
3. Expect sessions table, clicks  
4. Download daily PDF → opens, readable (summary + sessions)

## G — Screenshots

1. While signed in, wait for interval (dev: temporarily set `screenshot_interval_seconds` to `60` in `config.json`)  
2. Day detail → screenshot thumbs appear  
3. FAIL if upload 400/413 or empty forever after wait

## H — Reports CSV

1. **Reports** → Daily CSV download for today  
2. Monthly CSV for current year/month  
3. Open in Excel — rows for employees

## I — Security spot-checks

1. Logout → `/` redirects to login  
2. Without token, Swagger `GET /live` → 401  
3. Device token must not open manager pages

## J — Regression after any code change

Re-run: B → D → F (minimum)

---

## Current known gaps vs new “top 1%” rules (honest)

| Gap | Status |
|---|---|
| Agent still partly one large UI file | Hardening next |
| bcrypt version warning on seed | Cosmetic; login works |
| Monthly PDF | CSV only in Phase 1 |
| Live “working” needs agent Sign In | Cards OFFLINE until agent runs — **expected** |
| Web font/layout | Bumped larger in this pass |

Pass criteria for client demo: A–F + H green on your laptop first, then 1 real employee PC.
