# Phase 16d results: signed-claim scaling and shift audit

No public benchmark examples or targets are used. The Phase 16c semantics
are held fixed while a queue work-list replaces repeated whole-graph scans.

## Headline

- random shifted chains: **100/100**
- reverse 1,024-link legacy operations: **1,049,601**
- reverse 1,024-link queue operations: **3,073**
- abstract operation speedup: **341.6x**
- safe abstention retained: **True**
- formal chain/converse checks: **True**

## Scaling

| claims | order | legacy operations | queue operations | speedup | correct |
|---:|---|---:|---:|---:|---:|
| 1 | forward | 3 | 4 | 0.8x | True |
| 1 | reverse | 3 | 4 | 0.8x | True |
| 2 | forward | 5 | 7 | 0.7x | True |
| 2 | reverse | 7 | 7 | 1.0x | True |
| 4 | forward | 9 | 13 | 0.7x | True |
| 4 | reverse | 21 | 13 | 1.6x | True |
| 8 | forward | 17 | 25 | 0.7x | True |
| 8 | reverse | 73 | 25 | 2.9x | True |
| 16 | forward | 33 | 49 | 0.7x | True |
| 16 | reverse | 273 | 49 | 5.6x | True |
| 32 | forward | 65 | 97 | 0.7x | True |
| 32 | reverse | 1057 | 97 | 10.9x | True |
| 64 | forward | 129 | 193 | 0.7x | True |
| 64 | reverse | 4161 | 193 | 21.6x | True |
| 128 | forward | 257 | 385 | 0.7x | True |
| 128 | reverse | 16513 | 385 | 42.9x | True |
| 256 | forward | 513 | 769 | 0.7x | True |
| 256 | reverse | 65793 | 769 | 85.6x | True |
| 512 | forward | 1025 | 1537 | 0.7x | True |
| 512 | reverse | 262657 | 1537 | 170.9x | True |
| 1024 | forward | 2049 | 3073 | 0.7x | True |
| 1024 | reverse | 1049601 | 3073 | 341.6x | True |

## Claim boundary

This phase supports only semantic equivalence, distribution-shift robustness, and abstract operation-scaling claims for the measured signed-claim fragment.

## Limitations

- generated chains exercise unary signed reliability claims, not arbitrary nested propositions
- operation counts are abstract interpreter steps rather than hardware energy measurements
- phrase meanings remain independently supervised groundings
- formal finite-model search remains bounded to the controlled monadic fragment
- this phase measures robustness and scaling, not a new public capability
