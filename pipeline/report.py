"""Run report: one markdown file a researcher can read in five minutes.

Reads only the artifacts in the run directory, so it can be re-run at any time
without touching a model.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any

from pipeline import records
from pipeline.model import format_cost, summarise_usage
from pipeline.records import Decision, DivergenceVerdict, Family, Prompt, Response, Review
from pipeline.report_style import (
    coverage_tables,
    cross_run_style_table,
    latest_sibling_runs,
    three_way_divergence,
    top_similarity_pairs,
)

logger = logging.getLogger("pipeline.report")

REPORT_FILE = "report.md"


def _truncate(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def build_report(run_dir: Path, target_id: str, pricing: dict[str, Any] | None = None) -> str:
    families = records.read_jsonl(run_dir / records.FAMILIES_FILE, Family)
    prompts = records.read_jsonl(run_dir / records.PROMPTS_FILE, Prompt)
    responses = records.read_jsonl(run_dir / records.RESPONSES_FILE, Response)
    reviews = records.read_jsonl(run_dir / records.REVIEWS_FILE, Review)
    decisions = records.read_jsonl(run_dir / records.DECISIONS_FILE, Decision)
    verdicts = records.read_jsonl(run_dir / records.DIVERGENCE_FILE, DivergenceVerdict)
    usage = summarise_usage(run_dir / records.USAGE_FILE, pricing)

    prompt_by_id = {p.prompt_id: p for p in prompts}
    family_by_id = {f.family_id: f for f in families}
    review_by_response = {r.response_id: r for r in reviews}
    decision_by_response = {d.response_id: d for d in decisions}

    manifest: dict[str, Any] = {}
    manifest_path = run_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    lines: list[str] = [
        f"# Run report: {target_id} / {run_dir.name}",
        "",
        "## Stage counts",
        "",
        "| stage | output |",
        "|---|---|",
        f"| generate | {len(families)} families, {len(prompts)} prompts, {len(responses)} responses |",
        f"| baseline | {len(records.read_jsonl(run_dir / records.BASELINE_FILE))} baseline answers |",
        f"| validate | {len(reviews)} reviews, {len(decisions)} decisions, {len(verdicts)} divergence verdicts |",
    ]
    if manifest:
        counts = manifest.get("counts", {})
        lines.append(
            f"| export | {counts.get('sft_train_rows', 0)} training rows, "
            f"{counts.get('eval_rows', 0)} eval rows |"
        )
    lines += ["", "## Families by split and domain", "", "| split | families | domains |", "|---|---|---|"]
    for split in ("train", "eval", "reserved"):
        subset = [f for f in families if f.split == split]
        domain_counts = Counter(f.domain for f in subset)
        domains = ", ".join(f"{d}×{n}" for d, n in sorted(domain_counts.items())) or "-"
        lines.append(f"| {split} | {len(subset)} | {domains} |")
    groups = {f.counterfactual_group_id for f in families if f.counterfactual_group_id}
    explicit = [f for f in families if f.mode == "explicit"]
    reserved_by_screen = [f for f in families if f.reserved_reason]
    lines += [
        "",
        f"- contrastive groups: **{len(groups)}** covering "
        f"{sum(1 for f in families if f.counterfactual_group_id)} families",
        f"- explicit-mode families: **{len(explicit)}**",
        f"- reserved by the avoided-topic screen: **{len(reserved_by_screen)}**",
    ]
    for family in reserved_by_screen[:5]:
        lines.append(f"  - `{family.family_id}`: {family.reserved_reason}")
    lines += _situation_feature_spread(families)
    lines += coverage_tables(run_dir, families, prompts)

    kept = [d for d in decisions if d.keep]
    dropped = [d for d in decisions if not d.keep]
    lines += [
        "",
        "## Accept / reject",
        "",
        f"- kept: **{len(kept)}** of {len(decisions)} responses"
        + (f" ({len(kept)/len(decisions):.0%})" if decisions else ""),
        f"- dropped: **{len(dropped)}**",
        "",
        "Reasons recorded on dropped responses (a response can have several):",
        "",
        "| reason | count |",
        "|---|---|",
    ]
    reason_counts: Counter[str] = Counter()
    for decision in dropped:
        for reason in decision.reasons:
            reason_counts[_reason_bucket(reason)] += 1
    for reason, count in reason_counts.most_common():
        lines.append(f"| {reason} | {count} |")
    if not reason_counts:
        lines.append("| (nothing dropped) | 0 |")

    verdict_counts = Counter(review.verdict for review in reviews)
    score_means = _mean_scores(reviews)
    lines += [
        "",
        "## Reviewer",
        "",
        "| verdict | count |",
        "|---|---|",
    ]
    for verdict, count in verdict_counts.most_common():
        lines.append(f"| {verdict} | {count} |")
    lines += [
        "",
        "Mean scores: "
        + ", ".join(f"{name} {value:.2f}" for name, value in score_means.items())
        + (f" (n={len(reviews)})" if reviews else ""),
    ]
    lines += _flag_score_conflicts(reviews)
    lines += [
        "",
        "## Cue-term hits",
        "",
    ]
    cue_dropped = [d for d in dropped if any(r.startswith("cue terms found") for r in d.reasons)]
    if cue_dropped:
        for decision in cue_dropped[:10]:
            lines.append(f"- `{decision.response_id}`: {decision.reasons[0]}")
    else:
        lines.append("None. No forbidden term appeared in any prompt or response.")
    soft_flagged = [d for d in decisions if d.soft_cue_hits]
    soft_counts = Counter(term for d in soft_flagged for term in d.soft_cue_hits)
    lines += [
        "",
        f"Soft cue terms (flagged, never a reason to drop): **{len(soft_flagged)}** responses"
        + (
            ". " + ", ".join(f"{term} ×{n}" for term, n in soft_counts.most_common(8))
            if soft_counts
            else ". None."
        ),
    ]
    quoted = [r for r in reviews if r.scores.get("quoted_source_text")]
    archaic = [r for r in reviews if r.scores.get("archaic_register")]
    lines += [
        f"Reviewer flagged quoted or echoed source wording: **{len(quoted)}** "
        f"(a licensing control).",
        f"Reviewer flagged archaic or translated-sounding register: **{len(archaic)}**.",
        f"Explicit-mode records (cue check deliberately skipped): "
        f"**{sum(1 for p in prompts if p.mode == 'explicit')}**.",
    ]

    duplicates = [d for d in decisions if d.duplicate_of]
    lines += ["", "## Near-duplicates", ""]
    if duplicates:
        clusters: dict[str, list[str]] = {}
        for decision in duplicates:
            clusters.setdefault(decision.duplicate_of or "", []).append(decision.response_id)
        lines.append(f"{len(clusters)} cluster(s) covering {len(duplicates)} responses.")
        lines.append("")
        for representative, members in list(clusters.items())[:10]:
            lines.append(f"- `{representative}` absorbs {len(members)}: {', '.join(members[:5])}")
    else:
        lines.append("None above the threshold.")
    # Always show the ranking, threshold or no threshold: round 1 reported "none above
    # the threshold" on a run holding a 0.784 prompt-Jaccard near-repeat.
    lines += top_similarity_pairs(run_dir, decisions)

    leakage_values = [d.max_leakage for d in decisions if d.max_leakage is not None]
    lines += ["", "## Leakage between eval and train", ""]
    if leakage_values:
        top = sorted(
            ((d.max_leakage or 0.0, d.response_id) for d in decisions if d.max_leakage is not None),
            reverse=True,
        )[:5]
        lines.append(
            f"{len(leakage_values)} eval responses checked. "
            f"Maximum similarity to any training row: **{max(leakage_values):.3f}**."
        )
        lines.append("")
        for score, response_id in top:
            lines.append(f"- `{response_id}`: {score:.3f}")
    else:
        lines.append("No eval responses to check (no eval families kept, or no train rows).")

    intended = [d for d in decisions if d.divergence_status != "not_applicable"]
    confirmed = [d for d in intended if d.divergence_status == "confirmed"]
    relabelled = [d for d in intended if d.divergence_status == "not_confirmed"]
    unverified = [d for d in intended if d.divergence_status == "unverified"]
    lines += [
        "",
        "## Divergence from the baseline",
        "",
        f"- intended divergence cases: **{len(intended)}**",
        f"- confirmed by the judge: **{len(confirmed)}**"
        + (f" ({len(confirmed)/len(intended):.0%})" if intended else ""),
        f"- did not diverge, relabelled ordinary: **{len(relabelled)}**",
        f"- unverified (no baseline answer): **{len(unverified)}**",
    ]
    action = [d for d in confirmed if d.divergence_kind in ("action", "both")]
    reasons_only = [d for d in confirmed if d.divergence_kind == "reasons"]
    both = [d for d in confirmed if d.divergence_kind == "both"]
    lines += [
        "",
        "A difference in the reasons alone counts as divergence, not only a different action.",
        "",
        "| kind of divergence | count | share of intended cases |",
        "|---|---|---|",
    ]
    for name, subset in (
        ("action (incl. both)", action),
        ("reasons only", reasons_only),
        ("both action and reasons", both),
    ):
        share = f"{len(subset)/len(intended):.0%}" if intended else "-"
        lines.append(f"| {name} | {len(subset)} | {share} |")
    lines += three_way_divergence(verdicts, prompt_by_id)

    lines += ["", "## House style shared across targets", ""]
    lines += _house_style_section(run_dir)

    lines += [
        "",
        "## Cost and usage",
        "",
        f"- model calls: **{usage['calls']}**",
        f"- prompt tokens: {usage['prompt_tokens']:,}",
        f"- completion tokens: {usage['completion_tokens']:,} "
        f"(of which reasoning: {usage['reasoning_tokens']:,})",
        f"- cost: **{format_cost(usage)}**",
        "",
        "| stage | calls | prompt tokens | completion tokens |",
        "|---|---|---|---|",
    ]
    for stage, stats in sorted(usage["by_stage"].items()):
        lines.append(
            f"| {stage} | {stats['calls']} | {stats['prompt_tokens']:,} "
            f"| {stats['completion_tokens']:,} |"
        )

    lines += ["", "## Samples kept", ""]
    kept_ids = [d.response_id for d in kept]
    response_by_id = {r.response_id: r for r in responses}
    for response_id in kept_ids[:5]:
        response = response_by_id.get(response_id)
        if response is None:
            continue
        prompt = prompt_by_id.get(response.prompt_id)
        family = family_by_id.get(prompt.family_id) if prompt else None
        review = review_by_response.get(response_id)
        decision = decision_by_response.get(response_id)
        lines += [
            f"### `{response_id}` — {family.domain if family else '?'} / "
            f"{decision.final_case_type if decision else '?'} / "
            f"{family.split if family else '?'}",
            "",
            f"**User:** {_truncate(prompt.text if prompt else '', 400)}",
            "",
            f"**Deliberation:** {_truncate(response.deliberation, 500)}",
            "",
            f"**Answer:** {_truncate(response.answer, 700)}",
            "",
            f"*Scores:* {review.scores if review else 'n/a'}",
            "",
        ]

    lines += ["## Samples rejected", ""]
    for decision in dropped[:3]:
        response = response_by_id.get(decision.response_id)
        prompt = prompt_by_id.get(response.prompt_id) if response else None
        lines += [
            f"### `{decision.response_id}`",
            "",
            f"**Why dropped:** " + "; ".join(decision.reasons),
            "",
            f"**User:** {_truncate(prompt.text if prompt else '', 300)}",
            "",
            f"**Answer:** {_truncate(response.answer if response else '', 400)}",
            "",
        ]
    if not dropped:
        lines.append("Nothing was dropped in this run.")
    return "\n".join(lines) + "\n"


def _situation_feature_spread(families: list[Family]) -> list[str]:
    """Show whether the generated situations actually vary along the recorded axes."""
    from pipeline.records import SITUATION_FEATURE_KEYS

    present = [f for f in families if f.situation_features]
    if not present:
        return []
    lines = ["", "### Situation-feature spread", "", "| feature | most common values |", "|---|---|"]
    for key in SITUATION_FEATURE_KEYS:
        counts = Counter(
            f.situation_features[key] for f in present if f.situation_features.get(key)
        )
        if not counts:
            continue
        top = ", ".join(f"{value} ×{n}" for value, n in counts.most_common(4))
        lines.append(f"| {key} | {top} |")
    lines.append("")
    lines.append(
        f"Recorded on {len(present)} of {len(families)} families. A feature with one dominant "
        f"value means the coverage plan is not varying it."
    )
    return lines


def _house_style_section(run_dir: Path) -> list[str]:
    siblings = latest_sibling_runs(run_dir)
    # Always include the run being reported on, even when it is not its target's latest.
    siblings[run_dir.parent.name] = run_dir
    if len(siblings) < 2:
        return [
            "Only one target has a run under `runs/`, so there is nothing to compare "
            "this target's phrasing against."
        ]
    return cross_run_style_table(siblings)


def _flag_score_conflicts(reviews: list[Review]) -> list[str]:
    """Reviews that awarded a 5 while also raising a defect flag.

    A reply cannot be an exemplar of the target's judgment and also carry a template
    shape or name its own source, so a conflict means the reviewer is not applying the
    rubric. Two flags cap the judgment score in code, so a surviving conflict puts the 5
    on a dimension the cap does not cover, which is the case worth reading.
    """
    try:
        from pipeline.review import flag_score_conflicts
    except ImportError:
        return []
    conflicts = flag_score_conflicts(reviews)
    count = conflicts.get("reviews_with_flag_and_five", 0)
    total = conflicts.get("reviews_total", len(reviews))
    if not count:
        return [
            "",
            f"Reviews awarding a 5 while raising a defect flag: **0** of {total}. "
            f"The rubric was applied consistently.",
        ]
    pairs = ", ".join(
        f"{name} ×{n}" for name, n in (conflicts.get("flag_five_pairs") or {}).items()
    )
    return [
        "",
        f"Reviews awarding a 5 while raising a defect flag: **{count}** of {total}. "
        f"That combination means the reviewer is not applying the rubric, and the score "
        f"cap did not catch it because the 5 sits on another dimension.",
        "",
        f"Conflicting pairs: {pairs}." if pairs else "",
    ]


def _reason_bucket(reason: str) -> str:
    """Group free-text reasons so the table stays short."""
    for prefix in (
        "reviewer rejected",
        "note: reviewer asked for revision but all scores pass thresholds",
        "reviewer asked for revision",
        "scores below thresholds",
        "reviewer: confident resolution",
        "cue terms found",
        "reviewer flagged cue leakage",
        "near-duplicate of",
        "eval item too close to training data",
        "note: intended divergence did not hold",
        "note: intended divergence not checked",
        "note: soft cue terms present",
        "note: explicit-mode record",
        "note: quoted or closely echoed source-text wording",
        "quoted or closely echoed source-text wording",
        "reviewer flagged archaic or translated-sounding register",
        "no reviewer verdict",
        "empty answer",
        "orphan response",
    ):
        if reason.startswith(prefix):
            return prefix
    return reason[:60]


def _mean_scores(reviews: list[Review]) -> dict[str, float]:
    if not reviews:
        return {}
    out: dict[str, float] = {}
    for name in ("fidelity", "judgment_not_terminology", "scenario_quality"):
        values = [float(r.scores.get(name) or 0) for r in reviews]
        out[name] = sum(values) / len(values)
    for name in ("cue_leakage", "confident_on_unresolved"):
        out[name] = sum(1 for r in reviews if r.scores.get(name)) / len(reviews)
    return out


def run_stage(run_dir: Path, target_id: str, pricing: dict[str, Any] | None = None) -> Path:
    """Entry point for `main.py report`."""
    text = build_report(run_dir, target_id, pricing)
    out_path = run_dir / REPORT_FILE
    out_path.write_text(text, encoding="utf-8")
    logger.info("report: wrote %s", out_path)
    return out_path
