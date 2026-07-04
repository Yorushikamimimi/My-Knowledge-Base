import base64
import time

from app.chunking import chunk_text
from app.config import Settings
from app.parsers import parse_document
from app.providers import ModelProvider
from app.repository import RagRepository
from app.schemas import IngestRequest, IngestResponse, QueryRequest, QueryResponse, RagSource


class RagService:
    def __init__(self, settings: Settings, provider: ModelProvider, repository: RagRepository):
        self.settings = settings
        self.provider = provider
        self.repository = repository

    def ingest(self, request: IngestRequest) -> IngestResponse:
        raw = base64.b64decode(request.contentBase64)
        parsed = parse_document(request.documentName, request.contentType, raw)
        chunks = chunk_text(parsed.text, self.settings.chunk_size, self.settings.chunk_overlap)
        embedded_chunks = [
            (chunk.index, chunk.text, self.provider.embed(chunk.text)) for chunk in chunks
        ]
        self.repository.replace_document_chunks(
            request.knowledgeBaseId,
            request.documentId,
            request.documentName,
            embedded_chunks,
        )
        return IngestResponse(
            documentId=request.documentId, chunkCount=len(embedded_chunks), provider=self.provider.name
        )

    def query(self, request: QueryRequest) -> QueryResponse:
        started = time.monotonic()
        query_embedding = self.provider.embed(request.query)
        retrieved = self.repository.search(request.knowledgeBaseId, query_embedding, request.topK)
        hits = [chunk for chunk in retrieved if chunk.score >= self.settings.min_score]
        latency_ms = int((time.monotonic() - started) * 1000)
        if not hits:
            return QueryResponse(
                answer="没有在当前知识库中找到足够相关的资料，因此不生成猜测性回答。",
                sources=[],
                hitCount=0,
                latencyMs=latency_ms,
                refused=True,
            )

        context = "\n\n".join(
            f"[{index + 1}] {chunk.document_name} chunk {chunk.chunk_index}: {chunk.content}"
            for index, chunk in enumerate(hits)
        )
        prompt = (
            "你是企业知识库问答助手。只能根据资料回答；如果资料不足，必须说明无法从资料中确认。\n\n"
            f"资料：\n{context}\n\n问题：{request.query}\n\n回答："
        )
        answer = self.provider.generate(prompt)
        latency_ms = int((time.monotonic() - started) * 1000)
        return QueryResponse(
            answer=answer,
            sources=[
                RagSource(
                    documentId=chunk.document_id,
                    documentName=chunk.document_name,
                    chunkIndex=chunk.chunk_index,
                    score=round(chunk.score, 4),
                    preview=chunk.content[:240],
                )
                for chunk in hits
            ],
            hitCount=len(hits),
            latencyMs=latency_ms,
            refused=False,
        )
