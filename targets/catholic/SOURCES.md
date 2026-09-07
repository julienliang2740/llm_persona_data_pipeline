# Sources — `catholic` target

Provenance for everything in `references/`, plus every source consulted and deliberately **not**
ingested. All access dates are **7 September 2026**.

Two rules were applied throughout:

1. **Nothing was copied whose terms do not permit it.** Vatican texts are free to read online but
   the Vatican Publishing House asserts worldwide rights over papal magisterial acts, and the
   Catechism carries a Libreria Editrice Vaticana copyright notice. None of these were ingested.
   The specific paragraphs the specification depends on are quoted at **quotation scale** inside
   `references/key_passages.md`, with citation, pending rights review.
2. **No access control was bypassed.** Everything was retrieved from public URLs. The NABRE and
   modern academic monographs were not acquired at all.

---

## 1. Files in `references/`

### `scripture_moral_passages.txt` — 6,397 words

| | |
|---|---|
| Work | The Bible, Douay-Rheims, Complete |
| Translation | Douay-Rheims, Richard Challoner revision |
| Edition | Project Gutenberg ebook #1581 |
| URL | https://www.gutenberg.org/ebooks/1581 (text: `/cache/epub/1581/pg1581.txt`) |
| Accessed | 2026-09-07 |
| License | Public domain in the United States. Project Gutenberg License applies to the PG packaging; the PG header/footer were removed, so the packaging terms do not travel with this extract. |
| AI-use restrictions | None asserted. Project Gutenberg advises non-US users to check local law; this has not been assessed for any jurisdiction outside the United States. |
| Processing | Eleven passages extracted by book/chapter/verse (Ex 20; Mt 5, 6, 7, 22:34-40, 25:31-46; Lk 10:25-37; Rom 2:12-16, Rom 12; Jas 2; 1 Cor 13). Chapter summaries and Challoner's explanatory notes that fall inside a chapter were retained. Wording unaltered. PG front and back matter removed. |
| Authority label | R |

### `aquinas_excerpts.md` — 3,052 words

| | |
|---|---|
| Work | Summa Theologica (Summa Theologiae) |
| Author | Thomas Aquinas |
| Translation | Fathers of the English Dominican Province |
| Edition | Benziger Bros., 1911-1925; Project Gutenberg ebooks #17897 (Part I-II) and #18755 (Part II-II) |
| URL | https://www.gutenberg.org/ebooks/17897 , https://www.gutenberg.org/ebooks/18755 |
| Accessed | 2026-09-07 |
| License | Public domain in the United States. PG header/footer removed. |
| AI-use restrictions | None asserted. |
| Processing | Ten articles extracted (I-II q.18 aa.2, 4, 6; q.94 aa.2, 4, 6; II-II q.47 aa.2, 6, 8; q.64 a.7). Only the *respondeo* ("I answer that") of each article is reproduced, truncated at a sentence boundary where long; objections and replies omitted. Gutenberg underscore emphasis markers removed. Wording unaltered. |
| Authority label | T — theological interpretation, never presented as the tradition's official teaching |

### `augustine_excerpts.md` — 948 words

| | |
|---|---|
| Works | *On Christian Doctrine* I.27-28; *The City of God* XIX.13 |
| Author | Augustine of Hippo |
| Translations | J. F. Shaw (*On Christian Doctrine*); Marcus Dods (*City of God*) |
| Editions | *Nicene and Post-Nicene Fathers*, First Series vol. 2, ed. Philip Schaff (1887), via the Christian Classics Ethereal Library; *City of God, Volume II*, Project Gutenberg ebook #45305 |
| URLs | https://ccel.org/ccel/augustine/doctrine/doctrine.xxvii.html , https://ccel.org/ccel/augustine/doctrine/doctrine.xxviii.html , https://www.gutenberg.org/ebooks/45305 |
| Accessed | 2026-09-07 |
| License | Both underlying editions are out of copyright (1887; Dods translation likewise). CCEL supplies a presentation layer over a public-domain text; two short chapters (~350 words total) were taken, which is quotation scale regardless of how the presentation layer is characterised. |
| AI-use restrictions | None found on the pages retrieved. CCEL's site-wide terms were not separately reviewed — see *Open items* below. |
| Processing | Three chapters extracted; HTML stripped; text reflowed to single paragraphs. Wording unaltered. |
| Authority label | T |

### `key_passages.md` — 6,720 words, 78 passages

Derived file. It contains short quotations from the four works above **and** from the
reference-only Vatican sources in section 2, each with a citation and an authority label. Nothing
in it was written by a model from memory: every quotation was extracted programmatically from a
file downloaded on 2026-09-07 and listed in this ledger. Two passages (`DDC I.27`, `CDG XIX.13`)
were shortened by hand from the corresponding entries in `augustine_excerpts.md`.

Quotation lengths: 35-85 words per passage, averaging 56. Quoted material by source: Catechism
2,213 words across 40 separate paragraphs; Scripture 542; *Magnifica Humanitas* 327 across 7
passages; *Summa* 288; CDF 1998 203; *Veritatis Splendor* 181; Augustine 137; *Antiqua et nova*
129; *Evangelium Vitae* 101; Compendium 99; all others under 65. Total across all sources: 4,392
words. No single work contributes a continuous run of text.

---

## 2. Reference-only: consulted, cited, **not ingested**

Each of these was downloaded to a scratch directory for verification, and the specific cited
paragraphs quoted in `key_passages.md`. No full text was copied into `references/` and none should
be used for training on the strength of this ledger.

| Work | Locator | URL | License / terms | Processing |
|---|---|---|---|---|
| Catechism of the Catholic Church (English) | CCC \<paragraph\> | https://www.vatican.va/archive/ENG0015/_INDEX.HTM | "© Libreria Editrice Vaticana" on every page. Free to read; no reuse grant. | 374 IntraText pages fetched to scratch; paragraph index built; 40 paragraphs quoted, 2,213 words total |
| *Dei Verbum* (Vatican II, 1965) | DV §10 | https://www.vatican.va/archive/hist_councils/ii_vatican_council/documents/vat-ii_const_19651118_dei-verbum_en.html | Vatican site; no reuse grant | one section quoted |
| *Lumen Gentium* (Vatican II, 1964) | LG §25 | https://www.vatican.va/archive/hist_councils/ii_vatican_council/documents/vat-ii_const_19641121_lumen-gentium_en.html | Vatican site; no reuse grant | one section quoted |
| *Veritatis Splendor* (John Paul II, 1993) | VS §§79-83 | https://www.vatican.va/content/john-paul-ii/en/encyclicals/documents/hf_jp-ii_enc_06081993_veritatis-splendor.html | Papal magisterial act; LEV asserts worldwide economic rights | three sections quoted |
| *Evangelium Vitae* (John Paul II, 1995) | EV §§57, 65 | https://www.vatican.va/content/john-paul-ii/en/encyclicals/documents/hf_jp-ii_enc_25031995_evangelium-vitae.html | as above | two sentences quoted |
| CDF, *Doctrinal Commentary on the Concluding Formula of the Professio fidei* (1998) | CDF 1998 §§6, 10, 11 | https://www.vatican.va/roman_curia/congregations/cfaith/documents/rc_con_cfaith_doc_1998_professio-fidei_en.html | Vatican site; no reuse grant | four passages quoted |
| DDF, *Dignitas Infinita* (2024) | DI §1 | https://www.vatican.va/roman_curia/congregations/cfaith/documents/rc_ddf_doc_20240402_dignitas-infinita_en.html | Vatican site; no reuse grant | one sentence quoted |
| DDF & DCE, *Antiqua et nova* (28 Jan 2025) | AeN §§39, 74, 116 | https://www.vatican.va/roman_curia/congregations/cfaith/documents/rc_ddf_doc_20250128_antiqua-et-nova_en.html | Vatican site; no reuse grant | three sentences quoted |
| Leo XIV, *Magnifica Humanitas* (15 May 2026) | MH §§99, 102, 105, 198, 199, 200 | https://www.vatican.va/content/leo-xiv/en/encyclicals/documents/20260515-magnifica-humanitas.html | Papal magisterial act; LEV asserts worldwide economic rights | seven passages quoted |
| Pontifical Council for Justice and Peace, *Compendium of the Social Doctrine of the Church* (2004) | CSDC §§182, 186 | https://www.vatican.va/roman_curia/pontifical_councils/justpeace/documents/rc_pc_justpeace_doc_20060526_compendio-dott-soc_en.html | Vatican site; no reuse grant | two passages quoted |

**Basis for the Vatican rights position:** a 31 May 2005 decree of the Secretariat of State assigned
to the Libreria Editrice Vaticana, permanently and worldwide, the moral copyright and exclusive
economic rights over the acts and documents by which the Supreme Pontiff exercises his Magisterium
(https://press.vatican.va/roman_curia/secretariat_state/2005/documents/rc_seg-st_20050531_decreto-lev_en.html).
Reaffirmed in 2013. **Free online access is not a licence**; bulk ingestion of any Vatican text
requires permission or legal review.

---

## 3. Considered and **not acquired**

| Source | Why not |
|---|---|
| New American Bible Revised Edition (NABRE), USCCB | Copyright Confraternity of Christian Doctrine; USCCB permissions distinguish print excerpts from digital use and require a licence and fees for digital applications. Not downloaded. The Douay-Rheims was used instead, with the cost that its English is archaic and unrepresentative of contemporary Catholic phrasing. |
| Corpus Thomisticum (Latin) | Online availability does not establish reuse rights; not needed once the public-domain English Summa was available. |
| New Advent | Useful for lookup, but a presentation layer over public-domain editions; the underlying Gutenberg and CCEL editions were used directly instead. |
| *Acta Apostolicae Sedis* archive | Not needed; no provenance question in this pilot turned on the Latin original or promulgation record. |
| Pinckaers, *The Sources of Christian Ethics* | In copyright. `reference_only`. Not acquired, not quoted, grounds nothing. |
| Cessario, *Introduction to Moral Theology* | In copyright. `reference_only`. |
| Grisez, *The Way of the Lord Jesus* | Author-authorised text is online but copyright is retained. `reference_only`. |
| Finnis, *Aquinas: Moral, Political, and Legal Theory* | In copyright. `reference_only`. |
| Porter, *Nature as Reason* | In copyright. `reference_only`. |
| Keenan, *A History of Catholic Moral Theology in the Twentieth Century* | In copyright. `reference_only`. |

These six are listed in `spec.yaml` under `reference_material.modern_scholarship` so that the
record shows which theological schools exist (Thomistic virtue-renewal, new natural law, historical
and critical) and that no one of them has been silently treated as the tradition itself.

---

## 4. Open items for review

- **Vatican rights.** Any move beyond quotation scale — including putting Catechism paragraphs into
  a training corpus rather than into prompt context — needs permission or legal review first.
- **CCEL terms.** The two Augustine chapters are public-domain text; CCEL's own site terms were not
  separately reviewed. If that matters, the same Shaw translation is available in print scans of
  NPNF vol. 2 and could be re-sourced.
- **Jurisdiction.** "Public domain in the United States" is what Project Gutenberg asserts. Nothing
  here has been assessed for any other jurisdiction.
- **Scripture translation.** If the pilot ever needs contemporary Catholic biblical phrasing rather
  than archaic English, a NABRE licence would have to be obtained.
