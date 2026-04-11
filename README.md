# MyAIDoctor — Multi-Agent Medical Diagnostic System
 
An AI-powered diagnostic assistant built on a **LangGraph Reflexion loop** with three specialised agents — a Diagnostic Lead, a Skeptical Specialist, and a Clinical Researcher. Users describe their symptoms in a chat interface and receive a structured differential diagnosis, evidence-backed treatment options, and a final medical report sourced from trusted clinical databases.

> **Disclaimer:** MyAIDoctor is an educational simulation tool. It does not replace professional medical advice, diagnosis, or treatment. Always consult a licensed healthcare provider.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment Variables](#environment-variables)
  - [Running with Docker (recommended)](#running-with-docker-recommended)
  - [Running Locally (without Docker)](#running-locally-without-docker)
- [Groq API Key Rotation](#groq-api-key-rotation)
- [API Reference](#api-reference)
- [Running Tests](#running-tests)
- [Linting & Type Checking](#linting--type-checking)
- [Screenshots](#screenshots)

---

## Features

- **Multi-agent diagnostic workflow** — three agents collaborate and challenge each other through a Reflexion loop before producing a final report
- **Live medical research** — Tavily searches trusted clinical sources (NIH, Mayo Clinic, CDC, WHO, PubMed); Firecrawl scrapes full guideline pages for deep context
- **Human-in-the-loop (HITL)** — the Skeptical Specialist pauses the workflow to ask the patient follow-up questions before continuing
- **Structured medical report** — final output includes differential diagnosis with ICD codes, confidence scores, treatment recommendations, evidence log, and disclaimer
- **Groq API key rotation** — automatically rotates across multiple free-tier API keys when a rate limit is hit; each exhausted key gets a 65-second cooldown before re-entering the pool
- **User authentication** — JWT-based register/login with per-user session isolation
- **Multiple conversation sessions** — users can keep and switch between independent diagnostic conversations
- **Fully responsive UI** — works on desktop, tablet, and mobile; glassmorphic design with WebGL background shaders
- **Local demo mode** — run the full app without any API keys using a deterministic mock LLM (`LOCAL_DEMO=1`)
- **Observability** — optional LangSmith tracing for every agent run

---

## Architecture

### Agent Workflow (LangGraph)

```
User message
      │
      ▼
  ┌─────────┐
  │  intake  │  ── routes to ──────────────────────────────┐
  └─────────┘                                              │
       │ diagnostic_flow / tool_research                   │ direct_answer
       ▼                                                   │
  ┌─────────┐   needs_research   ┌────────────┐           │
  │  actor  │ ─────────────────► │ researcher │           │
  │(Dx Lead)│ ◄───────────────── │(Tavily +   │           │
  └─────────┘   returns results  │ Firecrawl) │           │
       │                         └────────────┘           │
       ▼                                                   │
  ┌─────────┐  needs_clarification  ┌──────────────┐      │
  │ skeptic │ ─────────────────────►│ HITL: patient│      │
  │(Critic) │ ◄─────────────────── │ answers Q     │      │
  └─────────┘                       └──────────────┘      │
       │                                                   │
       │ resolved / max_reflections                        │
       ▼                                                   │
  ┌─────────┐                                             │
  │  report │ ◄───────────────────────────────────────────┘
  │  node   │
  └─────────┘
       │
       ▼
 Final Report (JSON)
 ├── summary_of_findings
 ├── differential_diagnosis  [ { condition, confidence, icd_hint, evidence } ]
 ├── treatment_recommendations [ { drug_or_class, role, dosing_note, cautions } ]
 ├── recommended_next_steps
 ├── evidence_log  [ { title, url, snippet } ]
 └── metadata.disclaimer
```

| Agent | Role |
|---|---|
| **Intake** | Classifies the user message (diagnostic flow, tool research, or direct answer) |
| **Actor (Diagnostic Lead)** | Senior internal medicine persona — proposes a ranked differential diagnosis with confidence scores |
| **Skeptic (Skeptical Specialist)** | Devil's advocate — critiques the diagnosis, flags gaps, asks follow-up questions, triggers research |
| **Researcher (Clinical Researcher)** | Searches Tavily + scrapes pages via Firecrawl from trusted medical domains |
| **Report** | Assembles the final structured JSON report from the accumulated state |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 14, React 18, TypeScript, custom CSS (glassmorphism, WebGL shaders) |
| **Backend** | FastAPI, Python 3.11, Uvicorn |
| **Database** | PostgreSQL 16 |
| **ORM / Migrations** | SQLAlchemy 2.0, Alembic |
| **Authentication** | JWT (python-jose, passlib/bcrypt) |
| **Agent Framework** | LangGraph, LangChain |
| **LLM** | Groq `llama-3.3-70b-versatile` (with multi-key rotation), OpenAI `gpt-4o-mini` (fallback) |
| **Web Research** | Tavily (search), Firecrawl (scrape) |
| **Observability** | LangSmith |
| **Containerisation** | Docker, Docker Compose |
| **Code Quality** | Ruff, mypy, pytest |

---

## Project Structure

```
MyAIDoctor/
├── backend/
│   ├── agents/
│   │   ├── actor.py          # Diagnostic Lead agent
│   │   ├── skeptic.py        # Skeptical Specialist agent
│   │   └── researcher.py     # Clinical Researcher agent (Tavily + Firecrawl)
│   ├── graph/
│   │   ├── graph.py          # LangGraph workflow definition
│   │   ├── nodes.py          # Node wrappers for each agent
│   │   ├── edges.py          # Conditional routing logic
│   │   ├── state.py          # DiagnosticState schema
│   │   └── medication_intent.py
│   ├── app/
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── api/              # Route handlers (auth, sessions, chat, reports)
│   │   ├── core/             # Config, security (JWT)
│   │   ├── db/               # SQLAlchemy models & session
│   │   ├── services/         # Orchestrator (runs the LangGraph per request)
│   │   └── schemas.py        # Pydantic request/response models
│   ├── utils/
│   │   ├── llm.py            # LLM factory with Groq key rotation
│   │   ├── report.py         # Report generation helpers
│   │   ├── logging.py        # Structured logger
│   │   └── tracing.py        # LangSmith tracing helpers
│   ├── migrations/           # Alembic migration scripts
│   ├── tests/                # Pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── chat/page.tsx     # Main chat interface
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   ├── sessions/[id]/    # Session detail view
│   │   ├── reports/[id]/     # Report detail view
│   │   ├── layout.tsx
│   │   └── globals.css       # Design system (tokens, glassmorphism, responsive)
│   ├── components/
│   │   ├── AuthGuard.tsx     # Route protection
│   │   ├── ChatShader.tsx    # WebGL background shader (desktop only)
│   │   └── MedicalShaderBackground.tsx
│   ├── lib/api.ts            # Typed API client
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── pyproject.toml            # Ruff, mypy, pytest config
└── .env                      # Environment variables (never commit)
```

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (recommended), **or**
- Python 3.11+ and Node.js 18+ for local development

### Environment Variables

Copy `.env.example` to `.env` (or edit `.env` directly) and fill in your keys:

```env
# ── LLM ───────────────────────────────────────────────────────────────────────
# Primary Groq key (required unless LOCAL_DEMO=1)
GROQ_API_KEY=gsk_...

# Additional Groq keys for automatic rotation when rate limits are hit
GROQ_API_KEY_2=gsk_...
GROQ_API_KEY_3=gsk_...
# Add as many as you have: GROQ_API_KEY_4, GROQ_API_KEY_5, …

# OpenAI fallback (optional — used if no Groq key is found)
OPENAI_API_KEY=sk-...

# ── Research tools ────────────────────────────────────────────────────────────
TAVILY_API_KEY=tvly-...
FIRECRAWL_API_KEY=fc-...

# ── Observability (optional) ──────────────────────────────────────────────────
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=MyAIDoctor
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# ── Demo mode ─────────────────────────────────────────────────────────────────
# Set to 1 to run the full app without any API keys (uses a deterministic mock LLM)
LOCAL_DEMO=0
```

> **Free API keys:**
> - Groq — [console.groq.com](https://console.groq.com) (free tier available)
> - Tavily — [app.tavily.com](https://app.tavily.com) (free tier available)
> - Firecrawl — [firecrawl.dev](https://www.firecrawl.dev) (free tier available)

---

### Running with Docker (recommended)

```bash
# 1. Clone the repository
git clone https://github.com/sharif2552/MyAIDoctor.git
cd MyAIDoctor

# 2. Create your .env file and add your API keys (see above)
cp .env.example .env   # then edit .env

# 3. Start all services (PostgreSQL + FastAPI backend + Next.js frontend)
docker compose up --build

# 4. Run database migrations (first time only)
docker compose exec backend alembic upgrade head
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

---

### Running Locally (without Docker)

**Backend**

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
pip install -r requirements-dev.txt   # dev/test tools

# Start a local PostgreSQL instance and update DATABASE_URL in .env, then:
alembic upgrade head

# Run the API server
uvicorn backend.app.main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev        # starts on http://localhost:3000
```

---

## Groq API Key Rotation

MyAIDoctor automatically rotates across multiple Groq API keys when a free-tier rate limit (HTTP 429) is hit.

**How it works:**

1. All configured keys are loaded at startup into a `RotatingGroqLLM` wrapper
2. Every `invoke()` call tries the current active key
3. On a 429 error, the key is marked on a **65-second cooldown** (matching Groq's 1-minute rate window), and the next available key is selected instantly
4. The same request is retried on the new key with no disruption to the user
5. After 65 seconds, cooled-down keys automatically become eligible again
6. If every key is simultaneously exhausted, a clear error is returned

**Adding more keys:**

```env
GROQ_API_KEY=gsk_...      # key 1 — always required
GROQ_API_KEY_2=gsk_...    # key 2
GROQ_API_KEY_3=gsk_...    # key 3
GROQ_API_KEY_4=gsk_...    # key 4 — add as many as you have
```

No code changes are needed — the factory picks up all numbered keys automatically on the next restart.

---

## API Reference

All endpoints are prefixed with `http://localhost:8000`. Interactive docs are at `/docs`.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login and receive a JWT token |

### Sessions

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/sessions` | List all sessions for the authenticated user |
| `POST` | `/sessions` | Create a new diagnostic session |
| `GET` | `/sessions/{id}/messages` | Retrieve the message history for a session |

### Chat

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat/{session_id}` | Send a message and run the diagnostic workflow |
| `POST` | `/chat/{session_id}/hitl` | Submit an answer to a HITL follow-up question |
| `GET` | `/chat/{session_id}/report` | Retrieve the final structured medical report |

### Health

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Returns `{ "status": "ok" }` |

**Authentication header** (required for all session/chat endpoints):

```
Authorization: Bearer <token>
```

---

## Running Tests

```bash
# Run the full test suite
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest backend/tests/test_llm.py
```

Tests use `LOCAL_DEMO=1` (via `monkeypatch`) so no real API keys are needed to run them.

---

## Linting & Type Checking

```bash
# Lint and auto-fix with Ruff
ruff check . --fix

# Type check with mypy
mypy .
```

Configuration lives in `pyproject.toml`.

---

## Screenshots

> _Chat interface with slide-in conversation drawer, glassmorphic design, and WebGL background._

| Desktop | Mobile |
|---|---|
| Full chat with sidebar drawer | Hamburger menu, full-bleed layout |

---

## License

This project is for educational and demonstration purposes. No license for production medical use is granted or implied.
