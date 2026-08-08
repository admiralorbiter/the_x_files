import os
from dataclasses import dataclass

@dataclass
class Config:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    default_model: str = os.getenv("OLLAMA_MODEL", "gemma3:12b")
    fallback_model: str = os.getenv("OLLAMA_FALLBACK_MODEL", "mistral:latest")
    db_path: str = os.getenv("EMERGENCE_DB_PATH", "emergence_lab.db")
    temperature: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
    request_timeout: int = int(os.getenv("OLLAMA_TIMEOUT", "60"))

default_config = Config()
