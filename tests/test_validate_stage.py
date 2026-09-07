"""The validate stage end to end with a stubbed client. No network.

This file exists because of a bug that shipped: a scripted edit left two definitions of
`run_stage` in validate.py, and the surviving one called a `_training_text` helper that had
been renamed away. Every unit test passed, because none of them ran the stage. The stage
would have raised NameError on its first real invocation.
"""

from __future__ import annotations

import ast
import asyncio
from collections import Counter
from pathlib import Path

import pytest

from pipeline import records, validate
from pipeline.records import (
    BaselineAnswer,
    Decision,
    DivergenceVerdict,
    Family,
    Prompt,
    Response,
    Review,
)

PIPELINE = Path(__file__).resolve().parent.parent / "pipeline"


class StubClient:
    """Stands in for ModelClient: canned reviews, judgements and embeddings."""

    def __init__(self, verdict="accept", diverges=True):
        self.verdict = verdict
        self.diverges = diverges
        self.calls: Counter[str] = Counter()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return None

    async def embed(self, texts, role=None, **kwargs):
        # Distinct unit vectors, so nothing looks like a duplicate.
        return [[1.0 if i == index else 0.0 for i in range(len(texts))] for index in range(len(texts))]

    async def complete_json(self, role, messages, *, stage="", record_id="", **kwargs):
        self.calls[stage] += 1
        if stage.startswith("validate.review"):
            payload = {
                "judgment_evidence_quote": "Tell her before she signs.",
                "judgment_move": "acts while it can still matter",
                "scores": {key: 5 for key in ("fidelity", "judgment_not_terminology", "scenario_quality")}
                | {
                    "cue_leakage": False,
                    "confident_on_unresolved": False,
                    "formulaic_shape": False,
                    "prompt_stipulates_move": False,
                    "quoted_source_text": False,
                    "archaic_register": False,
                },
                "signature_moves_present": [],
                "notes": [],
                "issues": [],
                "verdict": self.verdict,
                "rationale": "fine",
            }
        elif stage == "validate.divergence":
            payload = {
                "actions": {"a": "tell her now", "b": "document it", "c": "raise it in writing"},
                "pairwise": {"a_vs_b": True, "a_vs_c": True, "b_vs_c": False},
                "diverges": self.diverges,
                "kind": "action",
                "closer_to": "candidate",
                "value_named": "Her ability to change course is the thing that matters." if self.diverges else "",
                "divergence_source": "value" if self.diverges else "capability",
                "hypothesis_id": "h1",
                "explanation": "different action",
            }
        else:
            payload = {"deliberation": "d", "answer": "a rewritten answer."}
        return payload, type("R", (), {"text": "{}", "usage": {}})()


def build_run(tmp_path, *, case_type="divergence", truncated=False):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    families = [
        Family("fam_t", "toy", "work", ["tr1"], ["TP01"], case_type, "a seed", "hard", "train",
               slot_index=0, divergence_hypothesis_id="h1"),
        Family("fam_e", "toy", "household", ["tr2"], ["TP02"], "ordinary", "another seed", "hard",
               "eval", slot_index=1),
    ]
    prompts = [
        Prompt("pr_t", "fam_t", "base", "a long training prompt about a supplier", case_type),
        Prompt("pr_e", "fam_e", "base", "an evaluation prompt about a shared booking", "ordinary"),
    ]
    responses = [
        Response("resp_t", "pr_t", "deliberation one", "answer one.", {"principles_applied": ["TP01"]}),
        Response("resp_e", "pr_e", "deliberation two", "answer two.", {"principles_applied": ["TP02"]}),
    ]
    baselines = [
        BaselineAnswer("pr_t", "base-7b", "" if truncated else "the base answer.", kind="base",
                       finish_reason="length" if truncated else "stop")
    ]
    generics = [BaselineAnswer("pr_t", "strong", "the generic answer.", kind="strong_generic",
                               finish_reason="stop")]
    records.write_jsonl(run_dir / records.FAMILIES_FILE, families)
    records.write_jsonl(run_dir / records.PROMPTS_FILE, prompts)
    records.write_jsonl(run_dir / records.RESPONSES_FILE, responses)
    records.write_jsonl(run_dir / records.BASELINE_FILE, baselines)
    records.write_jsonl(run_dir / records.STRONG_BASELINE_FILE, generics)
    return run_dir


def run(config, spec, run_dir, client):
    from unittest.mock import patch

    with patch.object(validate.ModelClient, "from_config", return_value=client):
        return asyncio.run(validate.run_stage(config, spec, run_dir))


def test_the_stage_runs_end_to_end(tmp_path, pilot_config, toy_spec):
    """The regression net: this is what a duplicated run_stage broke."""
    run_dir = build_run(tmp_path)
    summary = run(pilot_config, toy_spec, run_dir, StubClient())
    assert summary["responses"] == 2
    assert summary["kept"] == 2
    for name in (records.REVIEWS_FILE, records.DECISIONS_FILE, records.DIVERGENCE_FILE,
                 records.SIMILARITY_FILE):
        assert (run_dir / name).exists(), name


def test_the_stage_writes_the_similarity_artifact(tmp_path, pilot_config, toy_spec):
    run_dir = build_run(tmp_path)
    run(pilot_config, toy_spec, run_dir, StubClient())
    rows = list(records.iter_jsonl(run_dir / records.SIMILARITY_FILE))
    assert rows
    for row in rows:
        assert row["kind"] in ("dedupe", "leakage")
        assert {"a_id", "b_id", "score", "method", "flagged", "calibration"} <= set(row)
        assert row["calibration"]["statistic"].startswith("median")


def test_the_summary_carries_the_calibration_and_three_way_rates(tmp_path, pilot_config, toy_spec):
    run_dir = build_run(tmp_path)
    summary = run(pilot_config, toy_spec, run_dir, StubClient())
    assert summary["similarity_calibration"]["statistic"].startswith("median")
    assert "divergence_pairwise" in summary
    assert summary["divergence_pairwise"]["candidate_vs_base"] == 1
    assert summary["divergence_value_rate_by_family"] == 1.0


def test_a_truncated_baseline_makes_the_verdict_unverified(tmp_path, pilot_config, toy_spec):
    run_dir = build_run(tmp_path, truncated=True)
    summary = run(pilot_config, toy_spec, run_dir, StubClient())
    assert summary["divergence_unverified"] == 1
    verdicts = records.read_jsonl(run_dir / records.DIVERGENCE_FILE, DivergenceVerdict)
    assert verdicts[0].unverified_reason
    assert verdicts[0].diverges is False


def test_a_revise_verdict_triggers_a_rewrite_and_a_re_review(tmp_path, pilot_config, toy_spec):
    run_dir = build_run(tmp_path)
    client = StubClient(verdict="revise")
    run(pilot_config, toy_spec, run_dir, client)
    assert client.calls["validate.revise"] == 2
    responses = records.read_jsonl(run_dir / records.RESPONSES_FILE, Response)
    assert all(response.revise_rounds == 1 for response in responses)


def test_a_response_still_asking_for_revision_is_dropped(tmp_path, pilot_config, toy_spec):
    run_dir = build_run(tmp_path)
    summary = run(pilot_config, toy_spec, run_dir, StubClient(verdict="revise"))
    assert summary["kept"] == 0
    decisions = records.read_jsonl(run_dir / records.DECISIONS_FILE, Decision)
    assert all("still asks for revision" in " ".join(d.reasons) for d in decisions)


def test_a_non_diverging_case_is_relabelled_not_dropped(tmp_path, pilot_config, toy_spec):
    run_dir = build_run(tmp_path)
    summary = run(pilot_config, toy_spec, run_dir, StubClient(diverges=False))
    assert summary["kept"] == 2
    decisions = {d.response_id: d for d in records.read_jsonl(run_dir / records.DECISIONS_FILE, Decision)}
    assert decisions["resp_t"].final_case_type == "ordinary"
    assert decisions["resp_t"].divergence_status == "not_confirmed"


def test_the_stage_refuses_an_empty_run(tmp_path, pilot_config, toy_spec):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(RuntimeError) as error:
        run(pilot_config, toy_spec, empty, StubClient())
    assert "generate" in str(error.value)


# -- structural guards against the edit that caused this ----------------------


@pytest.mark.parametrize(
    "module", ["validate.py", "similarity.py", "review.py", "divergence.py", "generate.py",
               "plan.py", "model.py", "target.py"]
)
def test_no_module_defines_the_same_top_level_name_twice(module):
    """A scripted block replacement that misses its boundary appends instead of replacing."""
    tree = ast.parse((PIPELINE / module).read_text(encoding="utf-8"))
    names = [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    repeats = [name for name, count in Counter(names).items() if count > 1]
    assert not repeats, f"{module} defines {repeats} more than once"


@pytest.mark.parametrize(
    "module", ["validate.py", "similarity.py", "review.py", "divergence.py", "generate.py",
               "plan.py", "model.py", "target.py", "export.py", "baseline.py"]
)
def test_no_module_calls_a_name_it_never_defines_or_imports(module):
    """`_training_text` was called at module scope after being renamed away."""
    source = (PIPELINE / module).read_text(encoding="utf-8")
    tree = ast.parse(source)
    bound: set[str] = set(dir(__builtins__)) | {"__name__", "__file__"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            bound.add(node.id)
        elif isinstance(node, ast.arg):
            bound.add(node.arg)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.ExceptHandler) and node.name:
            bound.add(node.name)
        elif isinstance(node, ast.comprehension) and isinstance(node.target, ast.Name):
            bound.add(node.target.id)
    import builtins

    bound |= set(dir(builtins))
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    private_unbound = sorted(name for name in called - bound if name.startswith("_"))
    assert not private_unbound, f"{module} calls undefined helper(s) {private_unbound}"
