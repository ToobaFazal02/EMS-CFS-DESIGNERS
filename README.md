# CFS Designers — Phase 1

Windows agent + FastAPI + React manager dashboard.

## Quick start (dev)

### 1. API

```bash
cd apps/api
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m app.seed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Default manager: `admin@cfsdesigners.com` / `Admin123!`  
API docs: http://127.0.0.1:8000/docs

### 2. Web

```bash
cd apps/web
npm install
npm run dev
```

Open http://127.0.0.1:5173

### 3. Agent

```bash
cd apps/agent
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy config.example.json config.json
python -m ems_agent
```

Enroll device from manager web (Employees → Enroll) or use seed device token in `config.json`.

## Theme

Black · Yellow/Gold · White — see `docs/14-ui-theme.md`.
