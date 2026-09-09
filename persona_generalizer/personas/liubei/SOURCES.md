# SOURCES — Liu Bei 劉備 (161–223)

Acquired 8 September 2026 by following `.claude/skills/draft-persona/SKILL.md`. Unlike the LBJ
draft, **the primary source was reached directly and read in the original language**: the
*Sanguozhi* biography with Pei Songzhi's annotations, in Chinese, from a host that permits it.
That is the strength of this draft. Its weakness is the other half — circumstance rests on
general period reference material rather than on scholarship about this subject.

`robots.txt` was checked before every retrieval.

## Ingested — used to write `references/key_passages.md`

| slot | source | edition / access | licence & AI use | evidence | interestedness |
|---|---|---|---|---|---|
| words (W1–W18), deeds (D1–D28) | 《三國志》卷32 蜀書二 先主傳, with Pei Songzhi 裴松之 annotations | `zh.wikisource.org/wiki/三國志/卷32`, accessed 2026-09-08 | Text is 3rd/5th century, long in the public domain. Transcription CC BY-SA. Wikimedia `robots.txt` disallows `/w/` and `/api/`; the `/wiki/` article path used here is permitted. | tier 1 (the documents it quotes) and tier 4 (Chen Shou's narrative) | Chen Shou was born in Shu and wrote under Jin, successor to Wei — close to his subject and writing for a regime with reason to prefer the Wei succession. Pei Songzhi quotes hostile and friendly sources alike. |
| testimony (T7, T8), the entrusting (W5) | 《三國志》卷35 蜀書五 諸葛亮傳, with annotations | `zh.wikisource.org/wiki/三國志/卷35`, accessed 2026-09-08 | as above | tier 1 for the speech; tier 3–4 for the commentary | Contains Sun Sheng's 孫盛 hostile attack on the entrusting, preserved inside the source — the most useful single piece of adversarial testimony in this file. |
| circumstance (C1, C2, C7, C11) | Reference material on the late Han collapse, the 189–220 transition and the provincial-governor reform | search result summaries, 2026-09-08 | copyrighted secondary work; paraphrased | tier 4 | Encyclopaedic; low interest in this subject specifically. |
| circumstance (C18, C19, C20, C21) | Reference material on Chen Shou, Pei Songzhi's commission and method, and the absence of a Shu court history | search result summaries, 2026-09-08 | copyrighted secondary work; paraphrased | tier 4 | Historiographical scholarship; its interest is in the text rather than the man, which is what makes it usable here. |

**Processing applied to the primary text.** Fetched with `curl`, content extracted from the
`mw-parser-output` container up to `printfooter` by a local Python script, tags stripped,
inter-character spacing removed (classical Chinese has no word spaces), saved as UTF-8 text.
Passages were then written in English from readings of that text. **No classical Chinese was
machine-translated wholesale**; each cited passage was located in the Chinese and rendered by
hand, which is also why the corpus is 93 entries rather than 200.

## Checked and NOT used

| site | what it holds | what was found | what was used instead |
|---|---|---|---|
| `ctext.org` (Chinese Text Project) | The standard online *Sanguozhi*, with parallel translations and a concordance | Its `robots.txt` **has changed** since the precedent recorded in `targets/confucian/SOURCES.md`. It now names `GPTBot`, `ChatGPT-User` and `Amazonbot` with `Disallow: /`, and its `User-agent: *` group blocks only `/admin` and `/hp.pl`. **No Claude agent is named.** | **Declined anyway.** The site's evident intent is to refuse AI crawlers, the absence of a Claude rule reads as omission rather than permission, and this repository's own precedent is to decline it. Wikisource used instead. Recorded in full because the changed file is itself worth knowing. |
| `kanripo.org` (Kanseki Repository) | Critical editions of the Chinese classical corpus | `Content-Signal: search=yes, ai-train=no, use=reference` | **Declined.** `ai-train=no` is directly on point: the export of this pipeline is training data. |
| `zhonghuadiancang.com` | Popular Chinese classical text portal | no `robots.txt` served | Not needed once Wikisource supplied the text; unverified provenance in any case. |
| Chinese-language secondary scholarship | Modern historiography on Liu Bei and Shu Han | not searched | **This is the largest gap in the draft** and is recorded as such rather than glossed over. |

Also discarded: fan-wiki and game-derived pages appeared throughout search results for every
query naming this subject, and were not used. They are downstream of the novel, which is the
exact contamination `subject.canon_boundary.excluded` exists to prevent.

## Deduplicate by claim

Nearly every English-language claim about this subject traces to one of two places: the
*Sanguozhi* (usable) or the fourteenth-century novel (excluded). Where a search result asserted
something colourful, the test applied was whether it appears in the juan 32 text actually
retrieved. Several widely repeated items do not, and are absent from the corpus — the peach
garden oath most prominently, corrected in C23.

## What a sound version of this ledger still needs

| tier | source | why it matters |
|---|---|---|
| 1 | A critical edition of the *Sanguozhi* (Zhonghua shuju punctuated text) | Wikisource is a transcription without apparatus; variants and punctuation choices are invisible here. |
| 3 | Chinese-language scholarship on Shu Han and on Chen Shou's Shu sources | The single largest gap. Every circumstance entry would be rewritten against it. |
| 3 | Rafe de Crespigny's biographical dictionary and studies of the period | The standard English-language apparatus, not consulted. |
| 2 | The *Huayang guozhi* 華陽國志 | A regional history of the southwest with independent material on the Yi province administration he inherited. |

## Reproducing the acquisition

```bash
# 1. Refusal check first, for every host
curl -s https://ctext.org/robots.txt
curl -s https://zh.wikisource.org/robots.txt

# 2. The primary text (URL-encode the Chinese title)
python3 -c "import urllib.parse;print(urllib.parse.quote('三國志/卷32'))"
curl -s -o juan32.html "https://zh.wikisource.org/wiki/%E4%B8%89%E5%9C%8B%E5%BF%97/%E5%8D%B732"
# extract from mw-parser-output to printfooter, strip tags, remove inter-character spaces

# 3. Locate the decisive passages in the Chinese
grep -o '夫濟大事必以人為本' juan32.txt     # Changban
grep -o '勿以惡小而為之' juan32.txt         # testamentary edict
grep -o '君可自取' juan35.txt               # the entrusting
```

Search-result summaries are not stable over time, so the circumstance rows will not reproduce
exactly. The primary-text rows will.
