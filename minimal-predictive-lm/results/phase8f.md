# Phase 8f results: probabilistic effects, missing sensors, and exact one-probe VOI

Beta/Dirichlet sufficient statistics replace episode replay. Missing outcomes add no fictitious failure, and missing lags update success without inventing a completion time.

- training episodes: **1,200**
- missing outcomes: **389**
- successful outcomes with missing lag: **154**
- active sufficient statistics: **126 bits**
- compact raw event code: **10,800 bits**
- history/stat ratio: **85.71x**
- learned Brier score: **0.157493**
- uniform-prior Brier score: **0.250000**

## Observation policies

| policy | accuracy | probes | probe rate | missing probes | total objective |
|---|---:|---:|---:|---:|---:|
| none | 77.6% | 0 | 0.0% | 0 | 43,072 |
| always | 87.9% | 3,000 | 100.0% | 738 | 35,232 |
| voi | 87.9% | 1,873 | 62.4% | 454 | 30,724 |

The VOI policy enumerates positive, negative, and missing readings exactly. It therefore solves the finite ACT-NOW versus PROBE-THEN-ACT problem without search approximation.

Compared with always probing, VOI preserves the same held-out accuracy while removing **1,127 probes (37.6%)** and reducing the total error-plus-observation objective by **4,508 (12.8%)**.

## Contradiction and retraction

- retraction restores previous claim: **True**
- provenance claims: **512**
- resolved active keys: **32**
- active contradictory alternatives: **192**
- provenance ledger: **86,272 bits**
- finalized active snapshot: **2,992 bits**
- finalized compaction ratio: **28.83x**

Snapshot compaction is valid only after the retraction horizon is finalized. Before that point, older claims must remain reachable because retracting a newer claim can expose an older value.

## Limitations

- the effect family and relation identity are supplied during this phase
- Beta and Dirichlet sufficient statistics assume stationary exchangeable episodes
- the VOI theorem is exact only for one optional binary/missing probe and a binary terminal decision
- sensor reliability is known rather than jointly induced
- snapshot compaction requires a finalized retraction horizon
- this is not open-domain conversation, writing, or repository-scale coding
