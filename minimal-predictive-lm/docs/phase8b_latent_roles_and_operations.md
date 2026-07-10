# Phase 8b: Latent roles and operations from interaction traces

## Motivation

Phase 8a still receives entity/location type inventories and supervised intent labels. That is too much structure to call semantic discovery.

Phase 8b removes those labels from the main learner. It observes only:

- pre-state
- utterance
- post-state
- response

From those traces it attempts to infer the smallest state operation and the reusable argument roles needed to execute it.

## Operation induction

For a deterministic key-value world:

- if exactly one mapping changes and the key/new value occur in the utterance, infer `SET(key, value)`
- if state is unchanged and the response exposes one existing key/value pair requested by the utterance, infer `GET(key)`

The surface labels `remember`, `move`, and `query` are not used by this induction path.

## Role discovery

Argument positions create candidate latent roles:

```text
SET(role_0, role_1)
GET(role_0)
```

Symbols appearing in `role_0` form one class and symbols appearing in `role_1` form another. The hypothesis is not accepted merely because it fits training traces. It competes against:

1. exact utterance memory
2. a single untyped symbol inventory
3. two reusable latent roles

The objective charges validation errors, surface-rule bits, stored symbol strings, and role-assignment bits.

## Why role separation can reduce total cost

An untyped parser can accept role-reversed commands such as treating a location as the object being moved into an entity. Two latent roles add a small assignment cost but reject those invalid compositions and permit the same surface program to transfer across valid symbols.

## Factor linguistic distinctions by state effect

Declarative remembering and imperative moving may look linguistically different while producing the same state transition:

```text
remember(entity, location) -> SET(entity, location)
move(entity, location)     -> SET(entity, location)
```

If downstream behavior depends only on the state update, retaining separate internal intents is redundant. Phase 8b compares the stored rule bits for three surface intents against two state operations.

## Incremental symbols

After the program is learned, a new observed transition can assign roles to new symbols. Only the new symbol strings and role assignments are stored; no new surface-rule bits should be required.

## Limitations

This experiment is deliberately narrow:

- the world contains one deterministic relation
- state transitions and responses are observable
- traces are noise-free
- surface features remain restricted to the Phase 8a hypothesis language
- goals and arbitrary predicates are not discovered

The result is evidence that some semantic structure can be derived from effects rather than handwritten intent labels. It is not evidence of open-domain language understanding.

## Next step

Phase 8c should introduce multiple relations, noisy/partial observations, delayed effects, and tasks spanning conversation, writing, code, and tools. Competing latent schemas must be evaluated by held-out regret plus total lifetime resource cost, not training fit alone.
