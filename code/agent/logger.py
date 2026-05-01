from __future__ import annotations

from pathlib import Path

from agent.models import Chunk, Classification, Ticket, TriageDecision


class TranscriptLogger:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")

    def log(
        self,
        ticket: Ticket,
        classification: Classification,
        decision: TriageDecision,
        chunks: list[Chunk],
        response: str,
    ) -> None:
        sources = ", ".join(dict.fromkeys(chunk.source_url for chunk in chunks if chunk.source_url)) or "none"
        entry = (
            f"[{ticket.id}] {'-' * 48}\n"
            f"TICKET: {ticket.text[:500]}\n"
            f"DOMAIN: {classification.domain} ({classification.confidence:.2f})\n"
            f"ISSUE TYPE: {classification.issue_type}\n"
            f"PRODUCT AREA: {classification.product_area}\n"
            f"ACTION: {decision.action.upper()} ({decision.reason}, confidence={decision.confidence:.2f})\n"
            f"SOURCES: {sources}\n"
            f"RESPONSE: {response}\n\n"
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(entry)

