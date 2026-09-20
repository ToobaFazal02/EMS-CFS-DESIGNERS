# Execution gate

| Key | Value |
|---|---|
| EXECUTION_APPROVED | **yes** |
| Current phase | Code complete on `desktop+agent` — **P0 ship/QA** left |
| Git branch | **`desktop+agent`** |
| Manager / Web | **0.1.6** |
| Agent | **1.1.6** |

## Coverage map (20 Sep) — what’s done in code

| Area | Status | Docs / PDFs |
|---|---|---|
| Desktop Manager (same React) | Done — need Setup rebuild for office | `48`, `62`, `66` |
| Employee Agent 1.1.6 | Done in source — zip ship pending (Sign In label, Break states, no focus dashed border) | `62` |
| Past 7 days | Per-employee dropdown + **aligned** update counts | — |
| Payment badges | **Admin/Manager only** — staff never see Advance pending | — |
| Downloads nav | **Admin + HR only** | — |
| Notify bell + **Test sound** | Done | `66`, PDF 01 |
| Click→background update MVP | Done (not force-silent; preserves enroll/DB) | PDF **06** |
| Admin/HR PWA | Done | `65`, `66` |
| Ops PDF pack **v0.1.6** | Regenerated | `docs/pdfs/` |
| Master AI build prompt | PDF **07** | `docs/pdfs/07-…` |

## Still remaining (honest)

| Priority | What | Type |
|---|---|---|
| **P0** | Build Manager Setup **0.1.6** + Agent zip · upload `/downloads/` · office reinstall | **Ops** |
| **P0** | VPS: pull `desktop+agent`, API restart, web `npm run build` | **Ops** |
| **P1** | Human QA walk (PDF 01) | **QA** |
| **P3 ops** | Optional signed updater keys (`docs/64`) | **Ops later** |

**Data:** Never wipe `/var/lib/ems/ems.db`.

## How staff get apps

| App | Staff? | How |
|---|---|---|
| **Desktop App** (Setup.exe) | **Yes** | Login → **Downloads** → Desktop App |
| **Employee Agent** | **Yes** | Downloads → Agent zip + Admin enroll code |
| Phone / Chrome “Install app” | **No** | Admin/HR only |

Handoff steps: `docs/67-client-delivery-checklist.md` + PDF `08`.

