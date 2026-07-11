# Phase 8e results: residual-driven partition search

Bell-number exhaustive enumeration is replaced by splits proposed only from observed
lag/cell residual conflicts. A bounded beam keeps alternative hypotheses, and merge
moves can undo an over-split.

| templates | hidden relations | Bell partitions | evaluated | checks | exact partition | validation | objective | oracle gap |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 2 | 15 | 13 | 1,404 | True | 100.0% | 70 | 0 |
| 8 | 3 | 4,140 | 35 | 15,995 | True | 100.0% | 115 | 0 |
| 12 | 3 | 4,213,597 | 55 | 37,455 | True | 100.0% | 123 | n/a |
| 32 | 4 | 128,064,670,049,908,713,818,925,644 | 101 | 318,352 | True | 100.0% | 196 | n/a |

For the 4- and 8-template worlds the exhaustive oracle is still feasible.
The residual search reaches the same minimum objective and exact hidden partition.
For 12 and 32 templates the hidden generator is used only for evaluation; exhaustive
enumeration is not run.

## Search amortization

Search is paid once and compiled away. The table below keeps the search work visible
instead of hiding it outside model size.

| templates | one deployment | 100 deployments | 10,000 deployments |
|---:|---:|---:|---:|
| 4 | 1,404.0 | 14.04 | 0.1404 |
| 8 | 15,995.0 | 159.95 | 1.5995 |
| 12 | 37,455.0 | 374.55 | 3.7455 |
| 32 | 318,352.0 | 3,183.52 | 31.8352 |

## Limitations

- residual signatures are derived from a restricted anonymous-cell timeline interface
- beam search is not a proof of the global optimum outside oracle-sized worlds
- relations are deterministic and each has one shared lag
- the acted-on value is directly visible in the sensor stream
- candidate generation is polynomial only under fixed beam width and round budget
