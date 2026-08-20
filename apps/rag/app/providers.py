from dataclasses import dataclass
from typing import Protocol

import httpx

from app.config import Settings


@dataclass(frozen=True)
class GenerationResult:
    """Result of an LLM generation call, including optional token usage.

    Usage mirrors the fields returned by Ollama /api/generate so the RAG service
    can forward them to observability without changing model call behavior.
    """

    answer: str
    model: str
    prompt_eval_count: int | None = None
    eval_count: int | None = None
    total_duration_ns: int | None = None
    eval_duration_ns: int | None = None


class ModelProvider(Protocol):
    @property
    def name(self) -> str: ...

    def embed(self, text: str) -> list[float]: ...

    def generate(self, prompt: str) -> GenerationResult: ...


class ModelProviderError(Exception):
    pass


class OllamaProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def name(self) -> str:
        return "ollama"

    def embed(self, text: str) -> list[float]:
        try:
            response = httpx.post(
                f"{self.settings.ollama_base_url}/api/embeddings",
                json={"model": self.settings.embedding_model, "prompt": text},
                timeout=60,
                trust_env=False,
            )
            response.raise_for_status()
            embedding = response.json().get("embedding")
            if not isinstance(embedding, list) or not embedding:
                raise ModelProviderError("Ollama embedding response did not contain embedding")
            return [float(value) for value in embedding]
        except (httpx.HTTPError, ValueError) as exc:
            raise ModelProviderError("Embedding provider unavailable") from exc

    def generate(self, prompt: str) -> GenerationResult:
        try:
            response = httpx.post(
                f"{self.settings.ollama_base_url}/api/generate",
                json={"model": self.settings.chat_model, "prompt": prompt, "stream": False},
                timeout=120,
                trust_env=False,
            )
            response.raise_for_status()
            payload = response.json()
            answer = payload.get("response")
            if not isinstance(answer, str) or not answer.strip():
                raise ModelProviderError("Ollama generation response did not contain answer")
            return GenerationResult(
                answer=answer.strip(),
                model=self.settings.chat_model,
                prompt_eval_count=payload.get("prompt_eval_count"),
                eval_count=payload.get("eval_count"),
                total_duration_ns=payload.get("total_duration"),
                eval_duration_ns=payload.get("eval_duration"),
            )
        except (httpx.HTTPError, ValueError) as exc:
            raise ModelProviderError("Chat provider unavailable") from exc


class OpenAICompatibleProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def name(self) -> str:
        return "openai-compatible"

    def embed(self, text: str) -> list[float]:
        headers = {"Authorization": f"Bearer {self.settings.openai_api_key}"}
        try:
            response = httpx.post(
                f"{self.settings.openai_base_url}/embeddings",
                headers=headers,
                json={"model": self.settings.embedding_model, "input": text},
                timeout=60,
                trust_env=False,
            )
            response.raise_for_status()
            embedding = response.json()["data"][0]["embedding"]
            return [float(value) for value in embedding]
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise ModelProviderError("Embedding provider unavailable") from exc

    def generate(self, prompt: str) -> GenerationResult:
        headers = {"Authorization": f"Bearer {self.settings.openai_api_key}"}
        try:
            response = httpx.post(
                f"{self.settings.openai_base_url}/chat/completions",
                headers=headers,
                json={
                    "model": self.settings.chat_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
                timeout=120,
                trust_env=False,
            )
            response.raise_for_status()
            payload = response.json()
            answer = payload["choices"][0]["message"]["content"].strip()
            usage = payload.get("usage") or {}
            return GenerationResult(
                answer=answer,
                model=self.settings.chat_model,
                prompt_eval_count=usage.get("prompt_tokens"),
                eval_count=usage.get("completion_tokens"),
            )
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise ModelProviderError("Chat provider unavailable") from exc


def create_provider(settings: Settings) -> ModelProvider:
    if settings.provider == "openai-compatible":
        return OpenAICompatibleProvider(settings)
    return OllamaProvider(settings)
