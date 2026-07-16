# SPARC-HS1: Large-capacity, low-activation Japanese conversation

## Objective

The target is a Japanese conversational intelligence system that can eventually reach the breadth of a capable Japanese high-school student while using substantially less active memory and computation than a Transformer language model. HS1 does **not** claim that target has been reached. It establishes a learned language surface and a genuinely large sparse model instance without abandoning the resource constraint.

## Capacity is not activity

| profile | concept code space | active bits/turn | response capacity | sparse edge capacity |
|---|---:|---:|---:|---:|
| `ci` | 65,536 | 128 | 16,384 | 262,144 |
| `desktop-large` | 1,048,576 | 192 | 262,144 | 8,388,608 |
| `desktop-xl` | 4,194,304 | 256 | 1,048,576 | 33,554,432 |

The capacities are upper bounds, not preallocated dense arrays. A turn activates a fixed sparse code and a bounded set of candidate assemblies regardless of the configured global capacity.

## Brain-inspired mechanisms

1. **Variable-length surprise chunks**: repeated character sequences are selected by compression gain, so reusable chunks are learned from the corpus.
2. **Sparse distributed event codes**: a small number of columns represent an utterance in a much larger code space.
3. **Hebbian response assemblies**: only co-active event columns and the observed response assembly are strengthened.
4. **Homeostatic inhibition**: columns occurring in too many assemblies are inhibited during routing.
5. **Bounded global workspace**: only a fixed number of recent response assemblies are retained; no full-history KV cache is kept.
6. **Local online plasticity**: new question/answer pairs update only active columns, one assembly and a local transition.

## Validation

The conversation gate tests held-out Japanese paraphrases, context-dependent follow-ups, immediate online teaching, compressed save/load persistence and calibrated unknown responses.

The desktop-large stress model contains 8,000 distinct response assemblies and 1,536,000 sparse posting edges. This is a capacity and routing stress test, not evidence of 8,000 meaningful school concepts. It verifies that increasing stored knowledge does not force a scan of every assembly at inference.

## Remaining gates

- HS2: induced relational microprograms and multi-hop reasoning over learned events;
- HS3: compositional chunk renderer rather than whole-response retrieval;
- HS4: broad Japanese curriculum ingestion with knowledge/source separation;
- HS5: sustained free conversation, planning, mathematics and high-school subject evaluations;
- final: compare capability per byte, active operation and joule against compact Transformer/SSM baselines.

A high-school-level claim is forbidden until broad held-out free-response evaluations and human conversation tests pass.
