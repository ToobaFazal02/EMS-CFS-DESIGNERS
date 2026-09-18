# Execution gate

| Key | Value |
|---|---|
| EXECUTION_APPROVED | **yes** |
| Current phase | **Desktop-first remaining** — `docs/62-remaining-work-desktop-first.md` |
| Code allowed | STEP 1 Desktop Manager parity (Tauri) → STEP 2 Agent zip → STEP 3 Wave 4 ship |
| Approved by | User 18 Sep — Desktop app first, then remaining web |

## Honest status (18 Sep)

- Waves **0–3** (identity, Agent trust, Day/Live, Phase C + D/E + soft gate + dash progress + Live day totals): **code mostly in tree**
- Wave **4** Manager Setup + office Desktop receive: **not done** ← client-visible gap
- Recent work felt “web-only” because we tested in Chrome; Desktop = same React **after** new Setup.exe

## Done (production / recent code)

- Workforce: agent, live, day, PDF/Excel, multi-monitor, re-enroll
- Phase A helpers: Payments Actions, Tauri URL helpers, PDF modal (re-verify in Desktop)
- Phase E partial: version API + banners; Agent/Manager click-update path
- Wave 0–2: identity, Agent idle/shots/sound, Day auto-refresh
- Wave 3: projects codes/scopes/Detailer+Engineer/daily %; soft payment gate; Dashboard EOD %; Live today clicks/keys — see `docs/61`

## Next (locked order)

1. **STEP 1** — Desktop Manager parity checklist in Tauri/Setup (`docs/62`)
2. **STEP 2** — Agent zip rebuild + 1-PC test
3. **STEP 3** — Wave 4 ship (Setup + Agent + VPS downloads)
4. **STEP 4** — Remaining web (notify/audit bell, doc 61 edges, ops)
5. Phase E signed updater polish → **Phase D admin PWA last**

**Data:** Never wipe `/var/lib/ems/ems.db`.

## Auto-update honesty (client line)

- Banner: **Update available**
- Click: download + install in background + restart
- Server / hours / screenshots data: **safe**
- First install of a new build: still extract/Setup once per PC
