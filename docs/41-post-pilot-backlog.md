# After MVP handover — saved list

Sources: `docs/42-client-voice-2026-08-30-plan.md` · **`docs/45-client-voice-2026-09-03-plan.md` (latest product asks)**

Priority order for the **next coding sprint** (after your approval of doc 45):

| Pri | Item | Status |
|---|---|---|
| **P0** | Invoice PDF exact match to client sample (COST $, no COMMENTS, spacing, maroon not bright red) | **Done in code 7 Sep** — verify PDF side-by-side |
| **P1** | Faisal / Asad partner share: paid invoices − CFS expenses → ÷ 2, admin-visible | **Done in code 7 Sep** — `/partner-shares` + Dashboard KPI |
| P2 | Employee Agent enroll + how-to screen video (ops) | Ongoing ops |
| P3 | Sales white-label demo walkthrough | Later — after CFS ops stable |
| — | PDF report hours `8.1 h` vs `2h 32m` | Nice-to-have |

---

## 0. Ops (not new product)

- Add employees + professional EMS emails + unique passwords
- Enroll PCs; four punch buttons; branded Agent already in zip
- Record a **short screen video** of install → enroll → Sign In (client asked)

---

## 1. Hubstaff-style dashboard (first screen) — **done**

- Home = **Dashboard**. Live is its own tab. Money (unpaid invoices) **admin only**.

## 2. Settings gear — **done 31 Aug 2026**

## 3. Themed thin scrollbars — **done 31 Aug 2026**

## 4. Agent as a real desktop app — **done** (`CFS-Agent-Install.zip`)

## 5. Decimal hours — **web day view 8.1 h (done)**; PDF reports still `2h 32m`

## 6–8. Distinct HR + expenses isolation — **done Sep 2026**

- HR: attendance / projects / expenses — **not** Payments / invoice $
- Demo role + `is_demo` catalog — never mixed into real data
- Receipts upload/view/download + monthly + yearly expense totals

## 10. Invoice PDF parity (P0 — client 3 Sep 2026)

See `docs/45-client-voice-2026-09-03-plan.md`.

- Column **COST ($)** (not Budget)
- Drop **COMMENTS** column
- Spacing: Invoice To / USD Account Details / Thank you — match sample
- No bright red; maroon only on unpaid/highlights
- Side-by-side test vs `Invoice - Faisal - CFS Designers (30-07-26).pdf`

## 11. Partner shares — Faisal / Asad (P1 — client 3 Sep 2026)

```
Total invoice value (period) − CFS office expenses = net
net ÷ 2 = Faisal share | Asad share
```

Admin-only; not HR / not demo. Confirm 50/50 + paid-only defaults in doc 45 before coding.

## 9. Sales / marketing demo (BACKLOG — do not start until CFS ops stable)

**Goal:** A public or invite-only walkthrough that sells the *product*, not CFS Designers’ private data.

| Piece | Plan |
|---|---|
| Brand | White-label: “Studio EMS” / generic logo — **no CFS name** on sales demo |
| Data | Only fictional sample staff / projects / expenses (`is_demo=True`) |
| Scope | Full tour: Dashboard, Live (fake cards), Team, Projects, Expenses, Reports (sample), Payments (fake invoices) |
| Access | Password-rotated demo login, rate-limited; never production DB |
| Ads / Reels | 15–30s: Sign In blink → Live board → day hours → invoice PDF — sample only |
| USA targeting | Pain: “CAD detailers / LGS shops / remote drafting teams”; LinkedIn + Meta ads to AEC / cold-formed steel / remote engineering orgs; landing = book a call + demo login |

**Do not** run ads that show real CFS clients, screenshots, or invoice bank details.
