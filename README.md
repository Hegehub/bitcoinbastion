# 🏰 Bitcoin Bastion

> **Sovereign Intelligence Layer for Bitcoin**

---

## 🚀 Overview

**Bitcoin Bastion** is a Bitcoin-native intelligence and operations platform designed to sit **on top of the Bitcoin protocol**.

It transforms raw network state into:

- actionable signals
- risk assessments
- operational decisions
- sovereignty insights

---

> Most systems *consume Bitcoin data*.
> Bitcoin Bastion **interprets Bitcoin reality**.

---

## 🎯 Problem

Bitcoin users, treasuries, and operators face a fragmented landscape:

- on-chain data is noisy and hard to interpret
- wallet structure risks are invisible
- treasury operations are manual and error-prone
- privacy exposure is poorly understood
- recovery readiness is rarely verified
- no unified system exists for **sovereignty assurance**

---

## 💡 Solution

Bitcoin Bastion provides a unified system that:

### 1) Understands Bitcoin state
- on-chain activity
- news and narratives
- entity behavior

### 2) Interprets it
- explainable signal generation
- risk scoring
- contextual recommendations

### 3) Enables action
- treasury workflows
- policy enforcement
- operational visibility

### 4) Ensures survivability (Citadel)
- recovery readiness
- dependency mapping
- disaster simulation
- repair planning

---

## 🧠 System Architecture

```text
Bitcoin Network (Protocol Layer)
        ↓
Data Ingestion
  - On-chain
  - News
  - Entities
        ↓
Interpretation Layer
  - Signal Engine
  - Explainability Graph
        ↓
Operational Layer
  - Wallet Intelligence
  - Treasury Engine
  - Policy Engine
  - Privacy Analysis
        ↓
Citadel Layer (Sovereignty)
  - Recovery
  - Dependencies
  - Simulations
  - Repair Plans
        ↓
Delivery Layer
  - API
  - Telegram
  - Operator Tools
```

---

## 🏰 Citadel — Sovereignty Layer

Citadel is the defining layer of the system.

It answers critical questions:

- Can your Bitcoin be recovered?
- What dependencies can break your system?
- What happens under failure conditions?
- What must be fixed immediately?

---

> Bastion tells you what is happening.
> Citadel tells you whether you survive it.

---

## ⚙️ Core Capabilities

### Intelligence
- News ingestion and reputation tracking
- Explainable signal generation
- Entity tracking and watchlists

### On-chain Monitoring
- Transaction activity
- Large transfer detection
- Event-based signals
- Chain-state baseline endpoint (`/api/v1/onchain/state`)

### Wallet & Treasury
- Wallet health evaluation
- Treasury request workflows
- Policy-based approvals
- UTXO structure analysis (baseline)
- Descriptor awareness checks (baseline)

### Policy & Privacy
- Policy simulation and enforcement
- Privacy risk scoring

### Observability
- Metrics and health probes
- Job tracking and audit logs

### Sovereignty (Citadel)
- Assessment scoring (baseline with synthetic components)
- Dependency graph (synthetic/baseline)
- Recovery readiness
- Disaster simulations (synthetic/baseline)
- Inheritance verification (baseline)
- Repair plans (baseline)

---

## 🧰 Technology

- **Backend**: FastAPI
- **Language**: Python 3.12
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy 2.x
- **Queue**: Celery + Redis
- **Migrations**: Alembic
- **Auth**: JWT + Argon2
- **Metrics**: Prometheus
- **Telegram**: aiogram + Telegram Bot API

---

## 📊 Roadmap & Execution Status

> ✔ = Implemented
> ◐ = Baseline / partial
> ◌ = Synthetic placeholder behavior present
> ❌ = Missing

### 🧱 Foundation

- ✔ Modular FastAPI backend
- ✔ Database models & repositories
- ✔ Auth system (JWT)
- ✔ Middleware / logging / metrics
- ✔ Docker infrastructure
- ◐ Full migration consistency enforcement
- ◐ CI-level schema validation hardening

### 📰 Intelligence Layer

- ✔ News ingestion
- ◐ Signal engine (baseline)
- ◐ Explainability models (baseline graph depth)
- ◐ Full signal pipeline maturity

### ⛓ On-chain Layer

- ✔ On-chain ingestion baseline
- ✔ Provider abstraction
- ◐ Chain-state awareness endpoint + service
- ◐ Reorg/finality modeling calibration
- ❌ Proven production-grade full-node depth

### 👛 Wallet & Treasury

- ✔ Wallet health evaluation
- ✔ Treasury workflows
- ✔ Policy engine
- ✔ Privacy scoring
- ◐ UTXO intelligence
- ◐ Descriptor awareness
- ◐ Spend simulation depth

### 🏰 Citadel (Sovereignty)

- ✔ Citadel API surface
- ✔ Assessment persistence lifecycle
- ◐ Recovery/inheritance/policy checks
- ◌ Dependency graph realism
- ◌ Disaster simulation realism
- ◌ Scoring realism/calibration

### ⚡ Bitcoin-native Depth

- ◐ UTXO engine
- ◐ Mempool analyzer
- ◐ Fee market modeling
- ◐ Script awareness
- ◐ Descriptor system
- ◐ Chain-state engine

### 📡 Delivery & Ops

- ✔ Admin endpoints
- ✔ Job tracking
- ✔ Observability snapshot
- ◐ Telegram runtime (config + external dependency gated)
- ◐ Delivery orchestration
- ❌ Operator tooling UI

---

## 🧠 Design Principles

### Bitcoin-native
- UTXO model
- transaction structure
- fee market dynamics
- script system

### Explainability-first
All outputs should:
- include reasoning
- show evidence
- provide confidence

### Sovereignty-first
The system assumes:
- no custody
- no trust
- no assumptions about user setup

### Modular evolution
Each layer can evolve independently:
- ingestion
- signals
- policy
- Citadel

---

## 🔐 Security Model

- No private keys stored
- No seed phrase handling
- Authenticated API access
- Role-based access control (baseline)

---

## 🧪 Development

```bash
docker compose up --build
```

Docs:

```text
http://localhost:8000/docs
```

Metrics:

```text
http://localhost:8000/metrics
```

---

## 🚧 Current Reality

Bitcoin Bastion is currently:

- a **strong backend platform**
- a **functional intelligence baseline**
- an **early-stage sovereignty engine**

It is not yet:

- fully deterministic for Citadel scoring/graph/simulation
- fully production-hardened for all failure modes
- fully validated for deep protocol edge cases

---

## Core documentation
- `docs/SPEC.md`
- `docs/SYSTEM_PROMPT.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/DOMAIN_MODELS.md`
- `docs/API_CONTRACTS.md`
- `docs/CODEX_WORKFLOW.md`
- `docs/PRODUCTION_READINESS.md`
- `docs/STATUS.md`

## API groups
- health
- auth
- news
- signals
- onchain
- entities
- wallet
- fees
- treasury
- admin
- users
- policy
- privacy
- education
- observability
- citadel

## Operations endpoints
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`
- `GET /metrics`
- `GET /api/v1/policy/executions`
- `GET /api/v1/policy/catalog`
- `POST /api/v1/news/sources/reputation/refresh`
- `GET /api/v1/news/sources/reputation`
- `GET /api/v1/signals/{signal_id}/explanation`

## Production guardrails
- `ENVIRONMENT=prod|production` rejects weak/default `JWT_SECRET_KEY` values.
- Alembic supports deterministic DB URL resolution via `DATABASE_URL` override.
- Reproducibility check: `make alembic-repro`.

See `docs/STATUS.md` for current implementation status and truth-audit baseline.
