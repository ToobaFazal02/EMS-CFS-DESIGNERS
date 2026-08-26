# Final testing — step by step (Urdu + English)

Use this before you hand over to the client. Test on **your PC first**, then **second laptop** (optional but recommended).

---

## Part A — What runs where?

| Piece | File | Who uses it |
|---|---|---|
| **API (brain)** | `RUN-API.bat` | Always on — office server PC |
| **Web (Chrome)** | `RUN-WEB.bat` | Admin + staff login |
| **Agent (Windows app)** | `RUN-AGENT.bat` | Each employee CAD PC |
| **Auto check** | `AUDIT.bat` | You — must say **20/20 pass** |

---

## Part B — Your first test (same PC, 30 min)

### Step 1 — Start
1. Double-click **`RUN-API.bat`** — leave window open  
2. Browser: http://127.0.0.1:8000/api/v1/health → must show `phase5-complete`  
3. Double-click **`RUN-WEB.bat`**  
4. Chrome: http://127.0.0.1:5173 → **Ctrl+F5**

### Step 2 — Admin (CEO)
Login: `admin@cfsdesigners.com` / `Admin123!`

| # | Where in menu | What to check |
|---|---|---|
| 1 | **Live** | Employee cards (after agent Sign In) |
| 2 | **Employees** | Add staff: code + name + **email + password** → Enroll PC code |
| 3 | **Projects** | SAMPLE cards visible; Harbour blocked until Paid |
| 4 | **Payments** | Status **green PAID**, **red PENDING**; Download Excel — colors in file |
| 5 | **Reports** | Day PDF + monthly PDF open |
| 6 | **Account** | Change password (eye icon on fields); admin can change email |

### Step 3 — Staff (employee)
Logout → login: `waheed@cfsdesigners.com` / `Emp123!`

| # | Check |
|---|---|
| 1 | Menu shows only **My Day**, **My Projects**, **Account** |
| 2 | **No** Live, Payments, Reports |
| 3 | My Projects — no $ amounts, no payment comments |
| 4 | Account — **cannot** change email; **can** change password (eye icons) |
| 5 | Day page back link says **My Projects** not Live |

### Step 4 — Agent (workforce)
1. **`RUN-AGENT.bat`** on same PC  
2. Admin → Employees → **Enroll PC** → copy code  
3. Agent → paste code → Enroll  
4. **Sign In** → red **● LIVE** blinks (agent window + screen corner)  
5. Admin **Live** board shows LIVE  
6. **Sign Out** → LIVE stops  

### Step 5 — Automated
Run **`AUDIT.bat`** → **20 passed, 0 failed**

---

## Part C — Two laptops test (recommended before client)

**Why:** Proves Agent on another PC talks to API.

| Machine | Role |
|---|---|
| **Laptop A** | API + Web (server) — run `RUN-API.bat` + `RUN-WEB.bat` |
| **Laptop B** | Employee — install/copy `apps/agent` folder |

**On Laptop A:** Find LAN IP: `ipconfig` → e.g. `192.168.1.20`

**On Laptop B:** Edit `apps/agent/config.json`:
```json
"api_base": "http://192.168.1.20:8000"
```
Windows Firewall on A must allow port **8000** on private network.

Then: Enroll → Sign In on B → Live on A shows employee.

---

## Part D — Who manages logins?

| Task | Who | Where |
|---|---|---|
| Add new employee | **Admin** | Employees → code, name, email, temp password |
| Reset staff email/password | **Admin only** | Employees → **Set login** |
| Staff changes own password | **Employee** | Account → eye icon fields |
| Staff changes email | **No** — admin assigns email |
| Admin changes own email/password | **Admin** | Account |
| Enroll employee PC | **Admin** gives code; **employee** enters in Agent |

---

## Part E — What to give the client

1. Folder `ems-cfs-designers` (or ZIP)  
2. This file + `docs/visuals/` images  
3. Logins: admin + one demo staff  
4. Short note: external clients (Willie/Harbour) do **not** get this board — internal only (`docs/39-external-clients-portal.md`)  
5. Optional: 5‑min screen recording of Admin + Agent Sign In  

---

## Part F — Payment colors (web + Excel)

| Status | Color |
|---|---|
| **Paid** | Green |
| **Pending / Overdue / Unpaid** | Red |
| **Sent / Proforma / Info sent** | Amber |
| **Delayed days > 0** | Red (when not paid) |

---

## Quick “done?” checklist

- [ ] AUDIT 20/20  
- [ ] Admin sees everything; staff sees no $  
- [ ] Agent LIVE blink on Sign In  
- [ ] Payments Excel has colors + PROJECT column  
- [ ] Two-laptop test OR client office LAN planned  
- [ ] Admin changed password from default `Admin123!` before go-live  
