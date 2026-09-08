# Adolf Hitler (1889–1945) — refuse_scope

Refused 8 September 2026, on scope rather than on evidence. Not admissible as a persona target.

## The gate would have said admit

This is the point of recording it. First-person volume is enormous, documented decisions with
stated reasoning run far past the 6–8 floor, domain breadth and testimonial variety are trivially
met, and the attributable core dwarfs the disputed part. **Every evidentiary criterion passes
comfortably.** The sufficiency gate cannot reach this subject, which is why `refuse_scope` exists
as a separate axis and why `sufficiency.scope_check` is now required on every admitted spec.

## Why scope excludes it

A persona spec is fidelity-maximising by design. It carries no modern-constraint clause — the
schema forbids one, because "the purpose is a dataset that trains a model to behave as closely to
the subject as possible, and a modern-norms override defeats it". `divergence_hypotheses`
deliberately enumerates where the subject departs from ordinary assistant ethics, since that is
"where the dataset earns its keep". The export is `sft_train.jsonl`.

So the artefact would be several hundred fine-tuning rows of Nazi-ideological reasoning applied to
ordinary modern situations — work, community, family, civic — with the guardrail clause removed as
a matter of specification. The fidelity requirement also rules out building a softened version and
calling it compliant.

The exclusion is narrower than "did terrible things", and the contrast that fixes the line is LBJ,
who is admitted: his unattractive half is a stolen Senate seat, self-dealing in office and twenty
years of votes against civil rights legislation, and a spec that softened *that* would be the
defect. The difference is not a severity ranking. It is that here the distinctive value content
**is** the extermination, so the faithful rendering and the harmful artefact are the same object.
There is no version where the objectionable part is a wart on something else.

## What this refusal produced

The conversational refusal did not bind the script arm: `personas/ah/` holds a `usage.jsonl`
showing seven generator calls and $0.96 spent on `sufficiency` and `evidence` passes for this
subject, run after the refusal. That directory has since been deleted — it held no spec and no
passages, only the empty `references/` skeleton and the spend log — and the figure is recorded
here so the episode is not lost with it. That is the argument for putting the boundary in code, and
it is now at pass 0 of `draft_persona.py` — before config is loaded, before any directory is
created, before anything is spent.
