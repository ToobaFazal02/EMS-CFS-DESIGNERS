# EMS — kya kahan khulta hai

| Cheez | Kahan | Kaun use karta hai |
|-------|--------|-------------------|
| **Web** | Browser → http://127.0.0.1:5173 | Manager (reports, live, employees) |
| **Agent** | Choti black/gold window "CFS Designers" | Employee (Sign In / Out) |
| **API** | Background — black CMD "EMS API" | Dono ke liye — band mat karo |

## Start (2 CMD + Agent)

1. Double-click **`START-EMS.bat`** → 2 windows (API + Web)
2. Double-click **`RUN-AGENT.bat`** → UAC **Yes** → Agent taskbar pe

## Sign In error / Sign Out grey?

Sleep ke baad agent **OFF** dikhta hai lekin server pe session **open** reh jata hai.

**Fix:** Agent mein button **"Close open session"** dabao (Sign Out ki jagah) → phir **Sign In**.

Ya Sign In dabao → popup **Yes** = auto close + fresh Sign In.

## Sirf 2 terminals

`START-EMS.bat` ab sirf API + Web kholta hai. Agent alag hai — 4 windows nahi.
