"""Configuration settings for the RAG Retrieval Module."""
from pathlib import Path
import os

RETRIEVAL_DIR = Path(__file__).resolve().parent
APP_DIR = RETRIEVAL_DIR.parent
BACKEND_DIR = APP_DIR.parent
ROOT_DIR = BACKEND_DIR.parent

DATA_DIR = BACKEND_DIR / "data"
DOCS_DIR = ROOT_DIR / "data" / "documents"

CHROMA_PERSIST_DIR = DATA_DIR / "chroma_db"
COLLECTION_NAME = "fitzone_corpus"
BM25_INDEX_PATH = DATA_DIR / "bm25_index.pkl"
MANIFEST_PATH = DATA_DIR / "indexing_manifest.json"

# RAG & Chunking Parameters
TOP_K = int(os.getenv("RAG_TOP_K", "4"))
SIMILARITY_THRESHOLD = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.35"))
MAX_RAG_TOKENS = int(os.getenv("MAX_RAG_TOKENS", "600"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "600"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
CACHE_CAPACITY = int(os.getenv("RAG_CACHE_CAPACITY", "256"))
ENABLE_HYBRID_SEARCH = os.getenv("ENABLE_HYBRID_SEARCH", "true").lower() in ("1", "true", "yes")
