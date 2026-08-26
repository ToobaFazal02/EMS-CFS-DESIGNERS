# Non-functional requirements — CFS Designers platform

## Scale

| Now | Design for | Hard ceiling before rethink |
|---|---|---|
| 10–12 employees | 50 concurrent agents | 100 → Redis/queue + Postgres |

- Live WS: one manager fan-out; no Kafka in v1–3.
- Screenshots: ~1 shot / 5 min × office hours × staff; retention default **30 days**.
- Projects/payments: hundreds of clients/projects OK on single office server.

## Performance

- Agent CPU < 5% average with CAD foreground; capture off UI thread.
- Admin first paint < 2 s on LAN; reports responsive (no fake delays).
- Daily PDF with graph < 15 s.
- Kanban board: smooth with 50–100 cards (client-side filter).

## Reliability

- Agent autostart on Windows logon (INSTALL-AGENT.bat).
- Outbox survives crash; UUID punches; no duplicate sign-in without end session.
- API health: `/api/v1/health` includes `report_version`.
- Daily DB backup recommended on-prem.

## Availability

- Agent works **offline**; live board needs LAN/VPN/server.
- Target: agent 99% of signed-in time; API 99% office hours.

## Security / safety

See `05-security-privacy.md` and `.cursor/rules/01-security.mdc`.

| Bar | Requirement |
|---|---|
| Auth | JWT managers; device tokens for agents; hashed passwords |
| Money data | Finance/Admin only; API 403 for employees |
| Uploads | Image MIME allowlist, size cap, random names |
| Secrets | `.env` never committed |
| Monitoring | Visible LIVE; no keylogger; no stealth |
| CAD | On-prem screenshots by default |

## Maintainability

- Monorepo: `apps/agent`, `apps/api`, `apps/web`
- Docs index: `docs/INDEX.md`
- Minimum change; no drive-by refactors
- Typed Python 3.11 + TS; Alembic when Postgres migrates

## Observability

- Agent: last sync line
- Health endpoint for ops
- Future: screenshot view audit log

## Localization

- UI English; times **Asia/Karachi (PKT)**
- UTF-8 names

## Compatibility

- Windows 10/11 agent only
- Chrome/Edge for manager web
- Responsive: phone → ultrawide (full-bleed shell)

## UX quality

- Black + gold + white; finished empty/error states
- Red danger banners for validation/API errors (no raw `alert()` for product errors)
- Intuitive enough for non-technical finance/HR (client ask)

## Delivery

- Professional package: installer/scripts, runbooks, training — not WhatsApp zip of source as the product
- Demo link for client when hosted (LAN or VPS)
