# Engineering quality (how we build — permanent)

This is the rule set so you do not have to repeat “be professional / test first / latest docs” every chat.

## What we are shipping

**One product, two clients:**

1. `apps/agent` — Windows desktop app (PySide6)
2. `apps/web` — manager dashboard (React + TS)
3. `apps/api` — FastAPI + PostgreSQL (the brain)

Not a browser extension. Not PHP-only. Not a marketing website.

## Research before code

For every library/framework used:

1. Open **current official docs** for the version in `requirements.txt` / `package.json`
2. Prefer patterns from those docs over blog posts older than 2 years
3. If unsure, write a 5-line spike — then delete it or keep it

## Feature gate (mandatory)

```
Plan → Implement → Test locally → Mark checklist → Only then next feature
```

Never: “UI done, logic later” as Done. Never stack 5 half modules.

### Module order (Phase 1)

1. Auth + employees + devices
2. Punches (sign in/out, break) + server time
3. Activity (clicks, key counts, window titles) + offline outbox
4. Screenshots upload + gallery
5. Live WebSocket board
6. End-of-day PDF/CSV
7. Installer + 2–3 real PC pilot

Each step has a pass/fail checklist in the section below. Fail = stay on that step.

## Test checklist template (copy per feature)

```
Feature:
Date:
- [ ] Happy path works on Windows 10/11
- [ ] Offline / API down path works (if agent)
- [ ] Empty / error states shown
- [ ] No secrets in logs
- [ ] Manager role cannot be bypassed
- [ ] Screenshot/disk size reasonable
- [ ] Demoed once to self with fake employee
Result: PASS / FAIL — notes:
```

## Subtle / polished bar

- Agent: tray icon, clear Recording/Break/Offline states, no focus-steal every minute
- Web: live board readable in 3 seconds; day timeline not a mess of cards
- PDF: TimesheetV2 parity (overview + 30-min graph + window table) then screenshots index
- Failures: human messages, not stack traces to users

## Security / ethics (non-negotiable)

- Disclosed monitoring; agent always shows recording state
- No typed keystroke capture
- No tracking after Sign Out
- CAD screenshots = confidential; on-prem default

## Market alignment (defaults)

See `docs/11-questions-explained-and-market-defaults.md`.  
We copy **professional defaults** from Hubstaff/DeskTime/Time Doctor shape — not their cloud brand. Client confirms or adjusts; we do not invent from thin air.
