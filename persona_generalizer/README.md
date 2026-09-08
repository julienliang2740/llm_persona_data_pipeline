# Persona generalizer

The pipeline in this repository turns a **target** — one reviewed value system — into fine-tuning
data. This directory generalises the idea from a value system to a **person**: give it a subject,
historical or fictional, and it produces a spec the existing pipeline can build a dataset from.

The output is a model that judges as that person judged, not one that answers well. Where the
subject's judgment and the best available answer come apart, the subject wins.

```
persona_generalizer/
  README.md                        this file
  docs/persona-spec-schema.md      the field reference, including the sufficiency gate
  check_persona.py                 schema + gate validation
  skills/draft-persona/SKILL.md    the drafter, default arm (agent, with web search)
  draft_persona.py                 the drafter, fallback arm (script, model memory only)
  draft_prompts.py                 model-facing text for the script arm
  personas/
    _template/                     a complete, validating, invented persona — copy this
    <persona_id>/                  your personas
```

Everything under `personas/` is a drop-in target for the existing pipeline:

```bash
python main.py check --target <id> --targets-dir persona_generalizer/personas
python main.py all   --target <id> --targets-dir persona_generalizer/personas \
                     --config configs/pilot.yaml --n-families 2 --new-run --skip-baseline
```

Nothing under `pipeline/`, `prompts/` or `configs/` is persona-specific, and nothing in this
directory requires a change to them. The persona-only spec fields load and sit inert until the
renderer is taught about them.

## What is different from a value-system target

A tradition is a style of judgment with the voice deliberately stripped out — `cue_policy` forbids
its vocabulary and `archaic_register_examples` exists to stop the generator imitating source
diction. A person is recognisable *by* voice, idiosyncrasy and blind spots. Three consequences:

**Conduct outranks statements.** When what they said conflicts with what they did, try to explain
the gap first — danger, coercion, a view that moved over a lifetime — and write the reasoning
down. Where no reconciliation holds, what they *did* governs. Actions over words. The said/did
distinction gets called out in prose wherever it is visible; it is not a label on every datapoint,
and a persona needs a great deal of material — social background, period, the events that happened
to them — that no such taxonomy fits.

**No modern-constraint clause.** The value-system specs place their tradition inside modern
commitments and forbid attributing those to the sources. Persona specs do not. Fidelity governs
the content; conflicts with contemporary norms are declared in `redistribution_note` and in the
export manifest, the same way source licences already travel with a dataset. A persona corrected
into a better person is a different person.

**Voice is a slice, not the default.** Most rows stay uncued, so divergence remains measurable
against a generic assistant. A smaller tagged slice (`generation.voice_fraction`, default 0.2)
renders the subject's actual register. That is the persona product; the uncued majority is the
evidence that the judgment moved rather than the style.

**The world counts as much as the words.** A tradition has no childhood, no wages and no
precarity; a person is largely made of them. `context` and `formation` carry the socio-economic
and psychological conditions that produced the subject — what money meant, whose permission they
needed, what was ordinary to endure, what happened to them and what it left them with — and they
are sourced and weighted like every other section, not written as background. The checker warns
below 400 words for a reason: a persona built from words and deeds alone is fluent, characterful
and weightless.

New sections the schema adds: `subject` (with `canon_boundary`), `context`, `formation`,
`conflicts`, `voice`, `epistemic_horizon`, `sufficiency`, `attribution_policy`. Full reference in
`docs/persona-spec-schema.md`.

## Who can be generalised

Not everyone, and the gate is a first-class part of the spec rather than a judgement call.
`sufficiency` measures first-person volume, **documented decisions with their reasoning** (the
binding criterion, and the one most subjects fail), domain breadth, contestedness, and
testimonial variety, and returns `admit`, `admit_with_caveats` or `refuse`.

An unremarkable person from the fifteenth century fails on volume — nothing survives to be
faithful to. An object fails before the gate, having no conduct. Living private individuals are
out of scope regardless of how much material exists. Public figures, historical subjects and
fictional characters are in.

## Drafting: two arms

The drafter turns a subject into a draft spec. **Both arms exist deliberately, and the skill is
the default.** They differ in one thing — acquisition — and keeping both lets the difference be
measured on the same subject rather than argued about.

| | skill (default) | script (fallback) |
|---|---|---|
| run by | an agent, `skills/draft-persona/SKILL.md` | `python persona_generalizer/draft_persona.py` |
| sources | real: searches, retrieves, checks `robots.txt`, records URLs and access dates | none: a Fireworks model's own memory |
| can reach deeds | yes — registers, minutes, court records | no |
| can tell apocrypha from attestation | yes, by tracing to earliest source | no |
| reproducible | no | yes, and costed in `usage.jsonl` |
| cost | none | ~4 model calls |

```bash
# default: ask an agent to run the draft-persona skill for your subject

# fallback / comparison arm:
python persona_generalizer/draft_persona.py --subject "<name>" --id <slug>
python persona_generalizer/draft_persona.py --subject "<name>" --id <slug> --dry-run
```

Neither arm produces a usable target. Both produce a **draft for human review**, and the script
arm marks every passage unverified and writes an empty `SOURCES.md` saying so, because it
consulted nothing. Run the same subject through both and read them side by side; that comparison
is why both were built.

## How much material

The spec is the **seed**, not the dataset: `configs/full.yaml` expands one spec into about 240
scenario families and roughly 500 training rows. So the input has to be sized for that output.

The four reviewed value-system targets carry **49–128 passages, 5,100–8,300 words**. Aim for
**60–120 passages and 6,000–8,000 words**, about a third of it circumstance material. The checker
warns outside that band for any persona whose id does not begin with an underscore.

There is a hard ceiling at the top of it: `references/key_passages.md` is placed into **every**
generation prompt, so its size is a per-call token budget rather than storage. A subject with
30,000 words of surviving material cannot have all of it reach the generator; curate down and
record what you left out. (Lifting that ceiling by rotating passages across families would be a
change to prompt assembly in `pipeline/`, and has not been made.)

The shipped `_template` carries 24 passages and is exempt from the floor. It is a thing you copy
and delete, not a target.

## The steps

1. **Run the sufficiency gate first.** Criteria in `docs/persona-spec-schema.md`. A `refuse` is a
   real answer; a spec written past one is the researcher's imagination wearing a real name.

2. **Copy the template.**
   ```bash
   cp -r persona_generalizer/personas/_template persona_generalizer/personas/<id>
   sed -i '' 's/^id: _template/id: <id>/' persona_generalizer/personas/<id>/spec.yaml
   ```

3. **Acquire sources** under the ledger discipline in `targets/confucian/SOURCES.md`: primary
   material first, exact URLs, access dates, licences, `robots.txt` checked and refusals honoured,
   every processing step recorded, and consulted-but-not-ingested sources listed with reasons.

   Acquire three kinds of material, not one. **What they did** — registers, minutes,
   administrative and court records — because a persona built only from someone's writings is a
   persona of their rhetoric. **What they said or wrote.** And **the conditions they lived in** —
   wage books, census returns, inquest records, statistics on what was ordinary, the composition
   of the bodies they answered to. The third is the one that gets skipped and the one that decides
   whether the persona has a world.

4. **Fill `references/key_passages.md`.** One heading per item — circumstance, words, deeds and
   testimony in one file — each entry saying in prose what kind of record it is and what it bears
   on. Passage ids are parsed only from this file, so anything `context`, `formation` or a
   principle cites has to be here.

5. **Write `spec.yaml`.** `sufficiency` first, then `subject`, then `context` and `formation`,
   then `conflicts`, then the reused sections. Every field is annotated in the template. Write
   `context` and `formation` before the principles: the principles should fall out of the world
   and the life, not be imposed on them.

6. **Check it.**
   ```bash
   python persona_generalizer/check_persona.py <id>      # or --all
   ```
   Runs the target-schema validation in strict mode *and* the persona rules on top: the
   admissibility gate, the conflict adjudication, the epistemic horizon, the attribution policy,
   and the absence of a modern-constraint clause. Every problem prints at once. Errors block;
   warnings are a reviewer's call.

   `python main.py check --target <id> --targets-dir persona_generalizer/personas` still works
   and is what the pipeline itself enforces, but it knows nothing about the persona sections — a
   spec carrying a `refuse` verdict passes it. Use the persona checker. (Its output line labels
   the directory `targets/<id>` regardless of `--targets-dir`; that label is cosmetic.)

7. **Run a tiny pilot and read it.**
   ```bash
   python main.py all --target <id> --targets-dir persona_generalizer/personas \
       --config configs/pilot.yaml --n-families 2 --new-run --skip-baseline
   ```
   Open `runs/<id>/<run_id>/report.md` and `responses.jsonl`. If the responses could have been
   written without the spec, the spec is not yet doing its job. For a persona there is a second
   test: if they could have been written about a *different* person, `conflicts` and `voice` are
   too thin.

## Status

Steps 1–3: the contract, the gate, and both drafter arms. The template validates in strict mode
and passes the persona checker. 52 tests guard the schema, the checker and the script arm's
output, all without network — including a round-trip proving the drafter writes a
`key_passages.md` the pipeline's own parser accepts, and an end-to-end fixture proving a complete
draft passes the checker.

The skill arm has not yet been run on a real subject; the script arm has been dry-run only.
Neither has produced a dataset yet.
