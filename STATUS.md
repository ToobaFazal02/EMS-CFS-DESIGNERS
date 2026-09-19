# Execution gate

| Key | Value |
|---|---|
| EXECUTION_APPROVED | **yes** |
| Current phase | **Desktop Manager + Agent → 100% first** — `docs/62-remaining-work-desktop-first.md` |
| Code allowed | STEP 1–3 (Desktop parity → Agent → Wave 4 ship). Staff UI is shared React (helps Desktop too). |
| Git branch | **`desktop+agent`** |
| Approved by | User 18 Sep — Desktop + Agent 100% then least-priority web/mobile |

## Locked product order

1. Desktop Manager (Setup.exe) **100%**
2. Employee Agent (zip) **100%**
3. Gate → ship
4. Remaining web polish — least priority
5. Mobile Phase D — last

## Branch `desktop+agent` — done so far

| Item | Status |
|---|---|
| Manager 0.1.5 + silent update + Tauri URL fixes | Done |
| Password eye (WebView2 native hide) | Done |
| Staff My dashboard + Lovable-inspired UX | Done |
| Staff monthly professional PDF (view/download) | Done |
| Month trend (capped vs work-day avg) + 100% bar fill | Done (19 Sep) |
| Assigned work scroll + hide finished/manual | Done (19 Sep) |
| Personal/daily PDF section page breaks | Done (19 Sep) |
| Live day clicks/keys + Dashboard EOD progress | Done (earlier) |
| Soft payment gate + Detailer/Engineer | Done (earlier) |

## Still remaining (honest)

| Priority | What | Notes |
|---|---|---|
| **P0** | Desktop Manager smoke in Tauri + Setup rebuild | `tauri:dev` / Actions Setup.exe; office reinstall |
| **P0** | Agent zip rebuild + 1-PC enroll/Sign In/shots test | Ship zip when green |
| **P0** | Wave 4 ship | Upload Setup + Agent to VPS `/downloads/`; version API |
| **P1** | Doc 61 happy/edge walk | Soft gate / D/E / initials |
| **P2** | Notify / audit bell | Not started — least priority |
| **P3** | Signed Tauri updater polish | After click-update proven |
| **P4** | Phase D admin mobile PWA | Last |

**Data:** Never wipe `/var/lib/ems/ems.db`.
