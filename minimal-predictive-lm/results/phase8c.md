# Phase 8c results: multiple latent relations under partial, noisy, delayed traces

The learner receives opaque state-effect channels rather than semantic relation names.
It must map language to reusable SET/GET schemas while distinguishing missing observations
from deletions, recovering one-step delayed effects, and rejecting unsupported accidental correlations.

- traces: **27**
- expected operations: **24**
- raw inference precision: **96.0%**
- raw inference recall: **100.0%**

## Representation competition

| hypothesis | bits | validation | lifetime objective |
|---|---:|---:|---:|
| exact_surface | 6,400 | 36.8% | 18,688 |
| support_1_schema | 3,983 | 94.7% | 5,007 |
| robust_multi_relation_schema | 3,703 | 100.0% | 3,703 |

Selected: **robust_multi_relation_schema**.

The support-1 learner memorizes a single accidental `雑談` correlation and fails a held-out distractor.
The support-2 schema removes it while preserving all direct, partial-observation, delayed-effect, and query rules.

## Indexed routing

- compiled rules: **12**
- linear scan: **12.0 rule checks/input**
- cue index: **0.789 rule checks/input**
- symbol checks after routing: **3.737/input**

The index cost is included in the serialized description length.

## New relation bootstrap

Two consistent traces expand the opaque relation count from **3** to **4**.
They add **1 rule** and **357 bits**.
A held-out key/value recombination is handled at **100.0%**.

## Limitations

- opaque effect-channel identifiers are observable even though their semantics are not named
- surface-rule candidates remain a restricted template language
- noise handling is support-based and does not model adversarial or correlated noise
- delayed effects span one step only
- the experiment does not yet infer arbitrary goals or repository-scale programs
