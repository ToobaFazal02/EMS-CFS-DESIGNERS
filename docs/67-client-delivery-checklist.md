# Client delivery — step-by-step (CFS EMS)

**Branch:** `desktop+agent` · Manager/Web **0.1.6** · Agent **1.1.6**  
**Never wipe** `/var/lib/ems/ems.db` or Agent `agent_data/`.

---

## What each person installs

| Who | Install | How | Not allowed |
|---|---|---|---|
| **Staff** | **Desktop App** (Setup.exe) | Downloads → Desktop App | Phone / Chrome “Install app” |
| **Staff** | **Employee Agent** (zip) | Downloads → Agent zip + enroll code | — |
| **Admin / Manager** | Desktop App (Setup.exe) | Downloads | — |
| **Admin / HR** | Phone home-screen PWA | Production HTTPS → Install banner | Staff must not get this |
| Everyone | Website browser | `https://ems.cfsdesigners.com` | Optional fallback |

**Remember:** Desktop App ≠ Agent.  
- Desktop = My dashboard / office UI (no browser chrome).  
- Agent = Sign In / Break / screenshots on the CAD PC.

---

## Phase A — You (developer) prepare binaries

### A1. Push latest code
```bat
cd D:\imp\ems-cfs-designers
git status
git push origin desktop+agent
```

### A2. Manager Setup.exe (GitHub — avoid local 16GB OOM)
1. GitHub → **Actions** → **Build Manager Setup** → **Run workflow** (branch `desktop+agent`)
2. Wait ~20–40 min
3. Download artifact `CFS-Designers-Manager-Setup`
4. Keep the `.exe` ready for VPS upload

### A3. Agent zip (local Windows PC)
```bat
cd D:\imp\ems-cfs-designers\apps\agent
BUILD-EXE.bat
```
Zip the folder `dist\CFS-Designers-Agent\` → name it **`CFS-Agent-Install.zip`**

### A4. Confirm versions
- Footer Desktop/Web: **v0.1.6**
- Agent window: **v1.1.6**
- API `GET /api/v1/agent/version` returns matching `manager_version` / `agent_version`

---

## Phase B — VPS / Hostinger (production)

```bash
cd /opt/ems-src   # your clone path
git fetch && git checkout desktop+agent && git pull

# Web UI
cd apps/web && npm ci && npm run build
cp -r dist/* /var/www/ems/

# API
# Confirm apps/api/.env on server:
#   EMS_ENV=production
#   AUTO_SEED_SAMPLES=false
#   SECRET_KEY=<long random>
systemctl restart ems-api
systemctl status ems-api --no-pager
```

Upload binaries:
```bash
# From your PC (example)
scp CFS-Designers-Manager-Setup.exe user@vps:/var/www/ems/downloads/
scp CFS-Agent-Install.zip user@vps:/var/www/ems/downloads/
```

Check files are **real** (Setup many MB, Agent zip ~50 MB) — not 1–2 KB HTML.

Smoke:
- https://ems.cfsdesigners.com → Admin login
- Downloads page shows both cards
- Staff login → **Downloads** visible; no phone Install banner

---

## Phase C — Hand to client (office day)

### C1. Admin PC
1. Open website → **Downloads** → Desktop Setup → install → login Admin  
2. Optional: phone → Install Admin/HR app  
3. Create enroll codes for each staff PC (Employees)

### C2. Each staff PC (same day checklist)
1. Browser login as staff → **Downloads**  
2. Download **Desktop App** → install → login → My dashboard works  
3. Download **Agent zip** → Extract All → `INSTALL-AGENT.bat`  
4. Paste enroll code → **Sign In** → button shows **Signed In**  
5. Confirm Admin **Live** sees them  

### C3. Tell client clearly
- Chrome “Open in app” / phone install = **Admin/HR only**  
- Staff desktop = **Setup.exe** from Downloads  
- Tracking = **Agent** (must stay running while working)  
- Later updates: banner → click Update (no DB wipe)

---

## Phase D — Final acceptance (30–45 min)

| # | Test | Pass? |
|---|---|---|
| 1 | Staff Desktop login → My dashboard | ☐ |
| 2 | Staff Agent Sign In → Signed In label + Live | ☐ |
| 3 | Break In golden / Break Out dim (and reverse) | ☐ |
| 4 | Staff My % today → Admin Past 7 days dropdown | ☐ |
| 5 | Staff sees **no** Advance pending | ☐ |
| 6 | Staff sees **no** phone Install / minimal Chrome PWA | ☐ |
| 7 | Admin notify sound on soft-gate / progress | ☐ |
| 8 | Daily PDF opens clean | ☐ |
| 9 | `.env` production, no sample seed | ☐ |

---

## If something fails

| Problem | Fix |
|---|---|
| Download tiny / wrong file | Re-upload real exe/zip to `/downloads/` |
| GitHub Actions fail | Re-run workflow; check Actions log; branch `desktop+agent` |
| Agent enroll fail | New code from Admin; check API online |
| No Live | Agent Signed In + API up |
| Staff still see Install app | Hard refresh; SW unregistered; no manifest for staff |

Full PDFs: `docs/pdfs/` (deploy, QA, auto-update, break/fix).
