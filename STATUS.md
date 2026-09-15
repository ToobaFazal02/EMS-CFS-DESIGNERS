# Execution gate

| Key | Value |
|---|---|
| EXECUTION_APPROVED | **yes** |
| Current phase | **Phase E click→background update MVP** (doc 54) + Phase A live |
| Code allowed | Phases 1–5 + hardening + A + E MVP; B leave alone; C not started |
| Approved by | User 15 Sep 2026 — option 1 silent/background update today |

## Done (production / recent)

- Workforce: agent, live, day, PDF/Excel, idle 30s, multi-monitor, re-enroll
- Phase A: Payments sheet columns, Actions dropdown, Tauri URL helpers, PDF modal
- Phase E partial: version API + banners (1.1.1 / 0.1.1 era = download page only)
- Phase B audit 15 Sep: normal Sign In → screenshots OK — **do not change** unless bug

## In progress (15 Sep afternoon)

**Click → background update** — see `docs/54-phase-e-click-background-update.md`

| Still needed (ops) | Why |
|---|---|
| You push code | Agent `self_update`, Manager silent command, API 1.1.2 / 0.1.2 |
| `BUILD-EXE.bat` → upload Agent zip **1.1.2** | Employees get background update |
| GitHub Actions Manager Setup **0.1.2** → upload | Managers get silent `/S` update |
| VPS pull + web build + `ems-api` restart | Serves new version JSON + web banner |
| One office install of 1.1.2 / 0.1.2 | Unlocks future click-updates |

**Data:** Never wipe `/var/lib/ems/ems.db`. Updates replace local binaries only.

## Next after E MVP stable

1. Phase C — project codes / scopes / multi-assignee / daily %  
2. Optional: screenshot API Sign In hard-block  
3. Signed Tauri `plugin-updater`  
4. Phase D — admin PWA last  

## Auto-update honesty (client line)

- Banner: **Update available**  
- Click: download + install in background + restart  
- Server / hours / screenshots data: **safe**  
- First install of the new build: still extract/Setup once per PC  
