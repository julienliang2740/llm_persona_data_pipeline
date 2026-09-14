# Research notes — Julian the Apostate (DRAFT)

Produced by `draft_persona.py`, the script arm of the drafter, working from a model's own
memory with no sources consulted. **Nothing here is verified.** This file is the checklist
a human works through before the spec is used.

## 1. Sufficiency

Verdict: **admit_with_caveats**. This is one of the strongest ancient subjects available. The binding criterion — decisions with stated reasoning — is met unusually well because Julian wrote prolifically about his own policies and their justifications, and an eyewitness-grade external narrative (Ammianus) corroborates the acts. Domain breadth is wide, testimonial variety is excellent, and the contestedness, while real, is checkable against the first-person corpus. I stop short of a clean admit because the single most distinctive text survives only in hostile quotation and the narrative record is heavily legend-contaminated; those are caveats about curation, not gaps that force reconstruction of the persona's core.

- Binding criterion (decisions with reasoning): Strong — this is the unusual case where the binding criterion is met. Multiple major decisions survive with Julian's own stated reasoning: the restoration of pagan cults and temple property (letters and edicts explain his rationale), the school edict barring Christians from teaching classical literature (he states the reason openly — that one should not teach what one believes false), the revocation of clerical privileges, the price edict and grain policy at Antioch (the Misopogon gives his own account and self-justification), the authorization to rebuild the Jerusalem Temple (a letter to the Jewish community states his reasoning), and his toleration policy deliberately rejecting forced conversion (his letters argue coercion cannot produce belief). Ammianus supplies the acts; Julian's own texts supply the reasons. Confidence: high on the substance of these policies; I am reconstructing substance, not wording, and some letter attributions are debated.
- First-person volume: Exceptionally high for an ancient figure — arguably the best-documented Roman emperor in his own words after Marcus Aurelius. Survives: a substantial letter corpus (dozens of letters, some of disputed authenticity), several full orations (two panegyrics on Constantius, the Hymn to King Helios, the Hymn to the Mother of the Gods), the Misopogon (a self-mocking satirical address to Antioch), the Caesars (a satire judging his imperial predecessors), and Against the Galileans, his anti-Christian polemic, which survives only in fragments quoted by Cyril of Alexandria's refutation. Confidence: high that this corpus exists and is extensive; moderate on exact letter counts and authenticity disputes.
- Contestedness: Moderate to high on the narrative record, low on the first-person core. The external sources are intensely partisan: Gregory of Nazianzus's invectives and later church historians (Socrates, Sozomen, Theodoret) contain legend — the famous dying cry conceding defeat to 'the Galilean' is late and generally regarded as invention. On the other side, Libanius and Eunapius are adulatory. Ammianus is the nearest to balanced but openly admires him. The large authentic corpus anchors the persona against these distortions, but any dataset must flag hagiographic and demonizing material as such.

This verdict was reached without consulting anything and is the least trustworthy part of
the draft. Re-run the gate against real sources before accepting it.

## 2. Every passage needs verification

70 passages were drafted; none is sourced. No entry is a verbatim quotation
— all are paraphrases or reconstructions — but a paraphrase of something the person never
said is still a fabrication. Check each against a primary source, or delete it.

Entries the model itself flagged as medium or low confidence:

- `C3` (circumstance): The surveillance itself is in Wikipedia; the dissimulation claim comes from a modern Greek popular article and should be treated as interpretation unless traced to Ammianus or Libanius.
- `C6` (circumstance): DIR attests the teachers; the Libanius ban appears in the evprattein.gr popular article — trace it to a primary source before relying on it.
- `C8` (circumstance): The page attributes the story to Eunapius; I did not read Eunapius directly. Check the fragment in Eunapius's Vitae Sophistarum.
- `C19` (circumstance): Negri is a 19th-century biographer quoting Libanius and Sozomen; the Libanius oration postdates Julian. Check Libanius Oration 30 and Sozomen directly.
- `C20` (circumstance): Negri paraphrases the Misopogon; check the Misopogon itself and Ammianus 22.12-14 for the Daphne fire and food-shortage disputes.
- `C21` (circumstance): The vermin-and-dirt details come from a confessional popular article (Christian Courier); the pillow anecdote is DIR's. Check Ammianus 25.4 and Julian's Misopogon, which itself mentions his beard and lice.
- `D4` (deed): Only encyclopedia.com asserts Mithraic initiation; the EUP book page shows modern scholarship debates its weight.
- `D12` (deed): Attested only in a popular Greek article in this retrieval; confirm against Ammianus 22 or a scholarly biography before weighting.
- `D13` (deed): Confirm the Chalcedon tribunal and its victims against Ammianus 22.3; the vengeance inference is el.wikipedia's.
- `W2` (words): Verify against Eunapius's Lives of the Sophists; the wording reached us through two layers of reporting.
- `W7` (words): The quoted prayer is a popular-book translation; check against the Loeb text of the Hymn to the Mother of the Gods.
- `W9` (words): Existence and genre are attested by the listing pages; content must be checked against the text itself, which was not retrieved.
- `W10` (words): Confirm the attribution of Anthology IX 368 to the emperor Julian rather than another Julian; paraphrase only, do not quote.
- `W13` (words): Trace the earliest source of the 'Galilean' cry (usually given as Theodoret); it belongs in the disputed layer, not as Julian's actual words.
- `W14` (words): Only existence is attested by these pages; the letter's argument must be read in the text, which was not retrieved.
- `T5` (testimony): Check Eunapius's Lives of the Philosophers and Sophists (life of Maximus or Aedesius) for the actual anecdote; Wikipedia is relaying it.
- `T6` (testimony): Confirm the panegyric's date, occasion, and themes from the Latin text; the retrieved pages attest its existence and inclusion, not its content.
- `T8` (testimony): Check Sozomenes' Ecclesiastical History book 5 for the procession and fire; Negri is an intermediary, not the primary source.
- `T9` (testimony): Trace the legend to its earliest attestations (Theodoret is usually named); confirm no contemporary source records it. Treat as disputed tradition.

## 3. Conflicts and how each resolved

- **panegyrics_under_power_vs_chalcedon_settling** — W11 against D13 → `conduct` (confidence: medium)
- **persuasion_not_blows_vs_legal_dispossession** — W6 against D16 → `conduct` (confidence: high)
- **persuasion_not_blows_vs_school_gate** — W6 against D17 → `reconciled` (confidence: medium)
- **happiness_for_all_vs_exiling_athanasius** — W7 against D18 → `conduct` (confidence: medium)
- **anti_galilean_polemic_vs_christian_institutional_copy** — W3 against D19 → `reconciled` (confidence: high)
- **gallic_prudence_vs_persian_logistical_gamble** — W8 against D22 → `conduct` (confidence: medium)

Each resolution rests on an unsourced chronology. Where a conflict resolved as a change of view over time, check the dates first: that reading collapses if the statement postdates the conduct.

## 4. Known losses in this draft

No invented passage ids were cited.

## 5. Before this is used

1. Verify every passage against a real source, or delete it.
2. Fill in `SOURCES.md` completely; establish the licence of everything.
3. Re-run the sufficiency gate against what actually survives.
4. Re-adjudicate every conflict against a sourced chronology.
5. Run `python persona_generalizer/check_persona.py <id>` until clean.
6. Compare against the skill arm's draft of the same subject and reconcile the two.


## Verification against the retrieved material

A second model family audited the drafted items against the pages actually retrieved and flagged **115**. Each was downgraded rather than deleted: the claim may well be true, and the honest repair is to stop calling it attested, not to pretend it was never made. A downgrade is a prompt to go and find the source, not a verdict that the claim is false.

- looked for `evprattein.gr Greek popular page` after the audit named it; 33 page(s) retrieved
- looked for `Catholic Encyclopedia` after the audit named it; 33 page(s) retrieved
- looked for `Greek popular page` after the audit named it; 33 page(s) retrieved
- looked for `popular page` after the audit named it; 33 page(s) retrieved
- looked for `Tougher volume excerpt (dokumen.pub/julian-the-apostate-9781474473286.html)` after the audit named it; 33 page(s) retrieved
- looked for `Tougher excerpt` after the audit named it; 33 page(s) retrieved
- looked for `Catholic Encyclopedia and Greek Wikipedia` after the audit named it; 33 page(s) retrieved
- looked for `Greek popular page` after the audit named it; 33 page(s) retrieved
- looked for `Christian Scholar's Review article` after the audit named it; 33 page(s) retrieved
- looked for `Negri biography (archive.org)` after the audit named it; 33 page(s) retrieved
- looked for `Negri biography (archive.org)` after the audit named it; 33 page(s) retrieved
- looked for `Christian Courier` after the audit named it; 33 page(s) retrieved
- looked for `Catholic Encyclopedia` after the audit named it; 33 page(s) retrieved
- looked for `Greek popular page and Wikisource author page` after the audit named it; 33 page(s) retrieved
- looked for `Catholic Encyclopedia` after the audit named it; 33 page(s) retrieved
- looked for `Catholic Encyclopedia` after the audit named it; 33 page(s) retrieved
- looked for `Catholic Encyclopedia and dokumen.pub excerpt` after the audit named it; 33 page(s) retrieved
- looked for `Catholic Encyclopedia and Tougher excerpt` after the audit named it; 33 page(s) retrieved
- looked for `Tougher excerpt and Catholic Encyclopedia` after the audit named it; 33 page(s) retrieved
- looked for `Tougher excerpt and BMCR review` after the audit named it; 33 page(s) retrieved
- looked for `Catholic Encyclopedia and Greek Wikipedia` after the audit named it; 33 page(s) retrieved
- looked for `Catholic Encyclopedia` after the audit named it; 33 page(s) retrieved
- looked for `mixanitouxronou.gr` after the audit named it; 33 page(s) retrieved
- looked for `Greek Wikipedia` after the audit named it; 33 page(s) retrieved
- looked for `Catholic Encyclopedia` after the audit named it; 33 page(s) retrieved
- looked for `Negri text and mixanitouxronou page` after the audit named it; 33 page(s) retrieved
- looked for `Catholic Encyclopedia` after the audit named it; 33 page(s) retrieved
- looked for `Christian Scholar's Review and Catholic Encyclopedia` after the audit named it; 33 page(s) retrieved
- looked for `Negri text` after the audit named it; 33 page(s) retrieved
- looked for `Catholic Encyclopedia and BMCR review` after the audit named it; 33 page(s) retrieved
- looked for `Negri text` after the audit named it; 33 page(s) retrieved
- looked for `Catholic Encyclopedia` after the audit named it; 33 page(s) retrieved
- looked for `Catholic Encyclopedia` after the audit named it; 33 page(s) retrieved
- looked for `Catholic Encyclopedia and Negri biography` after the audit named it; 33 page(s) retrieved
- looked for `Negri biography` after the audit named it; 33 page(s) retrieved
- looked for `Christian Scholar's Review and Negri biography` after the audit named it; 33 page(s) retrieved
- looked for `Negri biography` after the audit named it; 33 page(s) retrieved
- looked for `erenow page, Wikisource author page, Tougher contents` after the audit named it; 33 page(s) retrieved
- looked for `dokumen.pub Tougher text` after the audit named it; 33 page(s) retrieved
- looked for `Wikisource author page and Tougher sourcebook` after the audit named it; 33 page(s) retrieved
- looked for `Greek Wikisource author page` after the audit named it; 33 page(s) retrieved
- looked for `Catholic Encyclopedia` after the audit named it; 33 page(s) retrieved
- looked for `Catholic Encyclopedia` after the audit named it; 33 page(s) retrieved
- looked for `Wikisource author page, Tougher sourcebook, Negri index` after the audit named it; 33 page(s) retrieved
- looked for `Tougher volume excerpt (dokumen.pub)` after the audit named it; 33 page(s) retrieved
- looked for `Christian Scholar's Review article` after the audit named it; 33 page(s) retrieved
- looked for `Negri volume` after the audit named it; 33 page(s) retrieved
- looked for `Negri full text` after the audit named it; 33 page(s) retrieved
- looked for `BMCR page` after the audit named it; 33 page(s) retrieved
- looked for `Negri biography` after the audit named it; 33 page(s) retrieved
- looked for `Catholic Encyclopedia` after the audit named it; 33 page(s) retrieved
- looked for `restoration of pagan cults and temple property` after the audit named it; 33 page(s) retrieved
- looked for `revocation of clerical privileges` after the audit named it; 33 page(s) retrieved
- looked for `price edict and grain policy at Antioch` after the audit named it; 33 page(s) retrieved
- looked for `authorization to rebuild the Jerusalem Temple` after the audit named it; 33 page(s) retrieved
- the gate admitted this subject partly on `restoration of pagan cults and temple property`, which no passage covered: D14 records reopening temples and restoring sacrifice but not the restoration of temple property, and no passage gives Julian's stated rationale from letters or edicts.
- the gate admitted this subject partly on `revocation of clerical privileges`, which no passage covered: D16 and C17 record the act of stripping privileges and offices, but no passage supplies Julian's own stated reasoning for the revocation.
- the gate admitted this subject partly on `price edict and grain policy at Antioch`, which no passage covered: No passage mentions the price edict or grain policy at Antioch; W4 and C20 cover the Misopogon only for the beard satire, Babylas, and temple burning, not the economic measures or his self-justification.
- the gate admitted this subject partly on `authorization to rebuild the Jerusalem Temple`, which no passage covered: D21 records the rebuilding attempt and an inferred anti-Christian motive, but the corpus omits the letter to the Jewish community in which Julian states his reasoning.
- `C1` flagged unsupported: Wikipedia page does not state Basilina died shortly after birth; that detail is in Encyclopedia.com, not the cited page. (evidence_basis attested -> reconstructed)
- `C4` flagged unsupported: DIR page does not mention Mardonius, his origin, or tutoring Julian's mother; those details are in New World Encyclopedia/Encyclopedia.com. No retrieved page mentions Nicocles. (evidence_basis attested -> reconstructed)
- `C10` flagged unsupported: DIR page does not mention Gallus's fall, detention near Comum, or Eusebia's intercession; those are in Wikipedia/Encyclopedia.com. (evidence_basis attested -> reconstructed)
- `C11` flagged unsupported: Wikipedia page states Julian knew Gregory and Basil and was initiated, but does not state he studied under pagan and Christian teachers or that Athens offered pagan-majority intellectual life. (evidence_basis attested -> reconstructed)
- `C13` flagged unsupported: dokumen.pub excerpt mentions Ursicinus only as Ammianus's commander and Florentius, but does not state Julian operated under handlers Ursicinus, Barbatio, Florentius, or that correspondence was watched. (evidence_basis attested -> reconstructed)
- `C14` flagged unsupported: DIR page does not state Gaul devastated, Cologne sacked, Strasbourg victory, or tax cuts; those are in dokumen.pub excerpt, and 'cut taxes' is not stated anywhere (only prevented tax increase). (evidence_basis attested -> reconstructed)
- `C17` flagged unsupported: Encyclopedia.com entry does not state imperial office/army/curial class heavily Christian or New World Encyclopedia's judgment about momentum; retrieved New World Encyclopedia also lacks that judgment. (evidence_basis attested -> reconstructed)
- `C24` flagged unsupported: Encyclopedia.com entry does not describe Julian's positive program of Neoplatonism-based paganism or priesthood modeled on Christian clergy; it only says religious program met complete apathy. (evidence_basis attested -> reconstructed)
- `D2` flagged unsupported: DIR page does not state Julian slept with Maximus's letters under his pillow or sent speeches for approval; it only mentions a letter to Maximus. (evidence_basis attested -> reconstructed)
- `D6` flagged unsupported: DIR page does not detail 356 campaign, Autun, or Cologne; those details are in dokumen.pub/Catholic Encyclopedia, not DIR. (evidence_basis attested -> reconstructed)
- `D7` flagged unsupported: dokumen.pub excerpt does not state Catholic Encyclopedia's claim of unsupported by Constantius's troops or 30,000 Alamanni; it only says Ammianus describes Strasbourg set piece. (evidence_basis attested -> reconstructed)
- `D8` flagged unsupported: dokumen.pub excerpt does not state Catholic Encyclopedia's claims about reopening Rhine shipping or 359 penetration; it only mentions Salii/Chamavi offensives. (evidence_basis attested -> reconstructed)
- `D9` flagged unsupported: No retrieved page states Gaul's population appreciated extensive tax cuts; retrieved pages say he prevented a tax increase, not cut taxes. (evidence_basis attested -> reconstructed)
- `T3` flagged unsupported: Edinburgh UP page's contents list is truncated and does not show Gregory's two orations; that appears in dokumen.pub, not the cited page. (evidence_basis attested -> reconstructed)
- `T6` flagged unsupported: BMCR page does not mention Mamertinus or his Speech of Thanks; EUP page lists the title but not the gratiarum actio detail. (evidence_basis attested -> reconstructed)
- `C4` flagged laundered: Body names Catholic Encyclopedia as source for Nicocles, but no Catholic Encyclopedia page is retrieved. (evidence_basis reconstructed -> reconstructed)
- `C15` flagged laundered: Body names Catholic Encyclopedia and Greek Wikipedia; neither is among retrieved pages. (evidence_basis attested -> mixed)
- `C18` flagged laundered: Body names Christian Scholar's Review article; not retrieved. (evidence_basis attested -> mixed)
- `C19` flagged laundered: Body names Negri's biography and Libanius's On the Temples; not retrieved. (evidence_basis attested -> mixed)
- `C20` flagged laundered: Body names Negri's text; not retrieved. (evidence_basis attested -> mixed)
- `C21` flagged laundered: Body names Christian Courier; not retrieved. (evidence_basis mixed -> mixed)
- `C22` flagged laundered: Body names Catholic Encyclopedia; not retrieved. (evidence_basis attested -> mixed)
- `C23` flagged laundered: Body names Wikisource author page and Greek popular page; not retrieved. (evidence_basis mixed -> mixed)
- `D3` flagged laundered: Body names Catholic Encyclopedia; not retrieved. (evidence_basis attested -> mixed)
- `D5` flagged laundered: Body names Catholic Encyclopedia; not retrieved. (evidence_basis attested -> mixed)
- `D6` flagged laundered: Body names Catholic Encyclopedia; not retrieved. (evidence_basis reconstructed -> reconstructed)
- `D7` flagged laundered: Body names Catholic Encyclopedia; not retrieved. (evidence_basis reconstructed -> reconstructed)
- `D8` flagged laundered: Body names Catholic Encyclopedia; not retrieved. (evidence_basis reconstructed -> reconstructed)
- `D10` flagged laundered: Body names Catholic Encyclopedia and Greek Wikipedia; not retrieved. (evidence_basis attested -> mixed)
- `D11` flagged laundered: Body names Catholic Encyclopedia; not retrieved. (evidence_basis attested -> mixed)
- `D12` flagged laundered: Body names mixanitouxronou page; not retrieved. (evidence_basis attested -> mixed)
- `D13` flagged laundered: Body names Greek Wikipedia; not retrieved. (evidence_basis mixed -> mixed)
- `D14` flagged laundered: Body names Catholic Encyclopedia; not retrieved. (evidence_basis attested -> mixed)
- `D15` flagged laundered: Body names Negri text and mixanitouxronou page; not retrieved. (evidence_basis mixed -> mixed)
- `D16` flagged laundered: Body names Catholic Encyclopedia; not retrieved. (evidence_basis attested -> mixed)
- `D17` flagged laundered: Body names Christian Scholar's Review; not retrieved. (evidence_basis attested -> mixed)
- `D18` flagged laundered: Body names Negri text; not retrieved. (evidence_basis attested -> mixed)
- `D19` flagged laundered: Body names Catholic Encyclopedia; not retrieved. (evidence_basis attested -> mixed)
- `D20` flagged laundered: Body names Negri text; not retrieved. (evidence_basis attested -> mixed)
- `D21` flagged laundered: Body names Catholic Encyclopedia; not retrieved. (evidence_basis attested -> mixed)
- `D22` flagged laundered: Body names Catholic Encyclopedia; not retrieved. (evidence_basis attested -> mixed)
- `W3` flagged laundered: Body names Catholic Encyclopedia; not retrieved. (evidence_basis attested -> mixed)
- `W4` flagged laundered: Body names Negri biography; not retrieved. (evidence_basis attested -> mixed)
- `W5` flagged laundered: Body names Christian Scholar's Review and Negri; not retrieved. (evidence_basis attested -> mixed)
- `W6` flagged laundered: Body names Negri biography; not retrieved. (evidence_basis attested -> mixed)
- `W7` flagged laundered: Body names erenow page; not retrieved. (evidence_basis attested -> mixed)
- `W9` flagged laundered: Body names Wikisource author page; not retrieved. (evidence_basis attested -> mixed)
- `W10` flagged laundered: Body names Greek Wikisource author page; not retrieved. (evidence_basis attested -> mixed)
- `W12` flagged laundered: Body names Catholic Encyclopedia; not retrieved. (evidence_basis attested -> mixed)
- `W13` flagged laundered: Body names Catholic Encyclopedia; not retrieved. (evidence_basis attested -> mixed)
- `W14` flagged laundered: Body names Wikisource author page and Negri index; not retrieved. (evidence_basis attested -> mixed)
- `T2` flagged laundered: Body names Christian Scholar's Review; not retrieved. (evidence_basis attested -> mixed)
- `T3` flagged laundered: Body names Negri volume; not retrieved. (evidence_basis reconstructed -> reconstructed)
- `T4` flagged laundered: Body names Negri; not retrieved. (evidence_basis attested -> mixed)
- `T8` flagged laundered: Body names Negri; not retrieved. (evidence_basis attested -> mixed)
- `T9` flagged laundered: Body names Catholic Encyclopedia; not retrieved. (evidence_basis attested -> mixed)