from __future__ import annotations

import json
import re
from pathlib import Path


WORD_RE = re.compile(r"\S+")


def chunk_text(text: str, chunk_size: int = 260, overlap: int = 50) -> list[str]:
    words = WORD_RE.findall(text)
    if not words:
        return []
    chunks: list[str] = []
    step = max(1, chunk_size - overlap)
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + chunk_size])
        if chunk:
            chunks.append(chunk)
        if start + chunk_size >= len(words):
            break
    return chunks


def build_jsonl_index(corpus_dir: str | Path, output_path: str | Path) -> int:
    corpus_dir = Path(corpus_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0

    with output_path.open("w", encoding="utf-8") as out:
        for path in sorted(corpus_dir.glob("*/*.txt")):
            domain = path.parent.name
            title = path.stem.replace("_", " ").replace("-", " ").strip().title()
            source_url = ""
            text = path.read_text(encoding="utf-8", errors="ignore")

            if text.startswith("{"):
                try:
                    doc = json.loads(text)
                    title = doc.get("title") or title
                    source_url = doc.get("url") or doc.get("source_url") or ""
                    text = doc.get("text") or ""
                except json.JSONDecodeError:
                    pass

            for idx, chunk in enumerate(chunk_text(text)):
                row = {
                    "id": f"{domain}:{path.stem}:{idx}",
                    "domain": domain,
                    "title": title,
                    "source_url": source_url,
                    "text": chunk,
                }
                out.write(json.dumps(row, ensure_ascii=True) + "\n")
                count += 1
    return count

