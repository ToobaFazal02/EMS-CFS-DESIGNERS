# Client voice — 3 Sep 2026 (invoice PDF parity + partner shares)

Sources:

| Audio / file | Transcripts |
|---|---|
| `WhatsApp Ptt 2026-09-03 at 6.39.08 PM (1).ogg` (~67s) | `references/client-voice-2026-09-03/*6.39*` |
| `WhatsApp Ptt 2026-09-03 at 7.18.29 PM.ogg` (~25s) | `references/client-voice-2026-09-03/*7.18*` |
| `WhatsApp Ptt 2026-09-03 at 7.19.31 PM.ogg` (~12s) | `references/client-voice-2026-09-03/*7.19*` |
| Reference PDF | `references/client-invoice-2026-09-03/Invoice-Faisal-CFS-Designers-30-07-26.pdf` |
| Annotated WhatsApp screenshot (green circle on COST + TOTAL BUDGET) | `references/client-invoice-2026-09-03/whatsapp-annotated-invoice.png` |

Whisper ASR is messy on Roman Urdu; meaning below is **interpreted**.

**Answers locked 7 Sep 2026 (user):**

| # | Question | Locked answer |
|---|---|---|
| Q1 | Second partner | **Asad Khan** (with Faisal Khan) |
| Q2 | Split | Always **50/50** |
| Q3 | Invoice side | **All paid** invoice amounts |
| Q4 | Expense side | **All** office expenses in the period |
| Q5 | Dashboard | Summary **yes**, but **only partners** (admin / Faisal–Asad) — never HR, employee, demo, or manager |

**Status:** Implementation started 7 Sep 2026.

---

## Voice note map

| Time | Core ask (interpreted) |
|---|---|
| **6:39 PM** | Keep **Add New Invoice**. After save, PDF download must match **his format** (client, project, area, rate, cost). Also introduce **Faisal share / Asad share**: total invoice $ − CFS office expenses → remainder ÷ 2 → each partner’s visible share. |
| **7:18 PM** | **No bright red** on the invoice (use maroon / theme). **Remove COMMENTS column** — his PDF does not have it. Follow his invoice **exactly**. Move **USD Account Details** a bit lower. |
| **7:19 PM** | Fine-tune vertical spacing: Account Details lower, **Invoice To** block lower, **THANK YOU FOR YOUR BUSINESS!** lower — match the sample he sent. |

---

## Locked intent — Invoice PDF (P0)

Reference layout to match (Harbour Steel Frames / Cydney Skeens style):

```
INVOICE
Faisal Khan
Islamabad, Pakistan
+92 …
DATE : DD-MM-YYYY

Invoice To
CLIENT NAME
Country / phone

[CLIENT NAME banner — green]
S/NO | Project Name | Scope of Work | AREA | $ per sq.ft | COST ($)
…line rows (AREA × rate = COST)…
TOTAL BUDGET                         [yellow]  <sum>

USD Account Details:   ← slightly more space above
  Name / Account / Routing / Swift / Bank …

Contact blurb + email
THANK YOU FOR YOUR BUSINESS!
```

### Must-change vs current `invoice_pdf.py`

| # | Current | Client wants |
|---|---|---|
| 1 | Column header **Budget ($)** | **COST ($)** (circled in WhatsApp) |
| 2 | **COMMENTS** column present | **Remove** from PDF (and form default) |
| 3 | Unpaid cells / picker “red” | **Maroon** only (`#7A1F2E`) — already partly done; verify PDF + color picker + UI |
| 4 | Bank block tight under table | **More spacer** before USD Account Details |
| 5 | Invoice To / thanks spacing | **Slightly lower** blocks to match sample |
| 6 | Line math | Keep / verify: `AREA × $ per sq.ft = COST`; lump-sum rows allowed (e.g. Engineering Review $500) |
| 7 | TOTAL BUDGET row | Yellow total cell; sum of COST column |

### Explicitly out of this PDF pass

- Emailing PDF from EMS (still later)
- Live FX conversion
- Tax / discount lines (not on his sample)

---

## Locked intent — Partner share ledger (P1)

Client language: *“Faisal share / Asad share … total invoice value se CFS expenses minus … baqi divide by two … visible ho ke kis ke kitne paise padh rahe hain.”*

### Formula (v1)

```
Gross invoices (period, paid or billed — confirm below)
− CFS office expenses (same period, from Expenses module)
= Net pool
Net pool ÷ 2 = Faisal share
Net pool ÷ 2 = Asad share
```

### Product shape (proposed)

| Piece | Behavior |
|---|---|
| **Screen** | New admin-only page or Dashboard card: **Partner shares** (not visible to HR / employee / demo) |
| **Inputs** | Auto from: Payments invoices + Office expenses (already built) |
| **Period** | Month + year filters (same as expenses) |
| **Visibility** | Running total + per-month breakdown; who is “ahead” if draws differ (v1 can be equal split only) |
| **Not payroll** | This is **owner profit split**, not employee salary |

### Open questions — **LOCKED 7 Sep 2026**

| # | Answer |
|---|---|
| Q1 | Partner B = **Asad Khan** |
| Q2 | Always **50/50** |
| Q3 | **Paid invoices only** (USD pool) |
| Q4 | **All** CFS office expenses in period — each expense date’s live USD/PKR rate |
| Q5 | Dashboard summary + `/partner-shares` page; **admin/partner only** |
| FX | **Per-row daily rate** via currency-api (cached). PKR + USD both shown. Hardcoded 280 removed. |

---

## Priority backlog (implementing)

### P0 — Invoice PDF exact match — **IN PROGRESS / done in code**

1. Rename Budget → **COST ($)**; drop **COMMENTS** column from PDF (+ form).
2. Spacing pass: Invoice To, bank block, thanks.
3. Maroon unpaid cells (`#7A1F2E`).
4. Manual test vs client sample.

### P1 — Faisal / Asad share — **IN PROGRESS / done in code**

1. API `GET /api/v1/partner-shares` + dashboard `partner_shares` (require_partner).
2. UI: Shares nav + Partner shares page + Dashboard KPI.
3. Gate: `Role.admin` + Faisal/Asad name/email **or** `admin@cfsdesigners.com` — never HR / employee / demo / manager.

### P2 — Already done recently (do not rebuild)

- HR cannot see Payments / invoice $
- Demo role + `is_demo` isolation
- Office expenses + receipts + monthly/yearly totals
- Maroon UI theme (site-wide) — complete PDF leftover in P0

### P3 — Ops / later (unchanged)

- Employee Agent enroll + how-to video
- Sales white-label demo walkthrough (`docs/41` item 9)
- PDF report hours still `2h 32m` vs `8.1 h`

---

## Done vs not (honest snapshot — 6 Sep 2026)

| Area | Status |
|---|---|
| Add New Invoice + download PDF | **Built** — layout **not yet** exact to 3 Sep sample |
| COMMENTS column | Still in PDF — **remove** (P0) |
| COST ($) label | Still says Budget ($) — **rename** (P0) |
| Red → maroon UI | **Done** on web; PDF unpaid = maroon hex but client still flagged red → re-check |
| Office expenses + receipts + year totals | **Done** |
| HR finance lock + demo isolation | **Done** |
| Faisal / Asad share ledger | **Not built** (P1) |
| Employee PC enroll video | Ops backlog |

---

## Implementation gate

| Key | Value |
|---|---|
| Plan status | **DRAFT — awaiting your approval** |
| Code for P0/P1 | **No** until you reply approve (and answer Q1–Q5 if changing defaults) |
| Reference of truth | Client PDF + green-circle screenshot in `references/client-invoice-2026-09-03/` |
