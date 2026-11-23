"""
Asynchronous web content fetcher for the research agent.

Fetches publicly accessible documentation pages with:
- Async HTTP via httpx
- Automatic redirect following
- Exponential backoff retries (tenacity)
- Configurable concurrency via semaphore
- robots.txt respect
- Content extraction via BeautifulSoup
- Structured fetch result records
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse, urljoin

import httpx
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from .sources import SourceRecord, FetchStatus, content_hash

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT = 8.0            # seconds per page fetch
ROBOTS_TIMEOUT = 3.0             # seconds for robots.txt
DEFAULT_CONCURRENCY = 5          # simultaneous requests
MAX_CONTENT_LENGTH = 500_000     # ~500KB max per page
MAX_EXCERPT_LENGTH = 2000        # chars in content_excerpt
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Elements to strip from extracted content
STRIP_TAGS = {
    "script", "style", "nav", "header", "footer", "aside",
    "iframe", "noscript", "svg", "form", "button",
}

# ---------------------------------------------------------------------------
# Robots.txt cache (simple in-memory, per-domain)
# ---------------------------------------------------------------------------

_robots_cache: dict[str, Optional[set[str]]] = {}


async def _check_robots_txt(
    client: httpx.AsyncClient, url: str
) -> bool:
    """
    Best-effort robots.txt check. Returns True if fetching is allowed.
    If robots.txt is unavailable or times out, we default to allowed.
    """
    parsed = urlparse(url)
    domain = f"{parsed.scheme}://{parsed.netloc}"

    if domain not in _robots_cache:
        try:
            resp = await client.get(
                f"{domain}/robots.txt", timeout=ROBOTS_TIMEOUT, follow_redirects=True
            )
            if resp.status_code == 200:
                disallowed: set[str] = set()
                in_star_agent = False
                for line in resp.text.splitlines():
                    line = line.strip()
                    if line.lower().startswith("user-agent:"):
                        agent = line.split(":", 1)[1].strip()
                        in_star_agent = agent == "*"
                    elif in_star_agent and line.lower().startswith("disallow:"):
                        path = line.split(":", 1)[1].strip()
                        if path:
                            disallowed.add(path)
                _robots_cache[domain] = disallowed
            else:
                _robots_cache[domain] = None
        except Exception:
            _robots_cache[domain] = None

    disallowed = _robots_cache.get(domain)
    if disallowed is None:
        return True

    path = parsed.path or "/"
    for d in disallowed:
        if path.startswith(d):
            return False
    return True


# ---------------------------------------------------------------------------
# Content extraction & validity checking
# ---------------------------------------------------------------------------


def check_content_validity(body: str, text: str) -> tuple[bool, Optional[str]]:
    """
    Detect whether an HTTP 200 response contains real documentation or is:
    - JavaScript placeholder / client-side rendering shell
    - Login / authentication wall
    - Cloudflare / bot verification challenge
    - Empty or near-empty response
    """
    cleaned = text.strip()
    if len(cleaned) < 40:
        return False, "Response text too short (likely empty JS shell)"

    lower = cleaned.lower()

    # JavaScript required / CSR shells
    js_patterns = [
        "you need to enable javascript",
        "javascript is required",
        "please enable javascript",
        "requires javascript",
        "browser does not support javascript",
        "enable javascript to run this app",
    ]
    if any(p in lower for p in js_patterns):
        return False, "Client-side rendering shell (requires JavaScript)"

    # Access denied / bot challenges
    challenge_patterns = [
        "checking your browser before accessing",
        "just a moment...",
        "verify you are human",
        "attention required! | cloudflare",
        "security check to access",
        "ray id:",
    ]
    if any(p in lower for p in challenge_patterns) and len(cleaned) < 500:
        return False, "Access denied or bot challenge detected"

    # Login walls
    login_patterns = [
        "sign in to continue",
        "log in to your account",
        "please sign in to",
        "login is required",
    ]
    if any(p in lower for p in login_patterns) and len(cleaned) < 300:
        return False, "Login wall detected"

    return True, None


def extract_text(html: str, max_length: int = MAX_EXCERPT_LENGTH) -> str:
    """
    Extract readable text content from HTML, stripping navigation,
    ads, scripts, and boilerplate. Preserves heading context.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted tags
    for tag in soup.find_all(STRIP_TAGS):
        tag.decompose()

    # Extract headings for document context
    headings = []
    for h in soup.find_all(["h1", "h2", "h3"]):
        htext = h.get_text(strip=True)
        if htext and 3 < len(htext) < 100 and htext not in headings:
            headings.append(htext)

    # Try to find main content area
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find(attrs={"role": "main"})
        or soup.find(id=re.compile(r"content|main", re.I))
        or soup.find(class_=re.compile(r"content|main|docs", re.I))
        or soup.body
        or soup
    )

    text = main.get_text(separator="\n", strip=True)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Prefix with headings context if available
    prefix = ""
    if headings:
        prefix = "Sections: " + " | ".join(headings[:5]) + "\n\n"

    combined = prefix + text
    return combined[:max_length]


def extract_title(html: str) -> str:
    """Extract page title from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    if title_tag:
        return title_tag.get_text(strip=True)[:200]
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)[:200]
    return ""


# ---------------------------------------------------------------------------
# Core fetcher
# ---------------------------------------------------------------------------


@dataclass
class FetchResult:
    """Result of fetching a single URL."""
    url: str
    final_url: str
    http_status: int
    title: str
    content_excerpt: str
    content_hash: str
    fetch_status: str
    fetched_at: str
    error_message: Optional[str] = None
    content_length: int = 0


class DocumentationFetcher:
    """
    Async documentation fetcher with concurrency control,
    retries, and robots.txt respect.
    """

    def __init__(
        self,
        concurrency: int = DEFAULT_CONCURRENCY,
        timeout: float = DEFAULT_TIMEOUT,
        respect_robots: bool = True,
    ):
        self.concurrency = concurrency
        self.timeout = timeout
        self.respect_robots = respect_robots
        self._semaphore = asyncio.Semaphore(concurrency)
        self._rate_delay = 1.0  # seconds between requests to same domain
        self._domain_last_request: dict[str, float] = {}

    async def _rate_limit(self, url: str) -> None:
        """Simple per-domain rate limiting."""
        domain = urlparse(url).netloc
        last = self._domain_last_request.get(domain, 0)
        elapsed = time.monotonic() - last
        if elapsed < self._rate_delay:
            await asyncio.sleep(self._rate_delay - elapsed)
        self._domain_last_request[domain] = time.monotonic()

    async def fetch_url(self, url: str) -> FetchResult:
        """
        Fetch a single URL with retries and error handling.
        Returns a FetchResult regardless of success or failure.
        """
        now = datetime.now(timezone.utc).isoformat()

        async with self._semaphore:
            try:
                await self._rate_limit(url)

                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    follow_redirects=True,
                    headers={"User-Agent": USER_AGENT},
                    limits=httpx.Limits(
                        max_connections=self.concurrency,
                        max_keepalive_connections=self.concurrency,
                    ),
                ) as client:
                    # Check robots.txt
                    if self.respect_robots:
                        allowed = await _check_robots_txt(client, url)
                        if not allowed:
                            logger.info(f"Blocked by robots.txt: {url}")
                            return FetchResult(
                                url=url,
                                final_url=url,
                                http_status=0,
                                title="",
                                content_excerpt="",
                                content_hash="",
                                fetch_status=FetchStatus.BLOCKED.value,
                                fetched_at=now,
                                error_message="Blocked by robots.txt",
                            )

                    resp = await self._fetch_with_retry(client, url)
                    final_url = str(resp.url)
                    status = resp.status_code
                    print(f"      HTTP {status} -> {url}", flush=True)

                    if status == 200:
                        body = resp.text[:MAX_CONTENT_LENGTH]
                        title = extract_title(body)
                        excerpt = extract_text(body)
                        chash = content_hash(excerpt)

                        # Validate content to avoid JS placeholders, bot challenges, or login walls
                        is_valid, validation_err = check_content_validity(body, excerpt)
                        if not is_valid:
                            status_val = (
                                FetchStatus.BLOCKED.value
                                if ("access denied" in (validation_err or "").lower() or "login" in (validation_err or "").lower())
                                else FetchStatus.FAILED.value
                            )
                            logger.info(f"Invalid content for {url}: {validation_err}")
                            return FetchResult(
                                url=url,
                                final_url=final_url,
                                http_status=status,
                                title=title,
                                content_excerpt="",
                                content_hash=chash,
                                fetch_status=status_val,
                                fetched_at=now,
                                error_message=validation_err,
                                content_length=len(body),
                            )

                        return FetchResult(
                            url=url,
                            final_url=final_url,
                            http_status=status,
                            title=title,
                            content_excerpt=excerpt,
                            content_hash=chash,
                            fetch_status=FetchStatus.SUCCESS.value,
                            fetched_at=now,
                            content_length=len(body),
                        )
                    elif status == 403:
                        return FetchResult(
                            url=url, final_url=final_url, http_status=status,
                            title="", content_excerpt="", content_hash="",
                            fetch_status=FetchStatus.BLOCKED.value,
                            fetched_at=now,
                            error_message=f"HTTP {status} Forbidden",
                        )
                    elif status == 429:
                        return FetchResult(
                            url=url, final_url=final_url, http_status=status,
                            title="", content_excerpt="", content_hash="",
                            fetch_status=FetchStatus.RATE_LIMITED.value,
                            fetched_at=now,
                            error_message=f"HTTP {status} Rate Limited",
                        )
                    else:
                        return FetchResult(
                            url=url, final_url=final_url, http_status=status,
                            title="", content_excerpt="", content_hash="",
                            fetch_status=FetchStatus.FAILED.value,
                            fetched_at=now,
                            error_message=f"HTTP {status}",
                        )

            except httpx.TimeoutException:
                return FetchResult(
                    url=url, final_url=url, http_status=0,
                    title="", content_excerpt="", content_hash="",
                    fetch_status=FetchStatus.FAILED.value,
                    fetched_at=now, error_message="Timeout",
                )
            except httpx.ConnectError as e:
                return FetchResult(
                    url=url, final_url=url, http_status=0,
                    title="", content_excerpt="", content_hash="",
                    fetch_status=FetchStatus.FAILED.value,
                    fetched_at=now, error_message=f"Connection error: {e}",
                )
            except Exception as e:
                logger.warning(f"Fetch error for {url}: {e}")
                return FetchResult(
                    url=url, final_url=url, http_status=0,
                    title="", content_excerpt="", content_hash="",
                    fetch_status=FetchStatus.FAILED.value,
                    fetched_at=now, error_message=str(e)[:300],
                )

    async def _fetch_with_retry(
        self, client: httpx.AsyncClient, url: str
    ) -> httpx.Response:
        """Fetch with max 1 retry for transient 429/503. Fail fast on connect/DNS errors."""
        for attempt in range(2):
            try:
                resp = await client.get(url)
                if resp.status_code in (429, 503) and attempt == 0:
                    logger.info(f"Got {resp.status_code} for {url}, retrying in 2s...")
                    await asyncio.sleep(2)
                    continue
                return resp
            except (httpx.TimeoutException, httpx.ConnectError):
                if attempt == 0:
                    await asyncio.sleep(1)
                    continue
                raise
        raise Exception("Exhausted retries")


    async def fetch_sources(
        self, records: list[SourceRecord]
    ) -> list[SourceRecord]:
        """
        Fetch all source records concurrently.
        Updates each record in-place with fetch results.
        Returns the updated records.
        """
        tasks = []
        for rec in records:
            if rec.fetch_status != FetchStatus.PENDING.value:
                continue  # Skip already-fetched
            if not rec.source_url:
                rec.fetch_status = FetchStatus.SKIPPED.value
                continue
            tasks.append((rec, self.fetch_url(rec.source_url)))

        # Gather all fetch results
        if tasks:
            results = await asyncio.gather(
                *(t[1] for t in tasks), return_exceptions=True
            )
            for (rec, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    rec.fetch_status = FetchStatus.FAILED.value
                    rec.error_message = str(result)[:300]
                else:
                    rec.final_url = result.final_url
                    rec.http_status = result.http_status
                    rec.source_title = result.title
                    rec.content_excerpt = result.content_excerpt
                    rec.content_hash = result.content_hash
                    rec.fetch_status = result.fetch_status
                    rec.retrieved_at = result.fetched_at
                    rec.error_message = result.error_message

        return records

