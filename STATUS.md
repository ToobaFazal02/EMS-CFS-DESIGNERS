# Execution gate

| Key | Value |
|---|---|
| EXECUTION_APPROVED | **yes** |
| Current phase | Code complete on `desktop+agent` — **P0 ship/QA** left |
| Git branch | **`desktop+agent`** |

## Coverage map (20 Sep) — what’s done in code

| Area | Status | Docs |
|---|---|---|
| Desktop Manager (same React) | Done — need Setup rebuild for office | `48`, `62`, `66` |
| Employee Agent 1.1.5 | Done in source — zip ship pending | `62` |
| Staff dashboard / 7-day % / hide jobs | Done | — |
| Daily + monthly PDF (IEEE layout) | Done | — |
| **P2** Notify bell + soft chime | Done | `66` |
| **P3** Updater MVP + signed checklist | MVP done; signed keys = ops | `64` |
| **P4** Admin mobile PWA | Done (home-screen install, not store) | `65`, `66` |
| Unpaid project red highlight | Done | — |

## Still remaining (honest)

| Priority | What | Type |
|---|---|---|
| **P0** | Build Manager Setup **0.1.6** + Agent zip · upload `/downloads/` · office reinstall | **Ops** |
| **P0** | VPS: pull `desktop+agent`, API restart, web `npm run build` | **Ops** |
| **P1** | Doc **61** happy/edge walk (human QA) | **QA** |
| **P3 ops** | Optional: Tauri signing keys (`docs/64`) | **Ops later** |

**Data:** Never wipe `/var/lib/ems/ems.db`.

## How Admin gets the “mobile app”

1. Phone → `https://ems.cfsdesigners.com` → Admin login  
2. Install / Add to Home Screen (`docs/65`, `docs/66`)  
3. All **office** Manager features work; **Agent punch does not** (by design)
