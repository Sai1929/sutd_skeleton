# EHS Inspection Platform — Backend

FastAPI backend for an EHS (Environment, Health & Safety) inspection portal.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Streamlit UI  (consumes REST API)                              │
└────────────────────────┬────────────────────────────────────────┘
                         │  HTTP / JSON
┌────────────────────────▼────────────────────────────────────────┐
│                    FastAPI Backend                               │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │  Component 1     │  │  Component 2     │  │ Component 3  │  │
│  │  Recommendation  │  │  Quiz Generation │  │ RAG Chatbot  │  │
│  │  (Frequency      │  │  (Azure GPT-4o   │  │ (pgvector +  │  │
│  │   Ranker)        │  │   mini)          │  │  BM25 + BGE) │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────┬───────┘  │
└───────────┼─────────────────────┼────────────────────┼──────────┘
            │                     │                    │
┌───────────▼─────────────────────▼────────────────────▼──────────┐
│                     PostgreSQL + pgvector                        │
│  (users, sessions, recommendations, quizzes, document_chunks,   │
│   conversation_history)                                         │
└─────────────────────────────────────────────────────────────────┘
```

### Component 1 — Sequential Recommendation

```
Student selects Activity → POST /sessions/start
  → Creates InspectionSession in DB
  → Frequency ranker returns ranked options for Step 1 (Hazard Type)

Student picks option → POST /sessions/{id}/step
  → Saves selection → returns ranked options for Step 2 (Severity × Likelihood)

Repeat for Step 3 (MOC/PPE) and Step 4 (Remarks)
  → Step 4: is_final=True

POST /submissions
  → Saves InspectionSubmission
  → Background Task 1: Generate Quiz (GPT-4o mini)
  → Background Task 2: Ingest submission into RAG vector store
```

### Component 2 — Quiz Generation

```
InspectionSubmission → QuizGenerator prompt → Azure GPT-4o mini
  → 3 MCQ + 2 short-answer questions → saved to DB

Student submits answers → POST /quiz/{id}/attempt/{aid}/submit
  → MCQ: instant scoring
  → Short answer: GPT-4o mini grades with rubric (0.0–1.0 + feedback)

Quiz Q&A also ingested into RAG vector store
```

### Component 3 — Hybrid RAG Chatbot

```
Query
  ↓
IntentClassifier → "structured" | "vague" | "hybrid"
  ├─ structured → SelfQueryParser (GPT extracts activity/date/hazard filters)
  └─ vague      → HyDE (hypothetical doc → embed → use as query vector)
  ↓
Sequential Retrieval
  ├─ pgvector HNSW ANN (semantic, top_k=20)
  └─ PostgreSQL FTS BM25 (keyword, top_k=20)
  ↓
RRF Fusion (k=60) → top-20
  ↓
BGE Cross-Encoder Reranker → top-5
  ↓
Azure GPT-4o mini → Answer + Source Citations
Conversation history stored in PostgreSQL (JSONB)
```

---

## How to Run

### 1 — PostgreSQL + pgvector

```sql
-- In psql as superuser:
CREATE USER ehs_user WITH PASSWORD 'your_password';
CREATE DATABASE ehs_db OWNER ehs_user;
\c ehs_db
CREATE EXTENSION vector;
CREATE EXTENSION pg_trgm;
```

### 2 — Python Environment

```bash
cd d:\projects\SUTD\ehs_backend

python -m venv .venv
source .venv/Scripts/activate   # Git Bash
# or: .venv\Scripts\activate    # CMD

pip install -e ".[all]"
python -m spacy download en_core_web_sm
```

### 3 — Environment Configuration

```bash
copy .env.example .env
```

Fill in `.env`:
```env
SECRET_KEY=<random-64-char-string>
DATABASE_URL=postgresql+asyncpg://ehs_user:your_password@localhost:5432/ehs_db

AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_EMBED_DEPLOYMENT=text-embedding-3-small
```

### 4 — Database Setup

```bash
alembic upgrade head
python scripts/seed_db.py
```

### 5 — Start the Server

```bash
# Development
uvicorn app.main:app --reload --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

- **Swagger UI**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health/ready

### 6 — Start the Streamlit UI

```bash
cd d:\projects\SUTD
streamlit run ehs_frontend.py
```

Get a JWT token from Swagger (`POST /api/v1/auth/login`), then paste it in the Streamlit sidebar.

### 7 — Ingest Historical Data (optional)

After seeding, ingest existing submissions into the RAG vector store:

```bash
python scripts/ingest_historical_data.py
```
