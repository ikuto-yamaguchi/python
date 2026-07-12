# Phase 15b results: discriminative routing guard

Ordering cues are induced from positive ordering interactions and independent non-ordering negatives. The smallest cue conjunction that covers all positives and no negatives is retained.

## Router

- selected required cues: **`sort`**
- positive / negative calibration examples: **4 / 4**
- candidate cue sets: **7**
- router payload: **103 bytes**

## Unseen public baseline before and after

- answered / correct before: **40 / 0**
- answered / correct after: **0 / 0**
- wrong answers removed: **40**
- original Phase 14b public regression: **200/200**

## Interpretation

The system now abstains on all 200 unsupported examples instead of emitting forty nonsensical navigation answers. This is better calibration, not new capability.

## Limitations

- negative routing examples were authored after observing the false-positive family
- the correction improves calibration but solves none of the five unseen capabilities
- cue induction is lexical and bounded to conjunctions of at most three words
- the original public suite is retained but broader paraphrase robustness is not established
