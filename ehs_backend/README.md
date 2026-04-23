# EHS Inspection Platform — Backend

Stateless FastAPI backend for an EHS (Environment, Health & Safety) inspection portal at SUTD.
No auth, no database required for active endpoints. React UI to be built separately.

---

## Active API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/inspect/recommend` | DistilBERT inspection field predictions |
| `POST` | `/api/v1/quiz/generate` | Groq/Llama quiz generation from inspection data |
| `POST` | `/api/v1/chat/query` | Groq/Llama WSH risk assessment chatbot |
| `GET` | `/health/live` | Liveness check |
| `GET` | `/health/ready` | Readiness check |

---

## Architecture

```
React UI (to be built)
        │  HTTP / JSON
        ▼
   FastAPI Backend  (stateless — no DB, no auth)
   ┌────────────────────────────────────────────┐
   │                                            │
   │  /inspect/recommend                        │
   │    DistilBERT per-step predictor           │
   │    4 models: hazard → severity →           │
   │             moc_ppe → remarks              │
   │                                            │
   │  /quiz/generate                            │
   │    Groq/Llama → 5 MCQ questions            │
   │    (hazard comprehension, risk reasoning,  │
   │     control effectiveness, alternatives,  │
   │     WSH regulatory awareness)             │
   │                                            │
   │  /chat/query                               │
   │    Groq/Llama + WSH system prompt          │
   │    Client owns conversation history        │
   │                                            │
   └────────────────────────────────────────────┘
```

### Recommendation Flow

```
POST /api/v1/inspect/recommend
{
  "activity": "Electrical Works",
  "selections": {}                    ← empty = predict all 4 fields
}
→ predictions for: hazard_type, severity_likelihood, moc_ppe, remarks

POST /api/v1/inspect/recommend
{
  "activity": "Electrical Works",
  "selections": {"hazard_type": "Arc Flash"}   ← confirmed by user
}
→ predictions for: severity_likelihood, moc_ppe, remarks only
  (hazard_type already confirmed — not re-predicted)
```

Only fields **below** the last confirmed selection are re-predicted.

---

## Quick Start

### 1 — Install

```bash
cd ehs_backend
pip install -e ".[all]"
```

### 2 — Configure

```bash
cp .env.example .env
```

Edit `.env`:
```env
GROQ_API_KEY=gsk_your-key-here
DISTILBERT_MODEL_PATH=./models/ehs_distilbert
DISTILBERT_DEVICE=cpu    # or cuda
```

### 3 — Train the Model (first time)

Use the RunPod GPU notebook:
1. Upload `ehs_distilbert_training.ipynb` + `data/sample.csv` to RunPod
2. Run all cells (strategy: `per_step`, device: `cuda`)
3. Download `ehs_distilbert_model.zip`
4. Extract to `ehs_backend/models/ehs_distilbert/`

Or train locally on CPU (slow):
```bash
python scripts/train_distilbert.py \
  --data_path data/sample.csv \
  --output_dir models/ehs_distilbert \
  --strategy per_step \
  --device cpu
```

### 4 — Start the Server

```bash
uvicorn app.main:app --reload --port 8000
```

- **Swagger UI**: http://localhost:8000/docs (only when `DEBUG=true`)
- **Health check**: http://localhost:8000/health/live

---

## API Reference

### `POST /api/v1/inspect/recommend`

Predicts inspection fields using DistilBERT. Only fields downstream of confirmed selections are returned.

**Request:**
```json
{
  "activity": "Electrical Works",
  "selections": {
    "hazard_type": "Arc Flash"
  }
}
```

**Response:**
```json
{
  "activity": "Electrical Works",
  "selections": {"hazard_type": "Arc Flash"},
  "predictions": {
    "severity_likelihood": [
      {"label": "High x Likely", "score": 0.786, "rank": 1},
      ...
    ],
    "moc_ppe": [...],
    "remarks": [...]
  }
}
```

---

### `POST /api/v1/quiz/generate`

Generates 5 MCQ questions from a completed inspection to test the student's understanding.

**Request:**
```json
{
  "activity": "Electrical Works",
  "hazard_type": "Arc Flash",
  "severity_likelihood": "High x Likely",
  "moc_ppe": "Full Face Shield + FR Jacket",
  "remarks": "Obtain permit-to-work before proceeding"
}
```

**Response:**
```json
{
  "questions": [
    {
      "question_number": 1,
      "question_text": "What is the primary injury risk from arc flash?",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct_answer": "A",
      "explanation": "..."
    }
  ]
}
```

---

### `POST /api/v1/chat/query`

WSH risk assessment chatbot. Client sends full history on every request (stateless).

**Request:**
```json
{
  "message": "What PPE is needed for working at height?",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

**Response:**
```json
{
  "reply": "For working at height above 2 metres...",
  "model": "meta-llama/llama-4-scout-17b-16e-instruct"
}
```

---

## Model

- **Architecture:** 4 × `DistilBertForSequenceClassification` (one per inspection step)
- **Training strategy:** `per_step` — separate fine-tuned model per step (~82–87% accuracy)
- **Input format:** `"Electrical Works [SEP] Arc Flash [SEP] High x Likely"`
- **Labels:**
  - `hazard_type`: 10 classes (Arc Flash, Electric Shock, Fall from Height, ...)
  - `severity_likelihood`: 6 classes (High x Likely, Medium x Unlikely, ...)
  - `moc_ppe`: 8 classes (Safety Harness + Lanyard, Insulated Gloves + LOTO, ...)
  - `remarks`: 6 classes (Obtain permit-to-work, Conduct toolbox talk, ...)

---

## Parked (code preserved, not active)

- `app/api/v1/sessions.py` — inspection session management (requires PostgreSQL)
- `app/api/v1/submissions.py` — submission storage (requires PostgreSQL)
- `app/api/v1/chatbot.py` — hybrid RAG chatbot (pgvector + BM25 + BGE + GPT-4o mini)
- `app/services/rag/` — full RAG pipeline
