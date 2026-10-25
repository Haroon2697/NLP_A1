"""
Context Budgeter Module
Guarantees that retrieved RAG chunks, conversational history, and system instructions
never exceed the model's context window limit (NUM_CTX).
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple
from .config import MAX_RAG_TOKENS


def estimate_tokens(text: str) -> int:
    """
    Fast, safe heuristic for token estimation on CPU.
    Standard rule of thumb for English text: 1 token ≈ 3.8 characters (or 0.75 words).
    Using max of character-based and word-based heuristics with a 15% safety buffer.
    """
    if not text:
        return 0
    char_estimate = int(len(text) / 3.8) + 1
    word_estimate = int(len(text.split()) * 1.3) + 1
    return max(char_estimate, word_estimate)


class ContextBudgeter:
    """
    Allocates and enforces token budgets across System Prompt, Dialogue History,
    and RAG Knowledge Chunks before passing payloads to the LLM.
    """

    def __init__(
        self,
        num_ctx: int = 2048,
        max_response_tokens: int = 256,
        max_rag_tokens: int = MAX_RAG_TOKENS,
    ) -> None:
        self.num_ctx = num_ctx
        self.max_response_tokens = max_response_tokens
        self.max_rag_tokens = max_rag_tokens
        # Total tokens reserved for the full prompt input
        self.prompt_ceiling = max(512, self.num_ctx - self.max_response_tokens - 64)

    def allocate_chunks(
        self,
        chunks: List[Dict[str, Any]],
        system_prompt: str,
        history_messages: List[Dict[str, str]],
        user_query: str,
    ) -> Tuple[str, List[Dict[str, Any]], int]:
        """
        Selects and formats top chunks that fit strictly within the RAG budget
        and prompt ceiling.
        Returns:
            - formatted_context_str: Clean text block ready for prompt injection
            - included_citations: Metadata list of sources used
            - total_rag_tokens: Count of tokens consumed by RAG
        """
        # Calculate tokens consumed by system prompt, history, and user query
        system_tokens = estimate_tokens(system_prompt)
        history_tokens = sum(estimate_tokens(m.get("content", "")) for m in history_messages)
        query_tokens = estimate_tokens(user_query)
        base_tokens = system_tokens + history_tokens + query_tokens

        # Available space for RAG chunks
        remaining_for_rag = min(self.max_rag_tokens, max(0, self.prompt_ceiling - base_tokens))

        if remaining_for_rag <= 50 or not chunks:
            return "", [], 0

        included_citations: List[Dict[str, Any]] = []
        formatted_snippets: List[str] = []
        tokens_used = 0

        for chunk in chunks:
            doc_id = chunk.get("doc_id", "DOC")
            title = chunk.get("title", "FitZone Guide")
            text = chunk.get("text", "").strip()

            snippet_formatted = f"### [Document: {title} | ID: {doc_id}]\n{text}\n"
            snippet_tokens = estimate_tokens(snippet_formatted)

            if tokens_used + snippet_tokens <= remaining_for_rag:
                formatted_snippets.append(snippet_formatted)
                included_citations.append({
                    "doc_id": doc_id,
                    "title": title,
                    "category": chunk.get("category", "General"),
                    "source_file": chunk.get("source_file", ""),
                    "score": chunk.get("similarity", chunk.get("rrf_score", 0.0)),
                    "snippet": text[:200] + "..." if len(text) > 200 else text,
                })
                tokens_used += snippet_tokens
            else:
                # Truncate final chunk if at least 60 tokens remain in budget
                available = remaining_for_rag - tokens_used
                if available >= 60:
                    allowed_chars = int(available * 3.5)
                    truncated_text = text[:allowed_chars].rsplit(" ", 1)[0] + "..."
                    snippet_formatted = f"### [Document: {title} | ID: {doc_id}]\n{truncated_text}\n"
                    formatted_snippets.append(snippet_formatted)
                    included_citations.append({
                        "doc_id": doc_id,
                        "title": title,
                        "category": chunk.get("category", "General"),
                        "source_file": chunk.get("source_file", ""),
                        "score": chunk.get("similarity", chunk.get("rrf_score", 0.0)),
                        "snippet": truncated_text[:200] + "...",
                    })
                    tokens_used += estimate_tokens(snippet_formatted)
                break

        if not formatted_snippets:
            return "", [], 0

        context_header = (
            "## RETRIEVED FITZONE DOMAIN DOCUMENTS (GROUND TRUTH):\n"
            "Ground your answer strictly in the facts and policies below. "
            "Cite the relevant document name(s) where appropriate. "
            "If the documents do not cover the requested detail, state that clearly.\n\n"
        )
        final_context_block = context_header + "\n".join(formatted_snippets)
        return final_context_block, included_citations, estimate_tokens(final_context_block)
