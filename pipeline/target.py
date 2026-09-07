"""Target specification loading, validation and rendering.

A target is one belief/value system. Nothing here names a tradition: everything
tradition-specific lives in targets/<id>/spec.yaml and its references/.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REQUIRED_TOP_LEVEL = ("id", "name", "version", "summary", "principles", "domains", "cue_policy")
KEY_PASSAGES_SUFFIX = "key_passages.md"

# key_passages.md format: each passage is a markdown heading holding the passage id,
# optionally followed by " — title", then the excerpt text until the next heading.
PASSAGE_HEADING = re.compile(r"^#{2,4}\s+(?P<id>[^\n#]+?)\s*$", re.MULTILINE)


class SpecError(Exception):
    """The target specification is missing something the pipeline needs."""


@dataclass
class KeyPassage:
    id: str
    title: str
    text: str
    # The reference_material entry this passage came from, matched on the literal prefix
    # of that entry's `passage_id_format`. `source_ids` holds every entry that matches;
    # some formats overlap (two Theravada entries both claim "DN 26" under different
    # licences), so licence aggregation should use the list and take the most restrictive.
    source_id: str = ""
    source_ids: list[str] = field(default_factory=list)

    def render(self) -> str:
        header = f"[{self.id}]" + (f" {self.title}" if self.title else "")
        return f"{header}\n{self.text.strip()}"


@dataclass
class TargetSpec:
    target_id: str
    name: str
    version: str
    summary: str
    principles: list[dict[str, Any]]
    domains: list[dict[str, Any]]
    cue_policy: dict[str, Any]
    boundaries: list[dict[str, Any]] = field(default_factory=list)
    tradeoffs: list[dict[str, Any]] = field(default_factory=list)
    unresolved_choices: list[dict[str, Any]] = field(default_factory=list)
    misinterpretations: list[dict[str, Any]] = field(default_factory=list)
    divergence_hypotheses: list[dict[str, Any]] = field(default_factory=list)
    layers: list[dict[str, Any]] = field(default_factory=list)
    reference_material: list[dict[str, Any]] = field(default_factory=list)
    key_passages: list[KeyPassage] = field(default_factory=list)
    root: Path = Path(".")
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def forbidden_terms(self) -> list[str]:
        """Hard cue terms. Any hit rejects the response."""
        return list(self.cue_policy.get("forbidden_terms") or [])

    @property
    def allowed_terms(self) -> list[str]:
        """Ordinary-English words the target needs. Never counted as cue leakage."""
        return list(self.cue_policy.get("allowed_terms") or [])

    @property
    def signature_moves(self) -> list[dict[str, Any]]:
        """Named, checkable moves a response should show when relevant."""
        moves = self.raw.get("signature_moves") or []
        return [m if isinstance(m, dict) else {"id": str(m), "description": ""} for m in moves]

    @property
    def deliberation_shape(self) -> str:
        """Per-target description of how this target deliberates, used in the response prompt."""
        return str(self.raw.get("deliberation_shape") or "").strip()

    @property
    def archaic_register_examples(self) -> list[str]:
        return list(self.cue_policy.get("archaic_register_examples") or [])

    @property
    def soft_terms(self) -> list[str]:
        """Ambiguous words that are reported as a flag but never reject on their own."""
        return list(self.cue_policy.get("soft_terms") or [])

    def default_layer_ids(self) -> list[str]:
        """Layer ids generated unless the config overrides them.

        A layer without `generate_by_default` is on; a spec without layers has none.
        """
        return [
            str(layer["id"])
            for layer in self.layers
            if layer.get("id") and layer.get("generate_by_default", True)
        ]

    def principles_for_layers(self, layer_ids: list[str] | None) -> list[dict[str, Any]]:
        """Principles in the selected layers. A principle with no layer is always included."""
        if layer_ids is None:
            layer_ids = self.default_layer_ids()
        if not self.layers:
            return list(self.principles)
        selected = set(layer_ids)
        return [
            principle
            for principle in self.principles
            if not principle.get("layer") or principle.get("layer") in selected
        ]

    def avoided_topics(self) -> list[dict[str, Any]]:
        """unresolved_choices the pilot must not generate scenarios about."""
        return [
            choice
            for choice in self.unresolved_choices
            if str(choice.get("generation_policy", "")).strip() == "avoid"
        ]

    def avoid_keywords(self) -> list[str]:
        """Optional keyword screen for avoided topics. Empty when no spec supplies them."""
        words: list[str] = []
        for choice in self.avoided_topics():
            words.extend(str(word) for word in (choice.get("avoid_keywords") or []))
        return words

    def passage(self, passage_id: str) -> KeyPassage | None:
        for passage in self.key_passages:
            if passage.id == passage_id:
                return passage
        return None

    def principle(self, principle_id: str) -> dict[str, Any] | None:
        for item in self.principles:
            if item.get("id") == principle_id:
                return item
        return None

    def tradeoff(self, tradeoff_id: str) -> dict[str, Any] | None:
        for item in self.tradeoffs:
            if item.get("id") == tradeoff_id:
                return item
        return None

    def domain_weights(self) -> list[tuple[str, float]]:
        pairs = [(d["id"], float(d.get("weight", 1.0))) for d in self.domains]
        total = sum(weight for _, weight in pairs) or 1.0
        return [(domain_id, weight / total) for domain_id, weight in pairs]


def _format_prefixes(passage_id_format: str) -> list[str]:
    """The literal prefixes a passage_id_format can produce.

    A format may list alternatives ("DV / LG / VS / CDF 1998 / CSDC <section>"), so each
    alternative becomes its own prefix; placeholders and section marks end a prefix.
    """
    prefixes: list[str] = []
    for alternative in str(passage_id_format or "").split("/"):
        text = alternative
        for marker in ("<", "§", "("):
            index = text.find(marker)
            if index != -1:
                text = text[:index]
        text = text.strip()
        if text:
            prefixes.append(text)
    return prefixes


def attach_passage_sources(
    passages: list[KeyPassage], reference_material: list[dict[str, Any]]
) -> None:
    """Match each passage to the reference entries whose id format it starts with."""
    candidates = [
        (prefix, str(entry.get("id", "")))
        for entry in reference_material
        if entry.get("passage_id_format") and entry.get("id")
        for prefix in _format_prefixes(entry.get("passage_id_format", ""))
    ]
    for passage in passages:
        matches = [
            (prefix, entry_id)
            for prefix, entry_id in candidates
            if prefix and passage.id.lower().startswith(prefix.lower())
        ]
        matches.sort(key=lambda pair: len(pair[0]), reverse=True)
        seen: set[str] = set()
        passage.source_ids = [
            entry_id
            for _prefix, entry_id in matches
            if not (entry_id in seen or seen.add(entry_id))
        ]
        passage.source_id = passage.source_ids[0] if passage.source_ids else ""


def parse_key_passages(text: str) -> list[KeyPassage]:
    """Split key_passages.md into passages keyed by their heading id."""
    passages: list[KeyPassage] = []
    matches = list(PASSAGE_HEADING.finditer(text))
    for index, match in enumerate(matches):
        heading = match.group("id").strip()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : end].strip()
        # "Analects 12.22 — Humane concern" keeps the id and the optional title apart.
        parts = re.split(r"\s+[—–-]{1,2}\s+", heading, maxsplit=1)
        passage_id = parts[0].strip()
        title = parts[1].strip() if len(parts) > 1 else ""
        if passage_id:
            passages.append(KeyPassage(id=passage_id, title=title, text=body))
    return passages


def _cited_ids(entries: list[dict[str, Any]], label: str) -> list[tuple[str, str, list[str]]]:
    """Return (label, item id, source ids) for each entry that should cite sources."""
    out = []
    for index, entry in enumerate(entries):
        item_id = str(entry.get("id") or entry.get("principle") or f"{label}[{index}]")
        sources = entry.get("sources") or []
        if isinstance(sources, str):
            sources = [sources]
        out.append((label, item_id, [str(s) for s in sources]))
    return out


def validate_spec(
    raw: dict[str, Any],
    key_passages: list[KeyPassage],
    spec_path: Path,
    strict: bool = False,
) -> list[str]:
    """Return every problem found, so one run of the loader fixes one round of edits.

    `strict` turns the section-D spec additions from optional into required. It stays off
    until every researcher has landed their fields.
    """
    problems: list[str] = []
    if strict:
        for index, choice in enumerate(raw.get("unresolved_choices") or []):
            if str(choice.get("generation_policy", "")).strip() != "avoid":
                continue
            if not (choice.get("avoid_keywords") or []):
                problems.append(
                    f"{spec_path}: unresolved_choices[{index}] "
                    f"('{choice.get('id')}') has generation_policy: avoid but no "
                    f"avoid_keywords, so nothing screens the generated situations."
                )
    for key in REQUIRED_TOP_LEVEL:
        if not raw.get(key):
            problems.append(f"{spec_path}: missing required top-level key '{key}'.")

    principles = raw.get("principles") or []
    if principles and len(principles) < 3:
        problems.append(
            f"{spec_path}: only {len(principles)} principles; the schema asks for 8-20 "
            f"(3 is the minimum the pipeline will run with)."
        )
    seen_principle_ids: set[str] = set()
    for index, principle in enumerate(principles):
        where = f"{spec_path}: principles[{index}]"
        principle_id = principle.get("id")
        if not principle_id:
            problems.append(f"{where} has no 'id'.")
        elif principle_id in seen_principle_ids:
            problems.append(f"{where} repeats principle id '{principle_id}'.")
        else:
            seen_principle_ids.add(principle_id)
        for required in ("name", "description"):
            if not principle.get(required):
                problems.append(f"{where} ('{principle_id}') has no '{required}'.")
        if not principle.get("sources"):
            problems.append(
                f"{where} ('{principle_id}') cites no sources; every principle must cite "
                f"at least one passage id."
            )

    for index, domain in enumerate(raw.get("domains") or []):
        if not domain.get("id"):
            problems.append(f"{spec_path}: domains[{index}] has no 'id'.")

    tradeoff_ids: set[str] = set()
    for index, tradeoff in enumerate(raw.get("tradeoffs") or []):
        where = f"{spec_path}: tradeoffs[{index}]"
        tradeoff_id = tradeoff.get("id")
        if not tradeoff_id:
            problems.append(f"{where} has no 'id'.")
        elif tradeoff_id in tradeoff_ids:
            problems.append(f"{where} repeats tradeoff id '{tradeoff_id}'.")
        else:
            tradeoff_ids.add(tradeoff_id)
        if not tradeoff.get("description"):
            problems.append(f"{where} ('{tradeoff_id}') has no 'description'.")
        if tradeoff.get("unresolved") is not True and not tradeoff.get("intended_lean"):
            problems.append(
                f"{where} ('{tradeoff_id}') is not marked unresolved but gives no "
                f"'intended_lean'; set one or mark unresolved: true."
            )

    cue_policy = raw.get("cue_policy") or {}
    forbidden = {str(t).strip().lower() for t in (cue_policy.get("forbidden_terms") or [])}
    for list_name in ("allowed_terms", "soft_terms"):
        overlap = sorted(
            {str(t).strip().lower() for t in (cue_policy.get(list_name) or [])} & forbidden
        )
        if overlap:
            problems.append(
                f"{spec_path}: cue_policy.{list_name} overlaps forbidden_terms on "
                f"{overlap}. A term cannot be both permitted and rejected. "
                f"(allowed_terms and soft_terms may overlap each other; that is fine.)"
            )
    if cue_policy and not cue_policy.get("forbidden_terms"):
        problems.append(
            f"{spec_path}: cue_policy has no 'forbidden_terms'; the cue check needs the "
            f"terms that would give the tradition away."
        )

    known_passage_ids = {passage.id for passage in key_passages}
    if not known_passage_ids:
        problems.append(
            f"{spec_path.parent}: no passages parsed from the reference_material entry "
            f"ending in {KEY_PASSAGES_SUFFIX}. Each passage needs a markdown heading "
            f"(## or ###) whose text is the passage id."
        )
    else:
        citing = (
            _cited_ids(raw.get("principles") or [], "principle")
            + _cited_ids(raw.get("boundaries") or [], "boundary")
            + _cited_ids(raw.get("tradeoffs") or [], "tradeoff")
        )
        for label, item_id, sources in citing:
            missing = [s for s in sources if s not in known_passage_ids]
            if missing:
                problems.append(
                    f"{spec_path}: {label} '{item_id}' cites passage ids not present in "
                    f"{KEY_PASSAGES_SUFFIX}: {missing}. Add the passage or fix the id."
                )
    return problems


def load_target(targets_dir: Path, target_id: str, strict: bool = False) -> TargetSpec:
    """Load and validate targets/<target_id>/spec.yaml. Raises SpecError listing all problems."""
    root = Path(targets_dir) / target_id
    spec_path = root / "spec.yaml"
    if not spec_path.exists():
        raise SpecError(
            f"No target specification at {spec_path}. Expected targets/<id>/spec.yaml."
        )
    raw = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise SpecError(f"{spec_path} must contain a YAML mapping.")

    key_passages: list[KeyPassage] = []
    passages_path: Path | None = None
    for entry in raw.get("reference_material") or []:
        path_value = str(entry.get("path", ""))
        if path_value.endswith(KEY_PASSAGES_SUFFIX):
            passages_path = root / path_value
            break
    if passages_path is None:
        default_path = root / "references" / KEY_PASSAGES_SUFFIX
        if default_path.exists():
            passages_path = default_path
    if passages_path is not None and passages_path.exists():
        key_passages = parse_key_passages(passages_path.read_text(encoding="utf-8"))
        attach_passage_sources(key_passages, raw.get("reference_material") or [])
    elif passages_path is not None:
        raise SpecError(
            f"{spec_path}: reference_material points at {passages_path}, which does not exist."
        )

    problems = validate_spec(raw, key_passages, spec_path, strict)
    if problems:
        raise SpecError(
            f"Target '{target_id}' is not usable yet ({len(problems)} problem(s)):\n  - "
            + "\n  - ".join(problems)
        )

    if raw["id"] != target_id:
        raise SpecError(f"{spec_path}: id is '{raw['id']}' but the directory is '{target_id}'.")

    return TargetSpec(
        target_id=raw["id"],
        name=raw["name"],
        version=str(raw["version"]),
        summary=str(raw["summary"]).strip(),
        principles=raw["principles"],
        domains=raw["domains"],
        cue_policy=raw["cue_policy"],
        boundaries=raw.get("boundaries") or [],
        tradeoffs=raw.get("tradeoffs") or [],
        unresolved_choices=raw.get("unresolved_choices") or [],
        misinterpretations=raw.get("misinterpretations") or [],
        divergence_hypotheses=raw.get("divergence_hypotheses") or [],
        layers=raw.get("layers") or [],
        reference_material=raw.get("reference_material") or [],
        key_passages=key_passages,
        root=root,
        raw=raw,
    )


def normalise_passage_ids(spec: "TargetSpec", claimed: list[str]) -> list[str]:
    """Map ids a model wrote back onto the ids in key_passages.md.

    Generators sometimes drop a passage-id prefix that is also on the forbidden-terms
    list (e.g. writing "12.22" for "Analects 12.22"). An id that still matches nothing
    is kept as written, so a wrong citation stays visible rather than being invented away.
    """
    known = {passage.id for passage in spec.key_passages}
    lowered = {passage.id.lower(): passage.id for passage in spec.key_passages}
    out: list[str] = []
    for raw in claimed:
        value = str(raw).strip()
        if value in known:
            out.append(value)
            continue
        if value.lower() in lowered:
            out.append(lowered[value.lower()])
            continue
        suffix_matches = [
            passage_id
            for passage_id in known
            if passage_id.lower().endswith(value.lower()) and value
        ]
        out.append(suffix_matches[0] if len(suffix_matches) == 1 else value)
    return out


# -- rendering --------------------------------------------------------------


def _bullets(lines: list[str]) -> str:
    return "\n".join(f"- {line}" for line in lines) if lines else "- (none recorded)"


def render_principles(
    spec: TargetSpec,
    principle_ids: list[str] | None = None,
    layer_ids: list[str] | None = None,
    *,
    compact: bool = False,
) -> str:
    """Render principles for a prompt.

    `layer_ids` selects which layers are in play; `principle_ids` narrows further to the
    ones a particular family actually uses. `compact` drops positive_indicators, which
    the generator does not need and which dominate the length of a large spec.
    """
    chosen = spec.principles_for_layers(layer_ids)
    if principle_ids:
        wanted = set(principle_ids)
        narrowed = [p for p in chosen if p.get("id") in wanted]
        chosen = narrowed or chosen
    blocks = []
    for principle in chosen:
        parts = [f"{principle.get('id')} {principle.get('name')}: {str(principle.get('description','')).strip()}"]
        if not compact and principle.get("positive_indicators"):
            parts.append("  looks like: " + "; ".join(map(str, principle["positive_indicators"])))
        if principle.get("failure_modes"):
            parts.append("  fails when: " + "; ".join(map(str, principle["failure_modes"])))
        if principle.get("sources"):
            parts.append("  grounded in: " + ", ".join(map(str, principle["sources"])))
        blocks.append("\n".join(parts))
    return "\n\n".join(blocks) if blocks else "(no principles)"


def render_tradeoffs(spec: TargetSpec, tradeoff_ids: list[str] | None = None) -> str:
    chosen = [t for t in spec.tradeoffs if tradeoff_ids is None or t.get("id") in tradeoff_ids]
    blocks = []
    for tradeoff in chosen:
        lines = [f"{tradeoff.get('id')}: {str(tradeoff.get('description','')).strip()}"]
        if tradeoff.get("considerations"):
            lines.append("  what is in tension: " + "; ".join(map(str, tradeoff["considerations"])))
        if tradeoff.get("unresolved"):
            lines.append(
                "  UNRESOLVED: the reviewed target does not settle this. Present the conflict "
                "honestly and do not write a confident resolution."
            )
        elif tradeoff.get("intended_lean"):
            lines.append("  how the target leans: " + str(tradeoff["intended_lean"]).strip())
        if tradeoff.get("sources"):
            lines.append("  grounded in: " + ", ".join(map(str, tradeoff["sources"])))
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) if blocks else "(no tradeoffs recorded)"


def render_boundaries(spec: TargetSpec) -> str:
    return _bullets(
        [
            f"{b.get('principle', 'general')}: {str(b.get('limit', '')).strip()}"
            for b in spec.boundaries
        ]
    )


def render_domains(spec: TargetSpec) -> str:
    return _bullets(
        [
            f"{d.get('id')} (weight {d.get('weight', 1)}): {str(d.get('notes', '')).strip()}"
            for d in spec.domains
        ]
    )


def render_unresolved(spec: TargetSpec) -> str:
    lines = []
    for choice in spec.unresolved_choices:
        policy = choice.get("generation_policy", "mark_ambiguous")
        lines.append(
            f"{choice.get('id')}: {str(choice.get('question','')).strip()} "
            f"[policy: {policy}; working assumption: {str(choice.get('working_assumption','')).strip()}]"
        )
    return _bullets(lines)


def render_misinterpretations(spec: TargetSpec) -> str:
    return _bullets(
        [
            f"WRONG: {m.get('claim')}  ->  RIGHT: {m.get('correction')}"
            for m in spec.misinterpretations
        ]
    )


def render_divergence_hypotheses(spec: TargetSpec) -> str:
    lines = []
    for hypothesis in spec.divergence_hypotheses:
        lines.append(
            f"{hypothesis.get('id')}: {str(hypothesis.get('description','')).strip()}"
            + (f" Example shape: {hypothesis['example_prompt_shape']}" if hypothesis.get("example_prompt_shape") else "")
        )
    return _bullets(lines)


def render_key_passages(
    spec: TargetSpec, passage_ids: list[str] | None = None, max_chars: int = 6000
) -> str:
    """Render the passages that actually go into a prompt, oldest-cited first."""
    chosen = spec.key_passages
    if passage_ids:
        wanted = [pid for pid in passage_ids]
        chosen = [p for p in spec.key_passages if p.id in wanted] or spec.key_passages
    rendered: list[str] = []
    used = 0
    for passage in chosen:
        block = passage.render()
        if used + len(block) > max_chars and rendered:
            rendered.append(f"[{len(chosen) - len(rendered)} further passages omitted for length]")
            break
        rendered.append(block)
        used += len(block)
    return "\n\n".join(rendered) if rendered else "(no key passages)"


def render_cue_policy(spec: TargetSpec) -> str:
    policy = spec.cue_policy
    lines = [
        f"User prompts must not name the tradition or ask for a persona: "
        f"{bool(policy.get('prompts_must_not_name_tradition', True))}",
        f"Responses use ordinary language, not doctrinal vocabulary: "
        f"{bool(policy.get('responses_avoid_doctrinal_vocabulary', True))}",
        "Terms that must not appear in prompts or responses: "
        + (", ".join(spec.forbidden_terms) if spec.forbidden_terms else "(none listed)"),
    ]
    if spec.allowed_terms:
        lines.append(
            "Ordinary-English words this target needs in order to say what it means. "
            "These are NOT cues and you should use them where they are the right word: "
            + ", ".join(spec.allowed_terms)
        )
    if spec.soft_terms:
        lines.append(
            "Terms to use only if the situation genuinely calls for them, never as a "
            "signal of where the judgment comes from: " + ", ".join(spec.soft_terms)
        )
    return _bullets(lines)


def render_avoided_topics(spec: TargetSpec) -> str:
    """Topics the pilot must not build scenarios about, for the family-generation prompt."""
    lines = []
    for choice in spec.avoided_topics():
        question = str(choice.get("question", "")).strip()
        lines.append(f"{choice.get('id')}: {question}")
    return _bullets(lines) if lines else "- (nothing is off limits)"


def render_for_generator(
    spec: TargetSpec,
    *,
    principle_ids: list[str] | None = None,
    tradeoff_ids: list[str] | None = None,
    layer_ids: list[str] | None = None,
    stage: str = "families",
) -> str:
    """The target description the generator reads.

    Real specs run to 60 KB, so this is selective. For `stage="families"` the whole
    target is in play. For `stage="responses"` only the principles and tradeoffs the
    family actually uses are rendered, and the coverage plan and divergence hypotheses
    are dropped: by then the family already encodes them.
    """
    sections = [
        f"# Target: {spec.name} (id {spec.target_id}, spec version {spec.version})",
        "## How this target judges\n" + spec.summary,
        "## Principles\n"
        + render_principles(spec, principle_ids, layer_ids, compact=(stage == "responses")),
        "## Limits the target imposes on itself\n" + render_boundaries(spec),
        "## Genuine tradeoffs\n" + render_tradeoffs(spec, tradeoff_ids),
        "## Open interpretation questions\n" + render_unresolved(spec),
        "## Common distortions to avoid\n" + render_misinterpretations(spec),
    ]
    if stage == "families":
        sections += [
            "## Where a generic assistant is expected to answer differently\n"
            + render_divergence_hypotheses(spec),
            "## Situation domains to cover\n" + render_domains(spec),
            "## Topics this pilot must not build scenarios about\n"
            + render_avoided_topics(spec),
        ]
    sections.append("## Cue policy\n" + render_cue_policy(spec))
    return "\n\n".join(sections)


def render_open_questions(spec: TargetSpec) -> str:
    """The clauses the reviewer must protect: what each unresolved item leaves open.

    A tradeoff marked unresolved may carry `resolved_part` and `open_question`; where a spec
    has not been updated yet, the whole description is treated as open.
    """
    lines: list[str] = []
    for tradeoff in spec.tradeoffs:
        if not tradeoff.get("unresolved"):
            continue
        resolved = str(tradeoff.get("resolved_part", "")).strip()
        open_question = str(tradeoff.get("open_question", "")).strip()
        lines.append(f"{tradeoff.get('id')}:")
        if resolved:
            lines.append(f"  SETTLED, be decisive about this: {resolved}")
        lines.append(
            f"  OPEN, do not settle this: {open_question or str(tradeoff.get('description', '')).strip()}"
        )
    for choice in spec.unresolved_choices:
        policy = str(choice.get("generation_policy", "")).strip()
        if policy not in ("mark_ambiguous", "avoid"):
            continue
        lines.append(f"{choice.get('id')}:")
        lines.append(f"  OPEN, do not settle this: {str(choice.get('question', '')).strip()}")
    return "\n".join(lines) if lines else "(this target marks nothing as open)"


def render_signature_moves(spec: TargetSpec) -> str:
    moves = spec.signature_moves
    if not moves:
        return ""
    return "\n".join(
        f"    - {move.get('id') or move.get('name')}: {str(move.get('description', '')).strip()}"
        for move in moves
    )


def render_for_reviewer(spec: TargetSpec, layer_ids: list[str] | None = None) -> str:
    """The reviewer needs the same target plus the red flags, not the coverage plan."""
    return "\n\n".join(
        [
            f"# Target: {spec.name} (id {spec.target_id}, spec version {spec.version})",
            "## How this target judges\n" + spec.summary,
            "## Principles\n" + render_principles(spec, None, layer_ids),
            "## Limits the target imposes on itself\n" + render_boundaries(spec),
            "## Genuine tradeoffs\n" + render_tradeoffs(spec),
            "## Open interpretation questions (a confident resolution is a defect)\n"
            + render_unresolved(spec),
            "## Common distortions (red flags)\n" + render_misinterpretations(spec),
            "## Topics this pilot does not build scenarios about\n"
            + render_avoided_topics(spec)
            + "\nA scenario that is really about one of these is a scenario_quality defect.",
            "## Cue policy\n" + render_cue_policy(spec),
        ]
    )
