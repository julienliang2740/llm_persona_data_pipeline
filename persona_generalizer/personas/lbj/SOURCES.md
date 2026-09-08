# SOURCES — Lyndon Baines Johnson

Acquired 8 September 2026 by following `.claude/skills/draft-persona/SKILL.md` phase 1,
coverage-driven: searches were aimed at the spec's required slots rather than at the subject's
name. This pass reached **tiers 1 and 2** for words and deeds, which the previous draft did not.
Circumstance and testimony remain tier 3–4 and are the weaker half of the file.

`robots.txt` was checked for every site before retrieval. Four declined automated AI use or
disallowed general crawling; nothing was taken from them and public-domain equivalents were used
instead. That substitution is the single most consequential fact in this ledger and is recorded in
full below.

## Ingested — used to write `references/key_passages.md`

| slot | source | edition / access | licence & AI use | evidence | interestedness |
|---|---|---|---|---|---|
| words (W1–W34) | Presidential speech transcripts, 14 addresses 1963-11-27 → 1968-04-11 | millercenter.org/the-presidency/presidential-speeches/`<slug>`, accessed 2026-09-08 | Underlying texts are US federal government works, not subject to copyright. Host `robots.txt` declares no AI-use restriction and disallows only `/admin/`, `/search/`, `/core/`, `/profiles/`. | tier 1, self-authored/delivered | The host is a scholarly centre presenting a president's public record; the texts themselves are the subject's own advocacy and are interested throughout. |
| deeds (D1–D11) | Roll call records, 75th–86th Congresses, member ICPSR 4979 | voteview.com static data: `rollcalls/{H075..H080,S081..S086}_rollcalls.csv` and matching `votes/*.csv`, accessed 2026-09-08 | Derived from official congressional roll calls (public records). Site serves no `robots.txt` (HTTP 404), so no restriction is declared. | tier 2, institutional record | Compiled by an academic project (Poole–Rosenthal lineage) for quantitative research; the vote codes are neutral, the *descriptions* are the compilers' and were read as such. |
| deeds (D13–D16), circumstance (C7, C8, C22) | Press and legal commentary on the 1948 election and the KTBC licence sequence | Retrieved via search result summaries only, 2026-09-08 | Copyrighted secondary work; paraphrased, not reproduced. | tier 4 | Mixed: contemporary press hostile in framing, legal commentary sceptical, popular retrospectives written to be striking. |
| circumstance (C4, C5, C6, C11, C12) | Reference works on the Southern Caucus, Rule XXII, the seniority system, and *Smith v. Allwright* | Retrieved via search result summaries only, 2026-09-08 | Copyrighted secondary work; paraphrased. | tier 4 | Institutional and encyclopaedic; low interest in the subject specifically. |
| testimony (T1, T2) | Evans and Novak's description of "the Treatment"; Humphrey's account | Retrieved via search result summaries only, 2026-09-08 | Copyrighted; paraphrased, not quoted at length. | tier 3, contemporary testimony | Evans and Novak were building a portrait and the passage is famous partly because it is vivid. Humphrey was an ally with no motive to make him monstrous — which is why it is worth having. |

**Processing applied to the speech texts.** Fetched with `curl`, content extracted from the
`presidential-speeches--body` container with a local Python script, whitespace normalised, saved as
plain text. No text was reproduced at length in `key_passages.md`; entries are original prose
summarising or closely paraphrasing what the speech says, with distinctive phrases quoted only in
fragments.

**Processing applied to the roll calls.** Roll call metadata and member vote files were joined on
`rollnumber` for ICPSR 4979 and filtered by a keyword pattern over `vote_desc`/`dtl_desc`
(`lynch|poll tax|civil right|cloture|fair employment|fepc|discriminat|segregat`). This produced 92
roll calls on which he is recorded. Cast codes were mapped with the standard scheme (1 Yea, 2
Paired Yea, 3 Announced Yea, 4 Announced Nay, 5 Paired Nay, 6 Nay, 7/8 Present, 9 Not Voting).

## Checked and NOT used — AI-use and crawl refusals honoured

| site | what it holds | what `robots.txt` says | what was used instead |
|---|---|---|---|
| `www.presidency.ucsb.edu` (American Presidency Project) | The complete *Public Papers of the Presidents* | `User-agent: ClaudeBot` → `Disallow: /`, in an explicit "Proactive Block for Major AI/LLM Scrapers" section | Nothing taken. Speech texts obtained from millercenter.org instead. |
| `www.discoverlbj.org` (LBJ Presidential Library digital archive) | His papers, and the telephone recordings and transcripts | `Content-Signal: ai-train=no, use=reference` **and** `User-agent: ClaudeBot` → `Disallow: /` | Nothing taken. This is the reason T10 is recorded as a gap rather than as evidence, and it is the largest single hole in this draft. |
| `texashistory.unt.edu` (Portal to Texas History) | Texas newspapers and local records — the natural source for C8 and D13 | `User-agent: ClaudeBot` → `Disallow: /` | Nothing taken. C8 and D13 rest on secondary accounts instead and are weaker for it. |
| `catalog.archives.gov` (National Archives catalog) | Federal records | `User-agent: *` → `Disallow: /` | Nothing taken. |
| `history.house.gov` | House historical record | `User-agent: *` → `Disallow: /` (named search engines only) | Nothing taken. Voteview used for House roll calls. |
| `www.govtrack.us` | Historical roll calls | Group listing `anthropic-ai`, `Claude-Web`, `ClaudeBot`, `GPTBot`, `CCBot` → `Disallow: /` | Nothing taken. Voteview used instead. |
| `archive.org` — *Public Papers* scans | Nine candidate volumes of the *Public Papers* | Site permits crawling, but every candidate item is `access-restricted-item: true` in the `inlibrary` controlled-lending collection and the full-text endpoint returns **HTTP 401** | Nothing taken; the restriction was not circumvented. Speech texts obtained from millercenter.org instead. |
| `www.senate.gov` | Senate historical office material | `robots.txt` itself returns **HTTP 403** via the site's CDN, so permission could not be established | Declined as a precaution. Nothing retrieved. |
| `www.loc.gov`, `quod.lib.umich.edu` | Library of Congress; Michigan digital texts | `robots.txt` unreadable behind a Cloudflare interstitial | Declined as a precaution. Nothing retrieved. |

Also discarded: `grokipedia.com` pages appeared in search results for the 1948 election and the
station and were **not used** — generated tertiary content with no attestable provenance, which is
exactly what the deduplicate-by-claim rule exists to exclude. Wikipedia was used only to orient,
never as the sole basis for a passage.

## Deduplication by claim

The "we have lost the South for a generation" quotation appeared across many pages and traces to no
contemporaneous source. Many URLs, one weak origin: it is recorded in
`subject.canon_boundary.disputed` and cited by nothing.

The KTBC sequence likewise appears in many places deriving from a small number of accounts. It is
stated in D14–D16 as a *sequence of dated events* rather than as an inference about motive,
because the sequence is what the sources agree on.

## What a sound version of this ledger still needs

| tier | source | why it matters |
|---|---|---|
| 1 | The White House telephone recordings, 1963–69 | Him deciding out loud. Would settle the unresolved tradeoff. Blocked by the archive's AI-use refusal; needs a human researcher. |
| 1 | *Congressional Record*, 1937–1961 (govinfo CRECB permits crawling and holds bound volumes back to this period) | The debate around the roll calls, which this pass has without the words spoken beside them. |
| 2 | FCC dockets on KTBC, 1943–45 | Would convert D15 from a reported sequence into a documented one. |
| 2 | Jim Wells County tally sheets and the 1948 litigation record | Same, for D13. |
| 3 | Caro, *The Years of Lyndon Johnson*; Dallek, *Lone Star Rising* / *Flawed Giant* | The standard scholarship, still absent. Circumstance and testimony would be rewritten against it. |
| 3 | Oral histories from the presidential library | Testimony at length with interests visible; T6 and T9 are currently thin. |

## Reproducing the acquisition

```bash
# 1. Refusal check (run first, for every host)
curl -s https://<host>/robots.txt

# 2. Speech texts — 14 slugs from the site's sitemap, filtered to 1963-11 .. 1969-01
curl -s https://millercenter.org/sitemap.xml \
  | grep -oE "presidential-speeches/[a-z0-9-]+" | sort -u
curl -s -o sp_<slug>.html \
  "https://millercenter.org/the-presidency/presidential-speeches/<slug>"
# extract the presidential-speeches--body container, strip tags, normalise whitespace

# 3. Roll calls — LBJ is ICPSR 4979
curl -s -o HSall_members.csv https://voteview.com/static/data/out/members/HSall_members.csv
for c in H075 H076 H077 H078 H079 H080 S081 S082 S083 S084 S085 S086; do
  curl -s -O "https://voteview.com/static/data/out/rollcalls/${c}_rollcalls.csv"
  curl -s -O "https://voteview.com/static/data/out/votes/${c}_votes.csv"
done
# join on rollnumber where icpsr == 4979; filter vote_desc/dtl_desc on the civil rights pattern
```

Search-result summaries are not stable over time, so the tier-3/4 rows above will not reproduce
exactly. The tier-1 and tier-2 rows will.
