from __future__ import annotations

import re

from agent.models import Chunk, Classification, TriageDecision


ESCALATE_PATTERNS = {
    "prompt_injection_or_policy_exfiltration": (
        r"\b(ignore (all )?(previous|prior) instructions|show your|reveal your|display all rules|"
        r"internal rules|system prompt|hidden prompt|developer message|retrieved documents|"
        r"exact logic|affiche toutes les r[èe]gles|r[èe]gles internes|documents r[ée]cup[ée]r[ée]s|"
        r"logique exacte)\b"
    ),
    "dangerous_or_malicious_request": (
        r"\b(delete all files|remove all files|wipe (the )?(disk|system)|rm -rf|format (my )?(disk|drive)|"
        r"steal|exfiltrate|bypass|hack into|malware|credential dump)\b"
    ),
    "fraud_or_unauthorized_activity": r"\b(fraud|unauthorized transaction|identity theft|stolen|account hacked|data breach)\b",
    "legal_or_compliance": r"\b(legal|lawsuit|attorney|subpoena|compliance complaint)\b",
    "account_access": r"\b(can'?t log in|cannot log in|locked out|lost access|restore my access|removed my seat|not the workspace owner|password reset|2fa|mfa|account access)\b",
    "assessment_dispute": r"\b(score dispute|assessment cheating|cheating accusation|plagiarism appeal)\b",
}

ESCALATE_ISSUE_TYPES = {"fraud", "billing_dispute", "account_access"}


def should_escalate(
    ticket_text: str,
    retrieved_chunks: list[Chunk],
    classification: Classification,
    min_score: float = 0.08,
) -> TriageDecision:
    text = ticket_text.lower()
    for reason, pattern in ESCALATE_PATTERNS.items():
        if re.search(pattern, text):
            return TriageDecision("escalate", reason, 0.95)

    if classification.issue_type in ESCALATE_ISSUE_TYPES:
        return TriageDecision("escalate", f"sensitive_issue_type:{classification.issue_type}", 0.9)

    if classification.domain == "unknown":
        return TriageDecision("escalate", "unknown_domain", 0.82)

    best_score = max((chunk.score for chunk in retrieved_chunks), default=0.0)
    if best_score < min_score:
        return TriageDecision("escalate", "no_corpus_coverage", 0.8)

    if classification.confidence < 0.45:
        return TriageDecision("escalate", "low_classification_confidence", 0.7)

    return TriageDecision("reply", "answerable_from_documentation", min(0.92, 0.55 + best_score))
