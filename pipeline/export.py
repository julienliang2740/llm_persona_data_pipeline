"""Export stage: family-based split, sft_train.jsonl, eval.jsonl, manifest.json.

Splitting is by family, never by response, so paraphrases of one situation cannot
straddle train and eval. Reserved families go nowhere: they are held for later.

The grading key written into eval.jsonl has to be usable by a judge that never sees the
reference answer, so it leads with the concrete choice this prompt turns on and, for a
member of a counterfactual pair, says what the varied fact changes.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from pipeline import records
from pipeline.config import REPO_ROOT, RunConfig
from pipeline.model import format_cost, summarise_usage
from pipeline.records import Decision, Family, Prompt, Response, Review
from pipeline.target import KEY_PASSAGES_SUFFIX, TargetSpec, normalise_passage_ids
from pipeline.validate import find_cue_hits

logger = logging.getLogger("pipeline.export")

SFT_FILE = "sft_train.jsonl"
EVAL_FILE = "eval.jsonl"
MANIFEST_FILE = "manifest.json"
# Copies of the two inputs that decide what a run contains, so config_hash and
# spec_hash can be checked against their sources long after the run.
CONFIG_COPY_FILE = "config.resolved.yaml"
SPEC_COPY_FILE = "spec.yaml"

# Drop reasons that must still remove an evaluation row: a rejected, cue-leaking,
# duplicated or empty answer is not a usable reference. Everything else -- in practice
# the score cut -- keeps the row, and the scores travel with it in meta, so reviewer
# strictness cannot silently shrink one target's eval set (generalisation F8).
HARD_EVAL_DROP_PREFIXES = (
    "no reviewer verdict",
    "reviewer rejected",
    # The rewrite round already ran and the reviewer still wants changes, so this is a
    # failed response rather than a strict score (B1), and it cannot serve as a reference.
    "reviewer still asks for revision after a rewrite",
    # A reference answer in a fixed template shape teaches a judge the wrong target.
    "reviewer: fixed template shape rather than a shape this case needed",
    "cue terms found",
    "reviewer flagged cue leakage",
    "reviewer flagged archaic or translated-sounding register",
    "quoted or closely echoed source-text wording",
    "near-duplicate of",
    "eval item too close to training data",
    "empty answer",
    "orphan response",
)

# What an eval row survives: the score cut, and nothing else. Listed for the report and
# so a reader of this module can see the exemption rather than infer it from the above.
SOFT_EVAL_DROP_PREFIXES = (
    "scores below thresholds",
    "reviewer: confident resolution of an unresolved tradeoff",
)

# "[Name]", "[date]", "[one concrete factual correction]": a template the writer left
# unfilled. Round-1 Protestant answers carried nine distinct ones.
BRACKETED = re.compile(r"\[([^\[\]\n]{1,60})\]")

# Failure modes come in three shapes across the specs: a third-person verb ("treats X as
# settled"), a gerund ("protecting a vulnerable person's feelings"), and a bare noun
# phrase ("sympathetic language with no action attached"). One template cannot carry all
# three, which is how round 1 produced "FAIL if the reply protecting a vulnerable...".
_GERUND = re.compile(r"^[a-z]+ing$")

# Enough for one PASS and one FAIL on five principles plus two review notes.
MAX_PASS_FAIL_NOTES = 12


def render_assistant_message(response: Response) -> str:
    """The one fixed rendering used for every training row: deliberation, blank line, answer."""
    deliberation = response.deliberation.strip()
    answer = response.answer.strip()
    if not deliberation:
        return answer
    return f"{deliberation}\n\n{answer}"


# -- grading key ------------------------------------------------------------


def _tidy(phrase: str) -> str:
    """One spacing and punctuation convention for spec prose pasted into a note."""
    text = " ".join(str(phrase).split()).rstrip(". ")
    if text[:1].isupper() and not text[:2].isupper():
        # Lowercase an ordinary sentence start, but leave "CEO", "HR", "I" alone.
        text = text[0].lower() + text[1:]
    return text


def _first_word(text: str) -> str:
    """The first word that decides the phrase's grammar, skipping a leading adverb."""
    words = [w.strip("\"'“”‘’(),").lower() for w in text.split()]
    words = [w for w in words if w]
    if words and words[0].endswith("ly") and len(words) > 1:
        return words[1]
    return words[0] if words else ""


def failure_note(phrase: str) -> str:
    """A grammatical FAIL line for any of the three shapes a failure mode comes in."""
    text = _tidy(phrase)
    if not text:
        return ""
    head = _first_word(text)
    if _GERUND.match(head):
        return f"FAIL if the reply ends up {text}."
    if head.endswith("s") and not head.endswith("ss") and len(head) > 3:
        return f"FAIL if the reply {text}."
    return f"FAIL if the reply shows {text}."


def pass_note(phrase: str) -> str:
    """Positive indicators are written as third-person verb phrases in every spec."""
    text = _tidy(phrase)
    return f"PASS if the reply {text}." if text else ""


def _writer_field(response: Response, name: str) -> str:
    """Read a writer-supplied field from the record or, for older runs, from `hidden`."""
    value = getattr(response, name, "") or response.hidden.get(name) or ""
    return " ".join(str(value).split())


def derive_grading_key(
    spec: TargetSpec,
    response: Response,
    review: Review | None,
    family: Family | None = None,
    case_type: str = "",
) -> tuple[str, list[str]]:
    """Build expected_behavior and pass_fail_notes from the writer, the spec and the review.

    No extra model call. The writer already recorded the concrete choice this prompt
    turns on and which principles it applied; the specification already records what
    honouring and failing each principle looks like.
    """
    sentences: list[str] = []
    expected_actions = _writer_field(response, "expected_actions")
    if expected_actions:
        # Leads the key: a judge needs the situation-specific choice before the
        # tradition's general commitments, not 500 words of pasted principle text.
        sentences.append(expected_actions)

    if family is not None and family.counterfactual_group_id and family.varied_fact:
        varied = " ".join(str(family.varied_fact).split()).rstrip(". ")
        effect = _writer_field(response, "varied_fact_effect")
        if not effect:
            effect = (
                "A reply that would be equally correct for the paired case has not "
                "engaged this fact."
            )
        sentences.append(
            f"This case is one of a pair that differ in exactly one fact: {varied}. "
            f"{effect.rstrip('.')}."
        )

    principle_ids = response.hidden.get("principles_applied") or []
    principles = [spec.principle(pid) for pid in principle_ids]
    principles = [p for p in principles if p]
    for principle in principles:
        sentences.append(
            f"{principle.get('name')}: {str(principle.get('description', '')).strip().rstrip('.')}."
        )

    note = response.hidden.get("intended_divergence_note") or ""
    # Round 1 appended this to every row because the writer fills the note in even on
    # ordinary cases. It belongs only where the case is actually an intended divergence.
    if note and case_type == "divergence":
        sentences.append(f"A generic assistant would probably instead: {note.strip()}")
    if not sentences:
        sentences.append(
            "An adequate reply engages the concrete obligations in this situation and takes a "
            "position rather than listing considerations."
        )

    # One PASS and one FAIL per applied principle, so every principle the writer used is
    # represented before the list is truncated. Round 1 took two of each and never got
    # past the second principle.
    principle_notes: list[str] = []
    for principle in principles:
        for indicator in (principle.get("positive_indicators") or [])[:1]:
            principle_notes.append(pass_note(indicator))
        for failure in (principle.get("failure_modes") or [])[:1]:
            principle_notes.append(failure_note(failure))
    review_notes = [
        f"NOTE from review of the reference answer: {issue}"
        for issue in (review.issues[:2] if review is not None else [])
    ]
    # The review notes are the only situation-specific lines here, so they are reserved
    # a place rather than truncated off the end as they were in round 1.
    principle_notes = [note for note in principle_notes if note]
    notes = principle_notes[: MAX_PASS_FAIL_NOTES - len(review_notes)] + review_notes
    if not notes:
        notes.append("PASS if the reply gives concrete, actionable judgment rather than hedging.")
    return " ".join(sentences), notes


# -- leak and placeholder checks --------------------------------------------


def _assistant_texts(train_rows: list[dict[str, Any]], eval_rows: list[dict[str, Any]]) -> list[str]:
    """Every string a model or a judge sees. The grading key is judge-visible too."""
    texts = [row["messages"][1]["content"] for row in train_rows]
    for row in eval_rows:
        texts.append(row["prompt"])
        texts.append(row["reference_answer"])
        texts.append(row["expected_behavior"])
        texts.extend(row["pass_fail_notes"])
    return texts


def _passage_ids_in_assistant_text(
    spec: TargetSpec, train_rows: list[dict[str, Any]], eval_rows: list[dict[str, Any]]
) -> set[str]:
    """Passage ids are internal provenance. None may reach text a model or a judge sees."""
    ids = [passage.id for passage in spec.key_passages]
    if not ids:
        return set()
    found: set[str] = set()
    for text in _assistant_texts(train_rows, eval_rows):
        found.update(find_cue_hits(text, ids))
    return found


def unwrap_passage_id(claimed: Any) -> str:
    """Recover the bare id from what a writer actually wrote.

    Round-1 responses cite passages three ways: "MN 58", "[MN 58]", and
    "[MN 58] the six cases of speech" with the passage title appended. Only the first
    resolves against the spec, so the licence lookup sees an unmapped source for the
    other two unless the wrapper and the trailing title come off first.
    """
    text = " ".join(str(claimed).split())
    if text.startswith("[") and "]" in text:
        return text[1 : text.index("]")].strip()
    return text.strip("[]").strip()


def find_placeholders(spec: TargetSpec, text: str) -> list[str]:
    """Unfilled template slots in an answer: "[Name]", "[date]", "[specific claim]".

    Passage ids are bracketed too in some specs, so anything that resolves to a real
    passage id is left to the passage-id check, which reports it as provenance leakage.
    """
    passage_ids = {passage.id.lower() for passage in spec.key_passages}
    found: list[str] = []
    for inner in BRACKETED.findall(text):
        stripped = inner.strip()
        if not stripped or not any(char.isalpha() for char in stripped):
            continue  # "[...]", an editorial ellipsis
        if stripped.lower() in passage_ids or any(char.isdigit() for char in stripped):
            continue
        found.append(f"[{stripped}]")
    return found


# -- licence metadata -------------------------------------------------------


def grounding_entries(spec: TargetSpec) -> list[dict[str, Any]]:
    return [
        entry
        for entry in spec.reference_material
        if str(entry.get("use", "")).strip() == "grounding"
    ]


# A licence that has to explain itself is not an unconditional one. Every plain
# public-domain statement in the four specs fits in a clause; every mixed or
# conditional one runs to a paragraph, and several of those mention public domain in
# passing ("3,425 of 4,392 words are ... the remainder are public domain").
PLAIN_LICENCE_CHARS = 80
LICENCE_CONDITIONS = (
    "cleared",
    "non-commercial",
    "noncommercial",
    "share-alike",
    "attribution",
    "cc by",
    "by-nc",
    "by-sa",
    "asks",
    "permission",
    "copyright",
    "©",
    "most restrictive",
    "mixed",
)


def is_public_domain(licence: str) -> bool:
    """True only for a licence that says public domain and states no further condition.

    Deliberately narrow. "public domain underlying text; CCEL edition asks that
    commercial republication be cleared" carries a condition, and a compiled licence
    whose public-domain part covers only some of the words carries several.
    """
    text = licence.lower().strip()
    if "public domain" not in text:
        return False
    if len(text) > PLAIN_LICENCE_CHARS:
        return False
    return not any(word in text for word in LICENCE_CONDITIONS)


def resolve_redistribution_note(spec: TargetSpec, config: RunConfig) -> str:
    """The spec states the terms its own sources carry; the config can add to them."""
    from_spec = str(spec.raw.get("redistribution_note") or "").strip()
    from_config = str(config.raw.get("redistribution_note") or "").strip()
    if from_spec and from_config and from_config not in from_spec:
        return f"{from_spec} {from_config}"
    return from_spec or from_config


def check_license_metadata(spec: TargetSpec, redistribution_note: str) -> None:
    """Refuse to export data whose terms are unknown. Licences travel with the dataset."""
    entries = grounding_entries(spec)
    missing = [str(entry.get("id", "?")) for entry in entries if not str(entry.get("license") or "").strip()]
    if missing:
        raise RuntimeError(
            f"Cannot export {spec.target_id}: grounding sources {missing} in "
            f"{spec.root / 'spec.yaml'} have no `license`. Every reference_material entry "
            f"with `use: grounding` reached the generator, so its terms travel with the "
            f"exported rows. Add a `license` line to each (state the most restrictive of "
            f"the sources it compiles)."
        )
    restricted = sorted(
        {
            str(entry.get("license")).strip()
            for entry in entries
            if not is_public_domain(str(entry.get("license")).strip())
        }
    )
    if restricted and not redistribution_note:
        raise RuntimeError(
            f"Cannot export {spec.target_id}: grounding licences {restricted} are not plain "
            f"public domain, so the export needs a `redistribution_note` saying what a "
            f"recipient may do with it. Set it at the top level of "
            f"{spec.root / 'spec.yaml'}, or in the run config."
        )


def license_constraints(spec: TargetSpec) -> list[dict[str, str]]:
    """Distinct licence terms on the grounding sources, so restrictions travel with the data."""
    seen: dict[tuple[str, str], dict[str, str]] = {}
    for entry in grounding_entries(spec):
        licence = str(entry.get("license") or "not recorded").strip()
        key = (licence, "grounding")
        if key not in seen:
            seen[key] = {"license": licence, "use": "grounding", "sources": entry.get("id", "")}
        else:
            seen[key]["sources"] += f", {entry.get('id', '')}"
    return list(seen.values())


def source_licenses(spec: TargetSpec, passage_ids: list[str]) -> list[dict[str, str]]:
    """Per-row licence provenance: which source each cited passage came from, and its terms.

    A passage can match more than one reference_material entry (two Theravada entries
    both claim "DN 26" under different licences), so every match is listed and the row
    carries the union rather than a guess at which one was used.
    """
    licence_by_source = {
        str(entry.get("id", "")): str(entry.get("license") or "not recorded").strip()
        for entry in spec.reference_material
    }
    # A passage whose id matches no `passage_id_format` still lives in key_passages.md,
    # whose own licence is the compiled most-restrictive one. That is the right fallback:
    # more accurate than "not recorded", and never less restrictive than the truth.
    compiled = next(
        (
            str(entry.get("id", ""))
            for entry in grounding_entries(spec)
            if str(entry.get("path", "")).endswith(KEY_PASSAGES_SUFFIX)
        ),
        "",
    )
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for passage_id in passage_ids:
        passage = spec.passage(passage_id)
        source_ids = list(getattr(passage, "source_ids", []) or []) if passage else []
        if not source_ids:
            source_ids = [compiled] if passage is not None and compiled else [""]
        for source_id in source_ids:
            if source_id in seen:
                continue
            seen.add(source_id)
            out.append(
                {
                    "source_id": source_id or "unmapped",
                    "license": licence_by_source.get(source_id, "not recorded"),
                }
            )
    return out


# -- reproducibility --------------------------------------------------------


def git_commit(repo_root: Path = REPO_ROOT) -> str:
    """The commit the run was produced from, with a marker when the tree was dirty."""
    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=repo_root, capture_output=True, text=True, timeout=10
        ).stdout.strip()

    try:
        commit = git("rev-parse", "HEAD")
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    if not commit:
        return "unknown"
    return f"{commit}-dirty" if git("status", "--porcelain") else commit


def write_input_copies(spec: TargetSpec, config: RunConfig, run_dir: Path) -> str:
    """Copy the resolved config and the spec into the run dir; return the spec hash.

    Without these, config_hash and spec_hash identify nothing that can be checked later.
    """
    (run_dir / CONFIG_COPY_FILE).write_text(
        yaml.safe_dump(config.raw, sort_keys=True, allow_unicode=True), encoding="utf-8"
    )
    spec_path = spec.root / "spec.yaml"
    spec_text = spec_path.read_text(encoding="utf-8")
    (run_dir / SPEC_COPY_FILE).write_text(spec_text, encoding="utf-8")
    return hashlib.sha256(spec_text.encode("utf-8")).hexdigest()[:12]


# -- the stage --------------------------------------------------------------


def run_stage(config: RunConfig, spec: TargetSpec, run_dir: Path) -> dict[str, Any]:
    """Entry point for `main.py export`. Writes the deliverables into the run dir."""
    families = records.read_jsonl(run_dir / records.FAMILIES_FILE, Family)
    prompts = records.read_jsonl(run_dir / records.PROMPTS_FILE, Prompt)
    responses = records.read_jsonl(run_dir / records.RESPONSES_FILE, Response)
    decisions = records.read_jsonl(run_dir / records.DECISIONS_FILE, Decision)
    reviews = records.read_jsonl(run_dir / records.REVIEWS_FILE, Review)
    if not decisions:
        raise RuntimeError(
            f"No decisions in {run_dir / records.DECISIONS_FILE}. Run the validate stage first."
        )

    redistribution_note = resolve_redistribution_note(spec, config)
    check_license_metadata(spec, redistribution_note)

    duplicate_family_ids = sorted(
        {f.family_id for f in families if sum(1 for g in families if g.family_id == f.family_id) > 1}
    )
    if duplicate_family_ids:
        raise RuntimeError(
            f"Split integrity failure: {records.FAMILIES_FILE} repeats family ids "
            f"{duplicate_family_ids}; one family cannot carry two splits."
        )
    family_by_id = {family.family_id: family for family in families}
    prompt_by_id = {prompt.prompt_id: prompt for prompt in prompts}
    review_by_response = {review.response_id: review for review in reviews}
    decision_by_response = {decision.response_id: decision for decision in decisions}

    train_rows: list[dict[str, Any]] = []
    eval_rows: list[dict[str, Any]] = []
    readmitted_eval: list[str] = []

    for response in responses:
        decision = decision_by_response.get(response.response_id)
        if decision is None:
            continue
        prompt = prompt_by_id.get(response.prompt_id)
        if prompt is None:
            continue
        family = family_by_id.get(prompt.family_id)
        if family is None:
            continue
        if not decision.keep:
            if family.split != "eval" or _has_hard_drop(decision):
                continue
            readmitted_eval.append(response.response_id)

        review = review_by_response.get(response.response_id)
        passages = normalise_passage_ids(
            spec,
            [
                unwrap_passage_id(claimed)
                for claimed in (response.hidden.get("source_passages") or [])
            ],
        )
        meta = {
            "response_id": response.response_id,
            "prompt_id": prompt.prompt_id,
            "family_id": family.family_id,
            "target_id": spec.target_id,
            "spec_version": spec.version,
            "domain": family.domain,
            "case_type": decision.final_case_type,
            "variant": prompt.variant,
            "mode": prompt.mode,
            "question_kind": getattr(prompt, "question_kind", ""),
            "register": getattr(prompt, "register", ""),
            "counterfactual_group_id": family.counterfactual_group_id,
            "varied_fact": family.varied_fact,
            "situation_features": family.situation_features,
            "asker_stance": getattr(family, "asker_stance", ""),
            "divergence_hypothesis_id": getattr(family, "divergence_hypothesis_id", ""),
            "tradeoff_ids": family.tradeoff_ids,
            "principles_applied": response.hidden.get("principles_applied") or [],
            # Repaired here too, so runs generated before the fix still export usable ids.
            "source_passages": passages,
            "source_licenses": source_licenses(spec, passages),
            "generator_model": response.generator_model,
            "divergence_status": decision.divergence_status,
            "divergence_kind": decision.divergence_kind,
        }
        if family.split == "train":
            train_rows.append(
                {
                    "messages": [
                        {"role": "user", "content": prompt.text},
                        {"role": "assistant", "content": render_assistant_message(response)},
                    ],
                    "meta": meta,
                }
            )
        elif family.split == "eval":
            expected, pass_fail = derive_grading_key(
                spec, response, review, family, decision.final_case_type
            )
            # A row kept despite the score cut is still graded, but a reader of the eval
            # set must be able to see that the reviewer was unhappy with the reference.
            meta["kept_by_validate"] = decision.keep
            meta["review_scores"] = review.scores if review is not None else {}
            meta["validate_reasons"] = decision.reasons
            eval_rows.append(
                {
                    "prompt": prompt.text,
                    "case_type": decision.final_case_type,
                    "family_id": family.family_id,
                    "variant": prompt.variant,
                    "expected_behavior": expected,
                    "pass_fail_notes": pass_fail,
                    "reference_answer": render_assistant_message(response),
                    "meta": meta,
                }
            )

    def split_groups(rows: list[dict[str, Any]]) -> set[str]:
        return {
            row["meta"]["counterfactual_group_id"] or row["meta"]["family_id"] for row in rows
        }

    # Survival is judged on the rows actually admitted, not on decision.keep: an eval row
    # carried past the score cut still holds up its half of the contrast.
    complete_groups, incomplete_groups = _counterfactual_group_survival(train_rows + eval_rows)
    if incomplete_groups:
        logger.warning(
            "export: counterfactual group(s) %s kept fewer than two families and are not "
            "exported; there is nothing left to contrast with.",
            sorted(incomplete_groups),
        )
        train_rows = [r for r in train_rows if r["meta"]["counterfactual_group_id"] not in incomplete_groups]
        eval_rows = [r for r in eval_rows if r["meta"]["counterfactual_group_id"] not in incomplete_groups]

    overlap = split_groups(train_rows) & split_groups(eval_rows)
    if overlap:
        raise RuntimeError(
            f"Split integrity failure: these families or counterfactual groups appear in "
            f"both train and eval: {sorted(overlap)}"
        )
    leaks = _passage_ids_in_assistant_text(spec, train_rows, eval_rows)
    if leaks:
        raise RuntimeError(
            f"Hidden metadata leaked into user-visible text: passage ids {sorted(leaks)} "
            f"appear in an assistant message, an evaluation prompt or a grading key. The "
            f"rendering template must never include record fields."
        )
    train_rows, eval_rows, placeholder_drops = _drop_rows_with_placeholders(
        spec, train_rows, eval_rows
    )
    counts = _bucket_counts(train_rows, eval_rows)

    records.write_jsonl(run_dir / SFT_FILE, train_rows)
    records.write_jsonl(run_dir / EVAL_FILE, eval_rows)
    spec_hash = write_input_copies(spec, config, run_dir)

    usage = summarise_usage(run_dir / records.USAGE_FILE, config.pricing)
    manifest = {
        "target_id": spec.target_id,
        "target_name": spec.name,
        "spec_version": spec.version,
        "spec_hash": spec_hash,
        "run_id": run_dir.name,
        "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "config_file": str(config.path),
        "config_hash": config.config_hash(),
        "config_copy": CONFIG_COPY_FILE,
        "spec_copy": SPEC_COPY_FILE,
        "models": {name: role.model for name, role in config.roles.items() if role.enabled},
        "counts": {
            "n_families_configured": config.generation.get("n_families"),
            "n_families_effective": len(families),
            "families": len(families),
            "families_train": sum(1 for f in families if f.split == "train"),
            "families_eval": sum(1 for f in families if f.split == "eval"),
            "families_reserved": sum(1 for f in families if f.split == "reserved"),
            "layers_generated": sorted(
                {layer for f in families for layer in getattr(f, "layers_generated", [])}
            ),
            "prompts": len(prompts),
            "responses": len(responses),
            "kept": sum(1 for d in decisions if d.keep),
            "dropped": sum(1 for d in decisions if not d.keep),
            "sft_train_rows": len(train_rows),
            "eval_rows": len(eval_rows),
            "eval_rows_kept_despite_score_cut": len(readmitted_eval),
            "rows_dropped_for_placeholders": placeholder_drops,
            "explicit_mode_rows": sum(
                1 for row in train_rows + eval_rows if row["meta"]["mode"] == "explicit"
            ),
            # Only groups that kept at least two families are counted: a lone member is
            # not a contrast, whatever its group id says.
            "counterfactual_groups": len(complete_groups),
            "counterfactual_groups_incomplete": len(incomplete_groups),
            "by_bucket": dict(sorted(counts.items())),
        },
        "license_constraints": license_constraints(spec),
        "redistribution_note": redistribution_note,
        "cost": {
            "usd": usage["cost_usd"] if usage["cost_known"] else None,
            "display": format_cost(usage),
            "calls": usage["calls"],
            "prompt_tokens": usage["prompt_tokens"],
            "completion_tokens": usage["completion_tokens"],
            "reasoning_tokens": usage["reasoning_tokens"],
        },
    }
    (run_dir / MANIFEST_FILE).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    logger.info(
        "export: %d training rows, %d eval rows -> %s",
        len(train_rows),
        len(eval_rows),
        run_dir,
    )
    return {"sft_train_rows": len(train_rows), "eval_rows": len(eval_rows)}


def _has_hard_drop(decision: Decision) -> bool:
    """True when a drop reason is one an evaluation row cannot be carried past."""
    return any(
        reason.startswith(prefix)
        for reason in decision.reasons
        for prefix in HARD_EVAL_DROP_PREFIXES
    )


def _bucket_counts(
    train_rows: list[dict[str, Any]], eval_rows: list[dict[str, Any]]
) -> Counter[str]:
    """Buckets describing the files as written, counted after every filter has run."""
    counts: Counter[str] = Counter()
    for row in train_rows:
        counts[f"train:{row['meta']['domain']}"] += 1
        counts[f"train_case:{row['meta']['case_type']}"] += 1
    for row in eval_rows:
        counts[f"eval:{row['meta']['domain']}"] += 1
        counts[f"eval_case:{row['meta']['case_type']}"] += 1
        # Its own namespace: round 1 added "eval_case:reframing" alongside the case types
        # and the bucket table then summed to more than the number of rows.
        counts[f"eval_variant:{row['meta']['variant']}"] += 1
        if row["meta"].get("question_kind"):
            counts[f"eval_question:{row['meta']['question_kind']}"] += 1
    return counts


def _counterfactual_group_survival(
    rows: list[dict[str, Any]],
) -> tuple[set[str], set[str]]:
    """Split counterfactual groups into those that kept a contrast and those that did not.

    A group whose partner family lost every row has nothing to be contrasted with, and a
    manifest that still counts it overstates what the dataset can test.
    """
    members: dict[str, set[str]] = {}
    for row in rows:
        group_id = row["meta"]["counterfactual_group_id"]
        if group_id:
            members.setdefault(group_id, set()).add(row["meta"]["family_id"])
    complete = {group for group, families in members.items() if len(families) >= 2}
    return complete, set(members) - complete


def _drop_rows_with_placeholders(
    spec: TargetSpec, train_rows: list[dict[str, Any]], eval_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    """Remove rows whose assistant text still holds an unfilled template slot.

    One row per slip rather than a failed export: "[Name]" is a writer defect on that
    response, not a rendering fault that would repeat across the run.
    """
    kept_train, kept_eval, dropped = [], [], 0
    for row in train_rows:
        found = find_placeholders(spec, row["messages"][1]["content"])
        if found:
            dropped += 1
            logger.warning(
                "export: dropping train row %s, unfilled placeholders %s",
                row["meta"]["response_id"],
                found,
            )
            continue
        kept_train.append(row)
    for row in eval_rows:
        found = find_placeholders(spec, row["reference_answer"])
        if found:
            dropped += 1
            logger.warning(
                "export: dropping eval row %s, unfilled placeholders %s",
                row["meta"]["response_id"],
                found,
            )
            continue
        kept_eval.append(row)
    return kept_train, kept_eval, dropped
