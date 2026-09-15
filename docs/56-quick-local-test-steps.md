# Phase E — Quick start (LOCAL TEST)

**Goal:** Verify Agent + Manager silent update on YOUR PC before office rollout.

---

## 1. Build test packages (5 min)

```powershell
# Agent
cd D:\imp\ems-cfs-designers\apps\agent
.\BUILD-EXE.bat
# Wait → dist\CFS-Designers-Agent\ ready

# Zip it as test package:
cd dist
Compress-Archive -Path CFS-Designers-Agent -DestinationPath test-agent-1.1.3.zip -Force
# Move to repo root: move test-agent-1.1.3.zip D:\imp\ems-cfs-designers\

# Manager (if you have 16GB+ RAM; else skip Manager test for now)
cd D:\imp\ems-cfs-designers\apps\web
npm run tauri:build
# Output: src-tauri\target\release\bundle\nsis\*.exe
# Rename to test-manager-0.1.3.exe, move to repo root
```

---

## 2. Start mock update server (1 min)

```powershell
cd D:\imp\ems-cfs-designers

# Install Flask if needed:
pip install flask

# Edit test_update_server.py line 10-11 to match your zip/exe paths, then:
python test_update_server.py
# Keep running in this terminal
```

Browser: `http://localhost:9999/api/v1/agent/version` — should return JSON.

---

## 3. Test Agent update (10 min)

### Install current Agent (1.1.2) first

```powershell
cd D:\imp\ems-cfs-designers\apps\agent\dist\CFS-Designers-Agent
.\INSTALL-AGENT.bat
# Desktop shortcut → launch Agent
```

### Point to mock server

1. Agent folder: `C:\Users\YourName\...\CFS-Designers-Agent\` (wherever you extracted)
2. Open `config.json` in Notepad
3. Change:
   ```json
   "api_base": "http://localhost:9999"
   ```
4. Save, close Agent, reopen

### Trigger update

- Agent window: **green banner** "Update available v1.1.3"
- Click **Update to v1.1.3**
- Watch: "Downloading…" → "Restarting Agent…"
- Agent closes → reopens (~10s)

### ✅ PASS if:

- Agent returns
- Open `config.json` → `device_token` still there
- Folder `agent_data\` still exists
- No error popup

### ❌ FAIL if:

- Agent doesn't return → check `%TEMP%\cfs-agent-apply-update.ps1` (PowerShell log)
- `config.json` gone → **CRITICAL** — robocopy broke
- Agent crashes → check `agent_data\` for lock files

---

## 4. Test Manager update (optional, 10 min)

If you built Manager Setup:

1. Install Manager **0.1.2** (from `tauri:build` output)
2. Launch desktop app
3. Edit Manager to point mock (harder — needs Tauri dev config OR test with production API returning fake version)
4. Click update → app exits → Setup installs → relaunches

**OR skip** — Manager test can happen on staging VPS after Agent test passes.

---

## 5. Decision point

### If local test PASS:

1. Revert `config.json` → `"api_base": "https://ems.cfsdesigners.com"`
2. Push code to GitHub
3. Build **real** 1.1.2 / 0.1.2 (not test versions)
4. Upload to VPS `/var/www/ems/downloads/`
5. VPS: `git pull` + web build + restart API
6. Office: install 1.1.2 on 1 PC → test → rollout

### If local test FAIL:

1. Debug error (PowerShell log, Agent crash, config missing)
2. Fix code
3. Retest
4. **OR** fallback: ship 1.1.2 with "Download" button only (silent update = tomorrow)

---

## What NOW (simplest path)

**Option 1 (safe, 1 hour):**  
Local test → fix if needed → production

**Option 2 (fastest, risky):**  
Skip local test → push → test on 1 office PC → fix live if breaks

**Recommendation:** Option 1. Office ke 20 PCs ko break mat karo without test.

Batao: **"start local test"** (main test server chalaun) ya **"skip, push now"**.
