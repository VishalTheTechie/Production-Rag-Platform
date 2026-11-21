import os

from dotenv import load_dotenv

load_dotenv()

# --- API keys and providers ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PROVIDERS = [p.strip() for p in os.getenv("PROVIDERS", "groq,gemini").split(",") if p.strip()]

# --- Models ---
LARGE_MODEL = os.getenv("LARGE_MODEL", "gemini-3.8-flash")
SMALL_MODEL = os.getenv("SMALL_MODEL", "gemini-3.5-flash-lite")
GROQ_LARGE = os.getenv("GROQ_LARGE", "openai/gpt-oss-120b")
GROQ_SMALL = os.getenv("GROQ_SMALL", "openai/gpt-oss-20b")
FALLBACK_MODELS = [m for m in os.getenv(
    "FALLBACK_MODELS", "gemini-3.8-flash,gemini-3.6-flash,gemini-3.5-flash-lite").split(",") if m]

# --- Vector database and embeddings ---
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = "chunks"
EMBED_MODEL = "all-MiniLM-L6-v2"
EMBED_DIM = 384

# --- Chunking and retrieval ---
CHUNK_WORDS = 350      # roughly 500 tokens
CHUNK_OVERLAP = 60
TOP_K = 5

# --- Security ---
JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-secret-change-me-0123456789abcdef")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "demo123")
AUDIT_DB = os.getenv("AUDIT_DB", "audit.db")

# --- Semantic cache, routing and cost tracking ---
CACHE_COLLECTION = os.getenv("CACHE_COLLECTION", "cache")
CACHE_THRESHOLD = float(os.getenv("CACHE_THRESHOLD", "0.85"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", str(24 * 3600)))
VERIFY_ENABLED = os.getenv("VERIFY_ENABLED", "true").lower() == "true"
VERIFY_MODEL = os.getenv("VERIFY_MODEL", "cross-encoder/quora-distilroberta-base")
VERIFY_THRESHOLD = float(os.getenv("VERIFY_THRESHOLD", "0.995"))
METRICS_DB = os.getenv("METRICS_DB", "metrics.db")
ROUTER_MODE = os.getenv("ROUTER_MODE", "rules")
FLAT_GAP = float(os.getenv("FLAT_GAP", "0.10"))

# Simulated prices in USD per 1M tokens (input, output). The API tiers used here are free,
# so cost is tokens x these example list prices. Check the provider's pricing page.
PRICES = {"openai/gpt-oss-120b": (0.15, 0.60), "openai/gpt-oss-20b": (0.075, 0.30)}
DEFAULT_PRICE = (0.15, 0.60)
