# CFS Designers — Client handover & testing (simple)

**Live (31 Aug 2026):** https://ems.cfsdesigners.com  
**Agent zip:** operator Desktop `CFS-Agent-Install.zip`  
**This week (client voice):** enroll employees first — `docs/42-client-voice-2026-08-30-plan.md`

Do **not** send sample passwords (`Admin123!` / `Emp123!`) as live logins. Admin password is whatever was set on Account. Staff: unique temp passwords on Employees → Add staff.

---

## Visual maps (open these first)

| Image | Meaning |
|---|---|
| `docs/visuals/cfs-platform-explained.png` | Poora software kya hai (Agent + Web + API) |
| `docs/visuals/cfs-who-sees-what.png` | Admin/CEO vs Employee — kaun kya dekhe |
| `docs/visuals/cfs-test-and-deliver.png` | Testing + client ko dena — 6 steps |

---

## Logins (local demo / seed only — not live)

| Who | Email | Password | Sees |
|---|---|---|---|
| **Admin / CEO** | `admin@cfsdesigners.com` | local seed `Admin123!` only | Live, Employees, Projects + $, Payments, Reports |
| **Employee** | `waheed@cfsdesigners.com` (101–104 same pattern) | local seed `Emp123!` only | **My Day** + **My Projects** — **no money** |
| **Agent (PC)** | Enroll code from Employees page | — | Sign In/Out, LIVE, screenshots |

Live staff emails: `firstname@cfsdesigners.com` with **unique** temp passwords. Agent = enroll once, not daily email login.

---

## Aap pehle kaise test karein (Windows)

1. `RUN-API.bat` → browser: http://127.0.0.1:8000/api/v1/health → `phase5-complete`
2. Optional: `AUDIT.bat` → 20/20
3. `RUN-WEB.bat` → http://127.0.0.1:5173 → Ctrl+F5
4. Admin login → Live / Projects SAMPLE / Payments SAMPLE / Reports PDF
5. Logout → employee login → Payments menu **nahi** hona chahiye
6. `RUN-AGENT.bat` → Enroll → Sign In → Live board pe LIVE

---

## Client ko kya dena hai

1. **CFS-Agent-Install.zip** (exe pack — no Python)
2. Live URL + Employees enroll codes (one per PC)
3. Short **screen recording**: install → enroll → Sign In (client asked 31 Aug)
4. Yeh doc + images in `docs/visuals/`
5. External clients (Willie/Harbour) do **not** get this board — internal only (`docs/39-external-clients-portal.md`)

---

## Simple answers (jo confuse kar rahe the)

### Google Sheets sync?
**Recommend: NO for now.** Software Excel *replace* karta hai. Sheet sync = do jagah truth → bugs. Baad me sirf export Excel (already hai).

### Postgres kyun nahi?
**Pilot = SQLite (sahi).** Startups pehle SQLite/file DB se ship karti hain. Postgres jab 50+ users / multi-office ho. Abhi change = risk, zero benefit.

### LAN IP kya hai?
Abhi Agent `127.0.0.1` = sirf *usi* PC pe API. Dusre employee PC se connect karne ke liye office server ka IP chahiye, e.g. `http://192.168.1.20:8000` in agent `config.json` → `api_base`.

### Inno Setup kya hai?
Optional `.exe` installer. Abhi `INSTALL-AGENT.bat` kaafi hai. Inno tab lagao jab client ko single Setup.exe chahiye.

### Windows pe chalega?
Haan — Agent = Windows PySide; Web = Chrome; API = Windows. Ye design Windows office ke liye hai.

---

## Professional recommendation (applied)

| Topic | Decision |
|---|---|
| Sheets sync | **Skip** — Excel export enough |
| Postgres | **Later** — SQLite pilot |
| Role split | **Done now** — Admin full / Employee no $ |
| Favicon | **Done** — CFS gold on black |
| Inno exe | Script ready; bat install for pilot |
| LAN | Document for office install day |
