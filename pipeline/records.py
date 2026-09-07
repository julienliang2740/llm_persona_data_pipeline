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
USAGE_FILE = "usage.jsonl"
LOG_FILE = "log.txt"

VARIANTS = ("base", "setting_shift", "role_shift", "fiction", "roleplay", "terse")
CASE_TYPES = ("ordinary", "divergence")
SPLITS = ("train", "eval", "reserved")
MODES = ("neutral", "explicit")
# Situation features the generator fills in per family. Free text, not a rigid enum:
# they exist so the coverage plan can check spread rather than to constrain generation.
SITUATION_FEATURE_KEYS = (
    "relationship",
    "role_type",
    "harm_severity",
    "urgency",
    "public_or_private",
    "asker_state",
)


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
    situation_features: dict[str, str] = field(default_factory=dict)
    reserved_reason: str = ""
    mode: str = "neutral"  # neutral | explicit, inherited by the family's prompts

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


@dataclass
class BaselineAnswer:
    """The un-finetuned base model's answer to the same prompt."""

    prompt_id: str
    base_model: str
    text: str
    usage: dict[str, Any] = field(default_factory=dict)


@dataclass
class DivergenceVerdict:
    """Judge comparing a candidate response with the baseline answer."""

    prompt_id: str
    judge_model: str
    diverges: bool
    kind: str  # action | reasons | both | none
    explanation: str
    presented_first: str = ""  # candidate | baseline, recorded for audit


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
