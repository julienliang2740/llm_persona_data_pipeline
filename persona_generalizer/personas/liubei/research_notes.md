# Research notes — Liu Bei (DRAFT)

Produced 8 September 2026 following `.claude/skills/draft-persona/SKILL.md`. **No passage has been
checked twice.** This file is the checklist a reviewer works through.

## 1. Why the verdict is `admit_reconstructed`

This is the first subject to use that verdict, and it is the case it was added for. The criteria
split cleanly:

- **Binding criterion MET, and comfortably.** Eight decisions survive with both the act and his
  stated reason. That is the opposite of the Basil II result (one), and it is why this subject is
  admissible where a superficially better-documented emperor was not.
- **First-person volume BELOW FLOOR.** Perhaps a thousand characters of classical Chinese. The
  surviving utterances are few but almost all of them are decisions with reasons attached, which is
  an unusual shape: the corpus is thin and unusually high-yield.
- Circumstance therefore has to be inference in places, and ten passages (11%) are marked
  `evidence_basis: reconstructed`. All ten are circumstance or psychological effect; none is cited
  by a conflict, which the checker enforces.

`admit_with_caveats` was considered and rejected as dishonest: it would have let inference travel
into prompts indistinguishable from the record.

## 2. Corrections made while checking

- **A pattern-match error that would have falsified the corpus.** Counting `先主曰` to measure his
  direct speech conflates it with `謂先主曰` — "said **to** Liu Bei". On that basis the famous line
  about the heroes of the age would have been attributed to him; it is **Cao Cao's**, spoken to
  him. Corrected by excluding the `謂` form, which cut the count of his own speeches from eight to
  four. This is the single most important correction in the file and it is the argument for
  reading the source rather than grepping it.
- **The peach garden oath is not in the record.** What juan 32 supports is that the three shared
  quarters and were as brothers. Recorded in C23 and excluded in `canon_boundary`.
- **His descent is doubted inside his own source.** Pei Songzhi observes that the line was too
  remote to determine which emperor to install as ancestor when the dynastic cult was founded.
  Moved to `canon_boundary.disputed` (T9) rather than repeated as fact.
- **The accession proceeded on a false report.** Pei preserves that a report of the deposed Han
  emperor's death reached him and that he acted on it; the emperor was alive. Kept in D17 rather
  than smoothed, and it is the part of the fourth conflict that the reconciliation does not cover.
- **A claim about ctext.org that I got wrong, and am correcting here.** The first version of this
  draft asserted that ctext.org's `robots.txt` had *changed* since `targets/confucian/SOURCES.md`
  recorded it. It has not. Re-reading both, the confucian ledger of 2026-09-07 describes the same
  file: GPTBot, ChatGPT-User and Amazonbot disallowed, plus a long list of mirroring and bulk
  download tools. What I had actually noticed was narrower — that no *Claude* agent is named — and
  that was equally true when the earlier ledger was written; it simply characterised the file by
  its evident intent rather than by enumerating which agents are absent. The decision to decline
  was correct and is unchanged; only my account of why was wrong. **The commit message that
  introduced this persona repeats the error and has not been rewritten.**

## 3. The conflicts, and why each resolved as it did

Four; two to `conduct`, two to `reconciled`.

- **`could_not_bear_it_versus_yi_province` → conduct.** The central finding. He refused to seize
  Jingzhou from a dead host's son on stated grounds of not being able to bear it, then took Yi
  province from a living kinsman who had invited him in, given him troops, and exchanged formal
  honours with him. Necessity is the strongest defence and fails on comparison: he was equally
  baseless in 208 and refused. The only surviving reading — that the statement covered a dead
  man's inheritance specifically — makes the principle so narrow it stops being one.
- **`the_people_are_the_foundation_versus_yiling` → conduct.** The stated ground for the eastern
  campaign in the record is fury, not strategy, and he refused the peace offered before the
  decisive engagement. A strategic reading has to explain that refusal and cannot.
- **`benevolence_professed_versus_the_legalist_reading_list` → reconciled.** He told his heir that
  only worth and virtue bring submission, and in the same document prescribed Shen Buhai, Han Fei,
  Guanzi and the *Book of Lord Shang*. These are not rival systems in his world; he lists the
  *Liji* in the same breath. **Flagged as a judgement call:** this conflict's `said` and `did` are
  both `W` passages, so it is strictly a said/said tension. It is included because W12 records an
  *act* — he directed the reading and the chancellor had already copied the texts out — but a
  reviewer may reasonably want it demoted to a tradeoff.
- **`han_restoration_versus_taking_the_throne` → reconciled.** By 221 the dynasty had been ended
  by someone else, so continuing it required an officeholder, and the accession text argues
  exactly that. The claim was also expensive, which is evidence against pure opportunism. The
  reconciliation explicitly does **not** cover proceeding on an unverified report of a death.

## 4. Left open on purpose

- **`proximity_against_number`** is unresolved. The sources give an emotional state as the ground
  for the eastern campaign and preserve no reasoning, so a response that has him weigh and choose
  claims too much — and so does one that has him merely swept along.
- **`what_the_entrusting_meant`** is unresolved and should stay that way. Sincere devolution, a
  binding of a man too honest to accept, and a test are all live readings; Sun Sheng's hostile
  attack (T8) is preserved inside the source itself. Note the structural fact that cuts against
  the most generous reading: he simultaneously appointed Li Yan alongside Zhuge Liang (D28), so
  whatever he said, he divided the authority.
- **Whether W9 is self-knowledge or the deepest form of the modesty his reputation rested on.**
  Recorded in principle LB14 as an ambiguity the persona carries rather than resolves.

## 5. Coverage warnings — read before generating

- **The two halves of this file are not of equal quality.** Words and deeds come from the primary
  text read in Chinese. All circumstance is general period history from search summaries, and none
  of it is scholarship about this subject. The schema asks circumstance to carry the same weight as
  words and deeds; here it does not.
- **No Chinese-language secondary scholarship was consulted.** The largest single gap.
- **No critical edition.** Wikisource is a transcription without apparatus, so textual variants and
  punctuation choices are invisible to this draft.
- **Shu kept no court history** (C18). This is a limitation at the source, not of the search: what
  survives is what one man could gather and remember a generation later.
- **Family and private life are thin** and mostly instrumental, hence the 0.15 weight. His wives
  appear chiefly as losses in routs and as an alliance.
- **The novel is the ambient contamination.** It supplies not merely invented episodes but a whole
  motive system in which every act follows from benevolence. Any reviewer working from memory will
  import it. The specific tell to watch for in generated output is a Liu Bei who *explains* the
  taking of Yi province — the record's man does not (W18, LB08).

## 6. What this implies for the pipeline

- **The `admit_reconstructed` path works end to end** and this is its first real exercise: the
  drafter's verdict, the per-passage markers, the 40% ceiling, the attested-conflict rule and the
  manifest declaration all engaged as designed.
- **One observation for the schema.** A conflict whose two sides are both statements has no
  natural home: `conflicts` presumes said-versus-did. The third conflict here is genuinely a
  tension between a professed principle and an instruction given in the same breath, and it had to
  be forced into the said/did shape. Worth considering whether the schema should admit a
  `said_versus_said` variety, or whether such items belong in `tradeoffs`.
- **The escalation ladder was not needed as a rescue** here, because pass 1 reached the primary
  text directly. That means passes 2 and 3 remain untested against a subject that genuinely needs
  them.

## 7. Before this is used

1. Verify every passage against the Chinese. The English renderings are mine and unchecked.
2. Acquire Chinese secondary scholarship and a critical edition; rewrite circumstance against them.
3. Decide the third conflict's status (conflict or tradeoff).
4. Resolve the CC BY-SA share-alike question for a derived dataset — `redistribution_note` blocks
   export until then.
5. Re-run `python persona_generalizer/check_persona.py liubei`, then read a 2-family pilot report
   before committing to a full generation.
