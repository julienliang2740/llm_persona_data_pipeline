#!/usr/bin/env python
"""Let the skill arm delegate one pass to a non-Claude model, and record what it cost.

The skill arm is one model doing everything: acquiring, judging the gate, writing the passages
and then checking its own work. That last part is the weakness. A drafter cannot audit its own
systematic bias — if it has quietly imported the popular version of a subject, re-reading its own
passages will not reveal it, because the same priors produced them and approve them.

The pipeline already solved this problem for generated rows, with `reviewer_second`: a model from
a different family reviews the same output and the agreement is recorded. This is that idea moved
upstream, to the draft itself.

What this is FOR:

* **A second opinion on the gate.** The skill states a verdict; a different family runs the same
  criteria over the same evidence, blind to the first answer, and the disagreement is recorded in
  `sufficiency` rather than resolved silently.
* **Adversarial review of the passages.** A different family reads `key_passages.md` against the
  `canon_boundary` and flags entries that read like the legend rather than the record.

What this is NOT for: writing the draft. The skill arm's quality is the agent's judgement, and
delegating the drafting to a cheaper model would trade that away to save a dollar. The value here
is in checking, which is the one thing the drafter cannot do for itself.

Usage:

    python persona_generalizer/ask_model.py --role reviewer --prompt-file /tmp/p.md
    python persona_generalizer/ask_model.py --role reviewer_second --prompt - --json

Cost is appended to `usage.jsonl` beside the persona (or to --usage), so a delegated pass is
costed exactly like a pipeline stage rather than being invisible.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.config import load_config  # noqa: E402
from pipeline.model import ModelClient, ModelError  # noqa: E402

# Roles a second opinion may legitimately come from. `generator` is excluded on purpose: in the
# pilot config it is the same model the pipeline generates with, and a check by the model that
# will later produce the rows measures nothing.
SECOND_OPINION_ROLES = ("reviewer", "reviewer_second", "judge")


async def ask(
    prompt: str,
    *,
    role: str,
    config_path: str,
    usage_path: Path | None,
    max_tokens: int | None,
    want_json: bool,
    system: str | None,
) -> tuple[str, object | None]:
    config = load_config(config_path)
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}
    ]
    async with ModelClient.from_config(config, usage_path, stage="ask") as client:
        if want_json:
            payload, response = await client.complete_json(
                role, messages, max_tokens=max_tokens, stage="ask", record_id=role
            )
            return response.text, payload
        response = await client.complete(
            role, messages, max_tokens=max_tokens, stage="ask", record_id=role
        )
        return response.text, None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ask_model.py",
        description="Delegate one drafting pass to a configured non-Claude model role.",
    )
    parser.add_argument(
        "--role",
        default="reviewer",
        help=f"model role from the config. For a second opinion use one of "
        f"{', '.join(SECOND_OPINION_ROLES)}.",
    )
    parser.add_argument("--prompt-file", help="file holding the prompt; '-' reads stdin")
    parser.add_argument("--prompt", help="the prompt inline; '-' reads stdin")
    parser.add_argument("--system", default=None, help="optional system message")
    parser.add_argument("--config", default="configs/persona_pilot.yaml")
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--json", action="store_true", help="ask for and parse JSON")
    parser.add_argument(
        "--usage",
        default=None,
        help="where to append the usage record (default: usage.jsonl beside the cwd)",
    )
    parser.add_argument(
        "--allow-any-role",
        action="store_true",
        help="permit a role outside the second-opinion set; needed for deliberate experiments",
    )
    return parser


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        return sys.stdin.read() if args.prompt_file == "-" else Path(args.prompt_file).read_text(
            encoding="utf-8"
        )
    if args.prompt:
        return sys.stdin.read() if args.prompt == "-" else args.prompt
    return sys.stdin.read()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.role not in SECOND_OPINION_ROLES and not args.allow_any_role:
        print(
            f"error: role {args.role!r} is outside the second-opinion set "
            f"({', '.join(SECOND_OPINION_ROLES)}). The point of delegating a pass is to hear from "
            f"a different model family than the one that will generate; pass --allow-any-role if "
            f"you mean to do something else.",
            file=sys.stderr,
        )
        return 2

    prompt = read_prompt(args).strip()
    if not prompt:
        print("error: empty prompt.", file=sys.stderr)
        return 2

    usage_path = Path(args.usage) if args.usage else Path("usage.jsonl")
    try:
        text, payload = asyncio.run(
            ask(
                prompt,
                role=args.role,
                config_path=args.config,
                usage_path=usage_path,
                max_tokens=args.max_tokens,
                want_json=args.json,
                system=args.system,
            )
        )
    except ModelError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if payload is not None:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
