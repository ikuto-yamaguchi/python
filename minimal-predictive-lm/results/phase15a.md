# Phase 15a results: frozen unseen public capability baseline

The Phase 14b system was frozen before evaluation on five previously unused public BIG-Bench-Hard tasks. No benchmark example, target, document, handler, or primitive was added.

## Frozen public result

| axis | correct | answered | wrong | abstained | examples |
|---|---:|---:|---:|---:|---:|
| date understanding | 0 | 0 | 0 | 40 | 40 |
| logical ordering | 0 | 0 | 0 | 40 | 40 |
| state permutation tracking | 0 | 0 | 0 | 40 | 40 |
| spatial navigation | 0 | 40 | 40 | 0 | 40 |
| stack completion | 0 | 0 | 0 | 40 | 40 |

Overall: **0/200**. Coverage was **20%** and selective accuracy was **0%**.

## Routing failure

All forty navigation prompts were incorrectly routed to the sequence-ordering program. The positive-only ordering calibration had retained the broad cue `these`; navigation prompts contain `follow these instructions`, and the router sorted the final `Options:` section into `- - No Yes`.

The other four axes correctly abstained. This frozen result therefore exposed both complete capability gaps and one over-broad routing rule.

## Claim boundary

Phase 15a is a failure boundary, not an adaptation result. The next phase must first remove the false-positive route without adding a navigation-specific branch.
