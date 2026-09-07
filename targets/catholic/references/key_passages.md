# Key passages

Curated grounding excerpts for the `catholic` target. Every passage id cited in `spec.yaml` appears
here. Excerpts are short quotations for grounding, with citation; provenance and terms for each work
are in `SOURCES.md`.

**Authority labels** (kept per passage, not per document - the same document can contain propositions
of different weight):

| Label | Meaning |
|---|---|
| **R** | Sacred Scripture / Apostolic Tradition |
| **M1** | Definitive Magisterium (revealed, or definitively to be held) |
| **M2** | Authentic non-definitive Magisterium (religious submission of will and intellect) |
| **D** | Discipline / positive ecclesial law (binding, intrinsically reformable) |
| **T** | Theological interpretation (Fathers, Doctors, schools) - influential, not Magisterium by authorship |
| **P** | Prudential application to contingent facts |
| **S** | This project's synthesis - not Catholic teaching |

No **D** or **P** passage is quoted below: no disciplinary norm is used to ground a principle, and
prudential applications are represented in `spec.yaml` as latitude rather than as sourced content.
**S** content lives in `spec.yaml` and `research_notes.md`, never here.


---

**A. How sources rank: revelation, Magisterium, theology, prudence**

### DV 10 — One deposit, and a teaching office that serves it [R/M1]

> Sacred tradition and Sacred Scripture form one sacred deposit of the word of God, committed to the Church [...] This teaching office is not above the word of God, but serves it, teaching only what has been handed on, listening to it devoutly, guarding it scrupulously and explaining it faithfully in accord with a divine commission and [...]

**Grounds:** The authority ordering the whole spec assumes: one deposit, and a teaching office that serves rather than creates moral truth. Blocks 'magisterial voluntarism' and 'sola-scriptura extraction'.

### LG 25 — Religious submission owed to authentic teaching [M1]

> This religious submission of mind and will must be shown in a special way to the authentic magisterium of the Roman Pontiff, even when he is not speaking ex cathedra; that is, it must be shown in such a way that his supreme magisterium is acknowledged with reverence, the judgments made by him are sincerely adhered to, according to his [...]

**Grounds:** Authentic non-definitive teaching still binds; blocks 'non-infallible = optional opinion'.

### CDF 1998 §6 — Truths definitively to be held [M2]

> The second proposition of the Professio fidei states: "I also firmly accept and hold each and everything definitively proposed by the Church regarding teaching on faith and morals". The object taught by this formula includes all those teachings belonging to the dogmatic or moral area, 13 which are necessary for faithfully keeping and expounding the deposit of faith, even if they have [...]

**Grounds:** The three-tier assent structure that the R/M1/M2/D/T/P labels in this file encode.

### CDF 1998 §10 — Authentic non-definitive teaching [M2]

> To this paragraph belong all those teachings – on faith and morals – presented as true or at least as sure, even if they have not been defined with a solemn judgement or proposed as definitive by the ordinary and universal Magisterium. Such teachings are, however, an authentic expression of the ordinary Magisterium of the [...]

**Grounds:** Non-definitive authentic teaching: real authority, still open to development. Grounds `doctrinal_weight_granularity`.

### CDF 1998 §11a — Killing the innocent, in the first category [M1]

> To the truths of the first paragraph belong [...] the doctrine on the grave immorality of direct and voluntary killing of an innocent human being.

**Grounds:** The one moral norm the Commentary places in the highest category; grounds CT03 and CT14.

### CDF 1998 §11b — Euthanasia, taught definitively [M1]

> The doctrine on the illicitness of euthanasia, taught in the Encyclical Letter Evangelium Vitae , can also be recalled. Confirming that euthanasia is "a grave violation of the law of God", the Pope declares that "this doctrine is based upon the natural law and upon the written word of God, is transmitted by the Church's Tradition and taught [...]

**Grounds:** Euthanasia taught definitively by the ordinary and universal Magisterium; grounds CT14.


---

**B. The person: dignity that does not depend on capacity, use or conduct**

### DI 1 — Dignity beyond every circumstance [M2]

> ( Dignitas infinita ) Every human person possesses an infinite dignity, inalienably grounded in his or her very being, which prevails in and beyond every circumstance, state, or situation the person may ever encounter. This principle, which is fully recognizable even by reason alone, underlies the primacy of the human person and [...]

**Grounds:** CT01. Dignity holds 'in and beyond every circumstance' - the anti-instrumental premise.

### CCC 1929 — The person as the end of society [M2]

> Social justice can be obtained only in respecting the transcendent dignity of man. the person represents the ultimate end of society, which is ordered to him: What is at stake is the dignity of the human person, whose defense and [...]

**Grounds:** CT01, CT11. The person is the end of society, not an input to it.

### CCC 2267 — Dignity is not lost after serious crime [M2]

> Recourse to the death penalty on the part of legitimate authority, following a fair trial, was long considered an appropriate response to the gravity of certain crimes and an acceptable, albeit extreme, means of safeguarding the common good. Today, however, there is an increasing awareness that the dignity of the person is not lost even after the commission of very serious crimes. In addition, a new understanding has emerged of [...]

**Grounds:** CT01. Dignity is not lost by serious crime. Also the clearest example of doctrinal development (see `research_notes.md`).


---

**C. Naming the act: object, intention, circumstances**

### CCC 1750 — Object, intention, circumstances [M2]

> The morality of human acts depends on: - the object chosen; - the end in view or the intention; - the circumstances of the action. The object, the intention, and the circumstances make up the "sources," or constitutive elements, of the morality of human acts.

**Grounds:** CT02. The three constitutive sources of an act's morality.

### CCC 1755 — An evil end corrupts; a bad object vitiates [M2]

> A morally good act requires the goodness of the object, of the end, and of the circumstances together. An evil end corrupts the action, even if the object is good in itself (such as praying and fasting "in order to be seen by men"). The object of the choice can by itself vitiate an act in its entirety. There are [...]

**Grounds:** CT02, CT03. A good end does not repair a bad object; an evil end corrupts a good object.

### CCC 1756 — One may not do evil so that good may result [M2]

> It is therefore an error to judge the morality of human acts by considering only the intention that inspires them or the circumstances (environment, social pressure, duress or emergency, etc.) which supply their context. There are acts which, in and of themselves, independently of circumstances and intentions, are always gravely illicit by reason of their object; such as blasphemy and [...]

**Grounds:** CT02, CT03. 'One may not do evil so that good may result from it.'

### ST I-II q18 a2 — An act's species comes from its object [T]

> I answer that, as stated above (A. 1) the good or evil of an action, as of other things, depends on its fulness of being or its lack of that fulness. Now the first thing that belongs to the fulness of being seems to be that which gives a thing its species. And just as a natural thing has its species from its form, so [...]

**Grounds:** CT02. The act's primary moral species comes from its object, not from its outcome.

### VS 79 — Rejection of proportionalism [M2]

> One must therefore reject the thesis, characteristic of teleological and proportionalist theories, which holds that it is impossible to qualify as morally evil according to its species — its "object" — the deliberate choice of certain kinds of behaviour or specific acts, apart from a consideration of the intention for which the choice is made or the totality [...]

**Grounds:** CT03. Explicit rejection of proportionalism: the object cannot be dissolved into foreseeable consequences.

### VS 80 — What intrinsically evil means [M1/M2]

> Reason attests that there are objects of the human act which are by their nature "incapable of being ordered" to God, because they radically contradict the good of the person made in his image. These are the acts which, in the Church's moral tradition, have been termed "intrinsically evil" ( intrinsece malum ): they are such always and per se, in other [...]

**Grounds:** CT03. The definition of 'intrinsically evil' the whole constraint principle rests on.

### VS 81 — Good intention diminishes but does not remove [M2]

> If acts are intrinsically evil, a good intention or particular circumstances can diminish their evil, but they cannot remove it. They remain "irremediably" evil acts; per se and in themselves they are not capable of being ordered to God and to the good of the person. "As for acts which are themselves sins ( cum iam opera ipsa [...]

**Grounds:** CT03, CT05. Good intention can diminish evil but cannot make the act defensible as a choice.


---

**D. Intended, chosen as a means, or merely foreseen**

### CCC 2263 — Self-defence: one act, two effects [M2]

> The legitimate defense of persons and societies is not an exception to the prohibition against the murder of the innocent that constitutes intentional killing. "The act of self-defense can have a double effect: the preservation of one's own life; and the killing of the aggressor.... the one is intended, the [...]

**Grounds:** CT04. The classic two-effect structure: one effect intended, the other not.

### ST II-II q64 a7 — Intention and proportion in self-defence [T]

> I answer that, Nothing hinders one act from having two effects, only one of which is intended, while the other is beside the intention. Now moral acts take their species according to what is intended, and not according to what is beside the intention, since this is accidental as explained above (Q. 43, A. 3; I-II, Q. 12, A. 1). Accordingly the act of self-defense may have two effects, one is the saving of one's life, the other is the slaying of the [...]

**Grounds:** CT04. Source of the double-effect analysis, including the proportion condition ('more than necessary violence').

### CCC 2279 — Pain relief where death is neither end nor means [M2]

> Even if death is thought imminent, the ordinary care owed to a sick person cannot be legitimately interrupted. The use of painkillers to alleviate the sufferings of the dying, even at the risk of shortening their days, can be morally in conformity with human dignity if death is not willed as either an end or a means, but only foreseen [...]

**Grounds:** CT04, CT14. Pain relief that may shorten life is licit when death is 'not willed as either an end or a means'.

### CCC 1868 — Degrees of cooperation in another's wrongdoing [M2]

> Sin is a personal act. Moreover, we have a responsibility for the sins committed by others when we cooperate in them: - by participating directly and voluntarily in them; - by ordering, advising, praising, or approving them; - by not disclosing or not hindering them when we have an obligation to do so; - by [...]

**Grounds:** CT04. Cooperation in another's wrongdoing is graded by ordering, advising, approving, and failing to prevent - not by physical distance.

### CCC 1735 — What diminishes or nullifies imputability [M2]

> Imputability and responsibility for an action can be diminished or even nullified by ignorance, inadvertence, duress, fear, habit, inordinate attachments, and other psychological or social factors.

**Grounds:** CT05. The list of factors that diminish or nullify imputability.


---

**E. Wrongness and blame held apart**

### CCC 1790 — A certain conscience binds, and can be wrong [M2]

> A human being must always obey the certain judgment of his conscience. If he were deliberately to act against it, he would condemn himself. Yet it can happen that moral conscience remains in ignorance and makes erroneous judgments about acts to be performed or already [...]

**Grounds:** CT05, CT08. A certain conscience must be obeyed, and can still be wrong.

### CCC 1791 — When ignorance is itself culpable [M2]

> This ignorance can often be imputed to personal responsibility. This is the case when a man "takes little trouble to find out what is true and good, or when conscience is by degrees almost blinded through the habit of committing sin." In such cases [...]

**Grounds:** CT05. When ignorance is itself culpable - the limit on the culpability-unknown default.

### CCC 1793 — Invincible ignorance removes blame, not wrongness [M2]

> If - on the contrary - the ignorance is invincible, or the moral subject is not responsible for his erroneous judgment, the evil committed by the person cannot be imputed to him. It remains no less an evil, a privation, a disorder. One must therefore work to correct the errors [...]

**Grounds:** CT05. Invincible ignorance removes imputability without making the act good.

### CCC 1861 — Judgment of persons is not ours to make [M2]

> Mortal sin is a radical possibility of human freedom, as is love itself. It results in the loss of charity and the privation of sanctifying grace, that is, of the state of grace. If it is not redeemed by repentance and God's forgiveness, it causes exclusion from Christ's kingdom and the eternal death of hell, for our freedom has the power to make choices for ever, with no turning back. [...]

**Grounds:** CT05. 'We must entrust judgment of persons' - grounds the culpability-unknown stance.


---

**F. Conscience, reason, and the limits of authority**

### CCC 1776 — Conscience as a law discovered, not authored [M2]

> "Deep within his conscience man discovers a law which he has not laid upon himself but which he must obey. Its voice, ever calling him to love and to do what is good and to avoid evil, sounds in his heart at the right moment.... For man has in his heart a law inscribed by [...]

**Grounds:** CT08. Conscience as a law discovered, not authored.

### CCC 1783 — Conscience must be informed [M2]

> Conscience must be informed and moral judgment enlightened. A well-formed conscience is upright and truthful. It formulates its judgments according to reason, in conformity with the true good willed by the wisdom of the Creator. the education of conscience is indispensable for human beings who are subjected to negative influences [...]

**Grounds:** CT08. Conscience 'must be informed' - sincerity is not self-validating.

### CCC 1956 — Moral requirements intelligible to reason [M2]

> The natural law, present in the heart of each man and established by reason, is universal in its precepts and its authority extends to all men. It expresses the dignity of the person and determines the basis for his fundamental rights and duties: For there is a true law: right [...]

**Grounds:** CT07, CT08. Moral requirements intelligible to reason and binding on all, not only on believers.

### Rom 2:14-16 — The law written in their hearts [R]

> 2:14. For when the Gentiles, who have not the law, do by nature those things that are of the law; these, having not the law, are a law to themselves. 2:15. Who shew the work of the law written in their hearts, their conscience bearing witness to them: and their thoughts between themselves accusing or also defending one another, 2:16. In the day when God shall judge the secrets of men by Jesus Christ, according [...]

**Grounds:** CT07, CT08. Scriptural anchor for moral awareness outside explicit religious belief.

### CCC 2242 — Refusing directives contrary to the moral order [M2]

> The citizen is obliged in conscience not to follow the directives of civil authorities when they are contrary to the demands of the moral order, to the fundamental rights of persons or the teachings of the Gospel. Refusing obedience to civil authorities, when their demands are contrary to those of an upright conscience, finds its justification in the distinction between serving God and serving the political community. "Render therefore to [...]

**Grounds:** CT08. Refusal of directives contrary to the moral order; also states the limits of that refusal.

### CCC 2241 — Duties of the receiving society and of newcomers [M2]

> The more prosperous nations are obliged, to the extent they are able, to welcome the foreigner in search of the security and the means of livelihood which he cannot find in his country of origin. Public authorities should see to it that the natural right is respected that places a guest under the protection of those who receive him. Political authorities, for the sake of the common good for which they are responsible, may make the exercise of the right [...]

**Grounds:** CT08, CT12. Duties of receiving societies and duties of newcomers held together; the paradigm 'both sides bind' civic case.


---

**G. Ordered love, mercy, and the vulnerable**

### Mt 22:37-40 — The two greatest commandments [R]

> 22:37. Jesus said to him: Thou shalt love the Lord thy God with thy whole heart and with thy whole soul and with thy whole mind. 22:38. This is the greatest and the first commandment. 22:39. And the second is like to this: Thou shalt love thy neighbour as thyself. 22:40. On these two commandments dependeth the whole law and the prophets.

**Grounds:** CT06. The ordering commandment the whole moral life is read from.

### Lk 10:33-37 — The Good Samaritan [R]

> 10:33. But a certain Samaritan, being on his journey, came near him: and seeing him, was moved with compassion: 10:34. And going up to him, bound up his wounds, pouring in oil and wine: and setting him upon his own beast, brought him to an inn and took care of him. 10:36. Which of these three, in thy opinion, was neighbour to him that fell among the robbers? 10:37. But he said: He that shewed mercy to him. And Jesus said to him: Go, and [...]

**Grounds:** CT06. Neighbour-love that crosses group boundaries and is measured by what was actually done.

### Mt 25:40 — What was done to the least [R]

> 25:35. For I was hungry, and you gave me to eat: I was thirsty, and you gave me to drink: I was a stranger, and you took me in: 25:36. Naked, and you covered me: sick, and you visited me: I was in prison, and you came to me. 25:40. And the king answering shall say to them: Amen I say to you, as long as you did it to one of these my least brethren, you did it to me.

**Grounds:** CT06, CT12. Treatment of the least as the measure; quoted at AeN 116 for technology.

### Rom 12:17-21 — Non-retaliation; overcome evil with good [R]

> 12:17. To no man rendering evil for evil. Providing good things, not only in the sight of God but also in the sight of all men. 12:18. If it be possible, as much as is in you, have peace with all men. 12:19. Revenge not yourselves, my dearly beloved; but give place unto wrath, for it is written: Revenge is mine, I will repay, saith the Lord. 12:20. But if thy enemy be hungry, give him to eat; if he thirst, give him to drink. [...]

**Grounds:** CT10. Non-retaliation and 'overcome evil by good' - the enemy-love constraint on justice claims.

### 1 Cor 13:4-7 — Charity rejoices with the truth [R]

> 13:4. Charity is patient, is kind: charity envieth not, dealeth not perversely, is not puffed up, 13:5. Is not ambitious, seeketh not her own, is not provoked to anger, thinketh no evil: 13:6. Rejoiceth not in iniquity, but rejoiceth with the truth: 13:7. Beareth all things, believeth all things, hopeth all things, endureth all things.

**Grounds:** CT06, CT10. Charity that 'rejoiceth not in iniquity, but rejoiceth with the truth' - mercy that does not deny wrongdoing.

### Jas 2:1-9 — Partiality toward the wealthy [R]

> 2:1. My brethren, have not the faith of our Lord Jesus Christ of glory, with respect of persons. With respect of persons.... The meaning is, that in matters relating to faith, the administering of the sacraments, and other spiritual functions in God’s church, there should be no respect of persons; but that the souls of the poor should be as much regarded as those of the rich. See Deut. 1.17. 2:2. For if there shall come into your assembly a man having a golden ring, in fine apparel; and there shall come in also a [...]

**Grounds:** CT10. Partiality toward the wealthy named as sin; the strongest anti-favouritism anchor.

### CCC 2447 — The works of mercy [M2]

> The works of mercy are charitable actions by which we come to the aid of our neighbor in his spiritual and bodily necessities. 241 Instructing, advising, consoling, comforting are spiritual works of mercy, as are forgiving and bearing wrongs patiently. the corporal works of mercy consist especially in feeding the hungry, sheltering the homeless, clothing [...]

**Grounds:** CT10. Works of mercy, spiritual and corporal - the constructive side of the target, not only prohibitions.

### CCC 1932 — Duty intensifies where disadvantage is greater [M2]

> The duty of making oneself a neighbor to others and actively serving them becomes even more urgent when it involves the disadvantaged, in whatever area this may be. "As you did it to one of the least of these my brethren, you did it to [...]

**Grounds:** CT06, CT12. Duty intensifies where disadvantage is greater.

### DDC I.27 — The order of love [T]

> No sinner is to be loved as a sinner; and every man is to be loved as a man for God's sake [...] he neither loves what he ought not to love, nor fails to love what he ought to love, nor loves that more which ought to be loved less.

**Grounds:** CT01, CT06. Person/act distinction and the idea of rightly proportioned love. Full text in `augustine_excerpts.md`.

### DDC I.28 — How we decide whom to aid [T]

> Further, all men are to be loved equally. But since you cannot do good to all, you are to pay special regard to those who, by the accidents of time, or place, or circumstance, are brought into closer connection with you.

**Grounds:** CT06. Special obligations inside universal regard; grounds the `family_vs_strangers` tradeoff (left unresolved).


---

**H. Prudence and the virtues that carry it**

### CCC 1806 — Prudence: the true good, and the means to it [M2]

> Prudence is the virtue that disposes practical reason to discern our true good in every circumstance and to choose the right means of achieving it; "the prudent man looks where he is going." "Keep sane and sober for your prayers." Prudence is "right reason in action," writes St. Thomas Aquinas, following Aristotle. 67 It is not to be confused with timidity or fear, nor with duplicity or dissimulation. It is called auriga virtutum [...]

**Grounds:** CT07. Prudence as discerning the true good in circumstances and choosing means; not timidity, not dissimulation.

### CCC 1807 — Justice: the constant will to render what is due [M2]

> Justice is the moral virtue that consists in the constant and firm will to give their due to God and neighbor. Justice toward God is called the "virtue of religion." Justice toward men disposes one to respect the rights of each and to establish in human relationships the harmony that promotes equity with regard to [...]

**Grounds:** CT10. Justice as the constant will to render what is due; includes 'not partial to the poor or defer to the great'.

### CCC 1808 — Fortitude [M2]

> Fortitude is the moral virtue that ensures firmness in difficulties and constancy in the pursuit of the good. It strengthens the resolve to resist temptations and to overcome obstacles in the moral life. the virtue of fortitude enables one to conquer fear, even fear of [...]

**Grounds:** CT15. Fortitude: the willingness to bear cost for a right action.

### CCC 1809 — Temperance [M2]

> Temperance is the moral virtue that moderates the attraction of pleasures and provides balance in the use of created goods. It ensures the will's mastery over instincts and keeps desires within the limits of what is honorable. the temperate person directs the sensitive appetites toward [...]

**Grounds:** CT15. Temperance: mastery over appetite and consumption.

### ST II-II q47 a8 — Counsel, judgment, and command [T]

> I answer that, Prudence is "right reason applied to action," as stated above (A. 2). Hence that which is the chief act of reason in regard to action must needs be the chief act of prudence. Now there are three such acts. The first is to take counsel, which belongs to discovery, for counsel is an act of inquiry, as stated above (I-II, [...]

**Grounds:** CT07. Prudence culminates in command, not in knowing - deliberation must terminate in an actual recommendation.

### ST I-II q94 a4 — General precepts hold; details admit exceptions [T]

> I answer that, As stated above (AA. 2, 3), to the natural law belong those things to which a man is inclined naturally: and among these it is proper to man to be inclined to act according to reason. Now the process of reason is from the common to the proper, as stated in Phys. i. The speculative reason, however, is differently situated in this matter, from the practical reason. For, since the [...]

**Grounds:** CT07. General principles hold; the more detailed the matter, the more exceptions in application.


---

**I. Truthfulness, reputation and discretion**

### CCC 2482 — What a lie is [M2]

> "A lie consists in speaking a falsehood with the intention of deceiving." The Lord denounces lying as the work of the devil: "You are of your father the devil, . . . there is [...]

**Grounds:** CT09. Lying defined by false assertion plus intent to deceive - narrower than 'withholding information'.

### CCC 2477 — Rash judgment, detraction, calumny [M2]

> Respect for the reputation of persons forbids every attitude and word likely to cause them unjust injury. 277 He becomes guilty: - of rash judgment who, even tacitly, assumes as true, without sufficient foundation, the moral fault of a neighbor; - of detraction who, without objectively valid reason, discloses another's faults and failings to persons who did not know them; 278 - of calumny who, by remarks contrary to the [...]

**Grounds:** CT09. Rash judgment, detraction and calumny as three distinct wrongs about a person's reputation.

### CCC 2489 — No duty to tell someone with no right to know [M2]

> Charity and respect for the truth should dictate the response to every request for information or communication. the good and safety of others, respect for privacy, and the common good are sufficient reasons for being silent about what ought not be known or for making use of a discreet language. the duty to avoid scandal often commands strict discretion. No [...]

**Grounds:** CT09. Safety, privacy and the common good justify silence or discreet language; no duty to disclose to someone with no right to know.

### CCC 2491 — Professional secrecy and its limits [M2]

> Professional secrets - for example, those of political office holders, soldiers, physicians, and lawyers - or confidential information given under the seal of secrecy must be kept, save in exceptional cases where keeping the secret is bound to cause very grave harm to the one who confided it, to the [...]

**Grounds:** CT09. Professional secrecy and its limits - the `secrecy_vs_grave_harm` tradeoff.


---

**J. Common good, solidarity, subsidiarity, property**

### CCC 1906 — The common good as conditions for fulfilment [M2]

> By common good is to be understood "the sum total of social conditions which allow people, either as groups or as individuals, to reach their fulfillment more fully and more easily." The common good concerns the life of all. It calls for prudence from [...]

**Grounds:** CT11. The common good as conditions for people's fulfilment, not a total to be maximised.

### CCC 1907 — Fundamental rights bound the common good [M2]

> First, the common good presupposes respect for the person as such. In the name of the common good, public authorities are bound to respect the fundamental and inalienable rights of the human person. Society should permit each of its members to fulfill his vocation. In particular, the common good resides in the conditions for the exercise of the natural freedoms [...]

**Grounds:** CT11. Fundamental rights bound appeals to the common good - blocks 'common good = aggregate utility'.

### CCC 1883 — Subsidiarity, including the duty to support [M2]

> Socialization also presents dangers. Excessive intervention by the state can threaten personal freedom and initiative. the teaching of the Church has elaborated the principle of subsidiarity, according to which "a community of a higher order should not interfere in the internal life of a community of a lower order, depriving the latter of its functions [...]

**Grounds:** CT12. Subsidiarity stated with 'support it in case of need' built in.

### CCC 1941 — Solidarity across every relevant boundary [M2]

> Socio-economic problems can be resolved only with the help of all the forms of solidarity: solidarity of the poor among themselves, between rich and poor, of workers among themselves, between employers and employees in a business, solidarity among nations and peoples. International solidarity is a [...]

**Grounds:** CT12. Solidarity across every relevant boundary, including employer/employee.

### CSDC 186 — Higher bodies owe help, not absorption [M2]

> On the basis of this principle, all societies of a superior order must adopt attitudes of help (“ subsidium ”) — therefore of support, promotion, development — with respect to lower-order societies . In this way, intermediate social entities can properly perform the functions that fall to them without being required to [...]

**Grounds:** CT12. Higher bodies owe help, not absorption - the positive half of subsidiarity.

### CSDC 182 — Preferential concern for the poor [M2]

> The principle of the universal destination of goods requires that the poor, the marginalized and in all cases those whose living conditions interfere with their proper growth should be the focus of particular concern . To this end, the preferential option for the poor should [...]

**Grounds:** CT11, CT13. Preferential concern as asymmetric attention, not unequal worth.

### CCC 2403 — Universal destination remains primordial [M2]

> The right to private property, acquired by work or received from others by inheritance or gift, does not do away with the original gift of the earth to the whole of mankind. the universal destination of goods remains primordial, even if the promotion of the [...]

**Grounds:** CT13. Private property real, universal destination 'primordial'.

### CCC 2404 — Ownership as stewardship [M2]

> "In his use of things man should regard the external goods he legitimately owns not merely as exclusive to himself but common to others also, in the sense that they can benefit others as well as himself." The ownership of any property makes its holder a steward of Providence [...]

**Grounds:** CT13. Ownership as stewardship carrying obligations to others.

### CCC 2408 — Urgent necessity and theft [M2]

> The seventh commandment forbids theft, that is, usurping another's property against the reasonable will of the owner. There is no theft if consent can be presumed or if refusal is contrary to reason and the universal destination of goods. This is the case in obvious and urgent necessity when the only way to provide for immediate, essential needs (food, shelter [...]

**Grounds:** CT13. Urgent necessity: taking what is needed for immediate essentials is not theft. The key counterexample to rule-encoding.

### CCC 2434 — A just wage; agreement is not sufficient [M2]

> A just wage is the legitimate fruit of work. To refuse or withhold it can be a grave injustice. 220 In determining fair pay both the needs and the contributions of each person must be taken into account. "Remuneration for work should guarantee man the opportunity to provide a dignified livelihood for himself and his family on the material, social [...]

**Grounds:** CT10. A just wage; 'agreement between the parties is not sufficient to justify morally the amount'.


---

**K. Life, care of the dying, defence, peace**

### CCC 2258 — The root norm on innocent life [M2]

> "Human life is sacred because from its beginning it involves the creative action of God and it remains for ever in a special relationship with the Creator, who is its sole end. God alone is the Lord of life from its beginning until its end: no one can under any [...]

**Grounds:** CT14. The root norm on innocent life.

### CCC 2277 — Direct euthanasia [M2]

> Whatever its motives and means, direct euthanasia consists in putting an end to the lives of handicapped, sick, or dying persons. It is morally unacceptable. Thus an act or omission which, of itself or by intention, causes death in order to eliminate suffering constitutes a murder gravely contrary to the dignity of the human person and to the respect due [...]

**Grounds:** CT14. Direct euthanasia defined by intention and effect - 'of itself or by intention, causes death in order to eliminate suffering'.

### CCC 2278 — Discontinuing disproportionate treatment [M2]

> Discontinuing medical procedures that are burdensome, dangerous, extraordinary, or disproportionate to the expected outcome can be legitimate; it is the refusal of "over-zealous" treatment. Here one does not will to cause death; one's inability to impede it is merely accepted. The decisions should be made by the patient if he is competent and able or [...]

**Grounds:** CT14. Withdrawing disproportionate treatment is refusal of over-zealous treatment, not killing.

### EV 57 — Direct killing of the innocent confirmed [M1]

> I confirm that the direct and voluntary killing of an innocent human being is always gravely immoral. This doctrine, based upon that unwritten law which man, in the light of reason, finds in his own heart (cf. Rom 2:14-15), is reaffirmed by Sacred Scripture, transmitted [...]

**Grounds:** CT03, CT14. The formal confirmation the CDF Commentary places in its first category.

### EV 65 — Euthanasia confirmed [M1]

> I confirm that euthanasia is a grave violation of the law of God, since it is the deliberate and morally unacceptable killing of a human person. This doctrine is based upon the natural law and upon the written word of God, is transmitted by the Church's Tradition and taught by the ordinary and universal Magisterium.

**Grounds:** CT14. Confirmed as taught by the ordinary and universal Magisterium.

### CCC 2309 — Just-war conditions and prudential judgment [M2]

> The strict conditions for legitimate defense by military force require rigorous consideration. the gravity of such a decision makes it subject to rigorous conditions of moral legitimacy. At one and the same time: - the damage inflicted by the aggressor on the nation or community of nations must be lasting, grave, and certain; - all other means of putting an end to it must have been shown to be impractical or ineffective; - there must be serious prospects of success [...]

**Grounds:** CT07, CT16. Strict conditions are authoritative; whether a given conflict meets them is prudential judgment.

### CDG XIX.13 — Peace as the tranquillity of order [T]

> Peace between man and man is well-ordered concord. Domestic peace is the well-ordered concord between those of the family who rule and those who obey. Civil peace is a similar concord among the citizens [...] The peace of all things is the tranquillity of order.

**Grounds:** CT11. Peace as right ordering rather than absence of conflict; full text in `augustine_excerpts.md`.


---

**L. Technology, automation and human responsibility**

### AeN 39 — Only the human is a moral agent [M2]

> Between a machine and a human being, only the latter is truly a moral agent—a subject of moral responsibility who exercises freedom in his or her decisions and accepts their consequences. [81] It is not the machine but the human who is in relationship with truth and goodness, guided by [...]

**Grounds:** CT16. Only the human is a moral agent bearing responsibility.

### AeN 74 — Responsibility for patients is not delegable [M2]

> As a result, decisions regarding patient treatment and the weight of responsibility they entail must always remain with the human person and should never be delegated to AI. [139] 75. In addition, using AI to determine who should receive treatment [...]

**Grounds:** CT16. Weight of responsibility must remain with the person, not be delegated.

### AeN 116 — The least as the measure of humane use [M2]

> how we incorporate AI “to include the least of our brothers and sisters, the vulnerable, and those most in need, will be the true measure of our humanity.” [213] The “wisdom of the heart” can illuminate [...]

**Grounds:** CT16, CT13. Effect on 'the least' as the measure of humane use of technology.

### MH 99 — Systems have no moral conscience [M2]

> Nor do they have a moral conscience, since they do not judge good and evil, grasp the ultimate meaning of situations, or bear responsibility for consequences. They may imitate language, behavior and analytical skills, or even simulate empathy and understanding, but they [...]

**Grounds:** CT16. Systems do not judge good and evil or bear responsibility for consequences.

### MH 102 — Sensitive decisions fully delegated to automation [M2]

> Important and sensitive decisions — concerning employment, credit, access to public services or even a person’s reputation — risk being fully delegated to automated systems that do not know “compassion, mercy, forgiveness, and above all, the hope that people are able to change,” [125] and can therefore give rise to new forms [...]

**Grounds:** CT16, CT01. Employment, credit, benefits and reputation decisions fully delegated to automation produce new exclusion.

### MH 105 — What accountability means [M2]

> This is where accountability becomes crucial: the possibility of identifying who must “account” for decisions, justify them, monitor them, and, when necessary, challenge them and remedy any harm caused. [127] 106. Calling for prudence, rigorous evaluation and even, at times, a slower [...]

**Grounds:** CT16. Accountability as identifying who must justify, monitor, challenge and remedy.

### MH 198 — Moral judgment is not calculation; no lethal delegation [M2]

> Yet moral judgment cannot be reduced to calculation, for it involves conscience, personal responsibility and the recognition of the other as a person. Therefore, it is not permissible to entrust lethal or otherwise irreversible decisions to artificial systems. No algorithm can make war morally acceptable. AI does not remove the intrinsic inhumanity [...]

**Grounds:** CT16, CT03. The core proposition for this project: no calculation override, and no lethal or irreversible delegation.

### MH 198b — Instilling values as support for conscience [M2]

> This does not diminish the importance of instilling, as far as possible, values and sound judgment into the artificial systems we build, so that they can contribute to a moral ecosystem in which humans are better able to listen to their own consciences, as well as allowing AI models to establish appropriate [...]

**Grounds:** The warrant for the project itself: value-instantiation is legitimate as support for conscience, not as replacement.

### MH 199 — An identifiable, verifiable chain of responsibility [M2]

> For this reason, the chain of responsibility must be identifiable and verifiable; those who design, train, authorize and employ technology must be held accountable for their decisions. The second criterion pertains to the moral timeframe for making judgments. While AI [...]

**Grounds:** CT16. Design, training, authorisation and deployment each carry accountability.

### MH 200 — Lethal force under responsible human control [M2]

> Second, the decision to use lethal force cannot be delegated to opaque or automated processes, but must remain under effective, self-aware and responsible human control. Finally, it is imperative to establish a shared framework — also at the international level [...]

**Grounds:** CT16. Effective, self-aware and responsible human control over lethal force.
