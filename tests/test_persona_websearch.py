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
        if "testimony" in query or "contemporaries" in query or "critics" in query:
            return []
        import websearch

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


def test_tertiary_hosts_are_labelled(ws):
    """Wikipedia prose must not reach a prompt looking like an archive transcript."""
    assert ws.source_tier("https://en.wikipedia.org/wiki/Basil_II") == "tertiary"
    assert ws.source_tier("https://www.britannica.com/biography/Basil-II") == "tertiary"
    assert ws.source_tier("https://www.doaks.org/resources/x") == "unclassified"
    assert ws.source_tier("") == "unclassified"


def test_the_escalation_stops_as_soon_as_the_slots_fill(ws, monkeypatch):
    """Passes 2 and 3 cost money; with no language named, a filled slot ends the acquisition."""
    class Backend:
        name = "stub"
        def search(self, query, n):
            return [ws.SearchResult("https://example.invalid/a", "A", "s", "")]

    monkeypatch.setattr(ws, "fetch", lambda url, ledger, **kw: "some retrieved text")
    pages, passes = ws.acquire_escalating(
        "A Subject", Backend(), ws.Acquisition(), slots=("words",),
        max_passes=3, fetch_per_slot=1,
    )
    assert [p["pass"] for p in passes] == [1], "a filled slot must not trigger a paid retry"
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
            return [ws.SearchResult("https://en.wikipedia.org/wiki/X", "X", "s", "")]

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
