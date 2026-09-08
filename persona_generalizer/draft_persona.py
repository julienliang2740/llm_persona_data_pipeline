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
    LOGGER.info("%s: %d completion tokens", stage, response.completion_tokens)
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


def render_notes(subject: str, sufficiency: dict[str, Any], evidence: list[dict[str, Any]],
                 conflicts: list[dict[str, Any]], dropped: set[str]) -> str:
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
    return "\n".join(lines)


def format_acquired(acquired: dict[str, list]) -> str:
    """Flatten the acquisition into prompt text, slot by slot, gaps included."""
    blocks: list[str] = []
    for slot, pages in acquired.items():
        if not pages:
            blocks.append(f"## {slot}\n\n(nothing retrieved for this slot — record it as a gap)")
            continue
        for result, text in pages:
            blocks.append(f"## {slot}\n\nURL: {result.url}\nTITLE: {result.title}\n\n{text}")
    return "\n\n".join(blocks)


async def draft(subject: str, persona_id: str, config_path: str, out_dir: Path,
                target_count: int, max_tokens: int, use_search: bool = False) -> int:
    config = load_config(config_path)
    root = out_dir / persona_id
    (root / "references").mkdir(parents=True, exist_ok=True)

    ledger: websearch.Acquisition | None = None
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
        LOGGER.info("pass 0/4: acquisition (%s)", backend.name)
        ledger = websearch.Acquisition()
        acquired = websearch.acquire(subject, backend, ledger)
        acquired_text = format_acquired(acquired)
        LOGGER.info(
            "  %d page(s) retrieved, %d declined, %d queries",
            len(ledger.fetched), len(ledger.declined), len(ledger.searches),
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
        if str(sufficiency.get("verdict")) == "refuse":
            print(
                f"refused: not enough survives about '{subject}' to build a persona from.\n"
                f"  {sufficiency.get('reasoning', '')}\n"
                f"A refusal is a real answer; no spec was written.",
                file=sys.stderr,
            )
            return 2

        LOGGER.info("pass 2/4: evidence")
        evidence_prompt = fill(
            P.EVIDENCE_PROMPT, subject=subject, target_count=str(target_count)
        )
        if acquired_text:
            evidence_prompt = (
                fill(P.SOURCED_PREAMBLE, sources=acquired_text) + "\n\n" + evidence_prompt
            )
        evidence = normalise_evidence(
            await run_pass(client, evidence_prompt, "evidence", max_tokens)
        )
        LOGGER.info("  %d passages", len(evidence))
        evidence_text = json.dumps(
            [{k: e.get(k) for k in ("id", "kind", "title", "period", "body")} for e in evidence],
            indent=1,
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
        render_notes(subject, sufficiency, evidence, conflicts, dropped), encoding="utf-8"
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
                f"{backend.name}, robots.txt honoured\n"
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
                args.search,
            )
        )
    except ModelError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
