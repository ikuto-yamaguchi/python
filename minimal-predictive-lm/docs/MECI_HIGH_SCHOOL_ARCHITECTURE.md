# MECI-HS: minimum-resource Japanese high-school-level intelligence

## Non-negotiable objective

Build a model that can converse in free Japanese at approximately a capable
Japanese high-school student's level while minimizing, in this order:

1. inference working memory;
2. inference operations per generated token;
3. stored parameters and knowledge bytes;
4. training compute required to acquire a new capability.

Multiple-choice benchmark improvement is evidence only. It is never the target.
A release is not considered successful until a user can hold a sustained,
open-ended conversation with the model and observe broad knowledge, reasoning,
learning, explanation, correction and planning.

## Hard exclusions

- No full-history softmax self-attention.
- No KV cache whose memory grows linearly with the conversation length.
- No claim of intelligence from memorized response replay.
- No task-ID router supplied by the evaluator.
- No benchmark-specific templates counted as general capability.
- No claim of high-school-level intelligence without held-out free-response tests.

## Core hypothesis: Selective Associative Cognitive State (SACS)

The model does not retain every previous token. It maintains a small executable
state with four distinct memory types.

### 1. Perceptual recurrent state

A tokenizer-light byte/subword encoder updates a fixed-size recurrent state.
The sequence mixer is a gated linear recurrence, not quadratic attention.
Multiple time constants preserve local syntax, discourse state and long-lived
intent at different decay rates.

### 2. Associative fast-weight memory

Each layer owns a small number of block-sparse key/value banks. A write uses a
delta correction rather than blindly adding a new association:

    prediction = M @ key
    error      = value - prediction
    M          = decay * M + write_gate * error outer key

Erase and write gates are independent. Only the top-k blocks selected by a
cheap hash/gate are read or changed. Context length therefore does not increase
inference memory. This is content-addressing, but not Transformer attention over
all previous tokens.

### 3. Compressed semantic/procedural graph

Stable facts, concepts and learned procedures are consolidated outside the
per-token recurrent state. Nodes and relations are quantized and deduplicated.
Only a small top-k neighborhood is activated for a turn. The knowledge store may
grow because broad knowledge has a real information lower bound, but active RAM
and compute must remain bounded.

### 4. Deliberation state machine

The controller may execute several internal recurrent steps before answering.
Each step selects one operation such as retrieve, compare, infer, calculate,
verify, revise or speak. A learned halt gate stops when confidence is adequate.
Easy utterances use one step; difficult questions spend more compute. This makes
reasoning compute conditional instead of paying a large fixed Transformer cost
for every token.

## Why no dogmatic ban on all attention-like behavior

A capable agent must select relevant information. The rejected mechanism is the
quadratic all-token softmax matrix and its growing KV cache. SACS permits:

- fixed-state recurrent selection;
- top-k associative reads;
- local-window mixing;
- external graph lookup;
- optional tiny bounded attention over 8-32 active slots only.

A bounded slot selector is acceptable only if measurements show that it improves
reasoning per byte and per operation. It must never scale with total history.

## Learning system

The same core must acquire capabilities from ordinary data rather than hand-made
per-task rules.

1. self-supervised next-unit and denoising learning for Japanese expression;
2. contrastive relation learning for semantic state;
3. delta-memory write/erase learning for online adaptation;
4. teacher distillation for explanations and tool-use traces;
5. curriculum from language grounding to multi-step reasoning;
6. consolidation that compresses episodes into facts and procedures;
7. replay chosen by information gain, not uniform replay.

## Resource score

Every experiment reports both intelligence and resources. A candidate dominates
another only when its capability gain is worth its resource increase.

    resource_cost =
        artifact_bytes
      + alpha * peak_inference_bytes
      + beta  * operations_per_generated_token
      + gamma * training_operations

Pareto-front candidates are retained. A larger model is rejected when a smaller
candidate matches it within the predeclared confidence interval.

## Milestones

### HS-0: stateful conversation kernel

- free Japanese input;
- online fact learning;
- multi-turn reference resolution;
- explicit unknown response;
- arithmetic and multi-hop symbolic reasoning;
- artifact under 100 KB.

This is a scaffold, not learned general intelligence.

### HS-1: learned recurrent language surface

- SACS sequence core trained from Japanese text/dialogue;
- responses are generated, not selected from stored episodes;
- no growing KV cache;
- held-out dialogue perplexity and semantic answer tests;
- interactive CPU or RTX 4060 execution.

### HS-2: unified memory and reasoning

- online memory correction without full retraining;
- 10+ turn consistency;
- unseen multi-step reasoning and explanation;
- active memory fixed with respect to conversation length.

### HS-3: broad Japanese high-school curriculum

Held-out free-response questions across Japanese, mathematics, science, social
studies, English understanding and everyday reasoning. Answers must include
explanations and allow follow-up challenges. Benchmark questions seen in
training are excluded.

### HS-4: conversational release candidate

- sustained open-ended Japanese conversation;
- broad high-school-level knowledge and reasoning;
- correction after user feedback;
- planning and explanation;
- resource target selected from the measured Pareto frontier.

## Immediate experiments

1. Replace the current byte n-gram generator with a learned block-sparse
   delta-memory recurrent core.
2. Compare fixed-state SSM, one-bank delta memory, multi-timescale banks and a
   bounded 16-slot selector at equal parameter and operation budgets.
3. Measure copy, induction, associative recall, Japanese generation and
   multi-hop reasoning—not only classification.
4. Keep the explicit semantic memory scaffold only as a teacher/debug oracle;
   progressively replace hand-written parsing with learned representations.
5. Distill a small Japanese dialogue corpus on the user's RTX 4060 while GitHub
   Actions runs deterministic CPU-scale ablations.

## Claim boundary

MECI-HS is a research program. No current artifact is yet Japanese
high-school-level intelligence. Success requires the HS-3 and HS-4 gates, not a
promising architecture name or isolated benchmark result.
