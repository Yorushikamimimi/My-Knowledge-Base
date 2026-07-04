from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException

from app.config import Settings, get_settings
from app.parsers import DocumentParseError, UnsupportedDocumentType
from app.providers import ModelProviderError, create_provider
from app.repository import RagRepository
from app.schemas import IngestRequest, IngestResponse, QueryRequest, QueryResponse
from app.service import RagService

app = FastAPI(title="My Knowledge Base RAG Service")


@lru_cache
def _settings() -> Settings:
    return get_settings()


def get_rag_service() -> RagService:
    settings = _settings()
    return RagService(settings, create_provider(settings), RagRepository(settings))


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/api/v1/rag/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest, service: RagService = Depends(get_rag_service)):
    try:
        return service.ingest(request)
    except UnsupportedDocumentType as exc:
        raise HTTPException(status_code=400, detail={"code": "UNSUPPORTED_DOCUMENT", "message": str(exc)})
    except DocumentParseError as exc:
        raise HTTPException(status_code=422, detail={"code": "DOCUMENT_PARSE_FAILED", "message": str(exc)})
    except ModelProviderError as exc:
        raise HTTPException(status_code=503, detail={"code": "MODEL_PROVIDER_UNAVAILABLE", "message": str(exc)})


@app.post("/api/v1/rag/query", response_model=QueryResponse)
def query(request: QueryRequest, service: RagService = Depends(get_rag_service)):
    try:
        return service.query(request)
    except ModelProviderError as exc:
        raise HTTPException(status_code=503, detail={"code": "MODEL_PROVIDER_UNAVAILABLE", "message": str(exc)})
