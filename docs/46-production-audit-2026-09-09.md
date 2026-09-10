# Production pre-deploy audit — 9 Sep 2026

**Status: DONE (code gate)** — backup DB + ship after your browser QA checklist.

---

## Your questions (answered)

| Question | Answer |
|---|---|
| HR types `/payments` → Dashboard? | **Was correct security** (HR must not see invoices). Now shows clear **403 Access denied** instead of silent redirect. |
| Blank page `/pay/…/Tocba@123`? | **Bug:** no catch-all route → empty screen. **Fixed:** unknown URLs → **404 Page not found**. |
| What is “ops”? | Not an app feature. Likely meant **ops = operations** (enroll PCs, video) or a misread. That URL is **not** a real Payments page. |
| Password in URL (`Tocba@123`)? | **Never put passwords in the address bar.** Browser history + logs leak them. Change that password if it was real. |

---

## AI / modern-SPA loopholes checked

| Common issue | CFS EMS status |
|---|---|
| Missing 404 catch-all | **Fixed** this pass |
| Client-only role hide (API still open) | Payments/Shares API use `require_finance` / `require_partner` |
| HR sees finance via URL | Blocked UI + API |
| Demo data mixed into production | `is_demo` filters |
| Secrets in frontend | Token in `localStorage` (normal SPA); no SMTP keys in repo |
| Weak JWT secret in prod | API **refuses to start** if `SECRET_KEY` weak |
| Login brute force | Rate limit login + enroll (`rate_limit.py`) |
| Upload abuse | Receipt MIME + 5MB cap |
| CSRF on cookie auth | Bearer JWT (not cookie session) — CSRF low |
| Open redirect | No open redirect pattern found |
| Blank error screens | 404 + 403 pages added |
| Full DDoS immunity in app code | **Not possible in app alone** — use Cloudflare / nginx / Hostinger WAF in front |

---

## Security residual (infra — do on production)

1. Strong `SECRET_KEY` in production `.env`  
2. HTTPS only (`base_url` https)  
3. Cloudflare or host firewall rate limits (DDoS)  
4. Backup DB before deploy  
5. Do not commit `.env` / receipts / screenshots  

---

## Client voice / product — code complete

| Area | Done |
|---|---|
| Workforce Agent + Live + reports | Yes |
| Projects + payment gates | Yes |
| Payments + invoice PDF (COST, colors, spacing) | Yes |
| HR isolation + expenses + receipts | Yes |
| Demo isolation | Yes |
| Partner 50/50 USD (daily FX on expenses) | Yes |
| 404 / 403 handling | Yes (this pass) |

**Still human/ops (not code blockers):** Agent install on office PCs + short enroll video.

---

## Deploy order

1. Browser QA (roles + PDF + Shares math + 404 URL test)  
2. Backup SQLite / DB  
3. Deploy API + web  
4. Set production `.env` (strong secret, HTTPS CORS)  
5. Smoke login as Admin + HR  

**Audit result: DONE for code ship.** Infra DDoS = host layer.
