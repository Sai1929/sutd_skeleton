# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EHS (Environment, Health & Safety) Inspection Portal for SUTD. **Stateless FastAPI backend only** — no auth, no database required for active endpoints. React UI to be built separately.

## Commands

### Backend (run from `ehs_backend/`)

```bash
# Install
pip install -e ".[all]"

# Dev server
uvicorn app.main:app --reload --port 8000

# Train DistilBERT model (use GPU — see ehs_distilbert_training.ipynb)
python scripts/train_distilbert.py \
  --data_path data/sample.csv \
  --output_dir models/ehs_distilbert \
  --strategy per_step \
  --device cuda

# Test trained model
python scripts/test_model.py --model_dir models/ehs_distilbert

# Lint & type check
ruff check .
ruff format .
mypy app/
```

### Training Notebook

`ehs_distilbert_training.ipynb` — self-contained Jupyter notebook for RunPod GPU training.
Upload notebook + `ehs_backend/data/sample.csv`, run all cells, download `ehs_distilbert_model.zip`,
extract to `ehs_backend/models/ehs_distilbert/`.

## Architecture

### Stateless Backend — 3 Active Endpoints

```
POST /api/v1/inspect/recommend   — DistilBERT inspection recommendations (no DB)
POST /api/v1/quiz/generate       — Groq/Llama quiz generation (no DB)
POST /api/v1/chat/query          — Groq/Llama WSH risk assessment chatbot (no DB)
```

No authentication. No database required. All endpoints are fully stateless.

### Recommendation Engine (`app/api/v1/inspect.py`)

Stateless HTTP — single endpoint. Client sends `{activity, selections}`, server returns
`predictions` only for fields **below** the last confirmed selection.

- Step order: `activity → hazard_type → severity_likelihood → moc_ppe → remarks`
- Model: `EHSMultiStepPredictor` (per-step) or `EHSPredictor` (shared) — auto-detected at startup
- If no selection is confirmed, all 4 fields are predicted
- If user overrides step N, only steps N+1 onward are re-predicted

### Quiz Generation (`app/api/v1/quiz.py`)

- `POST /quiz/generate` — takes inspection data, returns 5 MCQ questions via Groq
- Questions probe admin understanding: hazard comprehension, risk reasoning, control effectiveness,
  alternative scenarios, regulatory awareness (Singapore WSH)

### Chatbot (`app/api/v1/chat.py`)

- `POST /chat/query` — client sends full `history` array + `message` on every request
- Server holds no conversation state — frontend owns history
- System prompt: Singapore WSH risk assessment advisor

### Parked (code preserved, not in router)

- `app/api/v1/sessions.py` — inspection session management (requires DB)
- `app/api/v1/submissions.py` — submission storage (requires DB)
- `app/api/v1/chatbot.py` — hybrid RAG chatbot (pgvector + BM25 + BGE reranker + GPT-4o mini)
- `app/services/rag/` — full RAG pipeline

### ML Model

- Architecture: 4 separate `DistilBertForSequenceClassification` models (one per step)
- Trained with `--strategy per_step` (best accuracy ~82-87%)
- Saved to `models/ehs_distilbert/step_{hazard_type,severity_likelihood,moc_ppe,remarks}/`
- Input: activity + prior selections joined with ` [SEP] `
- Output: ranked list of labels with probability scores

## Key Configuration (`ehs_backend/.env`)

```env
DEBUG=true
GROQ_API_KEY=gsk_...
GROQ_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
DISTILBERT_MODEL_PATH=./models/ehs_distilbert
DISTILBERT_DEVICE=cpu
```

No database, no Azure OpenAI needed for active endpoints.

## File Structure

```
ehs_backend/
  app/
    api/v1/
      inspect.py      — /inspect/recommend (active)
      quiz.py         — /quiz/generate (active)
      chat.py         — /chat/query (active)
      sessions.py     — parked
      submissions.py  — parked
      chatbot.py      — parked (RAG)
    ml/
      distilbert/     — model, predictor, tokenizer
      training/       — dataset builder, trainer
    services/
      chat/           — GroqChatClient, WSH system prompt
      quiz/           — QuizGenerator (Groq)
      rag/            — parked RAG pipeline
  models/
    ehs_distilbert/   — trained model weights
  data/
    sample.csv        — 1,142 row training dataset
  scripts/
    train_distilbert.py
    test_model.py
ehs_distilbert_training.ipynb  — RunPod GPU training notebook
```

## Python

Python 3.11+. Ruff line length: 100.
