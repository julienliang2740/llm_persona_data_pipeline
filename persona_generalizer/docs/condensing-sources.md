# Condensing retrieved sources

Retrieved pages reach the drafting prompt as raw text under a character budget
(`max_passage_chars_responses`, `max_passage_chars_families`). The budget exists because
`key_passages.md` is placed into every generation prompt later, so every wasted word is a cost
paid on every row the pipeline ever produces.

Raising the budget is the wrong first move. A live run retrieved eleven pages for one slot,
nine of them navigation chrome, cookie notices, "see also" lists and unrelated article text. The
problem was never that there was too little room; it was that the room went to material carrying
no information about the subject. Condense first, and raise the budget only if condensed material
still does not fit.

## What to keep, in priority order

1. **Anything the subject said or wrote**, in full, and in the original language where the page
   gives it. This is the scarcest material in any persona corpus and the criterion most subjects
   fail on. Never paraphrase a direct utterance during condensation; a paraphrase cannot later be
   restored into a quotation, and the distinction between what someone said and what someone said
   about them is the one the whole schema turns on.
2. **Dated acts, with their circumstances.** A date, a place, an act, and who else was involved.
   Deeds are what the conduct-over-words rule stands on and a deed without a date cannot be put
   in a chronology or used to resolve a conflict.
3. **Attributions.** Who is reporting this, and what did they have at stake. "The hostile
   chronicle records" and "his own memorial claims" are different facts and condensing them into
   "sources say" destroys the interestedness the ledger is supposed to preserve.
4. **Numbers and specifics.** Sums, distances, counts, ages, titles, office names. These survive
   condensation badly because they look like detail, and they are the things a reviewer can check.
5. **Explicit uncertainty.** "Traditionally said to", "the date is disputed", "this is
   the novel rather than the record". Dropping a hedge converts a doubtful claim into a confident
   one, which is worse than dropping the claim entirely.

## What to drop

- Navigation, headers, footers, cookie and subscription notices, "see also", category lists,
  edit links, reference markers with no reference attached.
- Anything about a different person who shares the name. A salary query for a third-century
  warlord retrieved a living fashion model twice; the pages were kept and counted as sources.
- Plot summary of fiction about the subject, unless the page is explicitly distinguishing the
  fiction from the record — in which case keep the distinction and drop the plot.
- Restatements. Four pages repeating one underlying source are one source. Keep the earliest or
  most specific statement and note that the others agreed.
- Modern commentary about the subject's reputation or legacy, unless it is testimony from someone
  who knew them.

## How to write the condensed form

Write prose, not bullet fragments. The drafting pass reads this as evidence and fragments lose
the connections that make an act intelligible — "he refused, and the reason he gave was X" is
evidence; "refused / reason: X" is a note.

Attribute inline and specifically: `the chronicle records that…`, `<page> reports that the
chronicle records…`. The second form matters when the page is a summary rather than the source,
because a body that names a work nobody retrieved is the failure mode this whole file guards
against.

Target **a quarter to a third** of the source length for a substantial page, and do not compress
a page that is already dense — a transcription of a primary text should pass through close to
whole, because every sentence in it is the kind of material section 1 says to keep.

State what you dropped when it is load-bearing: `(the page's plot summary of the novel is
omitted)`. A reviewer reconstructing your reasoning needs to know whether something was absent
from the source or removed during condensation.

## Verifying a condensation

Three checks, cheap enough to run every time:

- **Could a reader tell what the subject said from what others said about them?** If not, the
  attribution was lost.
- **Does every claim that was hedged in the source remain hedged?**
- **Is anything in the condensation not in the source?** Condensation is lossy compression, not
  generation; a fluent summary that adds a motive is the most dangerous possible output because
  it reads exactly like the material it replaced.

## Status

**Untested.** This file is written from the failure modes observed in four live acquisition runs,
not from a measured comparison between condensed and raw material. The trial that would settle it
is a single subject drafted twice, once from raw pages and once from condensed ones, comparing
passage count, evidence basis distribution and how much of the primary source survived into the
corpus. Until that is run, treat the ratios above as starting points rather than findings.
