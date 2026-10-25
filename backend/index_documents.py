"""
Offline Document Indexing Pipeline for FitZone Gym (Assignment 2)
Chunks 50-100 Markdown domain documents, computes ONNX embeddings locally on CPU,
stores them into persistent ChromaDB, and builds the BM25 index for Hybrid Search.
Features:
- Idempotent and re-runnable with SHA-256 hash checking
- Section-aware chunking with token overlap
- Metadata preservation (doc_id, title, category, chunk_index)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import chromadb
from chromadb.utils import embedding_functions

# Ensure backend package can be imported
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.retrieval.config import (
    BM25_INDEX_PATH,
    CHROMA_PERSIST_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    COLLECTION_NAME,
    DATA_DIR,
    DOCS_DIR,
    MANIFEST_PATH,
)
from backend.app.retrieval.hybrid_search import BM25Retriever

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fitzone.indexer")


def compute_file_hash(filepath: Path) -> str:
    """Computes SHA-256 hash of file contents for change tracking."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


def parse_metadata_from_markdown(content: str) -> Dict[str, str]:
    """Extracts document title, ID, category from markdown header."""
    metadata = {
        "title": "FitZone Document",
        "doc_id": "DOC",
        "category": "General",
    }
    lines = content.splitlines()
    for line in lines:
        line_s = line.strip()
        if line_s.startswith("# "):
            metadata["title"] = line_s[2:].strip()
        elif "Document ID" in line_s or "doc_id" in line_s:
            match = re.search(r":\s*([A-Za-z0-9_-]+)", line_s)
            if match:
                metadata["doc_id"] = match.group(1).strip()
        elif "Category" in line_s:
            match = re.search(r":\s*(.+)", line_s)
            if match:
                metadata["category"] = match.group(1).strip()
    return metadata


def chunk_document(
    filepath: Path,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[Dict[str, Any]]:
    """
    Section-aware semantic chunking with document context preservation.
    1. Indexes the full document as chunk 1 so comprehensive details (Overview, Rates,
       Hours, Benefits) are never separated.
    2. Indexes individual sections with the document title and ID prepended as context,
       ensuring queries matching specific sections retain full document metadata.
    """
    content = filepath.read_text(encoding="utf-8")
    meta = parse_metadata_from_markdown(content)
    chunks: List[Dict[str, Any]] = []
    chunk_idx = 0

    # 1. Primary Full Document Chunk
    chunk_idx += 1
    chunks.append({
        "id": f"{meta['doc_id']}_c{chunk_idx}",
        "text": content.strip(),
        "doc_id": meta["doc_id"],
        "title": meta["title"],
        "category": meta["category"],
        "source_file": filepath.name,
        "chunk_index": chunk_idx,
    })

    # 2. Section Chunks with Document Header Injected
    sections = re.split(r"\n(?=## )", content)
    # sections[0] contains the document title and top metadata
    for section in sections[1:]:
        section_cleaned = section.strip()
        if not section_cleaned:
            continue

        context_header = f"# {meta['title']} [Doc: {meta['doc_id']}]\n"
        chunk_text = f"{context_header}\n{section_cleaned}"

        chunk_idx += 1
        chunks.append({
            "id": f"{meta['doc_id']}_c{chunk_idx}",
            "text": chunk_text,
            "doc_id": meta["doc_id"],
            "title": meta["title"],
            "category": meta["category"],
            "source_file": filepath.name,
            "chunk_index": chunk_idx,
        })

    return chunks


def load_manifest() -> Dict[str, str]:
    if MANIFEST_PATH.exists():
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_manifest(manifest: Dict[str, str]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def run_indexing(force: bool = False) -> Dict[str, Any]:
    """
    Executes the offline indexing pipeline.
    Re-runs incrementally unless --force is specified.
    """
    start_time = time.perf_counter()
    logger.info("=" * 60)
    logger.info("Starting FitZone Gym Offline Indexing Pipeline (Assignment 2)")
    logger.info(f"Corpus Directory: {DOCS_DIR}")
    logger.info(f"Chroma DB Directory: {CHROMA_PERSIST_DIR}")
    logger.info("=" * 60)

    if not DOCS_DIR.exists():
        raise FileNotFoundError(f"Documents directory not found at: {DOCS_DIR}")

    doc_files = sorted(list(DOCS_DIR.glob("*.md")) + list(DOCS_DIR.glob("*.txt")))
    if not doc_files:
        raise ValueError(f"No documents found in {DOCS_DIR}. Please run generate_corpus.py first.")

    logger.info(f"Found {len(doc_files)} domain documents in corpus.")

    manifest = load_manifest()
    current_hashes = {f.name: compute_file_hash(f) for f in doc_files}

    # Determine files that require indexing
    files_to_index: List[Path] = []
    for f in doc_files:
        if force or f.name not in manifest or manifest[f.name] != current_hashes[f.name]:
            files_to_index.append(f)

    # Initialize Chroma Persistent Client
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()

    if force:
        try:
            client.delete_collection(name=COLLECTION_NAME)
            logger.info(f"Deleted existing collection '{COLLECTION_NAME}' for force re-indexing.")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    if not files_to_index and collection.count() > 0 and BM25_INDEX_PATH.exists():
        elapsed = round(time.perf_counter() - start_time, 3)
        logger.info(f"All {len(doc_files)} documents are already indexed and up to date! ({elapsed}s)")
        return {
            "status": "up_to_date",
            "indexed_docs": 0,
            "total_docs": len(doc_files),
            "total_chunks": collection.count(),
            "elapsed_seconds": elapsed,
        }

    logger.info(f"Processing {len(files_to_index)} documents for indexing/updating...")

    all_chunks: List[Dict[str, Any]] = []
    for doc_path in doc_files:
        doc_chunks = chunk_document(doc_path)
        all_chunks.extend(doc_chunks)

    logger.info(f"Total chunks extracted from corpus: {len(all_chunks)}")

    # Delete existing items for modified files to ensure idempotency
    if not force and files_to_index:
        for f in files_to_index:
            try:
                collection.delete(where={"source_file": f.name})
            except Exception:
                pass

    # Batch add to ChromaDB
    batch_size = 64
    total_added = 0
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]
        ids = [c["id"] for c in batch]
        texts = [c["text"] for c in batch]
        metadatas = [
            {
                "doc_id": c["doc_id"],
                "title": c["title"],
                "category": c["category"],
                "source_file": c["source_file"],
                "chunk_index": c["chunk_index"],
            }
            for c in batch
        ]
        collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
        total_added += len(batch)
        logger.info(f"Indexed {total_added}/{len(all_chunks)} chunks into ChromaDB...")

    # Build and save BM25 Sparse Index
    logger.info("Building BM25 Sparse Index for Hybrid Keyword Search...")
    bm25_retriever = BM25Retriever()
    bm25_retriever.build_index(all_chunks)
    bm25_retriever.save(BM25_INDEX_PATH)
    logger.info(f"Saved BM25 index to: {BM25_INDEX_PATH}")

    # Update manifest
    save_manifest(current_hashes)

    elapsed = round(time.perf_counter() - start_time, 3)
    total_chunks = collection.count()

    logger.info("=" * 60)
    logger.info("Indexing Pipeline Complete!")
    logger.info(f"Documents Indexed: {len(doc_files)}")
    logger.info(f"Total Chunks in Vector Store: {total_chunks}")
    logger.info(f"Pipeline Duration: {elapsed}s")
    logger.info("=" * 60)

    return {
        "status": "success",
        "indexed_docs": len(doc_files),
        "total_chunks": total_chunks,
        "elapsed_seconds": elapsed,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FitZone Document Indexing Pipeline")
    parser.add_argument("--force", action="store_true", help="Force rebuild vector store and BM25 index from scratch")
    args = parser.parse_args()

    run_indexing(force=args.force)
