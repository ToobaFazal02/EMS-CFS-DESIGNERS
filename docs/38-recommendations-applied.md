# Recommendations (applied) — top-1% pilot practice

| Topic | Market practice | Our call | Status |
|---|---|---|---|
| Google Sheets live sync | Avoid dual source of truth in ops tools | **Do not build** — keep Payments Excel *export* | Deferred permanently for v1 |
| Postgres day-1 | Overkill under ~50 seats | **SQLite** until scale pain | Correct for pilot |
| Role separation | Finance never on staff UI | **Admin full / Employee My Day + My Projects** | Implemented |
| Agent distribution | Bat first, MSI/Inno later | `INSTALL-AGENT.bat` + optional Inno script | OK |
| Favicon / brand chrome | Always on day-1 SaaS | CFS gold favicon | Done |

Do not add Sheets sync unless client insists *after* using in-app Payments for 2+ weeks.
