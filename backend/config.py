import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    BASE_DIR: Path = BASE_DIR
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"))
    UPLOAD_DIR: str = str(BASE_DIR / os.getenv("UPLOAD_DIR", "./uploads"))
    
    JWT_SECRET: str = os.getenv("JWT_SECRET", "supersecret-document-qa-jwt-key-2026-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "gemini")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gemini-2.0-flash")
    
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "4"))

    # Runtime overrides (configured via UI Settings dialog)
    runtime_overrides = {}

    @classmethod
    def get(cls, key: str, default=None):
        if key in cls.runtime_overrides:
            return cls.runtime_overrides[key]
        return getattr(cls, key, default)

    @classmethod
    def set(cls, key: str, value):
        cls.runtime_overrides[key] = value

settings = Settings()

# Ensure directories exist
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
