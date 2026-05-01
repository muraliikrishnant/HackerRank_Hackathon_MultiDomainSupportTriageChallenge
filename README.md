# Multi-Domain Support Triage Agent

Runnable baseline for a HackerRank hackathon support triage agent. It classifies tickets across HackerRank, Claude, and Visa; retrieves grounded documentation chunks; chooses reply versus escalation; and writes both `output.csv` and `log.txt`.

## Quick Start

```bash
python3 code/main.py --build-index
```

To scrape fresh docs first:

```bash
python3 code/main.py --scrape --build-index
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

The scraper is optional because live website access may be restricted in judging environments. It can be run through the main CLI or directly:

```bash
python3 -m corpus.scraper --output-dir data --limit-per-domain 50
```

When running as a module from the repository root, set `PYTHONPATH=code` if your shell cannot resolve `corpus`.

## LLM Responses

If `GEMINI_API_KEY` is set, responses are generated with Gemini using only retrieved documentation as context. The default model is `gemini-2.5-flash`, and you can override it with `GEMINI_MODEL`. If the key or package is unavailable, the agent falls back to a deterministic grounded response so the project still runs offline.

Create a local `.env` file for your API key:

```bash
cp .env.example .env
```

Then edit `.env`:

```text
GEMINI_API_KEY=your_real_key_here
GEMINI_MODEL=gemini-2.5-flash
```

The `.env` file is ignored by git and should not be committed.

## Design Notes

- The default retriever is a pure-Python TF-IDF cosine retriever, so the project runs without FAISS or model downloads.
- Sensitive cases such as fraud, account access, billing disputes, legal mentions, and score disputes escalate.
- Responses are generated only from retrieved documentation snippets.
