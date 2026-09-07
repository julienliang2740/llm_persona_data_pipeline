"""Text similarity: cue terms, near-duplicates, leakage, and the per-run calibrated cut.

Pure functions plus the one embedding call, kept apart from the validation stage so the
whole calibration can be exercised offline. Similarity is measured on situations, never on
answers: generated answers share register and structure, which washes the scenario signal
out of the comparison.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from pipeline import records
from pipeline.config import RunConfig
from pipeline.model import ModelClient, ModelError
from pipeline.records import Family, Prompt, Response

logger = logging.getLogger("pipeline.similarity")


WORD = re.compile(r"[a-z0-9']+")


# -- pure checks (no network; unit-tested directly) --------------------------


def find_cue_hits(text: str, forbidden_terms: Sequence[str]) -> list[str]:
    """Return the forbidden terms that appear in `text`, case-insensitive, on word boundaries.

    Multi-word terms are matched as phrases. Substrings inside longer words never match,
    so "lion" does not fire on "million".
    """
    hits: list[str] = []
    for term in forbidden_terms:
        term = str(term).strip()
        if not term:
            continue
        pattern = r"\b" + r"\s+".join(re.escape(part) for part in term.split()) + r"\b"
        if re.search(pattern, text, re.IGNORECASE):
            hits.append(term)
    return hits


def tokenize(text: str) -> set[str]:
    return set(WORD.findall(text.lower()))


def jaccard(left: str, right: str) -> float:
    """Lexical similarity, used when embeddings are unavailable."""
    left_tokens, right_tokens = tokenize(left), tokenize(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def cosine(left: Sequence[float], right: Sequence[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


@dataclass
class DuplicateCluster:
    representative_id: str
    member_ids: list[str]
    similarity: float


def find_near_duplicates(
    item_ids: Sequence[str],
    similarity: Callable[[int, int], float],
    threshold: float,
    group_ids: Sequence[str] | None = None,
    within_group_threshold: float | None = None,
    never_compare_ids: Sequence[str | None] | None = None,
) -> tuple[dict[str, str], list[DuplicateCluster]]:
    """Greedy clustering: the first item seen is kept, later close ones point at it.

    Items in the same group (a scenario family) are compared against a separate, much
    higher threshold. Several prompts per family and reframing variants of an eval prompt
    are deliberately near-identical in situation; only a near-verbatim repeat there is a
    defect. Across families, any close pair is redundant data.

    Pairs sharing a `never_compare_ids` value are skipped entirely. That carries the
    counterfactual groups: two members of a contrastive pair are near-identical on purpose,
    and collapsing them destroys exactly the contrast they were written to draw.

    Returns (duplicate_of by item id, clusters). Deterministic in input order.
    """
    duplicate_of: dict[str, str] = {}
    representatives: list[int] = []
    clusters: dict[int, DuplicateCluster] = {}
    for index, item_id in enumerate(item_ids):
        best_index, best_score, best_threshold = None, 0.0, threshold
        for rep_index in representatives:
            if (
                never_compare_ids is not None
                and never_compare_ids[index] is not None
                and never_compare_ids[index] == never_compare_ids[rep_index]
            ):
                continue
            same_group = (
                group_ids is not None and group_ids[index] == group_ids[rep_index]
            )
            if same_group and within_group_threshold is None:
                continue
            applicable = within_group_threshold if same_group else threshold
            score = similarity(index, rep_index)
            if score >= applicable and score > best_score:
                best_index, best_score, best_threshold = rep_index, score, applicable
        if best_index is not None and best_score >= best_threshold:
            rep_id = item_ids[best_index]
            duplicate_of[item_id] = rep_id
            cluster = clusters.setdefault(
                best_index, DuplicateCluster(rep_id, [rep_id], best_score)
            )
            cluster.member_ids.append(item_id)
            cluster.similarity = max(cluster.similarity, best_score)
        else:
            representatives.append(index)
    return duplicate_of, list(clusters.values())


def max_leakage(
    eval_indices: Sequence[int],
    train_indices: Sequence[int],
    similarity: Callable[[int, int], float],
) -> dict[int, tuple[float, int | None]]:
    """For each eval item, the highest similarity to any train item and which one."""
    out: dict[int, tuple[float, int | None]] = {}
    for eval_index in eval_indices:
        best_score, best_train = 0.0, None
        for train_index in train_indices:
            score = similarity(eval_index, train_index)
            if score > best_score:
                best_score, best_train = score, train_index
        out[eval_index] = (best_score, best_train)
    return out


# -- stage -------------------------------------------------------------------


def _comparison_text(prompt: Prompt, family: Family | None) -> str:
    """What similarity is measured on: the situation, never the answer.

    Generated answers share register and structure, which washes out the scenario signal.
    Measured on round-1 data, one Catholic pair scored 0.784 on prompts alone and 0.412 once
    the answers were included, so a fixed 0.92 threshold could never fire.
    """
    seed = family.seed_situation if family else ""
    return f"{prompt.text}\n\n{seed}".strip()


def calibrated_threshold(
    scores: Sequence[float],
    sigmas: float = 3.0,
    floor: float = 0.0,
    ceiling: float = 0.98,
) -> tuple[float, float, float]:
    """Threshold at median + `sigmas` robust deviations of the pair distribution.

    An absolute cut cannot work across embedding models and traditions: the round-1 cross
    split maxima of 0.42 to 0.59 cosine were simply the embedding floor for English prose,
    nowhere near the configured 0.85.

    Median and MAD rather than mean and sd, because the duplicates are exactly the values
    that sit in the tail and they poison a mean-based cut. On eight pairs holding two
    near-duplicates at 0.81 and 0.83, mean plus three sd came to 0.98 and flagged neither;
    the robust cut lands at 0.21 and flags both. MAD is scaled by 1.4826 so that on a
    normal distribution it estimates the same quantity as the standard deviation.

    The one case it cannot resolve is a set where duplicates are not a minority: if half
    the pairs are near-identical the median sits between the two clusters and nothing is
    flagged. That is why the report always prints the closest pairs with their scores,
    whether or not any crossed the cut.

    Returns (threshold, centre, spread).
    """
    values = sorted(float(score) for score in scores)
    if len(values) < 2:
        return (min(ceiling, max(floor, 1.0)), values[0] if values else 0.0, 0.0)
    centre = _median(values)
    spread = 1.4826 * _median([abs(value - centre) for value in values])
    if spread <= 0:
        # Every pair identical to the median: fall back to the smallest gap that exists.
        gaps = [b - a for a, b in zip(values, values[1:]) if b > a]
        spread = min(gaps) if gaps else 0.0
    threshold = min(ceiling, max(floor, centre + sigmas * spread))
    return (threshold, centre, spread)


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    count = len(ordered)
    if not count:
        return 0.0
    middle = count // 2
    if count % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def all_pair_scores(
    count: int, similarity: Callable[[int, int], float]
) -> list[tuple[float, int, int]]:
    """Every distinct pair's score, for calibration and for the report's top-N table."""
    return [
        (similarity(left, right), left, right)
        for left in range(count)
        for right in range(left + 1, count)
    ]


async def _similarity_matrix(
    client: ModelClient, texts: list[str], config: RunConfig
) -> tuple[Callable[[int, int], float], str]:
    """Return a similarity function over text indices and the method actually used."""
    use_embeddings = bool(config.validation.get("use_embeddings", True))
    role = config.roles.get("embeddings")
    if use_embeddings and role is not None and role.enabled and texts:
        try:
            vectors = await client.embed(texts, role, stage="validate.embed")
            return (lambda i, j: cosine(vectors[i], vectors[j])), "embeddings"
        except (ModelError, KeyError) as error:
            logger.warning("embeddings unavailable (%s); falling back to lexical Jaccard", error)
    return (lambda i, j: jaccard(texts[i], texts[j])), "jaccard"


def _calibration(centre: float, spread: float, sigmas: float) -> dict[str, Any]:
    """Self-describing calibration record, so a report can print how the cut was reached."""
    return {
        "statistic": f"median + {sigmas:g} x robust_sd",
        "centre": round(centre, 4),
        "spread": round(spread, 4),
        "sigmas": sigmas,
    }


def _write_similarity_pairs(
    run_dir: Path,
    ordered: list[Response],
    prompts_by_id: dict[str, Prompt],
    families_by_id: dict[str, Family],
    pair_scores: list[tuple[float, int, int]],
    cross_scores: list[float],
    duplicate_threshold: float,
    leakage_threshold: float,
    method: str,
    dedupe_calibration: dict[str, float],
    leakage_calibration: dict[str, float],
    eval_indices: list[int],
    train_indices: list[int],
    similarity: Callable[[int, int], float],
    top_n: int = 50,
) -> None:
    """Write the closest pairs so the report can show them even when nothing is flagged.

    A dedupe stage that flags nothing is indistinguishable from one that is broken unless
    the distribution it saw is on record.
    """
    def describe(index: int) -> dict[str, Any]:
        response = ordered[index]
        prompt = prompts_by_id[response.prompt_id]
        family = families_by_id.get(prompt.family_id)
        return {
            "id": prompt.prompt_id,
            "family": prompt.family_id,
            "split": family.split if family else "",
        }

    rows: list[dict[str, Any]] = []
    for score, left, right in sorted(pair_scores, reverse=True)[:top_n]:
        a, b = describe(left), describe(right)
        rows.append(
            {
                "kind": "dedupe",
                "a_id": a["id"],
                "b_id": b["id"],
                "a_family": a["family"],
                "b_family": b["family"],
                "a_split": a["split"],
                "b_split": b["split"],
                "score": round(float(score), 4),
                "method": method,
                "flagged": float(score) >= duplicate_threshold,
                "threshold": round(duplicate_threshold, 4),
                "calibration": dedupe_calibration,
            }
        )
    cross_pairs = sorted(
        (
            (similarity(eval_index, train_index), eval_index, train_index)
            for eval_index in eval_indices
            for train_index in train_indices
        ),
        reverse=True,
    )[:top_n]
    for score, eval_index, train_index in cross_pairs:
        a, b = describe(eval_index), describe(train_index)
        rows.append(
            {
                "kind": "leakage",
                "a_id": a["id"],
                "b_id": b["id"],
                "a_family": a["family"],
                "b_family": b["family"],
                "a_split": a["split"],
                "b_split": b["split"],
                "score": round(float(score), 4),
                "method": method,
                "flagged": float(score) >= leakage_threshold,
                "threshold": round(leakage_threshold, 4),
                "calibration": leakage_calibration,
            }
        )
    records.write_jsonl(run_dir / records.SIMILARITY_FILE, rows)
