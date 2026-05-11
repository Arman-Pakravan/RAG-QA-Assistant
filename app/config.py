from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    llm_model: str = "claude-haiku-4-5-20251001"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_min_tokens: int = 300
    chunk_max_tokens: int = 800
    top_k: int = 5
    index_dir: str = "./data/index"
    upload_dir: str = "./data/uploads"

    class Config:
        env_file = ".env"
        extra = "ignore"

    def ensure_dirs(self):
        Path(self.index_dir).mkdir(parents=True, exist_ok=True)
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()