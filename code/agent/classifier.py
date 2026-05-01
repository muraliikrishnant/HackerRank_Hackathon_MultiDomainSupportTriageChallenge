from __future__ import annotations

import re
from collections import Counter

from agent.models import Classification


DOMAIN_KEYWORDS = {
    "visa": {
        "card",
        "visa",
        "transaction",
        "merchant",
        "cvv",
        "pin",
        "chargeback",
        "dispute",
        "payment",
        "unauthorized",
        "fraud",
    },
    "hackerrank": {
        "hackerrank",
        "assessment",
        "candidate",
        "test",
        "proctoring",
        "score",
        "interview",
        "coding challenge",
        "plagiarism",
        "question",
    },
    "claude": {
        "claude",
        "anthropic",
        "api",
        "model",
        "message limit",
        "workspace",
        "billing",
        "prompt",
        "console",
        "token",
    },
}

ISSUE_PATTERNS = [
    ("fraud", r"\b(fraud|unauthorized|identity theft|stolen card|unknown charge)\b"),
    ("billing_dispute", r"\b(refund|chargeback|billing dispute|incorrect charge|overcharged)\b"),
    ("account_access", r"\b(can'?t log in|cannot log in|locked out|account hacked|password reset|2fa|mfa|login)\b"),
    ("assessment", r"\b(assessment|test|score|proctor|candidate|plagiarism|coding challenge)\b"),
    ("permissions", r"\b(permission|role|admin|access denied|workspace access|team access)\b"),
    ("bug", r"\b(error|bug|crash|broken|not working|fails|failure|unable to)\b"),
    ("faq", r"\b(how do i|how to|where can i|what is|can i)\b"),
]

PRODUCT_AREAS = [
    ("hackerrank", "Assessments > Proctoring", r"\b(proctor|webcam|screen share|tab switch)\b"),
    ("hackerrank", "Assessments > Scores", r"\b(score|result|grade|plagiarism)\b"),
    ("claude", "Claude > API", r"\b(api|key|token|rate limit|console|model)\b"),
    ("claude", "Claude > Billing", r"\b(billing|invoice|subscription|refund|charge)\b"),
    ("visa", "Visa > Disputes", r"\b(dispute|chargeback|unauthorized|fraud)\b"),
    ("visa", "Visa > Card Support", r"\b(card|pin|cvv|merchant|transaction)\b"),
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def classify(ticket_text: str) -> Classification:
    text = _normalize(ticket_text)
    domain_scores: Counter[str] = Counter()
    signals: list[str] = []

    for domain, keywords in DOMAIN_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                domain_scores[domain] += 2 if " " in keyword else 1
                signals.append(f"domain:{domain}:{keyword}")

    if domain_scores:
        domain, score = domain_scores.most_common(1)[0]
        total = sum(domain_scores.values())
        domain_confidence = min(0.95, 0.45 + (score / max(total, 1)) * 0.5)
    else:
        domain = "unknown"
        domain_confidence = 0.2

    issue_type = "other"
    for label, pattern in ISSUE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            issue_type = label
            signals.append(f"issue:{label}:{match.group(0)}")
            break

    product_area = "General"
    for area_domain, area, pattern in PRODUCT_AREAS:
        if domain != "unknown" and area_domain != domain:
            continue
        match = re.search(pattern, text)
        if match:
            product_area = area
            signals.append(f"area:{area}:{match.group(0)}")
            break

    confidence = round((domain_confidence + (0.75 if issue_type != "other" else 0.35)) / 2, 3)
    return Classification(domain, issue_type, product_area, confidence, signals)
