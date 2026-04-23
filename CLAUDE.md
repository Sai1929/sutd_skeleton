# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EHS (Environment, Health & Safety) Inspection Portal for SUTD. Three-tier system: **Streamlit frontend** → **FastAPI backend** → **PostgreSQL + pgvector**.

## Commands

### Backend (run from `ehs_backend/`)

```bash
# Install
pip install -e ".[all]"
python -m spacy download en_core_web_sm

# Dev server
uvicorn app.main:app --reload --port 8000

# Database migrations
alembic upgrade head              # apply all migrations
alembic revision --autogenerate -m "description"  # create new migration

# Seed data
python scripts/seed_db.py
python scripts/ingest_historical_data.py  # ingest submissions into RAG vector store

# Tests
pytest                            # all tests
pytest tests/unit/                # unit tests only (SQLite in-memory, no Postgres needed)
pytest tests/integration/         # integration tests (requires running Postgres)
pytest tests/unit/test_foo.py::test_bar  # single test

# Lint & type check
ruff check .
ruff format .
mypy app/
```

### Frontend (run from project root)

```bash
streamlit run ehs_frontend.py     # full portal (needs backend running on :8000)
streamlit run chatbot1.py         # standalone risk assessment chatbot (Groq, no backend needed)
```

### Database setup (first time)

```bash
python db_setup.py                # creates ehs_user, ehs_db, extensions (edit passwords in file)
```

## Architecture

### Three Components in the Backend

The backend (`ehs_backend/app/`) has three independent service components that share the same PostgreSQL database:

1. **Recommendation Engine** (`services/recommendation/`) — Frequency-based sequential ranker. Students walk through a 4-step inspection: Activity → Hazard Type → Severity/Likelihood → MOC/PPE → Remarks. The engine ranks options at each step based on historical frequency. No ML model, purely DB-backed counts.

2. **Quiz Generation** (`services/quiz/`) — After submission, Azure GPT-4o mini generates 3 MCQ + 2 short-answer questions. Short answers are graded by GPT with a 0.0–1.0 rubric score. Quiz Q&A is also ingested into the RAG vector store.

3. **Hybrid RAG Chatbot** (`services/rag/`) — Intent classification → query routing:
   - `structured` queries → SelfQueryParser extracts filters (activity/date/hazard)
   - `vague` queries → HyDE generates hypothetical doc for embedding
   - Retrieval: pgvector HNSW (semantic) + PostgreSQL FTS BM25 (keyword) → RRF fusion → BGE cross-encoder reranker → GPT-4o mini answer generation

### Request Flow

- API routes: `app/api/v1/` — `auth.py`, `sessions.py`, `submissions.py`, `quiz.py`, `chatbot.py`
- All routes under `/api/v1/` prefix
- Auth: JWT tokens via `app/core/security.py`
- DB session injection via `app/dependencies.py`
- ML models loaded at startup in `app/main.py` lifespan handler and stored on `app.state`

### Frontend

- `ehs_frontend.py` — Full Streamlit portal with 4 tabs: Inspection, Submissions, Quiz, Risk Assessment Chatbot. Communicates with backend REST API. The chatbot tab uses Groq (Llama 4 Scout) directly, not the backend RAG pipeline.
- `chatbot1.py` — Standalone Streamlit chatbot for WSH risk assessments (Groq, no backend dependency).

### Other

- `SUTD_SUMANTH/recommendation/` — Separate standalone recommendation service with its own FastAPI app, alembic migrations, and scripts. Not integrated with the main backend.

## Key Configuration

- Backend config via `ehs_backend/.env` (copy from `.env.example`). Requires: `DATABASE_URL`, `SECRET_KEY`, Azure OpenAI credentials.
- Frontend chatbot requires `GROQ_API_KEY` in `.env` at project root.
- Python 3.11+. Ruff line length: 100. pytest asyncio_mode: auto.

## Database

PostgreSQL with extensions: `vector` (pgvector), `pg_trgm`, `uuid-ossp`. Async driver: `asyncpg`. ORM: SQLAlchemy 2.0 async. Migrations: Alembic.

Models defined in `app/db/base.py`. Schemas (Pydantic) in `app/schemas/`.
