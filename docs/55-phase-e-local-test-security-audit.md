# Phase E — Local Test + Security Audit (BEFORE production)

**Critical:** Do **not** upload Agent 1.1.2 / Manager 0.1.2 to production until local test complete.

---

## Security audit summary

| Layer | Risk | Mitigation | Status |
|---|---|---|
| Agent `self_update.py` download | MITM / malicious zip | URL host allowlist (`ems.cfsdesigners.com`), HTTPS only | ✅ Safe |
| Agent PowerShell `robocopy` | Code injection via path | PowerShell single-quote escape (`'` → `''`) | ✅ Safe |
| Agent file replace | Lose enroll / data | Explicit `/XF config.json`, never delete `agent_data/` | ✅ Safe |
| Manager Tauri command | Arbitrary download | Host allowlist + HTTPS check in Rust | ✅ Safe |
| Manager NSIS `/S` | Silent fail on admin-required install | Uses `currentUser` mode (no UAC) | ⚠️ **Test needed** |
| API version endpoint | Public scraping | By design public; no secrets exposed | ✅ Safe |
| Network drop mid-download | Partial zip / exe | `httpx` raises on incomplete; PowerShell verify file exists | ✅ Safe |
| Corrupt download | Bad zip / Setup.exe | Extract fails → user sees error + Retry button | ✅ Safe |
| DB / server data wipe | **Critical** | Code **never** touches `/var/lib/ems/ems.db` or API DB | ✅ Safe |
| Office-wide rollback | Bad update shipped | **Test local first**; VPS can revert `git` + old zip | ✅ Plan exists |

**Verdict:** No critical security holes. **One operational test needed:** Manager silent install without admin (currentUser NSIS).

---

## Local test plan (step-by-step — DO THIS FIRST)

### Setup (one-time)

1. **Fake update server** (local API mock or edit `api_base` temporarily):
   - Agent: change `api_base` in a test `config.json` to `http://localhost:9999` OR  
   - Edit `apps/agent/ems_agent/__main__.py` line `AGENT_PACKAGE_URL` to a local test zip path (then revert before real build)
   - Manager: same for test

2. **Host test packages locally:**
   ```powershell
   # Serve current Agent build as "new" version
   cd D:\imp\ems-cfs-designers\apps\agent\dist\CFS-Designers-Agent
   # Zip this folder → test-agent-update.zip
   # Put on local HTTP server (Python: `python -m http.server 8080` in a folder with the zip)
   ```

3. **Mock version endpoint** (test API response):
   ```python
   # test_update_server.py
   from flask import Flask, jsonify
   app = Flask(__name__)
   @app.route('/api/v1/agent/version')
   def version():
       return jsonify({
           "agent_version": "1.1.3",  # Higher than current
           "agent_package_url": "http://localhost:8080/test-agent-update.zip",
           "download_url": "http://localhost:8080",
           "manager_version": "0.1.3",
           "manager_download_url": "http://localhost:8080/test-manager-setup.exe"
       })
   if __name__ == '__main__':
       app.run(port=9999)
   ```

### Test 1: Agent background update (safe local)

| Step | Action | Expected | If fail |
|---|---|---|---|
| 1 | Install current Agent **1.1.2** (from `BUILD-EXE.bat` output) | Runs, shows enroll | |
| 2 | Edit `config.json` → `"api_base": "http://localhost:9999"` | | |
| 3 | Restart Agent | Banner shows "Update available v1.1.3" | Check mock server running |
| 4 | Click **Update to v1.1.3** | "Downloading…" → "Restarting…" | Check network / zip exists |
| 5 | Agent exits and returns | New version? (Check About if you add it, or test file timestamp) | PowerShell script failed — check `%TEMP%\cfs-agent-apply-update.ps1` |
| 6 | Open `config.json` | `device_token` still present | **CRITICAL FAIL** — robocopy broke |
| 7 | Check `agent_data\outbox.sqlite` | File exists, not empty if had queue | **CRITICAL FAIL** — robocopy deleted data |

**Pass criteria:** Agent restarts, enroll stays, banner gone (or "already latest" if version same).

### Test 2: Manager silent update (Tauri desktop)

| Step | Action | Expected | If fail |
|---|---|---|---|
| 1 | Build Manager **0.1.2** locally: `npm run tauri:dev` OR full `tauri:build` | Opens desktop app | Check Rust/Node deps |
| 2 | Point to mock server (edit API base in dev or use production API with fake `manager_version`) | Banner shows update | |
| 3 | Click **Update** | "Downloading…" → app exits | Rust command fail — check console logs |
| 4 | Wait ~30s | New Manager window opens | Check `%TEMP%` for `.exe` / `.ps1` errors |
| 5 | Check Manager version (if UI shows it) OR `tauri.conf.json` timestamp | Newer | Setup silent fail — may need `/NCRC` or check NSIS logs |

**Pass criteria:** Manager exits, Setup installs silently, app relaunches.

### Test 3: Production-like (safe staging)

Before uploading to production `/var/www/ems/downloads/`:

1. **Staging upload** (separate folder on VPS or local test VM):
   - Upload Agent zip **1.1.2** to `https://ems.cfsdesigners.com/downloads-staging/CFS-Agent-Install.zip`
   - Upload Manager Setup to `downloads-staging/CFS-Designers-Manager-Setup.exe`
   - Edit API **test instance** to return those staging URLs

2. Test from **one office PC** (not all):
   - Install Agent 1.1.2 from staging
   - Enroll, Sign In, take 1 screenshot
   - Trigger update (bump API version to 1.1.3 test)
   - Verify enroll stays, screenshots still visible in Day page

3. If **pass** → move staging zips to production `downloads/`, update API to 1.1.2 real.

---

## Deploy checklist (after local test PASS)

**DO NOT skip local test.**

### Pre-deploy

- [ ] Local Agent update test: enroll survives ✅
- [ ] Local Manager update test: silent install works ✅
- [ ] `config.json` + `agent_data/` untouched after update ✅
- [ ] Mock higher version → lower version = no phantom updates ✅
- [ ] Code review: no hardcoded secrets, no DB writes in update paths ✅

### Build

```powershell
# Agent
cd D:\imp\ems-cfs-designers\apps\agent
.\BUILD-EXE.bat
# Verify: dist\CFS-Designers-Agent\CFS-Designers-Agent.exe exists
# Zip entire folder → CFS-Agent-Install.zip (~50MB)

# Manager (GitHub Actions preferred — 16GB RAM issue)
# OR local if RAM sufficient:
cd D:\imp\ems-cfs-designers\apps\web
npm run tauri:build
# Output: src-tauri\target\release\bundle\nsis\*.exe
```

### Upload

```bash
# VPS (after you push code)
scp CFS-Agent-Install.zip root@VPS:/var/www/ems/downloads/
scp CFS-Designers-Manager-Setup.exe root@VPS:/var/www/ems/downloads/

# Verify URLs return real files (not HTML):
curl -I https://ems.cfsdesigners.com/downloads/CFS-Agent-Install.zip
# Expect: Content-Type: application/zip, ~50MB
```

### API deploy

```bash
ssh root@VPS
cd /opt/ems-src
git checkout -- apps/web/tsconfig.tsbuildinfo 2>/dev/null || true
git pull
cd apps/web
rm -f tsconfig.tsbuildinfo && rm -rf dist
npm run build
cp -r dist/* /var/www/ems/
systemctl restart ems-api

# Verify version endpoint:
curl -s https://ems.cfsdesigners.com/api/v1/agent/version | jq
# Expect: agent_version: "1.1.2", agent_package_url, manager_version: "0.1.2"
```

### Office rollout (staged)

| Phase | Who | Why |
|---|---|---|
| 1. Test PC (1 employee) | Faisal PC or one trusted staff | Catch any enroll/network issue before full office |
| 2. Managers (2-3) | Admin PCs | Manager desktop update test |
| 3. Full office | All staff | After 24h test period stable |

**Rollback plan:** VPS `git checkout` previous commit + restore old zip from backup.

---

## Security / scalability review

### Threats mitigated

| Threat | How |
|---|---|
| Malicious update server | Hardcoded `ems.cfsdesigners.com` host check |
| MITM package swap | HTTPS only; TODO later: sign zip + verify signature |
| Employee loses enroll after update | `robocopy /XF config.json` explicit |
| Offline queue lost | `robocopy /E` keeps `agent_data/` |
| DB wipe during update | Update code **never** imports `app.db` or touches `/var/lib/ems/` |
| Partial download corruption | `httpx` / PowerShell verify; user sees error + Retry |
| Silent install UAC fail | NSIS `currentUser` mode (no admin needed if original install was currentUser) |

### Scalability

| Scenario | Limit | Solution |
|---|---|---|
| 50 employees click Update same time | VPS bandwidth (~50MB × 50 = 2.5GB spike) | NSIS + zip CDN cache / schedule updates (morning vs afternoon) |
| Large zip (future 100MB+) | Slow 3G office | Progress bar already in code; consider delta updates later |
| Manager Tauri bundle size | ~60MB Setup.exe | Acceptable; web (browser) Manager = 0 MB install |

---

## Known limitations (honest)

| What | Status |
|---|---|
| Signed `@tauri-apps/plugin-updater` with CI keys | **Not in this MVP** — requires signing cert + `latest.json` |
| Agent update rollback (user regrets) | Manual — reinstall old zip |
| Screenshot API Sign In hard-block | **Not done** — Phase B polish optional |
| Update while offline | Banner won't show; retry when online |
| Corrupt download detection | Basic (file missing → error); no hash verify yet |

---

## Step-by-step NOW (what to do)

### Option A: Local test first (RECOMMENDED)

1. **Read this entire doc** (you are here)
2. Run **Test 1** (Agent mock update) — 20 min
3. Run **Test 2** (Manager mock update) — 20 min
4. If both PASS → push code
5. Build real Agent 1.1.2 + Manager 0.1.2
6. VPS staging test (1 PC)
7. Production upload + API deploy
8. Office 1 PC → wait 1 hour → rest of office

### Option B: Push now, test on 1 office PC (FASTER but riskier)

1. Push code now
2. Build + upload Agent 1.1.2 / Manager 0.1.2
3. VPS deploy
4. Install on **your own dev PC** first (you have enroll token?)
5. Click Update → verify enroll stays
6. Then roll to office

### Option C: Skip silent update today, ship 1.1.2 with "Download" only

If testing takes too long before 4pm:
- Keep banner → Download page (like 1.1.1)
- Ship silent update (1.1.3) **tomorrow** after thorough test

---

## My recommendation

**Do Option A** (local test). 4pm deadline is **reinstall day**, not "must have silent update." Client ke liye important = **staff productive**, not "fancy click feature breaks enroll."

Safe order:
1. Test mock update locally (2 PCs: yours + one test VM if available) — **1 hour**
2. If PASS → production rollout — **2 hours**
3. If FAIL → fix → retest OR fallback to "Download" banner (1.1.2 code mei already hai)

Matlab: **crash mat karo office ke 20+ PCs ko** — test pehle.

**Abhi karna kya hai?**
1. Main mock test server script likhta hoon
2. Tum 1 PC pe local test karo (Agent + Manager)
3. Pass ho to push + build + deploy
4. Fail ho to debug / fallback

Bolo: **"start local test"** ya **"skip test, push now"** (risky).
