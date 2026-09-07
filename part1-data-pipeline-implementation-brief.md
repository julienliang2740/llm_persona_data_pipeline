# Part 1 Data Pipeline — Implementation Brief

## Purpose

Build a small, generalizable pipeline that can produce and validate training data for a target value system or behavioral specification, then support a simple fine-tuning/evaluation loop.

Part 1 is intentionally narrow: make **data, training, and evaluation work end to end**. It is not the larger formative-document pipeline from Part 2.

## Core Inputs

1. **Reviewed target specification**
   - The principles or behaviors we want to instill.
   - Include important boundaries/failure modes where needed.
   - This should be researched and decided **before** the automated pipeline runs; the pipeline should not decide what the philosophy/value system means.

2. **Reference/source material**
   - Material used to ground generation in the chosen target.
   - For the first test case, this is Confucian material, but the pipeline should not hard-code Confucianism.

3. **Base model being fine-tuned**
   - Used during dataset construction to check whether candidate examples actually differ from the model's current behavior where divergence matters.

4. **Dataset requirements**
   - Desired train/eval sizes and broad coverage requirements.
   - Current Part 1 target: about **500 SFT examples + 50 held-out evaluation prompts**.

## Pipeline

Keep the implementation conceptually simple:

1. **Generate**
   - Create candidate training and evaluation cases from the target specification, references, and coverage requirements.

2. **Validate / filter**
   - Check target adherence, obvious duplication, leakage between related train/eval families, and whether intended divergence cases actually diverge from the base model.

3. **Train + evaluate**
   - Export the approved data, fine-tune the target model, and compare before/after behavior on the held-out evaluation set.

## Outputs

At minimum:

- SFT training dataset
- Held-out evaluation dataset
- Trained adapter/checkpoint
- Before-vs-after evaluation results
- Lightweight metadata/reporting needed to reproduce the dataset/run

Do not overbuild the audit or curriculum infrastructure for Part 1.

## Data-Generation Models

The **generator/teacher model is separate from the model being fine-tuned**.

Current preferred setup:

- **Primary generator:** Qwen3.5-397B-A17B
- **Reviewer / critic:** DeepSeek V4 Pro

Rationale:
- Use a strong model to generate nuanced, diverse examples.
- Use a different strong model for critique/review rather than having the generator fully grade itself.
- At Part 1 scale, API generation cost is small enough that quality matters more than minimizing every dollar.

A reasonable implementation should keep generator/reviewer providers configurable rather than hard-coded.

### Rough generation cost

For a Part 1 run that generates more candidates than needed, critiques them, and filters down to the final dataset:

- Expect roughly **a few dollars for one clean pass**
- Budget roughly **$10–20** for retries, extra candidates, prompt iteration, and multiple review passes

Human/source review is not included in that estimate.

## Generalization Principle

The pipeline engine should be reusable across target systems.

Conceptually:

```text
target specification
+ reference material
+ base model
+ dataset requirements
        ↓
generate
        ↓
validate/filter
        ↓
train/evaluate
```

Confucianism is the first configuration, not part of the pipeline architecture.

## Relevant Existing-Doc Constraints

These existing statements should remain true in the implementation:

- `UNIFIED-DOC.md` — **"Make data, training, and evaluation work end to end"**
- `data-design-planning(1).md` — **"run the baseline → verify actual divergence"**
- `data-design-planning(1).md` — **"Keep related scenario families together when splitting."**
- `data-design-planning(1).md` — Part 1 uses **"500 prompt–response pairs"** and **"50 separate prompts"** for evaluation.

Avoid importing Part 2's larger curriculum/document-generation machinery unless it becomes necessary later.
