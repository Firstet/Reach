# Reach — RayvenSC AI Business Development Platform Deployment Guide

## Production Readiness Overview

Reach is fully built, tested, containerized, and audited for deployment across local environments, Docker Compose, AWS, GCP, Azure, or VPS instances.

---

## 1. Environment & Secret Setup

Before deploying, generate required production secret keys and copy the environment template:

```bash
# Clone repository and enter directory
cd Reach

# Copy environment template
cp .env.example .env

# Generate secure random secret keys for production
make generate-keys
```

Update `.env` with the generated secret keys:
- `APP_SECRET_KEY`: 64-character random hex string.
- `JWT_SECRET_KEY`: 64-character random hex string.
- `ENCRYPTION_KEY`: Fernet AES encryption key for securing stored provider credentials.

---

## 2. Pre-flight Deployment Health Audit

Run the automated deployment auditor to verify environment configuration, secrets validity, and database connection readiness:

```bash
make check-deploy
```

Output:
```text
======================================================================
 REACH — PRODUCTION DEPLOYMENT AUDITOR
======================================================================
[✓] Environment File (.env): Found at /Users/.../Reach/.env
[✓] APP_SECRET_KEY: Configured securely
[✓] JWT_SECRET_KEY: Configured securely
[✓] ENCRYPTION_KEY: Valid Fernet encryption key format
[✓] LLM Provider: Active provider set to 'openai'
[✓] Email Provider: Active provider set to 'gmail'
[✓] Search Provider: Active provider set to 'serper'
[✓] Enrichment Provider: Active provider set to 'hunter'
[✓] Database Backend: PostgreSQL vector database configured
======================================================================
SUCCESS: System is verified and ready for production deployment!
```

---

## 3. Production Deployment via Docker Compose

Launch the complete containerized stack (PostgreSQL + pgvector, Redis, FastAPI Backend, Celery Worker, Next.js Production Frontend):

```bash
# Start full production stack
make prod-up

# Alternatively, directly via docker compose:
docker compose -f docker-compose.prod.yml up -d --build
```

### Access Services:
- **Frontend Dashboard**: `http://localhost:3000`
- **FastAPI API & Docs**: `http://localhost:8000/docs`
- **PostgreSQL Vector DB**: `localhost:5432` (`reach / reach_password`)
- **Redis Cache & Celery Broker**: `localhost:6379`

### Run Database Migrations:
```bash
make migrate
```

---

## 4. Quick Local Development Execution

For rapid testing and development mode:

1. **Start Backend**:
   ```bash
   cd backend
   PYTHONPATH=. .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Start Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. Open **`http://localhost:3000`** in your browser.
   - **Default Admin Credentials**:
     - Email: `admin@rayvensc.com`
     - Password: `admin123456`

---

## 5. Automated Test Suite & Build Verification

Run backend pytest suite:
```bash
make test
```
Output: `25 passed`

Run Next.js production build check:
```bash
cd frontend && npm run build
```
Output: `✓ Compiled successfully`

---

## 6. Key Security & Compliance Configuration

- **Zero-Paid Infrastructure Mode**: Works out of the box with zero required paid subscriptions.
- **Provider Encryption**: All API keys, SMTP credentials, and tokens are encrypted at rest using AES Fernet.
- **Global Emergency Kill-Switch**: One-click kill switch accessible via UI (`/dashboard`) or `POST /api/v1/agent/kill-switch` to immediately suspend all outgoing emails and web automation.
- **Monthly Email Send Cap**: Enforces configurable monthly outreach cap (default: `50 emails/month`).
- **Human Escalation Engine**: Automatically flags leads requesting custom proposals or pricing for human partner intervention.
