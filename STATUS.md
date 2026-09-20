# Execution gate

| Key | Value |
|---|---|
| EXECUTION_APPROVED | **yes** |
| Current phase | Desktop ship (P0 ops) + P2–P4 code done on `desktop+agent` |
| Git branch | **`desktop+agent`** |

## Done on branch (20 Sep)

| Item | Status |
|---|---|
| Staff dashboard / PDF polish | Done |
| **P2** Notify / audit bell | Done — office bell + deposit/progress/override alerts |
| **P3** Updater polish | Done — MVP copy + `docs/64-signed-updater-ops.md` (signed plugin needs CI keys) |
| **P4** Admin mobile PWA | Done — manifest + SW + install (office only) |

## Still remaining (ops / QA)

| Priority | What |
|---|---|
| **P0** | GitHub Actions Build Manager Setup **0.1.6** + Agent zip + VPS `/downloads/` |
| **P1** | Doc 61 happy/edge walk |
| **P3 ops** | When ready: generate updater signing keys per doc 64 |

**Data:** Never wipe `/var/lib/ems/ems.db`.
