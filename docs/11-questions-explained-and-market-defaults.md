# What those 8 questions mean (plain Urdu/English)

Ye sawal "client se sochne ko" nahi — **market standard se compare karke confirm** karne ke liye hain. Niche har sawal ka matlab + industry kya karti hai + hum kya recommend karte hain.

## End product pehle clear karo

| Cheez | Haan / Nahi |
|---|---|
| Chrome extension only | **Nahi** — AutoCAD/ScotSteel ke clicks/window titles extension se nahi milte |
| Website only | **Nahi** — browser PC ke andar hooks nahi laga sakta |
| Sirf TimesheetV2 clone EXE | **Kam** — live manager view + multi-user + anti-cheat nahi |
| **End product** | **Ek system, do surfaces:** (1) Windows desktop **agent** har employee PC par (2) Manager **web dashboard** browser mein |

Isay market mein **desktop time tracker + workforce dashboard** kehte hain (Hubstaff / Time Doctor / DeskTime jaisa shape). Extension nahi. Alag do products nahi — ek EMS.

---

## Q1 — Screenshot har 5 minute?

**Matlab:** Har kitne time baad employee ki screen ki photo save ho?

| Tool | Practice |
|---|---|
| [Hubstaff](https://hubstaff.com/time-tracker-with-screenshots) | Random shots, typically **1–3 per 10 minutes** while timer on |
| [DeskTime](https://desktime.com/features/time-tracking-with-screenshots) | Random within **5 / 10 / 15 / 30 min** intervals |
| Time Doctor | Periodic while tracking; configurable |

**Professional default (hum):** **Random within every 5 minutes** while Sign In and not on break. Fixed exact 5:00 cheat-able hai; random better. Disk ~150–200 KB/shot.

**Client se poochna:** “5 min OK ya 10 min?” — dono professional hain. 5 = tighter proof (CAD detailing ke liye better).

---

## Q2 — Server office ya cloud?

**Matlab:** Screenshots + attendance data kahan store ho — office PC ya internet VPS?

| Choice | Pros | Cons |
|---|---|---|
| **Office / on-prem** | Client drawings andar rehti hain; no monthly cloud bill for storage | Office internet down → manager live kharab; backup tumhare zimme |
| **Cloud VPS** | Manager ghar se bhi live; backup asaan | CAD drawings internet pe; privacy + client IP risk |

**Professional default (hum):** **On-prem office mini-PC/server pehle.** CAD/Scottsdale drawings sensitive. Agar owner ghar se live chahe → VPN office server ko, cloud pe raw drawings mat daalo.

---

## Q3 — Live = last photo + status (video nahi)?

**Matlab:** Manager “live” dekhna = kya exactly?

| Mode | Market |
|---|---|
| Last screenshot + online/offline + last app | Hubstaff / DeskTime / Time Doctor **standard** |
| Continuous video / live screen share | Kickidler-style; heavy, expensive, privacy hell — **v1 mein nahi** |

**Professional default:** Live board = green/red status + last window title + click rate + **latest screenshot thumb**. Video stream **nahi**.

---

## Q4 — Break In/Out ya sirf Sign In/Out?

**Matlab:** Lunch/chai alag punch, ya sirf aane/jane ka time?

Sheet mein Break columns hain lekin **hamesha 0.00** — matlab aaj wo feature use nahi karte. Hubstaff Grow+ mein **work breaks** paid feature hai.

**Professional default:** **Break In/Out buttons agent mein rakho** (sheet columns match). Agar koi break na dabaye → break hours 0 (aaj jaisa). Future-proof. Sirf Sign In/Out mat hard-code karo.

---

## Q5 — Sign Out ke baad tracking band?

**Matlab:** Kaam khatam dabane ke baad bhi screenshot/clicks?

Market: screenshots **sirf active tracking session** mein (Hubstaff docs: while timer running). After clock-out = **stop**.

**Professional default:** **Sign Out = sab band** (clicks, keys, windows, shots). Stealth after-hours = spyware; mat banana.

---

## Q6 — 10–12 logon ke naam/codes?

**Matlab:** Kitne accounts banane hain? Sheet mein sirf 4 tabs (101–104).

**Professional default:** Build se pehle list chahiye: `code, full name, role`. Warna demo 4 users pe chalega; production incomplete.

---

## Q7 — Official timing + timezone?

**Matlab:** Late kis time se? Overtime kab? Friday short day?

**Professional default assume:** `Asia/Karachi`, Mon–Fri ~09:00–18:00, late = Sign In after grace (e.g. 09:15). Confirm Friday hours. Reports is timezone mein.

---

## Q8 — Employee apni screenshots dekh sake?

| Tool | Practice |
|---|---|
| Hubstaff | Employees **can view** (and sometimes delete) own shots — transparency |
| DeskTime | Team visibility + optional blur |

**Professional default:** Employee **apna din + apni screenshots dekh sake** (read-only). Edit/delete punches **nahi**. Manager sab dekh sake. Hidden “sirf boss dekhe, employee na jaane” = toxic + legal risk — mat recommend karo.

---

## Client ko WhatsApp pe short version (recommended answers already filled)

```
Assalamualaikum — EMS ke liye industry-standard defaults propose kar rahe hain. Agar OK ho to bas “OK” likh dein; change ho to number ke saath bata dein.

1) Screenshot: har 5 min ke andar random (Hubstaff/DeskTime jaisa) — OK?
2) Data server: pehle office ke andar (drawings safe) — OK? (Ghar se dekhna ho to VPN)
3) Live: status + last photo + app name — video nahi — OK?
4) Break In/Out buttons rahenge (use optional; aaj jaisa 0 bhi chalega) — OK?
5) Sign Out ke baad tracking band — OK?
6) 10–12 employees ki list (code + naam) bhej dein
7) Timing: PKT, 9–6, Friday? confirm
8) Employee apni screenshots dekh sake (sirf dekhna; edit nahi) — OK?
```

Zyada sawal = confusion. Defaults ready hain; client sirf **reject/adjust** kare.
