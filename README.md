# Execution Aware RAG Code Explainer

Local full-stack application that indexes repositories, builds execution-aware graphs, stores embeddings, and generates explanations using an OpenAI-compatible LLM endpoint.

## Project Structure

```
project/
├── backend/
│   ├── api/
│   ├── parser/
│   ├── graph/
│   ├── embeddings/
│   ├── retriever/
│   ├── llm/
│   ├── config/
│   └── main.py
├── frontend/
│   ├── src/
│   └── package.json
├── data/
│   ├── milvus/
│   ├── sqlite/
│   └── repos/
├── .env
└── .env.example
```

## Backend Setup

1. Create a Python 3.11+ environment.
2. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3. Set LLM API key:

```bash
copy .env.example .env
# then edit .env and set MEGALLM_API_KEY
```

4. Run backend:

```bash
uvicorn backend.main:app --reload --port 8000
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Set API base URL if needed:

```bash
set VITE_API_BASE_URL=http://localhost:8000
```

## Required Services

- OpenAI-compatible LLM endpoint configured in `.env` (`LLM_BASE_URL`, `LLM_MODEL`)
- `MEGALLM_API_KEY` in `.env` (or key env var named by `LLM_API_KEY_ENV_VAR`)
- Ollama server with configured `embedding_model`
- Milvus instance reachable from backend

## API Endpoints

- `POST /index_repo`
- `POST /explain_function`
- `POST /explain_snippet`
- `GET /graph/{function_name}`
