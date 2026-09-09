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
import re
import urllib.robotparser
from pathlib import Path
from dataclasses import dataclass, field
from collections.abc import Sequence
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
        # Pre-modern and non-English subjects: the primary text is usually a public-domain
        # edition on a transcription site, and none of the queries above ever reach one. A live
        # run on a third-century subject retrieved four encyclopedia pages and a fan site while
        # the biography sat on Wikisource, permitted and untouched.
        "{s} wikisource full text original edition",
        "{s} primary text original language translated edition public domain",
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


# Where a provider's key lives when it is not in the environment. Same convention as the
# Fireworks key in pipeline/config.py: a gitignored file in the repo root, so a key survives a
# new shell without being pasted into a profile that syncs somewhere. `.gitignore` already
# covers these via its `*api_key*.txt` pattern.
KEY_FILES = {
    "BRAVE_SEARCH_API_KEY": "brave_api_key.txt",
    "SERPER_API_KEY": "serper_api_key.txt",
    "TAVILY_API_KEY": "tavily_api_key.txt",
}
REPO_ROOT = Path(__file__).resolve().parent.parent


def load_search_api_key(variable: str, repo_root: Path | None = None) -> str | None:
    """Environment first, then the gitignored key file. The key value is never logged."""
    value = os.environ.get(variable)
    if value and value.strip():
        return value.strip()
    filename = KEY_FILES.get(variable)
    if not filename:
        return None
    path = (repo_root or REPO_ROOT) / filename
    if not path.exists():
        return None
    key = path.read_text(encoding="utf-8").strip()
    return key or None


def backend_from_env(repo_root: Path | None = None) -> SearchBackend | None:
    """First configured provider wins. Returns None when none is set, which is not an error.

    Checks the environment and then the key file for each provider in turn, so a key file for
    Brave is not shadowed by an empty BRAVE_SEARCH_API_KEY in the environment. `repo_root` exists
    so a caller — a test, chiefly — can point the key-file half somewhere empty; clearing the
    environment alone no longer isolates this function.
    """
    for variable, factory in (
        ("BRAVE_SEARCH_API_KEY", BraveBackend),
        ("SERPER_API_KEY", SerperBackend),
        ("TAVILY_API_KEY", TavilyBackend),
    ):
        key = load_search_api_key(variable, repo_root)
        if key:
            LOGGER.info(
                "search backend: %s (%s)",
                factory.name,
                "environment" if os.environ.get(variable) else KEY_FILES[variable],
            )
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


# =================================================================================================
# Escalating acquisition
#
# A single acquisition pass conflates two very different outcomes: "this subject left nothing"
# and "this pass did not reach what the subject left". Only the second is a bug, and only the
# second is worth retrying. Everything below exists to tell them apart, and to make a retry
# escalate rather than repeat — three identical passes find the same nothing.
#
# Pass 1  slot-driven search, as `acquire` already does.
# Pass 2  reference harvesting: read what pass 1 found for the works it cites, then go looking
#         for those. This is how a researcher actually gets from a summary to the sources — you
#         find the standard edition and the standard monograph and chase their footnotes.
# Pass 3  cross-language, for subjects whose sources never existed in English.
#
# Wikipedia has one legitimate role here and it is NOT as a source of passages. Its prose is the
# popular version of the person — the thing the skill's phase 1 opens by warning against, and for
# a subject like Basil II it is largely the legend rather than the record. Its *reference list*,
# though, is a genuinely good index into tiers 3 and 4. So `wikipedia_reference_index` returns
# citations and never article text, and nothing here writes Wikipedia prose into a passage.
# =================================================================================================

# Enough of a citation to search for: a capitalised author-ish run, then a title, then a year.
_CITATION = re.compile(
    r"(?P<cite>[A-Z][A-Za-z'\-]+(?:,\s*[A-Z][A-Za-z.'\-]+)?[^.;]{5,140}?\(?(?P<year>1[5-9]\d{2}|20[0-2]\d)\)?)"
)
_REFERENCE_SECTION = re.compile(
    r"(?is)<(?:ol|div)[^>]*class=\"[^\"]*(?:references|reflist)[^\"]*\"[^>]*>(?P<body>.*?)</(?:ol|div)>"
)


# Hosts whose prose is tertiary under the skill's own tiering — "popular treatment, quarantined
# by default". They are not excluded from acquisition: they are a fine index and often the only
# thing a first pass returns. But their text must not reach a drafting prompt looking like a
# primary source, because the popular version of a person is exactly what phase 1 warns against,
# and for a subject whose fame is a later construction it is the legend rather than the record.
# NOTE ON THE SHAPE OF THIS LIST. It is a denylist, so anything absent counts as non-tertiary,
# and that is a real weakness rather than an oversight to be patched away: no enumeration will
# ever cover the open set of summary sites. A live run had reddit.com, quora.com and a fan
# encyclopedia treated as strong sources because they were not named here. The list is therefore
# used only to label material for the drafting prompt — never as the sole basis for deciding that
# acquisition may stop. Where a caller states which languages the sources survive in, that
# instruction governs instead.
TERTIARY_HOSTS = (
    "wikipedia.org", "wikiwand.com", "britannica.com", "grokipedia.com",
    "worldhistory.org", "thecollector.com", "history.com", "biography.com",
    # Observed on a live run, in descending order of how confidently they were mistaken for
    # sources: a fan encyclopedia, two forums, and a travel site.
    "kongming.net", "reddit.com", "quora.com", "travelchinaguide.com",
    "thefamouspeople.com", "kiddle.co", "baike.baidu.com",
)


def source_tier(url: str) -> str:
    """'tertiary' for hosts whose prose is a summary of the sources, else 'unclassified'.

    Deliberately coarse. It exists so the drafting prompt can see that a page is a summary rather
    than evidence; distinguishing tiers 1-4 from a URL is not possible and is not attempted.
    """
    lowered = (url or "").lower()
    return "tertiary" if any(host in lowered for host in TERTIARY_HOSTS) else "unclassified"


def fetch_html(url: str, ledger: Acquisition) -> str | None:
    """Retrieve raw HTML, honouring robots.txt. Needed where structure matters, not just text."""
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
    return response.text


def harvest_references(text: str, limit: int = 25) -> list[str]:
    """Pull citation-shaped strings out of a page, most specific first.

    Deliberately crude: the output is search queries for the next pass, not bibliography. A
    false positive costs one wasted search; a false negative costs a source.
    """
    seen: set[str] = set()
    out: list[str] = []
    for match in _CITATION.finditer(text):
        cite = re.sub(r"\s+", " ", match.group("cite")).strip(" ,;·—-")
        if len(cite) < 18 or cite.lower() in seen:
            continue
        seen.add(cite.lower())
        out.append(cite)
        if len(out) >= limit:
            break
    return out


def wikipedia_reference_index(
    subject: str, ledger: Acquisition, *, lang: str = "en", limit: int = 25
) -> list[str]:
    """Return the works an article CITES. Never returns article prose.

    Wikipedia's robots.txt disallows `/w/` and `/api/` for general agents, so this uses the
    ordinary `/wiki/<Title>` article path, which is allowed, and `robots_allows` checks it
    anyway. Only the reference/reflist block is read.
    """
    # A subject is often given as a search phrase rather than an article title — "Basil II
    # Byzantine emperor" rather than "Basil II" — and the verbatim title 404s, silently costing
    # the whole pass. Try the full string, then drop trailing words. Bounded at three attempts so
    # a wrong subject cannot turn into a crawl.
    words = subject.strip().split()
    html = None
    for drop in range(min(3, len(words))):
        candidate = "_".join(words[: len(words) - drop])
        if not candidate:
            break
        html = fetch_html(f"https://{lang}.wikipedia.org/wiki/{candidate}", ledger)
        if html:
            break
    if not html:
        return []
    blocks = [m.group("body") for m in _REFERENCE_SECTION.finditer(html)]
    if not blocks:
        return []
    return harvest_references(strip_markup(" ".join(blocks)), limit=limit)


def language_candidates(
    source_languages: Sequence[str] | None = None, *, include_english: bool = True
) -> list[str]:
    """Which language editions to try, English first.

    `source_languages` is the researcher's judgement about where this subject's sources actually
    survive — Greek, Arabic and Armenian for a Byzantine emperor, say. It is asked for rather
    than inferred on purpose. Ranking languages by article size, which is the obvious automatic
    proxy, measures how many modern editors a language has and not where the sources are; for a
    subject whose record is in Armenian it would confidently pick German.
    """
    ordered = ["en"] if include_english else []
    for code in source_languages or ():
        code = code.strip().lower()
        if code and code not in ordered:
            ordered.append(code)
    return ordered


def acquire_escalating(
    subject: str,
    backend: SearchBackend,
    ledger: Acquisition,
    *,
    slots: tuple[str, ...] | None = None,
    max_passes: int = 3,
    source_languages: Sequence[str] | None = None,
    per_query: int = 5,
    fetch_per_slot: int = 2,
) -> tuple[dict[str, list[tuple[SearchResult, str]]], list[dict[str, object]]]:
    """Acquire in up to `max_passes`, escalating strategy between them.

    Returns (slot -> pages, pass log). The pass log is what lets the gate say *which* refusal
    applies: a slot still empty after an escalated search is evidence about the subject; a slot
    empty after one pass is only evidence about the search.
    """
    chosen = tuple(slots or tuple(COVERAGE_QUERIES))
    merged: dict[str, list[tuple[SearchResult, str]]] = {slot: [] for slot in chosen}
    passes: list[dict[str, object]] = []

    def strong(slot: str) -> int:
        """Pages for a slot that are not tertiary summaries."""
        return sum(1 for result, _ in merged[slot] if source_tier(result.url) != "tertiary")

    def thin() -> tuple[str, ...]:
        """Slots that are empty, or filled only with tertiary summaries.

        Counting a slot as done because an encyclopedia answered it is how escalation gets
        skipped exactly where it is most needed. On a live run the cross-language pass never
        fired for a Chinese subject, because English tertiary pages had filled every slot on
        pass 1 — so `--source-languages zh` did nothing and the primary text was never sought.
        Quality of fill has to enter the test, or "thin" only ever means "empty".
        """
        return tuple(slot for slot in chosen if strong(slot) == 0)

    # ---- pass 1: slot-driven search --------------------------------------------------------
    first = acquire(
        subject, backend, ledger, slots=chosen, per_query=per_query, fetch_per_slot=fetch_per_slot
    )
    for slot, pages in first.items():
        merged.setdefault(slot, []).extend(pages)
    passes.append(
        {"pass": 1, "strategy": "slot_search", "slots_filled": len(chosen) - len(thin()),
         "slots_thin": list(thin())}
    )

    # ---- pass 2: chase what pass 1 cited ---------------------------------------------------
    if max_passes >= 2 and thin():
        citations: list[str] = []
        for pages in merged.values():
            for _result, text in pages:
                citations.extend(harvest_references(text, limit=8))
        citations.extend(wikipedia_reference_index(subject, ledger))
        # Deduplicate while keeping order; the earliest-seen citation is usually the most cited.
        seen: set[str] = set()
        queries = [c for c in citations if not (c.lower() in seen or seen.add(c.lower()))][:12]
        for slot in thin():
            for cite in queries:
                if strong(slot) >= fetch_per_slot:
                    break
                query = f"{cite} {subject}"
                try:
                    results = backend.search(query, per_query)
                except Exception as error:
                    LOGGER.warning("search failed for %r: %s", query, error)
                    continue
                ledger.record_search(f"{slot}/refs", query, results)
                for result in results:
                    if strong(slot) >= fetch_per_slot:
                        break
                    text = fetch(result.url, ledger)
                    if text:
                        merged[slot].append(
                            (SearchResult(result.url, result.title, result.snippet, slot), text)
                        )
        passes.append(
            {"pass": 2, "strategy": "reference_harvest", "citations_followed": len(queries),
             "slots_filled": len(chosen) - len(thin()), "slots_thin": list(thin())}
        )

    # ---- pass 3: cross-language ------------------------------------------------------------
    # Runs whenever source languages were named, NOT only when English slots came back empty.
    # Gating it on thinness was wrong twice over: `thin()` depends on classifying host quality,
    # and the classifier is a denylist that cannot know a fan wiki from an archive — on a live
    # run it counted reddit.com, quora.com and a fan encyclopedia "strong", reported nothing thin,
    # and skipped the pass for a subject whose primary text exists only in Chinese. A researcher
    # who states where the sources survive has given better information than any heuristic here
    # can infer, so that instruction is obeyed rather than second-guessed.
    if max_passes >= 3 and source_languages:
        langs = [code for code in language_candidates(source_languages) if code != "en"]
        # Thin slots first, then the two where an original-language primary text would land even
        # if an English summary has already answered them.
        targets = list(dict.fromkeys(list(thin()) + [s for s in ("words", "deeds") if s in chosen]))
        for slot in targets:
            for lang in langs:
                if strong(slot) >= fetch_per_slot:
                    break
                for cite in wikipedia_reference_index(subject, ledger, lang=lang, limit=8):
                    if strong(slot) >= fetch_per_slot:
                        break
                    try:
                        results = backend.search(cite, per_query)
                    except Exception as error:
                        LOGGER.warning("search failed for %r: %s", cite, error)
                        continue
                    ledger.record_search(f"{slot}/{lang}", cite, results)
                    for result in results:
                        if strong(slot) >= fetch_per_slot:
                            break
                        text = fetch(result.url, ledger)
                        if text:
                            merged[slot].append(
                                (SearchResult(result.url, result.title, result.snippet, slot), text)
                            )
        passes.append(
            {"pass": 3, "strategy": "cross_language", "languages": langs,
             "slots_filled": len(chosen) - len(thin()), "slots_thin": list(thin())}
        )

    return merged, passes


def gate_verdict_for_gaps(
    pages: dict[str, list[tuple[SearchResult, str]]],
    passes: list[dict[str, object]],
    *,
    max_passes: int = 3,
) -> tuple[str, str]:
    """Suggest which refusal a thin acquisition warrants. Advisory: the gate is a human's call.

    The distinction this exists to draw: escalation exhausted and still empty points at the
    sources; escalation not exhausted points at the search. It cannot see whether what WAS found
    contains decisions-with-reasoning, which is the binding criterion, so it never returns an
    admit verdict.
    """
    thin = sorted(slot for slot, found in pages.items() if not found)
    if not thin:
        return "", "every coverage slot returned material; run the gate on what it says."
    escalated = len(passes) >= max_passes
    if not escalated:
        return (
            "refuse_acquisition",
            f"{len(thin)} slot(s) empty after {len(passes)} pass(es) of a possible {max_passes}: "
            f"{', '.join(thin)}. Escalate before concluding anything about the subject.",
        )
    return (
        "refuse_evidence",
        f"{len(thin)} slot(s) still empty after {len(passes)} escalated pass(es): "
        f"{', '.join(thin)}. Record what was tried in sufficiency.acquisition_attempts.",
    )
