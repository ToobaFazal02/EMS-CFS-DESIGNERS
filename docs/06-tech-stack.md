# Tech stack

## Decision (proposed — not coded until approval)

| Layer | Choice | Why |
|---|---|---|
| Windows agent | **Python 3.11 + PySide6** | Same language as TimesheetV2; real UI; pynput/mss/Pillow already proven for this job |
| Local queue | SQLite | Offline outbox |
| API | **FastAPI** | WebSockets for live; background tasks; one language with agent |
| DB | **PostgreSQL 16** | Concurrent writers from 12–50 agents; JSON for events if needed |
| Admin UI | **React + TS + Vite** | Live dashboard; not a PHP brochure site |
| PDF | WeasyPrint or reportlab + matplotlib | TimesheetV2 parity |
| Installer | PyInstaller or Briefcase + Inno Setup | One `.exe` / setup for staff PCs |
| Reverse proxy | Caddy or IIS ARR on office server | TLS on LAN |

## Rejected for v1

| Option | Why not |
|---|---|
| **Website only** | Browser cannot read other apps’ window titles, global clicks, or reliable background screenshots |
| **PHP + Laragon only** | Fine for CFS public site; poor desktop hooks; painful live WebSockets; still need a non-PHP agent |
| **Tkinter clone** | Fine for a demo; looks amateur next to a paid EMS; keep PySide6 |
| **Electron agent** | Heavy RAM next to AutoCAD/ScotSteel |
| **C# / WPF** | Excellent on Windows; extra language for this team unless client later wants native shop |
| **Hubstaff buy** | Monthly per seat; not their PDF/window-click format; CAD files on US cloud |

## PHP’s role

None in the recorder. Optional later: **CSV export** into a page on their existing PHP site. Not required for EMS itself.

## Hosting recommendation

**On-prem office mini-PC or existing server** (screenshots of client drawings). Cloud only if client accepts drawings leaving the building — **ask first**.
