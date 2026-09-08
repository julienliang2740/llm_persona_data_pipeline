# Research notes — template persona

**Invented.** Replace entirely. This file records what was checked, what the research turned up
that the draft got wrong, and what was deliberately left open. It is written *after* the sources
are read and *while* the spec is being written, and it is where a reviewer looks first.

`targets/confucian/research_notes.md` is the model, including its practice of recording the
author's own errors found during checking.

---

## 1. Corrections made while checking the sources

State the claim, the correction, and how it was verified. For a persona, corrections cluster in
three places:

**Attribution.** A quotation everyone repeats that appears in no contemporary source. The "storm
sermon" is the example here: three county histories carry it, the earliest is 1931, and no
document in her hand or in the board's minutes contains it. Moved to
`subject.canon_boundary.disputed` and not cited anywhere in the spec.

**Deed versus report of a deed.** AR-D3 is the case that matters. The delays are visible only in
the aggregate of the register — no single entry looks irregular, and no contemporary noticed. It
would have been easy to write a spec from her letters alone and never find it. Say here how a
deed was established, because deeds carry more weight than statements in this schema and that
weight has to be earned.

**Chronology.** AR-W2 predates AR-D3 by three years. That ordering is the whole reason the
`livelihoods_vs_the_corrin_delays` conflict resolves to conduct rather than to "she changed her
mind", so it is checked and recorded rather than assumed.

## 2. Conflicts examined and how each resolved

One entry per `conflicts:` id, with the readings that were tested and rejected. The spec carries
the conclusion; this file carries the work. A conflict resolved to `conduct` should show that a
reconciliation was genuinely attempted first — that is the difference between applying the rule
and reaching for it.

## 3. What was left open on purpose

`impartiality_vs_grudge` is marked `unresolved: true` because the record cannot settle whether
she was ever aware of the pattern. Note here why the sources cannot settle it, so a later reader
does not mistake the gap for an oversight.

## 4. What this persona implies for the pipeline

Anything the spec could not express, or that needed a field the schema does not have. This is the
feedback channel: per `targets/README.md`, a target that seems to need a code change is a schema
gap, and it gets fixed in the schema rather than in `pipeline/`.

## 5. Coverage warnings

Where the sources are thin, say so, and make sure the domain weights reflect it. Here: eleven
letters to one sister are the entire family record, so `family_and_close_relationships` is
weighted 0.3 and should not be pushed higher. Generating family scenarios beyond what the
sources can ground produces invention, not persona.
