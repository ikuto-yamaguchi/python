# Phase 18d-4: self-supervised sequence program learning

Phase 18d-3 removed task IDs but still consumed explicit `inputs` and `output` records. Phase 18d-4 replaces those records with complete typed value sequences. The sole training objective is to predict the final sequence element from its prefix.

The sequence learner converts each prefix/next-element pair into the generic Phase 18d-3 latent partition engine. It receives no task name, no declared task count, and no explicit supervised output field. Audit cluster names are stored separately and are only used after induction.

The initial stream mixes numeric and string transformations. Five additional complete sequences from a new behavior are appended after the initial learner is frozen. The same code must discover one additional latent behavior while preserving every old behavior fingerprint.

Held-out evaluation masks the final value. A complete local support sequence selects a behavior, and the learned program predicts unseen prefixes. Ambiguous support, too-short sequences, and a subminimum four-example pattern must abstain.

This is a controlled self-supervised next-value experiment. Records are still segmented typed values rather than raw bytes or natural-language tokens. The final position is human-chosen as the prediction target, and the DSL, types, partition method, and support threshold remain fixed.
