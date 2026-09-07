# Fireworks account notes

Practical facts for `pipeline/model.py` and for run planning. Retrieved 2026-09-07.
Prices live in `configs/pricing.yaml`; this file covers everything that is not a number in that table.

## Pricing summary (Standard tier, USD per 1M tokens)

| model id (`accounts/fireworks/models/…`) | input | cached input | output |
|---|---|---|---|
| `kimi-k3` | 3.00 | 0.30 | 15.00 |
| `qwen3p8-max` | 2.00 | 0.25 | 6.00 |
| `qwen3p8-2p4t-a95b` | 2.00 | 0.25 | 6.00 |
| `glm-5p3` | 1.40 | 0.26 | 4.40 |
| `deepseek-v4-pro-0813` | 1.32 | 0.044 | 3.96 |
| `qwen3p7-plus` | 0.40 | 0.08 | 1.60 |
| `minimax-m3` | 0.30 | 0.06 | 1.20 |
| `deepseek-v4-flash-0731` | 0.22 | 0.007 | 0.66 |
| `gpt-oss-120b` | 0.15 | 0.015 | 0.60 |
| `glm-5p3-flash` | 0.15 | 0.03 | 0.50 |
| `qwen3-embedding-8b` | 0.10 | n/a | n/a (input only) |

Source: <https://docs.fireworks.ai/serverless/pricing>. Every model we use has a published price;
there are no nulls except embedding output, which does not exist as a billable quantity.

Two caveats worth encoding in the ledger:

- `qwen3p8-2p4t-a95b` is not its own row in the docs table. Its price comes from the model page
  <https://fireworks.ai/models/fireworks/qwen3p8-max>, which renders as "Qwen3.8-2.4T-A95B" and cites
  the `qwen3p8-2p4t-a95b` id at the same $2.00/$0.25/$6.00. The two ids look like one model.
- Fireworks does not return cached-token counts in the OpenAI-compatible `usage` block, so we cannot
  apply the cached rate. Cost every prompt token at the full `input` rate. That over-estimates rather
  than under-estimates, which is the safe direction for a budget.

Priority and Fast serving tiers cost roughly 1.25x and 1.5x Standard. We never request them, so
Standard applies.

## Rate limits

Serverless limits are **adaptive**, not a fixed per-account quota: they grow and shrink with recent
usage, bounded by ceilings set by model size and by the account's spending tier.
Source: <https://docs.fireworks.ai/serverless/rate-limits>.

Published ceilings, by model size, in tokens per minute:

| model size | total prompt TPM | uncached prompt TPM | generated TPM |
|---|---|---|---|
| < 400B | 64.8M | 16.2M | 648k |
| 400B – < 1.6T | 43.2M | 10.8M | 432k |
| >= 1.6T | 21.6M | 5.4M | 216k |

Separately there is an account-wide **6,000 requests/min** ceiling covering serverless, dedicated
deployments and training combined (<https://docs.fireworks.ai/guides/quotas_usage/rate-limits>).

These ceilings are far above anything this pipeline does. The binding constraint in practice is the
adaptive limit for a cold account, which is why the default concurrency of 4 per model stays.
Generated-TPM is the one to watch: 648k/min sounds large, but it is shared and it is the metric that
throttles long generation runs first.

Notes for `model.py`:

- Throttling shows up as `429 Too Many Requests`; overload as `503 Service Overloaded`. Both are in
  the retry set already specified in the design brief.
- The docs list `X-Ratelimit-Limit-Tokens-Prompt`,
  `X-Ratelimit-Limit-Tokens-Cache-Adjusted-Prompt` and `X-Ratelimit-Limit-Tokens-Generated` response
  headers. **This account does not return them.** A live probe on 2026-09-07 returned only
  `x-ratelimit-over-limit: no` and `x-request-id`. So do not build backoff around header values;
  react to the status code. `x-ratelimit-over-limit` is worth logging as a cheap early warning.
- `x-request-id` (e.g. `chatcmpl-a0ef…`) is the value to put in error messages, as the brief requires.
- Staying under the limit does not guarantee success: the docs state Standard-tier requests can be
  load-shed under peak traffic. Retries are mandatory, not defensive.

## Turning reasoning off

All the chat models return `reasoning_content` by default, which costs output tokens and inflates
`max_tokens` budgets. `reasoning_effort` controls it. Accepted values are `"none"`, `"low"`,
`"medium"`, `"high"`, `"max"`, plus booleans (`false` normalises to `"none"`, `true` to `"medium"`).

Probed live on 2026-09-07, one tiny call per model:

| model | `reasoning_effort: "none"` | notes |
|---|---|---|
| `qwen3p8-max` | works | no `reasoning_content`, 2 output tokens |
| `qwen3p8-2p4t-a95b` | works | same |
| `qwen3p7-plus` | works | same |
| `deepseek-v4-pro-0813` | works | same |
| `minimax-m3` | works | same |
| `kimi-k3` | works | same |
| `glm-5p3` | **rejected** | "GLM-5.3 is a thinking-only model" |
| `glm-5p3-flash` | **rejected** | same; `"low"` works and still returns reasoning |
| `gpt-oss-120b` | **rejected** | "Invalid reasoning effort: none"; `"low"` works |

Consequences:

- Pass `reasoning_effort` through `extra_body` per model, as the design brief already anticipates.
- Never send `"none"` blindly. For `glm-5p3`, `glm-5p3-flash` and `gpt-oss-120b` it is a hard 400,
  not a silent no-op. Use `"low"` for those three and keep budgeting output tokens for reasoning.
- For the reviewer role on `deepseek-v4-pro-0813`, `"none"` is safe and makes the JSON-scoring calls
  meaningfully cheaper and shorter.

## Which models are callable: `/v1/models` vs the catalog

The public catalog at <https://fireworks.ai/models> is much larger than what this account can call
serverless. Models not pre-deployed by Fireworks, including every custom upload and every fine-tuned
variant, need a dedicated deployment before inference works. This is why catalog ids such as
`llama-v3p1-8b-instruct` 404 on this account, as the design brief records: a 404 here means "not
served on this account", not "no such model". Treat it as a configuration error and fail loudly with
the model id in the message.

Consequence for the base model: there is no 7-8B instruct checkpoint we can call serverless, which
is exactly why it runs locally. See `docs/base-model.md`.

## Fine-tuning and dedicated deployments

Relevant if Part 2 trains the model rather than only producing data.

- Fine-tuning is offered on a per-model basis; a base model must carry a `Tunable: true` tag, checked
  with `firectl model get -a fireworks <MODEL-ID>`. The docs do not state that a standard
  pay-as-you-go account is excluded, but they also do not confirm it is enabled, and I did not
  create a job to find out. **Treat availability on this account as unverified.**
- Managed training price is per 1M training tokens and scales with model size
  (<https://fireworks.ai/pricing>):

  | model size | LoRA SFT | LoRA DPO | full-param SFT | full-param DPO |
  |---|---|---|---|---|
  | up to 16B | $0.50 | $1.00 | $1.00 | $2.00 |
  | 16.1B – 80B | $3.00 | $6.00 | $6.00 | $12.00 |
  | 80B – 300B | $6.00 | $12.00 | $12.00 | $24.00 |
  | > 300B | $10.00 | $20.00 | $20.00 | $40.00 |

  A 7-8B LoRA SFT run therefore falls in the $0.50 per 1M training tokens band, which is negligible
  next to generation cost for a dataset this size.
- **Serving a fine-tuned model is the expensive half.** The docs state dedicated deployments are the
  only supported way to serve a trained model; serverless LoRA addons are not supported. Dedicated
  deployments bill per GPU-second, listed per hour from 1 Sep 2026: H100 80GB $8, H200 141GB $8,
  B200 180GB $13, B300 288GB $15, GB300 288GB $20. So an evaluation session costs roughly $8/hour
  with the cheapest GPU, whether or not it is busy, and the deployment must be torn down afterwards.

That cost shape is the argument for keeping the local llama.cpp base model for before/after
comparisons during development, and reserving a Fireworks deployment for a single final evaluation.
