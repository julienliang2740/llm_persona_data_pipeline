"""The script arm of the drafter: its pure functions, with no network.

The four model passes are not exercised here — they need an API key and are the part that varies.
What is pinned is everything between the model's output and the files on disk: id assignment,
the stripping of invented citations, and the guarantee that what the drafter writes is something
the pipeline's own parser and checker will accept.
"""

from __future__ import annotations

import shutil
import sys

import pytest
import yaml

from pipeline.target import parse_key_passages
from tests.conftest import REPO_ROOT

GENERALIZER = REPO_ROOT / "persona_generalizer"

pytestmark = pytest.mark.skipif(
    not (GENERALIZER / "draft_persona.py").exists(), reason="drafter not present"
)


@pytest.fixture(scope="module")
def drafter():
    if str(GENERALIZER) not in sys.path:
        sys.path.insert(0, str(GENERALIZER))
    import draft_persona

    return draft_persona


@pytest.fixture
def evidence(drafter):
    return drafter.normalise_evidence(
        {
            "evidence": [
                {"kind": "circumstance", "title": "Wages", "body": "The post paid little.",
                 "bears_on": "why refusals cost her", "confidence": "medium", "verify": "wage books"},
                {"kind": "circumstance", "title": "Standing", "body": "Her office was provisional."},
                {"kind": "words", "title": "On the record", "body": "She wrote that records hold."},
                {"kind": "deed", "title": "Impoundment", "body": "She impounded a member's vessel."},
                {"kind": "deed", "title": "Delays", "body": "She slow-walked a rival's inspections."},
                {"kind": "testimony", "title": "A clerk", "body": "He recalled her refusals."},
                {"kind": "circumstance", "body": ""},  # dropped: no body
            ]
        }
    )


def test_ids_are_assigned_by_kind(drafter, evidence):
    """Passage ids have to be stable and prefixed, because spec sources cite them by string."""
    assert [(e["id"], e["kind"]) for e in evidence] == [
        ("C1", "circumstance"),
        ("C2", "circumstance"),
        ("W1", "words"),
        ("D1", "deed"),
        ("D2", "deed"),
        ("T1", "testimony"),
    ]


def test_items_without_a_body_are_dropped(drafter, evidence):
    assert all(e["body"] for e in evidence)


def test_rendered_passages_parse_with_the_pipelines_own_parser(drafter, evidence):
    """The drafter writes key_passages.md; the loader parses it. They must agree exactly."""
    text = drafter.render_key_passages("A Subject", evidence)
    parsed = parse_key_passages(text)
    assert {p.id for p in parsed} == {e["id"] for e in evidence}


def test_rendered_passages_carry_the_unverified_warning(drafter, evidence):
    text = drafter.render_key_passages("A Subject", evidence)
    assert "UNVERIFIED" in text
    assert "Confidence:" in text


def test_invented_citations_are_stripped_and_reported(drafter):
    """The composition pass cites from memory and sometimes invents an id, which would not load."""
    dropped: set[str] = set()
    cleaned = drafter.remap_sources(
        {"principles": [{"id": "P01", "sources": ["C1", "D9", "W1"]}]},
        {"C1", "W1"},
        dropped,
    )
    assert cleaned["principles"][0]["sources"] == ["C1", "W1"]
    assert dropped == {"D9"}


def test_conflicts_citing_missing_evidence_are_dropped(drafter, evidence):
    spec, _ = drafter.build_spec(
        "probe",
        "A Subject",
        {},
        {"verdict": "admit"},
        [
            {"id": "kept", "said": "W1", "did": "D1", "resolution": "conduct"},
            {"id": "dropped", "said": "W9", "did": "D1", "resolution": "conduct"},
        ],
        {e["id"] for e in evidence},
    )
    assert [c["id"] for c in spec["conflicts"]] == ["kept"]


def test_licence_and_redistribution_are_flagged_unknown(drafter, evidence):
    """The script consulted nothing, so it must not imply a licence it cannot know."""
    spec, _ = drafter.build_spec("probe", "A Subject", {}, {"verdict": "admit"}, [], set())
    assert "UNKNOWN" in spec["reference_material"][0]["license"]
    assert "UNVERIFIED" in spec["redistribution_note"]
    assert spec["attribution_policy"]["declare_in_manifest"] is True


def test_sources_ledger_records_that_nothing_was_consulted(drafter):
    ledger = drafter.render_sources("A Subject")
    assert "NO SOURCES WERE CONSULTED" in ledger
    assert "UNKNOWN" in ledger


def test_notes_treat_an_empty_conflicts_list_as_unexamined(drafter, evidence):
    notes = drafter.render_notes("A Subject", {"verdict": "admit"}, evidence, [], set())
    assert "unexamined rather than as settled" in notes


def test_notes_list_the_stripped_ids(drafter, evidence):
    notes = drafter.render_notes("A Subject", {"verdict": "admit"}, evidence, [], {"D9", "C7"})
    assert "`C7`" in notes and "`D9`" in notes


def test_a_complete_draft_passes_the_persona_checker(drafter, evidence, tmp_path, capsys):
    """End to end with the model replaced by a fixture: what the drafter writes must check clean.

    This is the contract `draft_prompts.py` has to satisfy. If the checker gains a rule, this
    fails here rather than after someone has spent an API budget discovering it.
    """
    sources = [e["id"] for e in evidence]
    block = lambda text: {"what": text, "psychological_effect": "It marked them.", "sources": sources}
    payload = {
        "name": "A Subject",
        "summary": "They judge by the record, and they are not always fair. " * 4,
        "subject": {
            "kind": "historical",
            "lived": "1834-1901",
            "canon_boundary": {"attributed": "Logbooks.", "disputed": "A sermon.", "excluded": "A novel."},
        },
        "context": {
            field: block("A condition of their life, stated at some length. " * 6)
            for field in (
                "period",
                "material_conditions",
                "standing_and_constraint",
                "institutions",
                "what_was_ordinary_then",
                "what_was_possible_for_someone_like_her",
            )
        },
        "formation": [
            {
                "phase": "Early (1834-1851)",
                "what_happened": "Something happened to them, at length. " * 8,
                "what_it_left_them_with": "It left them with a disposition. " * 8,
                "sources": sources,
            }
        ],
        "principles": [
            {
                "id": f"P{n:02d}",
                "name": f"Principle {n}",
                "description": "What it demands.",
                "positive_indicators": ["does the thing"],
                "failure_modes": ["does not"],
                "sources": sources,
            }
            for n in range(1, 9)
        ],
        "tradeoffs": [
            {"id": "a_vs_b", "description": "A conflict.", "intended_lean": "A wins.", "sources": sources}
        ],
        "voice": {"register": "Flat.", "never_says": ["I feel"], "do_not_imitate": "Period diction."},
        "epistemic_horizon": {"cannot_know": "Anything after 1901.", "policy": "translate_to_analogue"},
        "deliberation_shape": "Look at the record first.",
        "signature_moves": [{"id": "m1", "description": "Names the record."}],
        "divergence_hypotheses": [{"id": "h1", "description": "Differs.", "example_prompt_shape": "..."}],
        "domains": [{"id": "work", "weight": 1.0}],
        "cue_policy": {"forbidden_terms": ["A Subject"], "allowed_terms": ["record"]},
        "redistribution_note": "Draft.",
    }
    spec, _ = drafter.build_spec(
        "probe",
        "A Subject",
        payload,
        {
            "verdict": "admit",
            "first_person_volume": "some",
            "decisions_with_reasoning": "eight",
            "domain_breadth": "two",
            "contestedness": "low",
            "testimonial_variety": "two observers, differing interests",
            # Required on every admitted spec: scope is a separate axis from the criteria above,
            # and the checker blocks an admit that never asked the question.
            "scope_check": "in scope; deceased public office-holder, no atrocity content",
        },
        [
            {
                "id": "c1",
                "said": "W1",
                "did": "D1",
                "resolution": "conduct",
                "reconciliation_attempted": "Tested three readings; none held.",
                "consequence_for_the_persona": "The persona does the thing it disavowed.",
            }
        ],
        set(sources),
    )

    root = tmp_path / "probe"
    (root / "references").mkdir(parents=True)
    (root / "spec.yaml").write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
    (root / "references" / "key_passages.md").write_text(
        drafter.render_key_passages("A Subject", evidence), encoding="utf-8"
    )

    if str(GENERALIZER) not in sys.path:
        sys.path.insert(0, str(GENERALIZER))
    from check_persona import check_persona

    assert check_persona("probe", tmp_path) == 0, capsys.readouterr().err


# -------------------------------------------------------------------------------------------
# run_pass logs token usage. It read `response.completion_tokens`, which ModelResponse has
# never had — it carries the provider's raw `usage` dict. Every drafter run crashed on the
# first pass, AFTER the model call had been made and billed. A logging line must not be able
# to throw away work that has already been paid for.
# -------------------------------------------------------------------------------------------


class _Resp:
    def __init__(self, usage):
        self.usage = usage


class _Client:
    def __init__(self, usage):
        self._usage = usage

    async def complete_json(self, *args, **kwargs):
        return {"ok": True}, _Resp(self._usage)


def test_run_pass_logs_usage_without_crashing(caplog):
    import asyncio

    from draft_persona import run_pass

    usage = {
        "completion_tokens": 4046,
        "completion_tokens_details": {"reasoning_tokens": 2988},
    }
    with caplog.at_level("INFO"):
        payload = asyncio.run(run_pass(_Client(usage), "prompt", "sufficiency", 100))
    assert payload == {"ok": True}
    assert "4046" in caplog.text
    assert "2988" in caplog.text


@pytest.mark.parametrize("usage", [{}, {"completion_tokens": 12}, None])
def test_run_pass_survives_a_provider_that_reports_no_usage(usage, caplog):
    """The call is already paid for by this point; missing usage must not raise."""
    import asyncio

    from draft_persona import run_pass

    with caplog.at_level("INFO"):
        payload = asyncio.run(run_pass(_Client(usage), "prompt", "evidence", 100))
    assert payload == {"ok": True}


# -------------------------------------------------------------------------------------------
# Regressions from teaching the gate new verdicts.
# -------------------------------------------------------------------------------------------


def test_every_blocking_verdict_is_caught_by_the_drafter_guard():
    """The drafter halts on `verdict.startswith("refuse")`, so every refusal must start that way.

    The bug this pins: the gate learned refuse_evidence / refuse_acquisition / refuse_scope while
    the drafter still tested `== "refuse"`. None of the new verdicts matched, so a refusal would
    have been ignored and the spec built out anyway — the exact outcome the gate exists to stop.
    """
    import sys

    generalizer = REPO_ROOT / "persona_generalizer"
    if str(generalizer) not in sys.path:
        sys.path.insert(0, str(generalizer))
    from check_persona import BLOCKING_VERDICTS, VERDICTS

    assert all(v.startswith("refuse") for v in BLOCKING_VERDICTS)
    assert {v for v in VERDICTS if v.startswith("refuse")} == set(BLOCKING_VERDICTS)


def test_rendered_passages_declare_an_evidence_basis():
    """admit_reconstructed is unreachable unless the drafter writes the marker on every passage."""
    import sys

    generalizer = REPO_ROOT / "persona_generalizer"
    if str(generalizer) not in sys.path:
        sys.path.insert(0, str(generalizer))
    import draft_persona as drafter
    from pipeline.target import parse_key_passages

    markdown = drafter.render_key_passages(
        "A Subject",
        [
            {"id": "C1", "kind": "circumstance", "title": "a", "body": "b",
             "evidence_basis": "reconstructed"},
            {"id": "D1", "kind": "deed", "title": "c", "body": "d"},
            {"id": "W1", "kind": "words", "title": "e", "body": "f",
             "evidence_basis": "not-a-value"},
        ],
    )
    parsed = {p.id: p for p in parse_key_passages(markdown)}
    assert all(p.evidence_basis_declared for p in parsed.values())
    assert parsed["C1"].evidence_basis == "reconstructed"
    assert parsed["D1"].evidence_basis == "attested"
    # Under-marking is the serious error, so an unrecognised value fails safe.
    assert parsed["W1"].evidence_basis == "reconstructed"


def test_the_optional_draft_flags_are_passed_by_keyword():
    """Four optional flags of three types; positional order has already been got wrong once.

    Threading --no-condense in positionally put the tuple of source languages into the condense
    switch and the boolean into source_languages. Neither raises: the run just quietly does the
    wrong thing. Pinning the call shape is cheaper than finding that again in a paid run.
    """
    import inspect
    import sys

    generalizer = REPO_ROOT / "persona_generalizer"
    if str(generalizer) not in sys.path:
        sys.path.insert(0, str(generalizer))
    import draft_persona as drafter

    source = inspect.getsource(drafter.main)
    for flag in ("use_search=", "acquisition_passes=", "condense=", "source_languages="):
        assert flag in source, f"{flag} must be passed by keyword, not position"


def test_the_audit_section_reports_what_was_flagged():
    """The verification pass is only worth running if its findings reach a human."""
    import sys

    generalizer = REPO_ROOT / "persona_generalizer"
    if str(generalizer) not in sys.path:
        sys.path.insert(0, str(generalizer))
    import draft_persona as drafter

    notes = drafter.render_notes(
        "X", {"verdict": "admit"}, [], [], set(),
        ["- `C1` flagged laundered: names a work that was never fetched"],
    )
    assert "## Verification against the retrieved material" in notes
    assert "C1" in notes and "laundered" in notes


def test_an_empty_audit_is_not_reported_as_a_clean_bill():
    """An audit that finds nothing looks identical to an audit that did not try."""
    import sys

    generalizer = REPO_ROOT / "persona_generalizer"
    if str(generalizer) not in sys.path:
        sys.path.insert(0, str(generalizer))
    import draft_persona as drafter

    notes = drafter.render_notes("X", {"verdict": "admit"}, [], [], set(), [])
    assert "flagged nothing" in notes
    assert "spot-check" in notes, "an empty result must tell the reviewer to check by hand"


def test_verification_downgrades_rather_than_deletes():
    """A flagged claim may still be true; the repair is to stop calling it attested."""
    import sys

    generalizer = REPO_ROOT / "persona_generalizer"
    if str(generalizer) not in sys.path:
        sys.path.insert(0, str(generalizer))
    import draft_persona as drafter

    evidence = [
        {"id": "C1", "evidence_basis": "attested"},
        {"id": "D2", "evidence_basis": "attested"},
        {"id": "W3", "evidence_basis": "reconstructed"},
    ]
    notes = drafter.apply_verification(
        evidence,
        {
            "unsupported": [{"id": "C1", "why": "not in the material"}],
            "laundered": [{"id": "D2", "work_named": "a chronicle", "why": "never fetched"}],
            "overstated": [{"id": "W3", "why": "hedge dropped"}],
        },
    )
    by_id = {e["id"]: e for e in evidence}
    assert by_id["C1"]["evidence_basis"] == "reconstructed"
    assert by_id["D2"]["evidence_basis"] == "mixed"
    # Already inferred: a downgrade must not silently promote it back up.
    assert by_id["W3"]["evidence_basis"] == "reconstructed"
    assert len(notes) == 3 and len(evidence) == 3, "findings downgrade, they do not delete"


def _pages(ws, urls_and_text):
    return [(ws.SearchResult(u, "t", "s", ""), txt) for u, txt in urls_and_text]


def test_a_slot_holding_a_primary_source_is_not_condensed():
    """A transcription must pass through whole. On a live run this slot went 16,476 -> 32 words.

    The guideline said to preserve a primary text and the model discarded it anyway, destroying
    the one slot that mattered most. An instruction is not a control.
    """
    import asyncio, sys

    generalizer = REPO_ROOT / "persona_generalizer"
    if str(generalizer) not in sys.path:
        sys.path.insert(0, str(generalizer))
    import draft_persona as drafter
    import websearch as ws

    class Client:
        async def complete_json(self, *a, **k):
            raise AssertionError("a primary source must not be sent for condensation")

    pages = _pages(ws, [("https://zh.wikisource.org/wiki/x", "the chronicle " * 500)])
    out = asyncio.run(drafter.condense_acquired(Client(), {"words": pages}, 4000))
    assert out["words"] == pages


def test_an_over_aggressive_condensation_is_rejected():
    """Thresholds calibrated on a real run, where the ratios came out bimodal.

    Legitimate condensations landed between 11.9% and 28.9%; the broken ones at 0.1%, 0.2% and
    4.7%, which destroyed the deeds and words slots. A first guess of 20% would have thrown away
    five of the seven good ones, so the cutoff sits in the empty band at 8%, with an absolute
    floor because 26 words is useless whatever ratio produced it.
    """
    import asyncio, sys

    generalizer = REPO_ROOT / "persona_generalizer"
    if str(generalizer) not in sys.path:
        sys.path.insert(0, str(generalizer))
    import draft_persona as drafter
    import websearch as ws

    class Client:
        async def complete_json(self, *a, **k):
            return {"condensed": "far too little"}, None

    pages = _pages(ws, [("https://example.org/a", "word " * 1000)])
    out = asyncio.run(drafter.condense_acquired(Client(), {"slot": pages}, 4000))
    assert out["slot"] == pages, "losing the material is worse than an oversized prompt"


def test_a_legitimate_condensation_is_kept():
    """The floor must not reject real work: observed good ratios start at 11.9%."""
    import asyncio, sys

    generalizer = REPO_ROOT / "persona_generalizer"
    if str(generalizer) not in sys.path:
        sys.path.insert(0, str(generalizer))
    import draft_persona as drafter
    import websearch as ws

    class Client:
        async def complete_json(self, *a, **k):
            return {"condensed": "kept " * 120}, None   # 12% of 1000, above the 8% floor

    pages = _pages(ws, [("https://example.org/a", "word " * 1000)])
    out = asyncio.run(drafter.condense_acquired(Client(), {"slot": pages}, 4000))
    assert out["slot"] != pages and len(out["slot"]) == 1


def test_a_primary_source_gets_far_more_of_the_prompt_than_a_summary():
    """The last link in a chain that kept breaking in a new place each time.

    Source tiering, cross-language search, native-title lookup and the condensation guards all
    exist to put a transcription in front of the drafter. A flat 800-word-per-page cap at the
    final step undid all of it: a 13,000-word biography arrived as its first 800 words, so the
    drafter wrote from memory and 56% of its passages were then correctly downgraded as
    unsupported. Budget has to follow the tier.
    """
    import re
    import sys

    generalizer = REPO_ROOT / "persona_generalizer"
    if str(generalizer) not in sys.path:
        sys.path.insert(0, str(generalizer))
    import draft_persona as drafter
    import websearch as ws

    pages = [
        (ws.SearchResult("https://zh.wikisource.org/wiki/x", "t", "s", ""), "zh " * 9000),
        (ws.SearchResult("https://en.wikipedia.org/wiki/x", "t", "s", ""), "en " * 9000),
    ]
    out = drafter.format_acquired({"words": pages})
    sizes = {}
    for block in out.split("## words")[1:]:
        url = re.search(r"URL: (\S+)", block).group(1)
        sizes[ws.source_tier(url)] = len(block.split())
    assert sizes["primary"] > 4 * sizes["reference"], sizes


def test_gendered_schema_field_names_are_normalised():
    """Models silently rewrite gendered field names to match their subject.

    A run lost all eleven formation phases to `what_it_left_him_with`, and an earlier one dropped
    `what_was_possible_for_someone_like_her` — a field named after the template persona, who is a
    woman — rather than use it for a man. Renaming the schema fields is the other fix, but they
    are the published contract and two committed personas already use them.
    """
    import sys

    generalizer = REPO_ROOT / "persona_generalizer"
    if str(generalizer) not in sys.path:
        sys.path.insert(0, str(generalizer))
    import draft_persona as drafter

    out = drafter.normalise_field_names(
        {
            "formation": [{"phase": "p", "what_it_left_him_with": "x"}],
            "context": {"what_was_possible_for_someone_like_them": {"what": "y"}},
        }
    )
    assert "what_it_left_them_with" in out["formation"][0]
    assert "what_was_possible_for_someone_like_her" in out["context"]


def test_uncovered_gate_decisions_become_search_targets():
    """The run's own stated grounds are the one signal that can reveal an absence.

    A corpus cannot show what is missing from it. But the gate wrote down which decisions it
    admitted the subject for — on a real run, "the Baidicheng succession instruction" and "the
    deathbed testament" — and the evidence pass covered neither. Both live in a different chapter
    of the history than acquisition had found, which no query written in advance could know. So
    an uncovered decision becomes a search phrase through the same loop laundering uses.
    """
    import asyncio, sys

    generalizer = REPO_ROOT / "persona_generalizer"
    if str(generalizer) not in sys.path:
        sys.path.insert(0, str(generalizer))
    import draft_persona as drafter

    class Client:
        async def complete_json(self, role, messages, **k):
            assert role == "reviewer", "coverage must be judged by a different family"
            return {"uncovered": [
                {"decision": "the deathbed testament", "why": "no passage carries it"},
                {"decision": "", "why": "malformed, must be dropped"},
            ]}, None

    got = asyncio.run(drafter.check_gate_coverage(
        Client(),
        {"decisions_with_reasoning": "(1) the deathbed testament (2) Changban"},
        [{"id": "C1", "title": "t", "body": "b"}],
        4000,
    ))
    assert [g["decision"] for g in got] == ["the deathbed testament"]


def test_coverage_is_skipped_when_the_gate_said_nothing():
    """No stated grounds means no signal; the check must not invent one."""
    import asyncio, sys

    generalizer = REPO_ROOT / "persona_generalizer"
    if str(generalizer) not in sys.path:
        sys.path.insert(0, str(generalizer))
    import draft_persona as drafter

    class Client:
        async def complete_json(self, *a, **k):
            raise AssertionError("must not call the model with no grounds to check against")

    assert asyncio.run(drafter.check_gate_coverage(
        Client(), {"decisions_with_reasoning": ""}, [{"id": "C1"}], 4000)) == []
    assert asyncio.run(drafter.check_gate_coverage(
        Client(), {"decisions_with_reasoning": "grounds"}, [], 4000)) == []
