<div align="center">

<h1>🤖 Simple AI Chatbot Backend</h1>

<p>
  <strong>A production-grade, multi-user, memory-aware AI chatbot API with conflict resolution, streaming, distributed tracing, and LLM self-evaluation</strong>
</p>

<p>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.136-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/OpenAI-GPT-412991?style=for-the-badge&logo=openai&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/OpenTelemetry-Jaeger-FF6600?style=for-the-badge&logo=opentelemetry&logoColor=white" />
</p>

<p>
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" />
  <img src="https://img.shields.io/badge/Alembic-Migrations-13A8E5?style=for-the-badge" />
  <img src="https://img.shields.io/badge/SlowAPI-Rate_Limiting-8A2BE2?style=for-the-badge" />
  <img src="https://img.shields.io/badge/SSE-Streaming-22C55E?style=for-the-badge" />
</p>

<p>
  <img src="https://img.shields.io/badge/version-0.1.0-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" />
  <img src="https://img.shields.io/badge/status-active-brightgreen?style=flat-square" />
</p>

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [What's New in This Version](#-whats-new-in-this-version)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Memory System Deep Dive](#-memory-system-deep-dive)
- [Memory Conflict Resolution](#-memory-conflict-resolution)
- [LLM Self-Evaluation Pipeline](#-llm-self-evaluation-pipeline)
- [Observability & Tracing](#-observability--tracing)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Development Setup](#local-development-setup)
  - [Docker Setup (Recommended)](#docker-setup-recommended)
- [Environment Variables](#-environment-variables)
- [API Reference](#-api-reference)
- [Database Schema](#-database-schema)
- [Migration History](#-migration-history)
- [Configuration Tuning](#-configuration-tuning)
- [Roadmap](#-roadmap)

---

## 🌟 Overview

**Simple AI Chatbot Backend** is a production-grade REST API that powers a persistent, multi-user, memory-aware conversational AI assistant. Built on **FastAPI** and **OpenAI GPT**, it goes far beyond a stateless chatbot by implementing a sophisticated three-layer memory architecture — short-term message history, compressed summaries, and long-term user facts — with a dedicated **memory conflict resolution workflow**, **Server-Sent Events streaming**, **distributed tracing via OpenTelemetry + Jaeger**, **per-IP rate limiting**, and an **LLM self-evaluation pipeline** that quality-checks every AI response in real time.

---

## 🆕 What's New in This Version

This release is a significant upgrade from the initial implementation. The following capabilities have been added:

| Area | What Changed |
|---|---|
| 👥 **Multi-user support** | All memory and conversations are now scoped to a `user_id`. A `users` table anchors all data. |
| ⚡ **SSE Streaming** | `POST /api/v1/chat/stream` — token-by-token streaming with Server-Sent Events and client disconnect detection |
| 🔀 **Memory Conflict Resolution** | When extracted facts contradict stored memory, a conflict is staged and the user is asked to confirm or reject the update |
| 🧪 **LLM Self-Evaluation** | Every LLM operation (reply generation, fact extraction, confirmation classification) is automatically evaluated and logged to `llm_eval_results` |
| 📡 **Distributed Tracing** | Full OpenTelemetry integration with Jaeger exporter — every request traced across FastAPI and SQLAlchemy |
| 🚦 **Rate Limiting** | SlowAPI-powered per-IP rate limits: 10/min on chat endpoints, 30/min on conversation listing |
| 🆔 **Trace Middleware** | `X-Trace-ID` header propagated through every request and response |
| 📋 **Conversations API** | New `GET /api/v1/conversations/` endpoint to list a user's conversations with summaries and last activity |
| 🧠 **Memory Confidence Scoring** | Long-term memories now track `confidence`, `evidence_count`, and `source` |
| ⏱️ **Conflict TTL** | Pending memory conflicts auto-expire after a configurable TTL (default 24 hours) |
| 🗂️ **Structured Memory Keys** | Predefined keys (`name`, `location`, `goal`, `profession`, `favorite_language`) with `dynamic_` prefix support for free-form facts |

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🧠 **Three-Layer Memory** | Long-term user facts + conversation summaries + recent message history |
| 🔄 **Auto-Summarization** | Compresses old messages into summaries when a threshold is reached |
| 👤 **User Fact Extraction** | Automatically extracts stable user facts from messages using LLM |
| 🔀 **Conflict Resolution** | Contradictory memory updates are staged as `pending` and require user confirmation |
| 🏃 **Quick Confirm Detection** | Regex-based fast-path for common yes/no phrases before calling the LLM classifier |
| ⚡ **SSE Streaming** | Real-time token-by-token responses with graceful client disconnect handling |
| 🧪 **Self-Evaluation** | Every LLM operation is auto-evaluated against quality criteria and persisted |
| 📡 **Distributed Tracing** | OpenTelemetry + Jaeger traces every request across HTTP, DB, and LLM calls |
| 🚦 **Rate Limiting** | Per-IP limits via SlowAPI with configurable thresholds |
| 🆔 **Trace Propagation** | `X-Trace-ID` threaded through all requests, logs, and responses |
| 🗃️ **Persistent Storage** | All data in PostgreSQL via SQLAlchemy 2.0 ORM with cascading deletes |
| 📦 **Alembic Migrations** | 8-migration history with full up/down support |
| ❤️ **Health + Readiness** | `/health` and `/ready` endpoints for Kubernetes-style health probes |
| 🔒 **Input Validation** | Pydantic v2 schemas with field constraints on all inputs |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          CLIENT (HTTP / SSE)                         │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                   POST /api/v1/chat/   or   /chat/stream
                   GET  /api/v1/conversations/
                                 │
┌────────────────────────────────▼─────────────────────────────────────┐
│                        FastAPI Application                           │
│                                                                      │
│  ┌──────────────────┐   ┌──────────────────────────────────────┐    │
│  │ TraceMiddleware  │   │         SlowAPI Rate Limiter          │    │
│  │ X-Trace-ID inject│   │  10/min (chat)  30/min (convos)      │    │
│  └──────────────────┘   └──────────────────────────────────────┘    │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                     API Layer  (v1/)                          │  │
│  │                                                               │  │
│  │  chat.py                            conversations.py          │  │
│  │  ├── POST /chat/                    └── GET /conversations/   │  │
│  │  └── POST /chat/stream                                        │  │
│  └──────┬──────────────────────────────────────────────────┬────┘  │
│         │                                                   │       │
│  ┌──────▼──────────┐  ┌──────────────────┐  ┌─────────────▼─────┐ │
│  │  Memory Service │  │   LLM Service    │  │  Conversation Repo│ │
│  │                 │  │                  │  │                   │ │
│  │ build_context() │  │ generate_reply() │  │ list_by_user()    │ │
│  │ add_message()   │  │ stream_reply()   │  └───────────────────┘ │
│  │ should_summ.()  │  │ summarize_msgs() │                        │
│  │ compress_conv() │  │ extract_facts()  │                        │
│  └──────┬──────────┘  │ detect_confirm() │                        │
│         │             └──────────┬───────┘                        │
│  ┌──────▼────────────────────────▼──────────────────────────────┐  │
│  │                   Supporting Services                         │  │
│  │                                                               │  │
│  │  LongTermMemoryService      PendingMemoryService              │  │
│  │  update_memory()            set_pending_conflicts()           │  │
│  │  force_update_memory()      get_pending_conflicts()           │  │
│  │  format_for_prompt()        clear_pending_conflicts()         │  │
│  │                                                               │  │
│  │  ConfirmationService        EvalService                       │  │
│  │  quick_confirm()            evaluate_response()               │  │
│  │  (fast regex path)          evaluate_memory_extraction()      │  │
│  │                             evaluate_confirmation_class()     │  │
│  └──────────────────────────────┬────────────────────────────────┘  │
│                                 │                                    │
│  ┌──────────────────────────────▼────────────────────────────────┐  │
│  │              ConversationRepository (SQLAlchemy ORM)          │  │
│  │          Single source of truth for all DB operations         │  │
│  └──────────────────────────────┬────────────────────────────────┘  │
└─────────────────────────────────┼────────────────────────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
   ┌──────────────────┐  ┌──────────────┐  ┌─────────────────────┐
   │   PostgreSQL 16  │  │  OpenAI API  │  │   Jaeger (OTLP)     │
   │                  │  │  GPT model   │  │                     │
   │  users           │  │              │  │  UI:   port 16686   │
   │  conversations   │  │  Timeout 20s │  │  gRPC: port 4317    │
   │  chat_messages   │  │  Retries 2   │  │                     │
   │  long_term_mem.  │  │              │  │  Traces: FastAPI    │
   │  pending_conf.   │  │              │  │          SQLAlchemy │
   │  llm_eval_res.   │  │              │  │          Custom     │
   └──────────────────┘  └──────────────┘  └─────────────────────┘
```

---

## 🧠 Memory System Deep Dive

The chatbot uses a **three-layer memory architecture** to deliver contextual, token-efficient conversations:

```
Every Chat Request
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│  Layer 1 — Long-Term Memory  (User-Scoped, Persistent)        │
│                                                               │
│  • LLM extracts facts from EVERY user message                 │
│  • Stored per user_id — persists across ALL conversations     │
│  • Tracks: confidence, evidence_count, source                 │
│  • Structured keys: name, location, goal, profession,         │
│    favorite_language                                          │
│  • Free-form facts use the dynamic_ prefix                    │
│  • Conflicts → staged as PendingMemoryConflict (see below)    │
│  • Injected as system message at start of every context       │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│  Layer 2 — Conversation Summary  (Per-Conversation)           │
│                                                               │
│  • Triggered when message count ≥ SUMMARY_TRIGGER (def. 12)  │
│  • LLM generates concise summary preserving goals/decisions   │
│  • Old messages pruned; RECENT_MESSAGES_AFTER_SUMMARY kept    │
│  • Summary prepended as system message in context             │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│  Layer 3 — Recent Message History  (Short-Term)               │
│                                                               │
│  • Last MAX_HISTORY_MESSAGES messages (default: 10)           │
│  • Full role + content sent to the LLM                        │
│  • Provides immediate conversational context                  │
└───────────────────────────────────────────────────────────────┘
```

Long-term memories are **user-scoped** — if a user tells the chatbot their name in Conversation A, it will remember it in Conversation B.

---

## 🔀 Memory Conflict Resolution

When extracted facts **contradict** existing long-term memory, the system stages a conflict and asks the user to decide — it never silently overwrites:

```
User says: "Actually, I moved to London last month."
        │
        ▼  LLM extracts: { location: "London" }
        │
        ▼  Repository checks existing memory: location = "Colombo"
        │
   ┌────┴──────────────────────────────────────────────┐
   │  Conflict detected                                 │
   │  key:       location                               │
   │  old_value: "Colombo"                              │
   │  new_value: "London"                               │
   └────┬──────────────────────────────────────────────┘
        │
        ▼  PendingMemoryConflict row inserted
           status = "pending"  |  TTL = 24h
        │
        ▼  LLM prompted to ask user for confirmation
           "Should I update your location from Colombo to London?"
        │
        ├──────────────────────────────────────────────────┐
        │ User: "yes" / "y" / "sure"                       │ User: "no" / "nope"
        ▼                                                   ▼
  ConfirmationService.quick_confirm() → "confirm"   → "reject"
        │ (ambiguous? → LLM detect_memory_confirmation)    │
        ▼                                                   ▼
  force_update_memory()                         Keep old memory
  status → "confirmed"                          status → "rejected"
        │                                                   │
        └──────────────┬────────────────────────────────────┘
                       ▼
         EvalService logs classification result
         to llm_eval_results with trace_id
```

**Design highlights:**
- `ConfirmationService.quick_confirm()` runs first — avoids an LLM call for simple yes/no responses
- Only ambiguous messages fall through to `llm_service.detect_memory_confirmation()`
- Both paths are evaluated and stored in `llm_eval_results`
- Pending conflicts auto-expire via `PENDING_CONFLICT_TTL_HOURS` to prevent stale state

---

## 🧪 LLM Self-Evaluation Pipeline

Every LLM operation is automatically quality-checked and the result persisted to `llm_eval_results`. This creates an audit trail of AI output quality across all operations:

| Operation | Criteria Checked | Logged As |
|---|---|---|
| `generate_reply` | Not empty, length 5–3000 chars | `llm_eval_results` |
| `stream_reply` | Same as above, evaluated post-stream | `llm_eval_results` |
| `extract_user_facts` | ≤10 keys, valid string types, no empty values, no nested objects | `llm_eval_results` |
| `detect_memory_confirmation` | Result must be one of `confirm`, `reject`, `unclear` | `llm_eval_results` |

Each record stores:

| Column | Description |
|---|---|
| `trace_id` | Links back to the originating HTTP request |
| `operation` | Which LLM function was evaluated |
| `passed` | Boolean quality gate result |
| `issues` | JSON array of specific failure reasons |
| `metadata_json` | Operation-specific context (reply length, extracted key count, etc.) |

All eval spans are also exported to **Jaeger** for distributed trace correlation.

---

## 📡 Observability & Tracing

The application ships with full **OpenTelemetry** instrumentation, exporting traces to **Jaeger**:

```
HTTP Request arrives
        │
        ▼  TraceMiddleware
           Reads or generates X-Trace-ID
           Attaches to request.state.trace_id
           Echoes in response headers
        │
        ▼  FastAPIInstrumentor
           Auto-traces all HTTP routes, middleware timing
        │
        ▼  SQLAlchemyInstrumentor
           Auto-traces every DB query with table + operation
        │
        ▼  Custom EvalService spans:
           eval.response_quality
           eval.memory_extraction
           eval.confirmation_classification
        │
        ▼  BatchSpanProcessor
           → OTLPSpanExporter
           → Jaeger gRPC (port 4317)
```

**Accessing Jaeger UI** (when running via Docker Compose):

```
http://localhost:16686
```

Select service `ai-chatbot`. Each trace shows the full request lifecycle: HTTP routing → DB queries → LLM calls → eval spans.

**Structured log fields** included on every log entry:

| Field | Description |
|---|---|
| `trace_id` | Correlation ID for the request |
| `user_id` | The user making the request |
| `conversation_id` | The active conversation |
| `event` | Event name: `chat_request`, `chat_failed`, `llm_eval_result`, etc. |

---

## 📁 Project Structure

```
.
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── chat.py                  # POST /chat/ and POST /chat/stream
│   │       └── conversations.py         # GET /conversations/
│   ├── core/
│   │   ├── config.py                    # Settings via pydantic-settings + .env
│   │   ├── logger.py                    # Per-module structured logger setup
│   │   ├── memory_config.py             # Structured keys + dynamic_ prefix
│   │   ├── rate_limiter.py              # SlowAPI limiter (per-IP, 30/min default)
│   │   └── telemetry.py                 # OpenTelemetry setup → Jaeger OTLP exporter
│   ├── db/
│   │   ├── database.py                  # SQLAlchemy engine + session factory
│   │   ├── health.py                    # DB health probe helper
│   │   └── models.py                    # ORM models: User, Conversation, ChatMessage,
│   │                                    #   LongTermMemory, PendingMemoryConflict,
│   │                                    #   LLMEvalResult
│   ├── middleware/
│   │   └── trace_middleware.py          # X-Trace-ID inject/propagate middleware
│   ├── repositories/
│   │   └── conversation_repository.py  # All DB operations (single access point)
│   ├── schemas/
│   │   ├── chat.py                      # ChatRequest / ChatResponse (Pydantic v2)
│   │   └── conversation.py              # ConversationListItem schema
│   ├── services/
│   │   ├── llm_service.py               # OpenAI: reply, stream, summarize,
│   │   │                                #   extract_facts, detect_confirmation
│   │   ├── memory_service.py            # Short-term + summary orchestration
│   │   ├── long_term_memory.py          # User-scoped persistent fact management
│   │   ├── pending_memory_service.py    # Conflict staging and resolution
│   │   ├── confirmation_service.py      # Fast regex + LLM confirmation classifier
│   │   └── eval_service.py              # LLM output quality evaluation + logging
│   └── main.py                          # FastAPI app factory + middleware + routers
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/                        # 8 migrations (see Migration History)
├── Dockerfile                           # Python 3.12-slim image
├── docker-compose.yml                   # API + PostgreSQL 16 + Jaeger all-in-one
├── alembic.ini                          # Alembic configuration
├── requirements.txt                     # Pinned Python dependencies
└── run.py                               # Local dev entry point (uvicorn --reload)
```

---

## 🛠️ Tech Stack

| Layer | Technology | Version |
|---|---|---|
| **Runtime** | Python | 3.12 |
| **Web Framework** | FastAPI | 0.136.1 |
| **ASGI Server** | Uvicorn | 0.46.0 |
| **LLM Provider** | OpenAI Python SDK | 2.32.0 |
| **ORM** | SQLAlchemy | 2.0.49 |
| **Migrations** | Alembic | 1.18.4 |
| **Database** | PostgreSQL | 16 |
| **DB Driver** | psycopg2-binary | 2.9.12 |
| **Validation** | Pydantic v2 | 2.13.3 |
| **Config** | pydantic-settings | 2.14.0 |
| **Rate Limiting** | SlowAPI | 0.1.9 |
| **Tracing SDK** | OpenTelemetry | 1.41.1 |
| **Trace Backend** | Jaeger all-in-one | latest |
| **Containerization** | Docker + Compose | — |

---

## 🚀 Getting Started

### Prerequisites

- **Python** 3.12+
- **PostgreSQL** 16 (or Docker)
- **OpenAI API Key** — [Get one here](https://platform.openai.com/api-keys)
- **Docker & Docker Compose** (recommended — includes Jaeger)

---

### Local Development Setup

**1. Clone the repository**

```bash
git clone https://github.com/your-username/simple-ai-chatbot.git
cd simple-ai-chatbot
```

**2. Create and activate a virtual environment**

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

```bash
cp .env.example .env
# Edit .env — see Environment Variables section
```

**5. Run database migrations**

```bash
alembic upgrade head
```

**6. Start the development server**

```bash
python run.py
```

API: **http://127.0.0.1:8000** | Swagger UI: **http://127.0.0.1:8000/docs**

> ⚠️ In local mode without Jaeger running, OpenTelemetry traces will silently fail. The API will function normally.

---

### Docker Setup (Recommended)

The Docker Compose stack runs **three services**: the API, PostgreSQL, and Jaeger.

**1. Create the Docker environment file**

```bash
cp .env.example .env.docker
```

Edit `.env.docker` — set `DATABASE_URL` to use the Docker service name:

```env
DATABASE_URL=postgresql://chatbot_user:chatbot_password@db:5432/simple_chatbot
OPENAI_API_KEY=sk-...
```

**2. Build and start all services**

```bash
docker compose up --build
```

This will:
- Start **PostgreSQL 16** with a health check (API waits for `pg_isready`)
- Start **Jaeger all-in-one** (UI on `16686`, OTLP gRPC on `4317`)
- Build and launch the **API container**
- Automatically run `alembic upgrade head` before Uvicorn starts

**3. Verify all services**

```bash
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

**4. Open the Jaeger tracing UI**

```
http://localhost:16686
```

Select service `ai-chatbot` to explore distributed traces.

**Manage the stack**

```bash
docker compose logs -f api        # Tail API logs
docker compose down               # Stop, keep DB volume
docker compose down -v            # Stop + delete DB volume
```

---

## 🔧 Environment Variables

```env
# ─── Application ─────────────────────────────────────────────────────
APP_NAME=Simple AI Chatbot
APP_VERSION=0.1.0
ENVIRONMENT=development            # development | production

# ─── OpenAI ──────────────────────────────────────────────────────────
OPENAI_API_KEY=sk-...              # Required
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT_SECONDS=20
OPENAI_MAX_RETRIES=2

# ─── Database ────────────────────────────────────────────────────────
DATABASE_URL=postgresql://chatbot_user:chatbot_password@localhost:5432/simple_chatbot

# ─── Memory ──────────────────────────────────────────────────────────
MAX_HISTORY_MESSAGES=10
SUMMARY_TRIGGER_MESSAGES=12
RECENT_MESSAGES_AFTER_SUMMARY=6

# ─── Conflict Resolution ─────────────────────────────────────────────
PENDING_CONFLICT_TTL_HOURS=24
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | ✅ | — | OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-40-mini` | GPT model to use |
| `OPENAI_TIMEOUT_SECONDS` | No | `20` | Per-call timeout in seconds |
| `OPENAI_MAX_RETRIES` | No | `2` | Retry count on OpenAI failures |
| `DATABASE_URL` | ✅ | — | PostgreSQL connection string |
| `MAX_HISTORY_MESSAGES` | No | `10` | Recent messages included in each context |
| `SUMMARY_TRIGGER_MESSAGES` | No | `12` | Message count that triggers auto-summarization |
| `RECENT_MESSAGES_AFTER_SUMMARY` | No | `6` | Messages retained after compression |
| `PENDING_CONFLICT_TTL_HOURS` | No | `24` | Hours before unresolved conflicts auto-expire |

---

## 📡 API Reference

### Base URL

```
http://localhost:8000
```

---

### System Endpoints

| Method | Path | Description | Rate Limit |
|---|---|---|---|
| `GET` | `/` | App status + environment | — |
| `GET` | `/health` | Liveness probe — checks DB | — |
| `GET` | `/ready` | Readiness probe — checks DB | — |

**`GET /health` response:**
```json
{ "status": "healthy", "database": "connected" }
```

---

### `POST /api/v1/chat/`

Send a message and receive a complete reply. Rate limit: **10 requests/min per IP**.

**Request Headers**

| Header | Description |
|---|---|
| `X-Trace-ID` | Optional. Propagated through request/response. Auto-generated if absent. |

**Request Body**

```json
{
  "user_id": "user-abc-123",
  "message": "Hi, my name is Oshan and I work as a Python developer in Colombo.",
  "conversation_id": "optional-existing-uuid"
}
```

| Field | Type | Required | Constraints |
|---|---|---|---|
| `user_id` | `string` | ✅ | min length 1 |
| `message` | `string` | ✅ | 1–1000 chars |
| `conversation_id` | `string` | No | UUID of existing conversation to continue |

**Response — 200 OK**

```json
{
  "reply": "Nice to meet you, Oshan! Python is a great choice for developers...",
  "user_id": "user-abc-123",
  "conversation_id": "3f7a2d91-14bc-4e88-bf32-2c3a9c8f1234"
}
```

> 💡 Save the `conversation_id` and pass it in subsequent requests to maintain context.

---

### `POST /api/v1/chat/stream`

Send a message and receive a **Server-Sent Events** stream of tokens. Rate limit: **10 requests/min per IP**.

**Request Body** — same as `POST /api/v1/chat/`

**Response** — `Content-Type: text/event-stream`

```
event: token
data: Hello

event: token
data: , Oshan

event: token
data: ! How can I help?

event: done
data: 3f7a2d91-14bc-4e88-bf32-2c3a9c8f1234
```

| Event | Data | Meaning |
|---|---|---|
| `token` | Text chunk | One token/chunk from the LLM stream |
| `done` | `conversation_id` (UUID) | Stream completed successfully |
| `error` | Error description | Stream failed |

**Response Headers**

| Header | Value |
|---|---|
| `X-Conversation-ID` | Active conversation UUID |
| `X-Trace-ID` | Request trace ID |
| `Cache-Control` | `no-cache` |
| `Connection` | `keep-alive` |

**JavaScript streaming example:**

```javascript
const response = await fetch('/api/v1/chat/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ user_id: 'user-123', message: 'Tell me about Python.' })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  process.stdout.write(decoder.decode(value));
}
```

---

### `GET /api/v1/conversations/`

List all conversations for a user. Rate limit: **30 requests/min per IP**.

**Query Parameters**

| Parameter | Type | Required |
|---|---|---|
| `user_id` | `string` | ✅ |

**Response — 200 OK**

```json
[
  {
    "conversation_id": "3f7a2d91-14bc-4e88-bf32-2c3a9c8f1234",
    "summary": "User is a Python developer named Oshan based in Colombo.",
    "created_at": "2026-04-27T10:00:00Z",
    "last_activity_at": "2026-04-27T11:30:00Z",
    "last_message": "What are the best Python libraries for ML?"
  }
]
```

---

### End-to-End Multi-Turn Example

```bash
# 1. Start a conversation — facts are extracted and stored
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123", "message": "My name is Oshan, I live in Colombo."}'
# → { "reply": "...", "conversation_id": "abc-111" }

# 2. Continue — bot uses stored memory
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123", "message": "What is my name?", "conversation_id": "abc-111"}'
# → { "reply": "Your name is Oshan.", ... }

# 3. Trigger conflict resolution
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123", "message": "Actually I moved to London.", "conversation_id": "abc-111"}'
# → { "reply": "Should I update your location from Colombo to London?", ... }

# 4. Confirm the update
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123", "message": "yes", "conversation_id": "abc-111"}'
# → { "reply": "Got it — I updated that memory.", ... }

# 5. List all conversations
curl "http://localhost:8000/api/v1/conversations/?user_id=user-123"
```

---

## 🗄️ Database Schema

```sql
-- Users anchor all data in the system
CREATE TABLE users (
    id          VARCHAR PRIMARY KEY,   -- Client-provided user ID
    created_at  TIMESTAMP
);

-- Each user can have multiple conversations
CREATE TABLE conversations (
    id          VARCHAR PRIMARY KEY,
    user_id     VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    summary     TEXT DEFAULT '',       -- LLM-generated summary (updated on compression)
    created_at  TIMESTAMP
);

-- Individual messages within a conversation
CREATE TABLE chat_messages (
    id              VARCHAR PRIMARY KEY,
    conversation_id VARCHAR NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            VARCHAR NOT NULL,   -- 'user' | 'assistant'
    content         TEXT NOT NULL,
    created_at      TIMESTAMP
);

-- User-scoped long-term memory with confidence tracking
CREATE TABLE long_term_memories (
    id              VARCHAR PRIMARY KEY,
    user_id         VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key             VARCHAR NOT NULL,   -- e.g. 'name', 'goal', 'dynamic_hobby'
    value           TEXT NOT NULL,
    confidence      VARCHAR NOT NULL DEFAULT 'medium',   -- low | medium | high
    evidence_count  INTEGER NOT NULL DEFAULT 1,
    source          VARCHAR NOT NULL DEFAULT 'llm_extraction',
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP
);

-- Staged memory conflicts awaiting user confirmation
CREATE TABLE pending_memory_conflicts (
    id              VARCHAR PRIMARY KEY,
    user_id         VARCHAR NOT NULL REFERENCES users(id),
    conversation_id VARCHAR NOT NULL REFERENCES conversations(id),
    key             VARCHAR NOT NULL,
    old_value       TEXT NOT NULL,
    new_value       TEXT NOT NULL,
    status          VARCHAR NOT NULL DEFAULT 'pending',  -- pending | confirmed | rejected
    created_at      TIMESTAMP,
    resolved_at     TIMESTAMP
);

-- LLM operation quality evaluation results
CREATE TABLE llm_eval_results (
    id              VARCHAR PRIMARY KEY,
    trace_id        VARCHAR NOT NULL,
    user_id         VARCHAR,
    conversation_id VARCHAR,
    operation       VARCHAR NOT NULL,  -- generate_reply | extract_user_facts | detect_memory_confirmation
    passed          BOOLEAN NOT NULL,
    issues          TEXT,              -- JSON array of failure reason strings
    metadata_json   TEXT,              -- JSON object: reply_length, extracted_keys, etc.
    created_at      TIMESTAMP
);
```

---

## 📜 Migration History

| # | Revision ID | Description |
|---|---|---|
| 1 | `8060177cece5` | Initial schema: conversations, chat_messages, long_term_memories |
| 2 | `715e8c48dd03` | Add users table; move memories to user scope |
| 3 | `e0d35b850cc6` | Add `confidence` and `source` columns to long_term_memories |
| 4 | `d10d921df661` | Add `evidence_count` to long_term_memories |
| 5 | `325ff7eac7a2` | Add pending_memory_conflicts table |
| 6 | `897b21f163a7` | Add unique constraints on memories and conflicts |
| 7 | `2ab3d33df443` | Add database indexes for query performance |
| 8 | `c06b3e991f00` | Add llm_eval_results table |

```bash
alembic upgrade head      # Apply all migrations
alembic downgrade -1      # Roll back one step
alembic current           # Show current revision
alembic history           # Show full migration log
```

---

## ⚙️ Configuration Tuning

### Memory Behavior

| Setting | Default | Effect |
|---|---|---|
| `MAX_HISTORY_MESSAGES` | `10` | Higher = more context = more tokens per request |
| `SUMMARY_TRIGGER_MESSAGES` | `12` | Lower = more frequent summarization |
| `RECENT_MESSAGES_AFTER_SUMMARY` | `6` | Higher = more history retained after compression |
| `PENDING_CONFLICT_TTL_HOURS` | `24` | How long unresolved conflicts stay pending |

**Recommended profiles:**

| Use Case | `MAX_HISTORY` | `TRIGGER` | `KEEP_AFTER` |
|---|---|---|---|
| Lightweight Q&A | 5 | 8 | 3 |
| Standard assistant (default) | 10 | 12 | 6 |
| Long technical sessions | 15 | 20 | 8 |

### Rate Limits

Global default is set in `app/core/rate_limiter.py`:

```python
limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])
```

Per-endpoint overrides in `app/api/v1/chat.py`:

```python
@limiter.limit("10/minute")   # stricter for chat endpoints
```

### Structured Memory Keys

Add custom first-class keys in `app/core/memory_config.py`:

```python
STRUCTURED_MEMORY_KEYS = {
    "name", "location", "favorite_language", "goal", "profession",
    "age", "industry",   # add your own here
}
DYNAMIC_PREFIX = "dynamic_"
```

---

## 🗺️ Roadmap

- [ ] 🔐 JWT authentication with user registration and login
- [ ] 🌐 WebSocket support as alternative to SSE streaming
- [ ] 📊 Admin dashboard for memory inspection and eval analytics
- [ ] 🧪 Pytest test suite — unit + integration
- [ ] 🔁 Exponential backoff for OpenAI API retries
- [ ] 🌍 Multi-model support (Anthropic Claude, Gemini, Ollama)
- [ ] 📁 File and image upload support for multimodal conversations
- [ ] 🗑️ Memory management endpoints (user-controlled fact deletion)
- [ ] ☁️ Cloud deployment guides (Railway, Render, AWS ECS, GCP Cloud Run)
- [ ] 📈 Prometheus metrics endpoint for eval result aggregation

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

<div align="center">

Made with ❤️ by <a href="https://github.com/OshanYelena">Oshan Yelena</a>

</div>