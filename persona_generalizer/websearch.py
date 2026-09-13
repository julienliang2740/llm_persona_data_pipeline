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
# A NOTE ON WHAT THESE ASSUME. The first version of this table was written for modern subjects
# and asked about salaries, voting records and court papers. Run against a third-century warlord
# it retrieved a fashion model's salary page, a review of a twentieth-century dissident with a
# similar name, a Nature paper, two university library guides and a Steam forum thread — and
# because any fill counted as a filled slot, that noise satisfied the coverage matrix. Each slot
# therefore carries a pre-modern alternative alongside the modern phrasing: the query that finds
# a wage book for a Victorian clerk cannot find the landholding of an ancient general, and asking
# both costs one extra search.
COVERAGE_QUERIES: dict[str, tuple[str, ...]] = {
    "context.material_conditions": (
        # The salary query leads to a living namesake for any pre-modern subject — it twice
        # retrieved a fashion model's pay pages for a third-century warlord — so the historical
        # phrasing goes first and the modern one only runs if that comes up short.
        "{s} landholding household economy how he was supported historians",
        "{s} personal finances biography archival",
        "{s} salary income wealth debts finances",
    ),
    "context.standing_and_constraint": (
        "{s} social class background upbringing status",
        "{s} legal position constraints on office",
    ),
    "context.institutions": (
        "{s} institution served membership records",
        "{s} organisation colleagues who he answered to",
        "{s} office rank title under whose authority he held it",
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
    # ORDER IS PRIORITY, NOT PREFERENCE. `acquire` stops querying a slot the moment it has
    # fetch_per_slot pages, so a query placed fourth usually never runs at all. Adding the
    # primary-text queries at the end of this tuple was therefore a no-op: a live run filled the
    # slot from an encyclopedia on query one and never reached them, and the public-domain text
    # sat on Wikisource untouched. Best source first, always.
    "words": (
        "{s} wikisource full text original edition",
        "{s} primary text original language translated edition public domain",
        "{s} letters papers writings primary source archive",
        "{s} speeches transcripts recorded remarks",
    ),
    "deeds": (
        "{s} campaigns appointments recorded acts chronicle annals",
        "{s} documented decisions record of actions archive",
        "{s} voting record court records official papers",
    ),
    "testimony": (
        "{s} contemporaries described him memoir account",
        "{s} critics opponents said about him",
        "{s} historian's appraisal contemporary chronicle assessment of him",
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
# Set once per acquisition so `fetch` can score pages against the subject without threading it
# through every call site. Module-level because the alternative is changing a signature used in
# six places and in the tests, for a value that is constant for the life of one run.
_FETCH_SUBJECT: dict[str, str] = {}


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


# Terms that mark a paragraph as carrying the kind of thing a persona is built from. Cheap and
# deterministic on purpose: this runs on every page of every acquisition, and a model call per
# page would cost more than the drafting does.
_SIGNAL = re.compile(
    r"\b(said|wrote|replied|declared|refused|ordered|recorded|reports?|according to|"
    r"letter|memorial|edict|decree|chronicle|annals|manuscript|archive)\b"
    r"|[「『\"“”]"                      # any quotation marker, including CJK
    r"|\b1?[0-9]{3}\b"                 # a year
    r"|曰|云|詔|表|書|記|傳",            # classical Chinese speech and document markers
    re.IGNORECASE,
)


def extract_relevant(text: str, subject: str, max_words: int, *, slot: str = "") -> str:
    """Keep the parts of a page that bear on the subject, instead of its first N words.

    Truncation takes whatever the page put at the top, which is navigation, a lead section and a
    disambiguation note. A long biography's substance is in the middle, and a transcription's
    substance is everywhere. Paragraphs are scored on mentions of the subject, on markers of
    speech and documents, and on dates, then the best are kept IN THEIR ORIGINAL ORDER so the
    chronology a drafter reads is still the source's.

    Deterministic and free. It is not summarisation — nothing is rewritten, only selected — so a
    quotation that survives selection survives verbatim, which is what the words criterion needs.
    """
    words = text.split()
    if len(words) <= max_words:
        return text
    tokens = [w for w in re.split(r"[^\w]+", subject.lower()) if len(w) > 2]
    paragraphs = [p for p in re.split(r"\n\s*\n|(?<=[.。!?！？])\s{2,}", text) if p.strip()]
    if len(paragraphs) < 3:
        paragraphs = [text[i : i + 1200] for i in range(0, len(text), 1200)]

    slot_tokens = [w for w in re.split(r"[^\w]+", slot.lower()) if len(w) > 3]
    scored = []
    for index, para in enumerate(paragraphs):
        lowered = para.lower()
        score = 2 * sum(lowered.count(tok) for tok in tokens)
        score += sum(lowered.count(tok) for tok in slot_tokens)
        score += 2 * len(_SIGNAL.findall(para))
        # Per-word, so a long paragraph does not win on length alone.
        scored.append((score / max(1, len(para.split()) ** 0.5), index, para))

    kept: list[tuple[int, str]] = []
    budget = max_words
    for _, index, para in sorted(scored, key=lambda s: -s[0]):
        length = len(para.split())
        if length > budget:
            continue
        kept.append((index, para))
        budget -= length
        if budget <= 0:
            break
    if not kept:
        return " ".join(words[:max_words])
    return "\n\n".join(para for _, para in sorted(kept))


def fetch(url: str, ledger: Acquisition, max_words: int = 4000) -> str | None:
    """Retrieve one page as text, honouring robots.txt and recording the outcome."""
    # A product listing for a book is not the book. These were being fetched, counted as
    # sources, and in one run filled a slot that then blocked a cross-language search.
    if source_tier(url) == "marketplace":
        ledger.record_declined(url, "commercial marketplace listing, not a source")
        return None
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
    # Select rather than truncate. `subject` is not threaded down here, so selection falls back
    # to signal markers alone, which still beats taking whatever sat at the top of the page.
    return extract_relevant(text, _FETCH_SUBJECT.get("name", ""), max_words)


def strip_markup(html: str) -> str:
    """Crude tag stripping that PRESERVES paragraph boundaries. Enough to feed a model.

    It used to finish with a single collapse of all whitespace, which flattened every page into
    one unbroken line. Nothing downstream could then tell a heading from a sentence: condensation
    had no units to drop, and relevance selection fell back to slicing at fixed character offsets,
    which is why selecting scored no better than truncating. Block boundaries become blank lines
    here, once, so everything after this point has structure to work with.
    """
    html = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", html)
    # Block boundaries FIRST. Stripping every tag before this ran was the bug: the closes were
    # already gone by the time they were looked for, so no paragraph break was ever produced and
    # the "preserves boundaries" rewrite silently did nothing.
    html = re.sub(r"(?is)<br\s*/?>", "\n", html)
    html = re.sub(r"(?is)</(p|div|li|tr|h[1-6]|section|article|blockquote)>", "\n\n", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    html = (
        html.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&#39;", "'")
        .replace("&quot;", '"')
    )
    html = re.sub(r"[ \t\xa0]+", " ", html)
    html = re.sub(r" *\n *", "\n", html)
    return re.sub(r"\n{3,}", "\n\n", html).strip()


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
            # Best tier first: the engine ranks by relevance, which is not the same as ranking
            # by whether the thing at the far end is a transcription or a listicle.
            for result in rank_results(results):
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
# SOURCE TIERS. The first version of this was a denylist of summary sites, which cannot work:
# anything absent counted as a good source, so a live run treated an Amazon listing, a Wikidata
# entry and a fan encyclopedia as strong material. A denylist can only ever say what is bad. What
# the acquisition actually needs to know is what is GOOD, so it can prefer it — hence four named
# tiers, best first, with everything unrecognised falling through to "unclassified" rather than
# being flattered.

# Commercial listings. Never fetched at all: a product page for a book is not the book, and it
# carries no information about the subject beyond the title it is selling.
MARKETPLACE_HOSTS = (
    "amazon.", "ebay.", "alibaba.", "aliexpress.", "etsy.", "walmart.", "target.com",
    "bookdepository.", "abebooks.", "barnesandnoble.", "thriftbooks.", "taobao.", "jd.com",
)

# Transcriptions and scans of the sources themselves. This is what the acquisition is for.
PRIMARY_HOSTS = (
    "wikisource.org", "gutenberg.org", "archive.org", "hathitrust.org", "perseus.tufts.edu",
    "loc.gov", "govinfo.gov", "sacred-texts.com", "dmgh.de", "documentarchiv.de",
)

# Curated reference works. Reliable for orientation and for finding the sources, but still
# summary prose: good enough to cite as background, never as the record.
REFERENCE_HOSTS = (
    "wikipedia.org", "britannica.com", "wikidata.org", "plato.stanford.edu",
    "oxfordreference.com", "encyclopedia.com", "newworldencyclopedia.org",
)

# Summary sites with no editorial guarantee. Usable as an index, never as a passage.
TERTIARY_HOSTS = (
    "wikiwand.com", "grokipedia.com", "worldhistory.org", "thecollector.com", "history.com",
    "biography.com", "kongming.net", "reddit.com", "quora.com", "travelchinaguide.com",
    "thefamouspeople.com", "kiddle.co", "baike.baidu.com", "alchetron.com", "steamcommunity.com",
)

TIER_RANK = {"primary": 0, "reference": 1, "unclassified": 2, "tertiary": 3, "marketplace": 4}


def source_tier(url: str) -> str:
    """Rank a URL by what kind of thing is at the other end of it.

    Ordered checks, most specific first. "unclassified" sits between reference and tertiary on
    purpose: an unrecognised host might be a university archive or might be a content farm, and
    the honest position is that we do not know — not that it is good, which was the old bug.
    """
    lowered = (url or "").lower()
    for hosts, tier in (
        (MARKETPLACE_HOSTS, "marketplace"),
        (PRIMARY_HOSTS, "primary"),
        (REFERENCE_HOSTS, "reference"),
        (TERTIARY_HOSTS, "tertiary"),
    ):
        if any(host in lowered for host in hosts):
            return tier
    return "unclassified"


def rank_results(results: "list[SearchResult]") -> "list[SearchResult]":
    """Best-tier results first, stable within a tier so the engine's own ranking survives."""
    return sorted(results, key=lambda r: TIER_RANK.get(source_tier(r.url), 2))


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


def native_name(subject: str, ledger: Acquisition, *, lang: str) -> str:
    """The subject's name in another language, via Wikipedia's interwiki links.

    This is the missing piece that made the cross-language pass decorative. Searching a Chinese
    archive with the string "Liu Bei" finds nothing: the text is filed under 劉備, and the pass had
    no way to learn that. So it ran, queried in English, retrieved English encyclopedia pages and
    reported success. Recovering the native title first is what makes searching in a language
    mean anything.

    Uses the ordinary article path, which Wikipedia's robots.txt permits, and reads only the
    interwiki href — not the article prose.
    """
    words = subject.strip().split()
    for drop in range(min(3, len(words))):
        candidate = "_".join(words[: len(words) - drop])
        if not candidate:
            break
        html = fetch_html(f"https://en.wikipedia.org/wiki/{candidate}", ledger)
        if not html:
            continue
        match = re.search(
            rf'href="https://{re.escape(lang)}\.wikipedia\.org/wiki/([^"#]+)"', html
        )
        if match:
            return urllib.parse.unquote(match.group(1)).replace("_", " ")
    return ""


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
    _FETCH_SUBJECT["name"] = subject
    merged: dict[str, list[tuple[SearchResult, str]]] = {slot: [] for slot in chosen}
    passes: list[dict[str, object]] = []

    def strong(slot: str) -> int:
        """Pages good enough to stop looking for: a transcription or a curated reference work.

        Deliberately excludes `unclassified`. An unrecognised host was previously counted as
        strong, which let an Amazon listing and a Wikidata page satisfy a slot; the honest
        reading of an unknown host is that it has not been shown to be worth stopping for.
        """
        return sum(
            1 for result, _ in merged[slot] if source_tier(result.url) in ("primary", "reference")
        )

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
        for lang in langs:
            native = native_name(subject, ledger, lang=lang)
            if native:
                LOGGER.info("  %s: subject is known as %r", lang, native)
        for slot in targets:
            for lang in langs:
                native = native_name(subject, ledger, lang=lang) or subject
                # The in-language queries run UNCONDITIONALLY. Gating them on `strong(slot)`
                # reintroduced the very bug this pass was unblocked to fix: the slot had been
                # filled by an Amazon listing and a Wikidata entry, which count as strong only
                # because no denylist names them, so the Chinese search was skipped again. If a
                # caller says the sources are in Chinese, search in Chinese — the whole point is
                # that this instruction outranks a host heuristic that cannot be made reliable.
                for query in (f"{native} 原文", f"{native} wikisource", native):
                    try:
                        results = backend.search(query, per_query)
                    except Exception as error:
                        LOGGER.warning("search failed for %r: %s", query, error)
                        continue
                    ledger.record_search(f"{slot}/{lang}", query, results)
                    added = 0
                    for result in results:
                        # Bounded by pages added in THIS language, so an in-language source is
                        # always given a chance to enter the slot even when it is already full.
                        if added >= fetch_per_slot:
                            break
                        text = fetch(result.url, ledger)
                        if text:
                            merged[slot].append(
                                (SearchResult(result.url, result.title, result.snippet, slot), text)
                            )
                            added += 1
                for cite in wikipedia_reference_index(native, ledger, lang=lang, limit=8):
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

    # Final ordering, across the whole slot rather than within one query's results. Ranking per
    # query is not enough: pass 1 collects tertiary pages before the cross-language pass has even
    # run, so the transcription arrives last and is the first thing a per-response passage budget
    # discards. Sorting here puts the best source in front of the model rather than behind the
    # summaries that happened to be found first.
    for slot in merged:
        merged[slot] = sorted(
            merged[slot], key=lambda pair: TIER_RANK.get(source_tier(pair[0].url), 2)
        )
    return merged, passes


def reacquire_for_gaps(
    subject: str,
    backend: SearchBackend,
    ledger: Acquisition,
    needs: Sequence[str],
    *,
    per_query: int = 5,
    fetch_per_need: int = 2,
) -> list[tuple[SearchResult, str]]:
    """Go and get the things a draft discovered it needed but did not have.

    Acquisition otherwise happens once, before anything is written, so a draft can only work with
    what a blind first guess collected. The most informative moment in a run is later than that:
    the audit saying "this passage cites a chronicle we never fetched" names the exact document
    worth having, which no query written in advance could have known to ask for. That finding is
    an acquisition target, and this turns it into one — the thing a human researcher does without
    thinking, and the last of the three capabilities the script arm was missing.

    `needs` are free-text: a named work, a claim that could not be supported. Each is searched
    with the subject appended, since a title alone tends to return editions for sale.
    """
    found: list[tuple[SearchResult, str]] = []
    seen: set[str] = set()
    for need in list(dict.fromkeys(n.strip() for n in needs if n and n.strip()))[:8]:
        query = f"{need} {subject}".strip()
        try:
            results = backend.search(query, per_query)
        except Exception as error:
            LOGGER.warning("search failed for %r: %s", query, error)
            continue
        ledger.record_search("reacquire", query, results)
        added = 0
        for result in rank_results(results):
            if added >= fetch_per_need or result.url in seen:
                continue
            seen.add(result.url)
            text = fetch(result.url, ledger)
            if text:
                found.append(
                    (SearchResult(result.url, result.title, result.snippet, "reacquire"), text)
                )
                added += 1
    return found


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
