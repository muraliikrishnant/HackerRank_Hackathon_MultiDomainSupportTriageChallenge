from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - optional runtime dependency
    requests = None
    BeautifulSoup = None


SITES = {
    "hackerrank": "https://support.hackerrank.com/",
    "claude": "https://support.claude.com/en/",
    "visa": "https://www.visa.co.in/support.html",
}


def scrape_all(output_dir: str | Path, limit_per_domain: int = 50) -> dict[str, int]:
    if requests is None or BeautifulSoup is None:
        raise RuntimeError("Install requests and beautifulsoup4 to use the scraper.")

    output_dir = Path(output_dir)
    results: dict[str, int] = {}
    for domain, start_url in SITES.items():
        results[domain] = scrape_domain(domain, start_url, output_dir / domain, limit_per_domain)
    return results


def scrape_domain(domain: str, start_url: str, output_dir: Path, limit: int) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    queue = [start_url]
    saved = 0
    base_host = urlparse(start_url).netloc

    while queue and saved < limit:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            response = requests.get(url, timeout=15, headers={"User-Agent": "support-triage-bot/1.0"})
            response.raise_for_status()
        except requests.RequestException:
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        title = (soup.find("h1") or soup.find("title"))
        title_text = title.get_text(" ", strip=True) if title else url
        body = soup.get_text("\n", strip=True)
        body = re.sub(r"\n{3,}", "\n\n", body)

        if len(body.split()) > 80:
            slug = _slugify(title_text or f"article-{saved}")
            (output_dir / f"{slug}.txt").write_text(
                json.dumps({"url": url, "domain": domain, "title": title_text, "text": body}, indent=2),
                encoding="utf-8",
            )
            saved += 1

        for link in soup.find_all("a", href=True):
            href = urljoin(url, link["href"]).split("#", 1)[0]
            parsed = urlparse(href)
            if parsed.netloc == base_host and href not in seen and _looks_like_article(href):
                queue.append(href)

    return saved


def _looks_like_article(url: str) -> bool:
    lowered = url.lower()
    return not any(part in lowered for part in ["login", "signup", "facebook", "twitter", "linkedin"])


def _slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value[:80] or "article"


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape support documentation into data/{domain}/*.txt.")
    parser.add_argument("--output-dir", default="data", help="Directory where scraped documents are written.")
    parser.add_argument("--limit-per-domain", type=int, default=50, help="Maximum pages to save per domain.")
    args = parser.parse_args()

    results = scrape_all(args.output_dir, limit_per_domain=args.limit_per_domain)
    for domain, count in results.items():
        print(f"{domain}: saved {count} documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
