"""Report tables that are computed rather than counted.

Cross-target house style, coverage of the plan's axes, the closest scenario pairs and
the three-way divergence rates. They live here because they read either sibling run
directories or the spec snapshot rather than the run's own counts, and because
report.py is long enough already.

The house-style measure is the point of the module. If four traditions that disagree
about ethics produce answers built from the same four-word phrases, the corpora differ
in scenario nouns and not in judgment. That is measurable without a model: count the
four-grams appearing in more than 30% of one target's answers, and see how many targets
they clear that bar in.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from pipeline import records
from pipeline.records import (
    ASKER_STANCE_MIX,
    SIMILARITY_FILE,
    Decision,
    DivergenceVerdict,
    Family,
    Prompt,
)

NGRAM_SIZE = 4
# A phrase in fewer than three answers out of ten is not this target's habit.
PRESENCE_THRESHOLD = 0.30
# A second, looser bar. At pilot sizes (about 20 responses) almost no four-gram clears
# 30%, so the strict score cannot move between runs and the loose one can.
LOOSE_THRESHOLD = 0.15
WORD = re.compile(r"[a-z']+")


def _ngrams(text: str, size: int = NGRAM_SIZE) -> set[str]:
    """The distinct n-grams in one answer. Presence per answer, never frequency."""
    words = WORD.findall(text.lower())
    return {" ".join(words[i : i + size]) for i in range(len(words) - size + 1)}


def answer_texts(run_dir: Path) -> list[str]:
    """The assistant text of every response: deliberation and answer, as exported.

    Both halves count. The instructed deliberation shape is where round 1's repetition
    was worst, and it is trained on exactly like the answer.
    """
    texts = []
    for row in records.iter_jsonl(run_dir / records.RESPONSES_FILE):
        text = f"{row.get('deliberation', '')}\n{row.get('answer', '')}".strip()
        if text:
            texts.append(text)
    return texts


def presence_shares(texts: list[str]) -> dict[str, float]:
    """For each n-gram, the share of answers it appears in at least once."""
    if not texts:
        return {}
    counts: Counter[str] = Counter()
    for text in texts:
        counts.update(_ngrams(text))
    return {phrase: count / len(texts) for phrase, count in counts.items()}


def latest_sibling_runs(run_dir: Path) -> dict[str, Path]:
    """The most recent run of every target under the same runs/ directory.

    The house-style comparison is only interesting across targets, and the report has no
    way to be told about other runs, so it finds them.
    """
    runs_root = run_dir.parent.parent
    found: dict[str, Path] = {}
    if not runs_root.is_dir():
        return found
    for target_dir in sorted(runs_root.iterdir()):
        if not target_dir.is_dir():
            continue
        candidates = [
            candidate
            for candidate in sorted(target_dir.iterdir())
            if candidate.is_dir() and (candidate / records.RESPONSES_FILE).exists()
        ]
        if candidates:
            found[target_dir.name] = candidates[-1]
    return found


def cross_run_style_table(run_dirs: dict[str, Path], limit: int = 15) -> list[str]:
    """Markdown table of the four-grams that several targets' answers share.

    `run_dirs` maps a label (normally the target id) to a run directory.
    """
    shares_by_label = {label: presence_shares(answer_texts(path)) for label, path in run_dirs.items()}
    shares_by_label = {label: shares for label, shares in shares_by_label.items() if shares}
    if not shares_by_label:
        return []
    labels = sorted(shares_by_label)

    frequent = {
        phrase
        for shares in shares_by_label.values()
        for phrase, share in shares.items()
        if share >= PRESENCE_THRESHOLD
    }
    if not frequent:
        return [
            "",
            f"No four-gram appears in {PRESENCE_THRESHOLD:.0%} or more of any target's answers.",
        ]

    def rank(phrase: str) -> tuple[int, float]:
        above = sum(1 for label in labels if shares_by_label[label].get(phrase, 0.0) >= PRESENCE_THRESHOLD)
        mean = sum(shares_by_label[label].get(phrase, 0.0) for label in labels) / len(labels)
        return (above, mean)

    ordered = sorted(frequent, key=rank, reverse=True)[:limit]
    header = "| four-gram | targets ≥30% | " + " | ".join(labels) + " |"
    lines = [
        "",
        f"Share of each target's answers containing the phrase, over {len(labels)} runs: "
        + ", ".join(f"`{label}` ({len(answer_texts(run_dirs[label]))} responses)" for label in labels),
        "",
        header,
        "|---|---|" + "---|" * len(labels),
    ]
    for phrase in ordered:
        above, _ = rank(phrase)
        cells = " | ".join(f"{shares_by_label[label].get(phrase, 0.0):.0%}" for label in labels)
        lines.append(f"| {phrase} | {above} | {cells} |")
    lines += [
        "",
        "A phrase in the right-hand columns for every target is house style, not the "
        "target's judgment: the same sentence shape survived four different specifications.",
        "",
    ]
    lines += _shared_style_score(shares_by_label, labels)
    return lines


def _score_at(
    shares_by_label: dict[str, dict[str, float]], labels: list[str], threshold: float
) -> str:
    """One line: how much of each target's habitual phrasing is shared with the others."""
    habitual = {
        label: {phrase for phrase, share in shares_by_label[label].items() if share >= threshold}
        for label in labels
    }
    overlaps = []
    for index, first in enumerate(labels):
        for second in labels[index + 1 :]:
            union = habitual[first] | habitual[second]
            if union:
                overlaps.append(len(habitual[first] & habitual[second]) / len(union))
    everything: set[str] = set().union(*habitual.values()) if habitual else set()
    shared_two = sum(
        1 for phrase in everything if sum(1 for label in labels if phrase in habitual[label]) >= 2
    )
    mean_overlap = sum(overlaps) / len(overlaps) if overlaps else 0.0
    per_target = ", ".join(f"{label} {len(habitual[label])}" for label in labels)
    return (
        f"- at ≥{threshold:.0%}: {per_target}; **{shared_two}** shared by two or more targets; "
        f"mean pairwise overlap **{mean_overlap:.2f}**"
    )


def _shared_style_score(shares_by_label: dict[str, dict[str, float]], labels: list[str]) -> list[str]:
    """The figures to compare between a round-1 and a round-2 run.

    A response prompt that stops dictating a sentence shape should drive the overlap
    down. Reported at two bars because at pilot sizes almost nothing clears 30%, so the
    stricter number cannot move and the looser one can.
    """
    return [
        "Count of habitual four-grams per target, and how much of that habit is shared:",
        "",
        _score_at(shares_by_label, labels, PRESENCE_THRESHOLD),
        _score_at(shares_by_label, labels, LOOSE_THRESHOLD),
    ]


# -- coverage, similarity and divergence tables ------------------------------


def _spec_snapshot(run_dir: Path) -> dict[str, Any]:
    """The spec copy export leaves in the run dir, when there is one.

    It lets the report say which of the exercised tradeoffs were the unresolved ones
    without the report needing a loaded target.
    """
    path = run_dir / "spec.yaml"
    if not path.exists():
        return {}
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _count_table(title: str, counts: Counter[str], total: int, label: str) -> list[str]:
    lines = ["", f"**{title}**", "", f"| {label} | families | share |", "|---|---|---|"]
    if not counts:
        lines.append(f"| (none recorded) | 0 | - |")
        return lines
    for value, count in counts.most_common():
        lines.append(f"| {value} | {count} | {count/total:.0%} |" if total else f"| {value} | {count} | - |")
    return lines


def coverage_tables(
    run_dir: Path,
    families: list[Family],
    prompts: list[Prompt],
    hypothesis_coverage_floor: float = 1.0,
) -> list[str]:
    """What the run actually exercised: tradeoffs, hypotheses, asker stance, eval mix.

    Round 1 had no way to see that two targets exercised none of their unresolved
    tradeoffs and that one eval set held no divergence cases at all.
    """
    if not families:
        return []
    spec = _spec_snapshot(run_dir)
    unresolved_ids = {
        str(tradeoff.get("id"))
        for tradeoff in (spec.get("tradeoffs") or [])
        if tradeoff.get("unresolved")
    }
    all_tradeoff_ids = [str(t.get("id")) for t in (spec.get("tradeoffs") or []) if t.get("id")]
    hypothesis_ids = [str(h.get("id")) for h in (spec.get("divergence_hypotheses") or []) if h.get("id")]

    lines = ["", "### Coverage"]

    tradeoff_counts: Counter[str] = Counter()
    for family in families:
        for tradeoff_id in family.tradeoff_ids:
            name = f"{tradeoff_id} (unresolved)" if tradeoff_id in unresolved_ids else tradeoff_id
            tradeoff_counts[name] += 1
    lines += _count_table("Tradeoffs exercised", tradeoff_counts, len(families), "tradeoff")
    if all_tradeoff_ids:
        used = {tid for family in families for tid in family.tradeoff_ids}
        missed_unresolved = sorted(unresolved_ids - used)
        unknown = sorted(used - set(all_tradeoff_ids))
        lines.append("")
        lines.append(
            f"{len(used & set(all_tradeoff_ids))} of {len(all_tradeoff_ids)} spec tradeoffs reached; "
            f"unresolved tradeoffs never exercised: "
            + (", ".join(f"`{tid}`" for tid in missed_unresolved) if missed_unresolved else "none")
        )
        if unknown:
            # A family carrying an id the spec does not define renders as no tradeoff at
            # all in the response prompt, so it has to be visible in the report.
            lines.append("")
            lines.append(
                "Tradeoff ids on families that the specification does not define: "
                + ", ".join(f"`{tid}`" for tid in unknown)
            )

    hypothesis_counts = Counter(
        getattr(family, "divergence_hypothesis_id", "") or "(none assigned)"
        for family in families
        if family.case_type_intent == "divergence"
    )
    divergence_families = sum(1 for f in families if f.case_type_intent == "divergence")
    lines += _count_table(
        "Divergence hypotheses instantiated", hypothesis_counts, divergence_families, "hypothesis"
    )
    if hypothesis_ids:
        used = {getattr(f, "divergence_hypothesis_id", "") for f in families}
        missed = sorted(set(hypothesis_ids) - used)
        lines.append("")
        lines.append(
            "Hypotheses with no family: "
            + (", ".join(f"`{h}`" for h in missed) if missed else "none")
        )
        # The floor is configured per 100 families, so state what it means at this size.
        wanted = max(1, round(len(families) * hypothesis_coverage_floor / 100.0))
        thin = sorted(
            hypothesis
            for hypothesis in hypothesis_ids
            if hypothesis_counts.get(hypothesis, 0) < wanted
        )
        lines.append(
            f"Coverage floor is {hypothesis_coverage_floor:g} family per hypothesis per 100 "
            f"families, so {wanted} at this size ({len(families)} families). "
            + (
                f"{len(thin)} of {len(hypothesis_ids)} fall short: "
                + ", ".join(f"`{h}`" for h in thin[:6])
                if thin
                else "Every hypothesis meets it."
            )
        )

    stance_counts = Counter(
        getattr(family, "asker_stance", "")
        or (family.situation_features or {}).get("asker_stance", "")
        or "(not recorded)"
        for family in families
    )
    lines += _stance_table(stance_counts, len(families))

    lines += _eval_composition(run_dir, families, prompts)
    return lines


def _stance_table(stance_counts: Counter[str], total: int) -> list[str]:
    """Realised asker stance against the mix the plan asked for.

    The planned proportions exist because a run of nothing but conflicted askers is the
    failure mode round 1 kept hitting, so the report has to show both columns.
    """
    lines = [
        "",
        "**Asker stance**",
        "",
        "| stance | families | share | planned |",
        "|---|---|---|---|",
    ]
    names = sorted(set(stance_counts) | set(ASKER_STANCE_MIX))
    for name in names:
        count = stance_counts.get(name, 0)
        share = f"{count/total:.0%}" if total else "-"
        planned = f"{ASKER_STANCE_MIX[name]:.0%}" if name in ASKER_STANCE_MIX else "-"
        lines.append(f"| {name} | {count} | {share} | {planned} |")
    return lines


def _eval_composition(run_dir: Path, families: list[Family], prompts: list[Prompt]) -> list[str]:
    """Planned versus exported evaluation mix. The two diverge when drops follow the split."""
    eval_families = [f for f in families if f.split == "eval"]
    if not eval_families:
        return []
    planned = Counter(f.case_type_intent for f in eval_families)
    exported_rows = list(records.iter_jsonl(run_dir / "eval.jsonl"))
    exported = Counter(str(row.get("case_type", "?")) for row in exported_rows)
    variants = Counter(str(row.get("variant", "?")) for row in exported_rows)
    lines = [
        "",
        "**Evaluation composition**",
        "",
        "| case type | families planned | rows exported |",
        "|---|---|---|",
    ]
    for case_type in sorted(set(planned) | set(exported)):
        lines.append(f"| {case_type} | {planned.get(case_type, 0)} | {exported.get(case_type, 0)} |")
    lines += [
        "",
        f"Eval rows by prompt variant: "
        + (", ".join(f"{name} ×{n}" for name, n in sorted(variants.items())) or "none")
        + ".",
        "A mix that shifts between the two columns means drops are being applied after the "
        "split, so the eval set no longer measures what the plan asked for.",
    ]
    return lines


def _calibration_line(row: dict[str, Any]) -> str:
    """State the cut the way validate computed it, from the row's own self-description."""
    calibration = row.get("calibration") or {}
    threshold = row.get("threshold")
    statistic = calibration.get("statistic", "an unrecorded statistic")
    centre, spread = calibration.get("centre"), calibration.get("spread")
    cut = f"{float(threshold):.3f}" if threshold is not None else "not recorded"
    if centre is None or spread is None:
        return f"Flagged above **{cut}**, from {statistic}."
    return (
        f"Flagged above **{cut}**, from {statistic} over the whole pair distribution "
        f"(centre {float(centre):.3f}, spread {float(spread):.3f})."
    )


def top_similarity_pairs(run_dir: Path, decisions: list[Decision], limit: int = 10) -> list[str]:
    """The closest pairs with their scores, whether or not any crossed a threshold.

    Round 1 printed "none above the threshold" on a run holding a 0.784 near-repeat, so
    the ranking is shown unconditionally and the cut is stated next to it.
    """
    rows = list(records.iter_jsonl(run_dir / SIMILARITY_FILE))
    lines = ["", "### Closest pairs", ""]
    if not rows:
        # The decisions record only each eval response's single closest training row, and
        # the leakage section below already prints that, so name what is missing instead
        # of printing it twice.
        recorded = sum(1 for decision in decisions if decision.max_leakage is not None)
        lines.append(
            f"This run kept no `{SIMILARITY_FILE}`, so the pair distribution the calibrated "
            f"threshold is drawn from was not recorded. The leakage section below still shows "
            f"the closest training row for each of the {recorded} scored eval responses; it "
            f"covers no train-to-train or eval-to-eval pair."
        )
        return lines

    titles = {
        "dedupe": "Within the corpus, any two prompts",
        "leakage": "Across the split, an eval prompt against a training prompt",
    }
    for kind in sorted({str(row.get("kind", "")) for row in rows}):
        subset = sorted(
            (row for row in rows if row.get("kind") == kind),
            key=lambda row: float(row.get("score") or 0.0),
            reverse=True,
        )
        if not subset:
            continue
        lines += [
            f"**{titles.get(kind, kind)}** ({kind})",
            "",
            _calibration_line(subset[0]),
            "",
            "| a | b | score | families | splits | flagged |",
            "|---|---|---|---|---|---|",
        ]
        for row in subset[:limit]:
            lines.append(
                f"| `{row.get('a_id', '?')}` | `{row.get('b_id', '?')}` "
                f"| {float(row.get('score') or 0.0):.3f} "
                f"| {row.get('a_family', '?')} / {row.get('b_family', '?')} "
                f"| {row.get('a_split', '?')} / {row.get('b_split', '?')} "
                f"| {'yes' if row.get('flagged') else 'no'} |"
            )
        lines.append("")
    lines.append(
        f"Scored with {rows[0].get('method', 'an unrecorded method')}. The ranking is printed "
        f"whether or not anything crossed the cut, because a corpus can hold a near-repeat "
        f"that no threshold on this distribution would reach."
    )
    return lines


def three_way_divergence(
    verdicts: list[DivergenceVerdict], prompt_by_id: dict[str, Prompt]
) -> list[str]:
    """Candidate against the 7B base and against a strong generic answer, per family.

    A candidate that differs from the 7B base but not from a strong generic answer has
    shown better writing, not the target's values.
    """
    if not verdicts:
        return []
    by_family: dict[str, list[DivergenceVerdict]] = {}
    for verdict in verdicts:
        prompt = prompt_by_id.get(verdict.prompt_id)
        by_family.setdefault(prompt.family_id if prompt else verdict.prompt_id, []).append(verdict)
    total = len(by_family)

    def share(count: int) -> str:
        return f"{count/total:.0%}" if total else "-"

    def families_where(attribute: str) -> int:
        return sum(
            1
            for group in by_family.values()
            if any(bool(getattr(verdict, attribute, False)) for verdict in group)
        )

    def families_with_source(source: str, require_all: bool = False) -> int:
        """Families whose judged prompts carry `source`.

        With `require_all`, every judged prompt in the family must carry it. That is the
        conservative reading and the one worth quoting: the second prompt is the same
        situation reworded, so a value that survives only one rendering is a value the
        wording produced rather than the target.
        """
        quantifier = all if require_all else any
        return sum(
            1
            for group in by_family.values()
            if group
            and quantifier(
                getattr(verdict, "divergence_source", "") == source for verdict in group
            )
        )

    # A run judged before the three-way comparison existed leaves every three-way field
    # at its default, which is not the same as the judge having found no difference.
    three_way_recorded = any(
        getattr(verdict, "generic_action", "")
        or getattr(verdict, "closer_to", "")
        or verdict.diverges_vs_generic
        or verdict.generic_differs_from_base
        for verdict in verdicts
    )
    candidate_vs_base = families_where("diverges_vs_base") or sum(
        1 for group in by_family.values() if any(verdict.diverges for verdict in group)
    )
    candidate_vs_generic = families_where("diverges_vs_generic")
    if three_way_recorded and not candidate_vs_generic:
        # An older shape recorded only `closer_to`: a candidate the judge placed nearer
        # the generic answer has not departed from it.
        candidate_vs_generic = sum(
            1
            for group in by_family.values()
            if any(getattr(v, "closer_to", "") in ("candidate", "equidistant") for v in group)
        )
    generic_vs_base = families_where("generic_differs_from_base")
    value_attributed = families_with_source("value", require_all=True)
    value_any_prompt = families_with_source("value")
    stipulated = families_with_source("stipulated")

    lines = [
        "",
        "### Three-way comparison, per family",
        "",
        f"{total} families with a judged prompt.",
        "",
        "| comparison | families differing | share |",
        "|---|---|---|",
        f"| candidate vs 7B base | {candidate_vs_base} | {share(candidate_vs_base)} |",
    ]
    for name, count in (
        ("candidate vs strong generic", candidate_vs_generic),
        ("strong generic vs 7B base", generic_vs_base),
    ):
        lines.append(
            f"| {name} | {count} | {share(count)} |"
            if three_way_recorded
            else f"| {name} | not recorded | - |"
        )
    lines += [
        "",
        f"- attributed to a **value** the target holds, on EVERY judged prompt in the "
        f"family: **{value_attributed}** ({share(value_attributed)})",
        f"- the same on at least one prompt: **{value_any_prompt}** "
        f"({share(value_any_prompt)}), a ceiling rather than a result",
        f"- attributed to something the prompt stipulated: **{stipulated}** ({share(stipulated)})",
        "",
        "The first line is the number worth quoting. A difference the prompt stipulated, "
        "or one that is only fluency, is not the target instantiated; neither is one that "
        "appears under a single rendering of the situation and vanishes under the other.",
    ]
    return lines
