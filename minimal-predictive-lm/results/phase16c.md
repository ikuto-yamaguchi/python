# Phase 16c results: shared proposition runtime

An induced signed-claim graph and a finite-model monadic proposition engine
are shared across testimony, sensor audit, code review, quoted truth propagation,
and controlled formal validity. Public formats were inspected, so this is post-hoc
adaptation rather than strict zero-shot transfer.

## Runtime

- payload: **822 bytes**
- human-designed surface compilers: **2**
- benchmark task-name branches: **0**
- truth / attribution phrase groundings: **12 / 3**
- independent cross-domain: **5/5**
- contradiction / unanchored cycle abstention: **True / True**

## Third public slice

| axis | before correct/answered | after correct/answered | after wrong |
|---|---:|---:|---:|
| adjective order | 0/0 | 0/0 | 0 |
| belief propagation | 0/0 | 40/40 | 0 |
| causal judgement | 0/0 | 0/0 | 0 |
| formal validity | 0/0 | 40/40 | 0 |
| reference resolution | 0/0 | 0/0 | 0 |

Overall correct/answered: **0/0 → 80/80**
Accuracy / coverage gain: **40.0 / 40.0 percentage points**
Model payload delta: **822 bytes**
Original public regression: **200/200**
Second public raw regression: **198/200**

## Claim boundary

This phase may support only the measured proposition capabilities. It does
not establish strict zero-shot transfer, complete third-slice parity, arbitrary
proposition understanding, or general-LLM parity.

## Limitations

- truth and attribution phrase meanings use independent supervised grounding observations
- the two surface compilers were designed after inspecting public task formats
- finite-model search is bounded to at most fourteen predicate atoms per parsed argument
- the formal-language compiler covers a controlled fragment and abstains outside it
- signed claims are unary reliability reports rather than arbitrary propositions
- reference resolution, adjective ordering, and causal judgement are not targeted
- the third slice is only a five-task public benchmark sample
- free-form dialogue, real-repository coding, long context, multimodal perception, and autonomous parser induction remain untested
