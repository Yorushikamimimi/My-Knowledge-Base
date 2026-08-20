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


def test_ollama_provider_generate_parses_usage(monkeypatch):
    payload = {
        "response": " 正常 ",
        "prompt_eval_count": 35,
        "eval_count": 2,
        "total_duration": 152000000,
        "eval_duration": 22000000,
    }

    def fake_post(*args, **kwargs):
        return FakeResponse(payload)

    monkeypatch.setattr("app.providers.httpx.post", fake_post)

    provider = OllamaProvider(Settings())
    result = provider.generate("只回答两个字：正常")

    assert result.answer == "正常"
    assert result.model == "qwen2.5:7b"
    assert result.prompt_eval_count == 35
    assert result.eval_count == 2
    assert result.total_duration_ns == 152000000
    assert result.eval_duration_ns == 22000000
