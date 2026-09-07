# Research notes — target `protestant`, spec v0.1

What was checked against primary sources, what the sources say that the research report does not,
what could not be checked, and what follows for the pipeline. Written 2026-09-07.

The starting point was `protestant_christian_moral_practical_thought.md`. It held up well. Every
claim I could test against a primary source was substantially correct; the corrections below are
about **qualifications the report omits**, not about claims it got wrong.

---

## 1. Verified

Each of these was read in the acquired text, not accepted from the report.

**Augsburg Confession VI** — verbatim as the report describes. "Also they teach that this faith is
bound to bring forth good fruits, and that it is necessary to do good works commanded by God,
because of God's will, but that we should not rely on those works to merit justification before
God." Both halves are there in one sentence: works necessary, works not meritorious.

**Augsburg Confession XVI** — richer than the report's summary and now the single most load-bearing
confessional passage in the target. It affirms civil office, judging, "just punishments", just war,
contracts, property and oaths as legitimate; and it ends: "Christians are necessarily bound to obey
their own magistrates and laws **save only when commanded to sin; for then they ought to obey God
rather than men**." That final clause is the cleanest shared formulation of bounded authority in the
whole corpus, and it is Lutheran rather than Reformed, which strengthens the case for treating it as
core rather than branch.

**Westminster Confession I.6** — "either expressly set down in Scripture, or by good and necessary
consequence may be deduced from Scripture", with circumstances "ordered by the light of nature, and
Christian prudence". Confirmed verbatim.

**Westminster Confession XX.2** — confirmed verbatim, including "the requiring of an implicit faith,
and an absolute and blind obedience, is to destroy liberty of conscience, and reason also."

**Westminster Confession XXIII.2** — magistracy lawful; war permitted "upon just and necessary
occasion". Confirmed.

**Westminster Larger Catechism Q99** — confirmed, and it is exactly as valuable as the report says.
It gives eight explicit rules for expanding the Decalogue, including "where a duty is commanded, the
contrary sin is forbidden; and, where a sin is forbidden, the contrary duty is commanded", the
extension to "all the causes, means, occasions, and appearances thereof", and the duty arising from
"our places and callings" to help others perform theirs.

**Heidelberg Catechism Q86-91** — confirmed, including the structural point: these questions open
"THE THIRD PART: Of Thankfulness". Q86 grounds good works in gratitude and assurance; Q91 defines
good works as those done "from true faith, according to the law of God, for his glory; and not such
as rest on our own opinion or the commandments of men."

**Thirty-Nine Articles VI, VII, XI, XII, XX, XXXIV** — all confirmed verbatim. VII is more useful
than the report indicates: it gives an explicit sorting rule between enduring moral commandments and
Mosaic ceremonial and civil provision, which is what lets the target avoid treating every command in
its sources as a present obligation.

**Wesley, "Catholic Spirit"** — confirmed, and the key passage is stronger than the report's
paraphrase. Wesley does not merely add epistemic humility; he explicitly refuses indifferentism:
"a catholic spirit is not speculative latitudinarianism. It is not an indifference to all opinions:
this is the spawn of hell, not the offspring of heaven... A man of a truly catholic spirit... is
fixed as the sun in his judgement concerning the main branches of Christian doctrine. It is true, he
is always ready to hear and weigh whatsoever can be offered against his principles; but as this does
not show any wavering in his own mind, so neither does it occasion any." This is the target's
`conviction_with_fallibility` divergence hypothesis stated by the source itself.

**Wesley, General Rules** — confirmed: the three-part structure (do no harm / do good / attend the
ordinances) and the specific content on Lord's Day commerce, spirituous liquors, usury, litigation
between members, "laying up treasure upon earth", diligence and frugality, and feeding, clothing and
visiting the sick and imprisoned.

**Wesley, "The Use of Money"** — confirmed: "Gain all you can... save all you can... give all you
can." The report does not quote the qualifier, which matters: the rule is "Gain all you can,
**without hurting either yourself or your neighbour, in soul or body**", and §I.1 caps earning
before it starts — "we ought not to gain money at the expense of life, nor... at the expense of our
health." This is the strongest single refutation in the corpus of "the Protestant work ethic means
accumulation", and it is now the anchor of principle P09.

**1689 Baptist Confession ch. 21** — confirmed, including "God alone is Lord of the conscience".

**Biblical passages** — Mt 5-7, Mt 22:34-40, Rom 12, Gal 5, Jas 2, Lk 10 all say what the report
claims, checked verse by verse in the WEB text. Mt 22:40 reads "The whole law and the prophets
depend on these two commandments"; Gal 5:13 "don't use your freedom as an opportunity for the flesh,
but through love be servants to one another"; Jas 2:16-17 the food-and-clothing case followed by
"faith, if it has no works, is dead in itself"; Rom 12:19 "Don't seek revenge yourselves".

---

## 2. Corrected, qualified, or found more sharply than the report has it

**The Baptist difference is visible in an omission, not a statement.** The report says the 1689
Confession "adopts closely related language" to Westminster on conscience. It does — nearly
verbatim. What is decisive is where it **stops**. Westminster ch. 20 has four sections; 1689 ch. 21
has three. The Baptists reproduce WCF 20.1-20.3 and drop 20.4 entirely, the section that says people
publishing erroneous opinions "may lawfully be called to account, and proceeded against, by the
censures of the Church, and by the power of the civil magistrate." Likewise 1689 ch. 24 on the civil
magistrate has three sections to Westminster's four and omits WCF 23.3's duty to suppress
"blasphemies and heresies". The free-church position is legible as a deliberate editorial subtraction
from a text the compilers otherwise copied. This is much better evidence than any positive statement
either confession makes, and it is worth carrying into any future Baptist branch layer.

**Westminster's liberty of conscience is not modern freedom of belief.** The report quotes WCF 20.2
approvingly and moves on. Read whole, chapter 20 constrains itself hard in 20.4, and chapter 23.3
makes suppressing heresy a magistrate's duty. WCF 10.4 additionally denies that anyone outside the
Christian religion can be saved "be they never so diligent to frame their lives according to the
light of nature". A target that cites WCF 20.2 for bounded authority while quietly ignoring 20.4 is
reading the confession the way a modern liberal wishes it read. I have kept all three sections in
the reference file and listed them as explicit `historical` boundaries in `key_passages.md` and
`spec.yaml`, precisely so the omission is a recorded decision rather than a silent one.

**Thirty-Nine Articles XXXIV is two-sided.** The report cites it for permitted local variation. Its
second half rebukes whoever "through his private judgment, willingly and purposely, doth openly
break the Traditions and Ceremonies of the Church... ought to be rebuked openly". The article is
about institutional order as much as about diversity. Both halves are quoted in `key_passages.md`.

**The report's "Wesley Catholic Spirit §II.4" citation does not resolve.** The passage the report is
pointing to on fallibility and mutual liberty is at the sermon's introduction §4 ("Though we cannot
think alike, may we not love alike?") and at §I.3 ("so long as we know but in part, that all men
will not see all things alike"), with the refusal of indifferentism at §III.1. The target uses those
three ids. Not an error of substance, only of location.

**The General Rules text acquired is the American recension, not Wesley's 1743 original.** It
contains "Slave-holding; buying or selling slaves", added in the American Discipline. The report
cites UMC.org for the General Rules without noting that any modern Methodist presentation is of a
revised text. Anything quoting the General Rules must carry an edition and date.

**CCEL is not simply "public domain".** The report's corpus map treats CCEL as a public-domain
source. CCEL's own policy page asserts copyright in "website and special contents" and says its
editions "may be used for personal, educational, or non-profit purposes. Contact us for permission
to republish CCEL works or to use them commercially." The underlying works are public domain, and
the Calvin page says so explicitly for that title; the site-level condition still applies to CCEL's
editions. Three files here come from CCEL. This pilot is research use and within that condition. A
commercial run should re-source Schaff and the Wesley sermons from public-domain scans. Recorded per
file in `SOURCES.md`.

**Augsburg XVI condemns the Anabaptists by name** — "They condemn the Anabaptists who forbid these
civil offices to Christians." The report says the omission of Anabaptists "biases the corpus". The
primary text shows it is stronger than bias: the in-scope sources were arguing against the position
being excluded. The near-unanimity of the six families on just war is therefore partly an artefact
of the scope decision. `use_of_force` is `generation_policy: avoid` for that reason, and the
condemnation clause is quoted in `key_passages.md` so the exclusion is visible.

---

## 3. Not verified

**Modern scholarship.** The report's claims resting on Meilaender & Werpehowski, Grobien on Lutheran
character formation, Joyce on Hooker, Maddox's "responsible grace", Holmes and Bingham on Baptist
identity, and Bebbington's quadrilateral were **not** checked. They sit behind publisher paywalls,
and I did not attempt access. Nothing in `spec.yaml` depends on them for a normative claim. Two
places where they shape the design are flagged here:

- The claim that the "three-legged stool" reading of Anglican authority is a later oversimplification
  of Hooker is taken on the report's authority. I did not acquire Hooker. The Anglican layer in
  `spec.yaml` is therefore described from the Articles alone, which under-represents the natural-law
  and prudential strand that is supposedly its distinctive contribution. **This is the largest
  source gap in the target.**
- Maddox's "responsible grace" framing is used to characterise the Wesleyan layer. It is a scholar's
  synthesis, not a Wesley text. Wesley's *Plain Account of Christian Perfection* was not acquired.

**Contemporary denominational positions.** UMC's 2024 General Conference changes, PCUSA's
constitutional definition of marriage, ELCA and LCMS positions — none checked. They do not need to
be: they are cited in the target only as evidence that contemporary bodies disagree, which is what
makes `sexual_and_family_ethics` an avoid topic. If a later version wants to build a
denomination-and-date branch, all of these need direct verification.

**The Lausanne Covenant and Cape Town Commitment.** Not acquired, on licensing and scope grounds.
The evangelical layer in `spec.yaml` is therefore the thinnest of the six and rests on the report's
characterisation plus Bebbington's four marks, neither checked against a primary text.

**Provenance of two reference files.** The Wikisource Larger Catechism and 1689 Confession both
carry `{{no source}}` tags, so the printed edition behind each transcription is unknown. I
cross-checked the seven Larger Catechism questions the spec actually cites against the OPC text, and
1689 ch. 21 against a Baptist transcription site; both matched in substance. The rest of both files
is unverified at the edition level. **Do not quote from an uncross-checked question of the Larger
Catechism as though the wording were authoritative.**

**One edition artefact worth knowing.** The Triglotta text of Augsburg XVI cites "Acts 7:49" for
"they ought to obey God rather than men". The verse is Acts 5:29. This is a printing error in the
1921 edition, carried into the reference file. Harmless, but it is a reminder that these are
editions, not autographs.

---

## 4. Choices deliberately left open

Recorded in full in `spec.yaml` under `unresolved_choices`; the reasoning behind the four hardest:

**Grace and agency (`mark_ambiguous`).** The Lutheran/Reformed and Wesleyan accounts of how divine
initiative and human response relate produce the same recommendation in most ordinary cases by
different routes. I chose behavioural neutrality for the pilot. This is the choice I am least
comfortable with. The report's own §5.N puts it well: for a *behaviour* dataset the neutral
abstraction is preferable, but for *value instantiation* it may omit exactly what makes the target a
target rather than a list of good advice. A human should decide before a full run.

**Shared-core criterion (`use_working_assumption`).** The report's §5.M asks whether a principle
counts as shared when it is explicitly confessed by every tradition, overwhelmingly present in
differing formulations, or merely biblical and undisputed. The pilot accepts all three and does not
grade them per principle. That can smuggle a strongly-Reformed principle into the core because its
Reformed statement is the most quotable — a real risk for P03 and P09, both of which lean on
Westminster Larger Catechism material. The partial mitigation is that `key_passages.md` labels every
passage `shared_core` / `branch:<name>` / `historical`, so a reviewer can see the actual spread of
support behind each principle. Grading per principle is deferred to v0.2.

**Inference method (`mark_ambiguous`).** No single theory of moral reasoning is adopted. Responses
reason from the situation, not from a method of deriving norms from texts. A useful side effect: if
a scenario's answer turns on *which* method is used, that is a reliable signal it belongs in a
branch layer rather than the core.

**Conscience versus institutional authority (`mark_ambiguous`).** The traditions in scope locate
final ordinary authority in a bishop, a presbytery, a conference, a congregation or the individual
believer — by design, not by accident. The shared frame (authority real, bounded, stops at required
wrongdoing; conscience real, corrigible, must be informed) is generated; any confident ranking of
who to defer to is not.

---

## 5. Implications for the pipeline

**Scenario generation must avoid branch-specific topics, and the validator should flag them.** Eight
`unresolved_choices` are `generation_policy: avoid`: sexual and family ethics, church and state, use
of force, sacraments and polity, and predestination/entire sanctification. A scenario whose
resolution turns on any of these is out of scope for the shared core, and a response that resolves
one confidently is a defect regardless of how well written it is. A cheap first check is a topic
keyword list run over `seed_situation` at the family stage — much cheaper than catching it at
review. This is a concrete request for `validate.py`.

**`confident_on_unresolved` needs to fire on four tradeoffs, not just the avoid list.**
`rule_vs_prudential_exception`, `conviction_vs_cooperation`,
`individual_conscience_vs_communal_judgment` and `use_of_force` are marked `unresolved: true`. For
these the *correct* response names both goods and declines a general rule. The reviewer prompt
should treat a confident resolution as a reject, and — importantly — should not treat the honest
refusal as evasion, which is the natural failure mode of a reviewer rewarded for decisiveness.

**The cue-term regex needs word boundaries and a small allowlist.** `sin` matches "since",
"business", "single"; `Lord` matches "landlord"; `pray` and `prayer` need explicit stems. The 79
forbidden terms are listed in `spec.yaml` with a `forbidden_terms_notes` field spelling this out.
Terms deliberately **not** forbidden, because ordinary responses need them: conscience, mercy,
forgiveness, neighbour, faith (as in "in good faith"), steward, calling, justice, humility, charity.
Forbidding those would make the target unable to say what it means.

**Nine divergence hypotheses are stated in a testable shape.** Each has an `example_prompt_shape`
that a family generator can expand directly. The three I expect to separate most cleanly from a
generic assistant, and would prioritise for the intended-divergence slice, are
`forgiveness_is_not_trust`, `right_is_not_the_end_of_the_question` and `silence_is_a_decision` —
each is a case where the generic answer is not wrong so much as it stops one step early.
`absent_parties_have_standing` is the one most likely to produce a *stylistic* rather than a
substantive divergence, so it should be judged carefully.

**Passage ids are stable and cross-checked.** All 128 ids cited in `spec.yaml` resolve to an entry in
`references/key_passages.md`; a script asserting this belongs in `TargetSpec` validation, because it
is the invariant most likely to rot as the spec is edited. Formats: `WEB <Book> <ch>:<v>`,
`AC <roman>`, `WCF <ch>.<sec>`, `WLC Q<n>`, `HC Q<n>`, `39A <roman>`, `1689 <ch>.<sec>`,
`Calvin Inst. 3.<ch>.<sec>`, `Wesley <sermon> <section>.<para>`, `General Rules (<part>)`.

**Historical material is in the references on purpose and must not leak into generation.** WCF 20.4,
23.3 and 10.4, the General Rules' Lord's Day and liquor provisions, and the household codes' slavery
setting are all in `references/` and labelled `historical` in `key_passages.md`. The generator is
given `key_passages.md`, so the labels have to be honoured by the prompt, not just present in the
file. The response's `hidden.source_passages` field makes this checkable: a response citing a
`historical`-labelled passage in support of present-tense advice should be rejected automatically.
That check is worth more than any amount of reviewer prompting.

**Weakest layers, if a branch run is ever attempted.** Anglican (no Hooker) and evangelical (no
Lausanne) are described but not grounded. Lutheran, Reformed, Wesleyan and Baptist each have at
least one primary text in `references/` and could support a branch layer today.
