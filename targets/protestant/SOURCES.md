# Provenance ledger — target `protestant`

All items retrieved **2026-09-07** by the research teammate for this target. Licence statements
below record what the named page actually said on that date, quoted or closely paraphrased; they
are a corpus-engineering record, not legal advice.

Two standing cautions carried from the research report:

1. **Licence attaches to the edition, not the work.** A 1530 confession being out of copyright does
   not make a 2025 translation of it free. Every entry names the specific edition acquired.
2. **A site's terms can be narrower than the underlying text's status.** Where the two differ, both
   are recorded.

No paywall was bypassed. No modern denominational statement and no modern scholarship was copied
into `references/`.

---

## Files in `references/`

### `web_moral_passages.txt` — 143,713 bytes, 27,530 words

| | |
|---|---|
| Work | The Holy Bible, selected moral passages (38 chapters, 1,096 verses) |
| Edition | World English Bible, 2020 stable text edition, 66-book protocanon (`engwebp`) |
| URL | https://ebible.org/engwebp/ (per-chapter HTML); terms at https://ebible.org/engwebp/copyright.htm |
| Accessed | 2026-09-07 |
| Licence | **Public domain.** Verified on the copyright page: "The World English Bible is in the Public Domain. That means that it is not copyrighted... You may copy, publish, proclaim, distribute, redistribute, sell, give away, quote, memorize, read publicly, broadcast, transmit, share, back up, post on the Internet, print, reproduce, preach, teach from, and use the World English Bible as much as you want, and others may also do so." |
| AI-use restriction | None stated. One trademark condition: "World English Bible" is a trademark of eBible.org, and altered text must not keep the name. This file is **unaltered in wording**, so the condition is not triggered; any downstream paraphrase must not be labelled WEB. |
| Processing | Chapters GEN01, EXO20, LEV19, DEU05, MIC06, MAT05-07, MAT18, MAT22, MAT25, LUK06, LUK10, LUK12, LUK16, JHN13, ROM12-14, 1CO08, 1CO13, GAL05-06, EPH04-06, PHP02, COL03, 1TI06, JAS01-05, 1PE02-03, 1JN03-04. HTML markup, navigation, chapter labels, translator footnotes and footnote popups removed. Verses re-laid one per line with an `WEB <Book> <ch>:<v>` prefix. Wording untouched, including WEB's own quotation marks and small-caps LORD. |

*The ZIP bundles at `ebible.org/Scriptures/` (`engwebp_vpl.zip`, `engwebp_usfm.zip`) failed to
download from this host; per-chapter HTML was used instead.*

### `augsburg_confession.txt` — 59,585 bytes, 10,436 words

| | |
|---|---|
| Work | The Augsburg Confession, 1530. Articles I–XXI, XXVI, XXVII, XXVIII |
| Edition | *Concordia Triglotta* English translation (Bente / Dau, Concordia Publishing House, 1921) as published at thebookofconcord.org |
| URL | https://thebookofconcord.org/augsburg-confession/ ; terms at https://thebookofconcord.org/legal/ |
| Accessed | 2026-09-07 |
| Licence | **Out of copyright**, per the site's legal page: "Most of the text on this site is from the Triglotta edition of the Book of Concord, which is no longer covered by copyright; consequently, the overwhelming majority of the text on this site may be freely copied, shared, et cetera." The same page warns that "some other materials (e.g., Scripture translations) on this site are subject to the copyrights of their various owners" — none of those were taken. |
| AI-use restriction | None stated. |
| Processing | Per-article pages fetched. Site navigation, sidebar, breadcrumb and the Confutation/Apology cross-links removed; only the Confession text kept. Triglotta paragraph numbers preserved inline as `[n]`. |

### `westminster_confession_1646.txt` — 72,718 bytes, 12,506 words

| | |
|---|---|
| Work | The Westminster Confession of Faith, 1646 (first printed 1647) |
| Edition | *The Confession of Faith of the Assembly of Divines at Westminster*, Tercentenary Edition, ed. S. W. Carruthers, Presbyterian Church of England, 1946 — a transcription of the 1646 manuscript written by Cornelius Burges |
| URL | https://en.wikisource.org/wiki/The_Confession_of_Faith_of_the_Assembly_of_Divines_at_Westminster |
| Accessed | 2026-09-07 |
| Licence | **Public domain.** The Wikisource page carries `{{PD-old}}` and its text-status marker is "validated". Wikisource's own editorial contributions are CC BY-SA; only the transcribed 17th-century text was taken. |
| AI-use restriction | None stated. |
| Processing | Fetched as rendered HTML via the Wikisource REST API (the wikitext is ProofreadPage transclusion and yields nothing on its own). Parsoid `data-mw` JSON blobs, page-number spans, headers, navigation and scripture proof-text references removed. |
| **Important** | This is the **original British text**, not the American Presbyterian revision. Chapters 20.4, 23.3 and 10.4 therefore contain positions this target explicitly does not generate from; they are retained deliberately as documented boundaries. See `spec.yaml` boundaries and `research_notes.md`. |

### `westminster_larger_catechism.txt` — 94,105 bytes, 16,041 words

| | |
|---|---|
| Work | The Westminster Larger Catechism, 1647. All 196 questions |
| Edition | **Not established.** The Wikisource page carries a `{{no source}}` maintenance tag and a 50% text-quality rating; spelling is modernised ("binds" for "bindeth") relative to 17th-century printings. |
| URL | https://en.wikisource.org/wiki/Westminster_Larger_Catechism |
| Accessed | 2026-09-07 |
| Licence | The 1647 text is public domain. Because the transcriber's source edition is unidentified, this file's provenance is weaker than the others here. |
| AI-use restriction | None stated. |
| Processing | MediaWiki markup removed. Two transcription artefacts repaired mechanically: a colon-plus-capital pattern that rendered list items as ": What" (127 occurrences, changed to "; what" everywhere except the `Question N:` and `Answer:` headers) and `man_stealing` → `man-stealing`. **Cross-checked** question by question against the Orthodox Presbyterian Church text at https://opc.org/lc.html for Q99, Q135, Q136, Q141, Q142, Q144 and Q145 — every one of these is used in `spec.yaml`. Substance matches; only spelling and the numbering of Q99's eight rules differ. |
| Cross-check source | https://opc.org/lc.html — `use: reference_only`, consulted as a second witness, not copied. |

### `heidelberg_catechism.txt` — 48,097 bytes, 8,732 words

| | |
|---|---|
| Work | The Heidelberg Catechism, 1563 (English) |
| Edition | Philip Schaff, *The Creeds of Christendom*, Vol. III: The Creeds of the Evangelical Protestant Churches, 1877 |
| URL | https://www.ccel.org/ccel/schaff/creeds3.iv.vi.html |
| Accessed | 2026-09-07 |
| Licence | Underlying 1877 work is **public domain** (Schaff d. 1893). **The CCEL edition is not unrestricted:** the site's copyright policy (https://www.ccel.org/about/copyright.html) states "CCEL.org website and special contents copyright 1993–2020 Harry Plantinga", that most editions are based on US-public-domain books, and that "These books may be used for personal, educational, or non-profit purposes. Contact us for permission to republish CCEL works or to use them commercially." |
| AI-use restriction | None specific to AI. The non-commercial condition above applies to the CCEL edition. **This pilot is research use and is within it; a commercial run should either clear it with CCEL or re-source from a public-domain scan of Schaff (available on the Internet Archive).** |
| Processing | Schaff prints German and English in parallel table columns. Only the **English** column was kept (identified by the absence of `lang="DE"`); German text, Schaff's page numbers and HTML markup removed. |

### `thirty_nine_articles.txt` — 31,086 bytes, 5,341 words

| | |
|---|---|
| Work | The Thirty-Nine Articles of Religion of the Church of England, 1563/1571, with the Royal Declaration |
| Edition | *The Book of Common Prayer*, 1863 printing |
| URL | https://en.wikisource.org/wiki/Book_of_Common_Prayer_(1863)/Articles_of_Religion |
| Accessed | 2026-09-07 |
| Licence | **Public domain** — both the 16th-century work and the 1863 printing. |
| AI-use restriction | None stated. |
| Processing | Rendered HTML via the Wikisource REST API; Parsoid artefacts, page-scan furniture and navigation removed. |
| Note | The **current** Church of England Book of Common Prayer text was **not** used: the C of E states that rights in it are vested in the Crown and reproduced by permission of the Crown's Patentee. The 1863 printing avoids that question. |

### `baptist_confession_1689.txt` — 87,740 bytes, 15,252 words

| | |
|---|---|
| Work | The Second London Baptist Confession of Faith, 1677/1689 |
| Edition | **Not established** — the Wikisource page carries `{{no source}}` and `{{standardize}}` tags. |
| URL | https://en.wikisource.org/wiki/1689_Baptist_Confession_of_Faith |
| Accessed | 2026-09-07 |
| Licence | The 17th-century text is public domain. Provenance of this particular transcription is weak, as above. |
| AI-use restriction | None stated. |
| Processing | MediaWiki markup removed; parenthetical scripture proof-texts retained. Chapter 21 (Christian liberty and liberty of conscience) **cross-checked** against https://1689londonbaptistconfession.com/21/ — matches. |
| Cross-check source | https://1689londonbaptistconfession.com/21/ — `use: reference_only`, not copied. |

### `luther_christian_liberty.txt` — 100,644 bytes, 18,649 words

| | |
|---|---|
| Work | *Concerning Christian Liberty* (*Von der Freiheit eines Christenmenschen*, 1520), with Luther's letter to Pope Leo X |
| Edition | English translation by R. S. Grignon, as printed in the Harvard Classics vol. 36 (1910) |
| URL | https://www.gutenberg.org/ebooks/1911 (text at `https://www.gutenberg.org/cache/epub/1911/pg1911.txt`) |
| Accessed | 2026-09-07 |
| Licence | Project Gutenberg eBook #1911, release date 26 February 2006, listed as **public domain in the USA**. PG's standard notice adds that readers outside the USA must check local law. |
| AI-use restriction | None stated. |
| Processing | Project Gutenberg header and footer, including the PG licence and trademark boilerplate, **removed**. Under the PG licence, stripping the header means the Project Gutenberg trademark may not be applied to this file; the underlying text remains public domain. Nothing else altered. |

### `calvin_on_the_christian_life.txt` — 106,246 bytes, 18,471 words

| | |
|---|---|
| Work | *On the Christian Life* = *Institutes of the Christian Religion*, Book III, chapters VI–X |
| Edition | Translated by Henry Beveridge, 1845, for the Calvin Translation Society |
| URL | https://www.ccel.org/c/calvin/christian_life/christian_life1.0.txt (book page: https://www.ccel.org/c/calvin/christian_life/christian_life.html) |
| Accessed | 2026-09-07 |
| Licence | The CCEL book page states explicitly: **"This book is in the public domain."** CCEL's site-wide policy additionally asks that commercial republication of CCEL editions be cleared with them (see the Heidelberg entry). |
| AI-use restriction | None specific to AI. |
| Processing | **None.** The plain-text edition as published by CCEL, retrieved verbatim. |
| Note | CCEL's `CHAPTER I–V` correspond to *Institutes* III.6–III.10. Passage ids in this target use the *Institutes* numbering: CCEL ch. II = `Calvin Inst. 3.7`. |

### `wesley_catholic_spirit.txt` — 32,034 bytes, 5,775 words<br>`wesley_use_of_money.txt` — 29,635 bytes, 5,303 words

| | |
|---|---|
| Works | John Wesley, "Catholic Spirit" (Sermon 39) and "The Use of Money" (Sermon 50) |
| Edition | *Sermons on Several Occasions*, 1872 edition (the Thomas Jackson edition of Wesley's *Works*) |
| URL | https://www.ccel.org/ccel/wesley/sermons.v.xxxix.html and `.../sermons.v.l.html` |
| Accessed | 2026-09-07 |
| Licence | Wesley d. 1791; the 1872 edition is **public domain**. CCEL's non-commercial condition on its own editions applies as above. |
| AI-use restriction | None specific to AI. |
| Processing | CCEL site chrome, reader controls, Bible-version selector and prev/next navigation removed. Wesley's own roman-numeral sections and numbered paragraphs preserved, which is what the passage ids key on. |

### `wesley_general_rules.txt` — 8,024 bytes, 1,362 words

| | |
|---|---|
| Work | John Wesley, "The Nature, Design, and General Rules of Our United Societies", 1743 |
| Edition | *The Doctrines and Discipline of the Methodist Episcopal Church*, 1888, Part I ch. I, paragraphs 28–35. **American Methodist Episcopal recension**, not Wesley's 1743 English original. |
| URL | https://archive.org/download/doctrinesanddis35churgoog/doctrinesanddis35churgoog_djvu.txt |
| Accessed | 2026-09-07 |
| Licence | **Public domain** — an 1888 imprint. Internet Archive serves this Google-digitised scan without asserting additional restrictions over the text. |
| AI-use restriction | None stated. |
| Processing | Paragraphs 28–35 extracted; running heads, "Digitized by Google" artefacts, page numbers and hyphenated line breaks removed. **The file is uncorrected OCR** and contains word-level misreadings ("f^th" for "faith", "admoni^" for "admonish", "3mploying" for "employing"). Excerpts quoted into `key_passages.md` were hand-corrected against a second witness, the 1853 Discipline (Internet Archive `doctrinesdiscipl0000meth_u7v9`), whose OCR is worse overall but independent. |
| **Important** | This recension contains "Slave-holding; buying or selling slaves" among the prohibitions, added in the American Discipline and absent from Wesley 1743. Its rules on spirituous liquors, Lord's Day commerce and usury are **historical branch discipline, not shared core**, and are labelled `historical` in `key_passages.md`. |

*The UMC's own page for the General Rules (https://www.umc.org/en/content/the-general-rules-of-the-methodist-church), cited by the research report, carries a modern site copyright and was not used as a source file.*

### `key_passages.md` — 39,138 bytes, 6,571 words

Derived work, authored for this target. ~80 excerpts drawn from the files above, each carrying a
passage id, a normative label (`shared_core` / `branch:<name>` / `historical`), the excerpt, and a
note on what it grounds. Its licence is that of its constituents; the scripture excerpts are public
domain, and the confessional excerpts are short quotations from out-of-copyright editions.

---

## `reference_only` — consulted, deliberately NOT copied into `references/`

| Source | URL | Terms as found | Why excluded |
|---|---|---|---|
| Baptist Faith and Message 2000 (SBC) | https://bfm.sbc.net/bfm2000/ | Freely readable; no open reuse licence verified | Post-1900, and one contemporary body's position rather than a Baptist consensus. Its stewardship material is represented instead through the 1689 Confession, Calvin and Wesley. |
| The Lausanne Covenant (1974) | https://lausanne.org/statement/lausanne-covenant | Freely readable; no blanket open licence verified | Post-1900, outside this target's historical scope, and not licence-cleared. Its ethics of persuasion without coercion is instead grounded in WEB 1 Pet 3:15-16 and WLC Q145. |
| The Cape Town Commitment (2010) | https://lausanne.org/statement/ctcommitment | As above | As above. |
| The Lausanne Standards | https://lausanne.org/content/the-lausanne-standards | **CC BY-NC 4.0** | Usable non-commercially with attribution, but post-1900 and not needed once Lausanne is out of scope. Recorded for a future spec version. |
| Lausanne wealth-creation paper | https://lausanne.org/content/wealth-creation-biblical-views-perspectives | Personal/educational distribution permitted; **commercial use prohibited** | Same, plus an explicit commercial-use bar. |
| UMC General Rules page | https://www.umc.org/en/content/the-general-rules-of-the-methodist-church | Modern site copyright | The 1888 public-domain Discipline was sourced instead. |
| Church of England Book of Common Prayer | https://www.churchofengland.org/prayer-and-worship/worship-texts-and-resources/book-common-prayer | Rights stated to be vested in the Crown, reproduced by permission of the Crown's Patentee | The 1863 BCP printing was used for the Articles instead. Liturgical formation is noted as an Anglican branch feature but not grounded in text. |
| OPC Westminster texts | https://opc.org/lc.html , https://opc.org/WCF-WIP.html , https://opc.org/documents/WCF_orig.html | Freely accessible; no broad reuse licence established | Used **only** as a cross-check witness for the Larger Catechism. Not copied. |
| 1689londonbaptistconfession.com | https://1689londonbaptistconfession.com/21/ | Site transcription; terms not established | Used **only** to cross-check chapter 21. Not copied. |
| Heidelberg Catechism (RCA) | https://www.rca.org/about/theology/creeds-and-confessions/the-heidelberg-catechism/ | Modern displayed translation; reuse licence not established | Schaff 1877 used instead. |
| Richard Hooker, *Laws of Ecclesiastical Polity* | 1888 Keble edition, various hosts | 1888 edition public domain; some hosts modernise wording silently | Not acquired. Anglican reasoning is represented by the Articles alone, which under-represents the natural-law strand. Recorded as a gap in `research_notes.md`. |
| ELCA / LCMS / PCUSA / UMC current statements | denominational sites | Individual site terms; none cleared | Consulted through the research report only. Their mutual disagreement is the *evidence* for the `sexual_and_family_ethics` and `church_and_state` unresolved choices; none is normative here. |
| Oxford / Cambridge handbooks and monographs (Meilaender & Werpehowski; Grobien; Joyce on Hooker; Maddox; Holmes; Bingham; Bebbington) | publisher platforms | Copyrighted, subscription or purchase | Used to shape the taxonomy and the plurality claim. **No text ingested.** Claims resting only on these and not checkable against a primary source are listed as unverified in `research_notes.md`. |

---

## Reproducing this acquisition

Every file above is retrievable from the listed URL with `curl`. The three transformations that are
not obvious from the URL alone are recorded per file: the WEB verse re-layout, the Schaff
English-column extraction, and the General Rules paragraph range. No source required a login, a
paid subscription, or circumvention of any access control.
