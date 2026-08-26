# Version & phase tracking

| Field | Value |
|---|---|
| App | CFS Designers |
| Current phase | **Phase 5 complete (pilot ready)** |
| Report build | `phase5-complete` (see `/api/v1/health`) |
| API | FastAPI + SQLite |
| DB file | `apps/api/ems_data/ems.db` |
| Screenshots / PDFs | `apps/api/ems_data/` |

## How we version

1. **STATUS.md** — current phase + execution gate (source of truth)
2. **docs/27-phase2-plan.md** + **docs/35-final-dev-complete.md**
3. Git tags when you push: `v0.5.0-phase5`
4. After API restart, hard-refresh web (`Ctrl+Shift+R`)

## Health check

Open: http://127.0.0.1:8000/api/v1/health  

Must show: `"report_version": "phase5-complete"`  
If missing → old API still running. Kill port 8000 and run `RUN-API.bat` again.
