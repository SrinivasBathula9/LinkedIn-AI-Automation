# LinkedIn AI Automation Platform

> **Production-grade, enterprise-ready AI system for scaling LinkedIn network growth via intelligent, safe, and targeted connection requests.**

Built by [Srinivas Bathula](https://github.com/SrinivasBathula9) — AI & Platform Engineering

---

## Overview

This platform automates targeted LinkedIn connection requests using AI classification, relevance scoring, and safe browser automation. It replaces manual outreach with a fully governed, scheduled pipeline that respects LinkedIn's rate limits and simulates human behavior to avoid detection.

### What it does

- Scrapes LinkedIn's "My Network → Grow" page for connection suggestions
- Classifies each profile using a local ML model (sentence-transformers + logistic regression)
- Scores profiles 0–100 across role match, region, seniority, activity, and network proximity
- Generates personalized connection notes using a local LLM (Ollama / Mistral)
- Sends connection requests via stealth Playwright automation with human-like delays
- Runs on a region-aware schedule (9 AM and 7 PM local time per region)
- Displays real-time stats and activity on a React dashboard

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      LINKEDIN AUTOMATION PLATFORM                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │  React       │    │  FastAPI     │    │  AI Engine           │   │
│  │  Dashboard   │◄──►│  Backend     │◄──►│  Classifier +        │   │
│  │  (Analytics) │    │  (REST API)  │    │  Scorer + LLM        │   │
│  └──────────────┘    └──────┬───────┘    └──────────────────────┘   │
│                             │                                         │
│                    ┌────────▼────────┐                               │
│                    │  APScheduler    │  Region-aware cron jobs        │
│                    │  (6 regions ×   │  9 AM + 7 PM local time       │
│                    │   2 windows)    │                               │
│                    └────────┬────────┘                               │
│                             │                                         │
│                    ┌────────▼────────┐    ┌──────────────────────┐  │
│                    │  Playwright     │◄──►│  LinkedIn Profile    │  │
│                    │  Browser Agent  │    │  Scraper             │  │
│                    └────────┬────────┘    └──────────────────────┘  │
│                             │                                         │
│              ┌──────────────┼──────────────┐                         │
│         ┌────▼────┐   ┌────▼────┐   ┌─────▼────┐                   │
│         │PostgreSQL│   │  Redis  │   │  Qdrant  │                   │
│         │(Primary) │   │(Queue/  │   │(Vector   │                   │
│         │          │   │ Cache)  │   │ Store)   │                   │
│         └──────────┘   └─────────┘   └──────────┘                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI + Uvicorn (async Python) |
| **Browser Automation** | Playwright (Python, async) + stealth patches |
| **AI / NLP** | sentence-transformers `all-MiniLM-L6-v2` + scikit-learn |
| **Local LLM** | Ollama (`mistral:7b` or `llama3:8b`) |
| **Task Queue** | Celery + Redis |
| **Scheduler** | APScheduler (region-aware timezone crons) |
| **Primary DB** | PostgreSQL + SQLAlchemy async |
| **Vector DB** | Qdrant (profile similarity + deduplication) |
| **Cache** | Redis |
| **Frontend** | React + TailwindCSS + Recharts + TanStack Query |
| **Containers** | Docker + Docker Compose |
| **Monitoring** | Prometheus + Grafana |

---

## Features

### AI Engine
- **Profile Classifier** — Binary relevance classification using fine-tuned sentence-transformers embeddings + logistic regression head
- **Relevance Scorer** — Multi-dimension 0–100 score: role match (35%), region (20%), seniority (20%), activity (15%), network proximity (10%)
- **Message Personalizer** — Generates personalized ≤280-char connection notes via local Ollama LLM (zero API cost, fully private)

### Automation & Safety
- **Human-like behavior** — Randomized delays (normal distribution), mouse movements, variable scroll depth
- **Session warm-up** — Browses feed 30–60 sec before sending requests
- **Anti-ban circuit breaker** — Detects LinkedIn restriction signals, pauses 24h automatically
- **Daily limits** — 20 requests/region/day, 10/session (configurable)
- **Session persistence** — Reuses authenticated cookies to avoid repeated logins
- **Exponential backoff** — On any 429 or restriction signal

### Scheduler (Region-Aware)
Fires campaigns at local morning and evening windows across 6 regions:

| Region | Timezone | Windows |
|--------|----------|---------|
| SG | Asia/Singapore | 9:00 AM, 7:00 PM |
| IN | Asia/Kolkata | 9:00 AM, 7:00 PM |
| UK | Europe/London | 9:00 AM, 7:00 PM |
| EU | Europe/Berlin | 9:00 AM, 7:00 PM |
| US | America/New_York | 9:00 AM, 7:00 PM |
| UAE | Asia/Dubai | 9:00 AM, 7:00 PM |

### React Dashboard
- **Live KPI cards** — Sent today / week / month, accepted, pending, failed
- **Real-time activity feed** — WebSocket-driven event stream (campaign start/done, connection sent, restrictions)
- **Daily chart** — Sent vs accepted over 30 days (Recharts)
- **Campaign manager** — Create, edit, pause/resume, delete campaigns with multi-region selection
- **Profile queue** — Upcoming profiles with relevance scores and manual override
- **Auto-refresh** — Polls every 10s for stats, instant update via WebSocket cache invalidation

---

## Target Roles & Regions

**Roles**: CEO, CTO, COO, CIO, HR Recruiters, HR Managers, AI Architects, Platform Engineers, Cloud Solution Engineers, AI/ML Engineers, Job Consulting Agencies

**Regions**: Singapore, India, UK, Europe, USA, UAE

---

## Project Structure

```
linkedin-automation/
├── backend/
│   ├── main.py                   # FastAPI app + scheduler startup
│   ├── config.py                 # Pydantic settings from .env
│   ├── api/
│   │   ├── routes/
│   │   │   ├── campaigns.py      # CRUD + update endpoint
│   │   │   ├── stats.py          # Overview + daily KPIs
│   │   │   ├── profiles.py       # Queue + manual skip
│   │   │   └── logs.py           # Automation event log
│   │   └── websocket.py          # Real-time activity broadcast
│   ├── ai/
│   │   ├── classifier.py         # sentence-transformers + logistic regression
│   │   ├── scorer.py             # Multi-dimension relevance scorer
│   │   ├── embedder.py           # Local embeddings
│   │   └── personalizer.py      # Ollama message generation
│   ├── automation/
│   │   ├── browser_agent.py      # Playwright campaign runner
│   │   ├── scraper.py            # LinkedIn profile extractor
│   │   ├── session_manager.py    # Cookie persistence + login
│   │   └── anti_ban.py           # Rate limiter + circuit breaker
│   ├── scheduler/
│   │   ├── scheduler.py          # APScheduler job registration
│   │   └── job_registry.py       # Region/timezone definitions
│   ├── db/
│   │   ├── models.py             # SQLAlchemy ORM models
│   │   ├── session.py            # Async session factory
│   │   └── migrations/           # Alembic migrations
│   └── queue/
│       ├── celery_app.py         # Celery broker config
│       └── tasks.py              # Async task definitions
│
├── frontend/
│   └── src/
│       ├── pages/                # Dashboard, Campaigns, Analytics, Settings
│       ├── components/           # StatCard, ActivityFeed, Charts
│       └── api/client.js         # Axios + WebSocket helpers
│
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml        # Full stack: PG, Redis, Qdrant, Ollama
│
├── references/                   # Implementation references
├── .env.example
└── requirements.txt
```

---

## Quick Start

### Prerequisites
- Docker + Docker Compose
- (For local dev) Python 3.11+, Node.js 18+

### 1. Clone and configure

```bash
git clone https://github.com/SrinivasBathula9/LinkedIn-AI-Automation.git
cd LinkedIn-AI-Automation
cp .env.example .env
# Edit .env — add LinkedIn credentials, set limits
```

### 2. Start infrastructure

```bash
docker compose up -d postgres redis qdrant ollama
```

### 3. Pull the LLM model

```bash
docker exec -it ollama ollama pull mistral:7b
```

### 4. Run database migrations

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
```

### 5. Start backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### 6. Start frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### 7. Create your first campaign

Open the dashboard → Campaigns → New Campaign → select target roles and regions → Create.

The scheduler will automatically fire at 9 AM and 7 PM in each selected region's local timezone.

---

## Operations Guide

### Docker — First-Time Setup

```bash
# 1. Build images (one-time, ~5 min — includes Playwright + Chromium)
docker compose -p linkedin -f docker/docker-compose.automation.yml build

# 2. Start containers
docker compose -p linkedin -f docker/docker-compose.automation.yml up -d

# 3. Run database migrations (one-time)
docker exec linkedin-backend-1 alembic upgrade head

# 4. Verify all 5 containers are up
docker ps --format "table {{.Names}}\t{{.Status}}"

# 5. Verify API is live
curl http://localhost:8000/health
# Expected: {"status":"ok","version":"1.0.0"}
```

### Docker — Daily Commands

```bash
# Start automation stack
docker compose -p linkedin -f docker/docker-compose.automation.yml up -d

# Stop automation stack
docker compose -p linkedin -f docker/docker-compose.automation.yml stop

# Restart backend only (after code changes — no rebuild needed)
docker restart linkedin-backend-1

# Restart celery worker
docker restart linkedin-celery_worker-1

# Rebuild after requirements.txt or Dockerfile changes
docker compose -p linkedin -f docker/docker-compose.automation.yml build
docker compose -p linkedin -f docker/docker-compose.automation.yml up -d
```

### Logs

```bash
# Backend logs (scheduler + API)
docker logs linkedin-backend-1
docker logs -f linkedin-backend-1            # follow live
docker logs --tail 50 linkedin-backend-1     # last 50 lines

# Celery worker logs
docker logs -f linkedin-celery_worker-1

# Filter: scheduler fires only
docker logs linkedin-backend-1 2>&1 | grep "Scheduled job\|APScheduler\|Job registered"

# Filter: errors only
docker logs linkedin-backend-1 2>&1 | grep -i "error\|exception\|failed"

# Startup log (written by Task Scheduler bat scripts)
type automation_startup.log
```

### Scheduler — Change Job Times

Edit `backend/scheduler/job_registry.py`:

```python
SCHEDULE_WINDOWS = [
    {"hour": 9,  "minute": 0},    # 9:00 AM local per region
    {"hour": 19, "minute": 0},    # 7:00 PM local per region
]
```

Then apply without rebuilding:
```bash
docker restart linkedin-backend-1
```

Verify jobs reloaded:
```bash
docker logs linkedin-backend-1 | grep "APScheduler started"
# Expected: APScheduler started  job_count=12
```

### Scheduler — Windows Task Scheduler Auto-Start

```
run_as_admin.bat          — register/update daily start tasks (run as Admin)
start_automation.bat      — manually start containers + schedule auto-stop
stop_automation.bat       — immediately stop all containers
```

Change auto-start times by editing `register_schedule_tasks.ps1`:
```powershell
$MorningStart = "08:55"    # 5 min before morning job window
$EveningStart = "23:15"    # 5 min before evening job window
```
Then re-run `run_as_admin.bat`.

### Database

```bash
# Run migrations
docker exec linkedin-backend-1 alembic upgrade head

# List tables
docker exec linkedin-postgres-1 psql -U user -d linkedin_db -c "\dt"

# Connect to psql
docker exec -it linkedin-postgres-1 psql -U user -d linkedin_db

# Useful queries
docker exec linkedin-postgres-1 psql -U user -d linkedin_db -c \
  "SELECT id, name, target_regions, is_active FROM campaigns;"

docker exec linkedin-postgres-1 psql -U user -d linkedin_db -c \
  "SELECT status, count(*) FROM connection_requests WHERE sent_at >= CURRENT_DATE GROUP BY status;"
```

### API Quick Tests

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/campaigns
curl http://localhost:8000/api/stats/overview
curl http://localhost:8000/api/logs?limit=10
```

---

## Configuration (`.env.example`)

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/linkedin_db
REDIS_URL=redis://localhost:6379/0

# LinkedIn Session (prefer cookie over password)
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=yourpassword
LINKEDIN_SESSION_COOKIE=    # paste cookie value for safer auth

# AI
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Vector DB
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=linkedin_profiles

# Automation Limits (stay within LinkedIn soft limits)
DAILY_LIMIT_PER_REGION=20
SESSION_LIMIT=10
MIN_DELAY_SECONDS=5
MAX_DELAY_SECONDS=12

# Dry run — set true to simulate without actually sending
DRY_RUN=false

# Alerts
SLACK_WEBHOOK_URL=
ALERT_EMAIL=
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/stats/overview` | Dashboard KPI totals |
| `GET` | `/api/stats/daily?days=30` | Daily sent/accepted chart data |
| `GET` | `/api/campaigns/` | List all campaigns |
| `POST` | `/api/campaigns/` | Create campaign |
| `PUT` | `/api/campaigns/{id}` | Update campaign (regions, roles, limits) |
| `PUT` | `/api/campaigns/{id}/toggle` | Pause / resume campaign |
| `DELETE` | `/api/campaigns/{id}` | Delete campaign |
| `GET` | `/api/profiles/queue` | Upcoming send queue |
| `POST` | `/api/profiles/skip/{id}` | Manually skip a profile |
| `GET` | `/api/logs/` | Recent automation events |
| `WS` | `/ws/activity` | Real-time event stream |

---

## Database Schema

```sql
campaigns           — name, target_roles[], target_regions[], daily_limit, is_active
profiles            — linkedin_url, full_name, title, company, location, region,
                      relevance_score, classifier_confidence
connection_requests — campaign_id, profile_id, status, message_sent, sent_at, accepted_at
daily_limits        — date, region, sent_count, accepted_count  (unique per day+region)
automation_logs     — event_type, message, metadata JSONB
```

---

## Docker Compose (Full Stack)

```bash
docker compose up -d
```

Services started:
- `backend` → http://localhost:8000
- `frontend` → http://localhost:3000
- `postgres` → localhost:5432
- `redis` → localhost:6379
- `qdrant` → http://localhost:6333
- `ollama` → http://localhost:11434
- `grafana` → http://localhost:3001

---

## Safety & Rate Limits

| Period | Limit |
|--------|-------|
| Per session | 10 requests |
| Per day per region | 20 requests |
| Weekly | ~100 requests |
| Monthly | ~400 requests |

**Safeguards built-in:**
- Automatic 24h pause on LinkedIn restriction detection
- CAPTCHA detection with alert notification
- One-by-one sends only (no bulk)
- Exponential backoff on any 429 signal
- Session persistence to avoid repeated logins
- All credentials encrypted, never logged

---

## Ethical & Legal Notice

> LinkedIn's Terms of Service prohibit scraping and automated actions.
> This system is intended **only** for personal professional networking by the account owner.
> It must **not** be commercialized as a SaaS for third-party LinkedIn accounts.
>
> Use responsibly. Stay within the rate limits. The daily caps are set well below LinkedIn's soft limits.

---

## Implementation Phases

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | FastAPI + DB + Docker Compose | ✅ Complete |
| 2 | AI Engine (Classifier + Scorer + Embedder) | ✅ Complete |
| 3 | Playwright Agent + Anti-ban + Scheduler | ✅ Complete |
| 4 | React Dashboard + Charts + WebSocket | ✅ Complete |
| 5 | Proxy integration + CAPTCHA alerts + hardening | 🔄 In Progress |
| 6 | AWS / Hetzner cloud deployment + monitoring | 📋 Planned |

---

## Author

**Srinivas Bathula** — AI & Platform Engineering
GitHub: [@SrinivasBathula9](https://github.com/SrinivasBathula9)

---

*Built with FastAPI · Playwright · React · sentence-transformers · Ollama · PostgreSQL · Redis · Qdrant*
