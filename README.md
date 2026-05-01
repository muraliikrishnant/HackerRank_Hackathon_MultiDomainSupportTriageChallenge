# Multi-Domain Support Triage Agent

Runnable baseline for a HackerRank hackathon support triage agent. It classifies tickets across HackerRank, Claude, and Visa; retrieves grounded documentation chunks; chooses reply versus escalation; and writes both `output.csv` and `log.txt`.

## Quick Start

```bash
python3 code/main.py --build-index
```

Expected corpus layout:

```text
data/
  hackerrank/*.txt
  claude/*.txt
  visa/*.txt
```

Each `.txt` can be plain text or JSON with `url`, `title`, and `text` fields. The index is written to `vector_store/chunks.jsonl`.

## Input CSV

By default, the runner reads `support_tickets/support_tickets.csv` and writes `support_tickets/output.csv`. It accepts common columns such as `ticket_id`, `id`, `subject`, `body`, `description`, `message`, and `issue`. Unknown schemas fall back to concatenating the row values.

## Output CSV

For the challenge input schema (`Issue`, `Subject`, `Company`), the output matches `support_tickets/output.csv`:

- `issue`
- `subject`
- `company`
- `response`
- `product_area`
- `status`
- `request_type`
- `justification`

For generic CSV inputs, the output contains:

- `ticket_id`
- `domain`
- `issue_type`
- `product_area`
- `action`
- `response`
- `sources`
- `confidence`
- `triage_reason`

## Scraping

The scraper is optional because live website access may be restricted in judging environments.

```python
from corpus.scraper import scrape_all
scrape_all("data", limit_per_domain=50)
```

## Design Notes

- The default retriever is a pure-Python TF-IDF cosine retriever, so the project runs without FAISS or model downloads.
- Sensitive cases such as fraud, account access, billing disputes, legal mentions, and score disputes escalate.
- Responses are generated only from retrieved documentation snippets.
