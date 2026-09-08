# Research notes — LBJ (DRAFT, second pass)

Produced 8 September 2026 by following `.claude/skills/draft-persona/SKILL.md`. This pass replaces
a first draft that rested entirely on secondary web sources; that draft's own closing section
listed what it needed, and this pass supplied two of the five items — tier-1 words and tier-2
deeds. **Nothing here is verified against a physical archive.** This file is the checklist a
reviewer works through.

## 1. What changed from the first pass

| | first pass | this pass |
|---|---|---|
| words | speech texts via search summaries | 14 full speech transcripts read, ~38,000 words, US federal government works |
| deeds | a fact-check article's characterisation of the voting record | 92 civil-rights-related roll calls, joined to his member record by ICPSR, with dates and cast codes |
| passages | 31 (~2,500 words) | 98 (6,028 words) |
| conflicts | 4 | 5, one of them found only by reading the primary texts |
| refusals | not checked | 9 hosts checked, 8 declined or blocked, all recorded |

## 2. Corrections made while checking

These are the errors caught by reading sources rather than summarising them, and they are the
argument for doing it that way.

- **A Reagan speech was nearly ingested as Johnson's.** "A Time for Choosing" (27 October 1964)
  matched a date-range filter for LBJ-era speeches and was downloaded with the rest. Reading the
  first paragraph — "I have spent most of my life as a Democrat" — identified it. It was deleted
  before any passage was written from it. A name-blind date filter will do this; check the speaker.
- **The white primary claim was too broad.** The first draft said a Texas Democrat "held office
  through a white primary" as a general condition of his career. *Smith v. Allwright* struck the
  Texas white primary down in **1944**, which is inside his House years and well before all three
  of his Senate elections. `context.standing_and_constraint` now dates it and names the poll tax,
  which did outlast it in Texas, as the continuing mechanism.
- **A "Yea" in his civil rights record is not necessarily a vote for civil rights.** On 18 January
  1950 he voted Yea twice — on motions to *table* Langer amendments relating to lynching and to the
  poll tax. Aggregating his votes into for/against counts would have produced a materially wrong
  picture. D6 exists specifically to record this, D11 warns about it in terms, and no aggregate
  count appears in the spec.
- **The 1957 act is not a straightforward credit, and now there is a roll call for it.** The first
  draft said advocates called the weakening a betrayal. The record shows he personally voted Yea on
  the amendment deleting the Attorney General's preventive-relief power and Yea on the jury-trial
  amendment before voting Yea on passage. D8 states the three votes.
- **"We have lost the South for a generation" remains unusable.** Repeated everywhere, traceable to
  no contemporaneous source. Quarantined in `canon_boundary.disputed`, cited by nothing. Anyone
  drafting this persona from memory would very likely have used it.
- **Box 13 was Jim Wells County, not Duval County** — carried forward from the first pass, which
  had already corrected this.

## 3. The conflicts, and why each resolved as it did

Five conflicts; four resolve to `conduct`, one to `reconciled`. The two civil-rights entries are
deliberately separate and resolve **differently**, which remains the most interesting thing this
subject produces.

- **`professed_conviction_vs_the_twenty_year_record` → conduct.** Strengthened, not weakened, by
  the roll calls. Constituency necessity is a serious defence and was tested properly; it covers a
  Nay. What it does not cover is the craftsmanship the record now shows: a vote to sustain a
  filibuster on fair employment (D5), votes to table (D6), and a great deal of well-executed
  procedural work (D9). Necessity explains a vote; it does not explain supplying the instrument.
- **`claimed_continuity_vs_the_1957_and_1960_votes` → conduct. New in this pass, and only findable
  from the primary texts.** On 27 November 1963 he told Congress he urged civil rights legislation
  "again, as I did in 1957 and again in 1960". Held against D8 and D10 this is authorship claimed
  and method concealed. The generous reading — that he did deliver both acts and without the
  weakening neither would have passed — holds for the delivery and not for the implied consistency.
  This is the clearest single instance of the said/did gap in the file and it did not exist in the
  first draft, because the first draft had neither the speech text nor the roll calls.
- **`early_votes_vs_the_1965_turn` → reconciled.** Same subject matter as the first conflict,
  opposite outcome, and the difference is chronology. A view that moved is a defence only when the
  dates support it and the later conduct matches the later words. Here both hold, and D11 now
  locates the pivot in the roll call record rather than in his own account of himself — which is
  exactly the distinction the second conflict shows he cannot be trusted on.
- **`no_wider_war_vs_the_escalation` → conduct.** Rebuilt on a source actually held. The first
  draft used the Akron speech of 21 October 1964, whose text was not retrieved in either pass; this
  one uses the Gulf of Tonkin address of 4 August 1964, which was read in full. Changed
  circumstances partly holds. What defeats it is that the resolution obtained the same week
  authorised all necessary measures.
- **`servant_of_the_poor_vs_the_broadcast_fortune` → conduct.** Unchanged in outcome. The wife's
  name, the legality and the absence of concealment all explain why he was never punished; none of
  them explains the ordering of the permissions.

## 4. Left open on purpose

- **`the_count_vs_the_person_in_front_of_you`** stays `unresolved: true`. Nothing found shows him
  treating the twenty years of votes as requiring an apology rather than an explanation. A response
  that has him confess claims more than the sources support; so does one that has him untroubled.
  The recordings would settle it and they were not available (below).
- **`the_programme_against_its_own_evidence`** is new and also unresolved. He restates the thesis
  under pressure after Watts and Detroit, which is compatible with conviction and with
  stubbornness, and these sources cannot separate them.
- **The March 1968 withdrawal** is flagged inside `boundaries` rather than resolved. It is the
  hardest fact in the record to fit to principle LBJ05, and the honest options — a genuine limit,
  or a count he had already lost — are not distinguishable from what was consulted.

## 5. Refusals, and what they cost

Nine hosts were checked before retrieval; eight were declined or blocked. Full table in
`SOURCES.md`. Two refusals shaped this draft materially:

- **The presidential library's own digital archive declines automated AI use** (`ai-train=no`,
  plus an explicit ClaudeBot disallow). It holds the papers and the recordings. Nothing was taken.
  This is why T10 is written as a *gap* rather than as evidence, and why the unresolved tradeoff
  stays unresolved.
- **The American Presidency Project blocks ClaudeBot**, and the Internet Archive's scanned *Public
  Papers* volumes are all in controlled lending and return HTTP 401. Both routes to the complete
  public papers were therefore closed. The substitute — 14 full speech transcripts from a host that
  permits — is good material and is not the same thing as the complete papers. The selection is
  mine, which is a bias a reviewer should weigh: I chose the speeches I expected to be revealing.

## 6. Coverage warnings — read before generating

- **The two halves of this file are not of equal quality.** Words and deeds are tier 1–2. All 28
  circumstance entries and all 10 testimony entries are tier 3–4, several resting on search-result
  summaries rather than on documents read in full. The schema requires circumstance to carry the
  same weight as words and deeds; here it does not, and the persona is correspondingly more
  reliable about what he did than about the world that produced him.
- **No Caro, no Dallek.** The standard scholarship is still absent and remains the largest gap
  after the recordings.
- **Family and private life are genuinely thin**, hence the 0.1 domain weight. Lady Bird appears
  once (C25) and owned the business at the centre of a whole conflict entry, which is a real
  distortion.
- **The roll call filter is a keyword filter.** It caught 92 votes matching a civil-rights pattern;
  it will have missed votes whose descriptions use other language, and it swept in a handful of
  price-discrimination and foreign-aid votes that were read and discarded. It is not a complete
  civil rights voting record and is not described as one.
- **The speech extraction is scripted, not proofread.** Text was pulled from an HTML container by
  regex. Passages were written from readings of that text, but OCR-style errors and dropped
  fragments are possible and no passage has been checked against a second edition.

## 7. What this implies for the pipeline

No schema gap was found; everything needed could be expressed. Three observations:

1. **`conflicts:` again needed two entries on the same subject matter resolving differently**, and
   this pass added a third civil-rights conflict (`claimed_continuity_...`) that resolves the same
   way as the first but on a different mechanism — a false claim about his own record rather than a
   gap between conviction and vote. The schema handles it; the docs still do not mention that this
   arises, and it is the most informative thing the section produces.
2. **The refusal discipline changed the draft's shape, not just its ledger.** Two AI-use refusals
   removed the single best source (the recordings) and forced a substitution whose selection bias
   is mine. `SOURCES.md` can record that, but nothing in the spec surfaces "this persona's evidence
   base was shaped by access refusals" to whoever reads a generated dataset later. That may be
   worth a field.
3. **The corpus floor fired usefully again.** The first draft failed it at 31 passages; this one
   passes at 98 and 6,028 words, inside the 6,000–8,000 band.

## 8. Before this is used

1. Verify every passage against its source. Nothing in `key_passages.md` has been checked twice.
2. Acquire the recordings and the standard biographies; rewrite circumstance and testimony against
   them.
3. Re-adjudicate `claimed_continuity_vs_the_1957_and_1960_votes` and the unresolved tradeoff
   against the recordings.
4. Decide the licence question in `reference_material.license` — the reasoning there is mine and
   has not been reviewed.
5. Re-run `python persona_generalizer/check_persona.py lbj`, then read
   `runs/lbj/<id>/report.md` from a small pilot before committing to a full generation.
