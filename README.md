# Execution Aware RAG Code Explainer

A local full-stack system that indexes source code, builds a lightweight execution graph, retrieves relevant semantic context, and generates function/snippet explanations using an MegLLM's LLM API.

## Problem This Application Solves

Understanding an unfamiliar codebase is slow because code intelligence is often split across multiple disconnected views:

- Source search gives text matches but not execution relationships.
- Graph views show relationships but often miss semantic context.
- LLM summaries can be generic when they do not have repository-aware grounding.

This project combines those pieces into one workflow:

1. Parse repository code into symbols/calls/imports/variables.
2. Store relationships in a graph store.
3. Embed code and optional external knowledge into a vector store.
4. Retrieve graph + semantic context together.
5. Produce execution-aware explanations and graph visualizations in the UI.

## What It Does

- Indexes a Git repository URL (or local checked-out code after clone).
- Builds and stores function/class nodes and call/import edges.
- Tracks variable assignments by scope.
- Creates semantic embeddings for code chunks.
- Optionally enriches retrieval with external CSV knowledge.
- Serves explanation and graph endpoints for a React frontend.

## Architecture

### Backend (FastAPI + Python)

- **API Layer (`backend/api`)**
	- Exposes endpoints for indexing, explanation, and graph retrieval.
- **Service Assembly (`backend/services/service_factory.py`)**
	- Initializes and wires parser, graph store, embedder, retriever, vector store, and LLM engine.
- **Indexing Pipeline (`backend/services/indexing_service.py`)**
	- Clones repo → parses files → persists graph/variables → embeds code/external chunks → persists vectors.
- **Parser (`backend/parser/tree_sitter_parser.py`)**
	- Uses Tree-sitter Python grammar to extract symbols, call edges, import edges, and variable assignments.
- **Graph Store (`backend/graph/sqlite_graph.py`)**
	- Uses SQLite for nodes, edges, and variables, with configurable traversal depth for graph queries.
- **Embedding (`backend/embeddings/minilm_embedder.py`)**
	- Uses SentenceTransformers (`all-MiniLM-L6-v2` by default) with retry logic.
- **Vector Store (`backend/vector/faiss_store.py`)**
	- Uses FAISS (cosine via normalized inner product), stores metadata JSON sidecar, supports filtering + reranking.
- **Retriever (`backend/retriever/hybrid_retriever.py`)**
	- Combines graph neighborhood + semantic similarity hits + scoped variables.
- **LLM Engine (`backend/llm/explanation_engine.py`)**
	- Calls OpenAI-compatible chat completions API and returns structured explanation fields.

### Frontend (React + Vite)

- **Repository Input page**: submit repo URL/branch for indexing.
- **Function Explorer page**: load graph summary for target function.
- **Explanation Viewer page**: explain function or raw snippet.
- **Graph Viewer page**: render graph with React Flow.
- **Client API module (`frontend/src/api.js`)**: centralized REST calls and graph cache.

### Storage and Data Assets

- **SQLite**: execution graph (`nodes`, `edges`, `variables`).
- **FAISS + metadata JSON**: semantic vectors and retrievable chunk metadata.
- **Cloned repos**: local working copies under `data/repos/`.
- **Optional external KB**: `rag_kb_dataset.csv` ingested as additional retrievable knowledge.

## End-to-End Tech Stack Flow

### A) Repository Indexing Flow

1. Frontend calls `POST /index_repo` with repository URL.
2. Backend clones repository into configured clone directory.
3. Tree-sitter parser scans allowed file extensions (default `.py`) and extracts:
	 - symbols (functions/classes/modules)
	 - call relationships
	 - import relationships
	 - variable assignments with scope
4. Parser creates text chunks from file content (size/overlap configurable).
5. Graph store upserts nodes/edges/variables into SQLite.
6. Embedder generates embeddings for chunks.
7. FAISS store inserts vectors and persists both index + metadata.
8. If external knowledge is enabled, CSV/docs chunks are also embedded and inserted.

### B) Function Explanation Flow

1. Frontend calls `POST /explain_function` with `function_name`.
2. Hybrid retriever runs:
	 - graph traversal for related nodes/edges
	 - vector similarity search for semantic hits
	 - variable lookup for matching scope
3. Combined context is passed to LLM engine prompt builder.
4. LLM engine calls configured OpenAI-compatible endpoint.
5. API returns structured explanation payload:
	 - summary
	 - execution_flow
	 - dependencies
	 - variables
	 - improvements
	 - confidence_score

### C) Snippet Explanation Flow

1. Frontend calls `POST /explain_snippet` with code + language.
2. Backend sends truncated snippet context to LLM endpoint.
3. API returns the same structured explanation format.

### D) Graph Visualization Flow

1. Frontend calls `GET /graph/{function_name}`.
2. Backend retrieves function-centric graph from SQLite.
3. Frontend transforms graph response into React Flow elements.
4. User explores execution relationships visually.

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
│   ├── vector/
│   ├── services/
│   ├── config/
│   └── main.py
├── frontend/
│   ├── src/
│   └── package.json
├── data/
│   ├── faiss/
│   ├── sqlite/
│   └── repos/
├── rag_kb_dataset.csv
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

3. Configure environment:

```bash
copy .env.example .env
```

Then set at least:

- `MEGALLM_API_KEY` (or env var named by `LLM_API_KEY_ENV_VAR`)
- `LLM_BASE_URL`
- `LLM_MODEL`

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

Optional API base URL override:

```bash
set VITE_API_BASE_URL=http://localhost:8000
```

## Key Environment Variables

- `EMBEDDING_MODEL` (default `sentence-transformers/all-MiniLM-L6-v2`)
- `FAISS_INDEX_PATH`, `FAISS_METADATA_PATH`
- `SQLITE_PATH`
- `INDEXING_INCLUDE_EXTENSIONS` (default `.py`)
- `INDEXING_CHUNK_SIZE`, `INDEXING_CHUNK_OVERLAP`
- `GRAPH_TRAVERSAL_DEPTH`, `GRAPH_PAGE_SIZE`
- `EXTERNAL_KNOWLEDGE_ENABLED`
- `EXTERNAL_KNOWLEDGE_CSV_PATH`

## External Knowledge Dataset (CSV)

To enable CSV-backed retrieval enrichment:

1. Set `EXTERNAL_KNOWLEDGE_ENABLED=true`
2. Set `EXTERNAL_KNOWLEDGE_CSV_PATH=./rag_kb_dataset.csv`

CSV rows are ingested with metadata such as source type, domain, library, relevance label, votes/stars, and difficulty level. Retrieval supports optional metadata filtering (for example: `source_type`, `domain`, `difficulty_level`, `library`).

## API Endpoints

- `POST /index_repo`
- `POST /seed_external_kb` (seeds external KB only when vector DB is empty)
- `POST /explain_function`
- `POST /explain_snippet`
- `GET /graph/{function_name}`
- `GET /health`
