---
name: linkedin-automation
description: >
  Enterprise-grade AI-driven LinkedIn network automation system for targeted connection request
  campaigns. Use this skill whenever the user wants to automate LinkedIn outreach, build a
  connection automation pipeline, design an AI profile classifier for LinkedIn, create a scheduler
  for LinkedIn engagement, build a dashboard for connection analytics, or architect any
  LinkedIn growth automation system. Triggers on phrases like "LinkedIn automation", "auto connect",
  "connection request bot", "LinkedIn outreach system", "profile scoring for LinkedIn", or any
  request to scale LinkedIn network growth with AI. Always use this skill when the user asks
  about automating professional networking on LinkedIn — even if they only mention one component
  like "profile relevance scoring" or "anti-ban LinkedIn strategy".
---

# LinkedIn AI Automation System — CLAUDE.md

A production-grade, enterprise-ready AI automation skill for scaling LinkedIn network growth
via intelligent, safe, and targeted connection requests.

---

## 1. System Overview

### Goal
Automate targeted LinkedIn connection requests using AI classification, relevance scoring,
and safe browser automation — replacing manual outreach with a fully governed, scheduled pipeline.

### Target Roles
CEO, CTO, COO, CIO, HR Recruiters, HR Managers, AI Architects, Platform Engineers,
Cloud Solution Engineers, AI/ML Engineers, Job Consulting Agencies.

### Target Regions
Singapore, India, UK, Europe, USA, UAE.

### Scheduling Windows (local time of target region)
- Morning: 9:00 AM – 10:00 AM
- Evening: 7:00 PM – 9:00 PM

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      LINKEDIN AUTOMATION PLATFORM                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │  React       │    │  FastAPI     │    │  AI Engine           │   │
│  │  Dashboard   │◄──►│  Backend     │◄──►│  (Classifier +       │   │
│  │  (Analytics) │    │  (REST API)  │    │   Scorer + LLM)      │   │
│  └──────────────┘    └──────┬───────┘    └──────────────────────┘   │
│                             │                                         │
│                    ┌────────▼────────┐                               │
│                    │  Task Scheduler  │                               │
│                    │  (APScheduler)   │                               │
│                    └────────┬────────┘                               │
│                             │                                         │
│                    ┌────────▼────────┐    ┌──────────────────────┐  │
│                    │  Browser Agent   │◄──►│  LinkedIn Profile    │  │
│                    │  (Playwright)    │    │  Scraper             │  │
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

### Component Responsibilities

| Component | Role |
|-----------|------|
| React Dashboard | View metrics, manage campaigns, monitor queue |
| FastAPI Backend | REST API, orchestration, session management |
| AI Engine | Profile classification, relevance scoring, message personalization |
| APScheduler | Region-aware cron scheduling for connection windows |
| Playwright Agent | Safe browser automation — search, scroll, click |
| PostgreSQL | Primary relational store for profiles, campaigns, logs |
| Redis | Job queue (Celery), rate-limit counters, session cache |
| Qdrant | Vector embeddings for profile similarity and deduplication |

---

## 3. AI Components

### 3.1 Profile Classifier
**Purpose**: Binary classification — is a profile worth targeting?

**Input features**:
- Job title (NLP-normalized)
- Company name and industry
- Profile headline and summary
- Location / region
- Mutual connections count
- Recent activity signals (posts, comments)

**Model**: Fine-tuned `sentence-transformers/all-MiniLM-L6-v2` (open-source, runs locally)
with a lightweight XGBoost or logistic regression head.

**Output**: `{is_relevant: bool, confidence: float}`

**Training data**: Bootstrap with manually labeled LinkedIn profiles (~500 examples minimum),
then continuously label via user feedback from the dashboard.

---

### 3.2 Relevance Scorer
**Purpose**: Rank relevant profiles 0–100 for prioritization.

**Scoring dimensions**:
```python
score = (
    0.35 * role_match_score        # exact/fuzzy match to target roles
  + 0.20 * region_match_score      # target region alignment
  + 0.20 * seniority_score         # inferred from title keywords
  + 0.15 * activity_score          # recent LinkedIn activity
  + 0.10 * network_proximity_score # mutual connections
)
```

**Implementation**: Python scoring function + Qdrant ANN for deduplication
(skip profiles already connected or previously attempted).

---

### 3.3 Message Personalizer (Optional)
**Purpose**: Generate a personalized connection note (≤300 chars).

**LLM**: Use `Ollama` with `mistral:7b` or `llama3:8b` (fully local, zero API cost).

**Prompt template**:
```
You are a professional networking assistant.
Write a short LinkedIn connection note (max 280 chars) for:
- Sender: {sender_name}, {sender_title}
- Recipient: {recipient_name}, {recipient_title} at {company}
- Shared interest: {shared_topic}
Be concise, warm, and professional. No emojis. No generic phrases.
```

**Fallback**: Use pre-written template variants (A/B tested) if Ollama is unavailable.

---

## 4. Open-Source Tools & Frameworks

| Category | Tool | Reason |
|----------|------|--------|
| Backend | FastAPI + Uvicorn | Async, high performance REST |
| Task Queue | Celery + Redis | Distributed job execution |
| Scheduler | APScheduler | Cron + timezone-aware scheduling |
| Browser Automation | Playwright (Python) | Reliable, async, stealth-capable |
| Stealth | playwright-stealth | Bypass bot detection |
| AI / NLP | sentence-transformers | Local embeddings, no API cost |
| ML | scikit-learn / XGBoost | Profile classifier head |
| Local LLM | Ollama (Mistral / LLaMA3) | Free, private message generation |
| Vector DB | Qdrant | Profile deduplication + similarity |
| Primary DB | PostgreSQL + SQLAlchemy | Relational data, audit logs |
| Cache | Redis | Rate limiting, session storage |
| Frontend | React + TailwindCSS + Recharts | Dashboard UI |
| Containerization | Docker + Docker Compose | Local and cloud deployment |
| Monitoring | Prometheus + Grafana | Metrics, alerts |

---

## 5. Database Schema (PostgreSQL)

```sql
-- Core tables

CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    target_roles TEXT[],
    target_regions TEXT[],
    daily_limit INT DEFAULT 20,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    linkedin_url TEXT UNIQUE NOT NULL,
    full_name TEXT,
    title TEXT,
    company TEXT,
    location TEXT,
    region TEXT,               -- normalized: SG, IN, UK, EU, US, UAE
    relevance_score FLOAT,
    is_relevant BOOLEAN,
    classifier_confidence FLOAT,
    embedding VECTOR(384),     -- pgvector or stored in Qdrant
    scraped_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE connection_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id),
    profile_id UUID REFERENCES profiles(id),
    status TEXT CHECK (status IN ('pending','sent','accepted','failed','skipped')),
    message_sent TEXT,
    sent_at TIMESTAMPTZ,
    accepted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE daily_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    sent_count INT DEFAULT 0,
    accepted_count INT DEFAULT 0,
    region TEXT,
    UNIQUE(date, region)
);

CREATE TABLE automation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT,           -- scrape, classify, send, error, throttle
    message TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 6. Automation Strategy (Playwright)

### Core Workflow

```python
# pseudocode — see references/playwright_agent.py for full implementation

async def run_connection_campaign(campaign: Campaign):
    browser = await launch_stealth_browser()
    page = await browser.new_page()

    await linkedin_login(page)  # uses stored session cookie

    profiles = await get_prioritized_profiles(campaign, limit=campaign.daily_limit)

    for profile in profiles:
        if await is_rate_limit_reached(campaign.region):
            break

        await navigate_to_profile(page, profile.linkedin_url)
        await human_like_delay(2, 5)          # 2–5 sec random pause

        if await connect_button_visible(page):
            note = await generate_note(profile)
            await click_connect(page, note)
            await log_request(profile, status="sent")
            await human_like_delay(8, 20)      # 8–20 sec between sends
        else:
            await log_request(profile, status="skipped")

    await browser.close()
```

### Human Behavior Simulation
- Random mouse movements via `playwright-stealth`
- Variable delays between actions (drawn from normal distribution)
- Randomized scroll depth before clicking
- Session warm-up: browse feed 1–2 min before sending requests

---

## 7. Scheduler Design (Region-Aware)

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

scheduler = AsyncIOScheduler()

REGION_TIMEZONES = {
    "SG":  "Asia/Singapore",
    "IN":  "Asia/Kolkata",
    "UK":  "Europe/London",
    "EU":  "Europe/Berlin",
    "US":  "America/New_York",
    "UAE": "Asia/Dubai",
}

WINDOWS = [
    {"hour": 9,  "minute": 0},   # 9:00 AM window
    {"hour": 19, "minute": 0},   # 7:00 PM window
]

for region, tz_str in REGION_TIMEZONES.items():
    tz = pytz.timezone(tz_str)
    for window in WINDOWS:
        scheduler.add_job(
            run_connection_campaign,
            CronTrigger(hour=window["hour"], minute=window["minute"], timezone=tz),
            kwargs={"region": region},
            id=f"campaign_{region}_{window['hour']}",
            replace_existing=True,
        )

scheduler.start()
```

### Daily Limits (Anti-ban)
| Period | Max Requests |
|--------|-------------|
| Per session | 10–15 |
| Per day total | 20–25 |
| Weekly cap | 100 |
| Monthly cap | 400 |

---

## 8. Anti-Ban / Safe Automation Strategy

### Browser Fingerprint Hardening
```python
# Use playwright-stealth to mask automation signals
from playwright_stealth import stealth_async

async def launch_stealth_browser():
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
        viewport={"width": 1366, "height": 768},
        locale="en-US",
        timezone_id="America/New_York",
    )
    page = await context.new_page()
    await stealth_async(page)
    return page
```

### Rate Limit Circuit Breaker
```python
async def is_rate_limit_reached(region: str) -> bool:
    today_count = await get_today_sent_count(region)
    if today_count >= DAILY_LIMIT:
        await alert_dashboard(f"Daily limit reached for {region}")
        return True

    # Check for LinkedIn warning signals on page
    if await page_has_restriction_warning():
        await pause_campaign(hours=24)
        return True

    return False
```

### Additional Safeguards
- **Session persistence**: Reuse authenticated cookies (avoid repeated logins)
- **Proxy rotation**: Residential proxies (e.g., BrightData) per region for scale
- **CAPTCHA detection**: Auto-pause + Slack/email alert on CAPTCHA
- **Profile warm-up**: New accounts must engage (like, comment) for 2 weeks before automation
- **Exponential backoff**: On any 429 or restriction signal
- **No bulk message blasts**: One-by-one sends only

---

## 9. React Dashboard — UI Design

### Pages & Components

```
/dashboard
  ├── Overview Cards
  │     ├── Total Sent (today / week / month)
  │     ├── Accepted (count + acceptance rate %)
  │     ├── Pending
  │     └── Failed / Skipped
  │
  ├── Campaign Manager
  │     ├── Create / Edit campaign
  │     ├── Target role + region config
  │     └── Enable / Pause / Delete
  │
  ├── Profile Queue
  │     ├── Upcoming profiles (scored + ranked)
  │     ├── Manual override (skip / promote)
  │     └── Classifier confidence badge
  │
  ├── Analytics Charts (Recharts)
  │     ├── Daily requests sent vs accepted (line chart)
  │     ├── Acceptance rate by role (bar chart)
  │     ├── Acceptance rate by region (choropleth / bar)
  │     └── Queue depth trend
  │
  ├── Activity Log
  │     └── Real-time event feed (WebSocket)
  │
  └── Settings
        ├── Daily limits per region
        ├── Scheduling windows
        ├── Ollama / LLM config
        └── LinkedIn session management
```

### Key API Endpoints (FastAPI)

```
GET  /api/stats/overview          — dashboard KPIs
GET  /api/stats/daily?days=30     — time series for charts
GET  /api/campaigns               — list campaigns
POST /api/campaigns               — create campaign
PUT  /api/campaigns/{id}/toggle   — pause/resume
GET  /api/profiles/queue          — upcoming send queue
POST /api/profiles/skip/{id}      — manual skip
GET  /api/logs?limit=50           — recent automation logs
WS   /ws/activity                 — real-time event stream
```

---

## 10. Project Directory Structure

```
linkedin-automation/
├── backend/
│   ├── main.py                   # FastAPI app entrypoint
│   ├── api/
│   │   ├── routes/
│   │   │   ├── campaigns.py
│   │   │   ├── stats.py
│   │   │   ├── profiles.py
│   │   │   └── logs.py
│   │   └── websocket.py
│   ├── ai/
│   │   ├── classifier.py         # Profile relevance classifier
│   │   ├── scorer.py             # Multi-dimension relevance scorer
│   │   ├── embedder.py           # sentence-transformers embeddings
│   │   └── personalizer.py      # Ollama message generation
│   ├── automation/
│   │   ├── browser_agent.py      # Playwright automation core
│   │   ├── scraper.py            # LinkedIn profile scraper
│   │   ├── session_manager.py    # Cookie/session management
│   │   └── anti_ban.py           # Rate limiter + circuit breaker
│   ├── scheduler/
│   │   ├── scheduler.py          # APScheduler region-aware jobs
│   │   └── job_registry.py
│   ├── db/
│   │   ├── models.py             # SQLAlchemy ORM models
│   │   ├── session.py            # DB session factory
│   │   └── migrations/           # Alembic migrations
│   ├── queue/
│   │   ├── celery_app.py         # Celery worker config
│   │   └── tasks.py              # Async task definitions
│   └── config.py                 # Environment settings (pydantic-settings)
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Campaigns.jsx
│   │   │   ├── ProfileQueue.jsx
│   │   │   ├── Analytics.jsx
│   │   │   └── Settings.jsx
│   │   ├── components/
│   │   │   ├── StatCard.jsx
│   │   │   ├── ActivityFeed.jsx
│   │   │   └── Charts/
│   │   └── api/
│   │       └── client.js
│   └── package.json
│
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── infra/
│   ├── terraform/                # Optional: AWS/GCP/Azure IaC
│   └── k8s/                      # Optional: Kubernetes manifests
│
├── references/
│   ├── playwright_agent.py       # Full Playwright implementation reference
│   ├── classifier_training.py    # Model training pipeline
│   └── api_schemas.py            # Pydantic request/response models
│
├── .env.example
├── requirements.txt
└── README.md
```

---

## 11. Docker Compose Deployment

```yaml
# docker-compose.yml
version: "3.9"

services:
  backend:
    build: ./docker/Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/linkedin_db
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_URL=http://qdrant:6333
      - OLLAMA_URL=http://ollama:11434
    depends_on: [postgres, redis, qdrant, ollama]
    volumes:
      - ./backend:/app

  celery_worker:
    build: ./docker/Dockerfile.backend
    command: celery -A queue.celery_app worker --loglevel=info
    depends_on: [redis, postgres]

  frontend:
    build: ./docker/Dockerfile.frontend
    ports:
      - "3000:3000"

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: linkedin_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_models:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]   # GPU passthrough if available

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./infra/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"

volumes:
  postgres_data:
  qdrant_data:
  ollama_models:
```

---

## 12. Cloud Deployment Architecture

### Recommended: AWS (Production)

```
Route53 → CloudFront → ALB
                         ├── ECS (FastAPI backend, auto-scaling)
                         └── ECS (React frontend, static via S3+CF)

ECS Tasks:
  ├── FastAPI API service
  ├── Celery Worker (automation tasks)
  └── Playwright Browser Agent (low-traffic, 1 task)

Managed Services:
  ├── RDS PostgreSQL (with pgvector extension)
  ├── ElastiCache Redis
  └── ECR (container registry)

Qdrant: Self-hosted on EC2 (t3.medium) or Qdrant Cloud
Ollama: EC2 g4dn.xlarge (NVIDIA T4 GPU) — for LLM inference
Secrets: AWS Secrets Manager (LinkedIn credentials, DB passwords)
Monitoring: CloudWatch + Grafana Cloud
```

### Minimal Cloud Option (Low Cost)
- **Hetzner VPS** (CX31 or CX41): Run full Docker Compose stack
- Cost: ~€15–30/month
- Suitable for personal use / early scale

---

## 13. Implementation Phases

| Phase | Scope | Duration |
|-------|-------|----------|
| 1 — Foundation | FastAPI + DB + Docker Compose | Week 1 |
| 2 — AI Engine | Classifier + Scorer + Embedder | Week 2 |
| 3 — Automation | Playwright agent + anti-ban + scheduler | Week 3 |
| 4 — Dashboard | React UI + charts + WebSocket feed | Week 4 |
| 5 — Hardening | Proxy integration + CAPTCHA alerts + limits | Week 5 |
| 6 — Cloud Deploy | AWS/Hetzner deployment + monitoring | Week 6 |

---

## 14. Ethical & Legal Guardrails

> **Important**: LinkedIn's Terms of Service prohibit scraping and automated actions.
> This system must only be used for personal professional networking by the account owner.
> It must not be commercialized as a SaaS for third-party LinkedIn accounts.

Recommended safeguards:
- Store LinkedIn credentials encrypted (never plain text)
- Implement user consent logging for all actions
- Cap automation well below LinkedIn's soft limits
- Include a prominent legal disclaimer in the dashboard
- Provide a one-click "Emergency Stop" to halt all automation immediately

---

## 15. Key Configuration (`.env.example`)

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/linkedin_db
REDIS_URL=redis://localhost:6379/0

# LinkedIn Session (store cookie, not password in prod)
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=yourpassword
LINKEDIN_SESSION_COOKIE=   # preferred over password login

# AI
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Vector DB
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=linkedin_profiles

# Automation Limits
DAILY_LIMIT_PER_REGION=20
SESSION_LIMIT=10
MIN_DELAY_SECONDS=8
MAX_DELAY_SECONDS=20

# Notifications
SLACK_WEBHOOK_URL=
ALERT_EMAIL=
```

---

## 16. Claude Usage Guide (How to use this skill)

When this skill is active, Claude will:

1. **Generate full system architecture** with diagrams and component descriptions
2. **Produce working code** for any layer: AI classifier, Playwright agent, FastAPI routes, React components, Docker configs
3. **Design database schemas** with migrations
4. **Write scheduler logic** with region-aware timezone support
5. **Implement anti-ban strategies** with circuit breakers and human-like behavior simulation
6. **Create dashboard wireframes** and component structure
7. **Produce deployment configs** for Docker Compose and AWS/Hetzner
8. **Generate phased implementation plans** with effort estimates

### Prompts that trigger this skill:
- "Build the Playwright LinkedIn agent with stealth mode"
- "Write the FastAPI routes for the dashboard API"
- "Design the profile classifier model training pipeline"
- "Create the Docker Compose for the full stack"
- "Implement the region-aware APScheduler"
- "Write the React dashboard with Recharts analytics"
- "How do I avoid LinkedIn banning my automation?"

---

*Skill version: 1.0 | Author: Srinivas Bathula | Domain: AI Automation / LinkedIn Growth*
