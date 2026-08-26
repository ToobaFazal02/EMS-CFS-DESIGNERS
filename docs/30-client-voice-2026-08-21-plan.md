# Client voice — 21 Aug 2026 (NEW REQUIREMENTS)

Sources:
- WhatsApp text: “THIS IS LOOKING GREAT” + **NAME IT CFS DESIGNERS INSTEAD OF EMS CFS**
- Excel screenshot: client invoice pipeline (CLIENT NAME, LOCATION, INVOICE status, INVOICE #)
- 6 voice notes (`references/client-voice-2026-08-21/*.txt`)

Status: **Planning only — do not code until client confirms scope + quote**

---

## Voice note map (chronological)

| Time | Duration | Core ask (interpreted) |
|---|---|---|
| 9:50 PM | ~82s | **Project module** — phases like another company’s online system: intake → preliminary design/engineering → final design/engineering → review. Each project: deadline, assignee, stage % complete. All in one app with attendance. |
| 9:51 PM | ~46s | **Invoicing module** — today they track 20+ clients in Excel: amount, invoice date, delays, proper invoice format. Wants same flow inside software. |
| 9:52 PM | ~74s | **Payment queue / cash-flow rule** — clients pay in queue; advance (e.g. $15k) before work; many clients slow to pay → need visibility. **Rule: money first, then start project.** |
| 9:53 PM | ~43s | Invoicing belongs **in the same app** as attendance. Priority order: attendance foundation → invoicing → projects (details follow). |
| 9:56 PM | ~32s | **Role separation** — employees see **attendance + their projects only**. **Never finance.** Finance/admin sees money. HR/manager sees people + ops, not employee-facing money screens. |
| 9:57 PM | ~49s | **One unified system** for management, finance, attendance — not separate laggy tools. Must be **easy to use without training** (like demos on market products). Different people use different parts of same system. |

Whisper note: Roman Urdu/English mix → some words garbled (“invite” = likely **intuitive**, “devices delaying” = likely **payments delaying**). Confirm with client on marked items in §Open questions.

---

## What we understand (business truth)

CFS Designers is not “only employee monitoring.” Client wants **one office operating system**:

```
┌─────────────────────────────────────────────────────────────┐
│                    CFS DESIGNERS (one product)               │
├──────────────┬──────────────────────┬───────────────────────┤
│  WORKFORCE   │      PROJECTS        │       FINANCE         │
│  (built v1)  │      (new)           │       (new)           │
│              │                      │                       │
│ Sign In/Out  │ Client → Project     │ Invoice pipeline      │
│ Live board   │ Phases + %           │ PROFORMA/SENT/PAID    │
│ Screenshots  │ Deadline + owner     │ Amount + dates        │
│ Day/monthly  │ Assign to employee   │ Payment-before-start  │
│ reports      │                      │ Client payment queue  │
└──────────────┴──────────────────────┴───────────────────────┘
         ▲              ▲                        ▲
    Employee        Employee                 Finance / Admin
    (limited)       + Manager                (full money view)
                    + HR
```

**Excel today** = finance team’s source of truth for **client invoices**, not employee hours.  
**Old Timesheet** = employee activity proof.  
**Our Phase 1** = replaced Timesheet + part of attendance sheet.  
**Phase 3+** = replace Excel invoice tracker + add real **project lifecycle**.

---

## Client Excel → software fields (from screenshot)

| Column | Meaning | Software field |
|---|---|---|
| SN | Row # | auto |
| CLIENT NAME | Customer | `clients.name` |
| LOCATION | Country/market | `clients.country` |
| INVOICE | Pipeline status | enum: PROFORMA, SENT, PAID, UNPAID INFO, INFO SENT |
| INVOICE # | Reference | `invoices.number` |
| (hidden cols) | Amount, dates, notes | add after client sends full sheet |

Color badges in Excel → same status pills in web UI (finance role only).

---

## Project phases (client reference system)

Default template for LGS/CFS jobs:

1. **New project / Intake**
2. **Preliminary design**
3. **Preliminary engineering**
4. **Final design**
5. **Final engineering**
6. **Review**
7. **Complete / Delivered**

Per project:
- Client link
- Assigned employee(s)
- Deadline per phase + overall
- **% complete** per phase and total
- Status: Not started / In progress / On hold / Done

Market pattern: **ClickUp spaces** or **Monday.com boards** — simple kanban + phase checklist, not heavy Primavera.

---

## Roles & visibility (locked from voice)

| Role | Sees | Never sees |
|---|---|---|
| **Employee** | Own attendance, own assigned projects, Sign In agent | Invoice amounts, client payment status, other employees’ finance |
| **Manager / HR** | Live board, all attendance, all projects, assign work | — (finance optional: read-only or hidden — confirm) |
| **Finance / Admin** | Clients, invoice pipeline, payment queue, reports | — |
| **Super Admin** | Everything + settings | — |

Employee agent title: **CFS Designers** (not EMS CFS).

---

## Market inspiration (what to copy, not buy)

| Need | Market product | Copy this pattern |
|---|---|---|
| Time + proof of work | Hubstaff, DeskTime, Time Doctor | Agent + live board + day PDF (**done**) |
| Project phases + % | ClickUp, Monday.com, Asana | Project → stages → progress bar → assignee → due date |
| Client invoice pipeline | Pipedrive deals, Notion CRM, Harvest | Status column + color badges + filters (match Excel) |
| Time → project → invoice | Harvest, Toggl Track + FreshBooks | Later: hours on project roll into invoice readiness |
| All-in-one SMB | Odoo, ERPNext | **Modular menus** by role — do **not** deploy full ERP |

**Reshape strategy:** Keep our custom stack (FastAPI + React + agent). Add **modules** with role-based nav — same as Odoo/ERPNext UX idea, without their weight.

---

## Phased roadmap (recommended)

### Phase 2.x — finish & ship link (1–2 weeks)
- [ ] Rebrand all UI: **CFS Designers** (web, agent, PDF, Excel headers)
- [ ] Staging URL for client demo (office LAN or cheap VPS)
- [ ] Tray agent, report polish (in progress)
- [ ] 1-page “how to use” for manager

### Phase 3 — Projects module (3–4 weeks)
- Clients CRUD (name, location, contact)
- Projects CRUD linked to client
- Phase template + % complete + deadlines
- Assign employees to projects
- Manager project board; employee “My projects” view
- **No money fields on employee screens**

### Phase 4 — Finance / Invoice pipeline (3–4 weeks)
- Replicate Excel tracker in web (table + filters + status badges)
- Invoice record: client, #, status, amount, dates, notes
- Payment queue view (“who owes”, aging)
- **Pay before start** flag on project (blocked until deposit recorded)
- Export Excel/PDF for finance (same professional style as attendance)

### Phase 5 — Connect workforce ↔ projects (2–3 weeks)
- Optional: tag agent activity / day hours to active project
- Project dashboard: who worked, last activity
- “Ready to invoice” when phase = 100% + finance checklist

### Phase 6 — Hardening & optional (later)
- Google Sheet one-way sync (if client still wants backup)
- Overtime rules, screenshot blur, installer .exe
- White-label / second company (client mentioned “sell later” — out of scope until v1 stable)

**Do not quote Phases 3–5 as one lump with Phase 1.** Separate invoice milestones.

---

## Branding change (immediate, low risk)

| Location | Was | Becomes |
|---|---|---|
| Web header / title | EMS CFS Designers | **CFS Designers** |
| Login subtitle | EMS CFS | **CFS Designers** |
| Agent window | EMS CFS Designers — Agent | **CFS Designers — Agent** |
| PDF/Excel headers | EMS CFS Designers | **CFS Designers** |
| API `app_name` in config | EMS CFS Designers | **CFS Designers** |

Internal repo folder name can stay `ems-cfs-designers` until rename is worth it.

---

## Open questions for client (WhatsApp short list)

1. Excel sheet: full column list + sample rows (amount, invoice date, due date, currency)?
2. Project phases: is the 7-step list above correct for every job type?
3. **Pay before start**: fixed deposit ($15k) or % of quote per client?
4. Manager role: can manager **see** invoice status or finance-only?
5. One admin login or separate **Finance login** + **HR login**?
6. Link for demo: office PC IP OK or public HTTPS domain?
7. Priority if budget split: **Projects first** or **Invoicing first**? (Voice said attendance base → invoicing → projects — confirm order)

---

## Quote / scope guardrails

**In scope for “CFS Designers Platform v2”:** modules above, 10–12 users, role-based web, keep Windows agent.

**Out of scope unless new contract:**
- Full accounting (GL, tax filing, bank sync)
- Payroll
- Client portal (clients logging in)
- Mac agent
- Replacing FrameCAD / CAD tools

---

## Next action (team)

1. Client ko 7 questions bhejo + renamed screenshots (CFS Designers)
2. Client se poora Excel file (not cropped screenshot)
3. `STATUS.md` update: Phase 3 approved yes/no + budget band
4. Then implement: rebrand → Phase 3 or 4 per client priority
