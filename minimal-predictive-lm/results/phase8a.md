# Phase 8a results: residual-driven semantic program induction

This phase asks whether failed paraphrases can be compressed into reusable
typed-slot programs instead of being stored as exact utterances.

- selected minimum character feature width: **2**
- validation MDL objective: **901**
- induced rules: **7**
- induced program size: **389 bits**

## Generalization

| parser | compositional targets | distractor rejection | lexical-shift accuracy |
|---|---:|---:|---:|
| exact surface memory | 0.0% | 100.0% | 0.0% |
| typed slot templates | 100.0% | 100.0% | 0.0% |
| induced feature program | 100.0% | 87.5% | 33.3% |

Exact memorization cannot transfer to unseen names or combinations. Typed
slots remove that combinatorial duplication. The induced program additionally
transfers some lexical evidence, but it does not solve unrestricted paraphrase.

## Residual round

Four failed lexical constructions were added as supervised residual probes.
The refitted program uses **554 bits** and
**10 rules**.

- new entities/locations using those constructions: **100.0%**
- another unseen lexical family: **16.7%**

The residuals generalize across typed symbols, not merely exact strings. However,
the sharp drop on a second shift shows that the current hypothesis language still
learns surface evidence rather than open-domain semantics.

## Representation scaling

| entities = locations | exact surface bits | induced program + symbols | ratio |
|---:|---:|---:|---:|
| 8 | 83,120 | 1,093 | 76.0x |
| 32 | 1,349,840 | 3,557 | 379.5x |
| 128 | 22,112,432 | 13,989 | 1580.7x |

The exact utterance table grows quadratically with entity/location combinations.
The induced program is constant-size and pays linearly only for genuinely new
symbols. This is a real scaling improvement for the represented domain, not yet
evidence of high-performance open-domain conversation.

## Failure that remains

The system still receives the entity/location type inventory and supervised intent
labels. It does not yet invent predicates, discover types, or infer goals from raw
conversation. Phase 8b must induce those latent variables from action/prediction
collisions while charging search, storage, and verification cost.
