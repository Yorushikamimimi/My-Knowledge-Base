from dataclasses import dataclass

import psycopg

from app.config import Settings


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: str
    document_name: str
    chunk_index: int
    content: str
    score: float


class RagRepository:
    def __init__(self, settings: Settings):
        self.settings = settings

    def replace_document_chunks(
        self,
        knowledge_base_id: str,
        document_id: str,
        document_name: str,
        chunks: list[tuple[int, str, list[float]]],
    ) -> None:
        with psycopg.connect(self.settings.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("delete from rag_document_chunks where document_id = %s", (document_id,))
                for chunk_index, content, embedding in chunks:
                    cur.execute(
                        """
                        insert into rag_document_chunks
                          (knowledge_base_id, document_id, document_name, chunk_index, content, embedding)
                        values (%s, %s, %s, %s, %s, %s::vector)
                        """,
                        (
                            knowledge_base_id,
                            document_id,
                            document_name,
                            chunk_index,
                            content,
                            _vector_literal(embedding),
                        ),
                    )

    def search(self, knowledge_base_id: str, embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        with psycopg.connect(self.settings.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select document_id, document_name, chunk_index, content,
                           1 - (embedding <=> %s::vector) as score
                    from rag_document_chunks
                    where knowledge_base_id = %s
                    order by embedding <=> %s::vector
                    limit %s
                    """,
                    (_vector_literal(embedding), knowledge_base_id, _vector_literal(embedding), top_k),
                )
                return [
                    RetrievedChunk(
                        document_id=str(row[0]),
                        document_name=str(row[1]),
                        chunk_index=int(row[2]),
                        content=str(row[3]),
                        score=float(row[4]),
                    )
                    for row in cur.fetchall()
                ]


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(float(value)) for value in values) + "]"
