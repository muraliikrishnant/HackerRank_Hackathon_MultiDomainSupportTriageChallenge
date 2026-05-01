from __future__ import annotations

from agent.models import Chunk, Classification, Ticket, TriageDecision


def generate_response(
    ticket: Ticket,
    chunks: list[Chunk],
    classification: Classification,
    decision: TriageDecision,
) -> str:
    if decision.action == "escalate":
        return _escalation_response(classification, decision)

    if not chunks:
        return _escalation_response(classification, TriageDecision("escalate", "missing_context", 0.8))

    best = chunks[0]
    answer = _extract_actionable_sentence(best.text)
    source_title = best.title or "the support documentation"
    return (
        "Thanks for reaching out. Based on the available documentation, "
        f"{answer} If that does not resolve the issue, reply with the exact error message "
        "or a screenshot so support can review the next step.\n\n"
        f"Source: {source_title}"
    )


def _escalation_response(classification: Classification, decision: TriageDecision) -> str:
    area = classification.product_area if classification.product_area != "General" else "this request"
    return (
        f"Thanks for the details. I am routing {area} to a human support specialist because "
        f"it needs review beyond the public documentation ({decision.reason}). Please include "
        "any relevant account email, timestamps, screenshots, or transaction/test IDs so the "
        "team can investigate quickly."
    )


def _extract_actionable_sentence(text: str) -> str:
    clean = " ".join(text.split())
    if not clean:
        return "the relevant help article should be followed for this request."
    sentences = [part.strip() for part in clean.replace("?", ".").replace("!", ".").split(".")]
    useful = [sentence for sentence in sentences if len(sentence.split()) >= 8]
    chosen = useful[0] if useful else clean[:240]
    if len(chosen) > 280:
        chosen = chosen[:277].rsplit(" ", 1)[0] + "..."
    return _lowercase_first_word(chosen) + "."


def _lowercase_first_word(sentence: str) -> str:
    first, separator, rest = sentence.partition(" ")
    if first.isupper() or any(char.isupper() for char in first[1:]):
        return sentence
    return first.lower() + separator + rest
