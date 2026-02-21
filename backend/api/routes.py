from fastapi import APIRouter, HTTPException

from backend.api.schemas import (
    ExplainFunctionRequest,
    ExplainSnippetRequest,
    GraphEdge,
    GraphNode,
    GraphResponse,
    IndexRepoRequest,
)
from backend.services.service_factory import get_services

router = APIRouter()


@router.post("/index_repo")
def index_repo(payload: IndexRepoRequest) -> dict:
    services = get_services()
    try:
        return services["indexing_service"].index_repository(payload.repo_url, payload.branch)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/seed_external_kb")
def seed_external_kb() -> dict:
    services = get_services()
    try:
        return services["indexing_service"].seed_external_knowledge_if_empty()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/explain_function")
def explain_function(payload: ExplainFunctionRequest) -> dict:
    services = get_services()
    function_name = payload.function_name
    context = services["retriever"].retrieve(
        function_name,
        {
            "source_type": payload.source_type,
            "domain": payload.domain,
            "difficulty_level": payload.difficulty_level,
            "library": payload.library,
        },
    )
    return services["llm_engine"].explain(function_name, context)


@router.post("/explain_snippet")
def explain_snippet(payload: ExplainSnippetRequest) -> dict:
    services = get_services()
    return services["llm_engine"].explain_snippet(payload.code, payload.language)


@router.get("/graph/{function_name}", response_model=GraphResponse)
def get_graph(function_name: str) -> GraphResponse:
    services = get_services()
    nodes, edges = services["graph_store"].get_function_graph(function_name)

    graph_nodes = [
        GraphNode(id=item["id"], type=item["type"], file=item["file_path"])
        for item in nodes
    ]
    graph_edges = [
        GraphEdge(source=item["source"], target=item["target"], type=item["type"])
        for item in edges
    ]

    return GraphResponse(nodes=graph_nodes, edges=graph_edges)
