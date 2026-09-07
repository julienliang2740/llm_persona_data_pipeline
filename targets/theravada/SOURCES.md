# SOURCES — Theravāda target

Provenance ledger for everything in `references/`, plus the sources deliberately **not** used.
All access dates are **7 September 2026**. Licensing assessments here are a research screening,
not legal advice; re-check terms before any use beyond this non-commercial research pilot.

---

## 1. The binding constraint: SuttaCentral

SuttaCentral's licensing page (https://suttacentral.net/licensing) carries a section headed "AI".
Retrieved verbatim on 7 Sep 2026 from the page's own localisation payload at
`https://suttacentral.net/localization/elements/licensing_en.json`, key `licensing:27` (the page
itself is a single-page application whose text does not appear in the served HTML):

> SuttaCentral does not make use of artifically-generated data. We politely request that our content
> not be scraped or used in any way for the creation of datasets for generative AI or similar. This
> request applies to those who create applications directly, and those who build apps downstream of
> AI models that have scraped SuttaCentral's data.

**Decision: SuttaCentral and its data repositories are `reference_only` for this project.**
Nothing was taken from `suttacentral.net` or from `github.com/suttacentral/bilara-data`, and no text
in `references/` derives from either. This holds even though much of the underlying material is
permissively licensed — bilara-data's own `LICENSE.md` dedicates SuttaCentral-supported translations
to the public domain under CC0, and the same licensing page states that the original-language texts
are in the public domain and that SuttaCentral's own original material is CC0. The request is about
use, not about copyright, and it is treated as binding. It also constrained the research method: the
research report this target is built from cites SuttaCentral URLs throughout, and every one of those
claims was re-verified against a different, permitted copy of the same text rather than against
SuttaCentral.

`suttacentral.net/robots.txt` was checked and permits crawling (`User-agent: * / Disallow:`); the AI
request is a separate, stronger constraint and was honoured regardless. No access controls of any
kind were bypassed anywhere in this work.

---

## 2. Files in `references/`

### Access to Insight — Thanissaro Bhikkhu translations (CC BY-NC 4.0)

Each page's own licence block was read individually and each states: *"The text of this page … is
licensed under a Creative Commons Attribution-NonCommercial 4.0 International License."*

| File | Work | Source URL | Processing |
|---|---|---|---|
| `mn019_two_sorts_of_thinking_thanissaro.txt` | MN 19 Dvedhāvitakka Sutta | accesstoinsight.org/tipitaka/mn/mn.019.than.html | HTML stripped; site chrome and footer removed; whitespace normalised; provenance header prepended |
| `mn044_shorter_questions_thanissaro.txt` | MN 44 Cūḷavedalla Sutta | .../mn/mn.044.than.html | same |
| `mn058_to_prince_abhaya_thanissaro.txt` | MN 58 Abhaya Sutta | .../mn/mn.058.than.html | same |
| `mn061_instructions_to_rahula_thanissaro.txt` | MN 61 Ambalaṭṭhika-rāhulovāda Sutta | .../mn/mn.061.than.html | same |
| `mn117_the_great_forty_thanissaro.txt` | MN 117 Mahācattārīsaka Sutta | .../mn/mn.117.than.html | same |
| `sn42_03_to_the_warrior_thanissaro.txt` | SN 42.3 Yodhājīva Sutta | .../sn/sn42/sn42.003.than.html | same |
| `sn56_11_setting_the_wheel_thanissaro.txt` | SN 56.11 Dhammacakkappavattana Sutta | .../sn/sn56/sn56.011.than.html | same |
| `an03_065_to_the_kalamas_thanissaro.txt` | AN 3.65 Kālāma Sutta | .../an/an03/an03.065.than.html | same |
| `an03_100_the_salt_crystal_thanissaro.txt` | AN 3.100 Loṇaphala Sutta | .../an/an03/an03.099.than.html | same; note the site numbers it AN 3.99 (Thai 3.101) |
| `an05_177_wrong_livelihood_thanissaro.txt` | AN 5.177 Vaṇijjā Sutta | .../an/an05/an05.177.than.html | same |
| `an06_063_penetrative_thanissaro.txt` | AN 6.63 Nibbedhika Sutta | .../an/an06/an06.063.than.html | same |
| `dn26_wheel_turning_emperor_thanissaro.txt` | DN 26 Cakkavatti Sutta | .../dn/dn.26.0.than.html | same |

- **Rights holder:** Thanissaro Bhikkhu; Access to Insight (BCBS Edition), Barre Center for Buddhist Studies.
- **Licence:** Creative Commons Attribution-NonCommercial 4.0 International.
- **AI-use restriction:** none stated. Access to Insight publishes no `robots.txt`; requests were made
  at roughly one per 1.2 seconds.
- **Condition this places on the project:** the NC term makes this material usable for a
  non-commercial research pilot **only**. Any commercial use of a dataset or model derived from these
  files would require separate permission from the translator. This is the single most important
  downstream constraint in this target and it should be carried into the run manifest.
- **Attribution required in any redistribution:** e.g. *"Abhaya Sutta: To Prince Abhaya" (MN 58),
  translated from the Pali by Thanissaro Bhikkhu. Access to Insight (BCBS Edition), 30 November 2013.*

### Ancient Buddhist Texts — Ānandajoti Bhikkhu (CC BY-SA 3.0)

| File | Work | Source URL | Processing |
|---|---|---|---|
| `dn16_selected_anandajoti.txt` | DN 16 Mahāparinibbāna Sutta, four sections (§§1.12, 1.13, 1.23-24, 1.26ff) | ancient-buddhist-texts.net/English-Texts/Great-Emancipation/ | HTML stripped; audio widgets and navigation removed; section labels added; translator's footnotes retained inline |
| `dhammapada_selected_anandajoti.txt` | Dhammapada chapters 1, 2, 3, 5, 6, 8, 9, 10, 12, 14, 15, 16, 17, 18, 20, 24, Pāli with facing English | ancient-buddhist-texts.net/English-Texts/Dhamma-Verses/ | same |

- **Rights holder:** Ānandajoti Bhikkhu.
- **Licence:** Creative Commons Attribution-ShareAlike 3.0 Unported, confirmed at
  https://www.ancient-buddhist-texts.net/Miscellaneous/Copyright-Notice.htm on 7 Sep 2026. The site's
  Pāli root texts are prepared from the public-domain Buddha Jayanti Tripitaka. Some other items on
  that site are third-party copyrighted (Pali Text Society, Motilal Banarsidass and others); none of
  those were taken.
- **AI-use restriction:** none stated.
- **Condition this places on the project:** ShareAlike. Redistribution of these files or of adaptations
  of them requires the same licence and attribution to Anandajoti Bhikkhu. Whether a fine-tuned model
  counts as an adaptation under CC BY-SA 3.0 is unsettled; the conservative course is to attribute and
  to note the licence in the run manifest. **Note the interaction:** CC BY-SA 3.0 and CC BY-NC 4.0 are
  not mutually compatible for a combined redistributable work. This pilot mixes them in a research
  corpus, which is defensible for internal non-commercial use, but a *published* dataset would need
  either to segregate the two or to obtain permission. Flagged for human review.

### Public-domain print translations (Internet Archive scans)

| File | Work | Translator / edition | Source | Processing |
|---|---|---|---|---|
| `mn009_right_ideas_chalmers.txt` | MN 9 Sammādiṭṭhi Sutta | Lord Chalmers, *Further Dialogues of the Buddha* vol. I (Sacred Books of the Buddhists V), Oxford University Press, 1926 | archive.org/details/Chalmers-MN | OCR text sliced to the sutta; running page headers removed; end-of-line hyphenation rejoined; OCR errors NOT hand-corrected |
| `mn021_parable_of_the_saw_chalmers.txt` | MN 21 Kakacūpama Sutta | same volume | same | same |
| `dn26_poverty_sequence_rhys_davids.txt` | DN 26 §§10-16 | T. W. & C. A. F. Rhys Davids, *Dialogues of the Buddha* Part III (Sacred Books of the Buddhists IV), Oxford University Press, 1921 | archive.org/details/dialoguesofbuddh03davi | same, plus double-space normalisation |
| `dn31_sigalovada_rhys_davids.txt` | DN 31 Sigālovāda Suttanta, complete | same volume | same | same |

- **Licence:** public domain. Both volumes were published before 1930 and are out of copyright in the
  United States; the Internet Archive items carry no rights restriction.
- **AI-use restriction:** none.
- **Known defect:** these are optical character recognition outputs from scanned print. Wording is
  approximate — proper names, diacritics and footnote markers are unreliable. Every passage quoted
  from these files in `references/key_passages.md` was read against the surrounding text and, where a
  Pāli anchor exists, against `pali_anchors_sltp.txt`. Do not treat these files as citable editions.

### Pāli originals

| File | Work | Source | Processing |
|---|---|---|---|
| `pali_anchors_sltp.txt` | 17 short Pāli excerpts anchoring the passages this target relies on | Sri Lanka Tripitaka Project, republished at accesstoinsight.org/tipitaka/sltp/ | volume HTML stripped; excerpts located by string search and copied verbatim, including SLTP's editorial footnote digits and `[BJT Page nnn]` markers |

- **Licence:** public domain. The Access to Insight SLTP page states: *"The text of this page ('Sri
  Lanka Tripitaka Project: Pali Tipitaka Source Texts', by Public domain) is free of known copyright
  restrictions."* Its document metadata records `[LICENSE]={PUBLIC_DOMAIN}`. SuttaCentral's own
  licensing page independently states that the original-language texts are in the public domain.
- **AI-use restriction:** none.
- **Known defect:** the SLTP project itself warns that transcription errors exist and that serious
  research should cross-check printed editions. These excerpts were checked against the English
  translations in this directory but **not** against a printed critical edition. Orthography differs
  from the Ānandajoti files: SLTP writes niggahita as `ṃ`, Ānandajoti as `ṁ`.

### Project-authored

| File | Content | Notes |
|---|---|---|
| `key_passages.md` | 64 curated passages with ids, evidence labels, excerpts and grounding notes | Excerpts are quoted from the permitted files above under their respective licences, or are this project's own paraphrase where marked `(par.)`. Two entries record corrections to the research report. |

---

## 3. Sources deliberately not used

| Source | Terms | Why not used |
|---|---|---|
| **SuttaCentral** (suttacentral.net) | SuttaCentral's own material CC0; original languages public domain; **explicit request that content not be used to create generative-AI datasets** | `reference_only`. See §1. Nothing taken. |
| **bilara-data** (github.com/suttacentral/bilara-data) | Supported translations CC0 | `reference_only`. CC0 would permit it, but the repository is SuttaCentral's own and its `LICENSE.md` points back to the SuttaCentral licensing page. The AI request is treated as extending to it. Nothing taken. |
| **Ñāṇamoli, *The Path of Purification*** (Visuddhimagga) | Modern translation under copyright | `reference_only`. Consulted at wisdomlib.org to verify the near/far enemy analysis at IX.98-101. `key_passages.md` carries this project's own paraphrase from the Pāli, not a quotation, and says so. |
| **Ñāṇamoli & Bodhi, MN 9** (accesstoinsight.org/tipitaka/mn/mn.009.ntbb.html) | © 1991 Buddhist Publication Society, free-distribution licence: copies only free of charge, reprints capped at 50, derivatives must indicate derivation and include the full licence text | `reference_only`. The licence permits redistribution but attaches conditions to *derivative works* that a fine-tuned model could not cleanly satisfy. The public-domain Chalmers translation of MN 9 is used instead. |
| **Narada Thera, DN 31** (accesstoinsight.org/tipitaka/dn/dn.31.0.nara.html) | © 1985 Buddhist Publication Society, same free-distribution licence | `reference_only`, same reasoning. The public-domain Rhys Davids translation of DN 31 is used instead. |
| **dhammatalks.org sutta pages** | No licence statement on the sutta pages; `dhammatalks.org/copyright.html` returns 404 | `reference_only`. Consulted for MN 21, which Access to Insight does not host, to confirm the text exists as the report describes. No text taken; the public-domain Chalmers translation is used for MN 21. |
| **Bhikkhu Bodhi's Wisdom Publications translations** (MN, SN, AN) | Commercial copyright | `reference_only`. Not consulted online; cited only by the research report. |
| **Pali Text Society editions and post-1930 PTS translations** | Copyright; no open licence | `reference_only`. Includes Horner's *Middle Length Sayings* (1954-59), Woodward and Hare's *Gradual Sayings* (1932-), and Pe Maung Tin's *Path of Purity* Part II, which some catalogue entries date to 1931 and which is therefore not safely public domain in 2026. This is why the Visuddhimagga passage is paraphrased. |
| **VRI / Chaṭṭha Saṅgāyana Tipiṭaka XML** | Repository states non-commercial use | Not needed; SLTP covers the Pāli requirement under clearer public-domain terms. |
| **CRAN `tipitaka` / `tipitaka.critical`** | Packages declare CC0 while incorporating upstream material with different terms | Not used. The wrapper licence does not clear every upstream component; a provenance problem this project has no reason to inherit. |
| **GRETIL** | Mixed CC BY-SA notices with scholarly-use caveats, case by case | Not needed. |
| **Modern academic monographs** (Heim, Keown, Harvey, Hallisey, Crosby, Braun, Sharf, McMahan) | Commercial copyright | `reference_only`. Used as citations in `research_notes.md`; no text ingested. |
| **Journal of Buddhist Ethics articles** (Gethin 2004, Keown 2016, Karunanayaka 2026) | Open-access journal; individual article rights with authors | `reference_only`. Only titles, authors, and short abstract phrases are quoted in `key_passages.md` and `research_notes.md`, to record that a live scholarly disagreement exists. Full texts not ingested. |

---

## 4. Summary of downstream obligations

Anyone consuming this target must carry these forward:

1. **Non-commercial only.** Twelve of the twenty grounding files are CC BY-NC 4.0. A commercial
   dataset or model derived from this target requires separate permission from Thanissaro Bhikkhu.
2. **ShareAlike exposure.** Two grounding files are CC BY-SA 3.0. Redistribution of them or of
   adaptations requires the same licence and attribution to Anandajoti Bhikkhu.
3. **Licence incompatibility between 1 and 2** for a single published redistributable work. Internal
   research use is defensible; publication is not, without segregation or permission. Flagged for
   human review.
4. **No SuttaCentral-derived text may enter this pipeline**, at any stage, including via a generator
   model's own recall. The `cue_policy` term list does not detect this; a reviewer should watch for
   verbatim modern translation phrasing that matches no file in `references/`.
5. **Attribution strings** for each file are in that file's own header comment.
