from fastapi.testclient import TestClient

from app.main import app, get_rag_service
from app.parsers import DocumentParseError
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


class RejectingRagService(StubRagService):
    def ingest(self, request):
        raise DocumentParseError(
            "No indexable text was extracted from the document. Scanned PDFs may require OCR."
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


def test_ingest_endpoint_returns_unprocessable_when_document_has_no_indexable_text(monkeypatch):
    monkeypatch.setitem(
        app.dependency_overrides, get_rag_service, lambda: RejectingRagService()
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/rag/ingest",
        json={
            "knowledgeBaseId": "kb-test",
            "documentId": "doc-test",
            "documentName": "scan.pdf",
            "contentType": "application/pdf",
            "contentBase64": "",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "DOCUMENT_PARSE_FAILED"
    assert "No indexable text" in response.json()["detail"]["message"]
    assert "Scanned PDFs may require OCR" in response.json()["detail"]["message"]


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
