"""Source acquisition for the script arm. No network: the backend and fetch are substituted.

What matters here is the discipline, not the HTTP. Search runs per coverage slot rather than on
the subject's name; robots.txt refusals are honoured and recorded rather than worked around; and
slots that yield nothing come back empty so the caller can record a gap instead of losing it.
"""

from __future__ import annotations

import sys

import pytest

from tests.conftest import REPO_ROOT

GENERALIZER = REPO_ROOT / "persona_generalizer"

pytestmark = pytest.mark.skipif(
    not (GENERALIZER / "websearch.py").exists(), reason="websearch not present"
)


@pytest.fixture(scope="module")
def ws():
    if str(GENERALIZER) not in sys.path:
        sys.path.insert(0, str(GENERALIZER))
    import websearch

    return websearch


class FakeBackend:
    """Returns one result per query, and nothing at all for the slot we want to see gap out."""

    name = "fake"

    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, query, count):
        self.queries.append(query)
        import websearch

        # Match the slot's real query set rather than guessing at substrings. The previous
        # version keyed on the word "contemporaries" and silently started returning results for
        # the testimony slot the moment a query using "contemporary" was added — a test that
        # breaks when the data it mirrors is edited is worse than no test.
        testimony = {q.format(s="A Subject") for q in websearch.COVERAGE_QUERIES["testimony"]}
        if query in testimony:
            return []
        return [websearch.SearchResult(f"https://example.org/{len(self.queries)}", "T", "S")]


def test_search_runs_per_coverage_slot_not_on_the_name(ws, monkeypatch):
    monkeypatch.setattr(ws, "fetch", lambda url, ledger, **kw: "page text")
    backend = FakeBackend()
    ledger = ws.Acquisition()
    ws.acquire("A Subject", backend, ledger, slots=("deeds", "words"))
    assert all("A Subject" in q for q in backend.queries)
    # The point of the design: queries are aimed at what the slot needs, not at the person.
    assert any("record" in q or "archive" in q for q in backend.queries)
    assert {row["slot"] for row in ledger.searches} == {"deeds", "words"}


def test_empty_slots_come_back_as_gaps(ws, monkeypatch):
    monkeypatch.setattr(ws, "fetch", lambda url, ledger, **kw: "page text")
    acquired = ws.acquire("A Subject", FakeBackend(), ws.Acquisition(), slots=("testimony", "deeds"))
    assert acquired["testimony"] == []
    assert acquired["deeds"], "a slot with results should return pages"


def test_a_dead_provider_does_not_kill_the_acquisition(ws, monkeypatch):
    class Broken:
        name = "broken"

        def search(self, query, count):
            raise RuntimeError("provider down")

    monkeypatch.setattr(ws, "fetch", lambda url, ledger, **kw: "page text")
    ledger = ws.Acquisition()
    acquired = ws.acquire("A Subject", Broken(), ledger, slots=("deeds",))
    assert acquired["deeds"] == []
    assert ledger.searches, "the attempt is still recorded"


def test_robots_refusal_is_honoured_and_recorded(ws, monkeypatch):
    monkeypatch.setattr(ws, "robots_allows", lambda url, **kw: (False, "disallowed by robots.txt"))
    ledger = ws.Acquisition()
    assert ws.fetch("https://example.org/a", ledger) is None
    assert ledger.declined == [
        {"url": "https://example.org/a", "reason": "disallowed by robots.txt",
         "access_date": ledger.access_date}
    ]
    assert ledger.fetched == []


def test_non_http_urls_are_refused(ws):
    allowed, reason = ws.robots_allows("file:///etc/passwd")
    assert allowed is False
    assert "http" in reason


def test_ledger_renders_refusals_as_well_as_retrievals(ws):
    ledger = ws.Acquisition()
    ledger.record_fetch("https://example.org/kept", "T", 120)
    ledger.record_declined("https://ctext.org/analects", "disallowed by robots.txt")
    ledger.record_search("deeds", "q", [])
    rendered = ws.render_sources("A Subject", ledger)
    assert "https://example.org/kept" in rendered
    assert "ctext.org" in rendered and "disallowed by robots.txt" in rendered
    assert "Licences are unestablished" in rendered


def test_ledger_says_so_when_nothing_was_retrieved(ws):
    assert "_nothing retrieved_" in ws.render_sources("A Subject", ws.Acquisition())


def test_markup_stripping_drops_scripts(ws):
    assert ws.strip_markup("<p>Hello <b>world</b></p><script>evil()</script>") == "Hello world"


def test_no_backend_configured_is_not_an_error(ws, monkeypatch, tmp_path):
    """No environment variable AND no key file. Both sources have to be neutralised.

    `repo_root` is pointed at an empty directory on purpose: a developer with a real
    brave_api_key.txt in the repo root would otherwise see this pass or fail depending on
    their own machine.
    """
    for variable in ("BRAVE_SEARCH_API_KEY", "SERPER_API_KEY", "TAVILY_API_KEY"):
        monkeypatch.delenv(variable, raising=False)
    assert ws.backend_from_env(repo_root=tmp_path) is None


def test_a_key_file_configures_a_backend(ws, monkeypatch, tmp_path):
    """The file half of the lookup: same convention as the gitignored Fireworks key."""
    for variable in ("BRAVE_SEARCH_API_KEY", "SERPER_API_KEY", "TAVILY_API_KEY"):
        monkeypatch.delenv(variable, raising=False)
    (tmp_path / "brave_api_key.txt").write_text("not-a-real-key\n", encoding="utf-8")
    backend = ws.backend_from_env(repo_root=tmp_path)
    assert backend is not None and backend.name == "brave"


def test_the_environment_beats_the_key_file(ws, monkeypatch, tmp_path):
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "from-env")
    (tmp_path / "brave_api_key.txt").write_text("from-file\n", encoding="utf-8")
    assert ws.load_search_api_key("BRAVE_SEARCH_API_KEY", tmp_path) == "from-env"


def test_an_empty_key_file_is_not_a_key(ws, monkeypatch, tmp_path):
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    (tmp_path / "brave_api_key.txt").write_text("   \n", encoding="utf-8")
    assert ws.load_search_api_key("BRAVE_SEARCH_API_KEY", tmp_path) is None


def test_gaps_are_written_into_the_prompt_text():
    """The evidence pass has to see which slots came back empty, or it will fill them from memory."""
    if str(GENERALIZER) not in sys.path:
        sys.path.insert(0, str(GENERALIZER))
    import draft_persona

    text = draft_persona.format_acquired({"deeds": [], "words": []})
    assert text.count("record it as a gap") == 2


# -------------------------------------------------------------------------------------------
# Two bugs found by running the escalating acquisition against a live backend rather than a
# stub. Both were silent: the pass log said "0 citations followed" and looked like a thin
# subject rather than a broken lookup.
# -------------------------------------------------------------------------------------------


def test_a_subject_given_as_a_search_phrase_still_resolves_an_article(ws, monkeypatch):
    """"Basil II Byzantine emperor" is not an article title, and the verbatim lookup 404s."""
    seen: list[str] = []

    def fake_fetch_html(url, ledger):
        seen.append(url)
        # Only the trimmed title exists, as on the real encyclopedia.
        return '<ol class="references">Holmes, Catherine, Basil II (2005)</ol>' \
            if url.endswith("/Basil_II") else None

    monkeypatch.setattr(ws, "fetch_html", fake_fetch_html)
    cites = ws.wikipedia_reference_index("Basil II Byzantine emperor", ws.Acquisition())
    assert cites, "trailing words should be dropped until an article resolves"
    assert seen[0].endswith("/Basil_II_Byzantine_emperor"), "the full string is tried first"


def test_article_title_fallback_is_bounded(ws, monkeypatch):
    """A wrong subject must not turn the lookup into a crawl."""
    attempts: list[str] = []

    def fake_fetch_html(url, ledger):
        attempts.append(url)
        return None

    monkeypatch.setattr(ws, "fetch_html", fake_fetch_html)
    ws.wikipedia_reference_index("one two three four five six", ws.Acquisition())
    assert len(attempts) <= 3


def test_sources_are_ranked_by_what_is_at_the_far_end(ws):
    """Four tiers, because a denylist can only say what is bad and never what is worth having."""
    assert ws.source_tier("https://zh.wikisource.org/wiki/x") == "primary"
    assert ws.source_tier("https://en.wikipedia.org/wiki/Basil_II") == "reference"
    assert ws.source_tier("https://kongming.net/encyclopedia/x") == "tertiary"
    assert ws.source_tier("https://www.amazon.com/s?k=x") == "marketplace"
    # An unrecognised host is unknown, not good. Treating it as good is what let a product
    # listing and a Wikidata entry satisfy a coverage slot.
    assert ws.source_tier("https://www.doaks.org/resources/x") == "unclassified"
    assert ws.source_tier("") == "unclassified"


def test_results_are_reordered_best_source_first(ws):
    ranked = ws.rank_results([
        ws.SearchResult("https://kongming.net/x", "t", "s"),
        ws.SearchResult("https://www.amazon.com/x", "t", "s"),
        ws.SearchResult("https://zh.wikisource.org/x", "t", "s"),
        ws.SearchResult("https://en.wikipedia.org/x", "t", "s"),
    ])
    assert [ws.source_tier(r.url) for r in ranked] == [
        "primary", "reference", "tertiary", "marketplace",
    ]


def test_a_marketplace_listing_is_never_fetched(ws):
    """A product page for a book is not the book, and it filled a slot on a live run."""
    ledger = ws.Acquisition()
    assert ws.fetch("https://www.amazon.com/Books-Someone/s?rh=x", ledger) is None
    assert ledger.declined and "marketplace" in ledger.declined[0]["reason"]


def test_the_escalation_stops_as_soon_as_the_slots_fill(ws, monkeypatch):
    """Passes 2 and 3 cost money; with no language named, a filled slot ends the acquisition."""
    class Backend:
        name = "stub"
        def search(self, query, n):
            return [ws.SearchResult("https://zh.wikisource.org/a", "A", "s", "")]

    monkeypatch.setattr(ws, "fetch", lambda url, ledger, **kw: "some retrieved text")
    pages, passes = ws.acquire_escalating(
        "A Subject", Backend(), ws.Acquisition(), slots=("words",),
        max_passes=3, fetch_per_slot=1,
    )
    assert [p["pass"] for p in passes] == [1], "a primary source must end the paid retries"
    assert ws.gate_verdict_for_gaps(pages, passes, max_passes=3)[0] == ""


def test_naming_a_source_language_always_runs_the_cross_language_pass(ws, monkeypatch):
    """An explicit instruction beats the host-quality heuristic, which cannot be made reliable.

    Gating pass 3 on thinness meant a subject whose primary text exists only in Chinese never got
    searched in Chinese, because English pages — a fan encyclopedia and two forums among them —
    had filled every slot and nothing classified them as weak. A caller who says where the
    sources survive has supplied better information than the denylist can infer.
    """
    class Backend:
        name = "stub"
        def search(self, query, n):
            return [ws.SearchResult("https://example.invalid/a", "A", "s", "")]

    monkeypatch.setattr(ws, "fetch", lambda url, ledger, **kw: "some retrieved text")
    monkeypatch.setattr(ws, "fetch_html", lambda url, ledger: None)
    _, passes = ws.acquire_escalating(
        "A Subject", Backend(), ws.Acquisition(), slots=("words",),
        max_passes=3, source_languages=("zh",), fetch_per_slot=1,
    )
    assert 3 in [p["pass"] for p in passes], "a named language must be searched in"


def test_all_three_passes_run_when_nothing_is_found(ws, monkeypatch):
    class Backend:
        name = "stub"
        def search(self, query, n):
            return [ws.SearchResult("https://example.invalid/a", "A", "s", "")]

    monkeypatch.setattr(ws, "fetch", lambda url, ledger, **kw: None)
    monkeypatch.setattr(ws, "fetch_html", lambda url, ledger: None)
    pages, passes = ws.acquire_escalating(
        "A Subject", Backend(), ws.Acquisition(), slots=("words",),
        max_passes=3, source_languages=("el",), fetch_per_slot=1,
    )
    assert [p["pass"] for p in passes] == [1, 2, 3]
    assert ws.gate_verdict_for_gaps(pages, passes, max_passes=3)[0] == "refuse_evidence"


def test_an_unexhausted_ladder_can_only_claim_an_acquisition_refusal(ws, monkeypatch):
    """Pass 3 is skipped when no source languages are given, so the ladder is not exhausted.

    Claiming `refuse_evidence` there would assert something about the subject on the strength of
    a search that never tried the languages its sources are in.
    """
    class Backend:
        name = "stub"
        def search(self, query, n):
            return [ws.SearchResult("https://example.invalid/a", "A", "s", "")]

    monkeypatch.setattr(ws, "fetch", lambda url, ledger, **kw: None)
    monkeypatch.setattr(ws, "fetch_html", lambda url, ledger: None)
    pages, passes = ws.acquire_escalating(
        "A Subject", Backend(), ws.Acquisition(), slots=("words",), max_passes=3, fetch_per_slot=1,
    )
    assert [p["pass"] for p in passes] == [1, 2]
    assert ws.gate_verdict_for_gaps(pages, passes, max_passes=3)[0] == "refuse_acquisition"


def test_a_slot_filled_only_with_summaries_still_counts_as_thin(ws, monkeypatch):
    """The bug this pins cost a real run: escalation skipped exactly where it was needed.

    On a live third-century subject, English encyclopedia pages filled every slot on pass 1, so
    `thin()` reported nothing thin, the cross-language pass never fired despite --source-languages
    being given, and the primary text — public domain, permitted, in the original language — was
    never sought. A slot is not done because a summary answered it.
    """
    calls = {"n": 0}

    class Backend:
        name = "stub"
        def search(self, query, n):
            calls["n"] += 1
            return [ws.SearchResult("https://kongming.net/encyclopedia/X", "X", "s", "")]

    # Every fetch succeeds, but only ever with a tertiary page.
    monkeypatch.setattr(ws, "fetch", lambda url, ledger, **kw: "a summary")
    monkeypatch.setattr(ws, "fetch_html", lambda url, ledger: None)
    pages, passes = ws.acquire_escalating(
        "A Subject", Backend(), ws.Acquisition(), slots=("words",),
        max_passes=3, fetch_per_slot=1,
    )
    assert [p["pass"] for p in passes] == [1, 2], "tertiary-only fill must not stop escalation"
    assert pages["words"], "the tertiary pages are still kept, just not counted as sufficient"


def test_a_strong_source_does_stop_the_escalation(ws, monkeypatch):
    """The counterpart: a real source satisfies the slot and no further passes are paid for."""
    class Backend:
        name = "stub"
        def search(self, query, n):
            return [ws.SearchResult("https://zh.wikisource.org/wiki/X", "X", "s", "")]

    monkeypatch.setattr(ws, "fetch", lambda url, ledger, **kw: "primary text")
    _, passes = ws.acquire_escalating(
        "A Subject", Backend(), ws.Acquisition(), slots=("words",),
        max_passes=3, fetch_per_slot=1,
    )
    assert [p["pass"] for p in passes] == [1]


def test_the_words_slot_can_reach_a_primary_text_host(ws):
    """A query set that never names a transcription site cannot find a public-domain edition."""
    queries = " ".join(ws.COVERAGE_QUERIES["words"]).lower()
    assert "wikisource" in queries or "original language" in queries


def test_primary_source_queries_come_first(ws):
    """`acquire` stops at fetch_per_slot, so a query placed last usually never runs.

    Adding the primary-text queries to the end of the words slot was a no-op for exactly this
    reason: a live run filled the slot from an encyclopedia on the first query and never reached
    them. Order in these tuples is priority, and the regression is silent — the acquisition looks
    successful, it just never sought the better source.
    """
    words = ws.COVERAGE_QUERIES["words"]
    assert "wikisource" in words[0] or "primary text" in words[0], (
        "the best-source query must lead, or the slot fills from a summary before it is tried"
    )
    finances = ws.COVERAGE_QUERIES["context.material_conditions"]
    assert "salary" not in finances[0], (
        "a salary query leads with a living namesake for any pre-modern subject"
    )


def test_the_best_source_in_a_slot_is_first(ws, monkeypatch):
    """Per-query ranking is not enough: pass 1 fills with summaries before the good source exists.

    On a live run the transcription of the primary text arrived ninth of eleven pages, which is
    the first thing a per-response passage budget discards. Ordering has to be applied across the
    whole slot, after every pass has contributed.
    """
    urls = iter([
        "https://kongming.net/x", "https://en.wikipedia.org/x",
        "https://zh.wikisource.org/x", "https://unknown.tld/x",
    ])

    class Backend:
        name = "stub"
        def search(self, query, n):
            try:
                return [ws.SearchResult(next(urls), "t", "s", "")]
            except StopIteration:
                return []

    monkeypatch.setattr(ws, "fetch", lambda url, ledger, **kw: "text")
    monkeypatch.setattr(ws, "fetch_html", lambda url, ledger: None)
    pages, _ = ws.acquire_escalating(
        "A Subject", Backend(), ws.Acquisition(), slots=("words",),
        max_passes=3, source_languages=("zh",), fetch_per_slot=4,
    )
    tiers = [ws.source_tier(r.url) for r, _ in pages["words"]]
    assert tiers == sorted(tiers, key=lambda x: ws.TIER_RANK[x]), tiers
    if "primary" in tiers:
        assert tiers[0] == "primary", "the transcription must lead, not trail the summaries"


def test_markup_stripping_preserves_paragraph_boundaries(ws):
    """Collapsing all whitespace flattened every page into one line, which broke everything after.

    Condensation had no units to drop and relevance selection fell back to slicing at fixed
    character offsets — which is why, when first measured, selecting scored exactly the same as
    truncating. Structure has to survive the strip.
    """
    out = ws.strip_markup("<p>First para</p><p>Second para</p><div>Third</div>")
    assert out.count("\n\n") >= 2, out
    # The original contract still holds for a single block.
    assert ws.strip_markup("<p>Hello <b>world</b></p><script>evil()</script>") == "Hello world"


def test_selection_beats_truncation_on_signal_density(ws):
    """What extraction is for: keeping acts and utterances rather than navigation chrome.

    Topic presence is the wrong measure — no 1,200-word window of a 19,000-word article holds
    every topic. The thing that matters is how much of the budget carries speech, documents and
    dates rather than menus and lead-section boilerplate.
    """
    chrome = "Jump to content From Wikipedia the free encyclopedia See also References \n\n"
    body = (
        "In 208 he refused, and the reason he gave was recorded by the chronicle. "
        "He wrote to his commander and declared that he would not abandon them.\n\n"
    )
    text = chrome * 40 + body * 40
    budget = 220
    truncated = " ".join(text.split()[:budget])
    selected = ws.extract_relevant(text, "he", budget)
    assert len(ws._SIGNAL.findall(selected)) > len(ws._SIGNAL.findall(truncated))


def test_selection_keeps_source_order(ws):
    """Chronology must survive: a drafter reading selected text reads it in the source's order."""
    paras = [f"In 1{i:03d} he declared something recorded by the chronicle.\n\n" for i in range(20)]
    out = ws.extract_relevant("".join(paras), "he", 60)
    years = [int(y) for y in __import__("re").findall(r"\b1(\d{3})\b", out)]
    assert years == sorted(years), years


def test_reacquisition_turns_an_audit_finding_into_a_search(ws, monkeypatch):
    """The audit names the document worth having; no query written in advance could have.

    A passage citing a chronicle nobody fetched IS the search term. Acquisition otherwise happens
    once, before anything is drafted, so the most informative moment in the run — discovering
    which source the draft actually needed — was previously thrown away.
    """
    queries: list[str] = []

    class Backend:
        name = "stub"
        def search(self, query, n):
            queries.append(query)
            return [ws.SearchResult("https://zh.wikisource.org/wiki/x", "t", "s", "")]

    monkeypatch.setattr(ws, "fetch", lambda url, ledger, **kw: "the chronicle text")
    got = ws.reacquire_for_gaps(
        "Liu Bei", Backend(), ws.Acquisition(), ["Sanguozhi Xianzhu zhuan"]
    )
    assert got and got[0][1] == "the chronicle text"
    # The subject is appended: a bare title returns editions for sale.
    assert any("Liu Bei" in q and "Sanguozhi" in q for q in queries), queries


def test_reacquisition_is_bounded_and_deduplicated(ws, monkeypatch):
    """A long findings list must not turn into an unbounded crawl."""
    class Backend:
        name = "stub"
        def search(self, query, n):
            return [ws.SearchResult("https://example.org/same", "t", "s", "")]

    monkeypatch.setattr(ws, "fetch", lambda url, ledger, **kw: "text")
    got = ws.reacquire_for_gaps(
        "S", Backend(), ws.Acquisition(), [f"work {i}" for i in range(30)]
    )
    assert len(got) <= 8, "at most eight needs are chased"
    assert len({r.url for r, _ in got}) == len(got), "the same page is not fetched twice"


def test_reacquisition_ignores_empty_needs(ws):
    class Backend:
        name = "stub"
        def search(self, query, n):
            raise AssertionError("should not search for an empty need")

    assert ws.reacquire_for_gaps("S", Backend(), ws.Acquisition(), ["", "   ", None]) == []


def test_the_reacquisition_bound_is_high_enough_for_a_large_apparatus(ws, monkeypatch):
    """A subject with a big scholarly literature legitimately names many works.

    One audit named 25 and the code chased 8 — the log said one number and the behaviour was
    another, and each dropped need became a passage downgraded for want of a source nobody went
    and fetched.
    """
    seen: list[str] = []

    class Backend:
        name = "stub"
        def search(self, query, n):
            seen.append(query)
            return []

    ws.reacquire_for_gaps("S", Backend(), ws.Acquisition(), [f"work {i}" for i in range(25)])
    assert len(seen) == 24, f"chased {len(seen)} of 25"
