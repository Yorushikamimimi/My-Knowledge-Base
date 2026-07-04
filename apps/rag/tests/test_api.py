from fastapi.testclient import TestClient

from app.main import app, get_rag_service
from app.schemas import (
    IngestResponse,
    QueryResponse,
    RagSource,
)


class StubRagService:
    def __init__(self):
        self.ingest_requests = []
        self.query_requests = []

    def ingest(self, request):
        self.ingest_requests.append(request)
        return IngestResponse(documentId=request.documentId, chunkCount=2, provider="stub")

    def query(self, request):
        self.query_requests.append(request)
        return QueryResponse(
            answer="基于资料：项目使用 pgvector 做向量检索。",
            sources=[
                RagSource(
                    documentId="doc-1",
                    documentName="notes.md",
                    chunkIndex=0,
                    score=0.82,
                    preview="项目使用 pgvector 做向量检索。",
                )
            ],
            hitCount=1,
            latencyMs=12,
            refused=False,
        )


def test_healthz_returns_ok():
    client = TestClient(app)

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ingest_endpoint_delegates_to_service():
    service = StubRagService()
    app.dependency_overrides[get_rag_service] = lambda: service
    client = TestClient(app)

    response = client.post(
        "/api/v1/rag/ingest",
        json={
            "knowledgeBaseId": "kb-1",
            "documentId": "doc-1",
            "documentName": "notes.md",
            "contentType": "text/markdown",
            "contentBase64": "IyBUaXRsZQoKUmFnIGNvbnRlbnQ=",
        },
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {"documentId": "doc-1", "chunkCount": 2, "provider": "stub"}
    assert service.ingest_requests[0].documentName == "notes.md"


def test_query_endpoint_returns_answer_sources_and_metrics():
    service = StubRagService()
    app.dependency_overrides[get_rag_service] = lambda: service
    client = TestClient(app)

    response = client.post(
        "/api/v1/rag/query",
        json={"knowledgeBaseId": "kb-1", "query": "项目怎么检索？", "topK": 3},
    )

    app.dependency_overrides.clear()
    body = response.json()
    assert response.status_code == 200
    assert body["answer"].startswith("基于资料")
    assert body["hitCount"] == 1
    assert body["latencyMs"] == 12
    assert body["sources"][0]["documentName"] == "notes.md"
