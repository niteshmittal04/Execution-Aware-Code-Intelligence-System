from pydantic import BaseModel, Field


class IndexRepoRequest(BaseModel):
    repo_url: str
    branch: str | None = None


class ExplainSnippetRequest(BaseModel):
    code: str
    language: str = "python"


class ExplainFunctionRequest(BaseModel):
    function_name: str


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
