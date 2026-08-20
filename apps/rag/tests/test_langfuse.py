from app.config import Settings
from app.providers import GenerationResult
from app.repository import RetrievedChunk
from app.schemas import QueryRequest
from app.service import RagService


class FakeProvider:
    def __init__(self, embedding, gen_result):
        self.embedding = embedding
        self.gen_result = gen_result
        self.generated = False

    @property
    def name(self) -> str:
        return "fake"

    def embed(self, text: str) -> list[float]:
        return self.embedding

    def generate(self, prompt: str) -> GenerationResult:
        self.generated = True
        return self.gen_result


class FakeRepository:
    def __init__(self, chunks):
        self.chunks = chunks

    def search(self, knowledge_base_id: str, embedding: list[float], top_k: int):
        return self.chunks


def _chunk(score: float) -> RetrievedChunk:
    return RetrievedChunk(
        document_id="doc-1",
        document_name="spring-tx-test.md",
        chunk_index=0,
        content="Spring @Transactional 通常通过 AOP proxy 实现。",
        score=score,
    )


def test_query_with_tracing_disabled_matches_baseline(monkeypatch):
    # Tracing must be a no-op: business response identical to the untraced baseline.
    monkeypatch.setenv("LANGFUSE_TRACING_ENABLED", "false")
    provider = FakeProvider(
        [0.1, 0.2],
        GenerationResult(
            answer="AOP proxy 原因", model="qwen2.5:7b", prompt_eval_count=30, eval_count=12
        ),
    )
    repository = FakeRepository([_chunk(0.8), _chunk(0.2)])
    service = RagService(Settings(), provider, repository)

    response = service.query(
        QueryRequest(
            knowledgeBaseId="kb-1",
            query="@Transactional 为什么同一个类内部调用时可能不生效？",
            topK=5,
        )
    )

    assert response.refused is False
    assert response.hitCount == 1  # only the chunk above min_score=0.35
    assert response.answer == "AOP proxy 原因"
    assert response.sources[0].documentName == "spring-tx-test.md"
    assert response.sources[0].score == 0.8
    assert provider.generated is True


def test_query_refused_skips_generation(monkeypatch):
    # When every hit is below min_score, generation must not be invoked.
    monkeypatch.setenv("LANGFUSE_TRACING_ENABLED", "false")
    provider = FakeProvider([0.1, 0.2], GenerationResult(answer="x", model="qwen2.5:7b"))
    repository = FakeRepository([_chunk(0.2)])
    service = RagService(Settings(), provider, repository)

    response = service.query(
        QueryRequest(knowledgeBaseId="kb-1", query="Kafka ISR 的工作机制是什么？", topK=5)
    )

    assert response.refused is True
    assert response.hitCount == 0
    assert response.sources == []
    assert provider.generated is False


class FakeObservation:
    def __init__(self, client, **kwargs):
        self.kwargs = kwargs
        self.updates = []
        self.client = client
        self.parent_name = client._current_name if client._stack else None

    def __enter__(self):
        self.client._stack.append(self)
        self.client._current_name = self.kwargs["name"]
        return self

    def __exit__(self, *exc):
        self.client._stack.pop()
        self.client._current_name = self.client._stack[-1].kwargs["name"] if self.client._stack else None
        return False

    def update(self, **kwargs):
        self.updates.append(kwargs)


class FakeLangfuseClient:
    def __init__(self):
        self.observations = []
        self._stack = []
        self._current_name = None

    def start_as_current_observation(self, **kwargs):
        observation = FakeObservation(self, **kwargs)
        self.observations.append(observation)
        return observation


def _noop_propagate_attributes(**kwargs):
    class _Ctx:
        def __enter__(self):
            return None

        def __exit__(self, *exc):
            return False

    return _Ctx()


def test_generation_usage_maps_to_langfuse_flat_buckets(monkeypatch):
    monkeypatch.setenv("LANGFUSE_TRACING_ENABLED", "true")
    client = FakeLangfuseClient()
    monkeypatch.setattr("app.service.get_client", lambda: client)
    monkeypatch.setattr("app.service.propagate_attributes", _noop_propagate_attributes)

    provider = FakeProvider(
        [0.1, 0.2],
        GenerationResult(
            answer="ok", model="qwen2.5:7b", prompt_eval_count=35, eval_count=12
        ),
    )
    repository = FakeRepository([_chunk(0.8)])
    service = RagService(Settings(), provider, repository)

    service.query(QueryRequest(knowledgeBaseId="kb-1", query="q", topK=5))

    generation = next(o for o in client.observations if o.kwargs.get("name") == "ollama-generation")
    assert generation.updates[0]["usage_details"] == {"input": 35, "output": 12}


def test_query_trace_observation_tree_structure(monkeypatch):
    # A successful RAG trace must contain exactly one rag-query root with
    # query-embedding / vector-retrieval / ollama-generation as its children.
    monkeypatch.setenv("LANGFUSE_TRACING_ENABLED", "true")
    client = FakeLangfuseClient()
    monkeypatch.setattr("app.service.get_client", lambda: client)
    monkeypatch.setattr("app.service.propagate_attributes", _noop_propagate_attributes)

    provider = FakeProvider([0.1, 0.2], GenerationResult(answer="ok", model="qwen2.5:7b"))
    repository = FakeRepository([_chunk(0.8)])
    service = RagService(Settings(), provider, repository)

    service.query(QueryRequest(knowledgeBaseId="kb-1", query="q", topK=5))

    by_name = {o.kwargs["name"]: o for o in client.observations}
    assert set(by_name) == {"rag-query", "query-embedding", "vector-retrieval", "ollama-generation"}
    assert by_name["rag-query"].parent_name is None
    for child in ("query-embedding", "vector-retrieval", "ollama-generation"):
        assert by_name[child].parent_name == "rag-query"
    assert by_name["query-embedding"].kwargs["as_type"] == "embedding"
    assert by_name["vector-retrieval"].kwargs["as_type"] == "retriever"
    assert by_name["ollama-generation"].kwargs["as_type"] == "generation"
