# SOURCES — targets/confucian

Provenance for everything in `references/`, plus sources that were checked and deliberately
not ingested. All access dates are **7 September 2026**.

---

## Acquired and included in `references/`

### 1. `references/analects_legge.txt`

| field | value |
|---|---|
| Work | 論語 *Lunyu*, the Confucian Analects (received text) |
| Translation | James Legge, *The Chinese Classics* vol. I, 1861; revised 1893 |
| English source | Project Gutenberg eBook **#3330**, "The Analects of Confucius (from the Chinese Classics)" |
| English URL | https://www.gutenberg.org/ebooks/3330 — plain text at https://www.gutenberg.org/cache/epub/3330/pg3330.txt |
| Chinese source | Project Gutenberg eBook **#4094**, "The Chinese Classics — Volume 1: Confucian Analects" (Legge's bilingual edition) |
| Chinese URL | https://www.gutenberg.org/ebooks/4094 |
| Access date | 2026-09-07 |
| Licence | Public domain in the United States. Gutenberg's own metadata records "Public domain in the USA." Legge died in 1897, so the translation is out of copyright in life+70 jurisdictions as well. |
| AI-use restrictions | None stated. The Project Gutenberg licence permits copying, redistribution and reuse; the PG trademark header and footer were removed, which the licence permits for works used without the trademark. |

**Processing applied**

1. Downloaded with `curl`; PG header/footer and the digitiser's note stripped.
2. Split on `BOOK <roman>.` headings (20 books) and `CHAP. <roman>.` headings.
3. **Six chapter headings are misnumbered in the Gutenberg transcription**: book 2 chapter 18
   is printed "XVII" (duplicating 17); book 3 chapter 18 is printed "XVII" and chapter 23 is
   printed "XXXII"; book 5 chapter 8 is printed "VII"; book 9 chapter 23 is printed "XXV";
   book 14 chapter 47 is printed "XLVI". In every case the heading itself is present and the
   run is otherwise complete, so chapters were renumbered sequentially within each book.
4. The resulting per-book chapter counts were checked against Legge's own bilingual edition
   (#4094), whose Chinese carries explicit 【第N章】 markers. All 20 books matched
   (16, 24, 26, 26, 27, 28, 37, 21, 30, 18, 25, 24, 30, 47, 41, 14, 26, 11, 25, 3 = 499).
5. The Chinese of each chapter was taken from #4094, section markers 【N節】 removed, and
   appended to the English as a `[zh]` line.

**Passage ids.** Legge's own book.chapter division. It agrees with the commonly cited (Zhu Xi)
numbering in most books; it differs chiefly in book 15, where Legge counts as one chapter the
two openings usually counted separately, so from 15.2 onward Legge's number is one lower. The
reciprocity passage is **Legge 15.23 = commonly cited 15.24**. `key_passages.md` gives the
alternate number in brackets wherever the two differ. An earlier attempt to key the file to a
Chinese edition's numbering was abandoned because that edition splits chapters idiosyncratically
(it divides Analects 12.1 in two, which no standard division does); keying to Legge avoids
inventing a mapping.

---

### 2. `references/mengzi_legge.txt`

| field | value |
|---|---|
| Work | 孟子 *Mengzi*, the Works of Mencius |
| Translation | James Legge, *The Chinese Classics* vol. II, 1861; revised 1895 |
| English source | English Wikisource, "The Chinese Classics/Volume 2/The Works of Mencius", chapters 01–14 |
| English URL | https://en.wikisource.org/wiki/The_Chinese_Classics/Volume_2/The_Works_of_Mencius |
| Chinese source | Project Gutenberg eBook **#24178** (孟子) |
| Chinese URL | https://www.gutenberg.org/ebooks/24178 |
| Access date | 2026-09-07 |
| Licence | Public domain. The Wikisource page carries `{{translation license|original={{pd-old}}|translation={{pd-old}}}}` — both the Chinese original and Legge's translation are marked public domain by age. Gutenberg records #24178 as "Public domain in the USA." |
| AI-use restrictions | None stated. Wikimedia projects permit automated access; retrieval used the MediaWiki API with a descriptive User-Agent and a 1-second delay between the 14 requests. |

**Why not Project Gutenberg for the English.** Gutenberg has no complete Legge *Mencius*.
eBook #10056 ("Chinese literature", ed. Wilson) contains only a short Legge selection, roughly
book 1; it was checked and rejected as incomplete.

**Processing applied**

1. Fetched the 14 chapter pages via `action=parse&prop=wikitext`; MediaWiki templates, link
   markup, ref tags and bold/italic markup stripped. Each page interleaves a `{{lang|zh|…}}`
   Chinese paragraph with its Legge English paragraph.
2. The Wikisource pages carry **no chapter numbers** — they are continuous paragraph runs per
   book-part. Chapter boundaries were therefore taken from the Chinese edition (#24178), which
   numbers chapters explicitly under each 卷 heading.
3. The #24178 chapter counts were verified against the standard division and match it exactly:
   1A 7, 1B 16, 2A 9, 2B 14, 3A 5, 3B 10, 4A 28, 4B 33, 5A 9, 5B 9, 6A 20, 6B 16, 7A 46,
   7B 38 — 260 chapters. (One chapter number in #24178, 4B.10, shares a line with its text and
   needed a parser adjustment; no chapter is missing.)
4. Each Wikisource Chinese paragraph was matched into the concatenated Chinese of its book-part
   to determine which chapter it falls in. 681 of 688 paragraphs matched on a 7–24 character
   prefix. The remaining 7 are short interlocutor lines absent from the #24178 edition; in all
   7 the preceding and following matched paragraphs fall in the same chapter, so assignment was
   unambiguous.
5. Result: all 260 chapters covered, no gaps. Spot-checked against known content for
   1A.7, 1B.8, 2A.6, 4A.17, 4B.11, 5A.2, 6A.10, 6A.15, 7A.35, 7B.14.

**Passage ids.** `Mengzi <book><A|B>.<chapter>`, the standard division, e.g. `Mengzi 4A.17`.

---

### 3. `references/key_passages.md`

Compiled for this project. ~90 passages, 5,700 words. Contains short excerpts from the two
public-domain Legge translations above, plus a small number of close paraphrases explicitly
marked *[paraphrase]*, and a one-line note per passage on what it grounds. Every passage was
read in the full reference text before being included; two citation errors found during
checking are recorded in `research_notes.md`. No copyrighted translation is quoted anywhere.

---

## Checked and deliberately NOT ingested

### Chinese Text Project (ctext.org) — `use: reference_only`

- URL: https://ctext.org/analects , https://ctext.org/mengzi
- Checked: 2026-09-07. `https://ctext.org/robots.txt` retrieved and read.
- **Finding: their robots.txt disallows automated retrieval by AI crawlers and bulk
  downloaders.** `GPTBot`, `ChatGPT-User` and `Amazonbot` are given `Disallow: /`, as are
  `Python-urllib`, `Python`, `HTTrack`, `WebCopier`, `WebStripper`, `Teleport Pro`,
  `Mass Downloader`, `SiteSucker`, `Nutch`, `ia_archiver` and a long list of other
  crawlers and site-mirroring tools.
- **Action taken: no text was downloaded from ctext.org.** Two pages were retrieved manually
  to read the site's own terms (`/robots.txt` and `/faq`); no corpus content was taken and no
  crawling was performed. Their Chinese text is not present in `references/`.
- This cost nothing, because complete public-domain Chinese texts of both works were available
  from Project Gutenberg (#4094 for the Analects, #24178 for the Mengzi) and are used instead.
- ctext remains useful to a human reviewer for passage lookup, parallel passages and their
  chapter numbering, which is why it is recorded here rather than omitted.

### Kanripo / traditional commentary — `use: reference_only`

Not acquired. Traditional commentary (He Yan, Xing Bing, Zhu Xi's *Sishu zhangju jizhu*) is
valuable for difficult passages but belongs to later reception history. Under this target's
scope it must be tagged by commentator and period and must not be presented as the view of
Confucius or Mencius, so it was left out of a pilot-scale reference set rather than included
with insufficient tagging.

### Copyrighted modern translations — `use: reference_only`, NOT quoted

Consulted only as background for interpretation; **no text from any of these was copied into
`references/` or into `key_passages.md`.**

| Work | Note |
|---|---|
| Edward Slingerland, *Analects: With Selections from Traditional Commentaries* (2003) | Commentary integrated with translation |
| D. C. Lau, *The Analects* (1979); *Mencius* (1970) | Standard modern philological baseline |
| Annping Chin, *The Analects* (2014) | Historical and contextual notes |
| Roger Ames & Henry Rosemont, *The Analects of Confucius* (1998) | Relational/process reading |
| E. Bruce Brooks & A. Taeko Brooks, *The Original Analects* (1998) | Textual-critical reconstruction; a contested hypothesis, not a settled result |
| Bryan W. Van Norden, *Mengzi: With Selections from Traditional Commentaries* (2008) | Strongest single Mengzi resource |
| Irene Bloom, *Mencius* (2009) | Alternative translation |
| Kwong-loi Shun, *Mencius and Early Chinese Thought* (1997) | Moral psychology, cultivation |
| David B. Wong, on moral extension and differentiated care | Analogical judgment, graded concern |

Legge's nineteenth-century diction ("superior man", "perfect virtue", "benevolence") is dated
and interpretively loaded. `key_passages.md` says so explicitly and instructs the generator to
treat it as a pointer to the idea rather than as the register to write in. This is the main
cost of restricting the corpus to public-domain material, and it is a real one.

---

## Reproducing the acquisition

```
# Analects, English (Legge)
curl -L https://www.gutenberg.org/cache/epub/3330/pg3330.txt   -o pg3330.txt
# Analects, Legge's bilingual edition (Chinese with 【第N章】 markers)
curl -L https://www.gutenberg.org/cache/epub/4094/pg4094.txt   -o pg4094.txt
# Mengzi, Chinese (chapter-numbered)
curl -L https://www.gutenberg.org/cache/epub/24178/pg24178.txt -o pg24178.txt
# Mengzi, English (Legge), 14 chapter pages
for i in 01 02 03 04 05 06 07 08 09 10 11 12 13 14; do
  curl -L -A "<descriptive UA with contact>" \
    "https://en.wikisource.org/w/api.php?action=parse&page=The%20Chinese%20Classics%2FVolume%202%2FThe%20Works%20of%20Mencius%2Fchapter$i&prop=wikitext&format=json" \
    -o c$i.json
  sleep 1
done
```

Alignment and cleaning were done with throwaway Python in the session scratchpad; the outputs
in `references/` are the artifacts of record. Both reference files carry a header stating their
source, translator, edition and id convention, so a file separated from this ledger is still
self-describing.
