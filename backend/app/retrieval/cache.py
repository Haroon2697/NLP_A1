"""Thread-safe LRU Cache for RAG queries and retrieved results."""
from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Any, Dict, List, Optional


class QueryCache:
    """
    Least-Recently-Used (LRU) Cache for query retrieval results.
    Caches top-k chunks and metadata to avoid redundant vector and keyword searches
    for identical or repeated user prompts.
    """

    def __init__(self, capacity: int = 256) -> None:
        self.capacity = capacity
        self.cache: OrderedDict[str, List[Dict[str, Any]]] = OrderedDict()
        self.lock = threading.Lock()
        self.hits: int = 0
        self.misses: int = 0

    def _normalize_key(self, query: str) -> str:
        return " ".join(query.strip().lower().split())

    def get(self, query: str) -> Optional[List[Dict[str, Any]]]:
        key = self._normalize_key(query)
        with self.lock:
            if key in self.cache:
                self.hits += 1
                self.cache.move_to_end(key)
                return self.cache[key]
            self.misses += 1
            return None

    def put(self, query: str, results: List[Dict[str, Any]]) -> None:
        key = self._normalize_key(query)
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = results
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)

    def clear(self) -> None:
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def stats(self) -> Dict[str, Any]:
        with self.lock:
            total = self.hits + self.misses
            hit_ratio = round(self.hits / total, 3) if total > 0 else 0.0
            return {
                "size": len(self.cache),
                "capacity": self.capacity,
                "hits": self.hits,
                "misses": self.misses,
                "hit_ratio": hit_ratio,
            }
