<div align="center">

# 🏦 PropIQ

### _AI Collateral Intelligence Engine for Loan Against Property (LAP)_

**Built for the Poonawalla Fincorp Hackathon 2026**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)

</div>

---

## 📌 Table of Contents

- [What is PropIQ?](#-what-is-propiq)
- [The Problem We Are Solving](#-the-problem-we-are-solving)
- [Our Solution: PropIQ](#-our-solution-propiq)
- [Our USPs — Going Beyond the Problem Statement](#-our-usps--going-beyond-the-problem-statement)
- [Business Impact](#-business-impact)
- [System Architecture](#-system-architecture)
  - [System Design Considerations](#-system-design-considerations)
  - [Core Valuation Sequence Diagram](#-core-valuation-sequence)
- [Valuation Logic & Liquidity Model](#-valuation-logic--liquidity-model)
- [The Bloomberg Terminal](#-the-bloomberg-terminal)
- [Black Swan Simulator](#-black-swan-simulator)
- [Practical Deployability](#-practical-deployability)
- [API Reference](#-api-reference)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [Project Structure](#-project-structure)

---

## 🧭 What is PropIQ?

**PropIQ** is a complete, production-ready **AI-powered Collateral Valuation & Risk Management Operating System** designed for Indian NBFCs and secured lenders operating in the Loan Against Property (LAP) market.

It answers the two fundamental questions every secured lender asks:

| Question                             | PropIQ's Answer                                                        |
| ------------------------------------ | ---------------------------------------------------------------------- |
| **What is this asset worth today?**  | Hyper-local XGBoost ML valuation with SHAP-explainable feature drivers |
| **How easily can it be liquidated?** | Dynamic Resale Potential Index (0-100) + Time-to-Liquidate estimation  |

PropIQ combines **machine learning**, **computer vision**, **generative AI**, and **enterprise async architecture** to deliver valuation decisions in seconds — not weeks.

---

## ❗ The Problem We Are Solving

Traditional LAP underwriting relies on:

- ❌ Manual site inspections (2-3 weeks TAT)
- ❌ Subjective broker inputs with high variance
- ❌ Static circle rates that lag actual market conditions by 12-24 months
- ❌ No continuous portfolio monitoring after loan disbursement

This leads to:

- **Mispriced risk** → NPAs
- **Conservative lending** → lost business
- **Slow decisioning** → poor customer experience

---

## 💡 Our Solution: PropIQ

**PropIQ** is an end-to-end Collateral Intelligence OS that modernizes the entire LAP lifecycle. Instead of manual assessments, PropIQ ingests property data (via structured forms, NLP-based chat, or visual images), instantly computes a hyper-local market value using an advanced XGBoost model, adjusts that value using Computer Vision analysis of property conditions, and applies RBI-compliant LTV rules to generate a final, SHAP-explainable Credit Memo in seconds.

### 🔄 Detailed Workflow Diagram

```mermaid
graph LR
    A[Raw Property Input] --> B[Data Parsing]
    B --> C[Agentic Validation]
    C --> D{Valuation Engines}
    D -->|Features| E[XGBoost ML]
    D -->|Images| F[Groq VLM]
    E --> G[Composite Value]
    F --> G
    G --> H[SHAP & LTV Rules]
    H --> I[Credit Memo]
```

---

## 🌟 Our USPs — Going Beyond the Problem Statement

The problem statement asked for a basic valuation and liquidity engine. **PropIQ delivers 6 additional enterprise-grade capabilities** not present in the requirements:

### 1. 🤖 Agentic NLP Data Extraction

PropIQ's `/api/v1/chat` endpoint acts as an **autonomous AI loan officer**. You can literally paste a raw broker WhatsApp message:

> _"Got a 1200 sqft 10yr old flat in Wakad, 3rd floor, clear title, registered..."_

The LLM parses the text, validates the entities, structures the JSON, and fires the full valuation pipeline — automatically.

---

### 2. 👁️ Computer Vision Condition Scoring (VLM)

PropIQ implements **Groq's Llama-3.2-Vision** to analyze **multiple** interior/exterior property images simultaneously. It:

- Detects structural damage and distress
- Applies a data-driven **valuation haircut** (e.g., −15% for poor condition)
- Flags potential **visual fraud** (e.g., claimed "apartment" but photo shows commercial warehouse)
- Produces a detailed natural-language damage report

---

### 3. ⚡ Black Swan Market Shock Simulator

PropIQ includes a **portfolio-level macro-economic stress testing engine**. Risk managers can simulate severe market crashes (e.g., −20% sudden value shock) across the entire active loan book in seconds and instantly see which loans breach safe LTV thresholds.

---

### 4. 📋 Automated Internal Risk Escalation Memos (LLM)

When a loan goes underwater during a stress test, PropIQ automatically uses a **generative LLM** to draft a formal, RBI-compliant **Internal Credit Committee Risk Escalation Memo**, recommending specific defensive actions (blocking top-ups, flagging for provisioning) — aligned with Indian retail LAP banking norms.

---

### 5. 🔬 Explainable AI (XGBoost + SHAP)

PropIQ uses **SHAP (SHapley Additive exPlanations)** to provide mathematically exact attribution. Instead of just saying "listing density matters", we show:

> _"+₹ 8.2L contributed by infrastructure proximity, −₹ 3.4L subtracted by building age"_

---

### 6. 🔄 Automated 30-Day Portfolio Re-Assessment

PropIQ deploys a **Celery Beat background scheduler** that automatically re-evaluates the entire active loan portfolio on the 1st of every month — no human trigger required. New loans added during the day are assessed immediately upon creation.

---

## 📈 Business Impact

| Metric                             | Before PropIQ     | With PropIQ                   |
| ---------------------------------- | ----------------- | ----------------------------- |
| Valuation Turnaround Time          | 2–3 Weeks         | **< 9 Seconds**               |
| Surveyor Cost per Assessment       | ₹5,000–₹15,000    | **Near Zero**                 |
| Portfolio Stress Test Time         | Manual (Days)     | **< 60 Seconds**              |
| NPA Risk from Mispriced Collateral | High (subjective) | **Low (algorithmic)**         |
| Audit Trail                        | Paper-based       | **Full Digital (PostgreSQL)** |

---

## 🏗️ System Architecture

PropIQ follows a **microservice architecture** built for high-concurrency, fault tolerance, and Kubernetes deployability.

```text
╔═════════════════════════════════════════════════════════════════════╗
║                      DOCKER COMPOSE NETWORK                         ║
║                                                                     ║
║ ┌─────────────────────────────────────────────────────────────────┐ ║
║ │                         USER INTERFACE                          │ ║
║ │                   React Frontend (Port 3000)                    │ ║
║ │ ┌────────────┐ ┌────────────┐ ┌─────────────┐ ┌───────────────┐ │ ║
║ │ │ Form Input │ │ Bloomberg  │ │ Portfolio   │ │ Black Swan    │ │ ║
║ │ │ + Chat     │ │ Terminal   │ │ Monitor     │ │ Simulator     │ │ ║
║ │ └────────────┘ └────────────┘ └─────────────┘ └───────────────┘ │ ║
║ └──────────────────────────┬──────────────────────────────────────┘ ║
║                            │ REST / JSON                            ║
║                            ▼                                        ║
║ ┌─────────────────────────────────────────────────────────────────┐ ║
║ │                   FastAPI GATEWAY (Port 8000)                   │ ║
║ │         SlowAPI Rate Limiter → Global Exception Handler         │ ║
║ │ ┌────────────┐ ┌────────────┐ ┌─────────────┐ ┌───────────────┐ │ ║
║ │ │ /assess/*  │ │ /chat      │ │ /loans/*    │ │ /audit/*      │ │ ║
║ │ │ Valuation  │ │ Agentic NLP│ │ CHM Engine  │ │ LTV Audit     │ │ ║
║ │ └─────┬──────┘ └─────┬──────┘ └──────┬──────┘ └───────────────┘ │ ║
║ └───────┼──────────────┼───────────────┼──────────────────────────┘ ║
║         │              │               │                            ║
║    ┌────▼───────┐ ┌────▼────┐  ┌───────▼──────────────────────┐     ║
║    │ AI/ML Layer│ │  LLM    │  │  Async Task Layer (Celery)   │     ║
║    │ XGBoost +  │ │  Groq   │  │  Celery Worker Container     │     ║
║    │ SHAP       │ │  Llama  │  │  Celery Beat Container       │     ║
║    │ Groq VLM   │ │  3.3-70B│  └────────────┬─────────────────┘     ║
║    └────────────┘ └─────────┘               │                       ║
║                                    ┌────────▼───────┐               ║
║                                    │ PostgreSQL DB  │               ║
║                                    │ + Redis Cache  │               ║
║                                    └────────────────┘               ║
╚═════════════════════════════════════════════════════════════════════╝
```

### 🛠️ System Design Considerations

PropIQ has been engineered applying core system design principles to ensure enterprise-grade scalability, resilience, and performance:

1. **Decoupled Microservices Pattern**: The architecture strictly separates the presentation layer (React SPA) from the API Gateway (FastAPI). Heavy computational services (ML inference, LLM generation) are isolated via asynchronous worker nodes, allowing independent horizontal scaling based on bottleneck demands.
2. **Asynchronous Event-Driven Processing (Redis + Celery)**: Synchronous HTTP requests for intensive operations (like the 1,000+ loan Black Swan portfolio stress test) typically lead to gateway timeouts. We utilize Celery backed by a Redis message broker to offload these workloads to background worker pools, returning immediate asynchronous acknowledgments to the client.
3. **Database Connection Pooling & Concurrency**: To handle high concurrent read/write loads without starving the PostgreSQL instance, we implemented SQLAlchemy connection pooling (`pool_size=20, max_overflow=10`).
4. **Stateless API Nodes**: The FastAPI application instances maintain zero internal session state. All required context is extracted from JWTs or the centralized caching layer, ensuring the backend can be infinitely scaled behind a standard load balancer.
5. **Rate Limiting & Fault Tolerance**: Implementing the **API Gateway Pattern**, we use SlowAPI to enforce endpoint-specific rate limits (e.g., 20 requests/min on expensive Groq VLM endpoints) to prevent resource exhaustion. A global exception interceptor acts as a circuit breaker against cascading failures and prevents raw stack trace leakage.

### 🔄 Core Valuation Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as React Frontend
    participant API as FastAPI Gateway
    participant AI as AI Engine (Groq/XGBoost)
    participant Worker as Celery Task Queue
    participant DB as PostgreSQL DB

    User->>UI: Submits Property Details / Chat / Image
    UI->>API: POST /api/v1/assess
    note right of API:  Core Processing
    API->>DB: Fetch Local Circle Rates
    DB-->>API: Statutory Floor
    
    par Parallel Execution
        API->>AI: Agentic NLP parsing (if chat)
        API->>AI: Run XGBoost ML Model (18 Features)
        API->>AI: VLM Damage Scoring (if Images)
    end
    AI-->>API: Composite Market Value & SHAP
    API->>API: Compute RBI LTV & Risk Flags
    API->>DB: Save Audit Trail
    
    alt If Black Swan / Portfolio Batch
        API->>Worker: Trigger Async Stress Test
        Worker->>DB: Re-evaluate Active Loans
        Worker->>AI: Draft Escalation Memos
        Worker-->>DB: Update Stressed LTVs
    end
    
    API-->>UI: Return Full Credit Memo JSON
    UI-->>User: Display Bloomberg Terminal Dashboard
```

---

## 🧠 Valuation Logic & Liquidity Model

### Valuation Pipeline

```
Input Parameters
      │
      ▼
┌────────────────────┐
│ 1. Circle Rate Lookup│  ← RBI statutory floor per locality
│    (India DB)        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 2. XGBoost ML Model │  ← 18-feature prediction engine
│    Feature Inputs:  │
│    • Infrastructure │
│    • Listing Density│
│    • Zone Tier      │
│    • Age & Deprec.  │
│    • Legal Status   │
│    • Rental Yield   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 3. VLM Adjustment   │  ← Optional: −15% poor, −7% fair
│    (If images given)│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 4. SHAP Attribution │  ← Explainable per-feature contribution
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 5. RBI-LTV Calc     │  ← Max safe loan amount per guidelines
└─────────────────────┘
```

### Liquidity Model

The Resale Potential Index (RPI) is calculated as a weighted composite:

| Component                                         | Weight | Signal Source          |
| ------------------------------------------------- | ------ | ---------------------- |
| Asset Fungibility (property type standardization) | 30%    | Comparable sales mode  |
| Market Activity (listing density × absorption)    | 25%    | Local market proxies   |
| Location Demand (zone tier, infra score)          | 25%    | Circle rate enrichment |
| Legal Clarity (title, encumbrance, RERA)          | 20%    | Input flags            |

**RPI Interpretation:**

| Score  | Meaning                      | Distress Discount |
| ------ | ---------------------------- | ----------------- |
| 80–100 | Highly Liquid                | 10–15%            |
| 50–79  | Moderate Liquidity           | 20–28%            |
| < 50   | Illiquid / Specialized Asset | 30–40%            |

---

## 🖥️ The Bloomberg Terminal

PropIQ's frontend is built as a **multi-tab financial analysis dashboard** inspired by institutional trading terminals.

**Available Tabs:**
| Tab | Description |
|---|---|
| `Overview` | Exit Certainty Banner, Market Value Hero, LTV Gauge |
| `Drivers` | SHAP waterfall chart — per-feature rupee value attribution |
| `Risk` | All risk flags with severity levels and detailed reasoning |
| `Enrichment` | Zone tier, circle rate, infra score, geo-mapping |
| `Comps` | Comparable sales data and micro-market statistics |
| `Trends` | 24-month price momentum and listing velocity chart |
| `LTV` | RBI-compliant LTV calculation and max loan eligibility |
| `Memo` | LLM-generated formal credit assessment memo |
| `Terminal` | Raw financial analyst view — high-density data display |

**Key Features:**

- 📋 **Copy as JSON** — one-click full payload export for integration with legacy systems
- 📄 **Download PDF Credit Memo** — formatted, printable assessment for committee review
- 🗺️ **Interactive Map** — Leaflet-powered geo-visualization of the property location

---

## ⚡ Black Swan Simulator

The most powerful feature for risk teams — a **one-click macro-economic portfolio stress test**.

**How it works:**

1. Risk manager selects a shock magnitude (e.g., −20% sudden market crash)
2. PropIQ applies the shock to the current valuation of every active loan in the database
3. LTV ratios are re-calculated under stressed conditions in parallel
4. Loans that become "underwater" (Stressed LTV > 100%) are flagged
5. For each underwater loan, a **LLM generates an Internal Risk Escalation Memo** for the Credit Committee

**What the memo recommends (per Indian retail LAP norms):**

- 🔒 Immediate freeze on top-up loan requests
- 📊 Enhanced EMI monitoring schedule
- 🏷️ Tagging the account for Stage 2/3 provisioning under Ind AS 109

---

## 🚀 Practical Deployability

PropIQ is designed for **real-world production deployment**, not just a hackathon demo.

### ✅ Enterprise Readiness Checklist

| Feature                  | Implementation                  | Production Value                               |
| ------------------------ | ------------------------------- | ---------------------------------------------- |
| **Containerization**     | Full Docker Compose stack       | Deploy anywhere with `docker-compose up -d`    |
| **Connection Pooling**   | SQLAlchemy `pool_size=20`       | Handles high-concurrency without DB starvation |
| **Rate Limiting**        | SlowAPI on AI endpoints         | DDoS protection + API cost control             |
| **Deep Health Probes**   | Live Postgres + Redis check     | Kubernetes/AWS ALB auto-healing                |
| **Global Error Handler** | Catch-all exception interceptor | Prevents OWASP security leaks                  |
| **Async Task Queue**     | Celery + Redis workers          | Non-blocking heavy processing                  |
| **Scheduled Jobs**       | Celery Beat cron                | 30-day automated portfolio review              |
| **Audit Logging**        | PostgreSQL-backed audit trail   | Full regulatory traceability                   |
| **API Documentation**    | Auto-generated Swagger UI       | Ready for third-party integration              |

---

## 📡 API Reference

| Method | Endpoint                     | Description                                       | Rate Limit |
| ------ | ---------------------------- | ------------------------------------------------- | ---------- |
| `GET`  | `/api/v1/health`             | Deep dependency health probe                      | None       |
| `POST` | `/api/v1/assess`             | Standard full valuation                           | 20/min     |
| `POST` | `/api/v1/chat`               | **[AGENTIC]** NLP property extraction + valuation | 10/min     |
| `POST` | `/api/v1/assess/image`       | **[CV]** Valuation + VLM image damage scoring     | 20/min     |
| `POST` | `/api/v1/assess/full`        | **[KITCHEN-SINK]** All outputs in one call        | 20/min     |
| `POST` | `/api/v1/assess/batch`       | **[PORTFOLIO]** Bulk assess up to 50 properties   | —          |
| `POST` | `/api/v1/assess/pdf`         | Assessment + downloadable PDF report              | —          |
| `GET`  | `/api/v1/loans`              | List portfolio with health snapshots              | —          |
| `POST` | `/api/v1/loans`              | Add new loan (triggers immediate health check)    | —          |
| `POST` | `/api/v1/loans/health-check` | Trigger full portfolio re-assessment              | —          |
| `POST` | `/api/v1/loans/stress-test`  | **[BLACK SWAN]** Macro shock simulation           | —          |
| `GET`  | `/api/v1/comps`              | Query comparable sales for a locality             | —          |
| `GET`  | `/api/v1/trends/{locality}`  | 24-month price momentum tracking                  | —          |
| `GET`  | `/api/v1/audit/recent`       | System audit log (regulatory trail)               | —          |

Full interactive documentation: `http://localhost:8000/docs`

---

## 🤖 MLOps & AIML Platform

PropIQ runs a full production-grade ML lifecycle, not just a model file.

| Capability | Implementation | Endpoint / Location |
| ---------- | -------------- | ------------------- |
| **Feature store (train/serve parity)** | One canonical transform used by training AND serving — eliminates train/serve skew. Feast-backed (optional). | `app/ml/features.py`, `app/ml/feature_store.py`, `feature_repo/` |
| **Experiment tracking** | MLflow (local file store by default; UI at `:5000`) | `app/ml/tracking.py` |
| **Model registry + versioning** | Champion/challenger, stages, 1-click rollback | `GET /api/v1/ml/registry`, `POST /api/v1/ml/registry/promote/{version}` |
| **Realized-outcome loop** | Log every prediction; record actual sale/recovery; compute TRUE error | `POST /api/v1/outcomes`, `GET /api/v1/ml/performance` |
| **Drift monitoring** | PSI per feature + Evidently report | `GET /api/v1/ml/drift`, `GET /api/v1/ml/drift/report.html` |
| **Multi-model ensemble** | AVM + sales-comparison (kNN) + income approach, reconciled + calibrated band | `app/ml/ensemble.py` (in every `/assess` response under `ensemble_valuation`) |
| **Gated retraining** | data → train challenger → validate (MAPE + coverage gates) → promote only if it beats champion | `POST /api/v1/ml/retrain`, nightly/monthly Celery beat |
| **Model governance** | Model card + Responsible-AI notes | [`backend/MODEL_CARD.md`](backend/MODEL_CARD.md) |

> **Honesty note:** the model is currently trained on **synthetic** data, so the
> ~7% CV MAPE is *not* field accuracy. The realized-outcome loop is the mechanism
> that turns PropIQ into an empirically-grounded, self-improving system. See the
> model card for the full disclosure.

All MLOps services **degrade gracefully** — if MLflow/Feast/Redis are absent the
app still boots and serves; telemetry never breaks a request.

---

## 🧬 Deep AIML Capabilities

Beyond the MLOps spine, PropIQ ships a full modern AIML stack. **Every capability
has a graceful fallback**, so the one-command demo runs with zero extra installs;
installing the optional libs (chromadb, sentence-transformers, prophet, networkx)
upgrades each to its "rich" tier.

| Capability | What it does | Endpoint | Fallback when libs absent |
| ---------- | ------------ | -------- | ------------------------- |
| **RAG (grounded memos)** | Credit memos cite real RBI / internal-policy text from a vector knowledge base instead of free-form generation | `POST /api/v1/rag/query`, `GET /api/v1/rag/stats` | in-memory cosine + hashing embedder |
| **Agentic valuation agent** | LLM **plans and calls real tools** (circle rate → AVM → comps → ensemble → LTV → policy-RAG) to value collateral | `POST /api/v1/assess/agent` | deterministic plan still runs every tool |
| **Hallucination verifier** | Confirms **every number in the answer traces to a tool result**; flags unsupported claims | (in agent response `verification`) | regex numeric-trace check |
| **SSE streaming** | Live token-by-token memo, live agent trace, live portfolio health | `POST /api/v1/assess/narrate/stream`, `POST /api/v1/agent/stream`, `GET /api/v1/portfolio/stream` | hand-rolled `StreamingResponse` |
| **Learned forecasting** | Price forecast + confidence band (Prophet/Holt-Winters), momentum signal | `GET /api/v1/forecast/{locality}` | numpy trend+seasonal+residual CI |
| **Vector fraud detection** | Embeds each property; flags near-duplicate pledges & cross-borrower fraud rings | `POST /api/v1/fraud/duplicate-check`, `GET /api/v1/fraud/rings` | in-memory cosine |
| **Knowledge graph** | Portfolio concentration (HHI), developer-risk propagation, fraud-ring components | `GET /api/v1/graph/concentration`, `GET /api/v1/graph/developer-propagation` | dict adjacency + union-find |
| **Fairness / bias audit** | Disparate-impact (80% rule) by zone tier — fair-lending guardrail | `GET /api/v1/ml/fairness` | pure numpy/pandas |

**LLM provider** is pluggable behind `app/services/llm_provider.py` (Groq today;
swap is a one-file change). The agent, verifier and RAG memos all route through it.

> Example: `POST /api/v1/assess/agent` returns the agent's `agent_trace` (plan →
> each tool call → observation), the full `tool_ledger`, and a `verification`
> block proving every rupee figure is backed by a tool — not hallucinated.

---

## 🛠️ Tech Stack

| Layer                | Technology                                            |
| -------------------- | ----------------------------------------------------- |
| **Frontend**         | React 18, Recharts, Leaflet Maps, CSS3                |
| **Backend**          | Python 3.10, FastAPI, Pydantic v2                     |
| **Machine Learning** | XGBoost, SHAP, Scikit-learn                           |
| **AI / LLM**         | Groq (Llama-3.3-70B for NLP, Llama-3.2-Vision for CV) |
| **Database**         | PostgreSQL 15 (via SQLAlchemy ORM)                    |
| **Cache & Broker**   | Redis 7                                               |
| **Async Workers**    | Celery 5 + Celery Beat                                |
| **Containerization** | Docker, Docker Compose                                |
| **API Security**     | SlowAPI Rate Limiting, API Key Auth                   |
| **PDF Generation**   | ReportLab                                             |

---

## 🏁 Getting Started

PropIQ is fully containerized — the entire stack starts with a single command.

### Prerequisites

- **Docker Desktop** — [Install here](https://docs.docker.com/get-docker/) (required)
- **Groq API Key** — [Get free key here](https://console.groq.com/keys) (required for AI features)
- **Git** — [Install here](https://git-scm.com/downloads)

### Step-by-Step Setup

**1. Clone the repository**

```bash
git clone https://github.com/yourusername/propiq.git
cd propiq
```

**2. Configure environment variables**

Create a `.env` file in the root of the project:

```bash
# .env
GROQ_API_KEY=gsk_your_key_here
DATABASE_URL=postgresql://propiq:propiq_dev_2026@postgres:5432/propiq
REDIS_URL=redis://redis:6379/0
```

**3. Start the entire stack**

```bash
docker-compose up --build
```

This command automatically starts:

- 🌐 React Frontend on `http://localhost:3000`
- ⚙️ FastAPI Backend on `http://localhost:8000`
- 🗄️ PostgreSQL Database
- 📦 Redis Broker
- 👷 Celery Async Workers
- ⏰ Celery Beat Scheduler (30-day portfolio cron)

**4. Verify everything is running**

```bash
# Check service health (should show postgres: "up", redis: "up")
curl http://localhost:8000/api/v1/health

# Open the dashboard
open http://localhost:3000

# Open interactive API docs
open http://localhost:8000/docs
```

**5. Run the demo**

- Open `http://localhost:3000`
- Fill the property form (or use the **Agentic Chat** with a natural language description)
- Click **Assess** to generate a full valuation
- Navigate to **Portfolio Monitor** and click **⚡ Black Swan Simulator** to run a market shock

---

## 📁 Project Structure

```
propiq/
├── docker-compose.yml          # Full stack orchestration
├── .env                        # Environment variables (API keys)
│
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── ResultsDashboard.js    # Bloomberg Terminal UI (9-tab)
│       │   ├── PortfolioMonitor.js    # CHM Dashboard + Black Swan
│       │   ├── AssessmentForm.js      # Property input form
│       │   └── BloombergTerminal.js   # Analyst-mode view
│       └── App.js
│
└──backend/
    └── app/
        ├── main.py                # FastAPI app, all API routes
        ├── core/
        │   ├── config.py          # App configuration
        │   ├── db.py              # PostgreSQL + connection pooling
        │   ├── security.py        # API key authentication
        │   ├── celery_app.py      # Celery + Beat scheduler config
        │   └── tasks.py           # Async background tasks
        ├── ml/
        │   ├── valuation_model.py # XGBoost + SHAP engine
        │   └── cv_module.py       # Groq VLM image analyzer
        ├── services/
        │   ├── chm_engine.py      # Portfolio health + stress testing
        │   ├── llm_narration.py   # LLM credit memos + risk alerts
        │   ├── comps_engine.py    # Comparable sales engine
        │   ├── ltv_audit.py       # RBI LTV calculation engine
        │   ├── pdf_report.py      # PDF generation
        │   └── enrichment.py      # Location enrichment layer
        └── data/
            └── india_circle_rates.py  # 39-locality circle rate DB
```

---

<div align="center">
