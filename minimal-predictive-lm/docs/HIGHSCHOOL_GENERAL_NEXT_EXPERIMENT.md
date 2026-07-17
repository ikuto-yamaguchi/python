# Next experiment: shared predictive episode representation

## Hypothesis

A single sparse episode structure can replace separate world, textbook, dialogue, arithmetic, causal, and planning representations. Each observation is compressed into a bounded set of opaque slots representing participants, values, relations, temporal order, evidence, goals, and state changes. Slot roles are selected by predictive description-length gain across heterogeneous episodes rather than by domain labels.

## Required comparison

1. Existing main-line composition.
2. Surface-only character baseline.
3. Shared predictive episode learner.
4. Oracle-structure upper control, used only to estimate headroom.

## Frozen transfer

Training mixes Japanese reading, quantities, causal processes, social timelines, and simple plans. Final evaluation withholds one wording family and one complete domain. The same model and routing path answer every prompt.

## Pass conditions

- aggregate integrated accuracy at least 15 points above the best non-oracle baseline;
- minimum axis at least 40%;
- untouched domain at least 60%;
- untouched wording at least 70%;
- coverage at least 70% and selective accuracy at least 90%;
- continual regression below 5%;
- model no larger than 1 MiB for the first experiment;
- no global scan, task identifier, domain identifier, or example-specific rule.

Failure means the shared slot-induction mechanism is replaced rather than patched by task.
