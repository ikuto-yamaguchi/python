# Phase 8f: Probabilistic effects, missing observations, and minimum-cost information acquisition

## Goal

Phase 8e reduced latent-relation partition search, but its effects remained deterministic and every relation had one fixed delay. Phase 8f introduces uncertainty without returning to dense hidden-state vectors or replaying the entire interaction history.

The phase asks four questions:

1. Can stochastic success and 1--16 step delays be represented by a small sufficient state?
2. Can missing outcomes be handled without silently converting them into failures?
3. Can the machine decide exactly when another sensor read is worth its cost?
4. Can contradictions and retractions be preserved while keeping the active runtime state small?

This is still a closed micro-world. It is a mathematical substrate experiment, not a claim of LLM-level language ability.

## 1. Minimum sufficient statistics

For relation `r`, let eventual success be

```text
S_r ~ Bernoulli(theta_r)
```

and, conditional on success, let completion delay be

```text
L_r | S_r = 1 ~ Categorical(phi_r,1 ... phi_r,K)
```

with `K = 16` in this experiment.

We use conjugate priors:

```text
theta_r ~ Beta(1, 1)
phi_r   ~ Dirichlet(1, ..., 1)
```

The posterior requires only:

```text
(success_count, failure_count, lag_count[1:K])
```

The full episode sequence is unnecessary under the stationary exchangeable model. After `N` observations, counter storage is

```text
O((K + 2) log N) bits per relation
```

rather than `O(N)` event records.

The probability that an effect has happened by step `t` is

```text
P(changed by t)
  = E[theta_r | data]
    * sum(lag <= t) E[phi_r,lag | data]
```

A missing outcome performs no update. A known success with unknown lag updates the Beta statistic but not the lag counts. This prevents resource-saving shortcuts from inventing evidence.

## 2. Exact one-probe Value of Information

At decision time, let

```text
p = P(the effect has happened)
```

and let a wrong binary decision cost `C_e`.

The Bayes risk without another observation is

```text
R_now(p) = min(p, 1 - p) * C_e
```

The optional sensor has three outcomes:

```text
positive
negative
missing
```

with known true-positive, false-positive, and missing probabilities. For each observed result `y`, Bayes' rule produces `p_y`.

The expected risk after probing is

```text
R_after(p)
  = sum_y P(y | p) * min(p_y, 1 - p_y) * C_e
```

If the sensor costs `C_s`, then

```text
VOI(p) = R_now(p) - R_after(p) - C_s
```

Probe exactly when

```text
VOI(p) > 0
```

### Exactness statement

For the finite action set

```text
ACT-NOW
PROBE-THEN-ACT
```

with one optional sensor and a terminal binary decision, the algorithm enumerates every sensor outcome and both actions. Therefore it is Bayes-optimal for this restricted problem. It is not a heuristic search claim.

The computation is constant in conversation-history length: three outcome branches are evaluated from the sufficient belief state.

## 3. Experiment

Three effect families are generated:

```text
location: success 0.90, lag 2 or 4
owner:    success 0.75, lag 1 or 3
status:   success 0.60, lag 5 or 8
```

Training contains 1,200 episodes with:

- 30% missing final outcomes
- 25% missing delays among observed successes
- maximum supported delay 16

The held-out set contains 3,000 binary state decisions. The optional sensor has:

```text
true positive:  0.90
false positive: 0.08
missing:        0.25
read cost:      4
wrong decision: 64
```

Policies:

```text
NONE   : never probe
ALWAYS : probe every case
VOI    : probe only when exact expected risk reduction exceeds cost
```

## 4. Results

The active posterior state is 126 bits of counters. A compact fixed-width code for the 1,200 raw relation/outcome/lag events is 10,800 bits, an 85.71x ratio. This comparison counts only event fields; natural-language logs would be larger.

| policy | accuracy | probes | total objective |
|---|---:|---:|---:|
| none | 77.6% | 0 | 43,072 |
| always | 87.9% | 3,000 | 35,232 |
| VOI | 87.9% | 1,873 | 30,724 |

VOI removes 1,127 sensor reads while preserving the accuracy of always probing. It does not gain efficiency by accepting additional errors in this workload.

The learned probability model has Brier score 0.157493 versus 0.25 for a uniform predictor.

## 5. Contradiction and retraction

A simple latest-claim cache is insufficient because retracting a newer claim may expose an older claim.

The implementation therefore separates:

```text
append-only provenance ledger
minimal resolved active view
```

A claim contains key, value, timestamp, confidence, and ID. Retraction marks a claim inactive. Resolution chooses the latest active claim, with confidence and ID used as deterministic tie breakers.

In the test:

```text
設計書 = 棚A
設計書 = 保管庫
retract(second claim)
```

resolution correctly returns `棚A` again.

Across 512 claims and 32 keys:

```text
provenance ledger:          86,272 bits
finalized resolved snapshot: 2,992 bits
ratio:                       28.83x
```

The full provenance cannot be deleted while later retractions remain possible. Snapshot-only compaction is permitted only after a horizon is finalized. This avoids claiming an invalid memory saving.

## 6. What is mathematically minimal here

Phase 8f establishes restricted optima, not universal minimality:

- Beta/Bernoulli and Dirichlet/categorical histories admit count sufficient statistics under their model assumptions.
- one optional binary/missing observation is solved exactly by finite Bayes-risk enumeration.
- finalized claims with identical future decision consequences can be collapsed into one active snapshot.

Costs that remain unavoidable are kept visible:

- counters grow logarithmically with evidence count
- supporting 16 distinct delays requires lag distinctions
- uncertain decisions sometimes require a sensor read
- unresolved retractions require provenance

## 7. Failure modes

- relation identities are supplied rather than jointly induced with probabilities
- stationarity and exchangeability may fail in real agents
- sensor reliability is known
- only one optional probe is optimized exactly
- long-horizon information gathering becomes a POMDP and can again explode
- language grounding remains a restricted interface
- no evidence yet shows high-performance-LLM-level conversation, writing, or coding

## 8. Next phase

Phase 8g should remove more supplied structure while retaining resource accounting:

1. jointly infer relation partition, success probability, lag distribution, and sensor reliability
2. detect non-stationarity with change points rather than retaining all old evidence
3. allow multiple probes but stop by bounded VOI
4. compare exact small-world POMDP oracles with approximate policies
5. mix language interaction, code edits, test results, and tool observations in one event model
6. charge every belief bit, sensor read, branch evaluation, migration, and rollback

The acceptance criterion remains Pareto improvement in held-out task quality and full lifetime resource cost, not benchmark accuracy alone.
