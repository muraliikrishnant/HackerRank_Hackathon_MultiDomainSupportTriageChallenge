from __future__ import annotations

from agent.classifier import classify
from agent.logger import TranscriptLogger
from agent.models import Ticket
from agent.responder import generate_response
from agent.retriever import Retriever
from agent.triage import should_escalate


class SupportTriagePipeline:
    def __init__(self, index_path: str, log_path: str, top_k: int = 5):
        self.retriever = Retriever(index_path)
        self.logger = TranscriptLogger(log_path)
        self.top_k = top_k

    def process(self, ticket: Ticket) -> dict[str, str | float]:
        classification = classify(ticket.text, company=_raw_get(ticket.raw, "company"))
        chunks = self.retriever.retrieve(ticket.text, classification.domain, top_k=self.top_k)
        decision = should_escalate(ticket.text, chunks, classification)
        response = generate_response(ticket, chunks, classification, decision)
        self.logger.log(ticket, classification, decision, chunks, response)

        sources = ";".join(dict.fromkeys(chunk.source_url for chunk in chunks if chunk.source_url))
        return {
            "ticket_id": ticket.id,
            "domain": classification.domain,
            "issue_type": classification.issue_type,
            "product_area": classification.product_area,
            "action": decision.action,
            "response": response,
            "sources": sources,
            "confidence": round(min(classification.confidence, decision.confidence), 3),
            "triage_reason": decision.reason,
        }


def _raw_get(row: dict[str, object], key: str) -> str:
    for row_key, value in row.items():
        if row_key.lower().strip() == key:
            return str(value or "")
    return ""
