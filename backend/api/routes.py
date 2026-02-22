from fastapi import APIRouter, HTTPException
from pathlib import Path

from backend.api.schemas import (
    ExplainFunctionRequest,
    ExplainSnippetRequest,
    GraphEdge,
    GraphNode,
    GraphResponse,
    IndexRepoRequest,
    SeedExternalKnowledgeRequest,
    SessionActionRequest,
    SessionCreateRequest,
    SessionSwitchRequest,
)
from backend.services.service_factory import get_services

router = APIRouter()


@router.post("/index_repo")
def index_repo(payload: IndexRepoRequest) -> dict:
    services = get_services()
    try:
        session = services["session_manager"].get_session(payload.session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found.")

        result = services["indexing_service"].index_repository(
            session_id=payload.session_id,
            repo_url=payload.repo_url,
            branch=payload.branch,
            reindex=payload.reindex,
        )
        if result.get("status") == "indexed" or payload.reindex:
            services["structure_service"].extract_repo_structure(
                Path(session.repo_path),
                payload.session_id,
                force_refresh=True,
            )
        return result
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/seed_external_kb")
def seed_external_kb(payload: SeedExternalKnowledgeRequest) -> dict:
    services = get_services()
    try:
        return services["indexing_service"].seed_external_knowledge_if_empty(payload.session_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/explain_function")
def explain_function(payload: ExplainFunctionRequest) -> dict:
    services = get_services()
    session = services["session_manager"].get_session(payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    function_name = payload.function_name
    context = services["retriever"].retrieve(
        payload.session_id,
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
    session = services["session_manager"].get_session(payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    return services["llm_engine"].explain_snippet(payload.code, payload.language)


@router.get("/graph/stats")
def get_graph_stats(session_id: str, function_name: str | None = None) -> dict:
    services = get_services()
    session = services["session_manager"].get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    totals = services["graph_store"].get_graph_stats(session_id)
    response = {
        "session_id": session_id,
        "repo_path": session.repo_path,
        "totals": totals,
    }

    if function_name and function_name.strip():
        response["query"] = services["graph_store"].get_graph_stats_for_query(
            session_id,
            function_name,
        )

    return response


@router.get("/graph/{function_name}", response_model=GraphResponse)
def get_graph(function_name: str, session_id: str) -> GraphResponse:
    services = get_services()
    session = services["session_manager"].get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    nodes, edges = services["graph_store"].get_function_graph(session_id, function_name)

    graph_nodes = [
        GraphNode(id=item["id"], type=item["type"], file=item["file_path"])
        for item in nodes
    ]
    graph_edges = [
        GraphEdge(source=item["source"], target=item["target"], type=item["type"])
        for item in edges
    ]

    return GraphResponse(nodes=graph_nodes, edges=graph_edges)


@router.post("/session/create")
def create_session(payload: SessionCreateRequest) -> dict:
    services = get_services()
    try:
        if payload.repo_path:
            repo_path = Path(payload.repo_path).expanduser().resolve()
            if not repo_path.exists() or not repo_path.is_dir():
                raise HTTPException(status_code=400, detail="repo_path must point to an existing directory.")
        elif payload.repo_url:
            repo_path = services["indexing_service"].cloner.clone(payload.repo_url, payload.branch)
        else:
            raise HTTPException(status_code=400, detail="Provide repo_path or repo_url.")

        session = services["session_manager"].create_session(repo_path)
        return {"session": session.to_dict()}
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/session/switch")
def switch_session(payload: SessionSwitchRequest) -> dict:
    services = get_services()
    try:
        if payload.repo_path:
            repo_path = Path(payload.repo_path).expanduser().resolve()
            if not repo_path.exists() or not repo_path.is_dir():
                raise HTTPException(status_code=400, detail="repo_path must point to an existing directory.")
        elif payload.repo_url:
            repo_path = services["indexing_service"].cloner.clone(payload.repo_url, payload.branch)
        else:
            raise HTTPException(status_code=400, detail="Provide repo_path or repo_url.")

        session = services["session_manager"].switch_session(repo_path)
        return {"session": session.to_dict()}
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/session/close")
def close_session(payload: SessionActionRequest) -> dict:
    services = get_services()
    session = services["session_manager"].get_session(payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    services["session_manager"].close_session(payload.session_id)
    return {"status": "closed", "session_id": payload.session_id}


@router.post("/session/reset")
def reset_session(payload: SessionActionRequest) -> dict:
    services = get_services()
    session = services["session_manager"].get_session(payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    services["graph_store"].reset_session(payload.session_id)
    services["vector_store"].reset_session(payload.session_id)
    refreshed = services["session_manager"].reset_session(payload.session_id)
    return {"status": "reset", "session": refreshed.to_dict() if refreshed else None}


@router.get("/session/active")
def get_active_session() -> dict:
    services = get_services()
    active = services["session_manager"].get_active_session()
    return {"session": active.to_dict() if active else None}


@router.get("/session/structure")
def get_session_structure(session_id: str) -> dict:
    services = get_services()
    session = services["session_manager"].get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    structure = services["structure_service"].extract_repo_structure(
        Path(session.repo_path),
        session_id,
        force_refresh=False,
    )
    return {"session_id": session_id, "repo_path": session.repo_path, "structure": structure}
