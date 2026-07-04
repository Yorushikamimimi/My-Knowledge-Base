from dataclasses import dataclass
import re


@dataclass(frozen=True)
class TextChunk:
    index: int
    text: str


def chunk_text(text: str, chunk_size: int = 450, overlap: int = 80) -> list[TextChunk]:
    normalized = re.sub(r"\s+", " ", text or "").strip()
    if not normalized:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    words = normalized.split()
    chunks: list[TextChunk] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(TextChunk(index=len(chunks), text=" ".join(words[start:end])))
        if end == len(words):
            break
        start = end - overlap
    return chunks
