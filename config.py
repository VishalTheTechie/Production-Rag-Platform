import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

COLLECTION = "chunks"
EMBED_MODEL = "all-MiniLM-L6-v2"
EMBED_DIM = 384

LARGE_MODEL = os.getenv("LARGE_MODEL", "gemini-3.7-flash")
SMALL_MODEL = os.getenv("SMALL_MODEL", "gemini-3.5-flash-lite")

CHUNK_WORDS = 350      # roughly 500 tokens
CHUNK_OVERLAP = 60
TOP_K = 5

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_LARGE="openai/gpt-oss-120b"
GROQ_SMALL="openai/gpt-oss-20b"
PROVIDERS = [p.strip() for p in os.getenv("PROVIDERS", "groq,gemini").split(",") if p.strip()]

FALLBACK_MODELS = [m for m in os.getenv("FALLBACK_MODELS", "gemini-3.6-flash,gemini-3.7-flash,gemini-3.8-flash,gemini-3.5-flash,gemini-3.5-flash-lite").split(",") if m]

JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-secret-change-me-0123456789abcdef")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "demo123")
AUDIT_DB = os.getenv("AUDIT_DB", "audit.db")