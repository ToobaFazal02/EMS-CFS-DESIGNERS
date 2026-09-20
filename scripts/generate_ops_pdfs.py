#!/usr/bin/env python3
"""Generate CFS EMS operations / QA / security / master-prompt PDFs into docs/pdfs/."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "pdfs"
GOLD = colors.HexColor("#c9a227")
INK = colors.HexColor("#1a1a1a")
MUTED = colors.HexColor("#555555")

# Keep in sync with apps/web/src/version.ts + apps/api agent LATEST_* versions
PACK_VERSION = "0.1.6"
AGENT_VERSION = "1.1.6"
BRANCH = "desktop+agent"
DOC_DATE = date.today().isoformat()
VERSION_LINE = (
    f"EMS pack v{PACK_VERSION} · Agent {AGENT_VERSION} · branch {BRANCH} · docs {DOC_DATE}"
)


def styles():
    base = getSampleStyleSheet()
    return {
        "cover": ParagraphStyle(
            "cover",
            parent=base["Title"],
            fontSize=20,
            textColor=INK,
            spaceAfter=6,
            alignment=TA_CENTER,
            leading=26,
        ),
        "sub": ParagraphStyle(
            "sub",
            parent=base["Normal"],
            fontSize=10,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "ver": ParagraphStyle(
            "ver",
            parent=base["Normal"],
            fontSize=9,
            textColor=GOLD,
            alignment=TA_CENTER,
            spaceAfter=14,
            fontName="Helvetica-Bold",
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontSize=13,
            textColor=INK,
            spaceBefore=12,
            spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontSize=11,
            textColor=GOLD,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontSize=9,
            leading=12.5,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceAfter=5,
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["Normal"],
            fontSize=8,
            leading=10.5,
            textColor=MUTED,
            spaceAfter=3,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            parent=base["Normal"],
            fontSize=8.5,
            leading=11.5,
            textColor=INK,
            alignment=TA_LEFT,
        ),
        "code": ParagraphStyle(
            "code",
            parent=base["Code"],
            fontSize=7.5,
            leading=10,
            textColor=INK,
            backColor=colors.HexColor("#f4f4f4"),
            leftIndent=3,
            rightIndent=3,
            spaceBefore=3,
            spaceAfter=6,
        ),
        "prompt": ParagraphStyle(
            "prompt",
            parent=base["Normal"],
            fontSize=8,
            leading=11,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=4,
            fontName="Helvetica",
        ),
    }


def bullets(items: list[str], st) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(i, st["bullet"]), leftIndent=6, bulletColor=GOLD) for i in items],
        bulletType="bullet",
        start="•",
        leftIndent=12,
        spaceBefore=1,
        spaceAfter=6,
    )


def table(headers: list[str], rows: list[list[str]], col_widths: list[float] | None = None):
    st = styles()
    data = [[Paragraph(f"<b>{h}</b>", st["small"]) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), st["small"]) for c in row])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111111")),
                ("TEXTCOLOR", (0, 0), (-1, 0), GOLD),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cccccc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf8f2")]),
            ]
        )
    )
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(0.5)
    canvas.line(16 * mm, 11 * mm, A4[0] - 16 * mm, 11 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(16 * mm, 6 * mm, f"CFS EMS · {VERSION_LINE}")
    canvas.drawRightString(A4[0] - 16 * mm, 6 * mm, f"Page {doc.page}")
    canvas.restoreState()


def cover(title: str, blurb: str) -> list:
    st = styles()
    return [
        Paragraph("CFS Designers EMS", st["sub"]),
        Paragraph(title, st["cover"]),
        Paragraph(VERSION_LINE, st["ver"]),
        Paragraph(blurb, st["sub"]),
        Spacer(1, 4),
    ]


def build(path: Path, title: str, story: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title=f"{title} · v{PACK_VERSION}",
        author="CFS Designers EMS",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print("Wrote", path.name)


def pdf_index():
    st = styles()
    story = cover(
        "Operations PDF Pack — Index",
        "All PDFs below share the same pack version. Regenerate with scripts/generate_ops_pdfs.py after every release.",
    ) + [
        table(
            ["File", "Purpose"],
            [
                ["00-Ops-PDF-Pack-Index.pdf", "This index"],
                ["01-QA-Feature-Testing-Guide.pdf", "Feature QA + sensitive data"],
                ["02-Security-Audit-Report.pdf", "Security findings"],
                ["03-Hostinger-VPS-Deploy.pdf", "Production deploy"],
                ["04-Local-Run-and-Smoke-Test.pdf", "Local run + smoke"],
                ["05-Break-Fix-Runbook.pdf", "Repair without data wipe"],
                ["06-Click-Background-Auto-Update.pdf", "Honest auto-update status + risk"],
                ["07-Master-EMS-AI-Build-Prompt.pdf", "Top-tier one-shot AI build prompt"],
            ],
            [78 * mm, 96 * mm],
        ),
        Paragraph(
            f"Source of truth: branch <b>{BRANCH}</b>, Manager/Web <b>v{PACK_VERSION}</b>, Agent <b>{AGENT_VERSION}</b>.",
            st["body"],
        ),
    ]
    build(OUT / "00-Ops-PDF-Pack-Index.pdf", "EMS Ops Index", story)


def pdf_qa():
    st = styles()
    w = [26 * mm, 40 * mm, 54 * mm, 54 * mm]
    story = cover(
        "QA Feature Testing Guide",
        "Every feature, sensitive-data checks, and fix path. Never wipe ems.db.",
    ) + [
        Paragraph("1. Roles & sensitive UI", st["h1"]),
        table(
            ["Area", "Admin", "Manager", "HR", "Employee"],
            [
                ["Payments / $ / Advance badges", "Yes", "Yes", "No", "No"],
                ["Downloads (Agent/Setup)", "Yes", "No", "Yes", "No"],
                ["Phone PWA install", "Yes", "No", "Yes", "No"],
                ["Notify bell + Test sound", "Yes", "Yes", "Yes", "No"],
                ["Past 7 days employee dropdowns", "Yes", "Yes", "Yes", "N/A (own %)"],
                ["Screenshots of others", "Yes", "Yes", "Yes", "Self only"],
            ],
            w,
        ),
        Paragraph("2. Feature checks", st["h1"]),
    ]
    features = [
        (
            "Advance pending hidden from staff",
            "Login as employee → My Projects. Cards must NOT show Advance pending / Deposit due / red pay row. Admin still sees Deposit due / Final pay.",
            "gate blanked in API for non-finance; UI badges finance-only",
            "Pull latest API+web; hard refresh Desktop.",
        ),
        (
            "Past 7 days dropdowns aligned",
            "Dashboard → Past 7 days. Names left; “N updates” right-aligned in same column; chevron far right.",
            "attendance/progress aggregates",
            "CSS grid on .dash-progress-emp summary.",
        ),
        (
            "Notify bell + sound",
            "Admin Desktop: open bell → Test sound (beep). Then unpaid soft-gate or staff % save → badge + beep within ~45s.",
            "office_notifications",
            "One click unlocks WebView2 audio; Test sound verifies speakers.",
        ),
        (
            "Downloads nav",
            "Admin/HR see Downloads. Manager/Employee/Demo do not; /downloads redirects home.",
            "binaries distribution",
            "Admin hands Agent zip to staff offline if needed.",
        ),
        (
            "Click-to-update (Desktop/Agent)",
            "Banner when server version higher → click → background install. Enroll + DB stay.",
            "local binaries only",
            "See PDF 06. Host HTTPS zip/Setup on /downloads/.",
        ),
    ]
    for name, how, sens, fix in features:
        story.append(
            KeepTogether(
                [
                    Paragraph(name, st["h2"]),
                    Paragraph(f"<b>Check:</b> {how}", st["body"]),
                    Paragraph(f"<b>Sensitive:</b> {sens}", st["body"]),
                    Paragraph(f"<b>If broken:</b> {fix}", st["body"]),
                ]
            )
        )
    build(OUT / "01-QA-Feature-Testing-Guide.pdf", "EMS QA", story)


def pdf_security():
    st = styles()
    w = [22 * mm, 22 * mm, 58 * mm, 72 * mm]
    story = cover(
        "Security Audit Report",
        "Code review · no critical auth bypass · residual hardening listed.",
    ) + [
        Paragraph("Verdict", st["h1"]),
        Paragraph(
            "Safe for office pilot on HTTPS with strong SECRET_KEY and private repo. "
            "Payment badges no longer leak to staff/HR via UI or project list API gate field. "
            "Click-update uses host allowlist + HTTPS; cryptographic code-signing is optional next (docs/64).",
            st["body"],
        ),
        table(
            ["ID", "Sev", "Finding", "Status"],
            [
                ["S1", "OK", "bcrypt + JWT typ user/device", "Keep"],
                ["S2", "OK", "Screenshot path traversal blocked", "Keep"],
                ["S3", "OK", "Finance / partner / self-or-office gates", "Keep"],
                ["S4", "Fixed", "Advance pending visible to employees", "Hidden; gate=ok for hide_money"],
                ["S5", "Fixed", "PWA + Downloads too wide", "Admin+HR only"],
                ["S6", "Med", "JWT in localStorage (XSS)", "Escape HTML; CSP later"],
                ["S7", "Med", "No login rate limit", "nginx limit_req recommended"],
                ["S8", "Med", "12h access token", "Shorten in prod if desired"],
                ["S9", "Ops", "Updater not code-signed yet", "HTTPS allowlist MVP; keys later"],
            ],
            w,
        ),
        Paragraph("Sensitive data map", st["h1"]),
        bullets(
            [
                "Client $ / invoices / Advance badges — Admin + Manager only.",
                "Partner shares — named admin partners only.",
                "Screenshots — office or self; audited when audit=1.",
                "Downloads binaries — Admin/HR distribute Agent to staff.",
                "Never wipe /var/lib/ems/ems.db or Agent agent_data/.",
            ],
            st,
        ),
    ]
    build(OUT / "02-Security-Audit-Report.pdf", "EMS Security", story)


def pdf_hostinger():
    st = styles()
    story = cover(
        "Hostinger / VPS Deploy",
        "Production https://ems.cfsdesigners.com — never wipe ems.db.",
    ) + [
        Paragraph("Deploy order", st["h1"]),
        Paragraph(
            "cd /opt/ems-src<br/>"
            f"git fetch && git checkout {BRANCH} && git pull<br/>"
            "cd apps/web && npm ci && npm run build && cp -r dist/* /var/www/ems/<br/>"
            "# upload Manager Setup + Agent zip → /var/www/ems/downloads/<br/>"
            "systemctl restart ems-api",
            st["code"],
        ),
        bullets(
            [
                f"Bump LATEST_MANAGER_VERSION / LATEST_AGENT_VERSION to {PACK_VERSION} / {AGENT_VERSION} before ship.",
                "Confirm Downloads page as Admin; employee must not see nav link.",
                "Smoke: staff My Projects has no Advance pending badge.",
            ],
            st,
        ),
        Paragraph("Rollback without data loss", st["h1"]),
        Paragraph(
            "git checkout PREVIOUS_GOOD && rebuild web && restart ems-api<br/>"
            "# Keep ems.db + screenshots untouched",
            st["code"],
        ),
    ]
    build(OUT / "03-Hostinger-VPS-Deploy.pdf", "EMS Hostinger", story)


def pdf_local():
    st = styles()
    story = cover(
        "Local Run & Smoke Test",
        "Windows PowerShell · Desktop + API + notify Test sound.",
    ) + [
        Paragraph("Start", st["h1"]),
        Paragraph(
            "cd apps/api → venv → uvicorn app.main:app --reload --port 8000<br/>"
            "cd apps/web → npm run tauri:dev   # or npm run dev",
            st["code"],
        ),
        Paragraph("Smoke (30 min)", st["h1"]),
        table(
            ["#", "Action", "Expect"],
            [
                ["1", "Admin Dashboard Past 7 days", "Aligned N updates column"],
                ["2", "Bell → Test sound", "Soft beep"],
                ["3", "Employee My Projects", "No Advance pending"],
                ["4", "Employee nav", "No Downloads"],
                ["5", "Admin/HR nav", "Downloads visible"],
                ["6", "Staff save My %", "Admin dropdown updates"],
            ],
            [12 * mm, 70 * mm, 92 * mm],
        ),
    ]
    build(OUT / "04-Local-Run-and-Smoke-Test.pdf", "EMS Local", story)


def pdf_breakfix():
    st = styles()
    story = cover(
        "Break / Fix Runbook",
        "Repair production without wiping DB or enroll data.",
    ) + [
        table(
            ["Symptom", "Fix"],
            [
                ["Staff still sees Advance pending", "Pull API+web; hard refresh; confirm hide_money gate=ok"],
                ["No notify sound", "Bell → Test sound; click app once first (WebView2)"],
                ["Updates column misaligned", "Confirm latest CSS; hard refresh"],
                ["502 after deploy", "journalctl -u ems-api; SECRET_KEY ≥32; restart"],
                ["Agent enroll lost after update", "CRITICAL — robocopy must /XF config.json; restore backup"],
                ["Tiny Download zip (~2KB)", "SPA HTML served — upload real binary to /downloads/"],
            ],
            [70 * mm, 104 * mm],
        ),
    ]
    build(OUT / "05-Break-Fix-Runbook.pdf", "EMS Break Fix", story)


def pdf_autoupdate():
    st = styles()
    story = cover(
        "Click → Background Auto-Update (Honest)",
        "What ships today vs what is still ops / signing.",
    ) + [
        Paragraph("Short answer", st["h1"]),
        Paragraph(
            "<b>YES — click-to-background update exists</b> (Phase E MVP) for "
            f"<b>Manager Desktop v{PACK_VERSION}</b> and <b>Agent v{AGENT_VERSION}</b>. "
            "It is <b>not</b> silent force-update without user click. "
            "User sees “Update available” → clicks → download + install runs in background → app relaunches.",
            st["body"],
        ),
        Paragraph("Does it wipe data / sensitive info?", st["h1"]),
        table(
            ["Layer", "Touched?", "Safe by design?"],
            [
                ["Server ems.db / screenshots / invoices", "Never", "Yes — update is local PC only"],
                ["Agent config.json (enroll token)", "Preserved (/XF)", "Yes if robocopy path used"],
                ["Agent agent_data / outbox", "Preserved (no mirror delete)", "Yes"],
                ["Manager local settings", "Installer currentUser", "Yes — no server wipe"],
            ],
            [55 * mm, 40 * mm, 79 * mm],
        ),
        Paragraph("Security posture (honest risk)", st["h1"]),
        bullets(
            [
                "<b>Safe enough for office</b> when downloads are HTTPS on ems.cfsdesigners.com and Tauri/Agent host-allowlist blocks other hosts.",
                "<b>Not</b> full big-tech signed updater yet (Authenticode / Tauri plugin-updater keys) — that is docs/64 optional next.",
                "Risk if someone MITMs DNS and you somehow bypass HTTPS: mitigated by TLS + allowlist. Do not point Agents at HTTP.",
                "First office install of this version is still manual once; later bumps use the banner.",
            ],
            st,
        ),
        Paragraph("Client install → later updates", st["h1"]),
        bullets(
            [
                "Day 0: Admin installs Manager Setup + gives staff Agent zip.",
                "Day N: bump versions on VPS + upload new binaries → enrolled apps show banner.",
                "User clicks Update → background install → relaunch. No DB wipe. No screenshot delete.",
            ],
            st,
        ),
        Paragraph(
            "Verdict: <b>Not risky for server/client data</b> if you follow the preserve-config design. "
            "Remaining risk is binary authenticity until code-signing keys are added.",
            st["body"],
        ),
    ]
    build(OUT / "06-Click-Background-Auto-Update.pdf", "EMS Auto-Update", story)


def pdf_master_prompt():
    st = styles()
    story = cover(
        "Master EMS AI Build Prompt (Top 1%)",
        "Paste this into a strong coding AI to rebuild a production-grade CFS-style EMS in one program. "
        "Derived from CFS Designers latest docs + shipped behavior.",
    ) + [
        Paragraph("How to use", st["h1"]),
        Paragraph(
            "Copy the PROMPT block below into Cursor / Claude / GPT. Attach empty repo or greenfield. "
            "Say: follow the prompt exactly; do not invent other industries; no DB wipe scripts in prod.",
            st["body"],
        ),
        Paragraph("════════════ PROMPT START ════════════", st["h2"]),
        Paragraph(
            "<b>Role:</b> You are a principal engineer + senior product designer (30+ years) shipping a "
            "<b>Cold Formed Steel / LGS studio EMS</b> for a company like CFS Designers. "
            "Not civil roads/bridges. Markets: US/AU/global; office Islamabad. Brand: Black + Gold + White, "
            "Playfair + Nunito. Ship production-ready: secure, fast, reusable, visually finished.",
            st["prompt"],
        ),
        Paragraph(
            "<b>Product one-liner:</b> Workforce attendance + screenshots (PC Agent) + office Manager "
            "(Desktop Tauri + Web) + CFS project pipeline + soft payment gate + invoices + partner shares + "
            "daily/monthly PDFs + office notify bell. Phone = Admin/HR glance PWA only — never employee punch.",
            st["prompt"],
        ),
        Paragraph("<b>Stack (lock):</b>", st["prompt"]),
        bullets(
            [
                "API: Python 3.11+, FastAPI, SQLAlchemy async, SQLite (prod path durable), JWT (user + device typ), bcrypt, reportlab PDFs.",
                "Web/Desktop: React + TypeScript + Vite; same UI in Tauri 2 Desktop Manager.",
                "Agent: Python PySide6 + PyInstaller zip; enroll code; Sign In/Out/Break; idle; multi-monitor JPEG screenshots; offline outbox.",
                "Deploy: nginx + systemd on VPS (Hostinger-class); HTTPS only; OpenAPI disabled in prod.",
            ],
            st,
        ),
        Paragraph("<b>Roles & authorization (non-negotiable):</b>", st["prompt"]),
        bullets(
            [
                "admin / manager = finance ($ invoices, Advance/Deposit badges, payment soft-gate UI).",
                "hr = office ops, Live/Day/Employees/Projects/Expenses/Reports; NO payment $; NO Advance badges.",
                "employee = own Day, assigned projects, My % progress; NO Downloads nav; NO payment wording; gate field blanked in API.",
                "demo = isolated tour; never mix real client money.",
                "Partner shares = named admin partners only.",
                "Screenshots/Day of others = office roles or self only; path traversal blocked under data_dir.",
            ],
            st,
        ),
        Paragraph("<b>Core feature modules (build all):</b>", st["prompt"]),
        bullets(
            [
                "Auth login/logout; employee CRUD; enroll codes for Agent devices.",
                "Live presence + Day timeline + activity buckets + screenshot lightbox + audit on view.",
                "Dashboard: presence, week hours charts, roster, end-of-day % today + Past 7 days grouped by employee accordion (aligned meta column).",
                "Staff home: attendance trends (work-day avg), assigned work scroll + hide finished, personal monthly PDF.",
                "Projects Kanban phases: Intake → Prelim Design → Prelim Eng → Final Eng → Stamped → Field → Run. Soft gate leaving Intake without Paid deposit (notify admin); HARD lock Stamped/Field/Run until finance clears.",
                "Payments / invoices PDF parity; expenses; partner share ledger with FX.",
                "Office notification center: bell, unread badge, mark read, soft chime after user-gesture audio unlock; Test sound button.",
                "Reports: professional daily + monthly PDFs (no blank orphan pages; charts ≤ content width).",
                "Downloads page: Admin/HR only — Manager Setup + Agent zip.",
                "Admin/HR PWA install banner on HTTPS; SW must never cache /api.",
                "Click→background update MVP: version endpoint; Agent zip apply preserving config.json + agent_data; Manager silent Setup /S; never touch server DB.",
            ],
            st,
        ),
        Paragraph("<b>UI / UX bar:</b>", st["prompt"]),
        bullets(
            [
                "Finished spacing/type/contrast; dark + light themes; gold accents; no purple-AI cliché.",
                "Desktop-first Manager; responsive but not a toy. Kanban usable on wide monitors.",
                "Empty states, loading, toasts, confirm deletes. Keyboard focus visible.",
                "Sensitive badges never shown to non-finance. Client names masked to initials for staff where required.",
            ],
            st,
        ),
        Paragraph("<b>Security / production (big-tech bar):</b>", st["prompt"]),
        bullets(
            [
                "Refuse weak SECRET_KEY; EMS_ENV=production disables sample seed; security headers (nosniff, DENY frame, Permissions-Policy).",
                "CORS allowlist exact origins (web + Tauri). Prepared statements / ORM only.",
                "Upload MIME allowlist + size caps + random names; no PHP/exec in upload trees.",
                "Rate-limit login at reverse proxy; short-lived tokens preferred; no secrets in git.",
                "Updater: HTTPS host allowlist now; plan Authenticode / signed Tauri updater next.",
                "Retention job for old screenshots; audit log for sensitive views.",
                "Never ship destructive “reset DB” in production paths.",
            ],
            st,
        ),
        Paragraph("<b>NFR:</b>", st["prompt"]),
        bullets(
            [
                "Timezone Asia/Karachi for work dates; utf8mb4/sqlite unicode safe.",
                "Admin save/upload feels responsive; lazy images; paginate large lists.",
                "SEO N/A for private EMS; still semantic HTML + a11y labels.",
            ],
            st,
        ),
        Paragraph("<b>Delivery order:</b>", st["prompt"]),
        bullets(
            [
                "1) API auth + employees + Agent enroll/heartbeat/screenshots.",
                "2) Manager Live/Day/Reports PDFs.",
                "3) Projects + soft/hard payment gate + Payments.",
                "4) Desktop Tauri shell + Agent packaging.",
                "5) Notify + PWA Admin/HR + click-update.",
                "6) Ops docs: QA matrix, security audit, deploy, break/fix, auto-update honesty.",
            ],
            st,
        ),
        Paragraph("<b>Definition of done:</b>", st["prompt"]),
        bullets(
            [
                "Role matrix tested; employee cannot see Advance pending or Downloads.",
                "One Agent full day cycle; one Admin phone PWA; PDFs clean; notify Test sound works.",
                "Update click preserves enroll; server DB untouched.",
                "STATUS.md + version bump (Manager + Agent + API latest) in sync.",
            ],
            st,
        ),
        Paragraph("<b>Out of scope unless asked:</b> marketplace SaaS, public client portal v1, employee mobile punch, roads/geotech modules.", st["prompt"]),
        Paragraph("════════════ PROMPT END ════════════", st["h2"]),
        PageBreak(),
        Paragraph("Companion checklist (what “big tech ready” adds later)", st["h1"]),
        bullets(
            [
                "SSO/OIDC, hardware-backed session store, CSP + Trusted Types.",
                "Signed binaries + SBOM + vulnerability scanning in CI.",
                "Immutable audit warehouse; SOC2-style access reviews.",
                "Multi-region backups; PITR; chaos drills for Agent update.",
                "Feature flags; canary Desktop builds.",
            ],
            st,
        ),
        Paragraph(
            f"This prompt mirrors CFS EMS pack v{PACK_VERSION} / Agent {AGENT_VERSION} on branch {BRANCH}.",
            st["body"],
        ),
    ]
    build(OUT / "07-Master-EMS-AI-Build-Prompt.pdf", "EMS Master AI Prompt", story)


def main():
    pdf_index()
    pdf_qa()
    pdf_security()
    pdf_hostinger()
    pdf_local()
    pdf_breakfix()
    pdf_autoupdate()
    pdf_master_prompt()
    print("Done", OUT)


if __name__ == "__main__":
    main()
