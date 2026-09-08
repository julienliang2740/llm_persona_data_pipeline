"""Source acquisition for the script arm of the drafter.

The script arm was deliberately built without web access, so that it could be compared against
the skill arm, which has it. This module adds a third configuration: script **plus** search. That
isolates the interesting question — whether the skill's advantage comes from the tooling or from
the agent doing the reasoning — instead of leaving it to argument.

It is off by default. `draft_persona.py --search` turns it on and needs one of:

    BRAVE_SEARCH_API_KEY   https://brave.com/search/api/
    SERPER_API_KEY         https://serper.dev/
    TAVILY_API_KEY         https://tavily.com/

Two disciplines from `targets/confucian/SOURCES.md` are enforced here rather than left to the
caller, because they are the difference between a ledger and a pile of links:

* **robots.txt is checked before every fetch and refusals are honoured.** ctext.org disallows AI
  crawlers, so that target took nothing from it and recorded the refusal; this module does the
  same automatically and records what it declined.
* **Everything is recorded** — every query, every URL, every access date, every refusal — so the
  `SOURCES.md` a run produces is reproducible rather than reconstructed afterwards.
"""

from __future__ import annotations

import datetime as _dt
import logging
import os
import urllib.robotparser
from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import urlparse

import httpx

LOGGER = logging.getLogger("websearch")

USER_AGENT = "persona-generalizer/0.1 (research drafting; +https://example.invalid/contact)"
TIMEOUT = httpx.Timeout(20.0, connect=10.0)

# Searching a subject's name returns the popular version of them: heavy on quotation, light on
# conduct, dominated by whichever biography the web copied. Searching per coverage slot is what
# reaches the registers and returns where deeds and circumstances live. {s} is the subject.
COVERAGE_QUERIES: dict[str, tuple[str, ...]] = {
    "context.material_conditions": (
        "{s} salary income wealth debts finances",
        "{s} personal finances biography archival",
    ),
    "context.standing_and_constraint": (
        "{s} social class background upbringing status",
        "{s} legal position constraints on office",
    ),
    "context.institutions": (
        "{s} institution served membership records",
        "{s} organisation colleagues who he answered to",
    ),
    "context.what_was_ordinary_then": (
        "{s} era what was normal practice historians",
        "{s} period social conditions statistics",
    ),
    "context.what_was_possible_for_someone_like_her": (
        "{s} education schooling early training",
        "{s} travel languages what he could have known",
    ),
    "formation": (
        "{s} formative events early life turning point",
        "{s} biography chronology key events",
    ),
    "words": (
        "{s} letters papers writings primary source archive",
        "{s} speeches transcripts recorded remarks",
    ),
    "deeds": (
        "{s} documented decisions record of actions archive",
        "{s} voting record court records official papers",
    ),
    "testimony": (
        "{s} contemporaries described him memoir account",
        "{s} critics opponents said about him",
    ),
    "conflicts": (
        "{s} hypocrisy contradiction said versus did",
        "{s} broke his own stated principle historians",
    ),
}


@dataclass(frozen=True)
class SearchResult:
    url: str
    title: str
    snippet: str
    slot: str = ""


class SearchBackend(Protocol):
    name: str

    def search(self, query: str, count: int) -> list[SearchResult]: ...


class _HttpBackend:
    """Shared plumbing; subclasses supply the request and the response shape."""

    name = "http"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.client = httpx.Client(timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})

    def search(self, query: str, count: int) -> list[SearchResult]:  # pragma: no cover - network
        raise NotImplementedError


class BraveBackend(_HttpBackend):
    name = "brave"

    def search(self, query: str, count: int) -> list[SearchResult]:  # pragma: no cover - network
        response = self.client.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": count},
            headers={"X-Subscription-Token": self.api_key, "Accept": "application/json"},
        )
        response.raise_for_status()
        return [
            SearchResult(r.get("url", ""), r.get("title", ""), r.get("description", ""))
            for r in (response.json().get("web", {}).get("results") or [])
        ]


class SerperBackend(_HttpBackend):
    name = "serper"

    def search(self, query: str, count: int) -> list[SearchResult]:  # pragma: no cover - network
        response = self.client.post(
            "https://google.serper.dev/search",
            json={"q": query, "num": count},
            headers={"X-API-KEY": self.api_key},
        )
        response.raise_for_status()
        return [
            SearchResult(r.get("link", ""), r.get("title", ""), r.get("snippet", ""))
            for r in (response.json().get("organic") or [])
        ]


class TavilyBackend(_HttpBackend):
    name = "tavily"

    def search(self, query: str, count: int) -> list[SearchResult]:  # pragma: no cover - network
        response = self.client.post(
            "https://api.tavily.com/search",
            json={"api_key": self.api_key, "query": query, "max_results": count},
        )
        response.raise_for_status()
        return [
            SearchResult(r.get("url", ""), r.get("title", ""), r.get("content", ""))
            for r in (response.json().get("results") or [])
        ]


def backend_from_env() -> SearchBackend | None:
    """First configured provider wins. Returns None when none is set, which is not an error."""
    for variable, factory in (
        ("BRAVE_SEARCH_API_KEY", BraveBackend),
        ("SERPER_API_KEY", SerperBackend),
        ("TAVILY_API_KEY", TavilyBackend),
    ):
        key = os.environ.get(variable)
        if key:
            LOGGER.info("search backend: %s", factory.name)
            return factory(key)
    return None


@dataclass
class Acquisition:
    """The ledger. Everything that happened, in the order it happened."""

    searches: list[dict[str, object]] = field(default_factory=list)
    fetched: list[dict[str, str]] = field(default_factory=list)
    declined: list[dict[str, str]] = field(default_factory=list)

    @property
    def access_date(self) -> str:
        return _dt.date.today().isoformat()

    def record_search(self, slot: str, query: str, results: list[SearchResult]) -> None:
        self.searches.append({"slot": slot, "query": query, "results": len(results)})

    def record_fetch(self, url: str, title: str, words: int) -> None:
        self.fetched.append(
            {"url": url, "title": title, "words": str(words), "access_date": self.access_date}
        )

    def record_declined(self, url: str, reason: str) -> None:
        self.declined.append({"url": url, "reason": reason, "access_date": self.access_date})


_ROBOTS_CACHE: dict[str, urllib.robotparser.RobotFileParser | None] = {}


def robots_allows(url: str, user_agent: str = USER_AGENT) -> tuple[bool, str]:
    """Check robots.txt before retrieving. A refusal is honoured, not worked around.

    An unreachable robots.txt is treated as permission, which is the convention; a robots.txt
    that exists and disallows the path is final.
    """
    parts = urlparse(url)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        return False, "not an http(s) url"
    origin = f"{parts.scheme}://{parts.netloc}"
    if origin not in _ROBOTS_CACHE:
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(origin + "/robots.txt")
        try:
            with httpx.Client(timeout=TIMEOUT, headers={"User-Agent": user_agent}) as client:
                response = client.get(origin + "/robots.txt")
            if response.status_code >= 400:
                _ROBOTS_CACHE[origin] = None
            else:
                parser.parse(response.text.splitlines())
                _ROBOTS_CACHE[origin] = parser
        except httpx.HTTPError:
            _ROBOTS_CACHE[origin] = None
    parser = _ROBOTS_CACHE[origin]
    if parser is None:
        return True, "no robots.txt reachable"
    if parser.can_fetch(user_agent, url):
        return True, "allowed by robots.txt"
    return False, "disallowed by robots.txt"


def fetch(url: str, ledger: Acquisition, max_words: int = 4000) -> str | None:
    """Retrieve one page as text, honouring robots.txt and recording the outcome."""
    allowed, reason = robots_allows(url)
    if not allowed:
        LOGGER.info("declined %s (%s)", url, reason)
        ledger.record_declined(url, reason)
        return None
    try:
        with httpx.Client(
            timeout=TIMEOUT, headers={"User-Agent": USER_AGENT}, follow_redirects=True
        ) as client:
            response = client.get(url)
        response.raise_for_status()
    except httpx.HTTPError as error:
        ledger.record_declined(url, f"fetch failed: {type(error).__name__}")
        return None
    text = strip_markup(response.text)
    words = text.split()
    ledger.record_fetch(url, url, len(words))
    return " ".join(words[:max_words])


def strip_markup(html: str) -> str:
    """Crude tag stripping. Enough to feed a model; not a parser."""
    import re

    html = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    html = (
        html.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&#39;", "'")
        .replace("&quot;", '"')
    )
    return re.sub(r"\s+", " ", html).strip()


def acquire(
    subject: str,
    backend: SearchBackend,
    ledger: Acquisition,
    *,
    slots: tuple[str, ...] | None = None,
    per_query: int = 5,
    fetch_per_slot: int = 2,
) -> dict[str, list[tuple[SearchResult, str]]]:
    """Search per coverage slot and fetch the top allowed results for each.

    Returns slot -> [(result, page text)]. Slots that yield nothing are returned empty rather
    than omitted, so the caller can record them as gaps instead of losing them silently.
    """
    chosen = slots or tuple(COVERAGE_QUERIES)
    seen_urls: set[str] = set()
    out: dict[str, list[tuple[SearchResult, str]]] = {}

    for slot in chosen:
        collected: list[tuple[SearchResult, str]] = []
        for template in COVERAGE_QUERIES.get(slot, ()):
            query = template.format(s=subject)
            try:
                results = backend.search(query, per_query)
            except Exception as error:  # a dead provider must not kill the whole acquisition
                LOGGER.warning("search failed for %r: %s", query, error)
                results = []
            ledger.record_search(slot, query, results)
            for result in results:
                if len(collected) >= fetch_per_slot:
                    break
                if not result.url or result.url in seen_urls:
                    continue
                seen_urls.add(result.url)
                text = fetch(result.url, ledger)
                if text:
                    collected.append((SearchResult(result.url, result.title, result.snippet, slot), text))
            if len(collected) >= fetch_per_slot:
                break
        out[slot] = collected
        LOGGER.info("%s: %d page(s)", slot, len(collected))
    return out


def render_sources(subject: str, ledger: Acquisition) -> str:
    """The provenance ledger, built from what actually happened."""
    lines = [
        f"# SOURCES — {subject}",
        "",
        "Acquired by `draft_persona.py --search`. Every row below is a page that was actually",
        "retrieved, with the date it was retrieved on. **Licences are unestablished**: this arm",
        "records where material came from, it does not clear it for redistribution. Establish the",
        "licence of every grounding source before any export.",
        "",
        f"Access dates: **{ledger.access_date}**.",
        "",
        "## Retrieved",
        "",
        "| URL | words | access date |",
        "|---|---|---|",
    ]
    for row in ledger.fetched:
        lines.append(f"| {row['url']} | {row['words']} | {row['access_date']} |")
    if not ledger.fetched:
        lines.append("| _nothing retrieved_ | — | — |")

    lines += [
        "",
        "## Checked and deliberately NOT retrieved",
        "",
        "`robots.txt` was checked before every fetch and refusals were honoured, following the",
        "precedent in `targets/confucian/SOURCES.md`.",
        "",
    ]
    if ledger.declined:
        lines += ["| URL | reason | date |", "|---|---|---|"]
        lines += [
            f"| {row['url']} | {row['reason']} | {row['access_date']} |" for row in ledger.declined
        ]
    else:
        lines.append("Nothing was refused.")

    lines += ["", "## Queries run", "", "| slot | query | results |", "|---|---|---|"]
    lines += [
        f"| {row['slot']} | `{row['query']}` | {row['results']} |" for row in ledger.searches
    ]
    lines += [
        "",
        "## Reproducing the acquisition",
        "",
        "```bash",
        "export BRAVE_SEARCH_API_KEY=...   # or SERPER_API_KEY / TAVILY_API_KEY",
        f'python persona_generalizer/draft_persona.py --subject "{subject}" --id <slug> --search',
        "```",
        "",
        "Search results are not stable over time, so a re-run will not reproduce this ledger",
        "exactly. That is a property of web acquisition, and it is why the retrieved pages and",
        "their access dates are recorded here rather than only the queries.",
    ]
    return "\n".join(lines) + "\n"
