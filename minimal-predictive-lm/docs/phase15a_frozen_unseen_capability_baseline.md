# Phase 15a: frozen unseen public capability baseline

## Purpose

After reaching 200/200 on the first public five-axis suite, the system is frozen and evaluated on five previously unused BIG-Bench-Hard tasks: date understanding, three-object logical deduction, three-object swap tracking, navigation, and Dyck-language completion.

No benchmark example, target, primitive, document, or handler is added before the run. The model fingerprint is unchanged.

## Result

The frozen system scores 0/200. Four axes correctly abstain. Navigation produces forty wrong answers because the sequence-ordering router fires on the broad cue `these` in `follow these instructions` and sorts the final Yes/No options.

This separates two failures:

- absent state mechanisms for time, order, permutation, space, and stack;
- an over-broad lexical route that produces unsupported answers.

## Consequence

Before adding capability, calibration must be repaired. Phase 15b therefore learns a discriminative ordering cue from positive and negative interactions, with no navigation-specific branch.
