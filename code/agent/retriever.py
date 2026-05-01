from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

from agent.models import Chunk


TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_+-]*")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
    "you",
    "your",
}


def tokenize(text: str) -> list[str]:
    return [tok for tok in TOKEN_RE.findall(text.lower()) if tok not in STOPWORDS and len(tok) > 1]


class Retriever:
    def __init__(self, index_path: str | Path):
        self.index_path = Path(index_path)
        self.chunks = self._load_chunks()
        self.doc_freq = self._doc_freq()
        self.total_docs = max(len(self.chunks), 1)
        self.chunk_vectors = {
            chunk.id: self._tfidf(tokenize(f"{chunk.title} {chunk.text}")) for chunk in self.chunks
        }

    def _load_chunks(self) -> list[Chunk]:
        if not self.index_path.exists():
            return []
        chunks: list[Chunk] = []
        with self.index_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                chunks.append(
                    Chunk(
                        id=str(row["id"]),
                        domain=row.get("domain", "unknown"),
                        title=row.get("title", ""),
                        source_url=row.get("source_url", ""),
                        text=row.get("text", ""),
                    )
                )
        return chunks

    def _doc_freq(self) -> Counter[str]:
        freq: Counter[str] = Counter()
        for chunk in self.chunks:
            freq.update(set(tokenize(f"{chunk.title} {chunk.text}")))
        return freq

    def _tfidf(self, tokens: list[str]) -> dict[str, float]:
        counts = Counter(tokens)
        length = math.sqrt(sum(value * value for value in counts.values())) or 1.0
        vector: dict[str, float] = {}
        for token, count in counts.items():
            idf = math.log((self.total_docs + 1) / (self.doc_freq[token] + 1)) + 1
            vector[token] = (count / length) * idf
        return vector

    @staticmethod
    def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        if len(left) > len(right):
            left, right = right, left
        numerator = sum(value * right.get(token, 0.0) for token, value in left.items())
        left_norm = math.sqrt(sum(value * value for value in left.values())) or 1.0
        right_norm = math.sqrt(sum(value * value for value in right.values())) or 1.0
        return numerator / (left_norm * right_norm)

    def retrieve(self, ticket_text: str, domain: str, top_k: int = 5) -> list[Chunk]:
        if not self.chunks:
            return []
        candidates = [chunk for chunk in self.chunks if domain == "unknown" or chunk.domain == domain]
        if not candidates:
            candidates = self.chunks

        query_vec = self._tfidf(tokenize(ticket_text))
        scored: list[Chunk] = []
        for chunk in candidates:
            chunk_vec = self.chunk_vectors.get(chunk.id, {})
            score = self._cosine(query_vec, chunk_vec)
            if score > 0:
                scored.append(
                    Chunk(
                        id=chunk.id,
                        domain=chunk.domain,
                        title=chunk.title,
                        source_url=chunk.source_url,
                        text=chunk.text,
                        score=round(score, 4),
                    )
                )

        scored.sort(key=lambda item: item.score, reverse=True)
        return _mmr(scored, top_k=top_k)


def _mmr(chunks: list[Chunk], top_k: int) -> list[Chunk]:
    selected: list[Chunk] = []
    seen_titles: set[str] = set()
    for chunk in chunks:
        title_key = chunk.title.lower().strip()
        if title_key and title_key in seen_titles and len(selected) >= max(1, top_k // 2):
            continue
        selected.append(chunk)
        if title_key:
            seen_titles.add(title_key)
        if len(selected) >= top_k:
            break
    return selected
