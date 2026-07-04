from app.config import Settings
from app.providers import OllamaProvider


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_ollama_provider_ignores_system_proxy_environment(monkeypatch):
    calls = []

    def fake_post(*args, **kwargs):
        calls.append(kwargs)
        return FakeResponse({"embedding": [0.1, 0.2, 0.3]})

    monkeypatch.setattr("app.providers.httpx.post", fake_post)

    provider = OllamaProvider(Settings())
    assert provider.embed("hello") == [0.1, 0.2, 0.3]

    assert calls[0]["trust_env"] is False
