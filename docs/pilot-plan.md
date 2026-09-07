# Pilot plan (round 1)

Purpose: prove the pipeline end to end on four contrasting targets with small samples, then read the
data and let independent critics find what is wrong before anything is scaled.

## Sizes (per target)

| item | pilot | full Part 1 target |
|---|---|---|
| families | 8 (≈6 train, 2 eval; ~30% counterfactual groups) | 100 |
| prompts per family | 3 (eval families also get 2 reframing variants) | 5 |
| responses per prompt | 1 (+ optional 1 revise round, config) | 1 |
| intended-divergence fraction | 0.5 | ≥ 0.2 (≥100 of 500) |
| baseline answers | all divergence-intended prompts + all eval prompts | same |
| reviewer passes | 1 | 1-2 |

Models: generator `qwen3p8-max`, reviewer/judge `deepseek-v4-pro-0813`, base local Qwen2.5-7B-Instruct
(llama.cpp), embeddings `qwen3-embedding-8b`. Concurrency 4.

## What we read after the run

For each target, the run report plus raw JSONL. Independent critics (Opus teammates, one per lens,
each sees all four targets) evaluate:

1. **Fidelity** to spec and sources; confident resolution of unresolved tradeoffs; modern constraints
   attributed to the tradition; translation collapse.
2. **Scenario quality and diversity**: realism, variety of institutions/relationships/stakes, register,
   whether counterfactual groups actually vary one fact, duplicate/near-duplicate cases.
3. **Judgment vs vocabulary**: keyword/doctrinal imitation, explicit ideological cues, translationese,
   whether responses would be recognisable as the target's judgment with all vocabulary stripped.
4. **Divergence reality**: does the candidate differ from the base model in action or reasons; are the
   intended-divergence labels honest; what fraction is generic good advice.
5. **Leakage and splits**: eval families vs train families, reframing variants, group integrity.
6. **Cross-tradition generalisation**: assumptions baked into prompts/records that fit one tradition
   and break another (e.g. deliberation shape, "asker state", authority labels, culpability stance).

Each critic writes `runs/critique/<lens>.md` with concrete example ids, a severity rating, and a
proposed change (prompt, record, config, or spec). The lead consolidates into a change list, the
implementer applies, and round 2 reruns the same sizes for comparison.

## Competing approaches to try in round 2 (if round 1 warrants)

- reviewer = `kimi-k3` or `glm-5p3` vs `deepseek-v4-pro-0813` on the same responses (agreement rate);
- `revise_rounds: 1` vs 0 (does critique-and-revise raise reviewer scores or just vocabulary?);
- family generation with vs without `situation_features` (does structure raise diversity?);
- explicit-mode slice 0.1 vs 0 (does naming the tradition change fidelity scores?).
