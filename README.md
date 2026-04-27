<div align="center">

<h1>🤖 Simple AI Chatbot Backend</h1>

<p>
  <strong>A production-ready, memory-aware AI chatbot API built with FastAPI, OpenAI GPT, and PostgreSQL</strong>
</p>

<p>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12"/>
  <img src="https://img.shields.io/badge/FastAPI-0.136-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/OpenAI-GPT-412991?style=for-the-badge&logo=openai&logoColor=white" alt="OpenAI"/>
  <img src="https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy"/>
  <img src="https://img.shields.io/badge/Alembic-Migrations-13A8E5?style=for-the-badge" alt="Alembic"/>
</p>

<p>
  <img src="https://img.shields.io/badge/version-0.1.0-blue?style=flat-square" alt="Version"/>
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"/>
  <img src="https://img.shields.io/badge/environment-development-yellow?style=flat-square" alt="Environment"/>
</p>

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Memory System](#-memory-system)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Development Setup](#local-development-setup)
  - [Docker Setup](#docker-setup)
- [Environment Variables](#-environment-variables)
- [API Reference](#-api-reference)
- [Database Schema](#-database-schema)
- [Configuration](#-configuration)
- [Development](#-development)
- [Roadmap](#-roadmap)

---

## 🌟 Overview

**Simple AI Chatbot Backend** is a production-style REST API that powers a persistent, memory-aware conversational AI assistant. Built on **FastAPI** and **OpenAI's GPT models**, it goes beyond a stateless chatbot by implementing a three-layer memory architecture — short-term message history, summarized long-term context, and extracted user facts — all persisted in **PostgreSQL**.

The system is designed to maintain natural, context-aware conversations across sessions without ballooning token usage, using intelligent conversation compression triggered automatically after a configurable message threshold.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🧠 **Three-Layer Memory** | Short-term history + conversation summaries + persistent user facts |
| 🔄 **Auto-Summarization** | Compresses old messages into summaries when a threshold is reached |
| 👤 **User Fact Extraction** | Automatically extracts stable user facts (name, preferences, goals) from messages using LLM |
| 🗃️ **Persistent Storage** | All conversations, messages, and memories stored in PostgreSQL via SQLAlchemy ORM |
| 🐳 **Docker Ready** | Fully containerized with `docker-compose` including PostgreSQL with health checks |
| 📦 **Schema Migrations** | Alembic-managed database migrations for safe schema evolution |
| 📝 **Structured Logging** | Per-module logging with configurable setup |
| ❤️ **Health Check** | `/health` endpoint verifying API and database connectivity |
| 🔒 **Input Validation** | Pydantic v2 request/response schemas with field constraints |
| ⚙️ **Config via Env** | All settings driven by environment variables using `pydantic-settings` |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (HTTP)                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │  POST /api/v1/chat/
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Application                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  API Layer  (v1/chat.py)                 │   │
│  │  • Validates request via Pydantic schemas                │   │
│  │  • Orchestrates memory + LLM service calls               │   │
│  │  • Returns ChatResponse with reply + conversation_id     │   │
│  └──────────┬───────────────────────┬───────────────────────┘  │
│             │                       │                           │
│  ┌──────────▼──────────┐  ┌─────────▼──────────────────────┐  │
│  │   Memory Service    │  │        LLM Service              │  │
│  │                     │  │                                 │  │
│  │ • get/create conv.  │  │ • generate_reply()              │  │
│  │ • add_message()     │  │ • summarize_messages()          │  │
│  │ • build_context()   │  │ • extract_user_facts()          │  │
│  │ • should_summarize()│  │                                 │  │
│  │ • compress_conv()   │  │  OpenAI GPT API (gpt-4o-mini)  │  │
│  └──────────┬──────────┘  └─────────────────────────────────┘  │
│             │                                                   │
│  ┌──────────▼──────────────────────────────────────────────┐   │
│  │            Long-Term Memory Service                      │   │
│  │  • update_memory()   • get_memory()                      │   │
│  │  • format_memory_for_prompt()                            │   │
│  └──────────┬──────────────────────────────────────────────┘   │
│             │                                                   │
│  ┌──────────▼──────────────────────────────────────────────┐   │
│  │            Conversation Repository                       │   │
│  │  SQLAlchemy ORM — single source of truth for DB access   │   │
│  └──────────┬──────────────────────────────────────────────┘   │
└─────────────┼───────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PostgreSQL Database                         │
│                                                                 │
│   conversations  │  chat_messages  │  long_term_memories        │
│   ─────────────  │  ─────────────  │  ──────────────────        │
│   id (UUID)      │  id (UUID)      │  id (UUID)                 │
│   summary        │  conversation_id│  conversation_id           │
│   created_at     │  role           │  key                       │
│                  │  content        │  value                     │
│                  │  created_at     │  created_at / updated_at   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Memory System

The chatbot uses a **three-layer memory architecture** to maintain meaningful, efficient conversations:

```
Each Chat Request
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  Layer 1: Long-Term Memory (Persistent User Facts)    │
│                                                      │
│  • LLM extracts facts from every user message        │
│  • Stored as key-value pairs in long_term_memories   │
│  • e.g.  name: "Oshan", goal: "learn Python"         │
│  • Injected as system context on every request       │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  Layer 2: Conversation Summary (Mid-Term Context)    │
│                                                      │
│  • Triggered when message count ≥ 12 (configurable) │
│  • LLM summarizes full history → stored in DB        │
│  • Old messages pruned; last 6 kept (configurable)   │
│  • Summary injected as system message in context     │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  Layer 3: Recent Message History (Short-Term)        │
│                                                      │
│  • Last N messages (default: 10) sent to LLM        │
│  • Full role/content preserved for immediate context │
└──────────────────────────────────────────────────────┘
```

This design keeps token usage bounded while preserving conversational continuity across long sessions.

---

## 📁 Project Structure

```
.
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── chat.py              # Chat endpoint — request orchestration
│   ├── core/
│   │   ├── config.py                # Settings via pydantic-settings + .env
│   │   └── logger.py                # Structured per-module logger setup
│   ├── db/
│   │   ├── database.py              # SQLAlchemy engine + session factory
│   │   ├── health.py                # DB connection health check
│   │   └── models.py                # ORM models: Conversation, ChatMessage, LongTermMemory
│   ├── repositories/
│   │   └── conversation_repository.py  # All DB operations (single access point)
│   ├── schemas/
│   │   └── chat.py                  # Pydantic request/response schemas
│   ├── services/
│   │   ├── llm_service.py           # OpenAI integration: reply, summarize, extract facts
│   │   ├── memory_service.py        # Short-term + summary memory orchestration
│   │   └── long_term_memory.py      # Persistent user fact management
│   └── main.py                      # FastAPI app factory + router registration
├── alembic/
│   ├── env.py                       # Alembic migration environment
│   ├── script.py.mako               # Migration template
│   └── versions/
│       └── 8060177cece5_create_chatbot_memory_tables.py
├── Dockerfile                       # Python 3.12-slim container
├── docker-compose.yml               # API + PostgreSQL services
├── alembic.ini                      # Alembic configuration
├── requirements.txt                 # Pinned Python dependencies
└── run.py                           # Local dev entry point (uvicorn with reload)
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
| **Containerization** | Docker + Compose | — |

---

## 🚀 Getting Started

### Prerequisites

- **Python** 3.12+
- **PostgreSQL** 16 (or Docker)
- **OpenAI API Key** — [Get one here](https://platform.openai.com/api-keys)
- **Docker & Docker Compose** (optional, for containerized setup)

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
```

Edit `.env` with your values (see [Environment Variables](#-environment-variables)).

**5. Run database migrations**

```bash
alembic upgrade head
```

**6. Start the development server**

```bash
python run.py
```

The API will be available at **http://127.0.0.1:8000**

Interactive API docs: **http://127.0.0.1:8000/docs**

---

### Docker Setup

**1. Create the Docker environment file**

```bash
cp .env.example .env.docker
```

Edit `.env.docker` — set `DATABASE_URL` to use the Docker Compose service name:

```env
DATABASE_URL=postgresql://chatbot_user:chatbot_password@db:5432/simple_chatbot
```

**2. Build and start all services**

```bash
docker compose up --build
```

This will:
- Start a **PostgreSQL 16** container with a health check
- Build and start the **API container**
- Automatically run `alembic upgrade head` before the server starts
- Expose the API on **port 8000**

**3. Verify the services are running**

```bash
docker compose ps
curl http://localhost:8000/health
```

**Stop the services**

```bash
docker compose down           # Keep database volume
docker compose down -v        # Also remove database volume
```

---

## 🔧 Environment Variables

Create a `.env` file in the project root:

```env
# ─── Application ───────────────────────────────────────────────
APP_NAME=Simple AI Chatbot
APP_VERSION=0.1.0
ENVIRONMENT=development          # development | production

# ─── OpenAI ────────────────────────────────────────────────────
OPENAI_API_KEY=sk-...            # Required
OPENAI_MODEL=gpt-4o-mini         # Model to use

# ─── Database ──────────────────────────────────────────────────
DATABASE_URL=postgresql://chatbot_user:chatbot_password@localhost:5432/simple_chatbot

# ─── Memory Configuration ──────────────────────────────────────
MAX_HISTORY_MESSAGES=10          # Recent messages sent to LLM
SUMMARY_TRIGGER_MESSAGES=12      # Message count before summarization triggers
RECENT_MESSAGES_AFTER_SUMMARY=6  # Messages to retain after compression
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | ✅ Yes | — | Your OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-40-mini` | GPT model identifier |
| `DATABASE_URL` | ✅ Yes | — | PostgreSQL connection string |
| `MAX_HISTORY_MESSAGES` | No | `10` | Max recent messages in context |
| `SUMMARY_TRIGGER_MESSAGES` | No | `12` | Messages before auto-summarization |
| `RECENT_MESSAGES_AFTER_SUMMARY` | No | `6` | Messages kept after compression |
| `ENVIRONMENT` | No | `development` | Runtime environment label |

---

## 📡 API Reference

### Base URL

```
http://localhost:8000
```

---

### `GET /`

Health check — returns app name and environment.

**Response**

```json
{
  "message": "Simple AI Chatbot API is running",
  "environment": "development"
}
```

---

### `GET /health`

Deep health check — verifies API is running **and** the database is reachable.

**Response — 200 OK**

```json
{
  "status": "healthy",
  "database": "connected"
}
```

**Response — 500 Internal Server Error** (if DB is unreachable)

```json
{
  "detail": "Database connection failed"
}
```

---

### `POST /api/v1/chat/`

Send a message to the chatbot. Optionally pass a `conversation_id` to continue an existing session.

**Request Body**

```json
{
  "message": "Hi! My name is Oshan and I love Python.",
  "conversation_id": "optional-uuid-string"
}
```

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `message` | `string` | ✅ Yes | 1–1000 chars | The user's message |
| `conversation_id` | `string` | No | UUID | Resume an existing conversation |

**Response — 200 OK**

```json
{
  "reply": "Nice to meet you, Oshan! Python is a fantastic language...",
  "conversation_id": "3f7a2d91-14bc-4e88-bf32-2c3a9c8f1234"
}
```

> 💡 Save the returned `conversation_id` and pass it in subsequent requests to maintain conversation context.

**Response — 500 Internal Server Error**

```json
{
  "detail": "Chat service failed. Please try again."
}
```

---

### Example: Multi-turn conversation

```bash
# First message — no conversation_id needed
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "My name is Oshan and I am a Python developer."}'

# Response includes a conversation_id
# {
#   "reply": "Nice to meet you, Oshan! ...",
#   "conversation_id": "abc-123"
# }

# Continue the conversation
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my name?", "conversation_id": "abc-123"}'

# The bot remembers: "Your name is Oshan."
```

---

## 🗄️ Database Schema

```sql
-- Stores each conversation session
CREATE TABLE conversations (
    id          VARCHAR PRIMARY KEY,   -- UUID
    summary     TEXT DEFAULT '',       -- LLM-generated summary (updated on compression)
    created_at  TIMESTAMP
);

-- Stores individual messages within a conversation
CREATE TABLE chat_messages (
    id              VARCHAR PRIMARY KEY,
    conversation_id VARCHAR REFERENCES conversations(id) ON DELETE CASCADE,
    role            VARCHAR NOT NULL,   -- 'user' | 'assistant'
    content         TEXT NOT NULL,
    created_at      TIMESTAMP
);

-- Stores extracted long-term user facts (key-value)
CREATE TABLE long_term_memories (
    id              VARCHAR PRIMARY KEY,
    conversation_id VARCHAR REFERENCES conversations(id) ON DELETE CASCADE,
    key             VARCHAR NOT NULL,   -- e.g. 'name', 'goal', 'preference'
    value           TEXT NOT NULL,
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP
);
```

---

## ⚙️ Configuration

### Tuning the Memory System

Adjust these settings in your `.env` file to tune memory behavior:

```
MAX_HISTORY_MESSAGES=10
```
Controls how many recent messages are included in the LLM context window. Higher = more context, more tokens.

```
SUMMARY_TRIGGER_MESSAGES=12
```
When a conversation exceeds this many messages, summarization is triggered automatically.

```
RECENT_MESSAGES_AFTER_SUMMARY=6
```
After compression, this many recent messages are kept alongside the new summary.

**Recommended tuning by use case:**

| Use Case | `MAX_HISTORY` | `TRIGGER` | `KEEP_AFTER` |
|---|---|---|---|
| Brief Q&A chatbot | 5 | 8 | 3 |
| Standard assistant (default) | 10 | 12 | 6 |
| Deep technical sessions | 15 | 20 | 8 |

---

## 👨‍💻 Development

### Running Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "describe your change"

# Downgrade one step
alembic downgrade -1
```

### Accessing Interactive API Docs

FastAPI automatically generates documentation:

| Interface | URL |
|---|---|
| **Swagger UI** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |
| **OpenAPI JSON** | http://localhost:8000/openapi.json |

### Viewing Logs

```bash
# Docker
docker compose logs -f api

# Local
python run.py   # logs print to stdout
```

---

## 🗺️ Roadmap

- [ ] 🔐 Authentication (JWT / API key per user)
- [ ] 👥 Multi-user support with user-scoped conversations
- [ ] 🌐 WebSocket support for streaming responses
- [ ] 📊 Admin dashboard for conversation analytics
- [ ] 🧪 Unit and integration test suite (pytest)
- [ ] 🔁 Retry logic and circuit breaker for OpenAI API calls
- [ ] 🌍 Multi-model support (Anthropic Claude, Gemini, etc.)
- [ ] 📁 File / image upload support
- [ ] ☁️ Cloud deployment guide (Railway, Render, AWS ECS)

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

<div align="center">

Made with ❤️ by <a href="https://github.com/OshanYelena">Oshan Yelena</a>

</div>