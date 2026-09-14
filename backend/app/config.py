import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"


def get_setting(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


OLLAMA_BASE_URL = get_setting("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = get_setting("OLLAMA_MODEL", "qwen2.5:3b-instruct")
MAX_HISTORY_PAIRS = int(get_setting("MAX_HISTORY_PAIRS", "6"))
MAX_RESPONSE_TOKENS = int(get_setting("MAX_RESPONSE_TOKENS", "256"))
TEMPERATURE = float(get_setting("TEMPERATURE", "0.3"))
TOP_P = float(get_setting("TOP_P", "0.9"))
NUM_CTX = int(get_setting("NUM_CTX", "2048"))

HOST = get_setting("HOST", "0.0.0.0")
PORT = int(get_setting("PORT", "8000"))
