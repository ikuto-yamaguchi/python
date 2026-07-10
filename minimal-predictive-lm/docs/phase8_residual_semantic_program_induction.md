# Phase 8: Residual-driven semantic program induction

## Goal

Phase 7 showed that indexed memory and long conversation state can scale, while free paraphrase remains the main failure point. Adding one handwritten rewrite per failed utterance overfits and eventually becomes another surface cache.

Phase 8 asks whether failures can instead produce a reusable, minimum-description semantic program.

The target path is:

```text
raw utterance
-> typed symbols and candidate relations
-> smallest rule set that separates required actions
-> canonical semantic program
-> shared state rewrite / effect / response
```

The first experiment remains supervised and deliberately narrow. It is not presented as open-domain language understanding.

## Phase 8a hypothesis language

An utterance is normalized, then known runtime entities and locations are replaced by typed slots:

```text
試作品を検査室に移して
-> <E>を<L>に移して
```

Candidate rules are conjunctions of at most two atoms:

- entity/location slot presence or absence
- entity-before-location or location-before-entity
- short character substrings

The learner searches minimum character widths 1 through 4. It chooses the parser minimizing:

```text
validation errors * error bits
+ stored rule description bits
```

The validation set contains unseen entity/location combinations and unrelated conversational distractors. This prevents selecting only the shortest character feature when it causes false positives.

## Baselines

1. **Exact surface memory**
   - stores complete utterance -> complete program
   - cannot transfer to new names or combinations

2. **Typed slot templates**
   - replaces entity/location strings with slots
   - transfers compositionally, but not across new lexical constructions

3. **Induced feature program**
   - searches reusable slot/substring conjunctions
   - may transfer some lexical evidence beyond exact templates

## Residual round

After initial evaluation, four failed lexical constructions are supplied with their correct semantic intents. The learner is refit and evaluated on:

- the same constructions with different entities and locations
- a second, different lexical family

This distinguishes slot-level reuse from genuine open-domain paraphrase generalization.

## Scaling audit

For `N` entities and `N` locations, enumerating all remember/move utterances grows as `O(N^2)`. The induced rule program remains constant and the symbol table grows only with genuinely new names, `O(N)`.

All reported bits include the rule program and stored symbol strings. They do not include a hidden neural encoder.

## Non-negotiable limitations

Phase 8a still receives:

- the entity and location inventories
- supervised intent labels
- a restricted candidate language
- a curated validation set

It does not yet invent types, predicates, relations, goals, or program structures from raw interaction.

## Phase 8b

The next experiment must remove those gifts. Candidate latent variables should be proposed only when two histories currently map to the same internal state but require different predictions or actions.

A proposed feature, type, predicate, or parameterized program is retained only when its held-out reduction in regret exceeds:

```text
program bits
+ active state bits
+ indexing and memory traffic
+ induction search
+ verification cost
+ migration cost
```

The benchmark must mix conversation, writing, code edits, and tool actions so that a representation specialized to one surface task cannot win by local overfitting.
