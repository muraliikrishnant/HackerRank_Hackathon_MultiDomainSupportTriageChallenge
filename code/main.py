from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from agent.models import Ticket
from agent.pipeline import SupportTriagePipeline
from corpus.chunker import build_jsonl_index


INTERNAL_FIELDNAMES = [
    "ticket_id",
    "domain",
    "issue_type",
    "product_area",
    "action",
    "response",
    "sources",
    "confidence",
    "triage_reason",
]

CHALLENGE_FIELDNAMES = [
    "issue",
    "subject",
    "company",
    "response",
    "product_area",
    "status",
    "request_type",
    "justification",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the multi-domain support triage agent.")
    parser.add_argument("--input", default="support_tickets/support_tickets.csv", help="Input support tickets CSV.")
    parser.add_argument("--output", default="support_tickets/output.csv", help="Output CSV path.")
    parser.add_argument("--log", default="log.txt", help="Transcript log path.")
    parser.add_argument("--corpus-dir", default="data", help="Directory containing domain/*.txt docs.")
    parser.add_argument("--index", default="vector_store/chunks.jsonl", help="Chunk index JSONL path.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of retrieved chunks per ticket.")
    parser.add_argument("--build-index", action="store_true", help="Build chunk index before running tickets.")
    return parser.parse_args()


def read_tickets(path: str | Path) -> list[Ticket]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Input CSV not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [_ticket_from_row(idx, row) for idx, row in enumerate(reader, start=1)]


def _ticket_from_row(idx: int, row: dict[str, str]) -> Ticket:
    lowered = {key.lower().strip(): value for key, value in row.items() if key}
    ticket_id = (
        lowered.get("ticket_id")
        or lowered.get("id")
        or lowered.get("issue_id")
        or lowered.get("case_id")
        or f"TICKET-{idx:03d}"
    )
    subject = lowered.get("subject") or lowered.get("title") or ""
    body = (
        lowered.get("body")
        or lowered.get("description")
        or lowered.get("message")
        or lowered.get("issue")
        or lowered.get("ticket")
        or ""
    )
    if not subject and not body:
        body = " ".join(value for value in row.values() if value)
    return Ticket(str(ticket_id), subject, body, row)


def write_output(path: str | Path, rows: list[dict[str, str | float]], fieldnames: list[str]) -> None:
    path = Path(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def is_challenge_schema(tickets: list[Ticket]) -> bool:
    if not tickets:
        return False
    keys = {key.lower().strip() for key in tickets[0].raw}
    return {"issue", "subject", "company"}.issubset(keys)


def challenge_row(ticket: Ticket, result: dict[str, str | float]) -> dict[str, str | float]:
    status = "escalated" if result["action"] == "escalate" else "resolved"
    return {
        "issue": _raw_get(ticket.raw, "issue"),
        "subject": _raw_get(ticket.raw, "subject"),
        "company": _raw_get(ticket.raw, "company") or result["domain"],
        "response": result["response"],
        "product_area": result["product_area"],
        "status": status,
        "request_type": result["issue_type"],
        "justification": f"{result['triage_reason']}; confidence={result['confidence']}; sources={result['sources'] or 'none'}",
    }


def _raw_get(row: dict[str, str], key: str) -> str:
    for row_key, value in row.items():
        if row_key.lower().strip() == key:
            return value
    return ""


def main() -> int:
    args = parse_args()
    if args.build_index or not Path(args.index).exists():
        count = build_jsonl_index(args.corpus_dir, args.index)
        print(f"Built index with {count} chunks at {args.index}", file=sys.stderr)

    tickets = read_tickets(args.input)
    pipeline = SupportTriagePipeline(args.index, args.log, top_k=args.top_k)
    challenge_schema = is_challenge_schema(tickets)
    rows: list[dict[str, str | float]] = []
    for ticket in tickets:
        result = pipeline.process(ticket)
        rows.append(challenge_row(ticket, result) if challenge_schema else result)
    write_output(args.output, rows, CHALLENGE_FIELDNAMES if challenge_schema else INTERNAL_FIELDNAMES)
    print(f"Processed {len(rows)} tickets -> {args.output}; log -> {args.log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
