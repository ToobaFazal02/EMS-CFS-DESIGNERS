# Project management (recommended for this EMS)

Yes — ye project barha hoga (agent + API + web + reports + installers). Manage karo, warna WhatsApp pe sab kho jayega.

## Tool pick (one board only)

| Tool | Use when |
|---|---|
| **Notion** (free) | Best for you: docs + board + client pages in one place |
| **ClickUp** (free) | If you want stronger task statuses / due dates |
| **GitHub Projects** | If repo is on GitHub and you like issues |

**Recommendation:** Notion Free — 1 database “EMS CFS” with statuses.

## Board columns

`Backlog` → `Doing` → `Test` → `Blocked (client)` → `Done`

## Card fields (har task pe)

- Phase: 1 / 2.1 / 2.2  
- Area: Agent / API / Web / Reports / Deploy  
- Acceptance: 2–4 bullets (test steps)  
- Owner: you  

## Version rule

| Event | What to do |
|---|---|
| Phase slice done + tested | Update `STATUS.md` + `VERSION.md` |
| Client demo OK | Git tag `v0.x.y` |
| Bug after demo | Card in Doing, not a new phase |

## What NOT to use as the backlog

- WhatsApp (status only)  
- Random Cursor chats (use docs/ + Notion)  
- Spreadsheet of 80 vague rows  

## Client-facing board (optional share)

Columns: Requested / Planned / Building / Ready to test / Shipped  

Is se client dekhega progress without raw engineering noise.
