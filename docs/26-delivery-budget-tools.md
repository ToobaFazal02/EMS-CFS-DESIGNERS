# Delivery, budget, Docker, tools (locked answers)

## Docker — do we need it?

**Phase 1 client handover: No Docker required.**

| Approach | When |
|---|---|
| Simple Windows service / start scripts | **Default for CFS office** — one office PC runs API |
| Docker Compose | Optional later if they want easier updates on Linux server |

Client ko Docker seekhne ki zaroorat nahi. Tum install karke de sakti ho.

## Client budget beyond your fee?

Usually **minimal**:

| Item | Cost |
|---|---|
| Office PC / mini PC for server | Unke paas pehle se hona chahiye; warna ~cheap used PC |
| Windows licenses | Already on employee PCs |
| Domain / SSL | Optional; LAN pe IP chal sakta hai |
| Cloud VPS | **Only if** they choose cloud — then ~$5–20/mo |
| Hubstaff-style SaaS | **Not needed** — ye custom hai |

Unhe alag se “software license buy” nahi — tum custom deliver karti ho. Electricity + backup disk recommend karo.

## What is a professional deliverable?

**Source code zip WhatsApp pe bhej dena = amateur.**

Professional package:

1. **Installer / setup folder** for agent (`.exe` or Inno Setup later)  
2. **Server pack**: API + `.env.example` + seed + start script  
3. **Manager web** URL on office network  
4. **Admin login** + enroll guide (1 page PDF)  
5. **Training** 30–45 min  
6. **Acceptance checklist** signed  
7. Source code: optional escrow / after full payment — contract pe likho  

They install **your built software**, not raw folders of Python (unless they hire a maintainer).

## Reports: XLSX vs CSV

- **XLSX** = client-facing professional (colors, title, freeze header) — **primary**  
- **CSV** = machine/payroll import — secondary  

`########` in Excel = date column too narrow OR bad date parse. We now export dates as `20-Aug-2026` text + branded `.xlsx`.

## Project tracking tool (senior freelancer)

**Recommendation for you:**

| Tool | Use |
|---|---|
| **ClickUp** (free) or **Notion** | Client board: Backlog / Doing / Review / Done + docs |
| **GitHub Projects** or **Linear** | If git remote — issues linked to code |
| WhatsApp | Only status updates — not the backlog |

Simple ClickUp lists for this project:

- Backlog  
- Phase 1 In Progress  
- Testing  
- Blocked (needs client)  
- Done  

Don’t buy Jira for one client EMS.
