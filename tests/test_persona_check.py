"""The persona checker: the admissibility gate and the persona-only rules.

`main.py check` validates what the pipeline needs to run and knows nothing about the persona
sections, so a persona spec can pass it while carrying a `refuse` verdict or a conflict that
resolves to nothing. These tests pin the rules `check_persona.py` adds on top, and in particular
the two decisions the whole schema turns on: conduct outranks statements, and the persona is
never placed inside modern constraints.
"""

from __future__ import annotations

import copy
import shutil
from pathlib import Path

import pytest
import yaml

from tests.conftest import REPO_ROOT

PERSONAS_DIR = REPO_ROOT / "persona_generalizer" / "personas"
TEMPLATE_DIR = PERSONAS_DIR / "_template"

pytestmark = pytest.mark.skipif(
    not (TEMPLATE_DIR / "spec.yaml").exists(), reason="persona template not present"
)


@pytest.fixture(scope="module")
def check_persona():
    import sys

    generalizer = REPO_ROOT / "persona_generalizer"
    if str(generalizer) not in sys.path:
        sys.path.insert(0, str(generalizer))
    from check_persona import check_persona as fn

    return fn


@pytest.fixture(scope="module")
def template_raw() -> dict:
    return yaml.safe_load((TEMPLATE_DIR / "spec.yaml").read_text(encoding="utf-8"))


def build(tmp_path: Path, raw: dict, persona_id: str = "probe") -> Path:
    """Write a persona directory under tmp_path, reusing the template's passages."""
    root = tmp_path / persona_id
    shutil.copytree(TEMPLATE_DIR / "references", root / "references")
    raw = copy.deepcopy(raw)
    raw["id"] = persona_id
    (root / "spec.yaml").write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    return tmp_path


def test_the_shipped_template_passes(check_persona, capsys):
    assert check_persona("_template", PERSONAS_DIR) == 0
    assert "OK (persona, strict)" in capsys.readouterr().out


def test_a_clean_copy_passes(check_persona, tmp_path, template_raw):
    assert check_persona("probe", build(tmp_path, template_raw)) == 0


def test_refuse_verdict_blocks_the_build(check_persona, tmp_path, template_raw, capsys):
    """A refusal is a real answer; a spec written past one is imagination wearing a real name."""
    raw = copy.deepcopy(template_raw)
    raw["sufficiency"]["verdict"] = "refuse"
    assert check_persona("probe", build(tmp_path, raw)) == 2
    assert "not admissible" in capsys.readouterr().err


def test_missing_binding_criterion_blocks(check_persona, tmp_path, template_raw, capsys):
    raw = copy.deepcopy(template_raw)
    del raw["sufficiency"]["decisions_with_reasoning"]
    assert check_persona("probe", build(tmp_path, raw)) == 2
    assert "decisions_with_reasoning" in capsys.readouterr().err


def test_conflict_citing_an_unknown_passage_blocks(check_persona, tmp_path, template_raw, capsys):
    raw = copy.deepcopy(template_raw)
    raw["conflicts"][0]["did"] = "AR-D99"
    assert check_persona("probe", build(tmp_path, raw)) == 2
    assert "AR-D99" in capsys.readouterr().err


def test_conflict_without_a_reconciliation_attempt_blocks(
    check_persona, tmp_path, template_raw, capsys
):
    """Conduct is the fallback, not the first move: the attempt has to be on the record."""
    raw = copy.deepcopy(template_raw)
    del raw["conflicts"][0]["reconciliation_attempted"]
    assert check_persona("probe", build(tmp_path, raw)) == 2
    assert "reconcile" in capsys.readouterr().err


def test_conflict_without_a_behavioural_consequence_blocks(
    check_persona, tmp_path, template_raw, capsys
):
    raw = copy.deepcopy(template_raw)
    del raw["conflicts"][0]["consequence_for_the_persona"]
    assert check_persona("probe", build(tmp_path, raw)) == 2
    assert "never reaches the data" in capsys.readouterr().err


def test_invalid_resolution_blocks(check_persona, tmp_path, template_raw, capsys):
    raw = copy.deepcopy(template_raw)
    raw["conflicts"][0]["resolution"] = "idealised"
    assert check_persona("probe", build(tmp_path, raw)) == 2
    assert "resolution" in capsys.readouterr().err


def test_modern_constraint_clause_blocks(check_persona, tmp_path, template_raw, capsys):
    """The clause every value-system target carries is exactly what a persona must not have."""
    raw = copy.deepcopy(template_raw)
    raw["summary"] += (
        "\nMODERN CONSTRAINTS: anti-discrimination and safeguarding govern here and this "
        "persona operates inside them.\n"
    )
    assert check_persona("probe", build(tmp_path, raw)) == 2
    assert "modern-constraint clause" in capsys.readouterr().err


def test_living_private_individual_is_out_of_scope(check_persona, tmp_path, template_raw, capsys):
    raw = copy.deepcopy(template_raw)
    raw["attribution_policy"]["subject_status"] = "living_private_individual"
    assert check_persona("probe", build(tmp_path, raw)) == 2
    assert "out of" in capsys.readouterr().err


def test_attribution_must_reach_the_manifest(check_persona, tmp_path, template_raw, capsys):
    raw = copy.deepcopy(template_raw)
    raw["attribution_policy"]["declare_in_manifest"] = False
    assert check_persona("probe", build(tmp_path, raw)) == 2
    assert "declare_in_manifest" in capsys.readouterr().err


@pytest.mark.parametrize(
    "section", ["subject", "context", "formation", "voice", "epistemic_horizon", "attribution_policy"]
)
def test_each_persona_section_is_required(check_persona, tmp_path, template_raw, section, capsys):
    raw = copy.deepcopy(template_raw)
    del raw[section]
    assert check_persona("probe", build(tmp_path, raw)) == 2
    assert section in capsys.readouterr().err


def test_unknown_epistemic_horizon_policy_blocks(check_persona, tmp_path, template_raw, capsys):
    raw = copy.deepcopy(template_raw)
    raw["epistemic_horizon"]["policy"] = "modernise"
    assert check_persona("probe", build(tmp_path, raw)) == 2
    assert "epistemic_horizon.policy" in capsys.readouterr().err


def test_warnings_do_not_block(check_persona, tmp_path, template_raw, capsys):
    """Thin domain weights are a reviewer's call, not a failure."""
    raw = copy.deepcopy(template_raw)
    for domain in raw["domains"]:
        domain["weight"] = 0.1
    assert check_persona("probe", build(tmp_path, raw)) == 0
    assert "domain weights sum to" in capsys.readouterr().out


def test_an_empty_conflicts_list_warns_but_passes(check_persona, tmp_path, template_raw, capsys):
    """A researcher may assert they looked and found no gap; that is theirs to claim."""
    raw = copy.deepcopy(template_raw)
    raw["conflicts"] = []
    assert check_persona("probe", build(tmp_path, raw)) == 0
    assert "none recorded" in capsys.readouterr().out


def test_an_absent_conflicts_key_blocks(check_persona, tmp_path, template_raw, capsys):
    """Absent means the question was never asked, which is not the same as finding nothing."""
    raw = copy.deepcopy(template_raw)
    del raw["conflicts"]
    assert check_persona("probe", build(tmp_path, raw)) == 2
    assert "conflicts: missing" in capsys.readouterr().err


# --- the world that produced the person -------------------------------------------------------
# These guard a regression that actually happened: sixteen vivid passages of words and deeds
# beside four unsourced lines of context. The persona reads fluently and has no world.


def test_missing_context_field_blocks(check_persona, tmp_path, template_raw, capsys):
    raw = copy.deepcopy(template_raw)
    del raw["context"]["material_conditions"]
    assert check_persona("probe", build(tmp_path, raw)) == 2
    assert "context.material_conditions" in capsys.readouterr().err


def test_context_as_a_bare_paragraph_blocks(check_persona, tmp_path, template_raw, capsys):
    """A string where a sourced block belongs is the shape this schema exists to prevent."""
    raw = copy.deepcopy(template_raw)
    raw["context"]["institutions"] = "A harbour board of eleven seats."
    assert check_persona("probe", build(tmp_path, raw)) == 2
    assert "bare paragraph" in capsys.readouterr().err


def test_context_must_be_sourced(check_persona, tmp_path, template_raw, capsys):
    raw = copy.deepcopy(template_raw)
    del raw["context"]["what_was_ordinary_then"]["sources"]
    assert check_persona("probe", build(tmp_path, raw)) == 2
    assert "cites no sources" in capsys.readouterr().err


def test_context_sources_must_resolve(check_persona, tmp_path, template_raw, capsys):
    raw = copy.deepcopy(template_raw)
    raw["context"]["standing_and_constraint"]["sources"] = ["AR-C99"]
    assert check_persona("probe", build(tmp_path, raw)) == 2
    assert "AR-C99" in capsys.readouterr().err


def test_missing_psychological_effect_warns(check_persona, tmp_path, template_raw, capsys):
    """Recording the condition without its effect leaves out the half that reaches the persona."""
    raw = copy.deepcopy(template_raw)
    del raw["context"]["institutions"]["psychological_effect"]
    assert check_persona("probe", build(tmp_path, raw)) == 0
    assert "psychological_effect" in capsys.readouterr().out


def test_formation_phase_must_be_sourced(check_persona, tmp_path, template_raw, capsys):
    raw = copy.deepcopy(template_raw)
    del raw["formation"][1]["sources"]
    assert check_persona("probe", build(tmp_path, raw)) == 2
    assert "cites no sources" in capsys.readouterr().err


def test_thin_context_warns(check_persona, tmp_path, template_raw, capsys):
    """The regression itself: every field present, every field a sentence long."""
    raw = copy.deepcopy(template_raw)
    for field, value in raw["context"].items():
        value["what"] = "Briefly stated."
        value.pop("psychological_effect", None)
    for phase in raw["formation"]:
        phase["what_happened"] = "It happened."
        phase["what_it_left_them_with"] = "It marked her."
    assert check_persona("probe", build(tmp_path, raw)) == 0
    out = capsys.readouterr().out
    assert "under the 400 expected" in out


def test_the_shipped_template_is_not_thin(check_persona, capsys):
    assert check_persona("_template", PERSONAS_DIR) == 0
    out = capsys.readouterr().out
    assert "context+formation:" in out
    assert "under the 400 expected" not in out


# --- corpus volume ----------------------------------------------------------------------------
# The spec is the seed for ~500 training rows, not the dataset. A thin corpus produces repetitive
# scenarios rather than fewer of them, and an oversized one blows the per-call prompt budget.


def test_volume_floor_is_skipped_for_template_ids(check_persona, capsys):
    """`_template` is deliberately small: it exists to be copied and deleted."""
    assert check_persona("_template", PERSONAS_DIR) == 0
    assert "under the 60 expected" not in capsys.readouterr().out


def test_volume_floor_warns_on_a_real_persona(check_persona, tmp_path, template_raw, capsys):
    assert check_persona("probe", build(tmp_path, template_raw)) == 0
    out = capsys.readouterr().out
    assert "under the 60 expected" in out
    assert "under the 6000 expected" in out


def test_volume_ceiling_warns(check_persona, tmp_path, template_raw, capsys):
    """key_passages.md is placed into every prompt, so its size is a token budget."""
    src = (TEMPLATE_DIR / "references" / "key_passages.md").read_text(encoding="utf-8")
    root = build(tmp_path, template_raw)
    padded = src + "\n\n### AR-X1 — padding\n" + ("word " * 9000) + "\n"
    (root / "probe" / "references" / "key_passages.md").write_text(padded, encoding="utf-8")
    assert check_persona("probe", root) == 0
    assert "over the 8000 ceiling" in capsys.readouterr().out


# -------------------------------------------------------------------------------------------
# Evidence basis, and the split between the two refusals.
#
# These pin the distinction the gate used to collapse: "the material does not survive" and "I
# did not reach the material" are different findings, and only the second is retryable. And the
# rule that makes reconstruction safe to allow at all — that it is visible downstream rather
# than indistinguishable from evidence.
# -------------------------------------------------------------------------------------------


def mark_reconstructed(root: Path, persona_id: str, passage_ids: set[str]) -> None:
    """Add an `evidence_basis:` line to the named passages of a built persona."""
    path = root / persona_id / "references" / "key_passages.md"
    out, current = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") and not line.startswith("# "):
            heading = line.lstrip("#").strip()
            current = heading.split("—")[0].split(" - ")[0].strip()
            out.append(line)
            if current in passage_ids:
                out.append("evidence_basis: reconstructed")
            continue
        out.append(line)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def test_refuse_evidence_blocks_the_build(check_persona, tmp_path, template_raw, capsys):
    raw = copy.deepcopy(template_raw)
    raw["sufficiency"]["verdict"] = "refuse_evidence"
    build(tmp_path, raw)
    assert check_persona("probe", tmp_path) == 2
    assert "does not survive" in capsys.readouterr().err


def test_refuse_acquisition_blocks_but_names_itself_retryable(
    check_persona, tmp_path, template_raw, capsys
):
    raw = copy.deepcopy(template_raw)
    raw["sufficiency"]["verdict"] = "refuse_acquisition"
    raw["sufficiency"]["acquisition_attempts"] = "three passes; slot-driven, references, Greek."
    build(tmp_path, raw)
    assert check_persona("probe", tmp_path) == 2
    err = capsys.readouterr().err
    assert "fact about the search" in err


def test_refuse_acquisition_requires_recording_what_was_tried(
    check_persona, tmp_path, template_raw, capsys
):
    raw = copy.deepcopy(template_raw)
    raw["sufficiency"]["verdict"] = "refuse_acquisition"
    raw["sufficiency"].pop("acquisition_attempts", None)
    build(tmp_path, raw)
    assert check_persona("probe", tmp_path) == 2
    assert "acquisition_attempts" in capsys.readouterr().err


def test_bare_refuse_still_blocks_but_is_deprecated(check_persona, tmp_path, template_raw, capsys):
    raw = copy.deepcopy(template_raw)
    raw["sufficiency"]["verdict"] = "refuse"
    build(tmp_path, raw)
    assert check_persona("probe", tmp_path) == 2
    assert "deprecated" in capsys.readouterr().err


def test_reconstruction_without_the_matching_verdict_blocks(
    check_persona, tmp_path, template_raw, capsys
):
    """An inferred passage in an `admit` spec is invisible downstream. That is the whole risk."""
    raw = copy.deepcopy(template_raw)
    raw["sufficiency"]["verdict"] = "admit_with_caveats"
    build(tmp_path, raw)
    mark_reconstructed(tmp_path, "probe", {"AR-C1"})
    assert check_persona("probe", tmp_path) == 2
    assert "admit_reconstructed" in capsys.readouterr().err


def test_reconstructed_verdict_requires_every_passage_to_declare(
    check_persona, tmp_path, template_raw, capsys
):
    raw = copy.deepcopy(template_raw)
    raw["sufficiency"]["verdict"] = "admit_reconstructed"
    raw["sufficiency"]["caveats"] = "thin first-person volume; circumstance is inferred."
    build(tmp_path, raw)
    mark_reconstructed(tmp_path, "probe", {"AR-C1"})
    assert check_persona("probe", tmp_path) == 2
    assert "must declare an 'evidence_basis:' line" in capsys.readouterr().err


def test_a_conflict_may_not_rest_on_a_reconstructed_passage(
    check_persona, tmp_path, template_raw, capsys
):
    """Conduct-over-words cannot run on inference: the gap might be one the researcher made."""
    raw = copy.deepcopy(template_raw)
    raw["sufficiency"]["verdict"] = "admit_reconstructed"
    raw["sufficiency"]["caveats"] = "thin; some passages inferred."
    said = raw["conflicts"][0]["said"]
    build(tmp_path, raw)
    mark_reconstructed(tmp_path, "probe", {said})
    assert check_persona("probe", tmp_path) == 2
    assert "both sides must be attested" in capsys.readouterr().err


def test_reconstruction_over_the_ceiling_blocks(check_persona, tmp_path, template_raw, capsys):
    import re as _re

    raw = copy.deepcopy(template_raw)
    raw["sufficiency"]["verdict"] = "admit_reconstructed"
    raw["sufficiency"]["caveats"] = "thin; mostly inferred."
    build(tmp_path, raw)
    text = (tmp_path / "probe" / "references" / "key_passages.md").read_text(encoding="utf-8")
    every = {
        h.lstrip("#").strip().split("—")[0].strip()
        for h in _re.findall(r"^#{2,4}\s+.+$", text, _re.MULTILINE)
    }
    mark_reconstructed(tmp_path, "probe", every)
    assert check_persona("probe", tmp_path) == 2
    assert "over the 40% ceiling" in capsys.readouterr().err


# -------------------------------------------------------------------------------------------
# Scope: the axis the evidentiary criteria cannot reach.
#
# The gate asks whether enough material survives. These pin the separate question of whether a
# faithful persona of a subject should be built at all — which the criteria answer wrongly,
# because the subjects excluded here are among the best-documented people who ever lived.
# -------------------------------------------------------------------------------------------


def test_scope_check_is_required_on_every_admitted_spec(
    check_persona, tmp_path, template_raw, capsys
):
    raw = copy.deepcopy(template_raw)
    raw["sufficiency"].pop("scope_check", None)
    build(tmp_path, raw)
    assert check_persona("probe", tmp_path) == 2
    assert "scope_check" in capsys.readouterr().err


def test_refuse_scope_blocks_the_build(check_persona, tmp_path, template_raw, capsys):
    raw = copy.deepcopy(template_raw)
    raw["sufficiency"]["verdict"] = "refuse_scope"
    build(tmp_path, raw)
    assert check_persona("probe", tmp_path) == 2
    assert "out of scope" in capsys.readouterr().err


def test_a_tripwire_subject_cannot_be_admitted(check_persona, tmp_path, template_raw, capsys):
    """Evidence volume is irrelevant here, which is the whole reason the axis is separate.

    The subject is read from the list rather than written out, so the test pins the behaviour
    and not the contents — and stays correct if the list is ever revised.
    """
    import sys

    generalizer = REPO_ROOT / "persona_generalizer"
    if str(generalizer) not in sys.path:
        sys.path.insert(0, str(generalizer))
    import scope as scope_rules

    raw = copy.deepcopy(template_raw)
    raw["name"] = f"{scope_rules.TRIPWIRE[0][0].title()} (dates)"
    build(tmp_path, raw)
    assert check_persona("probe", tmp_path) == 2
    assert "scope tripwire" in capsys.readouterr().err


def test_an_in_scope_subject_is_untouched_by_the_tripwire(check_persona, tmp_path, template_raw):
    raw = copy.deepcopy(template_raw)
    raw["name"] = "Lyndon Baines Johnson (1908-1973)"
    build(tmp_path, raw)
    assert check_persona("probe", tmp_path) == 0
