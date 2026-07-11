# Phase 8g: Shared stochastic event intelligence across domains

## Goal

Phase 8f modeled stochastic effects after relation identities were supplied. Phase 8g asks whether conversation, writing, coding, and tool use can share the same small stochastic operation vocabulary instead of maintaining four separate internal runtimes.

The experiment is still a synthetic micro-world. It does not claim open-domain language understanding. Its purpose is to test three mathematical claims:

1. surface actions from different domains can be grouped by common consequences and probability laws;
2. pooling evidence across domains can reduce model description length and improve few-shot prediction;
3. non-stationary behavior and information acquisition can be handled without replaying the full history.

## 1. Shared operation model

Each observed event has

```text
(surface template, domain, observed effect, success/failure, delay)
```

The learner is not given the hidden operation label. It compares partitions of surface templates. A cluster stores one stochastic operation model:

```text
success ~ Bernoulli(theta)
delay | success ~ Categorical(phi)
effect ~ Categorical(psi)
```

With conjugate priors, the integrated negative log likelihood is computed from counts. A partition is scored by

```text
J(partition)
  = cluster description bits
  + template-to-cluster assignment bits
  + Bernoulli marginal NLL
  + delay marginal NLL
  + effect marginal NLL
```

The 48-bit cluster charge is an explicit opcode/schema cost. It prevents one cluster per surface expression from being free.

The hidden operations are deliberately reused across domains:

```text
SET      conversation memory / paragraph insertion / assignment / tool-result storage
VERIFY   intent confirmation / fact check / tests / tool-output check
RETRACT  correction / sentence removal / patch rollback / action cancellation
EMIT     answer / prose output / patch output / command send
```

A domain-separated baseline keeps one schema per surface/domain operation. The shared model may merge templates only when the reduction in description length exceeds the increased stochastic NLL.

## 2. Search

For eight templates, all 4,140 set partitions are evaluated as an oracle. A merge-beam starts from one cluster per surface template and proposes pairwise merges. In the oracle-sized world, it reaches the same minimum objective and hidden partition.

For sixteen templates, exhaustive enumeration is not used. A width-64 merge beam is used. This is not a proof of global optimality, but the hidden generator is used after fitting to measure exact recovery.

## 3. Few-shot domain transfer

The learner first sees conversation, writing, and code events. Tool events are held out. For each new tool surface template, six calibration events are supplied.

The template is assigned to the existing cluster that minimizes the incremental integrated NLL. After assignment, the pooled posterior is used:

```text
posterior(existing cross-domain cluster + six tool events)
```

This is compared with a six-shot-only posterior that ignores the related domains.

## 4. Non-stationarity

A stationary Bernoulli model can become harmful when an operation changes. For a sequence of outcomes, the learner compares

```text
one stationary segment
```

against

```text
segment 1 + segment 2 + split-description bits
```

using exact Beta-Bernoulli marginal code lengths. A split is accepted only when its MDL gain is positive.

The full bit history is not kept as active prediction state. After a split, two count summaries plus the change-point index are sufficient for this one-change model.

## 5. Multiple information probes

Phase 8f solved one optional observation. Phase 8g allows three heterogeneous sensors. The state is a binary belief `p` plus the set of unused probes.

For each belief state, the available actions are

```text
ACT NOW
PROBE sensor 1
PROBE sensor 2
PROBE sensor 3
```

Each probe has positive, negative, and missing outcomes. Dynamic programming enumerates every action and outcome recursively:

```text
V(p, remaining probes)
  = min(
      terminal Bayes risk,
      probe cost + expected V(updated belief, remaining probes)
    )
```

For this finite binary POMDP the solution is exact. It is compared with no probing, a best one-probe policy, and always probing all sensors.

## 6. Resource accounting

The experiment reports:

- partition candidates evaluated;
- model description and marginal likelihood objective;
- sufficient-statistic bits versus a compact event stream;
- representation conversions avoided by sharing one event form;
- new-domain Brier score;
- change-point summary bits;
- dynamic-program belief states;
- expected probes, error probability, and total decision cost.

## 7. What this establishes

Within the controlled world:

- cross-domain actions with the same consequence can be induced as one operation;
- the shared representation is smaller than domain-separated schemas;
- pooled evidence improves few-shot prediction in a new domain;
- a change point can be selected by positive MDL gain and stored compactly;
- bounded multi-probe information acquisition can be solved exactly.

## 8. What remains unsolved

- Free-form utterances are currently stable template identities. Mapping arbitrary language to a template is still the largest gap.
- Observable effect categories anchor the operation partition.
- The change-point model allows one abrupt shift, not arbitrary continual drift.
- The exact POMDP has one binary hidden variable and three probes; general belief planning is much harder.
- The workflows are synthetic and do not yet execute real repository edits, long-form writing, or unrestricted dialogue.

The next phase must remove persistent template IDs and infer a canonical event program from raw token/AST/tool traces, then run a real mixed workflow with one shared state and effect boundary.
