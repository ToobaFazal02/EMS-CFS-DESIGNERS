# Phase 1 runbook

## What’s built

| Piece | Path | Status |
|---|---|---|
| API | `apps/api` | Auth, employees, enroll, punches, activity, screenshots, live WS, day view, daily PDF, daily/monthly CSV |
| Agent | `apps/agent` | PySide6, LIVE blink, Sign In/Break/Sign Out, clicks/keys/window, screenshots, idle, offline queue |
| Web | `apps/web` | Login, live board, employees+enroll, day detail+shots+PDF, reports CSV |

Theme: black / gold / white.

## Run (3 terminals)

**API**
```
cd D:\imp\ems-cfs-designers\apps\api
.\.venv\Scripts\activate
python -m app.seed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Web**
```
cd D:\imp\ems-cfs-designers\apps\web
npm run dev
```
Open http://127.0.0.1:5173 — `admin@cfsdesigners.com` / `Admin123!`

**Agent**
```
cd D:\imp\ems-cfs-designers\apps\agent
.\.venv\Scripts\activate
python -m ems_agent
```
Or double-click `Run-As-Administrator.bat`.

Enroll: Employees → Enroll PC → paste code in agent → within seconds Device shows **Enrolled** + **PC: hostname** (Windows PC name, e.g. Tooba — not a person).

Dev shortcut: seed writes `apps/api/ems_data/demo_device_token.txt` for Waheed (101).

## Verified smoke (20 Aug 2026)

- Health OK
- Admin login OK
- Live board lists 101–104
- Agent punch + activity OK
- Daily PDF generated (~2.5KB readable template)
