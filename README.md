# AFFECTORYX — Engineering Intelligence Platform

> **Deterministic Change Consequence Analysis, Blast Radius Topology & Evidence Provenance**

---

## 1. Product Vision

AFFECTORYX helps software engineering teams understand the potential consequences of software changes *before* they are deployed into production.

It answers the core engineering questions:
- Which services depend on this component?
- Which APIs or integrations could break?
- Which customers might be affected?
- Which workflows could stop working?
- What verifiable evidence supports each finding?
- What should engineers verify before deployment?

---

## 2. Core Architectural Pillars

- **Evidence-Based & Deterministic**: Every link in the dependency graph references concrete, machine-verifiable evidence (`OpenAPI Specification`, `Code Callsite AST`, `Database Migration DDL`, or `Customer SLA Contract`).
- **Strict Unknown Safety Principle**: **An unknown dependency is NEVER labeled as safe.** When evidence is incomplete or ambiguous, the platform raises an explicit caution flag requiring engineer verification.
- **Air-Gapped Untrusted Code Processing**: Uploaded or ingested source code is parsed strictly as data using Python's `ast` parser and static regex lexers. Code is **never executed, evaluated, or compiled dynamically**.
- **Multi-Tenant Isolation**: Strict organization-level data isolation enforced across database relations, API middleware, and service domains.

---

## 3. Technology Stack

- **Frontend**: Next.js 16 (App Router), TypeScript, Tailwind CSS, Lucide Icons, React Flow ready.
- **Backend**: Python 3.9+, FastAPI, SQLAlchemy 2.0, Alembic, NetworkX, Pydantic v2.
- **Security**: Argon2/Bcrypt password hashing, HS256 JWT access tokens, strict security headers (`nosniff`, `DENY`, `HSTS`, `Referrer-Policy`).
- **Infrastructure**: Docker Compose, PostgreSQL 16, Redis 7, Pytest, Playwright.

---

## 4. Quick Start (Local Development)

### Prerequisites
- Python 3.9+
- Node.js 20+ & npm 10+
- Git

### Backend Setup
```bash
# 1. Virtual Environment
python3 -m venv backend/.venv
source backend/.venv/bin/activate

# 2. Dependencies & Migrations
pip install -r backend/requirements.txt
cd backend
alembic upgrade head
cd ..

# 3. Start Backend API (Port 8000)
backend/.venv/bin/uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run build
npm run start -- -p 3000
```
Visit `http://localhost:3000` to access the enterprise engineering console.

---

## 5. Automated Verification & Testing

```bash
# Run Backend Pytest Suite
cd backend
pytest -v

# Run End-to-End Multi-Viewport Playwright Tests
python tests/e2e/test_phase1_e2e.py
python tests/e2e/test_phase2_e2e.py

# Run Pre-Commit Secrets Scanner
python3 scripts/scan_secrets.py
```
