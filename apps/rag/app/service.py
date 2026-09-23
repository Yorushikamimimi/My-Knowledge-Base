import base64
import time
from pathlib import Path

from langfuse import get_client, propagate_attributes

from app.chunking import chunk_text
from app.config import Settings
from app.parsers import DocumentParseError, parse_document
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
        if not chunks:
            message = "No indexable text was extracted from the document."
            content_type = (request.contentType or "").lower()
            is_text_content = content_type.startswith("text/") or "markdown" in content_type
            if (
                Path(request.documentName).suffix.lower() == ".pdf"
                and not is_text_content
            ):
                message += " Scanned PDFs may require OCR."
            raise DocumentParseError(message)
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
        langfuse = get_client()

        with langfuse.start_as_current_observation(
            as_type="span", name="rag-query", input=request.query
        ) as root:
            with propagate_attributes(
                trace_name="rag-query",
                metadata={
                    "knowledge_base_id": request.knowledgeBaseId,
                    "top_k": request.topK,
                    "min_score": self.settings.min_score,
                },
            ):
                with langfuse.start_as_current_observation(
                    as_type="embedding",
                    name="query-embedding",
                    input=request.query,
                    model=self.settings.embedding_model,
                ) as embedding_obs:
                    query_embedding = self.provider.embed(request.query)
                    embedding_obs.update(output={"dimension": len(query_embedding)})

                with langfuse.start_as_current_observation(
                    as_type="retriever",
                    name="vector-retrieval",
                    input={"query": request.query, "top_k": request.topK},
                ) as retrieval_obs:
                    retrieved = self.repository.search(
                        request.knowledgeBaseId, query_embedding, request.topK
                    )
                    hits = [chunk for chunk in retrieved if chunk.score >= self.settings.min_score]
                    retrieval_obs.update(
                        output=[
                            {
                                "document_id": chunk.document_id,
                                "document_name": chunk.document_name,
                                "chunk_index": chunk.chunk_index,
                                "score": round(chunk.score, 4),
                            }
                            for chunk in hits
                        ],
                        metadata={
                            "raw_retrieved_count": len(retrieved),
                            "filtered_hit_count": len(hits),
                            "min_score": self.settings.min_score,
                        },
                    )

                latency_ms = int((time.monotonic() - started) * 1000)
                if not hits:
                    root.update(output={"refused": True, "hit_count": 0})
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

                with langfuse.start_as_current_observation(
                    as_type="generation",
                    name="ollama-generation",
                    input=prompt,
                    model=self.settings.chat_model,
                ) as generation_obs:
                    result = self.provider.generate(prompt)
                    # Langfuse flat usage buckets: "input" / "output" (total auto-derived).
                    usage_details: dict[str, int] = {}
                    if result.prompt_eval_count is not None:
                        usage_details["input"] = result.prompt_eval_count
                    if result.eval_count is not None:
                        usage_details["output"] = result.eval_count
                    generation_obs.update(
                        output=result.answer,
                        usage_details=usage_details or None,
                        metadata={
                            "eval_duration_ns": result.eval_duration_ns,
                            "total_duration_ns": result.total_duration_ns,
                        },
                    )

                latency_ms = int((time.monotonic() - started) * 1000)
                root.update(output={"answer": result.answer, "hit_count": len(hits)})
                return QueryResponse(
                    answer=result.answer,
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
