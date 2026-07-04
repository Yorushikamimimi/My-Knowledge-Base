from typing import Protocol

import httpx

from app.config import Settings


class ModelProvider(Protocol):
    @property
    def name(self) -> str: ...

    def embed(self, text: str) -> list[float]: ...

    def generate(self, prompt: str) -> str: ...


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

    def generate(self, prompt: str) -> str:
        try:
            response = httpx.post(
                f"{self.settings.ollama_base_url}/api/generate",
                json={"model": self.settings.chat_model, "prompt": prompt, "stream": False},
                timeout=120,
                trust_env=False,
            )
            response.raise_for_status()
            answer = response.json().get("response")
            if not isinstance(answer, str) or not answer.strip():
                raise ModelProviderError("Ollama generation response did not contain answer")
            return answer.strip()
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

    def generate(self, prompt: str) -> str:
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
            return response.json()["choices"][0]["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise ModelProviderError("Chat provider unavailable") from exc


def create_provider(settings: Settings) -> ModelProvider:
    if settings.provider == "openai-compatible":
        return OpenAICompatibleProvider(settings)
    return OllamaProvider(settings)
