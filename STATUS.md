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
| Manager **0.1.6** + silent update + `open_external_url` | Done (19 Sep) |
| Password eye (WebView2 native hide) | Done |
| Staff My dashboard + Lovable-inspired UX | Done |
| Staff monthly + daily PDFs — IEEE/business professional layout | Done (19 Sep) |
| Month trend + 100% bar + Assigned work scroll/hide | Done |
| Live day clicks/keys + Dashboard EOD progress | Done (earlier) |
| Soft payment gate + Detailer/Engineer | Done (earlier) |
| Agent source **1.1.5** synced with API | Done (code) |

## Still remaining (honest) — mostly ship / QA

| Priority | What | Notes |
|---|---|---|
| **P0** | GitHub Actions → Build Manager Setup **0.1.6** | Actions → “Build Manager Setup” → download artifact |
| **P0** | Rebuild Agent zip **1.1.5** + 1-PC enroll/Sign In/shots | `apps/agent` packaging |
| **P0** | Wave 4 ship | Upload Setup + Agent to VPS `/downloads/`; restart API; office reinstall |
| **P1** | Doc 61 happy/edge walk | Soft gate / D/E / initials |
| **P2** | Notify / audit bell | Least priority |
| **P3** | Signed Tauri updater polish | After click-update proven |
| **P4** | Phase D admin mobile PWA | Last |

**Data:** Never wipe `/var/lib/ems/ems.db`.

## PDF layout standard (19 Sep)

Applied IEEE/business technical-report conventions via `pdf_layout.py`:
- ≥18 mm margins, running header + page numbers
- Numbered sections; major sections start on a new page
- Table captions above tables; `repeatRows=1` so headers repeat across pages
- KeepTogether for short tables (no orphan session rows)
