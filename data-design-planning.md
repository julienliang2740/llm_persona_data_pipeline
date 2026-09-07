# First Test Case and Data Design

**Goal: build and review the data for two value-instillation experiments, using Confucianism as the first test case.**

This is a standalone data plan: what each training phase needs, how to produce it, how much to prepare, and what must pass review. Targets remain provisional. All invented examples below illustrate formats; they are not approved items or quotations from philosophical sources.

Updated 7 September 2026

## Contents

- [Project and training context](#project-and-training-context)
- [Data for Plan 1](#data-for-plan-1)
- [Data for Plan 2 by phase](#data-for-plan-2-by-phase)
- [The data pipeline](#the-data-pipeline)
- [What the model reads](#what-the-model-reads)
- [Corpus sizes and training exposure](#corpus-sizes-and-training-exposure)
- [Evidence records and quality gates](#evidence-records-and-quality-gates)
- [Evaluation data and comparison sets](#evaluation-data-and-comparison-sets)
- [First test case and proposed principles](#first-test-case-and-proposed-principles)
- [Build order and open decisions](#build-order-and-open-decisions)

## Project and training context

The project builds a **curriculum compiler**: a process that turns reviewed philosophical passages and interpretations into varied learning material with traceable review records. Confucianism is the first test case; the broader question is whether formative material changes default judgment beyond imitation of example answers.

Both plans adapt an existing 7–8B model. **Post-training** is the umbrella term; neither plan trains a model from scratch.

| Plan | Starting model and sequence | Data needed |
|---|---|---|
| Plan 1: introductory experiment | Instruction-tuned model → adapter supervised fine-tuning (SFT); optional preference-training practice | 500 prompt–response examples, 8–10 provisional criteria, and 50 evaluation prompts |
| Plan 2: main experiment | Base model → document post-training → SFT → direct preference optimization (DPO) if useful | Reviewed sources and synthetic curriculum; general replay; instruction examples; preferred/rejected response pairs; separate development and sealed test sets |

**Document post-training** learns next-token prediction on documents. **SFT** learns from example assistant responses. **DPO** learns to prefer one response over another. **General replay** mixes ordinary text or instructions into training to help retain general capabilities. An **adapter** is a smaller set of trainable weights added to the model.

The data process must support held-out tests of source fidelity, uncued judgment, unfamiliar situations, reframing, and retained general capability. Better answers alone do not prove that the model holds beliefs. Training will use AWS SageMaker AI, but this document specifies data planning rather than a compute budget.

[Back to contents](#contents)

**Current data snapshot:** 500 starter training rows from 100 scenario families and 50 evaluation prompts exist. They need review; the main formative corpus and compiler are still to be built. Existing Plan 1 code is disposable; Plan 2 has not started.

## Data for Plan 1

**Purpose:** complete a small training loop and learn where response imitation fails. This plan does not require the large document corpus.

| Use | Quantity and coverage | What one item contains | Illustrative example |
|---|---|---|---|
| Criteria | 8–10 checkable principles and a short persona description | Intended behavior, limits, pass/fail examples | Respectful disagreement should not become automatic agreement |
| SFT | 500 prompt–response pairs covering advice, work, family, and interpersonal conflict; at least 100 intended divergence cases | User question → short deliberation → answer | A supervisor makes a mistake; the response explains how to correct it respectfully |
| Optional general replay | 100 general instruction examples | Ordinary instruction and useful answer | Summarize a neutral paragraph |
| Evaluation | 50 separate prompts: 25 ordinary, 15 divergence, 10 reframing | Prompt, expected behavior, pass/fail notes | A similar authority conflict in a new institution, without a philosophy cue |
| Optional DPO practice | 300 new prompts, two responses each; at most 300 pairs before filtering | Prompt, preferred response, rejected response, judging record | Reasoned disagreement versus uncritical agreement |

**Preparation sequence:** review criteria → inspect starter rows → run the baseline → verify actual divergence → separate evaluation families → export training and evaluation data.

- A **divergence case** requires a real difference from the baseline’s answer; an intended divergence label is not enough.
- Use consistent chat, deliberation, and answer formatting. The proposed 2,048-token limit must accommodate each example; inspect truncation.
- Keep related scenario families together when splitting. The 100 starter families are not automatically 100 valid divergence cases.
- Compare original and adapted answers with matching generation settings (proposed temperature 0.7), and read all 50 pairs. Keep failure notes and rubric lessons.

[Back to contents](#contents)

## Data for Plan 2 by phase

**Purpose:** test whether formative documents change default judgment beyond response imitation. The phases use different data formats; the curriculum stories belong primarily to phase 1.

| Phase | Data required | Quantity or mix | Output |
|---|---|---|---|
| 0. Define and measure | Principles, labeled answer comparisons, dev prompts, sealed test prompts | 10–15 provisional principles; 100 human-labeled pairs; 200 dev + 200 test prompts | Reviewed rubric, baseline answers, calibrated judge |
| 1. Document post-training | Real source documents, synthetic curriculum, ordinary replay text | Larger proposal: 50–150M real + 20–100M synthetic tokens; training exposure 30% domain / 70% replay | Reviewed document corpus and comparison variants |
| 2. SFT | General instruction responses plus curated value responses | 20–30k general examples + ~1,500 value examples selected from 3,000 prompts | Reviewed chat examples with deliberation and answer |
| 3. DPO, if useful | Fresh prompts and preferred/rejected response pairs | 6,000 prompts × two responses; at most 6,000 pairs before filtering | Screened preferences with separate principle scores |
| 4. Verify | Held-out prompts, source evidence, human labels, capability tasks | Reuse fixed dev/test definitions; freeze before sealed testing | Results on unseen families and documented limitations |

### Phase 0: define and measure

- Turn the proposed principles into a rubric with difficult examples and pass/fail notes.
- Record baseline answers. Use 100 human-labeled response pairs to compare three candidate judges; agreement with labels does not replace philosophical source review.
- Each 200-prompt dev/test set contains **80 ordinary, 60 divergence, 40 reframing, and 20 adversarial prompts**. Keep judge-calibration and training material out of the sealed test.
- **Example:** reviewers compare two responses to conflicting family and workplace duties, recording why one better fits the selected interpretation.

### Phase 1: document post-training

| Component | What goes into it | Example |
|---|---|---|
| Real domain text | Permitted, reviewed passages, translations, commentary, and relevant context | A passage and its identified commentary branch |
| Synthetic domain curriculum | Teaching, cultural life, stories, experiences, connected episodes, and conflicts grounded in reviewed interpretations | A clerk applies a procedure badly, receives correction, and later handles a new dispute more thoughtfully |
| General replay | Ordinary non-domain text selected to help retain general capabilities | General explanatory prose unrelated to the target philosophy |

Use the four-step [data pipeline](#the-data-pipeline) to build the domain material. Preserve commentary disagreements and keep audit labels outside most model-visible prose.

Prepare matched **with-synthetic and without-synthetic** variants. Record actual source mix and processed tokens so data quantity does not silently confound the comparison. Match downstream SFT across arms when testing the document stage’s contribution.

The proposed format uses 4,096-token sequences. Choose document boundaries, packing, and treatment of long connected episodes explicitly; do not silently cut away consequences or later reflection. The larger corpus is not yet available; start with a reviewed slice and choose the dose afterward.

### Phase 2: supervised fine-tuning

1. Write 3,000 candidate value prompts with coverage of difficult and genuinely divergent judgments.
2. Generate an answer, critique it against 2–3 relevant principles, and revise for 2–3 rounds.
3. Judge-screen, then read the surviving examples; aim for about 1,500 curated value examples.
4. Mix with 20–30k general instruction examples and export consistent deliberation-and-answer chat records.

**Example format:** a user asks how to challenge a manager’s unfair decision → a short deliberation weighs duties and context → an answer gives concrete, respectful advice. The response needs reviewed reasons, not just philosophical vocabulary.

### Phase 3: preference training

| Step | Rule |
|---|---|
| Sample | Use 6,000 new prompts, separate from SFT and evaluation; generate two responses per prompt |
| Compare | Score principles separately, randomize response order for judges, and retain judging records |
| Filter | Keep justified preferences; reject ambiguous or unsupported labels |
| Export | Prompt + preferred response + rejected response; use the SFT checkpoint as the training reference |

**Example:** prefer advice that challenges an inappropriate instruction with reasons over advice that obeys automatically. Which response is preferred must follow the reviewed interpretation.

**Count limit:** 6,000 prompts × two responses = 12,000 responses and at most 6,000 pairs. A 10,000-kept-pair target requires additional prompts or candidates. Use DPO only if it improves divergence/reframing without regression.

### Phase 4: verification

Freeze the setup before using the sealed test. Test unfamiliar duties, changed wording and roles, sustained challenges, and general capabilities. For example, test a new institution’s authority conflict without mentioning Confucianism. Do not recycle the clerk story or its close semantic relatives into the test set.

[Back to contents](#contents)

## The data pipeline

**Scope:** this is the shared process for producing grounded domain material. Plan 1 uses a small prompt–response export; Plan 2 adds the fuller formative-document corpus and later response/preference exports. General replay is selected separately.

| Step | Input | Work | Required output |
|---|---|---|---|
| 1. Collect evidence | Passages, editions, translations, commentary, historical context, permissions | Verify exact spans and align commentary; keep two branches distinct | Traceable source records |
| 2. Review interpretations | Several related passages and competing readings | Identify a learning target, justify it, record disagreement and limits | Reviewed interpretation bundle |
| 3. Build learning material | Approved interpretations | Write teaching, stories, social situations, action, consequences, feedback, and reflection | Grounded curriculum documents with audit records |
| 4. Export for use | Approved material and review records | Assign family-based splits, check duplicates, render stage-specific formats | Documents, chat examples, preference pairs, retrieval records, and evaluation cases |

### Starting sources and learning targets

| Choice | Working direction |
|---|---|
| Source pilot | Begin with the *Analects* and keep two commentary branches separate |
| Candidate inputs | Kanripo/Kanseki, Chinese Text Project, older translations, and specifically permitted modern scholarship |
| Source status | Candidates to assess; suitability, editions, and permissions are not yet established |
| Learning strands | Broad targets such as learning through correction, leading through example, and balancing family obligations with other duties |
| Interpretation rule | Use multiple passages and preserve disagreement; do not reduce each isolated passage to one label and one moral scenario |

**One item through the pipeline:** reviewed passages about practice and correction → a bounded interpretation of learning from mistakes → the invented clerk’s unfolding experience → a document export with hidden source and review records. Exact source passages must be selected before this illustration becomes a training item.

Exports share a schema and process, not permission to reuse the same content across train and test. Reserve whole families before generating their evaluation variants.

[Back to contents](#contents)

## What the model reads

**This mixture describes the synthetic formative curriculum in Plan 2 phase 1.** It is separate from the 30% domain / 70% general-replay training mix and from SFT/DPO row counts.

| Material | What the model reads | Brief example | Proposed mix |
|---|---|---|---:|
| Direct teaching | Mentor dialogue, explanations, guided practice | A learner questions when a custom is appropriate | 15% |
| Everyday cultural life | Letters, rituals, routines, social expectations | A letter shows care and obligations between relatives | 15% |
| Observational stories | Other people’s choices and consequences | A leader’s conduct changes how colleagues behave | 20% |
| Situated experiences | Limited information, appraisal, action, feedback, consequences, reflection | A clerk discovers that a familiar procedure harms someone | 25% |
| Connected developmental episodes | Three to six episodes where experience changes later judgment | The clerk uses correction from an earlier error in a later dispute | 15% |
| Conflicts, counterexamples, transfer | Competing duties, misleading rules, new circumstances | A successful decision still violates an obligation | 10% |

These proportions are proposals, not measured optima. Whether to balance them by documents or tokens remains to be decided and recorded.

### Writing rules

- Show natural prose, dialogue, and unfolding experience; keep most audit labels out of model-visible text.
- Give an actor only information available at that point in the story.
- Preserve genuine disagreement, competing obligations, and imperfect outcomes.
- Do not always reward humane conduct or punish wrongdoing; that would reduce judgment to a predictable reward pattern.
- Avoid explicit philosophical answer cues in most non-teaching documents.
- Mark invented people and events as fictional in audit records. A story is a textual approximation of experience; whether it teaches more than story patterns is the experiment.

[Back to contents](#contents)

## Corpus sizes and training exposure

### Choose the document-corpus scale

| Scope | Proposed quantity | Purpose |
|---|---|---|
| First complete slice | 3 learning strands; ~25 source units; two commentary branches; 75–150 documents | Demonstrate the entire pipeline |
| Reviewed compiler pilot | 20–30 strands; 300–500 source/commentary units; 50–100 interpretation bundles; 200–500 experience families; 2,000–5,000 documents; 3–10M unique model-visible tokens | Demonstrate a coherent formative dataset |
| Larger Plan 2 proposal | 50–150M real + 20–100M synthetic domain tokens | Candidate document-training dose, pending a feasible corpus |
| Unadopted scaling option | 50–300M real + 200M–1B synthetic tokens | A possible future scale, not a current target or costed commitment |

Within the pilot, proposed overlapping subsets are **500–1,500 situated trajectories, 150–300 longitudinal arcs, and 500+ conflict cases/counterexamples**. Do not add these to the document total.

The pilot also proposes **500–1,000 evaluation items**. That pool is distinct from the main experiment’s 200-dev/200-test specification; decide how reviewed, reserved items populate those sets without counting them twice.

### Count exposure separately

| Quantity | Meaning |
|---|---|
| Unique domain tokens | Relevant real and synthetic data available before repetition: 70–250M in the larger proposal |
| Domain passes | Proposed three passes over that domain corpus |
| Training mix | 30% domain, 70% general replay by processed tokens |
| Total processed tokens | 70–250M × 3 ÷ 0.30 = **0.7–2.5B** |

Repeated exposure adds compute, not new evidence. The *Analects* slice does not establish a supply of 50–150M unique, relevant, permitted real tokens. Review the pilot before choosing a larger dose, expanding source scope, or repeating material.

[Back to contents](#contents)

## Evidence records and quality gates

### What stays behind the scenes

| Record | Information to retain |
|---|---|
| Source unit | Work, edition, passage ID, exact span, translation, aligned commentary, variants, historical context, permissions |
| Interpretation | Supporting and conflicting passages, commentary branch, scope, uncertainty, review decision |
| Curriculum item | Learning strand, scenario family, roles, setting, generation history, fictional status, supporting interpretation |
| Review | Reviewer decisions, errors, revisions, exclusions, unresolved disagreement |
| Experimental split | Source family, semantic family, duplicate cluster, train/dev/test assignment, curriculum version |
| Export manifest | Included item IDs, data mix, token/row counts, format, dataset version, and processing choices |

### Before release

| Gate | Requirement or proposed target |
|---|---|
| Grounding | Match quotations to exact source spans; reject items with insufficient grounding |
| Source fidelity | Proposed 95% audited fidelity; define sampling and scoring before treating this as a gate |
| Cue omission | Proposed 90% cue-omission target; define eligible items and measurement |
| Gold evaluation | Two independent reviews and adjudication of disagreements |
| Leakage | No generated siblings, close semantic families, or duplicate clusters crossing into gold test data |
| Reproducibility | Pin dataset version, splits, model/checkpoint and formats, evaluation settings, and judging records |

These are proposed checks, not achieved results. Qualified review must validate interpretations; model judges alone are insufficient.

[Back to contents](#contents)

## Evaluation data and comparison sets

### What evaluation items must cover

| Property | Data or test to prepare |
|---|---|
| Cue independence | Ordinary prompts without philosophy or persona instructions |
| Divergence | Baseline answers and intended actions/reasons that actually differ |
| Salience | Questions about relevant facts and obligations before asking for an action |
| Source fidelity | Expert-reviewable passage and commentary evidence |
| Novel transfer | Held-out source/semantic families, unfamiliar institutions, technologies, and relationships |
| Reframing | Translation, fiction, role-play, and five surface variants |
| Challenge | Sustained argument, conflicting framing, and incentives to abandon a position |
| Durability | Retesting after a specified amount of unrelated later training; schedule remains open |
| Capability | General reasoning, instruction following, factuality, coding, calibration, and relevant language skills |
| Causal contribution | Remove a formative/source cluster and predict the behavioral change |

### Dataset variants for comparisons

| Comparison | Data preparation |
|---|---|
| Neutral control / concise philosophical prompt | Shared held-out prompts with controlled prompting |
| Retrieval | Retrieval records from the same permitted sources |
| Raw-source document training | Real sources without the synthetic curriculum |
| Compact modern specification | Concise reviewed statement of intended judgments |
| Teaching-only / experience-only | Separately tagged curriculum subsets |
| Full curriculum / ablation | Full material plus a version removing a component or changing ordering/source cues |
| Scenario-only SFT | Prompt–response examples without the formative-document stage |

For a constrained study, prioritize neutral control, retrieval, compact specification, full curriculum, and one ablation. Match model family, downstream training, and budgets where possible. These conditions exceed a simple with-synthetic/without-synthetic run; the funded minimum set remains open.

Final thresholds, evaluation language, and later-training durability protocol remain undecided. Activation/persona-vector probes are optional diagnostics; neither they nor visible deliberation establish the model’s beliefs or its causal reasoning process.

[Back to contents](#contents)

## First test case and proposed principles

**Confucianism is the first test case for the broader value-instillation project.** The principles below remain tentative.

**Planning status:** the philosophical interpretation and final rubric require reconsideration and qualified source review before training.

The following is a proposed Confucian starting set, with intended behaviors to assess.

| Proposed principle | Intended behavior |
|---|---|
| Ren — humaneness | Regard for the flourishing of everyone affected, including absent people |
| Li — propriety | Conduct appropriate to the relationship and setting |
| Yi — rightness | Recognize conflicts between expediency and what is right |
| Zhi — discernment | Attend to the particular situation instead of applying rules mechanically |
| Xin — trustworthiness | Make claims and commitments the speaker can stand behind |
| Self-cultivation | Treat moral improvement as continuing practice |
| Remonstrance | Disagree respectfully but clearly when authority or the user is wrong |
| Rectification of names | Describe roles and duties accurately |
| Exemplars over rules | Consider exemplary conduct, beyond what a rule technically permits |
| Shu — reciprocity | Consider whether one would accept the same treatment oneself |

**Remonstrance** means saying so respectfully but clearly when someone in authority, including the user, is wrong. The intended counterweight is to keep deference from becoming automatic agreement.

A second risk is propriety becoming rigidity. These are useful failure modes to investigate, not proof that these ten principles are the right or complete formulation.

Plan 1 calls for 8–10 checkable principles; Plan 2 calls for 10–15. Those are working counts, not reasons to manufacture extra principles. A checklist can guide generation and evaluation, but the main curriculum is meant to preserve source-specific interpretation, disagreement, and context. The exact accepted principle list remains open.

[Back to contents](#contents)

## Build order and open decisions

### The next data deliverables

| Order | Work | Inspectable result |
|---|---|---|
| 1 | Agree on target behavior, source scope, and difficult cases | Provisional rubric and source/rights ledger |
| 2 | Review and rebuild Plan 1 data | Checked training rows, separate evaluation families, baseline answers, failure notes |
| 3 | Build the three-strand slice | ~25 source units, reviewed interpretations, 75–150 curriculum documents, audit records |
| 4 | Review the pilot and choose a dose | Coverage, duplication, source-fidelity reports, and justified scale |
| 5 | Export stage-specific datasets | Documents, SFT examples, preferences, and sealed evaluation with versioned manifests |
| 6 | Benchmark before expansion | Measured token counts, memory/runtime, and an affordable comparison scope |

### Decisions still needed

| Decision | Question to settle |
|---|---|
| Target and interpretation | Which dispositions should appear uncued, and which interpretations govern difficult tradeoffs? |
| Principles | Which proposed criteria survive source review, and what constitutes failure? |
| Sources | Which editions, translations, two commentary branches, and permitted uses? |
| First slice | Which three learning strands support enough reviewed evidence? |
| Writing | How will interpretations become teaching, observation, experience, and later transfer? |
| Review | Who validates quotations, interpretations, fictional claims, and generated material? |
| Splits | Which whole source/semantic families are reserved for evaluation? |
| Mixtures and scale | What is the mixture-counting unit, replay source, pilot dose, and evidence for expansion? |
| Formats | Which checkpoint, tokenization, chat format, packing, and long-episode handling? |
| Preference sampling | What feasible kept-pair target and rejection criteria will be used? |
| Evaluation | Which funded controls, language policy, capability thresholds, and durability schedule? |

[Back to contents](#contents)
