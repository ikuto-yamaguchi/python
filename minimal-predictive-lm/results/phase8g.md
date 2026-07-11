# Phase 8g results: shared stochastic event intelligence across domains

Conversation, writing, code, and tool events are fitted with one stochastic
operation vocabulary instead of four domain-specific runtimes.

## Joint latent-operation induction

- surface templates: **16**
- latent operations recovered: **4**
- exact hidden partition: **True**
- evaluated merge candidates: **31,652**
- 8-template exhaustive-oracle gap: **0.000000**

| model | clusters | objective |
|---|---:|---:|
| domain-separated | 16 | 2118.346 |
| shared event model | 4 | 1192.948 |

The domain-separated objective is **1.78x** the shared objective.
Sufficient statistics use **560 bits** versus **8320 bits** for the compact event stream.

## New-domain transfer

- operation assignment: **100.0%**
- pooled Brier: **0.131574**
- six-shot-only Brier: **0.134095**
- effect accuracy: **99.2%**

## Non-stationary effect

- true / detected change point: **200 / 201**
- MDL gain: **35.234 bits**
- stationary / adaptive Brier: **0.280289 / 0.248998**
- raw history / two-segment summary: **400 / 45 bits**

## Exact bounded information acquisition

| policy | mean total cost | mean error | mean probes |
|---|---:|---:|---:|
| none | 17.777778 | 0.277778 | 0.000000 |
| one_probe | 10.726222 | 0.106833 | 0.777778 |
| exact_bounded | 9.759698 | 0.092136 | 1.013220 |
| always | 13.642492 | 0.072539 | 3.000000 |

The bounded policy enumerates every available action and sensor outcome
for this finite binary POMDP, so its oracle gap is zero in this experiment.

## Limitations

- surface templates are persistent IDs; free-form language grounding is not solved
- observable effect categories still anchor the latent operation
- the change-point experiment permits only one abrupt Bernoulli shift
- the exact POMDP has one binary hidden variable and three probes
- mixed-domain workflows are synthetic micro-tasks, not real repositories or open conversation
