import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path("graphrag/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "graphrag-pass-123")

N_MULTIHOP = int(os.getenv("GRAPH_N_QUESTIONS", "60"))      # HotpotQA bridge questions
N_DISTRACTORS = int(os.getenv("GRAPH_N_DISTRACTORS", "3"))  # unrelated paragraphs kept per question
N_SINGLE_HOP = int(os.getenv("GRAPH_N_SINGLE_HOP", "30"))   # single-hop control questions
SEED = 13

EMBED_DIM = 384
TOP_K = 5                 # chunks given to the LLM
VECTOR_CANDIDATES = 10    # chunks found by vector search before graph expansion
GRAPH_CANDIDATES = 20     # extra chunks found by graph expansion
MAX_HOPS = 2
RERANK_MODEL = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

CORPUS_FILE = DATA_DIR / "corpus.json"
QUESTIONS_FILE = DATA_DIR / "questions.json"
EXTRACTIONS_FILE = DATA_DIR / "extractions.jsonl"
GRAPH_FILE = DATA_DIR / "graph_data.json"
MERGES_FILE = DATA_DIR / "merges.txt"
