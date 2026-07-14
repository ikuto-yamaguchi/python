# CAP-GEN-003-RBOR-001: reset-free boundary operational reuse

## Purpose audit

The research goal is not event segmentation by itself. It is a tiny learner that acquires executable knowledge from heterogeneous experience and reuses it in a new context with lower lifetime cost.

MSO-001 removed supplied domain names but still used an explicit `RESET` event. RBOR-001 removes that token. A boundary is proposed only when the next observed record has zero support under the currently certified executable context. The proposal is causal because it uses only the current and past records. It is accepted as useful only after the new context earns prospective operational reuse.

## Prior-art boundary

The following are established and are not claimed as new:

- Bayesian online change-point detection and run-length inference;
- task-free continual learning without supplied task identities;
- predictive-error and reconstruction-error event segmentation;
- switching dynamical-system identification;
- minimum-description-length segmentation;
- graph automorphisms, MDP homomorphisms, and action-equivariant representations.

RBOR-001 is a project gate combining causal boundary proposals with the existing operational-reuse certificate and complete resource vectors. It is not a publication-level novelty claim.

## Boundary non-identifiability

Suppose two latent histories contain different hidden chronological boundaries but induce the same distribution over every observed prefix and the same future executable predictions. No causal learner can determine which hidden chronology occurred.

Therefore the project should not optimize recovery of every hidden boundary. It should infer only distinctions required for prospective prediction or economical operational reuse.

The frozen control concatenates two identical cycle episodes without a marker. The parser produces one segment and zero boundaries. This is correct: the hidden boundary has no observable operational consequence.

## Causal incompatibility proposition

Let a current context be certified by an executable hypothesis `H`. If the next observed event has zero support under `H`, the no-change continuation of `H` is falsified.

This permits a boundary proposal immediately before the incompatible event. It does not prove that a task switch is the unique explanation: the previous hypothesis could be wrong, the event could be noise, or another model change could have occurred.

Consequently RBOR-001 separates:

1. **proposal** — current evidence is incompatible with the certified context;
2. **certification** — the new segment supports a reusable operator and produces positive prospective reuse surplus.

A surprising singleton can trigger a proposal but cannot become a certified reusable context.

## Future-looking boundaries are invalid

A rule that separates two examples by reading the successor being predicted is unavailable at prediction time. It may fit a completed training stream but is not a causal boundary rule.

RBOR-001 records any use of an unobserved successor as future leakage and rejects the certificate regardless of accuracy.

## Segmentation absorption remains possible

For `N` observed transitions, an unrestricted learner can create one segment and one one-entry adapter per transition. A constant-size lookup core then achieves zero training error.

Counting only the core reports `N / 1` compression. Charging one boundary rule and all adapters gives:

```text
N / (N + 2) < 1
```

For the frozen 13-transition prefix, the apparent core-only reduction is `13x`, while the fully charged reduction is `13/15 = 0.866...`.

## Frozen reset-free stream

The stream contains only typed records:

```text
EDGE surface-a surface-b
STEP source successor
```

It contains no `RESET`, task name, or domain label. The held-out split index is used only by the evaluator after segmentation; it is not visible to the boundary parser.

The stream concatenates:

- a complete five-state training cycle;
- a complete seven-state training cycle with the opposite local orientation;
- a nine-state held-out cycle with all passive edges and one grounded active transition;
- an unsupported path-shaped context.

When a new structural record cannot be absorbed by the current certified cycle, the parser proposes a boundary from past and current evidence. The same learner then certifies two training contexts, learns one oriented-cycle successor operator, and transfers it to the held-out context.

## Required results

The gate requires:

- zero `RESET` tokens;
- zero domain-label tokens;
- all boundary proposals causal;
- one held-out interaction selecting one of two orientations;
- exact prediction of all nine held-out transitions;
- zero held-out interactions causing abstention;
- unsupported topology causing rejection;
- an operationally identical hidden boundary remaining merged;
- future-looking segmentation being rejected;
- singleton surprise segmentation failing delayed reuse certification.

## Resource vector and honest trade-off

Separate transition tables use:

```text
executable entries = 21
active interactions = 21
passive observations = 0
boundary proposals = 0
```

The shared reset-free representation uses:

```text
executable entries = 6
  event parser
  boundary rule
  shared operator
  three context adapters
active interactions = 13
passive observations = 21
boundary proposals = 3
```

This is a vector trade-off, not a universal scalar victory. With every component assigned unit cost, the shared global cost is one unit higher than the separate tables. The passive-observation relative cost must be below `20/21` for the shared global scalar cost to win under the frozen weighting.

For a new held-out context after the library already exists, the incremental comparison is positive:

```text
separate: 9 stored transitions + 9 active interactions = 18
shared:   1 adapter + 1 active interaction + 9 passive edges + 1 boundary = 12
incremental surplus = 6
```

The result therefore supports reuse in new contexts, but not a claim that the complete system is already universally cheaper.

## What this establishes

RBOR-001 removes an explicit reset marker and demonstrates causal boundary proposals tied to executable incompatibility. It also changes the target from recovering hidden chronology to discovering operationally necessary distinctions.

It does not establish:

- discovery of `EDGE` and `STEP` roles from raw bytes;
- robustness to stochastic noise;
- unknown executable-program induction;
- reuse across multiple structural families;
- transfer on a public or natural interaction trace;
- natural-language understanding;
- high-school-level or LLM-level intelligence.

## Next hypothesis

The next learner must remove at least one remaining supplied structure. The strongest direction is to infer event roles and executable programs jointly from less structured records, while keeping boundary proposals causal and accepting a component only when it improves held-out operational reuse after complete lifetime accounting.

A candidate objective is:

```text
K(event parser)
+ K(boundary rule)
+ K(shared programs)
+ K(adapters)
+ C(induction)
+ C(active grounding)
+ C(passive support)
+ C(inference)
+ M(peak)
+ prospective error and abstention risk
```

## Stagnation guard

The next step must not add more deterministic cycle sizes, state names, or impossible-edge examples. It must do at least one of:

- infer event roles from untyped or weakly typed records;
- handle noisy evidence with calibrated abstention;
- reuse one learned executable component across more than one structural family or CAP-GEN axis;
- evaluate the same artifact on a public or natural interaction trace.

Another reset-free typed cycle stream by itself is not research progress.
