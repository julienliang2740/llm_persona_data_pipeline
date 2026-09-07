# Value Instillation Project Guide

**Goal: teach an existing LLM a stable way of noticing, reasoning, and choosing, using Confucianism as the first test case.**

**Working guide · Updated 7 September 2026 · Platform: AWS SageMaker AI**

This is the project overview for the team. It contains the current goal, both plans, data summary, evaluation, budget, and open decisions. Proposals remain distinguishable from completed work.

## Contents

- [Current goal](#current-goal)
- [Status and existing work](#status-and-existing-work)
- [Project history](#project-history)
- [Terminology and the two plans](#terminology-and-the-two-plans)
- [First test case](#first-test-case)
- [Data design](#data-design)
- [Corpus sizes](#corpus-sizes)
- [Plan 1](#plan-1)
- [Plan 2](#plan-2)
- [Evaluation](#evaluation)
- [Resources and budget](#resources-and-budget)
- [Information still needed](#information-still-needed)
- [Research limits and alternatives](#research-limits-and-alternatives)
- [Proposed build order](#proposed-build-order)

## Current goal

**Build a way to teach stable values through the material an LLM learns from. Confucianism is our first test case.**

| What we are building | Purpose |
|---|---|
| Curriculum compiler | Turn reviewed philosophical sources into teaching, stories, experiences, feedback, and reflection |
| Training experiment | Test whether that curriculum changes default judgment in unfamiliar situations |

**Success would mean:** the model notices relevant obligations, makes source-faithful choices without a persona prompt, handles reframing and challenge, and retains general capabilities.

Both plans start from an existing 7–8B model. “More fundamental” currently means richer formative data and document post-training before assistant training. It does not establish that a model literally holds beliefs.

The curriculum compiler and reviewed data are the main research contribution; model training demonstrates whether they are useful.

[Back to contents](#contents)

## Status and existing work

| Item | Current snapshot |
|---|---|
| Plan 1 | Existing code is disposable; restart cleanly |
| Plan 2 | Not started |
| Available data | 500 starter training rows from 100 scenario families, plus 50 evaluation prompts |
| Platform | AWS SageMaker AI |

The reviewed formative corpus and compiler are still to be built. Update this snapshot as work progresses.

[Back to contents](#contents)

## Project history

The relevant shift was from imitating decisions to investigating what forms them: experiences, relationships, feedback, and worldview. That led to the current curriculum idea.

The working hypothesis is that examples of decisions alone may omit the experiences and feedback that shape judgment.

[Back to contents](#contents)

## Terminology and the two plans

We use **post-training** as the umbrella term for training an already pretrained model. The stages describe different learning objectives:

| Term | Meaning in this project |
|---|---|
| Document post-training | Next-token learning on source and synthetic documents, before rebuilding assistant behavior |
| Supervised fine-tuning (SFT) | Learning from example responses to user prompts |
| Preference training (DPO) | Learning to favor preferred responses over rejected alternatives |
| LoRA | The plan's method for training adapter weights in an existing model |
| QLoRA | The quantized adapter-training option proposed for smaller GPU memory |
| General replay | Ordinary text or instruction examples mixed in to help retain general capabilities |
| Base checkpoint | A released model before its assistant instruction-tuning stage |
| Instruction checkpoint | A released model already adapted to answering user instructions |
| Divergence case | A case where the intended philosophical judgment differs from the baseline model's actual answer |
| Uncued evaluation | The question does not tell the model which philosophy or persona to adopt |
| Ablation | A comparison that removes or changes one component to test its contribution |

Both current plans use released 7–8B models. Neither trains a model from scratch.

| | Plan 1: introductory experiment | Plan 2: main experimental proposal |
|---|---|---|
| Purpose | Make data, training, and evaluation work end to end | Test whether formative documents improve robust philosophical behavior |
| Starting model | Instruction checkpoint | Base checkpoint |
| Main data | 500 prompt–response examples | Source documents, synthetic curriculum, instructions, preference pairs |
| Training | LoRA SFT; optional tiny DPO exercise | Document post-training, then SFT, then DPO if it improves results |
| Intended output | A working pipeline and useful failure notes | A controlled comparison with evidence of transfer and source fidelity |
| AWS cash planning | About $20–50 for a small first run | Instance- and runtime-dependent; see the SageMaker scenarios below |
| Provisional calendar estimate | 3–5 hours with working tooling | 6–10 weeks first pass; 8–16 weeks for the project |

The active AWS budget is in [Resources and budget](#resources-and-budget). Calendar estimates remain provisional. Training from scratch is a separate future direction.

[Back to contents](#contents)

## First test case

**Confucianism is our first worked example, not the limit of the overall project.**

| Initial choice | What it means |
|---|---|
| Philosophical tradition | Use Confucian ethics to make the research question concrete |
| Source pilot | Begin with the Analects and keep two commentary branches distinct |
| Behaviors of interest | Humaneness, appropriate conduct, discernment, trustworthiness, and respectful disagreement with authority |
| Status | The exact principles and interpretation remain open |

The proposed starting set is humaneness (ren), propriety (li), rightness (yi), discernment (zhi), trustworthiness (xin), self-cultivation, respectful disagreement with authority (remonstrance), accurate roles and duties (rectification of names), exemplary conduct, and reciprocity (shu). These remain pending source review and agreement on a testable rubric. Deference must not become automatic agreement, and propriety must not become rigidity.

[Back to contents](#contents)

## Data design

### Data for Plan 1

| Use | Data | Brief example |
|---|---|---|
| SFT | 500 prompt–response pairs; optional 100 general instruction examples | Asked about a supervisor’s mistake → short deliberation and respectful, clear advice |
| Evaluation | 50 separate prompts: 25 ordinary, 15 divergence, 10 reframing | The same kind of duty conflict in an unfamiliar setting |
| Optional DPO practice | 300 new prompts × two candidate responses | Prefer reasoned disagreement over automatic agreement |

### Data for Plan 2 by phase

| Phase | Data | Brief example |
|---|---|---|
| 0. Define and measure | 10–15 provisional principles; 100 human-labeled pairs; 200 dev + 200 sealed test prompts | Reviewers compare two answers about conflicting duties |
| 1. Document post-training | Reviewed source text + synthetic curriculum; 30% domain / 70% general replay | A clerk makes a mistake, receives correction, and later applies the lesson |
| 2. SFT | 20–30k general instructions + ~1,500 curated value examples from 3,000 prompts | A present-day workplace question with a reviewed deliberation and answer |
| 3. DPO, if useful | 6,000 new prompts × two responses; at most 6,000 preference pairs before filtering | Prefer context-sensitive advice over rigid rule-following |
| 4. Verify | Held-out dev and sealed test cases, plus capability checks | New wording, roles, and challenges without naming the philosophy |

**Examples are illustrative, not approved training items.** Evaluation data stays out of training; DPO prompts stay separate from SFT. Document-corpus targets are in [Corpus sizes](#corpus-sizes).

### The data pipeline

| Step | Input | Output |
|---|---|---|
| 1. Collect evidence | Exact passages, editions, translations, commentaries, and context | Traceable source records |
| 2. Review interpretations | Several related passages and competing readings | A justified learning target with explicit limits |
| 3. Build learning material | The reviewed interpretation | Teaching, stories, social situations, consequences, and reflection |
| 4. Export for use | Approved material plus review records | Documents, chat examples, preference pairs, and evaluation cases |

### What the model reads in the formative curriculum

| Data type | Example of its purpose |
|---|---|
| Teaching and dialogue | Learn a concept through explanation and questions |
| Everyday social life | Encounter values in letters, routines, relationships, and rituals |
| Observational stories | See someone make a choice and face its consequences |
| Situated experiences | Work through limited information, action, feedback, and reflection |
| Connected episodes | See earlier mistakes change later judgment |
| Conflicts and counterexamples | Resolve competing duties and avoid mechanical rules |

**Example:** a clerk learns a procedure, applies it badly when circumstances change, receives correction, then handles a later dispute more thoughtfully.

### What stays behind the scenes

Each item also keeps its source passages, interpretation branch, fictional status, review history, and train/test family. These audit records support trustworthy data; most are not shown to the model.

**Design rules:** avoid answer-signaling labels; preserve real disagreement; include imperfect outcomes; keep related training and test families separate.

The model should usually see natural prose, dialogue, and unfolding experience.

[Back to contents](#contents)

## Corpus sizes

| Scope | Target | What it is for |
|---|---|---|
| First complete slice | 3 learning strands; ~25 source units; 75–150 documents | Test the data process end to end |
| Reviewed pilot | 2,000–5,000 documents; 3–10M unique curriculum tokens | Demonstrate a coherent formative dataset |
| Larger Plan 2 proposal | 50–150M real tokens + 20–100M synthetic tokens | Proposed document-training dose |

**Open decision:** the reviewed pilot and larger Plan 2 corpus are different scales. We have not established where the larger, relevant, permitted source corpus will come from.

Repeated training exposure is not new data. Trajectories, arcs, and conflict cases overlap within the document totals.

[Back to contents](#contents)

## Plan 1

**Purpose:** complete a cheap training loop and learn where shallow behavior imitation fails.

### Inputs and output

| Item | Working target |
|---|---|
| Model | Existing 7–8B instruction checkpoint |
| Principles | 8–10 checkable criteria plus a short persona description |
| Training examples | 500 prompt–response pairs with short deliberation and answer |
| Coverage | Advice, work, family, interpersonal conflict; at least 100 intended divergence cases |
| Evaluation | 50 prompts: 25 ordinary, 15 divergence, 10 reframing |
| Optional replay | 100 general instruction examples |
| Output | Before/after answers, failure notes, and a working training configuration |

### Run sequence

1. **Define and curate:** settle provisional criteria; check prompt coverage and actual divergence from the baseline.
2. **Train:** use LoRA SFT; on a 24 GB SageMaker instance, use the quantized QLoRA option.
3. **Compare:** run the original and adapted model on the same 50 prompts with matching settings; read every pair.
4. **Carry forward:** keep principles, evaluation lessons, and failure notes. The adapter can be discarded.

### Starting settings and cost

| Setting | Proposed starting point |
|---|---|
| Adapter | Rank 16; alpha 32; dropout 0.05; all linear layers |
| Optimization | Learning rate 2e-4; 3 epochs; batch 4 with accumulation 4; assistant-token loss |
| Format | Maximum sequence length 2,048; consistent chat and deliberation format |
| Evaluation generation | Same settings before/after; temperature 0.7 |
| SageMaker candidate | One `ml.g5.2xlarge` for QLoRA; benchmark memory and speed |
| Planning allowance | About **$20–50**, and **1–2 days** for a clean first setup and review |

With working tooling, allow roughly 3–5 hours for the small experiment. Training runtime on the A10G still needs measurement. Optional DPO practice uses 300 new prompts and two candidates each, with extra compute/judging cost.

This first experiment tests the pipeline; it cannot establish the broader philosophical hypothesis.

[Back to contents](#contents)

## Plan 2

**Purpose:** test whether formative documents improve the model's default judgment beyond ordinary response imitation.

**Starting point:** a released 7–8B base model. **Platform:** SageMaker AI training jobs. The exact instance is still to be selected and benchmarked.

### Stages

| Stage | Data | What happens | Gate or output |
|---|---|---|---|
| 0. Define and measure | 10–15 provisional principles; 200 dev prompts; 200 sealed test prompts; 100 human-labeled pairs | Record baselines and compare three candidate judges | A usable rubric, calibrated judge, and held-out test |
| 1. Document post-training | Real sources, synthetic curriculum, and general replay | Train next-token prediction across the model's parameters | Compare with/without synthetic data; check values and capability |
| 2. SFT | 20–30k general instructions + ~1,500 curated value examples from 3,000 prompts | Critique and revise answers, then train an adapter on deliberation and answer | Actual divergence improves; assistant capability is retained |
| 3. DPO | New prompts with preferred/rejected candidate responses | Train preferences using the SFT checkpoint as reference | Better divergence/reframing without regression |
| 4. Verify | Dev tests and the sealed test | Freeze the setup and evaluate | Honest held-out results and limitations |

### Training data and settings

| Stage | Proposed settings |
|---|---|
| Document post-training | 30% domain / 70% general replay; 3 domain passes; full-parameter FSDP; bf16; sequence 4,096; global batch ~1–2M tokens; learning rate 1e-5–3e-5; cosine decay; 2% warmup |
| SFT | Generate an answer, critique against 2–3 principles, revise 2–3 rounds, judge-screen, then read survivors; LoRA rank 16–32; learning rate 2e-4; 2–3 epochs |
| DPO | SFT model as reference; LoRA; beta 0.1; learning rate 5e-5; 1–2 epochs; score principles separately and randomize comparison order |

These are starting proposals. Full-parameter training has not been shown necessary by this project. GPU count, batches, and runtime must be adapted to the selected SageMaker instance.

**Exposure calculation:** 70–250M domain tokens × 3 passes ÷ 0.30 = **0.7–2.5B processed tokens**.

**DPO count correction:** 6,000 prompts × two responses gives **12,000 responses and at most 6,000 pairs**. A target of 10,000 kept pairs would require more prompts or candidates. Keep prompts disjoint from SFT and evaluation.

### Calendar planning

| Work | Provisional allowance |
|---|---|
| Definitions and baseline | 3–7 days |
| Corpus work and document training | About 2–3 weeks |
| SFT data preparation and training | 1–1.5 weeks, including 2–5 days reading |
| DPO and verification | About 2–5 days each |
| First pass / iterative project | **6–10 weeks / 8–16 weeks**, provisional |

Most calendar time is data and review. AWS capacity and measured job runtime can change the schedule. Use the SageMaker budget below.

[Back to contents](#contents)

## Evaluation

The research question is whether the formative curriculum improves behavior **over simpler explanations and alternatives**. A gain over an untouched model alone would not isolate the compiler's contribution.

### Comparisons

The proposed comparison set includes a neutral control, a concise philosophical prompt, retrieval over the same sources, raw-source document training, a compact modern specification, separate teaching and experience subsets, the full developmental curriculum, and a version with ordering or source cues changed.

For a constrained study, prioritize the neutral control, retrieval, compact specification, full curriculum, and an ablation of the full curriculum. The general research question also includes scenario-only SFT. These are experimental conditions; their compute costs are not all covered by the budgeted with-synthetic/without-synthetic comparison.

Compare the same model family with compatible downstream training and comparable budgets. In particular, a base model after document training and a separately instruction-tuned model differ in more than philosophical data. A useful main comparison gives both arms the same downstream SFT, with and without the formative-document stage.

### What to measure

| Property | Test | What would be insufficient |
|---|---|---|
| Cue independence | Ask ordinary questions without naming a philosophy or signaling the desired answer | Correct behavior only after a persona instruction |
| Divergence | Compare the intended action and reasons with the baseline's actual answer | The same answer with philosophical terms added |
| Salience | Ask what facts and obligations matter before asking for an action | A polished rationale after an otherwise unchanged choice |
| Source fidelity | Have qualified reviewers compare the justification with its passage/commentary evidence | A judge approving generic moral language |
| Novel transfer | Hold out entire semantic/source families and introduce new institutions, technologies, and relationships | New wording for a familiar training dilemma |
| Reframing | Translation, fiction, role-play, and five surface variants | Success on the original wording alone |
| Challenge | Sustained argument, conflicting framing, and incentives to abandon a position | A single compliant answer |
| Durability | Retest after a specified amount of unrelated later training | Robustness to prompts alone |
| Capability | General reasoning, instruction following, factuality, coding, calibration, and relevant language skills | Better philosophical scores accompanied by broad degradation |
| Causal contribution | Remove a formative/source cluster and predict how behavior should change | Correlation between a trait probe and a score |

The curriculum must justify its complexity through uncued novel behavior and expert-rated source fidelity.

The proposed dev and test sets each have **80 ordinary, 60 divergence, 40 reframing, and 20 adversarial prompts**. Each needs pass/fail notes. Judge calibration establishes agreement with the chosen labels; philosophical fidelity needs source review as well.

Internal activation/persona-vector probes are optional diagnostics. They do not establish a model's beliefs or make visible deliberation a faithful account of its causal process. These tests can raise confidence in behavioral reliability, but they do not establish what the model holds.

The exact later-training durability schedule, final thresholds, and evaluation language policy remain to be chosen. Conclusions from the first run should therefore be narrower than a claim of proven internalization.

[Back to contents](#contents)

## Resources and budget

**Platform: AWS SageMaker AI training jobs.** Plan 1 can stay inexpensive. Plan 2 has a substantially larger budget because it proposes full-parameter training and comparison runs.

### Verified AWS rates

**Pricing assumption:** US East (N. Virginia), `us-east-1`, on-demand **Training** rates in USD. This is a provisional region, not a confirmed team choice. Checked 7 September 2026 against AWS's price list published 4 September 2026; these are whole-instance prices.

| Candidate instance | GPU configuration | USD per instance-hour | Role to consider |
|---|---|---:|---|
| `ml.g5.2xlarge` | 1 A10G, 24 GB | **$1.515** | Plan 1 QLoRA |
| `ml.g6e.2xlarge` | 1 L40S, 48 GB | **$2.800** | Adapter SFT/DPO, subject to memory checks |
| `ml.g6e.12xlarge` | 4 L40S, 48 GB each | **$13.120** | Lower-cost full-parameter candidate to benchmark |
| `ml.p4d.24xlarge` | 8 A100, 40 GB each | **$25.251** | Full-parameter comparison scenario |
| `ml.p5.48xlarge` | 8 H100, 80 GB each | **$63.296** | Higher-throughput comparison scenario |

Rates: [AWS SageMaker regional training price list](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonSageMaker/current/us-east-1/index.json). Hardware: [AWS G5](https://aws.amazon.com/ec2/instance-types/g5/), [AWS G6e](https://aws.amazon.com/ec2/instance-types/g6e/), [AWS accelerated-instance specifications](https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html).

The eight-GPU rows bill the full instance even if only two GPUs are used. A single-H100 `ml.p5.4xlarge` also exists, but its SageMaker purchase options depend on region; no ordinary on-demand Training price for it appeared in the retrieved `us-east-1` list. A job requiring two H100 GPUs cannot be priced as one-quarter of an eight-H100 instance. [AWS single-H100 availability](https://aws.amazon.com/about-aws/whats-new/2025/08/p5-instance-nvidia-h100-gpu-sagemaker-training-processing-jobs)

### Plan 1 allowance

| Cost | Assumption | Amount |
|---|---|---:|
| GPU jobs | 2–6 billed hours on `ml.g5.2xlarge`; planning allowance, not a runtime measurement | $3–9 |
| Example generation | Small-data API allowance | $5–15 |
| Evaluation, small storage/CPU use, and retry cushion | Provisional allowance | $10–25 |
| **First-run allowance** | Rounded; no continuously running endpoint | **About $20–50** |

### Plan 2 scenarios

**These are cost scenarios, not runtime forecasts.** For comparison only, assume 15–40 hours for each document job. Eight GPUs may finish sooner; different GPUs may finish later. Benchmark a short job before committing the full corpus.

| Document-training scope | 8 A100 instance | 8 H100 instance |
|---|---:|---:|
| One 15–40-hour job | $379–1,010 | $949–2,532 |
| Two comparison jobs | $758–2,020 | $1,899–5,064 |
| Two jobs with a 2× compute retry allowance | **$1,515–4,040** | **$3,798–10,127** |

Add the following per-pass allowances:

| Additional cost | Assumption | Range |
|---|---|---:|
| Data generation and judge/evaluation APIs | $5 definitions + $75–525 corpus generation/screening + $90–190 SFT revisions/screening + $50–130 DPO judging + $20 verification | $240–870 |
| Adapter training and sampling | Provisional SageMaker job allowance, to replace with measured runtime | $50–200 |
| Storage, CPU notebooks/processing, and logs | Provisional short-project allowance | $50–150 |
| **Illustrative first-pass total** | Two document variants and the above retry allowance | **About $1,900–5,300 on 8 A100; $4,200–11,400 on 8 H100** |

This does **not** price every evaluation arm, paid curation, or licensed sources. The generation line assumes a 50M-token synthetic generation example; a different dose or model changes it. The whole-project total depends on which document jobs need repeating; do not multiply this first-pass scenario blindly.

### Cost controls

- Use finite training/evaluation jobs; persistent notebooks and endpoints are separate ongoing costs. [SageMaker pricing](https://aws.amazon.com/sagemaker/ai/pricing/)
- Managed Spot Training can reduce compute charges, but savings and capacity are not guaranteed; configure checkpoints for interrupted jobs. [AWS Managed Spot Training](https://docs.aws.amazon.com/sagemaker/latest/dg/model-managed-spot-training.html)
- Confirm region, training quota, and usable AWS credits before selecting the large instance. Credits change out-of-pocket spending, not the gross resource cost.
- Reprice after a short run measures tokens/second and memory. The 4-L40S option deserves comparison, but its lower hourly rate does not by itself prove a lower completed-job cost.

[Back to contents](#contents)

## Information still needed

The items below are **decisions or artifacts the project still needs**.

| Information or artifact needed | Why it is needed | Current state |
|---|---|---|
| Final target and philosophical scope | Define what should change, which interpretation governs it, and which tradeoffs are intended | Confucianism and the Analects pilot are the working direction; the exact rubric is tentative |
| Approved principles with examples | Let humans and generators distinguish a pass from a failure | Ten candidate principles exist; not finalized |
| Source and rights ledger | Identify exact editions, passages, translations, commentary branches, and permitted uses | Source candidates and schema proposals exist; the reviewed corpus does not |
| Data-scale decision | Choose a pilot dose and a defensible path to larger runs | The reviewed pilot and larger document-training proposal use different scales |
| Reviewed curriculum slice | Demonstrate that sources can produce grounded experiences with traceable review | Three-strand slice is proposed; compiler not yet built |
| Data manifests and splits | Prevent source/semantic-family leakage and reproduce exports | Starter JSONL exists; main-study manifests and sealed split remain to be built |
| Exact model and formats | Make training and evaluation comparable | Pin the 7–8B checkpoint, versions, and input/output formats |
| Baseline and gold labels | Verify real divergence and calibrate judges | Starter prompts exist; main-study labels and baseline measurements still needed |
| DPO sampling plan | Produce the intended number of valid comparison pairs | 6,000 two-response prompts yield at most 6,000 pairs; choose a feasible target |
| Main comparison conditions | Separate the effect of formative data from model choice and later instruction training | Controls are proposed in Evaluation; a funded minimum set is not finalized |
| Durability and capability gates | Define what robustness and acceptable regression mean | Test categories exist; exact protocols and thresholds remain open |
| AWS job budget | Determine which corpus and comparison scope is affordable | SageMaker rates checked; region, quotas, instance, credits, and measured runtime remain to be settled |
| Reproducible run package | Preserve the configuration, dataset version, checkpoints, evaluation settings, and results | Training package still to be assembled |

These are the working decisions for the current project.

[Back to contents](#contents)

## Research limits and alternatives

| Question | Current position |
|---|---|
| Can a small fine-tune change behavior? | A reasonable Plan 1 hypothesis; measure the change |
| Does the formative curriculum beat simpler methods? | The central open research question |
| Do more source tokens guarantee deeper values? | No such conclusion is established |
| Do full-parameter training, visible deliberation, or persona vectors prove internalization? | They are methods or diagnostics, not proof |
| Is GRPO required? | No; group relative policy optimization (GRPO) is an optional, unadopted reinforcement-learning branch |
| Should we scale to 32B/70B now? | No current commitment; first establish a useful small-model result |
| Is training from scratch part of the current plans? | No; it is a deferred, much larger research direction |

Training depth, data depth, and evidence of internalization are different.

Full-parameter training and GRPO have not been established as necessary. Larger models or corpora require new evidence and a separate budget.

[Back to contents](#contents)

## Proposed build order

| Order | Work | Inspectable result |
|---|---|---|
| 1 | Clarify target behavior and the first test case | Principles with difficult examples and a selected source scope |
| 2 | Rebuild Plan 1 cleanly | Before/after answers and failure notes |
| 3 | Build the first data slice | ~25 source units, reviewed interpretations, and 75–150 documents |
| 4 | Review the pilot and choose a training dose | Coverage, duplication, and source-fidelity reports |
| 5 | Benchmark a SageMaker job | Memory, tokens/second, and a revised cost estimate |
| 6 | Run the main comparison | Matched results, capability checks, and limitations |

Build and review the compiler’s first data slice before committing to large-scale document training.

[Back to contents](#contents)
