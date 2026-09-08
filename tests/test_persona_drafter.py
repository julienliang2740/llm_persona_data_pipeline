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
