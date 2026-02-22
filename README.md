# Execution-Aware Code Intelligence System

A full-stack system for repository indexing, execution-graph retrieval, and LLM-powered code explanation.

It combines:
- static code structure extraction (symbols, calls, imports, variables)
- graph-backed relationship lookup
- semantic retrieval with FAISS embeddings
- optional external knowledge enrichment
- explanation generation through an OpenAI-compatible API

## Why this project

Understanding large codebases is hard when context is split across tools.

This project gives you one workflow:
1. create a repo session
2. index repository code
3. retrieve graph + semantic context
4. generate execution-aware explanations
5. explore function graphs visually

## Tech stack

- **Backend:** FastAPI, Pydantic, Tree-sitter, FAISS, SentenceTransformers, SQLite
- **Frontend:** React + Vite
- **Model API:** OpenAI-compatible chat completions endpoint
- **Deployment:** Render blueprint via `render.yaml`

## Repository structure

```text
backend/
  api/
  config/
  embeddings/
  graph/
  llm/
  parser/
  repository/
  retriever/
  services/
  vector/
  main.py
frontend/
  src/
  package.json
data/
  cache/
  faiss/
  graph_storage/
  repos/
  sqlite/
rag_kb_dataset.csv
render.yaml
```

## Quick start (local)

### 1) Backend setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file at the repository root (same level as `backend/` and `frontend/`) and set at least:

```env
MEGALLM_API_KEY=your_key
LLM_BASE_URL=https://ai.megallm.io/v1
LLM_MODEL=claude-sonnet-4-5-20250929|
LLM_API_KEY_ENV_VAR=MEGALLM_API_KEY
```

Run API:

```bash
uvicorn backend.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

### 2) Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Optional API URL override:

```bash
set VITE_API_BASE_URL=http://localhost:8000
```

## Core API flow

The API is **session-based**.

1. Create (or switch) session for a repo path/URL.
2. Index repository into graph + vector storage.
3. Explain function/snippet and fetch graph.

### Example flow

```bash
# 1) Create session from local path
curl -X POST http://localhost:8000/session/create \
  -H "Content-Type: application/json" \
  -d "{\"repo_path\":\"D:/Execution Aware Code Intelligence System\"}"

# 2) Index repository
curl -X POST http://localhost:8000/index_repo \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"<SESSION_ID>\",\"reindex\":false}"

# 3) Explain a function
curl -X POST http://localhost:8000/explain_function \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"<SESSION_ID>\",\"function_name\":\"index_repository\"}"
```

## API endpoints

### General
- `GET /health`

### Session management
- `POST /session/create`
- `POST /session/switch`
- `POST /session/close`
- `POST /session/reset`
- `GET /session/active`
- `GET /session/structure?session_id=<id>`

### Indexing and retrieval
- `POST /index_repo`
- `POST /seed_external_kb`
- `POST /explain_function`
- `POST /explain_snippet`
- `GET /graph/{function_name}?session_id=<id>`
- `GET /graph/stats?session_id=<id>[&function_name=<name>]`

## Key environment variables

- `EMBEDDING_MODEL` (default: `sentence-transformers/all-MiniLM-L6-v2`)
- `FAISS_INDEX_PATH`, `FAISS_METADATA_PATH`, `FAISS_SEARCH_LIMIT`, `FAISS_SEARCH_METRIC`
- `SQLITE_PATH`
- `INDEXING_BATCH_SIZE`, `INDEXING_CHUNK_SIZE`, `INDEXING_CHUNK_OVERLAP`
- `INDEXING_MAX_FILE_BYTES`, `INDEXING_INCLUDE_EXTENSIONS`, `INDEXING_MAX_WORKERS`
- `GRAPH_TRAVERSAL_DEPTH`, `GRAPH_PAGE_SIZE`
- `GITHUB_CLONE_DIR`, `GITHUB_CLONE_TIMEOUT_SECONDS`
- `RUNTIME_REQUEST_TIMEOUT_SECONDS`, `RUNTIME_RETRY_ATTEMPTS`
- `EXTERNAL_KNOWLEDGE_ENABLED`, `EXTERNAL_KNOWLEDGE_CSV_PATH`
- `EXTERNAL_KNOWLEDGE_DOCS_URLS`, `EXTERNAL_KNOWLEDGE_STACKOVERFLOW_TAGS`, `EXTERNAL_KNOWLEDGE_GITHUB_ISSUE_REPOS`

## External knowledge (optional)

To enrich retrieval using CSV/docs/other external sources:

1. Set `EXTERNAL_KNOWLEDGE_ENABLED=true`
2. Set `EXTERNAL_KNOWLEDGE_CSV_PATH=./rag_kb_dataset.csv`
3. Call `POST /seed_external_kb` with `session_id`

## Deploy on Render

This repo includes `render.yaml` with:
- `execution-aware-backend` (FastAPI web service)
- `execution-aware-frontend` (Vite static site)

### Deploy steps

1. Push repository to GitHub.
2. In Render, create a new **Blueprint** deployment.
3. Select the repository and deploy.
4. Set `MEGALLM_API_KEY` in backend environment variables.

If backend URL differs from the default, update frontend `VITE_API_BASE_URL` and redeploy.

## Notes

- Default indexing target extensions: `.py`
- CORS is currently open (`allow_origins=["*"]`) for development convenience
- Existing `data/` directories are used for persisted graph/vector/session artifacts
