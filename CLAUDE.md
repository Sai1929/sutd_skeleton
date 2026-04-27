# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EHS (Environment, Health & Safety) Inspection Portal for SUTD. Stateless FastAPI backend + React/Vite/TypeScript frontend. No auth, no database required for active endpoints.

## Commands

### Backend (run from `ehs_backend/`)

```bash
# Install
pip install -e ".[all]"

# Dev server (port 8000)
uvicorn app.main:app --reload --port 8000

# Tests
pytest                          # all tests
pytest tests/unit               # unit only
pytest tests/integration        # integration only
pytest -k "test_name"           # single test

# Lint & type check
ruff check .
ruff format .
mypy app/

# Train DistilBERT (GPU — see ehs_distilbert_training.ipynb)
python scripts/train_distilbert.py \
  --data_path data/sample.csv \
  --output_dir models/ehs_distilbert \
  --strategy per_step \
  --device cuda

# Test trained model
python scripts/test_model.py --model_dir models/ehs_distilbert
```

### Frontend (run from `ehs_frontend/`)

```bash
npm install
npm run dev      # Vite dev server on http://localhost:3000
npm run build    # tsc && vite build
npm run preview  # preview production build
```

> **Port note:** Frontend axios client (`src/api/client.ts`) points to `http://localhost:8001`. Backend runs on `8000` by default — align these when running locally.

### Training Notebook

`ehs_distilbert_training.ipynb` — self-contained Jupyter notebook for RunPod GPU training.
Upload notebook + `ehs_backend/data/sample.csv`, run all cells, download `ehs_distilbert_model.zip`,
extract to `ehs_backend/models/ehs_distilbert/`.

## Architecture

### Stateless Backend — 3 Active Endpoints

```
POST /api/v1/inspect/recommend   — DistilBERT inspection recommendations
POST /api/v1/quiz/generate       — Groq/Llama quiz generation
POST /api/v1/chat/query          — Groq/Llama WSH risk assessment chatbot
GET  /health/live                — liveness
GET  /health/ready               — readiness
```

No authentication. No database. All state lives in the HTTP request body.

### Recommendation Engine (`app/api/v1/inspect.py`)

Client sends `{activity, selections}`, server returns `predictions` only for fields **below** the last confirmed selection.

- Step order: `activity → hazard_type → severity_likelihood → moc_ppe → remarks`
- Model: `EHSMultiStepPredictor` (per-step) or `EHSPredictor` (shared) — auto-detected at startup
- If no selection confirmed, all 4 fields are predicted
- If user overrides step N, only steps N+1 onward are re-predicted
- Fallback: frequency-based engine in `app/services/recommendation/` when model unavailable

### Quiz Generation (`app/api/v1/quiz.py`)

Takes completed inspection data, returns 5 MCQ questions via Groq probing hazard comprehension,
risk reasoning, control effectiveness, alternative scenarios, Singapore WSH regulatory awareness.

### Chatbot (`app/api/v1/chat.py`)

Client sends full `history` array + `message` on every request. Server holds no conversation
state — frontend owns history.

System prompt (`app/services/chat/prompt.py`) is a full risk-assessment engine:
- Generates structured RA tables with ≥12 rows, 5×5 risk matrix (L×S), and residual risk
- Activity-specific row checklists: Radiation/NDT, Lifting, WAH, Confined Space, Electrical, Hot Work, Excavation, Chemical, Demolition, Machinery, Manual Handling, Generic
- Cites inline Singapore WSH/SS references per control measure
- Hard rules: residual L ≥ 2 always; ≥12 rows always; mandatory output sections (Assumptions, RA table, Risk Matrix, Chemical Note, References)

**Do not simplify or summarize the system prompt** — its specificity is intentional and compliance-critical.

### Frontend Architecture (`ehs_frontend/src/`)

Two-page React app with tab navigation (`NavBar`):

- **InspectionPage** — inspection workflow; prediction cards in a 2×2 grid layout
- **ChatPage** — WSH chatbot with sidebar conversation list

State managed via custom hooks (no Redux):
- `useInspection` — `useReducer` for predictions, selections, step progression; debounces activity input (500ms) before triggering `/inspect/recommend`
- `useChat` — chat message history, send/receive cycle
- `useQuiz` — quiz overlay state, triggered from inspection completion

API layer (`src/api/`) uses axios. Each module exports one function: `recommend()`, `sendChat()`, `generateQuiz()`.

### ML Model

- 4 separate `DistilBertForSequenceClassification` models (one per step)
- Trained with `--strategy per_step` (accuracy ~82–87%)
- Saved to `models/ehs_distilbert/step_{hazard_type,severity_likelihood,moc_ppe,remarks}/`
- Input: activity + prior selections joined with ` [SEP] `
- Output: ranked list of labels with probability scores

### Parked (code preserved, not in router)

- `app/api/v1/sessions.py` — inspection session management (requires DB)
- `app/api/v1/submissions.py` — submission storage (requires DB)
- `app/api/v1/chatbot.py` — hybrid RAG chatbot (pgvector + BM25 + BGE reranker + GPT-4o mini)
- `app/services/rag/` — full RAG pipeline
- `app/db/` — SQLAlchemy models + alembic migrations

## Key Configuration (`ehs_backend/.env`)

```env
DEBUG=true
GROQ_API_KEY=gsk_...
GROQ_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
DISTILBERT_MODEL_PATH=./models/ehs_distilbert
DISTILBERT_DEVICE=cpu
```

No database, no Azure OpenAI needed for active endpoints.

## Python

Python 3.11+. Ruff line length: 100. Ruff rules: `E, F, I, UP`. mypy: non-strict, `ignore_missing_imports = true`. pytest: `asyncio_mode = "auto"`.
