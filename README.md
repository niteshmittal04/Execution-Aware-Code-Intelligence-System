# Execution Aware RAG Code Explainer

Local full-stack application that indexes repositories, builds execution-aware graphs, stores embeddings, and generates explanations using local Ollama models.

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
└── config.yaml
```

## Backend Setup

1. Create a Python 3.11+ environment.
2. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3. Run backend:

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

- Ollama server with configured `llm_model` and `embedding_model`
- Milvus instance reachable from backend

## API Endpoints

- `POST /index_repo`
- `POST /explain_function`
- `POST /explain_snippet`
- `GET /graph/{function_name}`
