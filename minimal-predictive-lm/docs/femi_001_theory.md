# FEMI-001: Factorized Executable Minimal Intelligence

## Purpose

The target is a non-neural intelligence architecture whose compute and memory do not grow with every past token merely because the transcript grows. MECI-001 used one monolithic operational quotient. That representation is exact but can create an intractable number of joint states and does not provide a credible route to a large conversational system.

FEMI replaces the monolithic state with a graph of independently addressable executable factors. A factor is a small program plus only the local state distinctions required by the queries that use it. Query indexes activate only relevant factors.

## Product-separable operational theorem

Assume a declared capability family decomposes into `k` operational factors. Factor `i` has `n_i` distinguishable local states, and every joint combination is reachable. Any exact agent must distinguish

```text
N = product_i n_i
```

joint configurations, so its active information state requires at least

```text
ceil(log2 N) bits.
```

FEMI stores one canonical local state id per factor, using

```text
sum_i ceil(log2 n_i) bits.
```

This is at most `k - 1` bits above the information-theoretic lower bound and is exact when every `n_i` is a power of two. For 32 binary factors, both the lower bound and FEMI state are 32 bits.

## Transition-description scaling

A flat transition table that treats the joint state as unstructured has `k * product_i n_i` entries for one local action per factor. A factorized description has only `sum_i n_i` entries. With 32 binary factors this is

```text
flat:       137,438,953,472 entries
factorized:              64 entries
reduction:     2,147,483,648x
```

This is not a claim that every problem factorizes. It states the precise benefit when operational independence exists and is discovered.

## Query-local compute

Each factor registers query keys. A query activates only factors indexed by its observable pattern. If a query depends on `r` factors, evaluation requires `O(r)` factor executions plus index lookup, rather than scanning all stored knowledge. Any exact implementation must inspect each relevant factor in the worst case, so linear dependence on `r` is query-local optimal up to indexing constants.

## Learning mechanism

The initial learner searches the same small executable language for all demonstrations, without task or domain labels:

- numeric extraction from raw Unicode text;
- MDL selection among arithmetic programs;
- character-level anti-unification for relation lookups;
- exact executable dialogue rules as fallback.

The experiment learns addition, a one-step linear equation transformation, factual lookup, science lookup, and a dialogue response. These are separate factors selected by one program learner.

## Prior-art boundary

Related foundations include algorithmic sufficient statistics, factored MDPs and dynamic Bayesian networks, predictive-state representations, probabilistic circuits, knowledge compilation, treewidth-based exact inference, inductive programming, and version-space algebra. The novelty candidate is the combination of:

1. operational-equivalence state minimization;
2. executable factor discovery from demonstrations;
3. a single sparse query index for language, knowledge and reasoning programs;
4. task-relative lower-bound accounting for active state and local query compute.

Novelty is not established until a broader literature review and public benchmarks are completed.

## Scaling condition and rejection rule

FEMI can scale only if broad intelligence admits reusable factors and most queries touch a bounded dependency closure. If factor discovery creates near-global factors, if dependency width grows with total knowledge, or if model code becomes comparable to a dense language model at matched quality, the proposed efficiency advantage disappears.

The next mandatory gate is the official `llm-jp-eval` suite or another public Japanese educational benchmark plus a public text corpus. It must report accuracy, bits per byte or perplexity, executable model bytes, peak memory, training operations, query throughput, factor count, and activated factors per query. Comparisons must include a memorization baseline, n-gram or context-tree model, and a small Transformer or efficient recurrent model at matched accuracy.

FEMI-001 is not Japanese-high-school-level intelligence and is not comparable with a high-performance LLM yet.
