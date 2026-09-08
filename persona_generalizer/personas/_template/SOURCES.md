# SOURCES — personas/_template

**Everything here is invented.** Adela Renn did not exist. This file is a worked example of the
ledger a real persona must carry, filled in with fictional entries so the shape is visible.
Delete it when you copy the directory.

The discipline is the one already used by `targets/confucian/SOURCES.md`: exact source, exact
URL, access date, licence, any AI-use restriction, what processing was applied, and a section for
sources that were checked and deliberately **not** ingested, with the reason.

Two things this ledger carries that a value-system ledger does not:

1. **Evidence type**, where it is visible — whether a source records what the subject *wrote or
   said*, what they *did*, or what someone else said about them. It is not a label on every row;
   it is a column you fill in when the answer is clear, because `conflicts:` in the spec cannot be
   adjudicated without it.
2. **Interestedness** — who produced the source and what they wanted. A hostile institutional
   minute and a friendly memoir are both usable and neither is neutral. For a persona this matters
   more than for a tradition, because the subject had enemies.

All access dates below are **8 September 2026**.

---

## Acquired and included in `references/`

### 1. `references/key_passages.md`

| field | value |
|---|---|
| Work | Curated words, deeds and testimony |
| Source | Invented for this template |
| URL | n/a |
| Access date | 2026-09-08 |
| Licence | Public domain (invented for this repository) |
| AI-use restrictions | None |
| Evidence types present | words (AR-W1–W4), deeds (AR-D1–D4), testimony (AR-T1–T2) |
| Interestedness | AR-T1 friendly memoirist; AR-T2 hostile institution; the rest self-authored |

**Processing applied.** None; written directly. A real persona records here what was extracted
from which edition, how passage ids were assigned, and how the numbering was verified against a
second source — see the Analects entry in `targets/confucian/SOURCES.md` for the standard.

---

## What a real persona's ledger has here

Rows a real subject needs, in rough order of evidentiary weight:

| tier | material | typical evidence type |
|---|---|---|
| 1 | The subject's own manuscripts, letters, logs, marginalia | words, sometimes deeds |
| 2 | Contemporary records of their acts: registers, minutes, court and administrative records | **deeds** |
| 3 | Contemporary testimony by people who knew them, with interestedness noted | testimony |
| 4 | Later biography and scholarship | `use: reference_only` — background, never grounding |
| 5 | Legend, novelisation, film | excluded; record in `subject.canon_boundary.excluded` |

Tier 2 is the one persona research skimps on and the one the conduct-over-words rule depends on.
A persona built only from tier 1 is a persona of someone's rhetoric.

**For a fictional subject** the tiers collapse: the canon text is tiers 1–3 at once, and the
question becomes which texts are canon. Record adaptations and continuations explicitly, with the
policy for what happens when they contradict the primary text.

---

## Checked and deliberately NOT ingested

*(A real ledger lists every source consulted and refused, with the reason. Two illustrative rows.)*

### The 1923 novelisation — `use: reference_only`, NOT quoted

In copyright, and in any case not evidence: it is the origin of most of what is popularly
believed about the subject. Recorded in `subject.canon_boundary.excluded` so a later reader does
not re-import it in good faith.

### A site whose robots.txt disallows AI crawlers — not retrieved

Where a source's `robots.txt` or terms refuse automated or AI use, **nothing is taken from it**,
the refusal is recorded here, and an alternative is found. `targets/confucian/SOURCES.md` sets
the precedent: ctext.org disallows `GPTBot` and bulk downloaders, so no text was taken from it
and public-domain equivalents were used instead. Follow that. Check `robots.txt` before
retrieving, and record that you checked.

---

## Reproducing the acquisition

A real ledger ends with the exact commands that fetched the material, as
`targets/confucian/SOURCES.md` does, so a reviewer can reproduce `references/` from scratch.
Nothing to reproduce here.
