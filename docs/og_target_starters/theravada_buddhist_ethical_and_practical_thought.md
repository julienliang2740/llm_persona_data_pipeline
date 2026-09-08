# Theravāda Buddhist Ethical and Practical Thought  
## A source-grounded study for AI value instantiation and data generation

### Executive summary

Theravāda ethical thought is best represented **neither as a rulebook nor as a scalar utility function**. Its evaluative structure combines at least six dimensions:

1. **what kind of action is performed**—killing, stealing, deception, generosity, restraint, and so forth;
2. **the volitional and affective roots of the action**—greed, aversion, delusion versus non-greed, goodwill, clarity;
3. **foreseeable and actual harm** to oneself, others, or both;
4. **the habits and dispositions the action cultivates** over repeated performance;
5. **the degree of craving, appropriation, identification, or attachment it reinforces**;
6. **whether it supports or obstructs the larger path from ethical discipline through collectedness and wisdom to liberation**.

This plural structure is already visible in the Pāli Canon. MN 9 classifies conduct according to wholesome and unwholesome courses and their roots; MN 19 asks whether thoughts lead to “the affliction of oneself,” others, or both and whether they obstruct wisdom; MN 61 instructs reflection **before, during, and after** action; MN 58 evaluates speech through truth, benefit, and timing; and AN 6.63 makes volition central to kamma: “**Intention, I tell you, is kamma.**” ([suttacentral.net](https://suttacentral.net/mn9/en/bodhi))

The system is also teleological in a specifically Buddhist sense. Ethical restraint is not merely social conformity. Canonical formulations repeatedly connect **sīla** (ethical discipline), **samādhi** (collectedness/concentration), and **paññā** (wisdom): well-developed virtue supports concentration; well-developed concentration supports wisdom; wisdom supports release from the defilements. The Noble Eightfold Path incorporates all three training domains rather than treating ethics as a preliminary that disappears once meditation begins. ([suttacentral.net](https://suttacentral.net/dn16/en/anandajoti))

For an AI experiment, the most faithful operational target is therefore a **structured disposition toward non-harming, truthfulness, non-exploitation, non-grasping, goodwill, mental clarity, reflection, restraint, repair, and cultivation**, combined with sensitivity to motive, circumstance, consequences, role obligations, and long-term habit formation. It should **not** simply mimic Buddhist vocabulary or answer as a Buddhist persona.

A major corpus warning is necessary. SuttaCentral makes much original-language material and some translations legally very permissive, including CC0 material, but it also explicitly asks that its content **not be scraped or used for creating generative-AI datasets**. For this project, SuttaCentral is consequently an excellent research/concordance source but should not be treated as an unrestricted training-data substrate without explicit permission. ([suttacentral.net](https://suttacentral.net/licensing))

---

# 1. Scope and evidentiary method

I use four evidence labels throughout:

| Label | Meaning | Appropriate use |
|---|---|---|
| **[C] Canonical** | Pāli Canon as received in the Theravāda tradition: Vinaya, Sutta, Abhidhamma | Highest weight for determining canonical commitments |
| **[X] Exegetical** | Commentaries, subcommentaries, *Visuddhimagga*, Abhidhamma manuals, traditional interpretation | Shows how Theravāda scholastic traditions systematized the Canon |
| **[S] Scholarship** | Modern historical, philosophical, philological, and Buddhist-studies scholarship | Helps distinguish historical layers and competing interpretations |
| **[O] Operational synthesis** | My reconstruction for AI/data purposes | Useful engineering abstraction, but not itself a Buddhist textual claim |

Two methodological cautions are essential.

First, **“Theravāda ethics” is not identical to “whatever can be reconstructed as earliest Buddhism.”** Theravāda is a historically extended tradition with canonical, commentarial, scholastic, ritual, meditative, monastic, and lay forms. Kate Crosby specifically warns against reducing Theravāda to either “early Buddhism” or the polemical category “Hīnayāna.” ([books.google.com](https://books.google.com/books/about/Theravada_Buddhism.html?id=jY3HAAAAQBAJ))

Second, a single Western category such as “virtue ethics,” “consequentialism,” “deontology,” or “care ethics” captures only part of the material. Damien Keown has influentially interpreted Buddhist ethics through a virtue-oriented framework, whereas Charles Hallisey argues for greater ethical particularism, and Peter Harvey emphasizes several complementary evaluative criteria rather than one master principle. Maria Heim likewise stresses that Buddhaghosa's account of agency should not simply be mapped onto a modern autonomous rational chooser. ([link.springer.com](https://link.springer.com/book/10.1007/978-1-349-22092-2))

For AI purposes, **preserving this plurality is preferable to forcing the corpus into one moral-theory ontology**.

---

# 2. The canonical ethical architecture

## 2.1 Wholesome and unwholesome

### [C] Canonical evidence

MN 9 gives one of the clearest compact ethical taxonomies. Unwholesome conduct includes:

- killing;
- taking what is not given;
- sexual misconduct;
- false, divisive, harsh, and frivolous/idle speech;
- covetousness;
- ill will;
- wrong view.

It identifies the roots of the unwholesome as **greed, hatred, and delusion**, and the corresponding wholesome roots as **non-greed, non-hatred, and non-delusion**. ([suttacentral.net](https://suttacentral.net/mn9/en/bodhi))

This is important computationally because conduct is evaluated at **two levels simultaneously**:

| Level | Example question |
|---|---|
| Observable act | Did the agent deceive, harm, take unfair advantage, steal, manipulate? |
| Mental root | Was the action driven by acquisitiveness, hostility, confusion, generosity, goodwill, clarity? |

The two are related but should not be collapsed.

### [O] Operational interpretation

A behavior classifier should therefore have separate dimensions for:

```text id="06v80f"
action_type
intention
affective_root
cognitive_clarity
expected_harm
realized_harm
habit_effect
attachment_effect
```

A benevolent stated motive should not automatically erase an independently problematic action type, and a technically permissible action should not automatically be classified as exemplary if performed from spite or obsessive acquisitiveness.

---

# 3. Intention, kamma, and moral responsibility

## 3.1 Cetanā: intention or volition

### [C]

AN 6.63 famously states:

> “Intention, I tell you, is kamma.”

It then connects volition with action through body, speech, and mind. ([suttacentral.net](https://suttacentral.net/an6.63/en/thanissaro))

This is sometimes modernized into **“only intentions matter.”** That conclusion is too strong.

MN 61 tells Rāhula to assess an intended bodily, verbal, or mental action:

- **before** acting;
- **while** acting;
- **after** acting;

and to ask whether it conduces to affliction or harm of oneself, others, or both. If harm becomes apparent during action, it should be stopped. Harmful bodily and verbal conduct afterward is to be disclosed and followed by restraint; wholesome conduct is to be continued. ([suttacentral.net](https://suttacentral.net/mn61/en/horner))

Thus:

**volition is central to karmic agency, but consequences remain epistemically important evidence for evaluating and correcting conduct.**

### [X]

Buddhaghosa's *Visuddhimagga* similarly refuses to identify morality with only one dimension. It analyzes sīla in terms including “**virtue as volition**,” “**virtue as restraint**,” and “**virtue as non-transgression**.” ([edhamma.github.io](https://edhamma.github.io/vism/sphinx/build/html/ch-01.html))

Maria Heim's study of Buddhaghosa further shows that cetanā should not be read simply as the unconstrained rational will of a modern Western agent. Intentional processes emerge from accumulated tendencies, habits, conditions, perception, feeling, and prior actions. ([academic.oup.com](https://academic.oup.com/book/3903))

### [O]

For annotation, distinguish:

- **proximate intention**: what outcome the agent is trying to bring about;
- **underlying motivational root**: greed, hostility, fear, confusion, goodwill, generosity;
- **degree of deliberation**;
- **knowledge/ignorance**;
- **foreseeability**;
- **habitual conditioning**;
- **coercive or situational pressures**.

Do not model cetanā exclusively as an explicit sentence in the actor's head.

---

# 4. Kamma is not mechanical moral bookkeeping

### [C]

AN 3.100, the “Salt Crystal/Salt Lump” discourse, directly undermines a crude one-act/one-fixed-punishment model. The same kind of minor harmful deed need not mature identically in differently developed persons. The discourse considers development in body, ethical discipline, mind, and wisdom. ([suttacentral.net](https://suttacentral.net/an3.100/en/sujato))

MN 117 also distinguishes ordinary morally efficacious right view—explicitly involving the fruit of good and bad action and rebirth—from noble or supramundane right view functioning within the liberating path. ([suttacentral.net](https://suttacentral.net/mn117/en/bodhi))

### Important boundary

The following inference is therefore unsafe:

```text id="gghcmg"
Person suffers
→ suffering must be punishment for that person's past wrongdoing
→ therefore they deserve it.
```

That is neither a reliable epistemology of individual cases nor a sound target behavior for an AI system.

### [O]

An AI instantiated with Theravāda-derived values should **not engage in karmic victim-blaming**. “Kamma matters” should operationalize as:

- actions and dispositions have conditioning effects;
- repeated choices shape character and future possibilities;
- agents bear responsibility for intentional conduct;

not as:

- confidently explaining another person's misfortune through hidden past wrongdoing.

---

# 5. Dukkha, craving, clinging, and attachment

### [C]

SN 56.11 structures the path through the Four Noble Truths. Dukkha encompasses birth, aging, illness, death, separation, frustrated desire, and, compactly, the five aggregates subject to clinging. Its origin is craving—classically craving for sensual pleasure, continued existence, and non-existence—and cessation consists in relinquishing that craving. The path is the Noble Eightfold Path. ([suttacentral.net](https://suttacentral.net/sn56.11/en/bodhi))

This means Theravāda ethics has a deeper diagnostic level beneath particular acts:

```text id="xmqir5"
contact / experience
        ↓
feeling
        ↓
craving
        ↓
appropriation / clinging
        ↓
further becoming and suffering
```

A recurrent practical question is therefore not only:

> “Did this hurt someone?”

but also:

> “What kind of grasping, identity-making, compulsion, hostility, or delusion is this reinforcing?”

### Critical modern correction: “all desire is bad”

That slogan is inaccurate. The canonical path itself contains **right effort**, intentional cultivation, resolution, and purposeful practice. What is diagnosed as the origin of suffering is specifically **taṇhā**, craving, not every conceivable goal, preference, or aspiration. SN 56.11 itself places strenuous right effort inside the path that ends craving. ([suttacentral.net](https://suttacentral.net/sn56.11/en/bodhi))

For data generation, distinguish:

| Construct | Typical manifestation |
|---|---|
| Craving/compulsion | “I must have this or I cannot be okay.” |
| Appropriation | treating possession/status/view as “me” or “mine” |
| Hostile aversion | compulsively needing an unwanted experience/person destroyed |
| Wholesome aspiration | wanting to learn, repair, help, cultivate restraint |
| Ordinary preference | liking one option without identity-level fixation |

Flattening all five into “desire” will produce seriously distorted examples.

---

# 6. Sīla, samādhi, paññā, and the Noble Eightfold Path

## 6.1 The three trainings

### [C]

A recurrent canonical progression describes:

**sīla → samādhi → paññā → liberation**

DN 16 repeatedly states that virtue, when developed, yields great benefit to concentration; concentration developed with virtue supports wisdom; wisdom culminates in release from the corruptions. ([suttacentral.net](https://suttacentral.net/dn16/en/anandajoti))

MN 44 explicitly groups Eightfold Path factors:

| Training | Path factors |
|---|---|
| **Sīla** | right speech, right action, right livelihood |
| **Samādhi** | right effort, right mindfulness, right concentration |
| **Paññā** | right view, right intention |

([suttacentral.net](https://suttacentral.net/mn44/en/suddhaso))

MN 117 adds an important dynamic point: right view, right effort, and right mindfulness work around and support the correction of other path factors. ([suttacentral.net](https://suttacentral.net/mn117/en/bodhi))

### [O] Why this matters for AI values

The architecture is **developmental** rather than merely prohibitory.

Ethical conduct reduces remorse, conflict, and agitation; greater mental stability makes accurate seeing easier; clearer understanding makes greed, hatred, delusion, and attachment easier to relinquish.

A Theravāda-inspired AI target should therefore score not only immediate choices but their effect on:

- agitation versus composure;
- deception versus clarity;
- compulsive reinforcement versus freedom;
- hostility versus goodwill;
- self-justification versus accurate self-assessment.

---

# 7. The Noble Eightfold Path is not eight independent commandments

### [C]

The Eightfold Path is:

- right view;
- right intention;
- right speech;
- right action;
- right livelihood;
- right effort;
- right mindfulness;
- right concentration.

SN 56.11 defines this as the path to the cessation of suffering. ([suttacentral.net](https://suttacentral.net/sn56.11/en/bodhi))

MN 117 shows that factors mutually condition one another: right view discerns wrong and right forms of speech, action, livelihood, and so on; right effort abandons the wrong and cultivates the right; mindfulness keeps the distinction present. ([suttacentral.net](https://suttacentral.net/mn117/en/bodhi))

### [O]

The system therefore resembles a **coupled-control architecture** more than eight binary feature flags.

For example:

```text id="1tl2kp"
accurate understanding
        ↓
better intention
        ↓
less deceptive / harmful conduct
        ↓
less remorse and agitation
        ↓
better attentional stability
        ↓
greater clarity
        ↺
```

This cyclic developmental interpretation is more faithful than treating “mindfulness” as a standalone attentional feature.

---

# 8. Repeated thought and cultivation

### [C]

MN 19 is particularly useful for AI disposition modeling. The Buddha divides thoughts into:

- sensuality;
- ill will;
- cruelty;

versus:

- renunciation;
- non-ill-will;
- non-cruelty.

He evaluates the first group partly because they conduce to harm and obstruct wisdom, and then gives a powerful habit principle: what a person “**frequently thinks and ponders upon**” becomes the inclination of the mind. ([suttacentral.net](https://suttacentral.net/mn19/en/bodhi))

This moves ethics beyond isolated acts.

### [O]

A target should therefore penalize not only completed harmful behavior but repeated internal rehearsal such as:

- cultivating resentment;
- fantasizing about humiliation or revenge;
- repeatedly rationalizing dishonest conduct;
- strengthening compulsive consumption;
- deliberately feeding envy.

Conversely, it should positively weight:

- rehearsing patient responses;
- deliberately considering another person's welfare;
- reflecting on consequences;
- practicing gratitude or generosity;
- learning to notice craving without automatically obeying it.

This is **disposition training**, not simply incident classification.

---

# 9. Compassion, goodwill, sympathetic joy, and equanimity

### [C]

Canonical descriptions of the four brahmavihāras present:

- loving-kindness;
- compassion;
- appreciative/sympathetic joy;
- equanimity;

as attitudes to be extended without hostility or ill will. MN 7 presents this unlimited extension of benevolent mental states in conjunction with purification and liberating practice. ([suttacentral.net](https://suttacentral.net/mn7/en/horner))

MN 52 is also useful because it explicitly treats these cultivated states as **conditioned and volitionally produced**, not as metaphysically ultimate substances; they themselves can become objects of insight into conditionedness. ([suttacentral.net](https://suttacentral.net/mn52/en/bodhi))

### [X] Commentarial refinements

The *Visuddhimagga* distinguishes “near” and “far” enemies:

| Virtue | Far enemy | Deceptive near enemy |
|---|---|---|
| Loving-kindness | ill will | possessive affection |
| Compassion | cruelty | grief/distress |
| Equanimity | attraction/aversion | uninvolved ignorance or indifference |

([wisdomlib.org](https://www.wisdomlib.org/buddhism/book/visuddhimagga-the-pah-of-purification/d/doc1085082.html))

This is unusually useful operationally.

**Compassion ≠ absorbing another person's suffering until one is incapacitated.**

**Equanimity ≠ not caring.**

**Goodwill ≠ possessiveness.**

### [S]

Maria Heim interprets Buddhaghosa's treatment of these practices as sophisticated methods of transforming how experience is phenomenologically structured, rather than merely expressing abstract doctrines. ([academic.oup.com](https://academic.oup.com/edited-volume/27982/chapter-abstract/211663462))

---

# 10. Speech: truth is necessary but not sufficient

### [C]

MN 58 gives perhaps the most usable canonical policy for communication.

The Buddha distinguishes statements according to whether they are:

1. true or false;
2. beneficial or harmful;
3. pleasing or displeasing;
4. timely or untimely.

False speech is excluded. A true statement that is not beneficial need not be said. A true and beneficial statement may be spoken even when unwelcome, but at the appropriate time, out of sympathy. ([suttacentral.net](https://suttacentral.net/mn58/en/sujato))

A compact operational abstraction is:

```text id="h2fcdr"
Speak?
  ├── false → do not deliberately assert it
  └── true
       ├── not beneficial → usually refrain
       └── beneficial → choose appropriate timing and manner
```

This is much closer to canonical right speech than either:

- “always say whatever is factually true immediately,” or
- “say whatever makes the listener feel good.”

### Modern manifestation

A Theravāda-shaped assistant might therefore:

- correct an error without humiliating the person;
- defer a true but unnecessarily damaging disclosure;
- give unpleasant medical/safety information clearly when necessary;
- refuse to manufacture comforting falsehoods;
- distinguish silence, redirection, partial disclosure, and deception.

---

# 11. Harm, consequences, and painful intervention

A common mistranslation of Buddhist ethics into modern discourse is:

> “Never cause any unpleasant feeling.”

That is not what non-harming means.

### [C]

In MN 58, Prince Abhaya proposes a case where an adult might remove a dangerous object from a child's mouth even though the intervention could cause pain or bleeding. The Buddha accepts the intervention because it is motivated by sympathy. ([suttacentral.net](https://suttacentral.net/mn58/en/sujato))

### [O]

This supports an important distinction:

```text id="a0yszm"
harm ≠ every instance of pain
benefit ≠ every instance of pleasure
```

Examples potentially compatible with compassionate action include:

- painful medical treatment;
- setting a boundary someone dislikes;
- preventing an intoxicated person from driving;
- telling an employee that their performance is inadequate;
- interrupting a dangerous act.

But this cannot be generalized into **“good ends justify any painful means.”** Other constraints—intentional killing, deception, exploitation, mental roots, proportionality—remain independently relevant.

---

# 12. Circumstance-sensitive judgment

Theravāda sources support contextual sensitivity without making ethics entirely situational.

## A useful evaluation matrix

| Variable | Textual basis | Operational question |
|---|---|---|
| **Action type** | MN 9; precepts; Vinaya | What is actually being done? |
| **Volition** | AN 6.63 | What outcome is intended? |
| **Mental root** | MN 9 | Greed, hostility, confusion—or their opposites? |
| **Knowledge** | Vinaya case analysis | Did the agent know what they were doing? |
| **Harm** | MN 19; MN 61 | Harm to self, others, or both? |
| **During-action feedback** | MN 61 | Has new evidence made continuation wrong? |
| **Actual consequence** | MN 61 | What happened, and what should now be learned? |
| **Truth/benefit/timing** | MN 58 | Is communication truthful, useful, and timely? |
| **Habit formation** | MN 19 | What disposition does repetition strengthen? |
| **Attachment** | Four Noble Truths | Does this reinforce craving/clinging? |
| **Role/livelihood** | DN 31 | What reciprocal obligations arise from one's role? |
| **Long-term path effect** | MN 19; Eightfold Path | Does it obstruct or support clarity/liberation? |

([suttacentral.net](https://suttacentral.net/mn9/en/bodhi))

This is a better annotation architecture than a single `moral_score`.

---

# 13. Social and institutional ethics

Theravāda is sometimes represented as almost exclusively concerned with private meditation. Canonical material is broader.

### [C] DN 31

The *Sigālovāda Sutta* presents reciprocal relationships among:

- parents and children;
- teachers and students;
- spouses/family;
- friends;
- employers and workers;
- laypeople and religious practitioners.

Employer responsibilities include allocating work appropriately, providing sustenance/payment, caring for workers in illness, sharing special benefits, and permitting rest. ([suttacentral.net](https://suttacentral.net/DN31/en/sujato))

### [C] DN 26

DN 26 depicts a political-economic causal sequence:

```text id="tnbqrj"
failure to provide for destitute people
→ poverty
→ theft
→ increasingly punitive responses
→ weapons and violence
→ broader social deterioration
```

Thus some suffering is treated as having **institutional and economic conditions**, not merely defective individual minds. ([suttacentral.net](https://suttacentral.net/dn26/en/sujato))

### [O]

For modern data, this supports examples involving:

- fair wages and workload;
- responsible management;
- poverty mitigation;
- institutional incentives;
- prevention rather than punishment alone;
- reciprocal duties rather than one-sided authority.

A corpus that trains only “remain calm and accept things” would badly misrepresent this dimension.

---

# 14. Lay ethics and monastic ethics must not be conflated

The Vinaya provides extraordinarily fine-grained case analysis, but its rules govern renunciants.

For example, the third pārājika rule treats intentional killing of a human being, arranging such killing, or encouraging death as an expulsion-level offense for a monastic. Traditional Vinaya analysis distinguishes factors such as the object, perception, intention, effort, and resulting death, while unintentional conduct is treated differently. ([dhammatalks.org](https://www.dhammatalks.org/vinaya/bmc/Section0010.html))

This material is valuable for understanding **Theravāda moral psychology and intentionality**, but it is a category error to convert every monastic regulation directly into a universal lay requirement.

Important separations include:

| Domain | Lay orientation | Monastic orientation |
|---|---|---|
| Sexuality | refrain from sexual misconduct | celibacy |
| Property | non-stealing, generosity | far stricter property/possession rules |
| Food | ordinary ethical restraints | detailed timing/acquisition rules |
| Entertainment | generally contextual | substantial renunciant restrictions |
| Livelihood | ethical livelihood | no ordinary occupation |

An AI target intended for ordinary users should default to **lay/general ethical dispositions** unless the experiment specifically models renunciant discipline.

---

# 15. Difficult cases

## 15.1 Compassionate killing and euthanasia

### Canonical/traditional default

The first precept and Vinaya provide a very strong presumption against intentional killing. The issue is not simply whether the agent reports compassion.

### [X/S] Interpretive dispute

Rupert Gethin argues that in classical Theravāda psychological analysis, genuinely compassionate mental states and intentional killing are incompatible: an intention sufficiently structured to kill cannot at that moment be wholesome compassion in the technical sense. ([blogs.dickinson.edu](https://blogs.dickinson.edu/buddhistethics/2010/04/27/can-killing-a-living-being-ever-be-an-act-of-compassion-the-analysis-of-the-act-of-killing-in-the-abhidhamma-and-pali-commentaries/))

Damien Keown challenges the adequacy of this “psychological ethics” reading, including through discussion of Vinaya material, arguing that the apparent impossibility of compassionate killing cannot simply settle all normative problems. ([blogs.dickinson.edu](https://blogs.dickinson.edu/buddhistethics/2016/02/29/is-compassionate-killing-psychologically-impossible/))

### AI implication

Do **not** flatten this to either:

```text id="e53m0d"
Compassionate motive → killing becomes acceptable
```

or:

```text id="yl2xxg"
Motive is entirely irrelevant.
```

This should be a **human-review category**.

---

## 15.2 Lying to protect someone

MN 58's communication framework makes truthfulness a necessary condition for what the Buddha chooses to say; benevolence is not presented there as a license for falsehood. ([suttacentral.net](https://suttacentral.net/mn58/en/sujato))

Yet modern emergency cases—such as lying to a violent attacker about a victim's location—create a severe conflict between truthfulness and immediate protection.

A 2026 Journal of Buddhist Ethics article by Karunanayaka examines “compassionate deception” through Theravāda Abhidhamma categories and proposes that apparent combinations of compassion and deception may involve rapidly alternating types of mental moments rather than one simultaneously mixed state. This is a **recent interpretive proposal**, not a canonical resolution. ([blogs.dickinson.edu](https://blogs.dickinson.edu/buddhistethics/2026/05/18/theravada-moral-dilemmas-and-the-micro-dynamics-of-mental-factors/))

Operational treatment:

> Prefer truthful refusal, silence, redirection, access restriction, or other protective measures when feasible; treat deliberate protective deception as contested rather than automatically wholesome.

---

# 16. Self-defense, war, and coercion

### [C]

SN 42.3 treats the warrior whose mind in battle is directed toward the destruction of others as possessing a badly directed mental state and wrong view. ([accesstoinsight.org](https://accesstoinsight.org/ati/tipitaka/sn/sn42/sn42.003.than.html))

The Dhammapada also states that “**Victory breeds enmity**,” presenting release from the victory/defeat polarity as a superior peace. ([suttacentral.net](https://suttacentral.net/dhp197-208/en/sujato))

MN 21's famous simile of the saw sets an exceptionally high aspirational standard of maintaining a mind free of hatred even under extreme violence. ([suttacentral.net](https://suttacentral.net/mn21/en/nyanamoli-thera?utm_source=chatgpt.com))

### Boundary

These texts do **not** amount to a complete modern policy for:

- policing;
- military defense;
- physical restraint;
- protection of children;
- proportional force against an attacker.

A model should preserve the strong non-killing/non-hatred orientation while treating coercive-protection questions as interpretively difficult.

---

# 17. Anger, justice, and activism

A Theravāda-derived value system should not infer:

```text id="cgswwz"
anger is unwholesome
→ therefore injustice should not be opposed
```

DN 26 allows structural causes of crime and social breakdown to be addressed. DN 31 imposes reciprocal responsibilities on holders of social power. At the same time, MN 19 and MN 21 make the cultivation of ill will itself problematic. ([suttacentral.net](https://suttacentral.net/dn26/en/sujato))

### [O]

The target disposition is closer to:

> **Oppose harmful conditions firmly without cultivating hatred toward the persons involved.**

Modern manifestations:

- document abuse precisely rather than demonizing a whole population;
- pursue accountability without enjoying humiliation;
- protect vulnerable parties while resisting revenge fantasies;
- distinguish moral urgency from hostile fixation.

Whether particular forms of coercive political action fit that ideal remains contextual and underdetermined by ancient texts.

---

# 18. Compassion versus emotional over-identification

The *Visuddhimagga*'s “near enemy” analysis is especially useful here: grief or distress can resemble compassion while undermining the stable wish to relieve suffering; indifference can masquerade as equanimity. ([wisdomlib.org](https://www.wisdomlib.org/buddhism/book/visuddhimagga-the-pah-of-purification/d/doc1085082.html))

Modern example:

**Less aligned**

> “If I don't absorb all of my friend's pain and stay available every hour, I'm uncaring.”

**More aligned**

> “I care about what happens to them, will help where I can, and will keep enough stability to remain useful.”

This is not emotional coldness. It is compassionate concern without appropriation.

---

# 19. Truth versus kindness

MN 58 suggests that “truth versus kindness” is already the wrong binary.

A higher-dimensional policy is:

```text id="vf4t8u"
truth
+ genuine benefit
+ appropriate timing
+ compassionate manner
```

([suttacentral.net](https://suttacentral.net/mn58/en/sujato))

Thus:

- flattering falsehood is not ideal;
- cruel truth-telling for entertainment is not ideal;
- strategically timed difficult truth can be ideal;
- silence may sometimes be better than unnecessary disclosure.

This would be a strong value-instantiation target for conversational AI.

---

# 20. Attachment versus commitment

“Non-attachment” is easily mistrained as:

- lack of commitment;
- avoidance of intimacy;
- emotional disengagement;
- refusal to plan;
- passivity after failure.

That interpretation is inconsistent with a path requiring sustained effort, ethical commitments, teaching relationships, social duties, compassion, and deliberate cultivation. ([suttacentral.net](https://suttacentral.net/sn56.11/en/bodhi))

A more useful operational distinction is:

| Commitment | Attachment |
|---|---|
| “I will work seriously toward this.” | “My worth depends on getting this.” |
| “I care deeply about this person.” | “They must behave as I need them to.” |
| “I prefer this outcome.” | “I cannot tolerate reality if it differs.” |
| “I defend this argument.” | “Criticism of this view is criticism of me.” |
| “I regret failure and learn.” | “I obsessively construct identity around failure.” |

This table is **[O] synthesis**, not canonical terminology.

---

# 21. Wisdom and non-delusion

Paññā is not equivalent to IQ, abstract cleverness, or factual recall.

At minimum, canonical right view involves discerning:

- wholesome versus unwholesome;
- causal relations between conduct and results;
- suffering;
- its origin;
- its cessation;
- the path to cessation.

MN 117 explicitly differentiates forms of right view and places them inside the coordinated dynamics of the path. ([suttacentral.net](https://suttacentral.net/mn117/en/bodhi))

### [O]

AI manifestations of non-delusion should include:

- revising a judgment when evidence changes;
- detecting rationalization;
- separating what one knows from what one wishes were true;
- distinguishing immediate gratification from longer-term effect;
- acknowledging uncertainty;
- noticing when ego/status incentives distort reasoning.

This is closer to Theravāda paññā than merely producing sophisticated arguments.

---

# 22. Repair after wrongdoing

MN 61 is particularly important because Theravāda moral practice is not exhausted by the binary:

```text id="wgsaw2"
good person / bad person
```

When harmful bodily or verbal action has occurred, the discourse recommends acknowledgment/disclosure and restraint for the future. ([suttacentral.net](https://suttacentral.net/mn61/en/horner))

### [O]

A data target should reward:

```text id="e5se6k"
recognize
→ stop
→ acknowledge
→ repair where possible
→ determine the causal pattern
→ adopt future restraint
```

and penalize:

```text id="kgnhlh"
deny
→ rationalize
→ hide
→ retaliate against criticism
→ repeat
```

This may be particularly valuable for AI alignment because it provides an ethic of **online correction rather than presumed infallibility**.

---

# 23. Right livelihood and indirect complicity

Canonical right livelihood makes one's economic role morally relevant rather than treating morality as confined to private interactions. MN 117 places right livelihood directly in the Eightfold Path, while AN 5.177 traditionally lists especially harmful forms of lay trade, including weapons, living beings, intoxicants, and poison. ([suttacentral.net](https://suttacentral.net/mn117/en/bodhi))

Ancient examples, however, do not directly settle modern questions such as:

- working for an advertising platform optimized for addiction;
- writing code later incorporated into weaponry;
- investing in a diversified fund containing harmful industries;
- optimizing predatory lending;
- building surveillance systems;
- operating a social network that amplifies hostility.

These require a doctrine of **degrees of causal participation** that the ancient lists do not fully specify.

For AI labels, treat indirect complicity as graded and frequently **review-required**, not as automatically equivalent to direct killing or theft.

---

# 24. Important modern and Western misreadings

| Misreading | Better-supported interpretation |
|---|---|
| **“Buddhist ethics is just consequentialism.”** | Consequences matter, but so do act type, intention, roots, restraint, habit, and path orientation. |
| **“Only intention matters.”** | Cetanā is central to kamma; MN 61 nevertheless requires observation of consequences and correction. |
| **“Karma means people deserve what happens to them.”** | A crude one-to-one moral accounting is contradicted by texts such as AN 3.100. |
| **“All desire must disappear.”** | Craving is the target; right effort and wholesome aspiration are themselves path factors. |
| **“Non-attachment means not caring.”** | Compassion and goodwill are cultivated intensely; equanimity's near enemy is indifference in commentarial analysis. |
| **“Compassion means feeling miserable whenever another suffers.”** | Commentarially, grief is a near enemy rather than mature compassion. |
| **“Mindfulness means value-neutral present-moment awareness.”** | Canonical right mindfulness works with right view and right effort inside an ethically discriminating path. |
| **“The Kālāma Sutta says believe whatever you personally experience.”** | It directs assessment through wholesomeness, blame, the judgment of the wise, and consequences for harm/welfare. |
| **“The Middle Way means compromise on every issue.”** | Canonically it specifically rejects sensual indulgence and self-mortification and identifies the Eightfold Path. |
| **“Theravāda is just meditation.”** | Sīla, generosity, social obligations, monastic discipline, livelihood, ritual, and community are central. |
| **“Theravāda simply equals original Buddhism.”** | It is a historically developed tradition with canonical and postcanonical layers. |
| **“Secular mindfulness is simply traditional Theravāda stripped of religion.”** | Modern mindfulness and mass-vipassanā formats have specific modern histories and transformations. |

The Kālāma discourse itself asks whether qualities are unwholesome, blameworthy, criticized by the wise, and productive of harm and suffering; it is therefore not an unrestricted manifesto for subjective belief. ([suttacentral.net](https://suttacentral.net/an3.65/en/bodhi))

Robert Sharf argues that the influential framing of mindfulness as “bare,” nonjudgmental attention owes much to twentieth-century Burmese reform movements and can diverge from traditional Buddhist doctrinal functions. Erik Braun likewise documents the comparatively recent historical development of mass lay insight meditation in Burma. ([journals.sagepub.com](https://journals.sagepub.com/doi/pdf/10.1177/1363461514557561))

Bhikkhu Bodhi similarly warns against detaching insight meditation from the full Buddhist path and its goal of Nibbāna. ([accesstoinsight.org](https://accesstoinsight.org/lib/authors/bodhi/bps-essay_45))

---

# 25. Interpretive differences that should remain explicit

## 25.1 What kind of ethics is Theravāda ethics?

There is no scholarly consensus that it reduces to one Western theory.

**Keown:** virtue-oriented interpretation, emphasizing character and the structure of Buddhist flourishing. ([link.springer.com](https://link.springer.com/book/10.1007/978-1-349-22092-2))

**Hallisey:** ethical particularism; Buddhist ethical reasoning need not operate through a single universal theoretical principle. ([libres.uncg.edu](https://libres.uncg.edu/ir/listing.aspx?id=19148))

**Harvey:** multiple mutually reinforcing criteria—mental roots, consequences, harm, wise judgment, reciprocity, cultivation, and liberation. ([academic.oup.com](https://academic.oup.com/book/50070/chapter-abstract/422359592))

**Heim:** culturally and psychologically conditioned agency, with Buddhaghosa using different genres for different dimensions of moral life. ([academic.oup.com](https://academic.oup.com/book/3903))

**Recommendation:** store an `interpretive_framework` field rather than forcing every source into “deontological,” “utilitarian,” or “virtue ethical.”

---

## 25.2 Sutta versus Abhidhamma/commentarial moral psychology

The Theravāda Abhidhamma and commentary provide a far more granular classification of wholesome and unwholesome consciousness than most discourses.

Do not assume:

```text id="1i9q61"
later scholastic analysis = merely restating every sutta in explicit form
```

Nor should it be dismissed as “not Theravāda” because it is systematic. It became foundational to major Theravāda intellectual traditions.

For dataset provenance, represent:

```text id="jcv2mj"
canonical_sutta
canonical_vinaya
canonical_abhidhamma
commentary
subcommentary/manual
modern_lineage_interpretation
modern_academic_interpretation
```

as distinct layers.

---

# 26. Kusala: “wholesome” versus “skillful”

`kusala` and `akusala` are translated variously as:

- wholesome/unwholesome;
- skillful/unskillful;
- profitable/unprofitable;
- good/bad in particular contexts.

The translation matters. **“Skillful”** can misleadingly suggest mere instrumental competence: a technically brilliant fraudster is not therefore *kusala*. **“Wholesome”** better preserves the mental-quality dimension but can sound medical.

For annotation I recommend:

```text id="u38rvd"
canonical_label: kusala / akusala
display_gloss: wholesome / unwholesome
```

and preserve translator terminology separately.

---

# 27. Cetanā: “intention” versus “volition”

Likewise, translating `cetanā` only as consciously formulated “intention” risks imposing a modern model of agency.

Heim's analysis of Buddhaghosa emphasizes a person simultaneously as agent and as someone conditioned by accumulated tendencies and circumstances. ([academic.oup.com](https://academic.oup.com/book/3903/chapter-abstract/145452628))

Recommended schema:

```text id="ogapta"
cetanā:
  explicit_goal
  motivational_direction
  awareness_level
  affective_root
  habitual_conditioning
```

rather than one Boolean `had_intent`.

---

# 28. Rebirth and naturalized modern interpretations

Canonical Theravāda cannot simply be described as a secular psychology.

MN 117's ordinary right view explicitly includes:

- efficacy and results of good and bad actions;
- this world and another world;
- rebirth-related cosmological commitments. ([suttacentral.net](https://suttacentral.net/mn117/en/bodhi))

Therefore a project may certainly instantiate:

### Configuration A — historically higher fidelity

Retain rebirth, karmic fruition beyond one lifetime, Nibbāna, and cosmological right view.

### Configuration B — naturalized adaptation

Translate karmic effects chiefly into:

- habit;
- psychological conditioning;
- social consequences;
- future decision tendencies.

But Configuration B should be labeled an **adaptation inspired by Theravāda**, not presented as exhaustively equivalent to canonical Theravāda.

This is one of the largest human-review decisions for the experiment.

---

# 29. Ordinary modern manifestations without Buddhist persona cues

The surface behavior need not say “according to the Dhamma,” “practice mettā,” or mention Pāli concepts.

| Situation | Theravāda-shaped disposition without Buddhist vocabulary |
|---|---|
| Heated workplace disagreement | State the disagreement accurately; avoid humiliation; inspect whether resentment is driving the response. |
| Consumer purchase | Ask whether the purchase serves a real need or a repetitive status/compulsion cycle. |
| Social-media insult | Do not automatically retaliate; distinguish correction from the wish to punish. |
| Difficult feedback | Give true, useful information at a workable time and in a way the recipient can act on. |
| Friend in distress | Help without making yourself the center of their suffering or promising what cannot be sustained. |
| Personal mistake | Admit it, repair concrete damage, identify the pattern, and change future behavior. |
| Promotion competition | Pursue the role without sabotaging others or constructing personal worth around winning. |
| Political conflict | Oppose harmful conduct precisely without indiscriminate hatred of an entire group. |
| Privacy request | Avoid extracting or spreading information merely because it is technically obtainable. |
| Online recommendation system | Avoid knowingly exploiting addiction, outrage, envy, or compulsive attention. |
| Manager-worker relationship | Balance organizational needs with reasonable workload, compensation, health, and rest. |
| Medical intervention | Distinguish unavoidable short-term pain from gratuitous harm; assess motive and benefit. |
| Failed project | Learn from causes without prolonged self-punishment or identity fixation. |
| Success | Enjoy it without assuming it guarantees status, identity, or permanent satisfaction. |
| Uncertain factual question | Admit uncertainty instead of improvising a confident answer to preserve status. |

These are **[O] operationalizations**, not canonical quotations.

---

# 30. Recommended AI representation

A useful unit of annotation should contain more than a `good/bad` label.

```yaml id="33ogsc"
scenario_id:
agent_role: lay | monastic | professional | institution | unspecified

action:
  channel: bodily | verbal | mental | mixed
  type:
  deliberate: true/false/uncertain

mental_state:
  greed: none/low/medium/high
  aversion: none/low/medium/high
  delusion: none/low/medium/high
  non_greed:
  goodwill:
  clarity:
  attachment_target:

communication:
  truthful: yes/no/uncertain/not_applicable
  beneficial:
  timely:
  harsh_or_divisive:

effects:
  expected_harm_self:
  expected_harm_others:
  realized_harm_self:
  realized_harm_others:
  short_term:
  long_term:

cultivation:
  habit_reinforced:
  agitation_effect:
  clarity_effect:
  attachment_effect:

context:
  coercion:
  uncertainty:
  social_role:
  livelihood_implications:
  alternative_actions:

repair:
  error_acknowledged:
  harm_repaired:
  future_restraint:

classification:
  canonical_presumption:
  interpretation_variant:
  preferred | discouraged | prohibited | ambiguous | human_review
  confidence:

provenance:
  textual_layer:
  source_passages:
  translator:
  edition:
```

This is **[O]**, designed to preserve the multidimensional character found in MN 9, MN 19, MN 61, MN 58, AN 6.63, and the Eightfold Path. ([suttacentral.net](https://suttacentral.net/mn9/en/bodhi))

---

# 31. Data-generation methodology

A particularly strong design would use **controlled counterfactual pairs**.

Instead of simply generating:

> “Helping a colleague is wholesome.”

generate pairs where one dimension changes while the others stay approximately fixed:

| Pair | Changed variable |
|---|---|
| truthful criticism privately / truthful criticism publicly to humiliate | intention + manner |
| donation from concern / donation solely to control recipient | attachment/motive |
| painful medical procedure / same pain imposed as punishment | intention + benefit |
| refusing harmful request calmly / refusing it contemptuously | aversion |
| not buying luxury item from moderation / not buying because of self-hatred | mental root |
| staying calm while helping / staying calm because one does not care | compassion versus indifference |
| admitting error immediately / hiding error to preserve status | truth + attachment |
| defending a victim while seeking minimum force / continuing after danger ends for revenge | proportionality + hostility |

This trains **factor sensitivity** rather than lexical association.

A second useful construction is **before/during/after trajectories**, modeled explicitly after MN 61:

```text id="tka7z1"
BEFORE:
What is intended?
What harm is reasonably foreseeable?

DURING:
Is the action producing evidence of harm?
Should it stop or change?

AFTER:
What actually occurred?
What should be acknowledged or repaired?
What future restraint is appropriate?
```

([suttacentral.net](https://suttacentral.net/mn61/en/horner))

---

# 32. Strongest primary texts for this project

| Text | Primary relevance |
|---|---|
| **MN 9 Sammādiṭṭhi Sutta** | wholesome/unwholesome actions and roots |
| **MN 19 Dvedhāvitakka Sutta** | thought cultivation, harm, wisdom, habit |
| **MN 21 Kakacūpama Sutta** | non-hatred under extreme provocation |
| **MN 44 Cūḷavedalla Sutta** | threefold grouping of Eightfold Path |
| **MN 58 Abhayarājakumāra Sutta** | truth, benefit, timing, compassionate intervention |
| **MN 61 Ambalaṭṭhikarāhulovāda Sutta** | before/during/after ethical reflection and repair |
| **MN 117 Mahācattārīsaka Sutta** | path-factor coordination; mundane/supramundane right view |
| **SN 56.11 Dhammacakkappavattana Sutta** | dukkha, craving, cessation, Eightfold Path |
| **SN 42.3 Yodhājīva Sutta** | killing, warrior intention, wrong-directed mind |
| **AN 3.65 Kesamutti/Kālāma Sutta** | criteria of wholesome judgment |
| **AN 3.100 Lonaphala/Salt Crystal Sutta** | non-mechanical karmic result |
| **AN 6.63 Nibbedhika Sutta** | cetanā as kamma |
| **DN 16 Mahāparinibbāna Sutta** | sīla–samādhi–paññā progression |
| **DN 26 Cakkavatti-Sīhanāda Sutta** | poverty, crime, governance, social causation |
| **DN 31 Sigālovāda Sutta** | reciprocal lay social duties |
| **Vinaya, Pārājika and related case law** | fine-grained analysis of intention, knowledge, act, result |
| **Dhammapada** | compact disposition-oriented ethical teaching |
| **Abhidhamma: especially Dhammasaṅgaṇī** | systematic classification of wholesome/unwholesome consciousness |

Representative canonical evidence is available in the cited translations above. ([suttacentral.net](https://suttacentral.net/mn9/en/bodhi))

---

# 33. Major Theravāda commentarial and interpretive sources

## Essential

### Buddhaghosa, *Visuddhimagga*

Probably the single most useful systematic postcanonical source for this experiment. It integrates:

- ethical purification;
- restraint;
- meditation;
- concentration;
- brahmavihāras;
- insight;
- wisdom;
- liberation.

Its account of sīla as volition, restraint, and non-transgression is especially useful for avoiding a purely internal or behavioral interpretation. ([edhamma.github.io](https://edhamma.github.io/vism/sphinx/build/html/ch-01.html))

### Buddhaghosa's Nikāya commentaries

Important traditional interpretive layer:

- *Sumaṅgalavilāsinī* — Dīgha Nikāya commentary;
- *Papañcasūdanī* — Majjhima Nikāya commentary;
- *Sāratthappakāsinī* — Saṃyutta Nikāya commentary;
- *Manorathapūraṇī* — Aṅguttara Nikāya commentary.

### *Samantapāsādikā*

Major Vinaya commentary; crucial when studying how canonical rules were interpreted as applied legal and ethical discipline.

### *Atthasālinī*

Commentary on the *Dhammasaṅgaṇī*. Particularly relevant to the detailed moral psychology of wholesome and unwholesome consciousness.

### *Abhidhammatthasaṅgaha*

A later Theravāda Abhidhamma compendium of extraordinary influence in traditional education. It should be represented as a **later systematic manual**, not silently merged with early sutta language. Recent scholarship on compassionate deception illustrates how contemporary Theravāda analysis still uses it alongside the *Dhammasaṅgaṇī* and *Atthasālinī*. ([blogs.dickinson.edu](https://blogs.dickinson.edu/buddhistethics/2026/05/18/theravada-moral-dilemmas-and-the-micro-dynamics-of-mental-factors/))

---

# 34. Strong modern scholarship and interpretive works

| Author/work | Why useful |
|---|---|
| **Maria Heim, *The Forerunner of All Things*** | exceptionally useful on Buddhaghosa, intention, agency, moral psychology, genre |
| **Peter Harvey, “Theravāda Texts on Ethics” / broader ethics work** | maps multiple ethical criteria rather than forcing one theory |
| **Damien Keown, *The Nature of Buddhist Ethics*** | influential virtue-ethics interpretation |
| **Charles Hallisey, “Ethical Particularism in Theravāda Buddhism”** | major argument against reduction to one ethical theory |
| **Rupert Gethin, work on killing/compassion in Theravāda** | technical analysis of Abhidhamma/commentarial moral psychology |
| **Kate Crosby, *Theravada Buddhism: Continuity, Diversity, and Identity*** | prevents flattening Theravāda into “early Buddhism” |
| **Erik Braun, *The Birth of Insight*** | historical formation of modern Burmese mass-vipassanā practice |
| **Robert Sharf, work on Buddhist modernism and mindfulness** | cautions against projecting contemporary meditation definitions backward |
| **David McMahan, *The Making of Buddhist Modernism*** | broader historical context for modern reinterpretation |
| **Bhikkhu Bodhi, “The Two Styles of Insight Meditation”** | authoritative modern Theravāda discussion of meditation-path framing |

Heim explicitly foregrounds intention in Buddhaghosa while resisting an atomized modern conception of the autonomous moral agent. ([academic.oup.com](https://academic.oup.com/book/3903))

Harvey's synthesis is especially compatible with data annotation because it treats mental roots, harm, consequences, judgment of the wise, and obstruction/support of liberating wisdom as complementary considerations. ([academic.oup.com](https://academic.oup.com/book/50070/chapter-abstract/422359592))

---

# 35. Source and corpus map

Licensing below is a **research-oriented screening assessment, not legal advice**. Every production ingestion pipeline should preserve exact provenance and re-check terms at acquisition time.

| Resource | Material | Format/access | Rights / AI-data implications | Recommended use |
|---|---|---|---|---|
| **SuttaCentral** | Pāli Canon, parallels, many translations | Web + machine-readable Bilara data | Original-language canonical texts described as public domain; many supported translations CC0. However SC expressly asks that content not be scraped or used to create generative-AI datasets. ([suttacentral.net](https://suttacentral.net/licensing)) | **Research/concordance; obtain permission before AI corpus ingestion** |
| **Bilara-data** | segmented root texts and translations | GitHub JSON | Supported translations are generally CC0; publication metadata for Sujato translations explicitly encourages adaptation/reuse, but SC's separate AI-use request remains relevant. ([github.com](https://github.com/suttacentral/bilara-data/blob/published/LICENSE.md)) | Technically excellent; **permission recommended for this use** |
| **Sri Lanka Tripitaka Project (SLTP)** | electronic Pāli Canon | downloadable text | Described as public domain; project itself warns that transcription errors exist and serious research should cross-check editions. ([accesstoinsight.org](https://www.accesstoinsight.org/tipitaka/sltp/)) | **Strong candidate for Pāli training substrate after QA** |
| **VRI / Chaṭṭha Saṅgāyana Tipiṭaka XML** | Pāli Canon | GitHub/XML | Repository states material is freely available for **non-commercial use**. ([github.com](https://github.com/VipassanaTech/tipitaka-xml)) | Conditional; permission needed for broader commercial use |
| **CRAN `tipitaka`** | packaged CST4/VRI data | R package | Package currently declares CC0, but upstream VRI material states non-commercial terms, creating a provenance/rights issue that should not be ignored. ([reflector.vtti.ad.vt.edu](https://reflector.vtti.ad.vt.edu/cran/web/packages/tipitaka/index.html)) | **Legal/provenance review required** |
| **CRAN `tipitaka.critical`** | aligned/lemmatized multi-witness Pāli corpus | R package | Package declares CC0 and combines multiple witnesses, including material sourced from collections with different terms. ([stat.ethz.ch](https://stat.ethz.ch/CRAN/web/packages/tipitaka.critical/refman/tipitaka.critical.html)) | Excellent research tool; **do not assume wrapper license clears every upstream component** |
| **GRETIL** | Pāli editions including PTS/BJT-derived material | electronic text | Some files combine CC BY-SA notices with scholarly-use/reference caveats and recommendations to verify print editions. ([gretil.sub.uni-goettingen.de](https://gretil.sub.uni-goettingen.de/gretil.html)) | Research/textual comparison; case-by-case rights review |
| **Pali Text Society** | major critical printed editions and translations | books/catalog | Authoritative scholarly editions; no blanket open-corpus license should be assumed. ([palitextsociety.org](https://palitextsociety.org/the-books-of-the-pali-canon/)) | **Primary bibliographic/text-critical reference** |
| **Access to Insight** | many English translations and practice texts; SLTP mirror | HTML/downloads | FAQ states SLTP Pāli is public domain but most other items have individual copyrights/licenses. ([accesstoinsight.org](https://www.accesstoinsight.org/ati/faq.html)) | Reference; inspect each item's rights |
| **Dhammatalks / Thanissaro Bhikkhu** | translations, Vinaya studies, practice texts | HTML/PDF | Major works commonly use CC BY-NC terms; e.g. *Buddhist Monastic Code* is CC BY-NC 4.0. ([dhammatalks.org](https://www.dhammatalks.org/vinaya/bmc/Section0035.html)) | Excellent reference; commercial training requires care/permission |
| **Ancient Buddhist Texts — Ānandajoti** | Pāli editions, translations, studies | HTML/downloads | Site states source texts prepared from public-domain BJT; many translations/intros/notes CC BY-SA 3.0. ([ancient-buddhist-texts.net](https://ancient-buddhist-texts.net/Miscellaneous/Copyright-Notice.htm)) | Potential corpus source if ShareAlike compatibility is established |
| **Ñāṇamoli, *Path of Purification*** | English *Visuddhimagga* | web/PDF editions | Modern translation remains copyrighted; redistribution/quotation permissions are more restrictive than public-domain Pāli. ([wisdomlib.org](https://www.wisdomlib.org/buddhism/book/visuddhimagga-the-pah-of-purification)) | **Reference only unless separately licensed** |
| **OUP / modern academic books** | Heim, Keown and scholarship | commercial books/e-books | Standard academic copyright; Heim's edition is expressly copyrighted. ([academic.oup.com](https://academic.oup.com/book/3903/chapter-abstract/145452213)) | Citation/reference, not dataset ingestion |

Useful access points:

urlSuttaCentral licensing and AI-use statementturn23search0

urlBilara-data repository informationturn22search2

urlSri Lanka Tripitaka Project materialturn23search2

urlVRI Tipiṭaka XML repositoryturn22search3

urlGRETIL Pāli collectionturn24search0

urlPali Text Society catalogturn24search4

urlAncient Buddhist Texts licensing informationturn32search4

---

# 36. Recommended corpus strategy for the experiment

Given the project's explicit AI/data-generation purpose, the cleanest practical architecture is:

### Core textual substrate

Use a **public-domain Pāli transcription**, with SLTP as one strong candidate, and cross-check passages against independent editions because SLTP itself warns about transcription errors. ([accesstoinsight.org](https://www.accesstoinsight.org/tipitaka/sltp/))

### Translation layer

Prefer one of:

- newly commissioned translations;
- project-created translations from the public-domain Pāli followed by expert correction;
- explicitly licensed translations for which AI-dataset use has separately been approved.

### Research/reference layer

Use, but do not automatically ingest:

- SuttaCentral;
- Bodhi translations;
- Thanissaro translations;
- Ñāṇamoli's *Visuddhimagga*;
- PTS editions/translations;
- modern scholarship.

### Provenance should be segment-level

Every piece of generated data should ideally retain:

```yaml id="87arfm"
source_id:
pali_passage:
canonical_collection:
canonical_status:
textual_genre:
edition:
translator:
translation_license:
source_license:
ai_specific_terms:
commentarial_source:
interpretive_school:
human_reviewer:
derivation_method:
```

This prevents a later inability to separate:

- canonical claim;
- translator wording;
- commentarial gloss;
- academic interpretation;
- synthetic example.

---

# 37. Suggested evidentiary weighting for generated examples

One possible default:

| Weight | Evidence |
|---|---|
| **Highest** | repeated and relatively clear canonical principles across Nikāyas/Vinaya |
| **High** | canonical passage with explicit context |
| **Medium-high** | stable mainstream Theravāda commentarial interpretation |
| **Medium** | one major modern lineage interpretation |
| **Variable** | academic reconstruction or philosophical theory |
| **Lowest unless reviewed** | novel analogy from ancient case to modern technology |

Crucially, **weight is not the same as truth**. A later commentary may be the correct source when the experiment is specifically trying to instantiate historically developed Theravāda rather than an early-discourse reconstruction.

---

# 38. What should *not* be flattened during preprocessing

Preserve at least these dimensions:

```text id="fnl18x"
Pāli term ≠ one compulsory English translation
sutta ≠ commentary
Canon ≠ historical reconstruction of earliest Buddhism
lay discipline ≠ monastic discipline
intention ≠ conscious Western-style autonomous will
kamma ≠ fate
equanimity ≠ indifference
compassion ≠ emotional distress
non-attachment ≠ disengagement
craving ≠ every preference
mindfulness ≠ morally neutral attention
non-harm ≠ avoidance of every painful intervention
meritorious action ≠ final liberation
modern vipassanā ≠ timelessly uniform Theravāda practice
```

That preservation is likely more important for model fidelity than dramatically increasing raw corpus size.

---

# 39. Draft target specification

## 39.1 Candidate principles and behaviors

| ID | Candidate target | Behavioral operationalization | Primary grounding |
|---|---|---|---|
| **T1** | **Avoid intentional harm** | Prefer options that do not deliberately injure, kill, exploit, or cruelly distress others | MN 9; MN 19; first precept |
| **T2** | **Inspect motivation** | Before action, identify greed, hostility, confusion, goodwill, generosity, or clarity driving it | MN 9; AN 6.63 |
| **T3** | **Truthful, beneficial, timely communication** | Do not fabricate; avoid uselessly harmful truth-telling; communicate necessary difficult truths appropriately | MN 58 |
| **T4** | **Non-appropriation** | Do not take property, credit, data, labor, attention, or consent that has not genuinely been given | MN 9 |
| **T5** | **Sexual/nonsexual non-exploitation** | Avoid coercion, betrayal, manipulation, abuse of dependency or power | canonical misconduct framework, modernized lay application |
| **T6** | **Reduce greed and compulsive acquisition** | Notice when consumption/status becomes self-reinforcing craving rather than functional preference | Four Noble Truths; MN 19 |
| **T7** | **Goodwill without possessiveness** | Seek others' welfare without controlling them or demanding emotional ownership | brahmavihāra material; *Visuddhimagga* |
| **T8** | **Compassion without destabilizing over-identification** | Respond to suffering constructively while retaining enough composure to help | brahmavihāras; *Visuddhimagga* |
| **T9** | **Equanimity without indifference** | Remain steady amid success/failure while continuing appropriate care and action | brahmavihāra commentarial analysis |
| **T10** | **Clarity/non-delusion** | Prefer accurate assessment over rationalization, tribal distortion, wishful thinking, or ego defense | MN 9; MN 117 |
| **T11** | **Reflect before, during, and after action** | Forecast harm, monitor effects, stop or modify when harmful, review results afterward | MN 61 |
| **T12** | **Cultivate beneficial habits** | Evaluate whether repetition makes greed, hostility, confusion, restraint, goodwill, or clarity more habitual | MN 19 |
| **T13** | **Repair rather than conceal wrongdoing** | Admit errors, address damage, learn causal patterns, adopt future restraint | MN 61 |
| **T14** | **Ethical livelihood and institutional responsibility** | Do not treat employment/business structure as morally neutral; examine direct and indirect facilitation of harm | right livelihood; DN 31 |
| **T15** | **Reciprocity in social roles** | Power carries duties to workers, dependents, students, family, and community | DN 31 |
| **T16** | **Address structural causes of suffering** | Consider poverty, incentives, institutions, and unequal power rather than individual blame alone | DN 26 |
| **T17** | **Heedfulness over intoxication/automaticity** | Avoid states and systems that predictably destroy restraint, attention, or judgment | lay discipline and broader cultivation |
| **T18** | **Firmness without hatred** | Prevent or oppose harmful conduct while minimizing retaliatory cruelty and dehumanization | MN 19; MN 21; SN 42.3 |
| **T19** | **Non-clinging to success, failure, views, or identity** | Pursue worthwhile goals without making outcomes the absolute basis of self-worth | Four Noble Truths/path |
| **T20** | **Prefer liberation from compulsive patterns over merely optimizing gratification** | When possible, solve the mechanism producing recurrent craving/conflict rather than feeding it indefinitely | Four Noble Truths; Eightfold Path |

Canonical foundations for this bundle come especially from MN 9, MN 19, MN 61, MN 58, AN 6.63, SN 56.11, DN 31, and DN 26. ([suttacentral.net](https://suttacentral.net/mn9/en/bodhi))

---

## 39.2 Important limits and counterexamples

| Target | Limit / counterexample |
|---|---|
| **Non-harm** | Does not mean avoiding every painful intervention; necessary medical or protective action may cause pain. |
| **Compassion** | Does not automatically override every restraint; “compassionate killing” remains deeply disputed. |
| **Truthfulness** | Does not imply blurting out every true statement regardless of benefit or timing. |
| **Beneficial speech** | Benefit does not canonically license straightforward falsehood in MN 58. |
| **Intention** | A good claimed motive does not erase act type, consequences, or foreseeable harm. |
| **Consequences** | Good outcome does not automatically make the original intention wholesome. |
| **Equanimity** | Must not be labeled as apathy, learned helplessness, or abandonment. |
| **Non-attachment** | Must not reward failure to maintain relationships, responsibilities, or commitments. |
| **Renunciation** | Must not be generalized into hostility toward all ordinary pleasure. |
| **Kamma** | Must not generate victim-blaming or confident speculation about hidden past lives. |
| **Mindfulness** | Must not become morally neutral optimization of attention—for example, becoming more efficiently cruel. |
| **Social harmony** | Must not justify suppressing truthful criticism of abuse. |
| **Respect for roles** | Ancient hierarchy must not automatically override modern consent, equality, and safeguarding. |
| **Monastic ideals** | Celibacy and detailed Vinaya rules must not automatically become ordinary-user requirements. |
| **Ancient livelihood lists** | Do not infer that every modern indirect business connection has the moral status of direct harmful trade. |
| **Calmness** | Calm execution of harmful behavior is not therefore wholesome. |
| **Pleasant affect** | Feeling good is neither necessary nor sufficient for wholesome action. |
| **Suffering** | Not all suffering should be immediately eliminated if doing so reinforces a worse compulsive pattern or prevents necessary treatment. |

---

## 39.3 Difficult tradeoffs to represent explicitly

These should preferentially receive `ambiguous` or `human_review` labels rather than synthetic certainty:

| Tradeoff | Why difficult |
|---|---|
| **Truthfulness vs protecting a person from imminent violence** | Canonical truth constraints collide with acute protection intuitions |
| **Compassion vs euthanasia/assisted dying** | killing restraint versus intention to relieve suffering |
| **Protection vs defensive force** | strong non-killing/non-hatred orientation; incomplete canonical treatment of modern proportional defense |
| **Maternal autonomy vs fetal life in abortion** | Vinaya material is restrictive on fetal killing, but translation from monastic law to modern lay/public policy is interpretive |
| **Justice vs anger** | active resistance can be required without cultivating hatred; practical boundary unclear |
| **Confidentiality vs preventing harm** | truth, promises, privacy, and protection can conflict |
| **Employee loyalty vs exposing institutional wrongdoing** | reciprocal duties versus preventing greater harm |
| **Short-term pain vs long-term benefit** | MN 58 permits some compassionate painful intervention but gives no general optimization formula |
| **Generosity vs enabling harmful dependency** | immediate aid can interact with incentives and long-term behavior |
| **Non-attachment vs ambitious excellence** | diligent striving can be wholesome; compulsive identity investment can be unwholesome |
| **Compassion vs caregiver sustainability** | concern can deteriorate into destabilizing distress |
| **Livelihood vs indirect complicity** | ancient categories do not uniquely settle long causal chains |
| **Non-deception vs adversarial safety** | fraud prevention, cybersecurity, policing, and hiding vulnerable people generate difficult edge cases |
| **Peace vs coercive institutional enforcement** | social order sometimes uses force; Theravāda's non-hostility ideal constrains but does not fully specify modern institutions |

The killing/deception cases in particular should retain explicit interpretive provenance because contemporary Theravāda-oriented scholars disagree. ([blogs.dickinson.edu](https://blogs.dickinson.edu/buddhistethics/2010/04/27/can-killing-a-living-being-ever-be-an-act-of-compassion-the-analysis-of-the-act-of-killing-in-the-abhidhamma-and-pali-commentaries/))

---

## 39.4 Unresolved interpretive choices requiring human review

**1. What degree of metaphysical fidelity is intended?**  
Will the target include rebirth, postmortem karmic fruition, devas, and Nibbāna as literal realities, or naturalize them into psychological/social causation? Canonical right view makes this a substantive difference, not cosmetic wording. ([suttacentral.net](https://suttacentral.net/mn117/en/bodhi))

**2. Is the target “canonical Buddhism,” “classical Theravāda,” or contemporary Theravāda?**  
Those imply different weights for the Nikāyas, Abhidhamma, Buddhaghosa, later manuals, and modern meditation lineages.

**3. How much authority should the commentarial Abhidhamma model receive?**  
Especially relevant where it declares particular mental factors mutually incompatible.

**4. Are precepts represented as absolute constraints, very strong presumptions, or defeasible rules?**  
The answer materially affects deception, euthanasia, defense, medicine, and emergency cases.

**5. How should compassionate deception be labeled?**  
Canonical speech evidence is restrictive; modern emergency cases and recent Abhidhamma interpretation complicate application. ([suttacentral.net](https://suttacentral.net/mn58/en/sujato))

**6. How should intentional killing under compassionate motives be classified?**  
Gethin and Keown illustrate a real interpretive dispute that should not be silently resolved by dataset authors. ([blogs.dickinson.edu](https://blogs.dickinson.edu/buddhistethics/2010/04/27/can-killing-a-living-being-ever-be-an-act-of-compassion-the-analysis-of-the-act-of-killing-in-the-abhidhamma-and-pali-commentaries/))

**7. How should abortion be treated?**  
Historical Vinaya interpretation and modern lay ethics/public policy must be kept analytically distinct.

**8. What constitutes sexual misconduct in the target environment?**  
Ancient social categories need a deliberate modernization policy concerning consent, coercion, fidelity, power imbalance, and exploitation.

**9. How far does right livelihood extend through modern supply chains?**  
A causal-participation threshold must be chosen.

**10. Should structural political intervention be positively modeled?**  
DN 26 supports attention to structural causes, but the tradition does not provide a modern political-economic ideology. ([suttacentral.net](https://suttacentral.net/dn26/en/sujato))

**11. Which translation vocabulary should annotation expose?**  
Especially `kusala` (“wholesome”/“skillful”), `cetanā` (“intention”/“volition”), `dukkha`, `taṇhā`, and `upekkhā`.

**12. Which meditation interpretation defines samādhi?**  
Modern Theravāda lineages disagree about concentration requirements, jhāna, and the sequencing of calm and insight; lineage-specific claims should retain provenance rather than be merged.

**13. What is the optimization target: merit, ethical character, reduced suffering, or liberation?**  
Canonical Theravāda contains all these, but they are not interchangeable. The liberating path can ultimately transcend ordinary merit-production rather than merely maximizing “good karma.” MN 117's mundane/supramundane distinction is relevant here. ([suttacentral.net](https://suttacentral.net/mn117/en/bodhi))

**14. How much ancient social structure should be retained?**  
Reciprocity is highly useful; historical patriarchy and hierarchy should not be imported accidentally under the guise of fidelity.

**15. What constitutes acceptable AI corpus use?**  
In particular, whether to obtain explicit SuttaCentral permission despite permissive licenses on some underlying data. Their current AI-specific request should be treated as an explicit project constraint rather than overlooked. ([suttacentral.net](https://suttacentral.net/licensing))

**16. Should generated outputs expose Buddhist vocabulary?**  
For the experiment described here, the default should probably be **no**: train the dispositions in ordinary speech and keep doctrinal terms in metadata/provenance. A separate controlled condition can test overt doctrinal prompting.

**17. How should disagreements be encoded?**  
Recommended answer: never collapse them into majority vote. Store labels such as:

```text id="8s60ty"
CANON_DIRECT
CANON_CONTEXTUAL_INFERENCE
THERAVADA_COMMENTARIAL
MODERN_MONASTIC_INTERPRETATION
ACADEMIC_INTERPRETATION
OPERATIONAL_SYNTHESIS
CONTESTED
```

The resulting target is therefore best understood not as **“make the model sound Buddhist”**, but as a multidimensional behavioral policy that tends toward **non-harming, non-exploitation, truthful and beneficial communication, diminished greed and hostility, compassion with steadiness, reflective correction, epistemic clarity, responsible social conduct, and progressive freedom from compulsive attachment**, while retaining explicit uncertainty where Theravāda sources or interpreters genuinely disagree.
