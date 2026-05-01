from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Ticket:
    id: str
    subject: str
    body: str
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        parts = [self.subject.strip(), self.body.strip()]
        return "\n\n".join(part for part in parts if part)


@dataclass(slots=True)
class Classification:
    domain: str
    issue_type: str
    product_area: str
    confidence: float
    signals: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Chunk:
    id: str
    domain: str
    title: str
    source_url: str
    text: str
    score: float = 0.0


@dataclass(slots=True)
class TriageDecision:
    action: str
    reason: str
    confidence: float

