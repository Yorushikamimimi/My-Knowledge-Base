from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    knowledgeBaseId: str
    documentId: str
    documentName: str
    contentType: str | None = None
    contentBase64: str


class IngestResponse(BaseModel):
    documentId: str
    chunkCount: int
    provider: str


class QueryRequest(BaseModel):
    knowledgeBaseId: str
    query: str = Field(min_length=1)
    topK: int = Field(default=5, ge=1, le=20)


class RagSource(BaseModel):
    documentId: str
    documentName: str
    chunkIndex: int
    score: float
    preview: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[RagSource]
    hitCount: int
    latencyMs: int
    refused: bool = False
