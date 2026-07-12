# Phase 17 reference: model-size targets for strong and frontier LLM parity

Date of evidence review: 2026-07-12.

## Why no single exact answer exists

The parameter counts of current proprietary frontier systems such as the newest GPT, Claude, and Gemini families are not publicly specified. Their visible performance also includes post-training, long test-time reasoning, tools, retrieval, agent scaffolds, and private data. Therefore an exact statement such as “frontier parity requires N parameters” is not supported.

The useful engineering prior comes from open-weight systems whose total and activated parameters are public. These figures are not mathematical lower bounds for the Minimum Predictive Machine. They define empirical comparison bands that the Phase 17 scaling campaign must eventually reach or forecast against.

## Public size anchors

| reference system | total parameters | active per token | public performance interpretation | approximate raw 4-bit weight bytes |
|---|---:|---:|---|---:|
| OpenAI gpt-oss-20b | 21B | 3.6B | similar to o3-mini on common benchmarks; deploys within 16GB | 10.5GB |
| OpenAI gpt-oss-120b | 117B | 5.1B | near o4-mini on core reasoning; deploys within 80GB | 58.5GB |
| Qwen3.6-35B-A3B | 35B | 3B | strong compact open agent/coding model, but below the broadest frontier tier | 17.5GB |
| Qwen3.5-397B-A17B | 397B | 17B | vendor evaluations place it near proprietary frontier systems across many language, reasoning, agent and coding benchmarks | 198.5GB |
| DeepSeek-V3 | 671B | 37B | report describes performance comparable to leading closed models; pretrained on 14.8T tokens | 335.5GB |
| Kimi K2.5 | 1T | 32B | broad multimodal/agentic model with vendor evaluations near frontier systems; approximately 15T continual-pretraining tokens | 500GB |

Raw 4-bit bytes are `parameters × 4 / 8` and exclude embeddings duplicated by serving stacks, metadata, KV cache, runtime workspace, vision encoders, speculative heads, and quantization overhead. Actual deployment memory can be larger. OpenAI reports 16GB and 80GB deployment envelopes for its native MXFP4 20B and 120B systems.

## Primary evidence

- OpenAI gpt-oss release: https://openai.com/index/introducing-gpt-oss/
- OpenAI gpt-oss model card: https://arxiv.org/abs/2508.10925
- Qwen3.6-35B-A3B official model card: https://huggingface.co/Qwen/Qwen3.6-35B-A3B
- Qwen3.5-397B-A17B official model card: https://huggingface.co/Qwen/Qwen3.5-397B-A17B
- DeepSeek-V3 technical report: https://arxiv.org/abs/2412.19437
- Kimi K2.5 official model card: https://huggingface.co/moonshotai/Kimi-K2.5
- Kimi K2 architecture/training paper: https://arxiv.org/abs/2507.20534
- Kaplan et al. scaling laws: https://arxiv.org/abs/2001.08361
- Hoffmann et al. compute-optimal training: https://arxiv.org/abs/2203.15556

Vendor benchmark tables are evidence supplied by the model creators. Protocols, reasoning budgets, tools, context management, and repeated sampling differ. They are suitable for defining target bands, not for declaring independent parity.

## Target bands for this project

### Band A: compact strong-mini comparison

```text
persistent acquired + knowledge budget: 1–16 GiB
active-equivalent compute target:       approximately 3B parameters/token or less
```

This is the first scale where a broad comparison with modern compact open models becomes meaningful. It is not expected to equal current frontier GPT/Claude/Gemini systems.

### Band B: strong reasoning-mini comparison

```text
persistent acquired + knowledge budget: 16–80 GiB
active-equivalent compute target:       approximately 3–6B parameters/token or less
```

This band is anchored by gpt-oss-20b/120b. Reaching equal quality with materially fewer bits or operations would be a strong result.

### Band C: broad frontier-open comparison

```text
persistent acquired + knowledge budget: 128–256 GiB initially,
                                         expandable to 512 GiB
active-equivalent compute target:       approximately 17–40B parameters/token or less
```

This band covers Qwen3.5-397B-A17B and extends through DeepSeek-V3/Kimi-class total storage. It is the relevant public proxy for broad high-performance LLM parity in 2026.

## What the Minimum Predictive Machine may compress

The architecture may require fewer stored bits than dense or MoE weights when a workload contains reusable exact algorithms, sparse knowledge, indexed state, and compiled proofs. It cannot compress arbitrary independent facts or arbitrary input-output mappings below their information content. Raw-language grounding, world knowledge, candidate generation, and open-ended writing may dominate before symbolic execution does.

Consequently the working hypothesis is not “frontier intelligence fits in a few megabytes.” It is:

> The same broad quality may be reachable with a smaller persistent representation and much lower active computation when reusable structure is discovered and compiled, but the size reduction must be measured rather than assumed.

## Phase 17 extended budget ladder

The pilot begins in bytes and KiB only to validate the learner and accounting. Subsequent frozen campaigns should use forecast-first geometric points:

```text
1 MiB, 4 MiB, 16 MiB, 64 MiB, 256 MiB,
1 GiB, 4 GiB, 16 GiB, 64 GiB,
128 GiB, 256 GiB, 512 GiB
```

The campaign must fit its curve on smaller points and predict reserved larger points before those runs are inspected. It must not actually allocate the highest points until lower-budget curves show that the architecture has not already saturated.

## Required parity definition

A frontier-size forecast is meaningful only when the target evaluation includes all of the following under matched tools and information:

- open-domain language and instruction following;
- knowledge acquisition and retrieval;
- mathematical and formal reasoning;
- causal, temporal, reference and discourse reasoning;
- real repository coding and test repair;
- long-context memory;
- constrained and open writing;
- tool-using agent tasks;
- calibrated abstention and adversarial shifts;
- total stored bits, active state, memory traffic, induction compute, inference compute, latency and energy.

Until these conditions are met, model size estimates remain target bands rather than a claim that a particular Phase 17 machine matches a frontier LLM.
