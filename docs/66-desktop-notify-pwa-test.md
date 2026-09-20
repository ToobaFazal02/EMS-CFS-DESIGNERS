# How to run Desktop + hear notify + test Agent

**Branch:** `desktop+agent` · Manager **0.1.6** (same React as web)

## 1) Start Manager Desktop (local)

Terminal A — API (if testing local):

```bat
cd D:\imp\ems-cfs-designers\apps\api
.\venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

Terminal B — Desktop shell:

```bat
cd D:\imp\ems-cfs-designers\apps\web
npm run tauri:dev
```

- Login as **Admin**
- Footer should show `v0.1.6 · Desktop`
- Or install Setup.exe from GitHub Actions / Downloads (production API)

## 2) Hear notification sound

1. **Click once** anywhere in the app (unlocks audio — WebView2 rule).
2. Keep Admin Desktop open.
3. In another browser / staff account: open a project → leave Intake **without** Paid deposit (soft gate), **or** staff saves My % today.
4. Within ~45s Admin bell badge increases → **louder two-tone alert**.
5. Click **bell** (next to gear) → see alert → Mark read.

No beep? Click anywhere in the app once (unlocks audio), then trigger another alert.

## 3) Admin / HR mobile “app” (PWA — not Play Store)

There is **no** separate APK/IPA. **Admin or HR** installs the **website** to the home screen.  
**Manager, Employee, Demo must never see the Install banner.**

1. Phone Chrome/Safari → `https://ems.cfsdesigners.com` (HTTPS required)
2. Login **Admin** or **HR**
3. Banner **Install Admin / HR app** → Install  
   - Android: also ⋮ → Install app  
   - iPhone: Share → Add to Home Screen
4. Open from home icon → same Manager UI (glance)

### What works on phone PWA

| Works | Does not |
|---|---|
| Dashboard, Live, Day, Projects, Reports, Downloads, bell (role-gated) | Employee Agent Sign In / Out |
| View PDFs, progress dropdowns, unpaid red cards | Screenshot capture from phone |
| Staff / Manager cannot install as “Agent” punch app | |

## 4) Agent test (staff PC)

1. Extract `CFS-Agent-Install.zip` · run START / exe  
2. Enroll with Admin code  
3. Sign In → idle → shots → Break → Sign Out  
4. Confirm on Manager Live + Day  
5. Restart: quit tray → start again (re-enroll only if asked)

## 5) Before production deploy

- [ ] `desktop+agent` pulled on VPS · API restart · web build  
- [ ] New Daily PDF (no blank click-sheet page)  
- [ ] Admin 7-day % · Staff 7-day %  
- [ ] Unpaid cards red  
- [ ] Bell + chime on Desktop after one click  
- [ ] PWA install on one Admin phone  
- [ ] Setup 0.1.6 + Agent zip on `/downloads/`
