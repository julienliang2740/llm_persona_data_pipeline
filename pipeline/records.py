"""Record types for every pipeline artifact, plus JSONL read/write.

Every stage reads and writes JSONL under runs/<target_id>/<run_id>/ so that any
artifact can be inspected on its own and any stage can be re-run alone.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Type, TypeVar

# Artifact file names inside a run directory.
FAMILIES_FILE = "families.jsonl"
PROMPTS_FILE = "prompts.jsonl"
RESPONSES_FILE = "responses.jsonl"
BASELINE_FILE = "baseline.jsonl"
REVIEWS_FILE = "reviews.jsonl"
DIVERGENCE_FILE = "divergence.jsonl"
DECISIONS_FILE = "decisions.jsonl"
SIMILARITY_FILE = "similarity_pairs.jsonl"
STRONG_BASELINE_FILE = "baseline_strong.jsonl"
REVIEWS_SECOND_FILE = "reviews_second.jsonl"
USAGE_FILE = "usage.jsonl"
LOG_FILE = "log.txt"

VARIANTS = ("base", "setting_shift", "role_shift", "fiction", "roleplay", "terse")
CASE_TYPES = ("ordinary", "divergence")
SPLITS = ("train", "eval", "reserved")
MODES = ("neutral", "explicit")

# Situation features are closed enums so the coverage plan can enforce a spread and the
# structural dedupe key is comparable across families. Free text goes in `note`.
HARM_SEVERITY = ("minor", "serious", "grave")
URGENCY = ("none", "days", "now")
PUBLIC_OR_PRIVATE = ("private", "semi_public", "public")
ROLE_TYPE = ("no_authority", "peer", "holds_authority", "institution")
# What the asker wants from the exchange. Planned per slot, not chosen by the generator,
# because a run of nothing but "conflicted" askers is the failure mode we keep hitting.
ASKER_STANCE = (
    "conflicted",
    "decided_wants_permission",
    "angry_wants_to_win",
    "defensive",
    "transactional",
)
ASKER_STANCE_MIX = {
    "conflicted": 0.40,
    "decided_wants_permission": 0.20,
    "angry_wants_to_win": 0.15,
    "defensive": 0.15,
    "transactional": 0.10,
}
#: role_type needs an enforced mix for the same reason asker_stance does: left to fall out
#: of a nested loop it never advanced past the first value in a whole round of pilots.
ROLE_TYPE_MIX = {
    "no_authority": 0.45,
    "peer": 0.25,
    "holds_authority": 0.25,
    "institution": 0.05,
}

SITUATION_FEATURE_ENUMS = {
    "harm_severity": HARM_SEVERITY,
    "urgency": URGENCY,
    "public_or_private": PUBLIC_OR_PRIVATE,
    "role_type": ROLE_TYPE,
}
SITUATION_FEATURE_KEYS = tuple(SITUATION_FEATURE_ENUMS) + ("relationship", "note")

# What a user message is actually asking for. Two prompts on one family must differ here,
# not merely in length.
QUESTION_KINDS = ("what_to_do", "how_to_say_it", "was_my_decision_right")

# Kinds of baseline answer kept for the three-way divergence comparison.
BASELINE_KINDS = ("base", "strong_generic")


def short_id(prefix: str, *parts: str) -> str:
    """Deterministic short id, so re-running a stage reuses the same ids."""
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{digest}"


@dataclass
class Family:
    """A scenario family: the unit of train/eval splitting and of leakage checks."""

    family_id: str
    target_id: str
    domain: str
    tradeoff_ids: list[str]
    principle_ids: list[str]
    case_type_intent: str  # ordinary | divergence
    seed_situation: str
    why_it_is_hard: str
    split: str  # train | eval | reserved
    source_passage_ids: list[str] = field(default_factory=list)
    generator_model: str = ""
    spec_version: str = ""
    # Members of one counterfactual group are the same situation with exactly one
    # morally relevant fact changed. They must never be split apart or deduped
    # against each other: the contrast is the point.
    counterfactual_group_id: str | None = None
    varied_fact: str = ""
    #: Which situation feature this pair varies. Round 2 varied harm severity every time.
    varied_axis: str = ""
    situation_features: dict[str, str] = field(default_factory=dict)
    reserved_reason: str = ""
    mode: str = "neutral"  # neutral | explicit, inherited by the family's prompts
    # Position in the coverage plan. Retries refill unfilled slot indices, never a
    # count-based tail slice, so a lost batch cannot silently change the plan.
    slot_index: int = -1
    # Which divergence hypothesis this family was written to instantiate. Required on
    # divergence-intent families so hypothesis coverage is measurable.
    divergence_hypothesis_id: str = ""
    asker_stance: str = ""
    institution: str = ""
    layers_generated: list[str] = field(default_factory=list)

    @property
    def structural_key(self) -> str:
        """Plan-time uniqueness key: two families in one domain must not share it."""
        features = self.situation_features or {}
        tradeoff = self.tradeoff_ids[0] if self.tradeoff_ids else ""
        return "|".join(
            [tradeoff, features.get("role_type", ""), features.get("harm_severity", ""), self.domain]
        )

    @property
    def split_group_id(self) -> str:
        """The unit the train/eval split actually operates on."""
        return self.counterfactual_group_id or self.family_id


@dataclass
class Prompt:
    """A user message. Uncued: no tradition name, no persona instruction."""

    prompt_id: str
    family_id: str
    variant: str  # base | setting_shift | role_shift | fiction | roleplay | terse
    text: str
    case_type: str  # ordinary | divergence
    # explicit prompts may name the tradition; the cue check is skipped for them.
    mode: str = "neutral"  # neutral | explicit
    register: str = ""  # long_detailed | short_blunt | mid_neutral | anxious | defensive
    question_kind: str = ""  # what_to_do | how_to_say_it | was_my_decision_right


@dataclass
class Response:
    """Generator output for one prompt. `hidden` never reaches the user turn."""

    response_id: str
    prompt_id: str
    deliberation: str
    answer: str
    hidden: dict[str, Any] = field(default_factory=dict)
    generator_model: str = ""
    usage: dict[str, Any] = field(default_factory=dict)
    revise_rounds: int = 0
    mode: str = "neutral"  # neutral | explicit, copied from the prompt
    # 2-4 sentences naming the concrete choice this prompt turns on. Leads the exported
    # grading key, so it is written by the same model that wrote the answer. Plain prose:
    # no principle ids and no passage ids, because a judge sees it verbatim.
    expected_actions: str = ""
    # For a family in a counterfactual group: what the varied fact changes about the right
    # answer here. Only the writer knows this, and the grading key cannot state it otherwise.
    varied_fact_effect: str = ""


@dataclass
class Review:
    """Reviewer critique of one response."""

    review_id: str
    response_id: str
    reviewer_model: str
    scores: dict[str, Any]
    issues: list[str]
    verdict: str  # accept | revise | reject
    rationale: str
    # A verbatim sentence from the answer that shows the target's judgment, and the name
    # of the move it makes. An empty quote caps judgment_not_terminology at 3.
    judgment_evidence_quote: str = ""
    judgment_move: str = ""
    # Which of the spec's signature_moves the answer shows.
    signature_moves_present: list[str] = field(default_factory=list)
    # Observations that must not touch the fidelity score, e.g. modern legal duties the
    # tradition never formulated.
    notes: list[str] = field(default_factory=list)


@dataclass
class BaselineAnswer:
    """An answer to compare the candidate against.

    `kind` is "base" for the un-finetuned 7B checkpoint being fine-tuned, and
    "strong_generic" for a strong model answering with no target specification at the
    same length budget. The three-way comparison separates a value difference from a
    capability difference.
    """

    prompt_id: str
    base_model: str
    text: str
    usage: dict[str, Any] = field(default_factory=dict)
    kind: str = "base"
    finish_reason: str = ""

    @property
    def truncated(self) -> bool:
        """A cut-off answer cannot be compared: it may not have reached its recommendation."""
        return self.finish_reason == "length" or not self.text.strip().endswith((".", "!", "?", '"'))


@dataclass
class DivergenceVerdict:
    """Judge comparing the candidate, the 7B base answer and a strong generic answer.

    The third answer is what separates "the target says something a generic assistant
    would not" from "the candidate is simply written by a better model".
    """

    prompt_id: str
    judge_model: str
    diverges: bool
    kind: str  # action | reasons | both | none
    explanation: str
    presented_first: str = ""  # candidate | baseline, recorded for audit
    # Each reply's recommended action, stated verbatim by the judge before it decides.
    candidate_action: str = ""
    base_action: str = ""
    generic_action: str = ""
    closer_to: str = ""  # generic | candidate | equidistant
    # The three pairwise comparisons the report needs, kept apart because "the candidate
    # differs from the weak 7B answer" and "it differs from a strong generic answer" are
    # different claims, and only the second is evidence of a value difference.
    diverges_vs_base: bool = False
    diverges_vs_generic: bool = False
    generic_differs_from_base: bool = False
    # The sentence a generic assistant would not have written. Empty forces diverges=false.
    value_named: str = ""
    # The closest sentence in the no-specification reply. When it makes the same claim, the
    # specification did not produce the difference and the source is capability, not value.
    generic_echo: str = ""
    generic_makes_same_claim: bool = False
    # Which label the candidate was shown under, recorded so a run can be audited for
    # position bias. The judge sees a different shuffle for every prompt.
    label_order: str = ""
    divergence_source: str = ""  # value | capability | stipulated | none
    hypothesis_id: str = ""
    unverified_reason: str = ""  # set when a compared answer was truncated


@dataclass
class Decision:
    """Final keep/drop for one response, combining every validation check."""

    response_id: str
    keep: bool
    reasons: list[str] = field(default_factory=list)
    final_case_type: str = "ordinary"
    duplicate_of: str | None = None
    max_leakage: float | None = None
    # confirmed | not_confirmed | unverified | not_applicable
    divergence_status: str = "not_applicable"
    # action | reasons | both | none, from the divergence judge
    divergence_kind: str = ""
    # value | capability | stipulated | none. Only "value" counts as real divergence.
    divergence_source: str = ""
    # cue_policy.soft_terms that appeared: reported, never a reason to drop
    soft_cue_hits: list[str] = field(default_factory=list)


T = TypeVar("T")


def write_jsonl(path: Path, records: Iterable[Any]) -> int:
    """Overwrite `path` with one JSON object per record. Returns the count."""
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(to_dict(record), ensure_ascii=False) + "\n")
            count += 1
    return count


def append_jsonl(path: Path, record: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(to_dict(record), ensure_ascii=False) + "\n")


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{line_number} is not valid JSON: {error}") from None


def read_jsonl(path: Path, record_type: Type[T] | None = None) -> list[T] | list[dict[str, Any]]:
    """Read a JSONL artifact. With `record_type`, build dataclasses and drop unknown keys."""
    rows = list(iter_jsonl(path))
    if record_type is None:
        return rows
    known = {f.name for f in fields(record_type)}  # type: ignore[arg-type]
    return [record_type(**{k: v for k, v in row.items() if k in known}) for row in rows]


def to_dict(record: Any) -> dict[str, Any]:
    if is_dataclass(record) and not isinstance(record, type):
        return asdict(record)
    if isinstance(record, dict):
        return record
    raise TypeError(f"Cannot serialise {type(record).__name__} to JSONL.")


def index_by(records: Iterable[Any], attribute: str) -> dict[str, Any]:
    return {getattr(record, attribute): record for record in records}
