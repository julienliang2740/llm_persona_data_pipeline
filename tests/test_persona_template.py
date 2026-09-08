"""The persona template must keep loading as a target.

`persona_generalizer/personas/_template/` is a superset of the target spec: it carries the
persona-only sections (subject, context, formation, conflicts, voice, epistemic_horizon,
sufficiency, attribution_policy) on top of everything the loader requires. That only works
while the loader keeps tolerating unknown top-level keys, so a tightening of
`pipeline/target.py` would break it silently — nothing else in the suite loads it.

These tests are the guard. They also pin the two decisions the persona schema turns on, so a
later edit that quietly reverts either one fails here rather than in generated data.
"""

from __future__ import annotations

import pytest

from pipeline.target import load_target
from tests.conftest import REPO_ROOT

PERSONAS_DIR = REPO_ROOT / "persona_generalizer" / "personas"
TEMPLATE_ID = "_template"


@pytest.fixture(scope="module")
def persona_template():
    if not (PERSONAS_DIR / TEMPLATE_ID / "spec.yaml").exists():
        pytest.skip("persona template not present")
    return load_target(PERSONAS_DIR, TEMPLATE_ID, strict=True)


def test_persona_template_loads_in_strict_mode(persona_template):
    """Strict mode is what `main.py check` runs, so this is the command's own contract."""
    assert persona_template.target_id == TEMPLATE_ID
    assert len(persona_template.principles) >= 3
    assert persona_template.deliberation_shape
    assert len(persona_template.signature_moves) >= 3


def test_persona_only_sections_survive_loading(persona_template):
    """Unknown top-level keys must reach `spec.raw`, or the persona fields render as nothing."""
    raw = persona_template.raw
    for section in (
        "subject",
        "context",
        "formation",
        "conflicts",
        "voice",
        "epistemic_horizon",
        "sufficiency",
        "attribution_policy",
    ):
        assert raw.get(section), f"persona section '{section}' was dropped by the loader"


def test_words_and_deeds_share_the_key_passages_file(persona_template):
    """Passage ids parse only from key_passages.md, so a cited deed has to live there too."""
    ids = {passage.id for passage in persona_template.key_passages}
    assert any(i.startswith("AR-W") for i in ids), "no words among the passages"
    assert any(i.startswith("AR-D") for i in ids), "no deeds among the passages"
    assert any(i.startswith("AR-T") for i in ids), "no testimony among the passages"


def test_conflicts_resolve_against_real_passages(persona_template):
    """Every conflict names a statement and a deed that exist, and says how it resolved."""
    ids = {passage.id for passage in persona_template.key_passages}
    conflicts = persona_template.raw["conflicts"]
    assert conflicts, "the conflicts section is what implements conduct-over-words"
    for conflict in conflicts:
        where = conflict.get("id")
        assert conflict.get("said") in ids, f"conflict '{where}' cites a missing statement"
        assert conflict.get("did") in ids, f"conflict '{where}' cites a missing deed"
        assert conflict.get("resolution") in {"conduct", "statement", "reconciled"}
        assert conflict.get("reconciliation_attempted"), (
            f"conflict '{where}' resolves without recording an attempt to reconcile it"
        )
        assert conflict.get("consequence_for_the_persona"), (
            f"conflict '{where}' states no behavioural consequence, so it never reaches the data"
        )


def test_an_unreconciled_conflict_defaults_to_conduct(persona_template):
    """Conduct outranks statements: the template must keep demonstrating that path."""
    resolutions = {c["id"]: c["resolution"] for c in persona_template.raw["conflicts"]}
    assert "conduct" in resolutions.values(), (
        "no conflict resolves to conduct, so the template no longer shows the default rule"
    )


def test_persona_carries_no_modern_constraint_clause(persona_template):
    """Persona specs must not place the subject inside modern norms; fidelity governs content.

    The value-system targets all carry such a clause in `summary`. A persona that grows one has
    had its purpose reversed, so this asserts the absence rather than trusting review to catch it.
    """
    summary = persona_template.summary.lower()
    assert "modern constraints:" not in summary
    assert "operates inside them" not in summary


def test_attribution_policy_declares_rows_are_constructions(persona_template):
    """Every generated row is synthesised; the manifest has to say so."""
    policy = persona_template.raw["attribution_policy"]
    assert policy.get("declare_in_manifest") is True
    assert policy.get("statement")


def test_epistemic_horizon_policy_is_one_of_the_known_options(persona_template):
    horizon = persona_template.raw["epistemic_horizon"]
    assert horizon.get("policy") in {
        "translate_to_analogue",
        "acknowledge_unfamiliarity",
        "answer_at_principle",
        "refuse",
    }
    assert horizon.get("cannot_know")


def test_sufficiency_gate_admits_the_template(persona_template):
    sufficiency = persona_template.raw["sufficiency"]
    assert sufficiency.get("verdict") in {"admit", "admit_with_caveats"}
    assert sufficiency.get("decisions_with_reasoning"), "the binding sufficiency criterion is unrecorded"
