# Execution gate

| Key | Value |
|---|---|
| EXECUTION_APPROVED | **yes** |
| Current phase | **Wave 3 Phase C** (doc 57/60) — C1–C5 in tree |
| Code allowed | Wave 3 C1–C5 local; test then C6 / Wave 4 |
| Approved by | User 17 Sep — Wave 0–2 then Phase C |

## Done (production / recent)

- Workforce: agent, live, day, PDF/Excel, multi-monitor, re-enroll
- Phase A: Payments sheet columns, Actions dropdown, Tauri URL helpers, PDF modal
- Phase E partial: version API + banners; Agent self-update click path
- **Wave 0+1:** Day identity + Agent idle 10s / idle shots / ≤5min random
- **Wave 2:** Day auto-refresh + Live hint (doc 59)
- **Wave 3 C1–C5 (local tree):** client initial/invoice; project code; scope enum; staff create + multi-assignee; daily % — matrix `docs/60-wave3-phase-c-test-matrix.md`

## In progress

**Test Wave 3 C1–C5** — matrix: `docs/60-wave3-phase-c-test-matrix.md`

| Still needed (ops) | Why |
|---|---|
| Restart API + rebuild web | New projects router + Projects UI |
| Happy + weeping C1–C5 | Before C6 / Desktop ship |
| No DB wipe | Columns/tables auto-patch / create_all |

**Data:** Never wipe `/var/lib/ems/ems.db`.

## Next after C1–C5 verified

1. C6 — role-aware client display polish  
2. Wave 4 — Manager Setup rebuild  
3. Phase D — admin PWA last  

## Auto-update honesty (client line)

- Banner: **Update available**  
- Click: download + install in background + restart  
- Server / hours / screenshots data: **safe**  
- First install of the new build: still extract/Setup once per PC  
