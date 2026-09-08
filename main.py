#!/usr/bin/env python
"""CLI entry point.

    python main.py check    --target confucian            # validate a target spec, no model calls
    python main.py generate --target confucian --config configs/pilot.yaml
    python main.py all      --target confucian --config configs/pilot.yaml --n-families 20

Every stage reads and writes JSONL in runs/<target>/<run_id>/ and is idempotent on
that directory: re-running a stage fills in what is missing rather than starting over.

Evaluating a run's eval.jsonl (before/after a fine-tune) lives in the llm_persona_eval
repository, and LoRA training in llm_persona_training; both read this repo's exports.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from pipeline import baseline, export, generate, report, records, validate
from pipeline.config import ConfigError, load_config, new_run_id, resolve_run_dir
from pipeline.target import SpecError, load_target

STAGES = ("check", "generate", "baseline", "validate", "export", "report", "all")


def configure_logging(run_dir: Path, verbose: bool) -> None:
    """Log to stdout and to runs/<target>/<run>/log.txt."""
    level = logging.DEBUG if verbose else logging.INFO
    formatter = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s", "%H:%M:%S")
    root = logging.getLogger()
    root.setLevel(level)
    for handler in list(root.handlers):
        root.removeHandler(handler)
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    root.addHandler(stream)
    file_handler = logging.FileHandler(run_dir / records.LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)
    for noisy in ("httpx", "httpcore", "httpcore.http11", "httpcore.connection"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py", description="Value-instantiation data pipeline (Part 1)."
    )
    parser.add_argument("stage", choices=STAGES)
    parser.add_argument("--target", required=True, help="target id, i.e. a directory under targets/")
    parser.add_argument("--config", default="configs/pilot.yaml")
    parser.add_argument("--run", default=None, help="run id; defaults to the latest run for this target")
    parser.add_argument("--new-run", action="store_true", help="start a fresh run id instead of resuming")
    parser.add_argument("--n-families", type=int, default=None, help="override generation.n_families")
    parser.add_argument("--targets-dir", default=None, help="override where targets/ is read from")
    parser.add_argument(
        "--skip-baseline",
        action="store_true",
        help="all: continue when the local base model is not running",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser


def check_target(targets_dir: Path, target_id: str) -> int:
    """Validate a target spec in strict mode and describe what the pipeline would use.

    This is the first command to run after adding or editing targets/<id>/; it never
    creates a run directory and never calls a model.
    """
    try:
        spec = load_target(targets_dir, target_id, strict=True)
    except SpecError as error:
        print(f"targets/{target_id}: NOT OK\n{error}", file=sys.stderr)
        return 2
    cue = spec.raw.get("cue_policy") or {}
    grounding = [r for r in spec.raw.get("reference_material") or [] if r.get("use") == "grounding"]
    unlicensed = [r.get("id") for r in grounding if not r.get("license")]
    unresolved = [t.get("id") for t in spec.tradeoffs if t.get("unresolved") is True]
    avoid = [c.get("id") for c in spec.unresolved_choices if c.get("generation_policy") == "avoid"]
    lines = [
        f"targets/{target_id}: OK (strict)",
        f"  {spec.name} v{spec.version}",
        f"  principles: {len(spec.principles)}   tradeoffs: {len(spec.tradeoffs)} ({len(unresolved)} unresolved)"
        f"   boundaries: {len(spec.raw.get('boundaries') or [])}",
        f"  divergence hypotheses: {len(spec.divergence_hypotheses)}   domains: {len(spec.domains)}"
        f"   layers: {[l.get('id') for l in spec.raw.get('layers') or []] or 'none'}",
        f"  key passages: {len(spec.key_passages)} (all cited ids resolve)",
        f"  cue policy: {len(cue.get('forbidden_terms') or [])} forbidden, "
        f"{len(cue.get('allowed_terms') or [])} allowed, {len(cue.get('soft_terms') or [])} soft",
        f"  deliberation_shape: {'yes' if spec.raw.get('deliberation_shape') else 'MISSING (responses will use the generic shape)'}"
        f"   signature_moves: {len(spec.raw.get('signature_moves') or [])}",
        f"  avoid topics: {avoid or 'none'}   avoid keywords: {len(spec.avoid_keywords())}",
        f"  grounding sources: {len(grounding)}"
        + (f"   WITHOUT LICENCE: {unlicensed} (export will refuse)" if unlicensed else "   (all licensed)"),
        f"  redistribution_note: {'yes' if spec.raw.get('redistribution_note') else 'none'}",
    ]
    print("\n".join(lines))
    return 0


async def run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    targets_dir = Path(args.targets_dir) if args.targets_dir else config.targets_dir
    if args.stage == "check":
        return check_target(targets_dir, args.target)
    run_id = args.run or (new_run_id() if args.new_run else None)
    run_dir = resolve_run_dir(config, args.target, run_id)
    configure_logging(run_dir, args.verbose)
    logger = logging.getLogger("main")

    if args.stage == "report":
        path = report.run_stage(run_dir, args.target, config.pricing, config.generation)
        print(path.read_text(encoding="utf-8"))
        return 0

    spec = load_target(targets_dir, args.target, strict=bool(config.raw.get("strict_specs")))
    logger.info(
        "target %s v%s (%d principles, %d tradeoffs, %d key passages); run dir %s",
        spec.target_id,
        spec.version,
        len(spec.principles),
        len(spec.tradeoffs),
        len(spec.key_passages),
        run_dir,
    )

    stages = [args.stage] if args.stage != "all" else ["generate", "baseline", "validate", "export", "report"]
    summary: dict[str, object] = {}
    for stage in stages:
        logger.info("=== stage: %s ===", stage)
        if stage == "generate":
            summary[stage] = await generate.run_stage(config, spec, run_dir, args.n_families)
        elif stage == "baseline":
            try:
                summary[stage] = await baseline.run_stage(config, run_dir)
                # The strong-generic leg needs no local server, so it runs even when the
                # base model is unavailable; it is what makes the three-way judge possible.
                summary["baseline.strong_generic"] = await baseline.run_strong_generic(
                    config, run_dir, spec
                )
            except baseline.BaselineUnavailable as error:
                logger.warning(
                    "local base model unavailable: %s Divergence cases will be unverified.",
                    error,
                )
                summary[stage] = {"skipped": str(error)}
                summary["baseline.strong_generic"] = await baseline.run_strong_generic(
                    config, run_dir, spec
                )
                if args.stage == "baseline" and not args.skip_baseline:
                    return 2
        elif stage == "validate":
            summary[stage] = await validate.run_stage(config, spec, run_dir)
        elif stage == "export":
            summary[stage] = export.run_stage(config, spec, run_dir)
        elif stage == "report":
            summary[stage] = str(
                report.run_stage(run_dir, args.target, config.pricing, config.generation)
            )

    print(json.dumps({"run_dir": str(run_dir), "stages": summary}, indent=2, default=str))
    return 0


def main() -> int:
    args = build_parser().parse_args()
    try:
        return asyncio.run(run(args))
    except (ConfigError, SpecError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except RuntimeError as error:
        # A stage whose inputs are missing says which stage to run first.
        print(f"error: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
