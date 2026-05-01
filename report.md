# Multi-Domain Support Triage Agent Report

## Project Summary

This project builds a support triage agent for three domains: HackerRank, Claude, and Visa. It reads support tickets from `support_tickets/support_tickets.csv`, classifies the domain and issue type, retrieves relevant documentation from a scraped corpus, decides whether to reply or escalate, and writes the final triage result to `support_tickets/output.csv`.

The final system includes:

- Domain classification with `Company` column override
- Issue type classification
- TF-IDF documentation retrieval over scraped support docs
- Sensitive-case escalation rules
- Prompt-injection and malicious-request detection
- Optional Gemini-generated grounded responses
- `.env` support for local API keys
- Human-readable `log.txt` output

## What Worked Well

- The overall architecture stayed clean and modular. The project has separate files for classification, retrieval, triage, response generation, logging, corpus scraping, and CLI orchestration.
- The challenge CSV format is handled directly. The agent reads `Issue`, `Subject`, and `Company`, then writes the expected output columns: `issue`, `subject`, `company`, `response`, `product_area`, `status`, `request_type`, and `justification`.
- The scraper successfully populated the corpus when run with network access. It scraped 50 HackerRank docs, 50 Claude docs, and 42 Visa docs, creating a 2,659-chunk index.
- Escalation behavior works well for sensitive tickets such as account access, score disputes, billing disputes, fraud, prompt injection, and dangerous requests.
- The project can still run without an API key because Gemini is optional. If `GEMINI_API_KEY` is missing, it falls back to a deterministic grounded response.

## What Did Not Work Initially

- The first version used only a small demo corpus, so retrieval quality was limited until the real scraper was run.
- The first version ignored the `Company` column and tried to infer domain only from ticket text. That could classify a Visa billing issue as Claude because `billing` appeared in Claude keywords.
- The first responder copied a sentence from the top retrieved chunk instead of generating a polished support answer.
- Prompt injection and dangerous instructions were not detected at first.
- API credentials were originally handled through environment variables only, then an API key was accidentally pasted into code during testing. This was fixed by adding `.env` support and ignoring `.env` in git.
- One Gemini response contradicted the triage decision by saying a ticket should be escalated even though the CSV status was `resolved`.

## Iteration History

### First Iteration: Initial Agent Scaffold

Commit: `5fe69ca Initial support triage agent`

The first implementation created the base project structure:

- `code/main.py`
- `code/agent/classifier.py`
- `code/agent/retriever.py`
- `code/agent/triage.py`
- `code/agent/responder.py`
- `code/agent/logger.py`
- `code/corpus/scraper.py`
- `code/corpus/chunker.py`

What worked:

- The CLI could read tickets, classify them, retrieve chunks, triage them, and write output.
- The log format was readable.
- The project structure matched the original battle plan.

What did not work:

- It used a deterministic sentence extraction response instead of an LLM.
- It used demo files first instead of the real `support_tickets` folder.
- It did not yet use the `Company` column as a domain override.

Fix:

- The input/output defaults were changed to use `support_tickets/support_tickets.csv` and `support_tickets/output.csv`.

### Second Iteration: Accuracy And Safety Improvements

Commit: `301abe0 Improve triage accuracy and grounded responses`

This iteration fixed the major audit findings.

What worked:

- `Company` became a hard domain override.
- Prompt injection detection was added.
- Dangerous/malicious request detection was added.
- TF-IDF vectors were precomputed at load time.
- Optional LLM response generation was added.

What did not work:

- The first LLM implementation used Anthropic, which was not ideal for this project because the user wanted a cheaper/free option.
- The project still needed a successful real scrape to improve retrieval quality.

Fix:

- The code was structured so the LLM path was optional and could be swapped later.

### Third Iteration: Classifier And Model Hardening

Commit: `5082328 Harden classifier defaults and Claude model`

This iteration cleaned up edge cases.

What worked:

- The classifier now initializes default domain values explicitly.
- This made unknown-domain handling safer and easier to read.

What did not work:

- The Anthropic model default was not the preferred direction anymore.

Fix:

- The model configuration was made easier to override, then later replaced with Gemini.

### Fourth Iteration: Gemini Migration

Commit: `a877695 Use Gemini for optional grounded responses`

This iteration replaced Anthropic with Gemini.

What worked:

- `requirements.txt` now uses `google-genai`.
- `responder.py` now reads `GEMINI_API_KEY`.
- The default model is `gemini-2.5-flash`.
- The deterministic fallback still works without an API key.

What did not work:

- The user still needed a safe place to store the API key locally.

Fix:

- The next iteration added `.env` support.

### Fifth Iteration: `.env` Credential Handling

Commit: `e5b4979 Load Gemini credentials from dotenv`

This iteration moved API key handling into a local `.env` file.

What worked:

- `.env` is ignored by git.
- `.env.example` documents the required variables without exposing secrets.
- `code/env_loader.py` loads local environment variables before the agent runs.

What did not work:

- During testing, a real-looking API key was accidentally pasted into code and `.env.example`.

Fix:

- The key was removed from tracked files.
- A repository scan confirmed no `AIza...` key remained in committed files.

### Sixth Iteration: Reply/Escalation Contradiction Fix

Commit: `e1de207 Prevent reply responses from contradicting triage`

This iteration fixed the visible output contradiction where the CSV said `resolved` but the Gemini response said the issue should be escalated.

What worked:

- The Gemini prompt now says the triage decision has already been made.
- For reply actions, Gemini is told not to say the case should be escalated, routed, handed off, or reviewed by a human.
- A post-LLM guard rejects responses containing escalation language and falls back to the deterministic grounded response.

What did not work:

- LLMs can still occasionally produce wording that is technically safe but less polished than desired.

Fix:

- The guard handles the most important failure mode: action/status contradiction.

## Final Test Commands

Compile check:

```bash
python3 -m compileall code
```

Run with existing scraped/indexed docs:

```bash
python3 code/main.py --build-index
```

Scrape fresh docs and rebuild the index:

```bash
python3 code/main.py --scrape --scrape-limit 50 --build-index
```

Check that `.env` is ignored:

```bash
git check-ignore -v .env
```

Check for accidentally committed Gemini keys:

```bash
rg "AIza" . --hidden -g '!data/**' -g '!vector_store/**' -g '!log.txt' -g '!support_tickets/output.csv' -g '!*.pyc' -g '!.git/**'
```

## Final Result

The final agent processes all 29 challenge tickets, uses a 2,659-chunk documentation index, produces real source URLs, escalates sensitive cases, answers answerable cases, and avoids leaking secrets or contradicting its own triage status.

## Remaining Limitations

- Gemini responses depend on `GEMINI_API_KEY` and available quota.
- The scraper depends on live support sites and may need network approval.
- The TF-IDF retriever is lightweight and reliable, but a real embedding retriever could improve semantic matching.
- The output quality depends heavily on scraped documentation coverage.

