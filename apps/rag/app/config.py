from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAG_", env_file=".env", extra="ignore")

    provider: str = "ollama"
    database_url: str = "postgresql://mykb:mykb@127.0.0.1:5432/mykb"
    ollama_base_url: str = "http://127.0.0.1:11434"
    embedding_model: str = "nomic-embed-text"
    chat_model: str = "qwen2.5:7b"
    openai_base_url: str = "http://127.0.0.1:11434/v1"
    openai_api_key: str = ""
    chunk_size: int = 200
    chunk_overlap: int = 40
    min_score: float = 0.35


def get_settings() -> Settings:
    return Settings()
