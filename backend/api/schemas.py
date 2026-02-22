from pydantic import BaseModel, Field


class IndexRepoRequest(BaseModel):
    session_id: str
    repo_url: str | None = None
    branch: str | None = None
    reindex: bool = False


class ExplainSnippetRequest(BaseModel):
    session_id: str
    code: str
    language: str = "python"


class ExplainFunctionRequest(BaseModel):
    session_id: str
    function_name: str
    source_type: str | None = None
    domain: str | None = None
    difficulty_level: str | None = None
    library: str | None = None


class ExplanationResponse(BaseModel):
    summary: str
    execution_flow: str
    dependencies: str
    variables: str
    improvements: str
    confidence_score: float


class GraphNode(BaseModel):
    id: str
    type: str
    file: str


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class SessionCreateRequest(BaseModel):
    repo_url: str | None = None
    repo_path: str | None = None
    branch: str | None = None


class SessionSwitchRequest(BaseModel):
    repo_url: str | None = None
    repo_path: str | None = None
    branch: str | None = None


class SessionActionRequest(BaseModel):
    session_id: str


class SeedExternalKnowledgeRequest(BaseModel):
    session_id: str
