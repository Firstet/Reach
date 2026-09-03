# Reach — AI Business Development Agent
## RayvenSC Internal Platform · v1.0

A self-hosted, AI-powered outbound business development agent for **Rayven Strategic Communications**.

---

## What Reach Does

Reach is a production-grade AI agent that:

1. **Discovers** qualified prospects matching campaign targets (industry, seniority, location)
2. **Enriches** contact data — email addresses, company context, LinkedIn profiles
3. **Researches** each prospect using web search and builds a personalized context brief
4. **Writes** hyper-personalized outreach emails grounded in the RayvenSC knowledge base (RAG)
5. **Executes** multi-step email sequences with intelligent follow-up timing
6. **Monitors** replies and classifies intent (interested / not interested / question / OOO / unsubscribe)
7. **Escalates** warm leads to human operators via Slack or email with full conversation context
8. **Records** every action in an immutable audit log

---

## Quick Start

### 1. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

Required keys (minimum viable config):
- `OPENAI_API_KEY` — LLM completion and embeddings
- `GMAIL_*` — OAuth2 email credentials (see docs/gmail-setup.md)
- `ADMIN_PASSWORD` — Dashboard admin account
- `APP_SECRET_KEY` + `JWT_SECRET_KEY` + `ENCRYPTION_KEY` — Security keys (generate with `openssl rand -hex 32`)

### 2. Start the Stack

```bash
make up
# or: docker-compose up -d
```

Services:
| Service | Port | Description |
|---------|------|-------------|
| `frontend` | 3000 | Next.js Dashboard |
| `backend` | 8000 | FastAPI (API + Docs) |
| `worker` | — | Celery background tasks |
| `postgres` | 5432 | PostgreSQL + pgvector |
| `redis` | 6379 | Task queue + cache |

### 3. Run Initial Setup

```bash
# Run database migrations
make migrate

# Ingest RayvenSC knowledge base
make ingest ADMIN_PASSWORD=your_password

# Open the dashboard
open http://localhost:3000
```

Default admin: `admin@rayvensc.com` / (your `ADMIN_PASSWORD`)

---

## Architecture

```
Reach/
├── backend/               FastAPI + Celery + SQLAlchemy (Async)
│   ├── app/
│   │   ├── main.py        App factory + lifespan
│   │   ├── core/          Config, DB, Security (JWT + Fernet encryption)
│   │   ├── models/        SQLAlchemy ORM (Postgres + pgvector)
│   │   ├── providers/     Pluggable provider system (LLM/email/search/enrichment/linkedin)
│   │   ├── api/           REST API routes + WebSocket notifications
│   │   ├── knowledge/     RayvenSC KB + ingestion + semantic search
│   │   ├── agents/        AI orchestration agents (Phase 2)
│   │   └── tasks/         Celery background jobs
│   ├── alembic/           Database migrations
│   └── tests/             Unit + integration tests
└── frontend/              Next.js 15 dashboard
    └── app/
        ├── login/
        └── dashboard/
            ├── Overview, Campaigns, Pipeline (Kanban)
            ├── Conversations (inbox + escalation)
            ├── Knowledge Base (semantic search)
            ├── Settings (provider config)
            └── Audit Log
```

---

## Provider Configuration

All providers are pluggable. Configure via the dashboard Settings page or `.env`:

| Provider | Purpose | Active Options |
|----------|---------|---------------|
| LLM | AI completion + embeddings | OpenAI, Anthropic |
| Email | Sending outreach | Gmail (OAuth2) |
| Search | Web research | Serper |
| Enrichment | Email finding | Hunter.io |
| LinkedIn | Profile research | Playwright (read-only, disabled by default) |
| Notifications | Escalation alerts | Slack, Email, Webhook |
| Vector DB | Semantic search | pgvector (built-in) |

---

## Security

- **No plaintext secrets** — All provider credentials encrypted at rest (Fernet AES-128)
- **JWT auth** — Short-lived access tokens (1h) + refresh tokens (7d)
- **LinkedIn safety** — Cookie-based only, never stores passwords, read-only, disabled by default
- **Human-in-the-loop** — All hot-lead responses require human approval
- **Audit trail** — Immutable log of every agent and human action
- **Rate limiting** — Conservative send limits prevent spam classification

---

## Development

```bash
# Backend tests
make test

# Backend dev (without Docker)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend dev
cd frontend
npm run dev

# View API docs
make docs   # opens http://localhost:8000/api/docs
```

---

## Roadmap

**Phase 1 ✅ — Foundation (Complete)**
- Infrastructure, data models, provider system, API, frontend dashboard, knowledge base

**Phase 2 🔄 — AI Agent Loop**
- Research agent, email writer (RAG), reply classifier, sequence orchestration
- Celery beat scheduler, send window enforcement
- Gmail reply polling + intent classification

**Phase 3 📋 — Intelligence & Scale**
- Apollo/Clearbit enrichment integration
- LinkedIn Sales Navigator automation
- A/B testing for email templates
- Campaign analytics and reporting

---

*Built for Rayven Strategic Communications · Contact: hello@rayvensc.com*
