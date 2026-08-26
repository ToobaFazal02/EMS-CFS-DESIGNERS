# CFS Designers — Client handover & testing (simple)

## Visual maps (open these first)

| Image | Meaning |
|---|---|
| `docs/visuals/cfs-platform-explained.png` | Poora software kya hai (Agent + Web + API) |
| `docs/visuals/cfs-who-sees-what.png` | Admin/CEO vs Employee — kaun kya dekhe |
| `docs/visuals/cfs-test-and-deliver.png` | Testing + client ko dena — 6 steps |

---

## Logins (pilot)

| Who | Email | Password | Sees |
|---|---|---|---|
| **Admin / CEO** | `admin@cfsdesigners.com` | `Admin123!` | Live, Employees, Projects + $, Payments, Reports |
| **Employee** | `waheed@cfsdesigners.com` (101–104 same pattern) | `Emp123!` | **My Day** + **My Projects** only — **no money** |
| **Agent (PC)** | Enroll code from Employees page | — | Sign In/Out, LIVE, screenshots |

Emails: `rohail@` / `waseem@` / `waleed@cfsdesigners.com` — password `Emp123!`

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

1. Folder ZIP: `ems-cfs-designers` (bina `node_modules`/`.venv` optional — ya full with venvs)
2. Yeh doc + 3 images in `docs/visuals/`
3. Demo logins upar
4. Short video (optional): Admin flow 3 min + Agent Sign In 1 min
5. Office install: API hamesha on (office PC), web Chrome, Agent har CAD PC pe

**Client test:** unke office me API ek PC pe chalao; agents ka `api_base` us PC ka LAN IP (neeche).

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
