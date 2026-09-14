#!/usr/bin/env python
"""Script arm of the drafter: turn a subject into a draft persona spec, from model memory.

    python persona_generalizer/draft_persona.py --subject "Adela Renn" --id renn
    python persona_generalizer/draft_persona.py --subject "..." --id x --dry-run

**The skill is the default arm; this is the fallback and the comparison arm.** The difference is
acquisition. `skills/draft-persona/SKILL.md` is run by an agent with web search, so it acquires
real sources, checks robots.txt, honours AI-use refusals, and records URLs and access dates. This
script has none of that: it asks a Fireworks model what it already remembers. It therefore cannot
tell an apocryphal quotation from an attested one, and it cannot reach the registers and minutes
where deeds live.

What it is good for: running the same four passes reproducibly, with every call costed in
`usage.jsonl` like any other pipeline stage, so the two arms can be compared on the same subject.
Keep both outputs and read them side by side; that comparison is the point of building this.

Everything it emits is marked unverified, and `research_notes.md` carries the checklist a human
must work through before the spec is used for anything.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import yaml  # noqa: E402

from pipeline.config import load_config  # noqa: E402
from pipeline.model import ModelClient, ModelError  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import draft_prompts as P  # noqa: E402
import scope  # noqa: E402
import websearch  # noqa: E402

LOGGER = logging.getLogger("draft_persona")
PERSONAS_DIR = REPO_ROOT / "persona_generalizer" / "personas"
KIND_PREFIX = {"circumstance": "C", "deed": "D", "words": "W", "testimony": "T"}


def fill(template: str, **values: str) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", str(value))
    return template


def messages(prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": P.SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]


async def run_pass(client: ModelClient, prompt: str, stage: str, max_tokens: int) -> Any:
    payload, response = await client.complete_json(
        "generator", messages(prompt), stage=stage, record_id=stage, max_tokens=max_tokens
    )
    # ModelResponse carries the provider's raw `usage` dict; there is no completion_tokens
    # attribute. Read defensively and never raise here: by this point the call has been made and
    # paid for, and a logging line that crashes throws away work that already cost money. At
    # reasoning_effort: max most of the spend is reasoning, so it is worth showing separately.
    usage = getattr(response, "usage", None) or {}
    details = usage.get("completion_tokens_details") or {}
    completion = usage.get("completion_tokens")
    reasoning = details.get("reasoning_tokens")
    LOGGER.info(
        "%s: %s completion tokens%s",
        stage,
        completion if completion is not None else "?",
        f" ({reasoning} reasoning)" if reasoning else "",
    )
    return payload


def normalise_evidence(payload: Any) -> list[dict[str, Any]]:
    """Give every item a stable prefixed id, so spec `sources` and passage headings agree."""
    items = payload.get("evidence") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise ModelError("evidence pass did not return a list")
    seen: dict[str, int] = {}
    out: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict) or not item.get("body"):
            continue
        kind = str(item.get("kind", "")).strip().lower()
        prefix = KIND_PREFIX.get(kind, "X")
        seen[prefix] = seen.get(prefix, 0) + 1
        item["kind"] = kind
        item["id"] = f"{prefix}{seen[prefix]}"
        out.append(item)
    return out


def remap_sources(node: Any, valid: set[str], dropped: set[str]) -> Any:
    """Strip cited ids the evidence pass did not actually produce, recording what was dropped.

    The composition pass cites from memory of its own earlier output and sometimes invents an id.
    A spec that cites a passage which does not exist fails to load, so the ids are filtered here
    and the loss is reported rather than silently repaired.
    """
    if isinstance(node, dict):
        out = {}
        for key, value in node.items():
            if key == "sources" and isinstance(value, list):
                kept = [s for s in value if s in valid]
                dropped.update(str(s) for s in value if s not in valid)
                out[key] = kept
            else:
                out[key] = remap_sources(value, valid, dropped)
        return out
    if isinstance(node, list):
        return [remap_sources(v, valid, dropped) for v in node]
    return node


def render_key_passages(
    subject: str, evidence: list[dict[str, Any]], sourced: bool = False
) -> str:
    order = ["circumstance", "words", "deed", "testimony"]
    labels = {
        "circumstance": "Circumstance: the world that produced them",
        "words": "Words: what they wrote or were recorded saying",
        "deed": "Deeds: what they are documented to have done",
        "testimony": "Testimony: what others recorded about them",
    }
    banner = (
        [
            "**DRAFT, PARTLY SOURCED.** Produced by `draft_persona.py --search`. Entries carrying a",
            "Source line were drafted with a retrieved page in front of the model; entries without",
            "one came from its memory alone. Neither has been checked against a primary source, and",
            "a retrieved page is not a primary source. Verify each entry before generating from it.",
        ]
        if sourced
        else [
            "**DRAFT, UNVERIFIED.** Produced by `draft_persona.py` from a model's own memory, with no",
            "sources consulted. Every entry below is a paraphrase or a reconstruction and none of it",
            "has been checked against a source. Nothing here may be used to generate a dataset until a",
            "human has verified each entry and replaced it with sourced material. See",
            "`research_notes.md` for the checklist.",
        ]
    )
    lines = [f"# Key passages — {subject}", ""] + banner + [""]
    for kind in order:
        items = [e for e in evidence if e.get("kind") == kind]
        if not items:
            continue
        lines += ["---", "", f"**{labels[kind]}**", ""]
        for item in items:
            title = str(item.get("title") or "").strip()
            heading = f"### {item['id']}" + (f" — {title}" if title else "")
            lines.append(heading)
            period = str(item.get("period") or "").strip()
            if period:
                lines.append(f"*Period:* {period}")
            lines.append(str(item.get("body") or "").strip())
            # The marker has to be on its own line for pipeline.target to parse it, and it is
            # written for every passage rather than only the reconstructed ones: a spec whose
            # verdict is admit_reconstructed must declare it everywhere, and a defaulted
            # "attested" is indistinguishable from a considered one.
            basis = str(item.get("evidence_basis") or "attested").strip().lower()
            lines.append(f"evidence_basis: {basis if basis in ('attested', 'reconstructed') else 'reconstructed'}")
            if item.get("bears_on"):
                lines.append(f"Bearing on: {item['bears_on']}")
            if item.get("source_url"):
                lines.append(f"Source: {item['source_url']}")
            lines.append(
                f"*Confidence: {item.get('confidence', 'unknown')}. "
                f"Verify: {item.get('verify', 'everything in this entry')}*"
            )
            lines.append("")
    return "\n".join(lines) + "\n"


def build_spec(persona_id: str, subject: str, spec: dict[str, Any], sufficiency: dict[str, Any],
               conflicts: list[dict[str, Any]], valid: set[str]) -> tuple[dict[str, Any], set[str]]:
    dropped: set[str] = set()
    spec = remap_sources(spec, valid, dropped)
    conflicts = [c for c in conflicts if c.get("said") in valid and c.get("did") in valid]

    out: dict[str, Any] = {
        "id": persona_id,
        "name": spec.get("name") or subject,
        "version": "0.1-draft",
        "subject": spec.get("subject") or {},
        "context": spec.get("context") or {},
        "formation": spec.get("formation") or [],
        "conflicts": conflicts,
        "summary": spec.get("summary") or "",
        "principles": spec.get("principles") or [],
        "boundaries": spec.get("boundaries") or [],
        "tradeoffs": spec.get("tradeoffs") or [],
        "misinterpretations": spec.get("misinterpretations") or [],
        "voice": spec.get("voice") or {},
        "epistemic_horizon": spec.get("epistemic_horizon") or {},
        "deliberation_shape": spec.get("deliberation_shape") or "",
        "signature_moves": spec.get("signature_moves") or [],
        "divergence_hypotheses": spec.get("divergence_hypotheses") or [],
        "domains": spec.get("domains") or [],
        "cue_policy": spec.get("cue_policy") or {},
        "sufficiency": {
            key: sufficiency.get(key, "")
            for key in (
                "verdict",
                "first_person_volume",
                "decisions_with_reasoning",
                "domain_breadth",
                "contestedness",
                "testimonial_variety",
                "scope_check",
                "caveats",
            )
        },
        "reference_material": [
            {
                "id": "key_passages",
                "path": "references/key_passages.md",
                "title": f"Drafted passages — {subject}",
                "use": "grounding",
                "license": "UNKNOWN — drafted from model memory; establish before any export",
                "notes": "unverified draft; the only file placed into prompts",
            }
        ],
        "attribution_policy": {
            "statement": (
                "Every response in a dataset built from this spec is synthesised. It is a "
                "construction of how this person would judge, not a record of anything they "
                "said. No generated text may be formatted as a quotation, dated, or attributed "
                "to a source document."
            ),
            "subject_status": (
                "fictional_character"
                if str((spec.get("subject") or {}).get("kind")) == "fictional"
                else "deceased_public_figure"
            ),
            "declare_in_manifest": True,
        },
        "redistribution_note": spec.get("redistribution_note")
        or "UNVERIFIED DRAFT. Source licences are unestablished; do not redistribute any export.",
    }
    return out, dropped


def render_sources(subject: str) -> str:
    return f"""# SOURCES — {subject}

**NO SOURCES WERE CONSULTED.** This ledger is empty on purpose. `draft_persona.py` works from a
model's own memory and has no web access, so it cannot record a URL, an access date, a licence or
a `robots.txt` check, because it performed none of them.

This is the difference between the two drafter arms, and it is not a small one. The skill arm
(`persona_generalizer/skills/draft-persona/SKILL.md`) acquires real sources under the ledger
discipline in `targets/confucian/SOURCES.md`. This arm does not.

Before this persona is used for anything, every row below must be filled in by hand.

| file | work | edition | URL | access date | licence | AI-use restrictions | use |
|---|---|---|---|---|---|---|---|
| `references/key_passages.md` | — | — | — | — | **UNKNOWN** | — | grounding |

## Consulted and deliberately not ingested

None; nothing was retrieved.

## Reproducing the acquisition

There was no acquisition. Re-run the drafter with the skill arm, or acquire the sources by hand
following the five steps in `persona_generalizer/README.md`.
"""


def render_verification(notes: list[str]) -> list[str]:
    """The audit section of research_notes.md — what a second model family flagged, and why."""
    lines = ["", "## Verification against the retrieved material", ""]
    if not notes:
        lines += [
            "A second model family audited every drafted item against the pages actually "
            "retrieved, looking for claims marked attested that the material does not state, "
            "works named as though consulted when no page of them was fetched, and hedges "
            "dropped from the source. **It flagged nothing.** That is a weaker result than it "
            "sounds: an audit finding nothing is also what a lazy audit looks like, and a "
            "reviewer should spot-check a handful of attested items by hand before trusting it.",
        ]
        return lines
    lines += [
        f"A second model family audited the drafted items against the pages actually retrieved "
        f"and flagged **{len(notes)}**. Each was downgraded rather than deleted: the claim may "
        f"well be true, and the honest repair is to stop calling it attested, not to pretend it "
        f"was never made. A downgrade is a prompt to go and find the source, not a verdict that "
        f"the claim is false.",
        "",
    ]
    lines += notes
    return lines


def render_notes(subject: str, sufficiency: dict[str, Any], evidence: list[dict[str, Any]],
                 conflicts: list[dict[str, Any]], dropped: set[str],
                 verification_notes: list[str] | None = None) -> str:
    low = [e for e in evidence if str(e.get("confidence", "")).lower() in ("low", "medium")]
    lines = [
        f"# Research notes — {subject} (DRAFT)",
        "",
        "Produced by `draft_persona.py`, the script arm of the drafter, working from a model's own",
        "memory with no sources consulted. **Nothing here is verified.** This file is the checklist",
        "a human works through before the spec is used.",
        "",
        "## 1. Sufficiency",
        "",
        f"Verdict: **{sufficiency.get('verdict', 'unknown')}**. "
        f"{sufficiency.get('reasoning', '')}",
        "",
        f"- Binding criterion (decisions with reasoning): {sufficiency.get('decisions_with_reasoning', '—')}",
        f"- First-person volume: {sufficiency.get('first_person_volume', '—')}",
        f"- Contestedness: {sufficiency.get('contestedness', '—')}",
        "",
        "This verdict was reached without consulting anything and is the least trustworthy part of",
        "the draft. Re-run the gate against real sources before accepting it.",
        "",
        "## 2. Every passage needs verification",
        "",
        f"{len(evidence)} passages were drafted; none is sourced. No entry is a verbatim quotation",
        "— all are paraphrases or reconstructions — but a paraphrase of something the person never",
        "said is still a fabrication. Check each against a primary source, or delete it.",
        "",
    ]
    if low:
        lines += ["Entries the model itself flagged as medium or low confidence:", ""]
        lines += [
            f"- `{e['id']}` ({e.get('kind')}): {e.get('verify', 'verify everything')}" for e in low
        ]
        lines.append("")
    lines += [
        "## 3. Conflicts and how each resolved",
        "",
    ]
    if conflicts:
        for conflict in conflicts:
            lines.append(
                f"- **{conflict.get('id')}** — {conflict.get('said')} against "
                f"{conflict.get('did')} → `{conflict.get('resolution')}` "
                f"(confidence: {conflict.get('confidence', 'unknown')})"
            )
        lines.append("")
        lines.append(
            "Each resolution rests on an unsourced chronology. Where a conflict resolved as a "
            "change of view over time, check the dates first: that reading collapses if the "
            "statement postdates the conduct."
        )
    else:
        lines.append(
            "None found. This is more often a failure of research than a fact about the person, "
            "and this arm cannot reach the institutional records where deeds live. Treat an empty "
            "conflicts list from the script arm as unexamined rather than as settled."
        )
    lines += [
        "",
        "## 4. Known losses in this draft",
        "",
    ]
    if dropped:
        lines.append(
            f"The composition pass cited {len(dropped)} passage id(s) that the evidence pass never "
            f"produced; they were stripped so the spec would load: "
            + ", ".join(f"`{d}`" for d in sorted(dropped))
            + ". Any section that now cites nothing needs sources adding by hand."
        )
    else:
        lines.append("No invented passage ids were cited.")
    lines += [
        "",
        "## 5. Before this is used",
        "",
        "1. Verify every passage against a real source, or delete it.",
        "2. Fill in `SOURCES.md` completely; establish the licence of everything.",
        "3. Re-run the sufficiency gate against what actually survives.",
        "4. Re-adjudicate every conflict against a sourced chronology.",
        "5. Run `python persona_generalizer/check_persona.py <id>` until clean.",
        "6. Compare against the skill arm's draft of the same subject and reconcile the two.",
        "",
    ]
    lines += render_verification(verification_notes or [])
    return "\n".join(lines)


# Acquisition text goes straight into the sufficiency and evidence prompts, so it is a token
# budget rather than storage. `websearch.fetch` returns up to 4,000 words per page and a full
# run retrieves two pages for each of ten slots, which is ~80,000 words — more than the
# generator's whole budget, and the repair retry then resends it along with the failed output.
# Budget it here instead, and tell the model where it is reading an excerpt so it does not treat
# a cut-off page as a complete source.
ACQUIRED_WORDS_PER_PAGE = 800
# A transcription gets far more room than a summary. Everything upstream — source tiering,
# cross-language search, native-title lookup, the condensation guards — exists to put the primary
# text in front of the drafter, and an 800-word cap applied at the last step threw most of it
# away again: a 13,000-word biography arrived as its first 800 words. That is why a run whose
# slots were intact still had 56% of its passages downgraded as unsupported. The drafter was
# writing from memory because it had not been shown the source.
ACQUIRED_WORDS_PER_PRIMARY_PAGE = 6000
ACQUIRED_WORDS_TOTAL = 16000


def format_acquired(
    acquired: dict[str, list],
    *,
    words_per_page: int = ACQUIRED_WORDS_PER_PAGE,
    words_total: int = ACQUIRED_WORDS_TOTAL,
) -> str:
    """Flatten the acquisition into prompt text, slot by slot, gaps included and size bounded."""
    blocks: list[str] = []
    budget = words_total
    for slot, pages in acquired.items():
        if not pages:
            blocks.append(f"## {slot}\n\n(nothing retrieved for this slot — record it as a gap)")
            continue
        for result, text in pages:
            if budget <= 0:
                blocks.append(
                    f"## {slot}\n\n(further pages retrieved but omitted from this prompt for "
                    f"length; see SOURCES.md for the full ledger)"
                )
                break
            words = text.split()
            per_page = (
                ACQUIRED_WORDS_PER_PRIMARY_PAGE
                if websearch.source_tier(result.url) == "primary"
                else words_per_page
            )
            allowance = min(per_page, budget)
            excerpt = " ".join(words[:allowance])
            budget -= min(len(words), allowance)
            truncated = "\n\n[excerpt truncated]" if len(words) > allowance else ""
            # The tier travels with the excerpt. Without it a Wikipedia summary and an archive
            # transcript arrive in the prompt looking identical, and the drafter has no way to
            # apply the tiering the skill asks for.
            tier = websearch.source_tier(result.url)
            tier_line = (
                "TIER: tertiary — a summary of the sources, not evidence. Use it to find what to "
                "look for; do not build a passage on it.\n"
                if tier == "tertiary"
                else ""
            )
            blocks.append(
                f"## {slot}\n\nURL: {result.url}\nTITLE: {result.title}\n{tier_line}\n"
                f"{excerpt}{truncated}"
            )
    return "\n\n".join(blocks)


async def verify_evidence(
    client: "ModelClient", evidence: list[dict], acquired_text: str, max_tokens: int
) -> dict:
    """Audit drafted items against the retrieved material, using a DIFFERENT model family.

    This is the pass the script arm was missing, and the absence shows in its output: one draft
    cited a third-century history 111 times having retrieved it zero times, and marked those
    passages attested. A drafter cannot find that in its own work. The reviewer role is used
    rather than the generator precisely so the check comes from somewhere else — a model auditing
    its own output measures nothing.

    Findings downgrade an item's evidence_basis rather than deleting it: the claim may well be
    true, and the honest repair is to stop calling it attested, not to pretend it was never made.
    """
    if not evidence or not acquired_text:
        return {}
    items = json.dumps(
        [
            {k: e.get(k) for k in ("id", "kind", "title", "body", "evidence_basis", "source_url")}
            for e in evidence
        ],
        indent=1,
        ensure_ascii=False,
    )
    prompt = fill(P.VERIFY_PROMPT, items=items[:60000], sources=acquired_text[:60000])
    try:
        payload, _ = await client.complete_json(
            "reviewer", messages(prompt), stage="verify", record_id="verify",
            max_tokens=max_tokens,
        )
    except ModelError as error:
        LOGGER.warning("  verification failed (%s); evidence is unaudited", error)
        return {}
    return payload if isinstance(payload, dict) else {}


def apply_verification(evidence: list[dict], findings: dict) -> list[str]:
    """Downgrade flagged items and return a human-readable list of what changed."""
    by_id = {str(e.get("id")): e for e in evidence}
    notes: list[str] = []
    for category, new_basis in (
        ("unsupported", "reconstructed"),
        ("laundered", "mixed"),
        ("overstated", "mixed"),
    ):
        for finding in findings.get(category) or []:
            item = by_id.get(str((finding or {}).get("id")))
            if not item:
                continue
            was = item.get("evidence_basis", "attested")
            if was == "attested":
                item["evidence_basis"] = new_basis
            notes.append(
                f"- `{item.get('id')}` flagged {category}: "
                f"{(finding or {}).get('why', '')} (evidence_basis {was} -> "
                f"{item.get('evidence_basis')})"
            )
    return notes


async def condense_acquired(
    client: "ModelClient", acquired: dict, max_tokens: int
) -> dict:
    """Replace each slot's raw pages with one condensed account, per docs/condensing-sources.md.

    Raw pages arrive as navigation chrome, cookie notices and restatement, and the passage budget
    then spends itself on those rather than on the source. Condensing first is cheaper than
    raising the budget, because the budget is paid again on every row the pipeline later
    generates. A slot whose condensation fails keeps its raw pages rather than being lost.
    """
    out: dict = {}
    for slot, pages in acquired.items():
        if not pages:
            out[slot] = pages
            continue
        # A slot carrying a transcription is not condensed at all. The guideline says a primary
        # text passes through close to whole, and on the first live run this slot went from
        # 16,476 words to 32 — the model discarded the source instead of compressing it, and the
        # one slot that mattered most was the one destroyed. Asking a model to be careful is not
        # a control; not asking it is.
        if any(websearch.source_tier(r.url) == "primary" for r, _ in pages):
            LOGGER.info("  %s: holds a primary source, left uncondensed", slot)
            out[slot] = pages
            continue
        joined = "\n\n".join(
            f"URL: {result.url}\nTIER: {websearch.source_tier(result.url)}\n\n{text}"
            for result, text in pages
        )
        prompt = fill(P.CONDENSE_PROMPT, slot=slot, pages=joined[:60000])
        try:
            payload = await run_pass(client, prompt, f"condense:{slot}", max_tokens)
        except ModelError as error:
            LOGGER.warning("  %s: condensation failed (%s); keeping raw pages", slot, error)
            out[slot] = pages
            continue
        condensed = str((payload or {}).get("condensed") or "").strip()
        before = sum(len(text.split()) for _, text in pages)
        after = len(condensed.split())
        # Thresholds calibrated against a real run rather than guessed. Measured ratios across
        # ten slots came out bimodal, which is what makes a cutoff possible at all:
        #
        #   legitimate   11.9%  12.4%  13.4%  14.7%  15.9%  26.3%  28.9%
        #   catastrophic  0.1%   0.2%   4.7%          <- deeds, words, formation
        #
        # A first guess of 20% would have rejected five of the seven good ones. 8% sits in the
        # empty band between the clusters. The absolute floor is there because ratio alone cannot
        # express the real failure: 26 words is useless whatever it came from.
        if not condensed or after < 100 or (before and after < before * 0.08):
            LOGGER.warning(
                "  %s: condensation returned %d words from %d (%.1f%%, under the floor); "
                "keeping the raw pages", slot, after, before,
                (after / before * 100) if before else 0.0,
            )
            out[slot] = pages
            continue
        LOGGER.info(
            "  %s: %d -> %d words", slot,
            sum(len(t.split()) for _, t in pages), len(condensed.split()),
        )
        # Keep the best-ranked result as the carrier so the URL and tier survive.
        carrier = pages[0][0]
        out[slot] = [(carrier, condensed)]
    return out


async def draft(subject: str, persona_id: str, config_path: str, out_dir: Path,
                target_count: int, max_tokens: int, use_search: bool = False,
                acquisition_passes: int = 3, condense: bool = True,
                source_languages: tuple[str, ...] = ()) -> int:
    # Scope is checked before anything is loaded, created or spent. The gate that follows asks
    # whether enough material survives; this asks whether a faithful persona of this subject
    # should be built at all, and no amount of evidence changes the answer. Running it here means
    # an out-of-scope subject costs nothing rather than a full acquisition pass.
    hit = scope.tripwire_match(subject)
    if hit is not None:
        needle, why = hit
        print(scope.refusal_message(subject, needle, why), file=sys.stderr)
        return 2

    # A refusal costs the same research as an admission. If this subject has been through the
    # gate before, say so loudly before spending anything again — the previous verdict may be
    # revisitable (refuse_acquisition usually is) but it should be an explicit decision, not an
    # accident of nobody having looked.
    prior = out_dir / "_refused"
    if prior.is_dir():
        needle = {w for w in scope._normalise(subject).split() if len(w) > 2}
        for record in sorted(prior.glob("*.md")):
            if record.name == "README.md":
                continue
            stem = set(scope._normalise(record.stem.replace("-", " ")).split())
            if needle and stem and (needle & stem) == stem:
                first = record.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
                LOGGER.warning(
                    "prior refusal on record for this subject: %s (%s). Proceeding, but read it "
                    "before trusting a different verdict.", first, record,
                )

    config = load_config(config_path)
    root = out_dir / persona_id
    (root / "references").mkdir(parents=True, exist_ok=True)

    ledger: websearch.Acquisition | None = None
    backend: "websearch.SearchBackend | None" = None
    acquired_text = ""
    if use_search:
        backend = websearch.backend_from_env()
        if backend is None:
            print(
                "error: --search needs a search provider. Set one of BRAVE_SEARCH_API_KEY, "
                "SERPER_API_KEY or TAVILY_API_KEY.",
                file=sys.stderr,
            )
            return 2
        LOGGER.info(
            "pass 0/4: acquisition (%s), up to %d escalating pass(es)",
            backend.name,
            acquisition_passes,
        )
        ledger = websearch.Acquisition()
        acquired, acquisition_log = websearch.acquire_escalating(
            subject,
            backend,
            ledger,
            max_passes=acquisition_passes,
            source_languages=source_languages,
        )
        acquired_text = format_acquired(acquired)
        if condense:
            LOGGER.info("pass 0b/4: condensing retrieved pages")
            async with ModelClient.from_config(
                load_config(config_path), root / "usage.jsonl", stage="condense"
            ) as condenser:
                acquired = await condense_acquired(condenser, acquired, max_tokens)
        LOGGER.info(
            "  acquisition text for prompts: %d words (budget %d)",
            len(acquired_text.split()),
            ACQUIRED_WORDS_TOTAL,
        )
        for entry in acquisition_log:
            LOGGER.info(
                "  pass %s (%s): %s slot(s) filled, thin: %s",
                entry["pass"], entry["strategy"], entry["slots_filled"],
                ", ".join(entry["slots_thin"]) or "none",
            )
        LOGGER.info(
            "  %d page(s) retrieved, %d declined, %d queries",
            len(ledger.fetched), len(ledger.declined), len(ledger.searches),
        )
        # Which refusal a thin acquisition warrants is the drafter's most useful output when it
        # has fallen short: "I did not reach it" and "it does not survive" are different findings
        # and the gate prompt should not have to guess which one it is looking at.
        suggested, why = websearch.gate_verdict_for_gaps(
            acquired, acquisition_log, max_passes=acquisition_passes
        )
        if suggested:
            LOGGER.warning("  gate hint: %s — %s", suggested, why)
            acquired_text += (
                f"\n\nACQUISITION SHORTFALL. Suggested gate verdict: {suggested}. {why}"
            )

    async with ModelClient.from_config(config, root / "usage.jsonl", stage="draft") as client:
        LOGGER.info("pass 1/4: sufficiency gate")
        sufficiency = await run_pass(
            client, fill(P.SUFFICIENCY_PROMPT, subject=subject), "sufficiency", max_tokens
        )
        if not isinstance(sufficiency, dict):
            print("error: sufficiency pass did not return an object", file=sys.stderr)
            return 2
        if sufficiency.get("living_private_individual") is True:
            print(
                f"refused: '{subject}' appears to be a living private individual, which is out of "
                f"scope. Public figures, historical subjects and fictional characters are in scope.",
                file=sys.stderr,
            )
            return 2
        # Every refusal halts, not just the legacy bare "refuse". When the gate learned to say
        # refuse_evidence / refuse_acquisition / refuse_scope, an equality test against "refuse"
        # stopped matching any of them and the drafter would have built the spec out anyway —
        # which is precisely the outcome the gate exists to prevent.
        verdict = str(sufficiency.get("verdict") or "")
        if verdict.startswith("refuse"):
            guidance = {
                "refuse_acquisition": (
                    "This is a finding about the search, not about the subject. Escalate: raise "
                    "--acquisition-passes, or supply --source-languages for the languages the "
                    "sources actually survive in, and run the gate again."
                ),
                "refuse_scope": (
                    "Out of scope whatever the evidence shows. See persona_generalizer/scope.py."
                ),
            }.get(verdict, "This is a finding about the sources; a further pass will not change it.")
            print(
                f"refused ({verdict}): '{subject}' is not admissible as a persona target.\n"
                f"  {sufficiency.get('reasoning', '')}\n"
                f"  {guidance}\n"
                f"A refusal is a real answer; no spec was written. Record it in "
                f"persona_generalizer/personas/_refused/.",
                file=sys.stderr,
            )
            return 2

        # Batched by kind rather than asked for in one call. Seventy structured items in a
        # single JSON response is the largest generation in this repository and it failed three
        # different ways on live runs: truncation at the token ceiling, a read timeout, and — with
        # a reasoning model at maximum effort — 88,000 characters of planning prose where the
        # object should have been. Four smaller calls each fit comfortably, a failure costs one
        # kind rather than the whole pass, and the weighting the schema wants is enforced by
        # construction instead of by asking the model to remember it.
        LOGGER.info("pass 2/4: evidence (batched by kind)")
        shares = (("circumstance", 0.34), ("deed", 0.32), ("words", 0.20), ("testimony", 0.14))
        evidence: list[dict[str, Any]] = []
        for kind, share in shares:
            want = max(4, round(target_count * share))
            used = [str(e.get("id")) for e in evidence]
            kind_prompt = fill(
                P.EVIDENCE_PROMPT,
                subject=subject,
                target_count=str(want),
                kind_clause=f", ALL of kind {kind!r}",
                id_clause=(
                    f"Ids already used, which you must not reuse: {', '.join(used)}"
                    if used
                    else "Use short stable ids appropriate to the kind, e.g. C1 / D1 / W1 / T1."
                ),
            )
            if acquired_text:
                kind_prompt = (
                    fill(P.SOURCED_PREAMBLE, sources=acquired_text) + "\n\n" + kind_prompt
                )
            try:
                batch = normalise_evidence(
                    await run_pass(client, kind_prompt, f"evidence:{kind}", max_tokens)
                )
            except ModelError as error:
                # One kind failing should not throw away the other three.
                LOGGER.warning("  %s batch failed (%s); continuing without it", kind, error)
                continue
            seen = {str(e.get("id")) for e in evidence}
            batch = [e for e in batch if str(e.get("id")) not in seen]
            evidence.extend(batch)
            LOGGER.info("  %s: %d item(s)", kind, len(batch))
        if not evidence:
            print(
                f"error: the evidence pass produced nothing for '{subject}'. No spec was written.",
                file=sys.stderr,
            )
            return 2
        LOGGER.info("  %d passages", len(evidence))
        evidence_text = json.dumps(
            [{k: e.get(k) for k in ("id", "kind", "title", "period", "body")} for e in evidence],
            indent=1,
        )

        verification_notes: list[str] = []
        reacquired_notes: list[str] = []
        if acquired_text:
            LOGGER.info("pass 2b/4: verifying evidence against the retrieved material")
            findings = await verify_evidence(client, evidence, acquired_text, max_tokens)

            # The audit names documents worth having that no query written in advance could have
            # known to ask for: a passage citing a chronicle nobody fetched IS the search term.
            # So the findings become an acquisition target, and the evidence is judged again
            # against the enlarged material — otherwise a claim would be downgraded for resting
            # on a source we had simply not gone and got.
            needs = [
                str(f.get("work_named") or "").strip()
                for f in (findings.get("laundered") or [])
                if str(f.get("work_named") or "").strip()
            ]
            if needs and backend is not None and ledger is not None:
                LOGGER.info("pass 2c/4: re-acquiring %d source(s) the audit named", len(needs))
                extra = websearch.reacquire_for_gaps(subject, backend, ledger, needs)
                if extra:
                    acquired.setdefault("reacquired", []).extend(extra)
                    acquired_text = format_acquired(acquired)
                    reacquired_notes = [
                        f"- looked for `{need}` after the audit named it; "
                        f"{len(extra)} page(s) retrieved"
                        for need in needs
                    ]
                    LOGGER.info("  %d page(s) retrieved; re-verifying", len(extra))
                    findings = await verify_evidence(
                        client, evidence, acquired_text, max_tokens
                    )

            verification_notes = apply_verification(evidence, findings)
            LOGGER.info(
                "  %d item(s) downgraded by the audit", len(verification_notes)
            )

        LOGGER.info("pass 3/4: conflicts")
        conflicts_payload = await run_pass(
            client,
            fill(P.CONFLICTS_PROMPT, subject=subject, evidence=evidence_text),
            "conflicts",
            max_tokens,
        )
        conflicts = conflicts_payload.get("conflicts", []) if isinstance(conflicts_payload, dict) else []

        LOGGER.info("pass 4/4: composition")
        spec_payload = await run_pass(
            client,
            fill(
                P.SPEC_PROMPT,
                subject=subject,
                evidence=evidence_text,
                conflicts=json.dumps(conflicts, indent=1),
            ),
            "spec",
            max_tokens,
        )

    valid = {e["id"] for e in evidence}
    spec, dropped = build_spec(persona_id, subject, spec_payload, sufficiency, conflicts, valid)

    (root / "spec.yaml").write_text(
        "# DRAFT — produced by draft_persona.py from model memory, with no sources consulted.\n"
        "# Every passage it cites is unverified. See research_notes.md before using this.\n\n"
        + yaml.safe_dump(spec, sort_keys=False, allow_unicode=True, width=96),
        encoding="utf-8",
    )
    (root / "references" / "key_passages.md").write_text(
        render_key_passages(subject, evidence, sourced=bool(ledger)), encoding="utf-8"
    )
    (root / "SOURCES.md").write_text(
        websearch.render_sources(subject, ledger) if ledger else render_sources(subject),
        encoding="utf-8",
    )
    (root / "research_notes.md").write_text(
        render_notes(
            subject, sufficiency, evidence, conflicts, dropped,
            (reacquired_notes + verification_notes) if reacquired_notes else verification_notes,
        ),
        encoding="utf-8",
    )

    print(f"draft written to {root}")
    print(f"  sufficiency: {sufficiency.get('verdict')}")
    print(f"  passages: {len(evidence)}   conflicts: {len(conflicts)}")
    if dropped:
        print(f"  stripped {len(dropped)} invented passage id(s): {', '.join(sorted(dropped))}")
    print(f"\nThis is an UNVERIFIED draft. Read {root / 'research_notes.md'} before using it.")
    print(f"Then: python persona_generalizer/check_persona.py {persona_id}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="draft_persona.py",
        description="Draft a persona spec from model memory. The fallback arm; prefer the skill.",
    )
    parser.add_argument("--subject", required=True, help='the person, e.g. "Adela Renn"')
    parser.add_argument("--id", dest="persona_id", required=True, help="lowercase slug")
    parser.add_argument("--config", default="configs/pilot.yaml")
    parser.add_argument("--out", default=None, help="output directory (default personas/)")
    parser.add_argument(
        "--passages", type=int, default=70, help="passages to ask for (schema wants 60-120)"
    )
    parser.add_argument("--max-tokens", type=int, default=24000)
    parser.add_argument(
        "--search",
        action="store_true",
        help="acquire real sources first (needs BRAVE_SEARCH_API_KEY, SERPER_API_KEY or "
        "TAVILY_API_KEY). Off by default: the script arm exists to be compared against the "
        "skill arm, and search is what separates them.",
    )
    parser.add_argument(
        "--acquisition-passes",
        type=int,
        default=3,
        help="how many escalating acquisition passes to allow (default 3: slot search, then "
        "reference harvesting, then cross-language). Later passes only run for slots still "
        "empty, so a well-covered subject costs no more than 1. Set 1 to disable escalation.",
    )
    parser.add_argument(
        "--source-languages",
        default="",
        help="comma-separated language codes where this subject's sources actually survive, e.g. "
        "'el,ar,hy'. Used by the cross-language pass. Asked for rather than inferred: ranking "
        "languages by article size measures editor population, not where the record is.",
    )
    parser.add_argument(
        "--no-condense",
        dest="condense",
        action="store_false",
        help="feed raw retrieved pages to the drafter instead of condensing them first. Kept so "
        "the two paths can be compared on one subject; the ratios in "
        "persona_generalizer/docs/condensing-sources.md are untested.",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="print the plan and exit without calling a model"
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )
    out_dir = Path(args.out) if args.out else PERSONAS_DIR

    if args.dry_run:
        backend = websearch.backend_from_env() if args.search else None
        if args.search:
            acquisition = (
                f"  pass 0: acquisition over {len(websearch.COVERAGE_QUERIES)} coverage slots via "
                f"{backend.name}, robots.txt honoured; up to {args.acquisition_passes} escalating "
                f"pass(es)"
                + (f", languages {args.source_languages}" if args.source_languages else "")
                + "\n"
                if backend
                else "  pass 0: SEARCH REQUESTED BUT NO PROVIDER CONFIGURED — set "
                "BRAVE_SEARCH_API_KEY, SERPER_API_KEY or TAVILY_API_KEY\n"
            )
        else:
            acquisition = (
                "  no acquisition: works from model memory alone. Add --search to acquire "
                "sources, or use skills/draft-persona/SKILL.md.\n"
            )
        print(
            f"would draft '{args.subject}' as {args.persona_id} into {out_dir / args.persona_id}\n"
            + acquisition
            + f"  4 passes (sufficiency, evidence, conflicts, composition) against the generator "
            f"role in {args.config}\n"
            f"  asking for {args.passages} passages, max_tokens={args.max_tokens}"
        )
        return 0

    try:
        return asyncio.run(
            draft(
                args.subject,
                args.persona_id,
                args.config,
                out_dir,
                args.passages,
                args.max_tokens,
                # Keyword from here on: these are four optional flags of three different types
                # and the positional order has already been got wrong once, which silently put a
                # tuple of languages into the condense switch.
                use_search=args.search,
                acquisition_passes=args.acquisition_passes,
                condense=args.condense,
                source_languages=tuple(
                    c.strip() for c in (args.source_languages or "").split(",") if c.strip()
                ),
            )
        )
    except ModelError as error:
        print(f"error: {error}", file=sys.stderr)
        # ModelError carries the text that failed to parse. Printing only str(error) throws away
        # the one thing that says WHY — truncated JSON, prose, or an empty completion because the
        # whole budget went on reasoning all look identical from the message alone.
        raw = getattr(error, "raw_text", "") or ""
        if raw:
            head = raw.strip()[:600]
            print(
                f"\nlast response ({len(raw)} chars), first 600:\n{head}",
                file=sys.stderr,
            )
        else:
            print(
                "\nthe model returned no text at all. That usually means the whole max_tokens "
                "budget went on reasoning: lower reasoning_effort or raise max_tokens for the "
                "generator role in the config.",
                file=sys.stderr,
            )
        return 2
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
