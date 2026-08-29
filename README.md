# CFS Designers - Employee Management System (EMS)

**Complete EMS + Invoice Management** for Cold Formed Steel (LGS) design office.

---

## 🎯 What This Software Does

**CFS EMS** manages:
1. **Employee attendance** — clock in/out, break tracking, screenshots
2. **Project workflow** — CFS/LGS jobs with payment gates, phases, audit logs
3. **Professional invoices** — multi-line items, custom colors, PDF generation
4. **Payment tracking** — deposits, balance, status, Excel export

**Built for:** CFS Designers (Islamabad-based, serving US/AUS clients)

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend (API)** | Python 3.11, FastAPI, SQLAlchemy, Pydantic |
| **Frontend (Web)** | React 18, TypeScript, Vite |
| **Desktop Agent** | Python, Pillow (screenshots), psutil (activity) |
| **Database** | SQLite (dev/local), PostgreSQL-ready |
| **PDF** | ReportLab (custom invoice templates) |
| **Deployment** | VPS (Hostinger KVM / DigitalOcean / Oracle Cloud) |

---

## ✨ Key Features

### 1. **Employee Attendance (Agent + Web)**
- Desktop agent: auto clock-in, screenshot every 5 min, activity tracking
- Manager view: live dashboard, session timelines, idle detection
- Manual overrides: manager can fix punches with audit trail

### 2. **Project Management**
- **Payment gates** — blocks work if deposit not received
- **Phases** — intake → design → engineering → stamped → field files
- **Client-linked** — auto-fill invoice details from client records
- **Audit log** — every project change tracked (who, what, when)

### 3. **Professional Invoices**
- **Multi-line items** — description, qty, rate, auto-calculate total
- **Editable bill-to** — client name/location/phone per invoice
- **Template settings** — company info, bank details, color customization
- **PDF export** — matches client invoice (Georgia/Arial, green header, yellow Detailing, red unpaid budget cells)
- **Status tracking** — proforma, sent, pending, paid, overdue
- **Excel export** — payment tracking list for analysis

### 4. **Security & Validation**
- **Auth** — manager/admin/employee roles, JWT tokens
- **Input validation** — frontend + backend (Pydantic models)
- **Prepared statements** — no SQL injection (SQLAlchemy)
- **Audit trail** — sensitive project actions logged
- **Error handling** — graceful degradation, user-friendly messages

---

## 📂 Project Structure

```
D:\imp\ems-cfs-designers\
├── apps/
│   ├── api/                 # FastAPI backend
│   │   ├── app/
│   │   │   ├── routers/     # API endpoints (auth, projects, payments, etc.)
│   │   │   ├── services/    # Business logic (PDF, Excel, invoice items, etc.)
│   │   │   ├── models.py    # SQLAlchemy ORM models
│   │   │   ├── schemas.py   # Pydantic request/response models
│   │   │   ├── auth.py      # JWT + password hashing
│   │   │   └── main.py      # FastAPI app entry
│   │   ├── .env             # SECRET_KEY, DB_URL, SMTP credentials
│   │   └── requirements.txt
│   ├── web/                 # React frontend
│   │   ├── src/
│   │   │   ├── pages/       # PaymentsPage, ProjectsPage, LivePage, etc.
│   │   │   ├── components/  # Reusable UI (CurrencySelect, ConfirmDialog, etc.)
│   │   │   ├── api.ts       # API client functions
│   │   │   └── styles.css   # Global + component styles
│   │   └── package.json
│   └── agent/               # Desktop employee agent (Windows/macOS/Linux)
│       ├── agent.py         # Screenshot + activity tracker
│       └── INSTALL-AGENT.bat
├── START-EMS.bat            # Launch API + Web (2 windows)
├── RUN-API.bat              # Start API only (production mode)
├── RUN-WEB.bat              # Start Web only (Vite dev server)
└── README.md                # This file
```

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- **Python 3.11+** — [Download](https://www.python.org/downloads/)
- **Node.js 18+** — [Download](https://nodejs.org/)
- **Git** — for cloning repo

### 1. Clone & Setup

```bash
cd D:\imp\ems-cfs-designers\apps\api
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt

cd ..\web
npm install
```

### 2. Configure `.env` (API folder)

```env
SECRET_KEY=your-32-char-secret-key-here
DATABASE_URL=sqlite:///./data/ems.db
BREVO_API_KEY=your-brevo-key-here
AUTO_SEED_SAMPLES=true
```

Generate secret key:
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Start Services

**Option A — Both services (recommended)**
```bash
D:\imp\ems-cfs-designers\START-EMS.bat
```

**Option B — Separate terminals**
```bash
# Terminal 1 (API)
cd D:\imp\ems-cfs-designers\apps\api
.\.venv\Scripts\uvicorn app.main:app --port 8000 --reload

# Terminal 2 (Web)
cd D:\imp\ems-cfs-designers\apps\web
npm run dev
```

### 4. Access

- **Web UI**: http://127.0.0.1:5173
- **API docs** (disabled in prod): http://127.0.0.1:8000/docs
- **API health**: http://127.0.0.1:8000/api/v1/health

**Default login** (if AUTO_SEED_SAMPLES=true):
- Email: `admin@example.com`
- Password: `admin123`

---

## 📋 Invoice System Usage

### **Invoices** Tab

1. **Create invoice**:
   - Click **"+ New invoice"**
   - Select client (bill-to auto-fills)
   - Add line items: description, qty, rate
   - Set date, status, notes
   - **Save** → PDF generated automatically

2. **Edit invoice**:
   - Click any invoice row → form opens
   - Modify fields
   - **Save** → PDF updates

3. **View/Download PDF**:
   - **View** — opens in browser
   - **PDF** — downloads to disk
   - **Delete** — removes invoice (with confirmation)

4. **Excel export**:
   - **Download Excel** — payment tracking list

### **Template Settings** Tab

Configure once, applies to all future invoices:

1. **Company info** — name, address, phone, email (top of invoice)
2. **Bank details** — account number, routing, Swift, bank address (bottom)
3. **Contact footer** — name, email, thank-you message
4. **Invoice colors** — table header & highlight (custom branding)

Changes take effect immediately on next PDF generation.

---

## 🎨 Customization

### Invoice Colors

1. Go to **Invoice template settings**
2. Scroll to **"Invoice colors (PDF styling)"**
3. Click color picker or enter hex code:
   - **Table header** — default `#92D050` (Excel green, matches client PDF)
   - Name / headings on PDF are fixed copper (`#A85914`) like the reference
4. **Save** → table header color applies to future PDFs

### Line Items

- Add unlimited rows (max 50 enforced server-side)
- Auto-calculates total
- Validates line items (area/rate can be numbers or text like `LumpSum`)
- Empty lines ignored on save

---

## 🛡️ Security Best Practices

### Production Deployment

1. **Change SECRET_KEY** — use strong 32+ char random string
2. **HTTPS only** — no plain HTTP in production
3. **Firewall** — only expose port 443 (HTTPS)
4. **Backup database** — regular snapshots of `data/ems.db`
5. **Update dependencies** — `pip install --upgrade` regularly
7. **Screenshot retention** — `SCREENSHOT_RETENTION_DAYS=60` (auto-delete after 60 days)
8. **`AUTO_SEED_SAMPLES=false`** on the live server — no demo `Admin123!` seed in production

### Environment Variables

**Never commit** `.env` to git:
```bash
# .gitignore already includes:
.env
*.db
uploads/
logs/
```

---

## 📊 Database Schema (Key Tables)

| Table | Purpose |
|-------|---------|
| `employees` | Staff records, roles, passwords (hashed) |
| `devices` | Employee desktop agents, tokens |
| `punches` | Clock in/out, break in/out events |
| `clients` | Client name, location, phone, notes |
| `projects` | CFS jobs, phases, payment gates, audit logs |
| `invoices` | Invoice header (number, dates, status, bill-to) |
| `invoice_settings` | Singleton — company/bank/color template |

**Line items** stored as JSON in `invoices.line_items` column.

---

## 🔧 Troubleshooting

### Port 8000 already in use

```powershell
netstat -ano | findstr ":8000"
taskkill /F /PID <pid>
```

Or use `RUN-API.bat` which auto-kills old processes.

### Validation error on invoice save

**Check:**
1. Line items have non-empty descriptions
2. Qty > 0, price >= 0
3. Browser console (`F12`) for detailed error
4. API logs in terminal

### PDF not generating

**Verify:**
1. `data/reports/` folder exists (auto-created)
2. ReportLab installed: `.\.venv\Scripts\pip show reportlab`
3. Invoice template saved (default values loaded on first access)

### Fresh start

```powershell
# Delete DB + recreate
del D:\imp\ems-cfs-designers\apps\api\data\ems.db
# Restart API — auto-seeds if AUTO_SEED_SAMPLES=true
```

---

## 🚢 Production Deployment

### Recommended Stack

| Component | Provider | Cost | Why |
|-----------|----------|------|-----|
| **VPS** | Hostinger KVM 1 / DigitalOcean $6 | ~$5/mo | Full control, no vendor lock-in |
| **Domain** | GoDaddy | ~$15/yr | Professional branding |
| **SSL** | Let's Encrypt (free) | $0 | HTTPS encryption |
| **Backup** | Daily snapshots | Included | Data safety |

### Steps (Ubuntu VPS)

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Python 3.11 + Node 18
sudo apt install python3.11 python3.11-venv nodejs npm -y

# 3. Clone repo
git clone <your-repo-url>
cd ems-cfs-designers

# 4. Setup API
cd apps/api
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 5. Setup Web (build static files)
cd ../web
npm install
npm run build

# 6. Configure systemd service (API)
sudo nano /etc/systemd/system/ems-api.service
```

**Service file:**
```ini
[Unit]
Description=CFS EMS API
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/ems-cfs-designers/apps/api
Environment="PATH=/path/to/ems-cfs-designers/apps/api/.venv/bin"
ExecStart=/path/to/ems-cfs-designers/apps/api/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 7. Start service
sudo systemctl enable ems-api
sudo systemctl start ems-api

# 8. Setup nginx reverse proxy
sudo apt install nginx -y
sudo nano /etc/nginx/sites-available/ems

# Add proxy config (HTTPS + Let's Encrypt)
# Point to: proxy_pass http://127.0.0.1:8000

# 9. Enable site
sudo ln -s /etc/nginx/sites-available/ems /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 10. SSL certificate
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d ems.cfsdesigners.com
```

**Done!** Access at `https://ems.cfsdesigners.com`

---

## 📝 API Endpoints (Key Routes)

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/api/v1/login` | Public | Employee login (JWT) |
| GET | `/api/v1/live` | Manager | Live employee dashboard |
| GET | `/api/v1/projects` | Manager | List all projects |
| POST | `/api/v1/projects` | Manager | Create project |
| PATCH | `/api/v1/projects/{id}` | Manager | Update project |
| GET | `/api/v1/invoices` | Manager | List all invoices |
| POST | `/api/v1/invoices` | Manager | Create invoice |
| GET | `/api/v1/invoices/{id}/pdf` | Manager | Generate PDF |
| GET | `/api/v1/invoice-settings` | Manager | Get template config |
| PATCH | `/api/v1/invoice-settings` | Manager | Update template |
| GET | `/api/v1/reports/payments.xlsx` | Manager | Excel export |

**All manager routes** require `Authorization: Bearer <token>` header.

---

## 🆘 Support & Maintenance

### Common Issues

1. **Forgot admin password** → Delete DB, restart API (auto-seeds)
2. **Invoice won't save** → Check browser console + API logs for validation errors
3. **PDF blank/broken** → Verify invoice template settings saved
4. **Agent won't connect** → Check `DEVICE_TOKEN` in agent config

### Logs

- **API** — terminal output (or systemd journal: `sudo journalctl -u ems-api -f`)
- **Browser** — F12 → Console tab
- **Agent** — `logs/agent.log` (if configured)

---

## 🎓 Development Notes

### Adding New Invoice Fields

1. **Model** (`models.py`):
   ```python
   new_field: Mapped[str] = mapped_column(String(100), default="")
   ```

2. **Schema patch** (`schema_patch.py`):
   ```python
   INVOICE_COLS["new_field"] = "VARCHAR(100) DEFAULT ''"
   ```

3. **Schema** (`schemas.py`):
   ```python
   class InvoiceIn(BaseModel):
       new_field: str = Field("", max_length=100)
   ```

4. **Frontend** (`PaymentsPage.tsx`):
   ```tsx
   <input value={form.new_field} onChange={...} />
   ```

5. Restart API + hard-refresh browser

### Testing

```bash
# API tests (if written)
cd apps/api
.\.venv\Scripts\pytest

# Frontend build check
cd apps/web
npm run build
```

---

## 📄 License & Credits

**Built for:** CFS Designers (Islamabad, Pakistan)  
**Purpose:** Internal EMS + invoicing (not for resale)  
**Stack:** FastAPI, React, ReportLab, SQLAlchemy, Vite  
**Deployment:** Self-hosted VPS (Hostinger/DigitalOcean/Oracle)

**No third-party invoice SaaS** — full ownership, no recurring fees, complete data control.

---

## 🔄 Version History

| Version | Date | Changes |
|---------|------|---------|
| **v1.0** | Aug 2026 | Initial release — attendance, projects, basic invoices |
| **v1.1** | Aug 2026 | Multi-line invoices, custom colors, template settings |
| **v1.2** | Aug 2026 | Enhanced validation, UI polish, full-width notes |

---

## 📞 Contact

**Questions?** → `cfsdesigners@gmail.com`  
**Issues?** → Check troubleshooting section first, then contact admin.

---

**Built with 💛 for CFS Designers** — Custom EMS + invoice system, no vendor lock-in, full control.
