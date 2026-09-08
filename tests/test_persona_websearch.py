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
